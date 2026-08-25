#!/usr/bin/env python3
# ==============================================================================
# CASSANDRA LIVE v1.0 — Paper trading Binance Testnet (paquete congelado)
# ==============================================================================
# Paquete: variante S | BTC | ENSEMBLE 6 seeds | refugio R1 (tracking)
# Corre 1 vez/dia (cron 00:45 UTC). Idempotente. Sin Telegram.
#
# MODOS:
#   DRY_RUN=true  -> calcula señal y decision, NO toca Binance (primer test)
#   DRY_RUN=false -> ejecuta ordenes market en testnet.binance.vision
#
# TRACKINGS PARALELOS (pre-registro Agreement):
#   A: señal ensemble + overlay            (la que OPERA en testnet)
#   B: señal ensemble x agreement + overlay (solo tracking interno, 90 dias)
#   Refugio R1 (~6% oro dinamico): tracking interno (testnet no opera oro;
#   en produccion real se implementaria con PAXG).
#
# REGLAS MC (del bootstrap del holdout, integradas al reporte):
#   DD 0-12%: normal | 12-18%: tipico | 18-24%: percentil alto, vigilar
#   DD >24%: FUERA de distribucion -> revisar sistema
# ==============================================================================
import os, sys, json, time, shutil, logging, traceback
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv

# Public release note: automatic pip installation was removed during publication
# hardening. Install dependencies from requirements.txt instead. Research and
# testnet execution logic below is otherwise preserved.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
_DRY = os.getenv("DRY_RUN", "true").lower() == "true"
if not _DRY:
    try:
        from binance.client import Client
        from binance.exceptions import BinanceAPIException, BinanceOrderException
    except ImportError as exc:
        raise SystemExit("python-binance is required when DRY_RUN=false") from exc
else:
    class BinanceAPIException(Exception): pass
    class BinanceOrderException(Exception): pass
    Client = None

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE/".env")
STATE_F = BASE/"paper_state.json"
PARAMS_F = BASE/"config"/"model_params.json"
DAILY_F, TRADES_F, LOG_F = BASE/"daily.csv", BASE/"trades.csv", BASE/"run.log"
BACKUP_D = BASE/"backups"; BACKUP_D.mkdir(exist_ok=True)

DRY_RUN   = os.getenv("DRY_RUN", "true").lower() == "true"
API_KEY   = os.getenv("BINANCE_TESTNET_API_KEY", "")
API_SEC   = os.getenv("BINANCE_TESTNET_API_SECRET", "")
SYMBOL    = "BTCUSDT"
TOLERANCE, MIN_TRADE, TRADE_FEE = 0.05, 11.0, 0.0040
DD_SOFT, DD_HARD, DD_FLOOR = 0.18, 0.30, 0.15
SHARPE_WINDOW, SHARPE_THRESHOLD = 90, 0.5
BEAR_MA, BEAR_SLOPE, BEAR_RED = 200, 90, 0.50
GOLD_CAP = 0.50

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                    handlers=[logging.FileHandler(LOG_F), logging.StreamHandler(sys.stdout)])
log = logging.getLogger("cassandra")

# ----------------------------------------------------------------- ESTADO ----
def load_state():
    if STATE_F.exists():
        try:
            return json.load(open(STATE_F))
        except Exception as e:
            log.error(f"state corrupto: {e} — restaura desde backups/")
            raise SystemExit(1)
    return {"start_date": None, "peak_equity": 0.0, "starting_balance": 0.0,
            "equity_history": [], "recent_returns": [],
            "trackB_equity": 0.0, "trackB_peak": 0.0, "trackB_recent": [],
            "refuge_equity": 0.0, "last_run": None, "errors": 0}

