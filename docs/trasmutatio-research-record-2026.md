# Trasmutatio — ADAUSDT Regime-Gated Trading Research

**Author:** Alan Ricardo Huerta Rincón  
**Research period:** 13 March 2026 through 13 September 2026  
**Public name:** **Trasmutatio**  
**Document status:** Public research record / canonical project index  
**Model family:** long/flat regime-gated systematic trading  

<!-- ☿  🜍  🜔 -->
<!-- V.I.T.R.I.O.L. :: Visita Interiora Terrae Rectificando Invenies Occultum Lapidem. -->
<!-- SOLVE: decompose movement into direction and path. COAGULA: permit exposure only when structure persists. -->

## Abstract

**Trasmutatio** is the public name of the ADAUSDT regime-gating research program developed during the March–September 2026 investigation. The project began as a microtrading problem and evolved into a market-state problem: rather than forcing continuous participation, the system attempts to remain dormant when structure is unfavorable and authorize exposure only when price behavior becomes sufficiently directional and mature.

The public empirical architecture remains deliberately small. It uses price relative to EMA20, EMA20 relative to EMA50, and a 10-period Kaufman Efficiency Ratio. The principal completed historical result was not an increase in raw return, but a large compression of drawdown and turnover: the corrected ungated reconstruction returned **+23.62%** with **-29.57%** maximum drawdown, while the regime-gated version returned **+20.17%** with **-9.37%** maximum drawdown. The later probation refinement was motivated by a false May activation and is frozen as the next model candidate; its approximately **+23.45%** six-month value remains a counterfactual estimate pending exact replay.

The name *Trasmutatio* refers only to the project's conceptual transformation: raw movement is decomposed, filtered through state, and recombined into authorized exposure. It does not alter the quantitative rules or claim any non-quantitative predictive mechanism.

<!-- nigredo / albedo / citrinitas / rubedo — process, not prediction -->

---

## 1. Research thesis

The project's central thesis is:

> A strategy does not need to trade continuously. If its payoff is concentrated in persistent directional regimes, refusing to participate in structurally poor periods can improve the relationship between return, drawdown and turnover.

This reframes the system from a continuous predictor into a **permission engine**.

The gate does not attempt to forecast every next candle. It determines whether the underlying trading rule is authorized to operate.

---

## 2. Empirical window

Primary research interval:

**13 March 2026 → 13 September 2026**

Asset:

**ADAUSDT**

A causal warm-up preceding the formal test interval is required for EMA50. Completed candles only are used for state determination.

The long-form technical record that preceded the Trasmutatio naming remains preserved unchanged for audit continuity at [`ada-regime-gated-microtrading-study-2026.md`](ada-regime-gated-microtrading-study-2026.md). This file is the canonical branded index; the legacy record is retained rather than rewritten so the research history remains inspectable.

---

## 3. Core regime structure

The public gate uses exactly three conditions:

```text
Close > EMA20
EMA20 > EMA50
ER10 > 0.35
```

with:

```text
ER10 = abs(Close[t] - Close[t-10]) /
       sum(abs(Close[i] - Close[i-1]), i=t-9..t)
```

The Efficiency Ratio measures how much of the traveled path became net displacement. A value nearer one represents more directional movement; a value nearer zero represents movement that largely cancels itself.

Two consecutive fully qualified daily closes are required before ordinary activation. Two consecutive closes on which at least two of the three regime conditions fail are required for ordinary deactivation.

<!-- The first operation is separation; the second is conjunction. -->

---

## 4. State machine

The model is organized around three operational states:

```text
SLEEP
PROBATION
ACTIVE
```

### SLEEP

The default state. No ordinary strategy exposure is authorized, while indicators continue updating.

### PROBATION

Used only when a qualifying regime appears close to a fresh bullish EMA20/EMA50 crossover. Normal exposure is reduced to **25%** while the new structure proves persistence.

### ACTIVE

Full normal strategy allocation is authorized. The underlying directional rule remains unchanged.

The current probation candidate requires a newly born regime to survive **five completed daily closes** before receiving full normal exposure.

<!-- Saturn guards the threshold; Mercury carries the signal; Sol is exposure. -->

---

## 5. Completed six-month comparison

| Metric | Ungated baseline | Trasmutatio regime gate |
|---|---:|---:|
| Net return | **+23.62%** | **+20.17%** |
| Maximum drawdown | **-29.57%** | **-9.37%** |
| Approx. transactions | 92 | **16** |
| Approx. round trips | 46 | **8** |
| Approx. invested days | 82 | **14** |
| Approx. Sharpe | 1.08 | **1.31** |
| Return / max DD | 0.80x | **2.15x** |

The gate sacrificed roughly **3.45 percentage points** of historical return while reducing maximum drawdown by roughly **20.2 percentage points**.

Approximate relative drawdown compression:

```text
1 - 9.37 / 29.57 ≈ 68%
```

The strongest completed finding is therefore the transformation of the return/drawdown relationship, not the largest headline return.

---

## 6. Month-level behavior

For an illustrative starting equity of 100,000 monetary units:

| Period | Predominant state | Approx. return | Approx. equity |
|---|---|---:|---:|
| 13–31 Mar | SLEEP | 0.00% | 100,000 |
| Apr | SLEEP | 0.00% | 100,000 |
| May | brief activation | **-3.51%** | 96,491 |
| Jun | SLEEP | 0.00% | 96,491 |
| Jul | SLEEP | 0.00% | 96,491 |
| Aug | ACTIVE | **+18.85%** | 114,678 |
| 1–13 Sep | ACTIVE → SLEEP | **+4.79%** | **120,171** |

The model's most valuable action for much of the interval was inactivity.

---

## 7. Why May and August differed

The May false activation and August successful activation both satisfied the original gate, but their trend structures were not equally mature.

| Feature near activation | May | August |
|---|---:|---:|
| ER10 | ~0.652 | ~0.390 |
| EMA20 > EMA50 | Yes | Yes |
| EMA20/EMA50 separation | ~+0.21% | ~+1.76% |
| Age of positive EMA relationship | ~0 days | ~28 days |
| Interpretation | Fresh crossover | Mature positive structure |

May is important because it demonstrates why simply increasing the ER threshold would be the wrong repair: May actually displayed the larger ER. The failure mechanism was **regime immaturity**, not insufficient directional efficiency.

Trasmutatio therefore leaves the general gate unchanged and modifies only capital authorization around fresh crossovers.

---

## 8. Probation refinement

The frozen candidate refinement is:

```text
SLEEP
  |
  | fully qualified regime
  v
Is bullish EMA20/EMA50 structure recent?
  |
  +-- no  --> ACTIVE 100%
  |
  +-- yes --> PROBATION 25%
                 |
                 +-- survives 5 closes --> ACTIVE 100%
                 |
                 +-- fails -------------> SLEEP
```

The first-order counterfactual effect on the May loss is:

```text
-3.51% × 0.25 ≈ -0.88%
```

If August and September were otherwise unchanged, the period result would move toward approximately **+23.45%**. This value is explicitly an **estimate**, not a finalized replay statistic.

<!-- 1 · 4 · 3 · 2 : separate, purify, mature, return -->

---

## 9. Anti-overfitting discipline

Trasmutatio adopts the following research rules:

1. New filters require a specific observed failure mechanism.
2. Every predictive parameter change creates a new model version.
3. Historical losses are not automatically defects.
4. Synthetic Monte Carlo output is risk illustration, not empirical alpha evidence.
5. Counterfactual estimates remain labeled until causally replayed.
6. Parameter-neighborhood tests measure stability; they do not select a new optimum after the fact.
7. New evidence should come from additional data rather than continued tuning of March–September 2026.
8. Safety overrides may reduce exposure but may never increase the model's authorized exposure.

---

## 10. Causality requirements

Any implementation carrying the Trasmutatio name must preserve:

- completed candles only;
- causal EMA warm-up;
- no future-bar information;
- no retroactive same-bar fills;
- explicit transaction costs;
- explicit execution timing;
- preserved state-transition chronology.

For daily-bar replay, signals generated from close `t` must be applied only to the next tradable observation.

---

## 11. Public/private boundary

The public record documents the research logic, historical observations, failure analysis and state architecture.

The private frozen package contains the normative operational specification, exact state-transition implementation, machine-readable configuration, test invariants, version policy and future exchange-specific execution wiring.

The private implementation must never contain exchange credentials committed to source control.

---

## 12. Current status

| Component | Status |
|---|---|
| Core regime gate | **Frozen for validation** |
| Six-month gated reconstruction | **Completed** |
| Probation refinement | **Frozen candidate** |
| Exact probation replay | Pending |
| Cross-asset validation | Pending |
| Forward paper validation | Pending |
| Real-money production approval | **Not established by this record** |

---

## 13. Preserved results

| Model | Net return | Max DD | Interpretation |
|---|---:|---:|---|
| Ungated baseline | **+23.62%** | **-29.57%** | Positive return, inefficient drawdown |
| Trasmutatio gate | **+20.17%** | **-9.37%** | Most return retained with materially lower DD |
| Trasmutatio + probation | **~+23.45% estimated** | Pending exact replay | Reduced capital during fresh regimes |

The compact machine-readable result manifest is [`trasmutatio-results.csv`](trasmutatio-results.csv).

---

## 14. Interpretation

The project began by asking how to trade more frequently and ended by discovering that the more useful question was when **not** to trade.

Trasmutatio is therefore a transformation of permission rather than a promise of prediction:

```text
raw price movement
        ↓
structural decomposition
        ↓
regime qualification
        ↓
capital authorization
        ↓
execution
```

The model should now remain frozen while new evidence is collected.

<!-- quod est inferius est sicut quod est superius — symmetry here is metaphor only, never a trading signal -->
<!-- 🜂  🜄  🜁  🜃 -->

---

## Sources and reproducibility

Future reproduction should preferentially use Binance official public historical archives and preserve checksums for all raw inputs.

- Binance public historical data: https://data.binance.vision/
- Binance Spot API documentation: https://developers.binance.com/docs/binance-spot-api-docs
- Binance USD-M Futures API documentation: https://developers.binance.com/docs/derivatives/usds-margined-futures
- Binance trading fee schedule: https://www.binance.com/en/fee/trading

---

## Disclaimer

This repository is a research and engineering record. It is not investment advice, a guarantee of future return, or evidence that a historical edge will persist. Cryptocurrency trading can result in substantial or total loss. Historical results are sensitive to data quality, execution assumptions, transaction costs and market regime.