def save_state(s):
    if STATE_F.exists():
        shutil.copy(STATE_F, BACKUP_D/f"state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        for old in sorted(BACKUP_D.glob("state_*.json"))[:-30]:
            old.unlink()
    json.dump(s, open(STATE_F, "w"), indent=2, default=str)

# ----------------------------------------------------------- DATOS+SEÑAL -----
def load_params():
    if not PARAMS_F.exists():
        raise SystemExit("❌ Falta cassandra_live_params.json (generar en Kaggle, ver README)")
    d = json.load(open(PARAMS_F))
    due = pd.Timestamp(d.get("reopt_due", "2000-01-01"))
    if pd.Timestamp.now() > due:
        log.warning(f"⚠️ RE-OPTIMIZACION VENCIDA (due {due.date()}): regenerar params en Kaggle")
    return d["params"]

def load_market():
    end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = {}
    for tk in ["BTC-USD", "GC=F", "^IRX"]:
        s = yf.download(tk, start="2014-01-01", end=end, progress=False)["Close"]
        if isinstance(s, pd.DataFrame):
            s = s.squeeze()
        s = s.dropna()
        today = datetime.now(timezone.utc).date()
        if len(s) and s.index[-1].date() >= today:        # C3 guard vela parcial
            s = s.iloc[:-1]
        out[tk] = s
    if len(out["BTC-USD"]) < 1500:
        raise RuntimeError("datos BTC insuficientes")
    log.info(f"Datos OK | ultima vela completa BTC: {out['BTC-USD'].index[-1].date()}")
    return out

def compute_signals(data, params_by_seed):
    px = data["BTC-USD"]
    ret = np.log(px).diff().dropna()
    MI = ret.index
    P = px.reindex(MI).ffill()
    v20, v60 = ret.rolling(20).std(), ret.rolling(60).std()
    sig_vol = (v20-v60).ewm(span=42).mean().shift(1).fillna(0)            # C1
    sig_stress = ((v60-v60.rolling(252).mean())/(v60.rolling(252).std()+1e-8)
                 ).ewm(span=42).mean().shift(1).fillna(0)
    ma = P.rolling(BEAR_MA).mean()
    bear_now = bool(((P < ma) & (ma < ma.shift(BEAR_SLOPE))).shift(1).fillna(False).iloc[-1])  # C2

    def engine_last(p):
        maf = P.rolling(int(p['ma_fast'])).mean(); mas = P.rolling(int(p['ma_slow'])).mean()
        zf = ((P-maf)/(P.rolling(int(p['ma_fast'])).std()+1e-8)).fillna(0)
        zs = ((P-mas)/(P.rolling(int(p['ma_slow'])).std()+1e-8)).fillna(0)
        ts = (zs*p['z_slow_w']+zf*(1-p['z_slow_w'])).clip(-2,2)
        tn = ((ts-ts.rolling(252).mean())/(ts.rolling(252).std()+1e-8))
        wA = pd.Series(np.where(tn>0,p['wA_base']+p['wA_range']*(tn.clip(0,2)/2),
             p['wA_base']*np.exp(tn.clip(-3,0)*p['wA_decay'])),index=MI).shift(1).fillna(0)
        w3 = max(1-p['mom_w1']-p['mom_w2'],.05)
        ms = (ret.rolling(int(p['mom_lb1'])).sum()*p['mom_w1']+
              ret.rolling(int(p['mom_lb2'])).sum()*p['mom_w2']+
              ret.rolling(int(p['mom_lb3'])).sum()*w3).fillna(0)
        mz = ((ms-ms.rolling(252).mean())/(ms.rolling(252).std()+1e-8))
        rv = ret.rolling(int(p['vol_lb'])).std()*np.sqrt(365)
        wB = (mz.clip(0,2)/2*(p['vol_target']/(rv+1e-8)).clip(.2,2.5)).shift(1).fillna(0).clip(0,p['wB_max'])
        g = ret.clip(lower=0).rolling(p['rsi_lb']).mean()
        l_ = (-ret.clip(upper=0)).rolling(p['rsi_lb']).mean()
        rsi = 1-(1/(1+g/(l_+1e-8)))
        mr = pd.Series(np.where((rsi<p['rsi_buy'])&(zs>0),(p['rsi_buy']-rsi)/p['rsi_buy'],0.),index=MI)
        mr = np.where(rsi>p['rsi_exit'],0.,mr)
        wC = pd.Series(mr,index=MI).clip(0,p['wC_max']).shift(1).fillna(0)
        bsc = pd.Series(1/(1+np.exp(-sig_vol*p['bull_steep'])),index=MI)
        lsc = pd.Series(1/(1+np.exp(sig_vol*p['bull_steep']+sig_stress*1.5)),index=MI)
        wc = (wA*(p['wA_orch']+(1-p['wA_orch'])*bsc)+wB*bsc+wC*lsc*p['wC_orch'])
        mb = P.rolling(int(p['bear_lb'])).mean()
        bs2 = pd.Series(np.clip(1.+(mb/mb.shift(int(p['bear_slope_lb']))-1).fillna(0)*p['bear_sens'],
              p['bear_floor'],1.),index=MI).shift(1).fillna(1.)
        ksc = pd.Series(1/(1+np.exp(p['kill_steep']*(sig_stress.values-p['kill_thr']))),index=MI)
        return float((wc*bs2*ksc).clip(0,p['max_exp']).iloc[-1])

    sigs = [engine_last(p) for p in params_by_seed.values()]
    s_mean = float(np.mean(sigs))
    s_disp = float(np.std(sigs))
    # Agreement (pre-registro, parametros fijos)
    agree = 1 - min(1.0, s_disp/(s_mean+0.05))
    sig_B = s_mean*max(0.5, agree)
    return {"sig_ensemble": s_mean, "sig_dispersion": s_disp, "agree": agree,
            "sig_trackB": sig_B, "bear": bear_now,
            "stress": float(sig_stress.iloc[-1]),
            "seeds_signals": {k: round(v, 4) for k, v in zip(params_by_seed, sigs)}}

def refuge_daily_return(data):
    """R1: ~6% oro dinamico (inversa de vol cap 50) + T-bill. Retorno de AYER."""
    g = data["GC=F"]; irx = data["^IRX"]
    gr = g.pct_change()
    vg = (gr.rolling(60).std()*np.sqrt(252))
    w = ((1/(vg+1e-8))/((1/(vg+1e-8))+(1/0.01))).clip(0, GOLD_CAP).shift(1)
    tb = ((1+irx.reindex(g.index).ffill()/100.0)**(1/365)-1).shift(1)
    r = (w*gr+(1-w)*tb).dropna()
    return float(r.iloc[-1]) if len(r) else 0.0

# -------------------------------------------------------- OVERLAY+CONTROL ----
def governor(dd):
    if dd < DD_SOFT: return 1.0
    if dd < DD_HARD:
        return max(DD_FLOOR, 1.0-(dd-DD_SOFT)/(DD_HARD-DD_SOFT)*(1.0-DD_FLOOR))
    return DD_FLOOR

def sharpe_mult(recent):
    if len(recent) < SHARPE_WINDOW:
        return 1.0
    a = np.array(recent[-SHARPE_WINDOW:])
    if a.std() < 1e-12:
        return 1.0
    return 0.5 if (a.mean()*365)/(a.std()*np.sqrt(365)) < SHARPE_THRESHOLD else 1.0

def mc_zone(dd):
    if dd < 0.12: return "NORMAL"
    if dd < 0.18: return "TIPICO (mediana MC 15%)"
    if dd < 0.24: return "ALTO pero esperado (p95=24%)"
    return "⚠️ FUERA DE DISTRIBUCION — REVISAR SISTEMA"

# ----------------------------------------------------------- BINANCE ---------
def _retry(fn, n=3, base=2):
    last = None
    for k in range(n):
        try:
            return fn()
        except (BinanceAPIException, BinanceOrderException) as e:
            if "insufficient balance" in str(e).lower():
                raise
            last = e; log.warning(f"binance retry {k+1}/{n}: {e}")
            time.sleep(base*2**k)
        except Exception as e:
            last = e; log.warning(f"retry {k+1}/{n}: {type(e).__name__}: {e}")
            time.sleep(base*2**k)
    raise RuntimeError(f"binance fallo tras {n}: {last}")

def get_client():
    if not API_KEY or not API_SEC:
        raise SystemExit("❌ API keys no configuradas en .env (ver README paso 2)")
    return Client(API_KEY, API_SEC, testnet=True)

def balances(c):
    def f():
        acc = c.get_account()
        b = {x['asset']: float(x['free'])+float(x['locked']) for x in acc['balances']}
        px = float(c.get_symbol_ticker(symbol=SYMBOL)['price'])
        return b.get('BTC', 0.0), b.get('USDT', 0.0), px
    return _retry(f)

def min_notional(c):
    try:
        info = _retry(lambda: c.get_symbol_info(SYMBOL))
        for f_ in info.get('filters', []):
            if f_.get('filterType') in ('MIN_NOTIONAL', 'NOTIONAL'):
                return float(f_.get('minNotional', 10.0))
    except Exception:
        pass
    return 10.0

def market_order(c, side, usd):
    def f():
        if side == "BUY":
            return c.order_market_buy(symbol=SYMBOL, quoteOrderQty=round(usd, 2))
        px = float(c.get_symbol_ticker(symbol=SYMBOL)['price'])
        qty = round(usd/px, 5)
        if qty <= 0:
            raise ValueError("qty invalida")
        return c.order_market_sell(symbol=SYMBOL, quantity=qty)
    return _retry(f, n=2)

def append_csv(path, row):
    pd.DataFrame([row]).to_csv(path, mode='a', header=not path.exists(), index=False)

# ------------------------------------------------------------------ MAIN -----
def main():
    log.info("="*66)
    log.info(f"CASSANDRA LIVE — {datetime.now(timezone.utc).isoformat()} | DRY_RUN={DRY_RUN}")
    state = load_state()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_run") == today:
        log.info("ya corrio hoy — exit")
        return 0
    try:
        params = load_params()
        data = load_market()
        S = compute_signals(data, params)
        log.info(f"Señal ensemble: {S['sig_ensemble']*100:.2f}% | disp {S['sig_dispersion']*100:.2f}% "
                 f"| agree {S['agree']:.2f} | bear={S['bear']} | stress {S['stress']:.2f}σ")
        log.info(f"  por seed: {S['seeds_signals']}")

        if DRY_RUN:
            btc_held, usdt, px = 0.0, 10_000.0, float(data["BTC-USD"].iloc[-1])
            mn = 10.0
            log.info("DRY_RUN: balance simulado $10,000 USDT")
        else:
            c = get_client()
            mn = min_notional(c)
            btc_held, usdt, px = balances(c)

        total = usdt + btc_held*px
        if state["peak_equity"] <= 0:
            state.update(peak_equity=total, starting_balance=total, start_date=today,
                         trackB_equity=total, trackB_peak=total, refuge_equity=total)
            log.info(f"PRIMER RUN: base ${total:,.2f}. Si hay BTC inicial del testnet y la "
                     f"señal es ~0%, lo vendera — esperado.")
        state["peak_equity"] = max(state["peak_equity"], total)
        dd = max(0, 1-total/state["peak_equity"])
        g = governor(dd)
        bm = BEAR_RED if S["bear"] else 1.0
        sm = sharpe_mult(state["recent_returns"])
        target = min(S["sig_ensemble"]*g*bm*sm, 0.95)
        log.info(f"Total ${total:,.2f} | DD {dd*100:.2f}% [{mc_zone(dd)}] | "
                 f"gov {g:.2f} · bear {bm:.2f} · shp {sm:.2f} → target {target*100:.2f}%")

        cur = (btc_held*px)/max(total, 1)
        delta = target-cur
        action, usd, oid = "HOLD", 0.0, None
        if abs(delta) >= TOLERANCE:
            usd = abs(delta)*total
            if usd >= max(MIN_TRADE, mn*1.05):
                side = "BUY" if delta > 0 else "SELL"
                log.info(f"DECISION: {side} ${usd:,.2f}")
                if DRY_RUN:
                    action = f"{side}(dry)"
                else:
                    try:
                        o = market_order(c, side, usd)
                        action, oid = side, o.get('orderId')
                        btc_held, usdt, px = balances(c)
                        total = usdt+btc_held*px
                    except Exception as e:
                        log.error(f"orden fallo: {e}")
                        state["errors"] = state.get("errors", 0)+1
            else:
                log.info(f"trade ${usd:.2f} < minimo — skip")
        else:
            log.info(f"delta {delta*100:.2f}% < tolerancia — HOLD")

        # retornos + trackings paralelos
        if state["equity_history"]:
            prev = state["equity_history"][-1]["total"]
            if prev > 0:
                state["recent_returns"] = (state["recent_returns"]+[total/prev-1])[-200:]
        ref_r = refuge_daily_return(data)
        state["refuge_equity"] = state.get("refuge_equity", total)*(1+ref_r)
        # track B (agreement): simulado sobre el mismo precio, su propio governor
        bB = state.get("trackB_equity", total)
        state["trackB_peak"] = max(state.get("trackB_peak", bB), bB)
        ddB = max(0, 1-bB/state["trackB_peak"])
        tgtB = min(S["sig_trackB"]*governor(ddB)*bm*sharpe_mult(state.get("trackB_recent", [])), 0.95)
        if state["equity_history"]:
            btc_r = px/float(state["equity_history"][-1].get("btc_price", px))-1
            held_pct = state["equity_history"][-1].get("trackB_pct", 0.0)
            newB = bB*(1+held_pct*btc_r)
            state["trackB_recent"] = (state.get("trackB_recent", [])+[newB/bB-1])[-200:]
            state["trackB_equity"] = newB
        row = {"date": today, "total": total, "btc_held": btc_held, "usdt": usdt,
               "btc_price": px, "sig_ensemble": S["sig_ensemble"], "dispersion": S["sig_dispersion"],
               "agree": S["agree"], "target": target, "trackB_pct": tgtB,
               "trackB_equity": state["trackB_equity"], "refuge_equity": state["refuge_equity"],
               "dd": dd, "mc_zone": mc_zone(dd), "gov": g, "bear": bm, "sharpe_m": sm,
               "action": action, "trade_usd": usd, "order_id": oid}
        state["equity_history"] = (state["equity_history"]+[row])[-400:]
        state["last_run"] = today
        append_csv(DAILY_F, row)
        if action not in ("HOLD",):
            append_csv(TRADES_F, row)
        save_state(state)
        log.info(f"RESUMEN: ${total:,.2f} | target {target*100:.1f}% | {action} | "
                 f"trackB ${state['trackB_equity']:,.0f} | refugio ${state['refuge_equity']:,.0f}")
        return 0
    except Exception as e:
        log.error(f"FATAL: {type(e).__name__}: {e}")
        log.error(traceback.format_exc())
        state["errors"] = state.get("errors", 0)+1
        save_state(state)
        return 1

if __name__ == "__main__":
    sys.exit(main())
