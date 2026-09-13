# Regime-Gated Microtrading on ADAUSDT — Research Record

**Author:** Alan Ricardo Huerta Rincón  
**Research period:** 13 March 2026 through 13 September 2026  
**Document status:** Public research record  
**Version:** 1.0  
**Frozen-model implementation:** intentionally excluded from this public document  

---

## Abstract

This study documents the development of a deliberately simple regime-gated trading architecture for ADAUSDT. The research began with a microtrading objective: repeatedly enter and exit a highly liquid cryptocurrency while accounting for transaction costs, attempt to maintain tolerable drawdown, and seek returns substantially above a passive benchmark. Early work explored increasingly aggressive synthetic portfolio configurations, including spot and futures variants. Those experiments were useful for understanding the interaction between turnover, fees, leverage and drawdown, but they were not accepted as empirical evidence because Monte Carlo output cannot establish that a market edge exists.

The research therefore moved to a more restrictive empirical design. The central question became: can a simple strategy remain dormant during unfavorable market structure and activate only when price behavior becomes sufficiently directional? The goal was explicitly not to maximize in-sample fit. Instead, the study reduced the model to a small number of interpretable state variables and a state machine.

The final public research architecture uses three regime variables: price relative to a 20-period exponential moving average, the relationship between the 20-period and 50-period exponential moving averages, and a 10-period Kaufman Efficiency Ratio. A regime gate determines whether the trading engine is asleep or active. A later refinement introduces a probation state only for newly born trend regimes, motivated by a false activation observed in May 2026.

In the six-month research window, the ungated trading rule produced materially positive return but experienced a large drawdown. Adding the regime gate reduced trading frequency sharply and materially reduced drawdown while retaining most of the positive return. The May false activation was then diagnosed separately rather than redesigning the global model. The distinguishing feature was not the absolute Efficiency Ratio but the maturity of the EMA20/EMA50 relationship: the May activation occurred immediately after a fresh crossover, whereas the August activation occurred after the positive EMA structure had been established for weeks. This led to the probation-state refinement.

The principal conclusion is architectural rather than promotional: the most valuable component was not a more complicated predictor, but a mechanism for refusing to trade when the market structure was not favorable. The model remains research-only. Reported results are historical and do not establish future profitability.

---

## 1. Research objective

The original objective was to build a Binance-compatible trading system capable of making small purchases and sales while explicitly incorporating fees, keeping drawdown controlled, and targeting a meaningful positive return.

The investigation quickly exposed a basic constraint: extremely small price targets can be mathematically invalid once round-trip trading fees, spread, slippage and imperfect fills are included. A strategy cannot create a durable edge merely by trading more frequently. If the expected price movement captured per trade is smaller than execution friction, higher turnover accelerates losses.

The research objective was therefore reframed from:

> maximize the number of microtrades

into:

> maximize net expectancy while remaining inactive when market structure does not justify trading.

A second constraint was added later in the research process: avoid excessive filter proliferation. The project intentionally rejects the idea that a profitable six-month backtest should be manufactured by stacking many indicators until historical losses disappear. The architecture instead seeks a small number of variables with direct economic interpretation.

---

## 2. Research progression

The project developed through several stages.

### 2.1 Synthetic feasibility stage

Initial internal experiments used synthetic trade distributions and Monte Carlo paths to study whether combinations of win rate, average win, average loss, turnover and position size could theoretically produce returns above 15% while preserving low drawdown.

Those experiments established several useful facts:

1. Fees dominate very small price targets.
2. A high win rate is not strictly necessary if the payoff distribution is asymmetric.
3. Increasing exposure can dramatically increase expected return, but it also changes tail behavior faster than ordinary summary metrics suggest.
4. Spot and futures should not be modeled as the same strategy with different leverage because their fee structures, long/short capability, funding and liquidation dynamics differ.
5. Synthetic results cannot be treated as proof of real market profitability.

For this reason, none of the synthetic annual return figures are considered validated performance in this public research record.

### 2.2 Asset selection

The empirical study focused on ADAUSDT. ADA was chosen because it provides continuous crypto trading, substantial liquidity, large enough directional moves to test regime persistence, and enough noise to expose whether a simple trend-state filter can avoid unfavorable periods.

The central empirical window was:

**13 March 2026 to 13 September 2026.**

A warm-up period preceding the main evaluation window is required whenever EMA50 is used. This is necessary to prevent artificial initialization at the start boundary.

### 2.3 Simplification stage

The research deliberately moved away from a large microstructure feature stack. The core idea became:

- use a simple regime engine to decide whether trading is allowed;
- let execution logic optimize fees and fills;
- do not confuse execution features with predictive filters;
- preserve the same trading logic across months rather than fitting month-specific behavior.

This separation is central to the project.

---

## 3. Baseline trading concept

The empirical baseline used a simple causal directional rule. The intent was not to claim this is the only possible execution rule, but to create a sufficiently simple fixed mechanism so that the effect of the regime gate could be isolated.

The baseline logic can be summarized as:

- observe completed market information;
- enter exposure only according to the fixed rule;
- exit when the rule no longer authorizes exposure;
- charge transaction costs;
- never alter parameters because of knowledge of later outcomes.

The baseline six-month reconstruction used a single consistent historical series and causal timing after an earlier preliminary calculation was found to be inconsistent. The corrected baseline result is the one preserved here.

### 3.1 Corrected baseline research result

| Metric | Baseline ungated result |
|---|---:|
| Research window | 13 Mar 2026 – 13 Sep 2026 |
| Net return | **+23.62%** |
| Maximum drawdown | **-29.57%** |
| Approx. transactions | 92 |
| Approx. round trips | 46 |
| Approx. invested days | 82 |
| Approx. Sharpe | 1.08 |
| Return / max drawdown | 0.80x |

A prior preliminary figure of +30.83% was discarded after the series, timing and warm-up procedure were reconstructed consistently. The corrected figure of +23.62% is the research record used for comparison in this document.

The important observation is that the baseline produced attractive positive return but used an uncomfortably large amount of drawdown. The research did not attempt to solve this by adding stops, dozens of indicators or trade-specific exceptions. Instead, it asked whether the same strategy could simply remain inactive during market states where its expected behavior was poor.

---

## 4. Regime-gate hypothesis

The regime-gate hypothesis is:

> The strategy does not need to trade continuously. If its payoff is concentrated in persistent directional regimes, then inactivity during low-efficiency or structurally immature regimes can improve the return-to-drawdown relationship even if total gross opportunity decreases.

This is fundamentally different from trying to forecast every next price movement.

The regime engine is therefore a permission system, not a price target model.

---

## 5. Regime variables

The gate uses only three variables.

### 5.1 Price versus EMA20

The first condition is:

```text
Close > EMA20
```

This asks whether current price is above its shorter-term exponential trend estimate.

It does not by itself establish a durable trend. It is simply a local directional condition.

### 5.2 EMA20 versus EMA50

The second condition is:

```text
EMA20 > EMA50
```

This asks whether the shorter-term trend estimate is above the slower trend estimate.

Compared with a single price/EMA relationship, this condition attempts to avoid activating solely because of a one-day price spike.

### 5.3 Kaufman Efficiency Ratio, 10 periods

The third variable is the 10-period Efficiency Ratio:

```text
ER10 = abs(Close[t] - Close[t-10]) /
       sum(abs(Close[i] - Close[i-1]), i=t-9..t)
```

The interpretation is straightforward:

- ER close to 1: most of the path traveled in one net direction;
- ER close to 0: large amount of movement but little net displacement.

The gate threshold is:

```text
ER10 > 0.35
```

This is intended to distinguish directional movement from choppy movement without attempting to forecast the next return.

---

## 6. Frozen public regime logic

The public regime condition is:

```text
Close > EMA20
AND
EMA20 > EMA50
AND
ER10 > 0.35
```

The model does not immediately become active after one qualifying observation.

### Activation confirmation

Two consecutive qualifying closes are required before the strategy transitions from sleep to active.

Conceptually:

```text
SLEEP
  |
  | 2 consecutive fully-qualified closes
  v
ACTIVE
```

### Deactivation confirmation

The strategy does not shut down after a single noisy observation. It returns to sleep after two consecutive closes in which at least two of the three regime conditions fail.

This hysteresis is intended to reduce rapid state flipping.

---

## 7. Six-month regime-gated result

Applying the regime gate to the same research interval materially changed the distribution of activity.

| Metric | Baseline ungated | Regime-gated |
|---|---:|---:|
| Net return | **+23.62%** | **+20.17%** |
| Maximum drawdown | **-29.57%** | **-9.37%** |
| Approx. transactions | 92 | **16** |
| Approx. round trips | 46 | **8** |
| Approx. invested days | 82 | **14** |
| Approx. Sharpe | 1.08 | **1.31** |
| Return / max drawdown | 0.80x | **2.15x** |

The gated version sacrificed approximately 3.45 percentage points of return while reducing maximum drawdown by approximately 20.2 percentage points.

Relative drawdown reduction was roughly:

```text
1 - 9.37 / 29.57 ≈ 68%
```

This is the central empirical result of the study.

The important outcome is not that the gate maximized absolute return. It did not. The result is useful because the system remained inactive for long periods yet retained most of the profitable behavior while sharply reducing realized drawdown and turnover.

---

## 8. Approximate monthly behavior

Using an illustrative starting equity of 100,000 monetary units, the gated strategy's reconstructed month-by-month behavior was approximately:

| Period | Predominant state | Approx. return | Approx. P&L | Approx. equity |
|---|---|---:|---:|---:|
| 13–31 Mar | Sleep | 0.00% | 0 | 100,000 |
| Apr | Sleep | 0.00% | 0 | 100,000 |
| May | Brief activation | **-3.51%** | -3,509 | 96,491 |
| Jun | Sleep | 0.00% | 0 | 96,491 |
| Jul | Sleep | 0.00% | 0 | 96,491 |
| Aug | Active | **+18.85%** | +18,186 | 114,678 |
| 1–13 Sep | Active then sleep | **+4.79%** | +5,493 | **120,171** |

Values are rounded research reconstructions, so multiplication of rounded monthly figures may not exactly reproduce the headline period result.

This table reveals why the gate matters: the system's most valuable action for several months was doing nothing.

---

## 9. Why August mattered

The August period produced a large share of the positive return because price behavior became directionally persistent rather than simply volatile.

The research did not encode the calendar month. The gate did not contain an `August` rule. Instead, August happened to satisfy the structural conditions the gate was designed to detect.

The profitable behavior was driven by a small number of large favorable moves rather than a high proportion of winning trades. This is consistent with a convex trend-capture profile: many small losses can be acceptable if occasional persistent moves are substantially larger.

One reconstructed cycle from 18 August to 22 August produced an approximate net gain of +29.44% on the active sleeve. This single event illustrates why win rate should not be used as the primary model-quality metric.

The relevant statistic is expectancy:

```text
expectancy = P(win) * avg_win - P(loss) * avg_loss - costs
```

A strategy can remain profitable with a low win rate if the right tail is sufficiently large and execution costs are controlled.

---

## 10. The May false activation

The regime gate was not perfect. It briefly activated in May and generated an approximate -3.51% loss.

Rather than adding a broad new indicator to improve the whole six-month backtest, the research isolated the exact structural difference between the May false activation and the August successful activation.

### 10.1 What the simple conditions saw in May

May contained a rapid positive rebound. That rebound was sufficient to produce:

- price above EMA20;
- EMA20 above EMA50;
- ER10 above 0.35.

The gate therefore behaved correctly according to its original definition.

The false activation was not caused by a calculation error. It revealed a missing distinction in the state model.

### 10.2 Diagnostic comparison

The key research comparison was:

| Feature near activation | May | August |
|---|---:|---:|
| ER10 | ~0.652 | ~0.390 |
| EMA20 > EMA50 | Yes | Yes |
| EMA20/EMA50 separation | ~+0.21% | ~+1.76% |
| Age of positive EMA relationship | ~0 days | ~28 days |
| Interpretation | Fresh crossover | Mature positive structure |

The surprising feature is that May actually had the higher Efficiency Ratio.

This means a simple rule such as "raise the ER threshold" would have been the wrong response. It could have rejected valid regimes while failing to address the actual structural issue.

The useful difference was **regime maturity**.

In May, the EMA20/EMA50 relationship was newly born. In August, it had existed for weeks.

---

## 11. Probation-state refinement

The research therefore adds one localized state-machine refinement:

> A fresh EMA20/EMA50 positive crossover is not immediately granted full capital.

This does not alter the three core regime variables. It changes only position authorization during newly born regimes.

The state machine becomes:

```text
               qualifying regime
SLEEP ------------------------------------+
  |                                       |
  | if EMA structure is mature            | if EMA20/EMA50 crossover is recent
  v                                       v
ACTIVE 100%                         PROBATION 25%
                                            |
                           +----------------+----------------+
                           |                                 |
                     survives 5 closes                regime fails
                           |                                 |
                           v                                 v
                      ACTIVE 100%                          SLEEP
```

### 11.1 Probation sizing

The frozen research proposal uses:

```text
probation exposure = 25% of normal active exposure
probation duration = 5 completed daily closes
```

If the regime remains valid through probation, exposure is allowed to transition to 100% of the normal active allocation.

If the regime breaks before probation ends, the system returns to sleep.

### 11.2 Why sizing rather than total rejection

A new trend may be genuine. Completely rejecting every fresh crossover would create a different problem: the strategy could systematically miss the early part of profitable new regimes.

Using reduced exposure recognizes uncertainty without assuming the signal is worthless.

This is a general state-machine principle:

```text
new regime != mature regime
```

---

## 12. Counterfactual impact on May

The May loss in the prior gated model was approximately -3.51% at full active exposure.

If the same unfavorable event had occurred entirely during 25% probation exposure, a first-order sizing approximation is:

```text
-3.51% * 0.25 ≈ -0.88%
```

This is an approximation, not a completed replay. Exact results depend on execution timing, compounding and when the probation state exits.

If August and September were otherwise unaffected, the resulting period return would be expected to improve toward approximately +23.45% rather than +20.17%.

**This +23.45% figure is explicitly a counterfactual estimate, not a finalized backtest result.**

The distinction matters. The probation architecture is frozen as the next model candidate, but it still requires a complete causal replay before its performance statistics are promoted from estimate to historical result.

---

## 13. Why this is not intended as month-specific fitting

The May refinement could easily become overfitting if encoded as an arbitrary collection of details that merely describe May 2026.

The project therefore rejects rules such as:

- require a particular calendar month;
- forbid activation after a fixed historical price level;
- add a special ADA threshold derived only from May;
- create multiple new oscillators to erase the observed loss;
- tune the probation duration repeatedly until the six-month return is maximized.

Instead, the refinement is deliberately generic:

> freshly crossed trend structure receives reduced confidence until it demonstrates persistence.

This mechanism can be evaluated on other assets and time windows without changing its interpretation.

---

## 14. State-machine design

The model is best understood as a state machine rather than a continuous score.

### 14.1 SLEEP

Characteristics:

- no ordinary trading exposure;
- indicators continue updating;
- capital remains uncommitted to the directional strategy;
- no attempt is made to predict every daily move.

The SLEEP state is not a failure state. It is the default state.

### 14.2 PROBATION

Characteristics:

- used only when a qualifying regime emerges from a recently crossed EMA20/EMA50 structure;
- normal allocation is reduced to 25%;
- the regime must survive five completed daily closes to mature;
- failure returns the model to SLEEP.

### 14.3 ACTIVE

Characteristics:

- full normal strategy allocation is authorized;
- the underlying trading engine operates without changing its own predictive logic;
- two consecutive deactivation confirmations are required before returning to SLEEP.

This separation prevents the execution engine from carrying the burden of regime discovery.

---

## 15. Causality and look-ahead controls

Any future implementation or validation must preserve the following rules.

### 15.1 Completed data only

State transitions are based only on completed candles. No intraday high, low or close that is not yet finalized may be used as if it were known.

### 15.2 EMA warm-up

EMA50 must be initialized with data preceding the formal evaluation window. Starting EMA50 from the first test day would distort the early regime state.

### 15.3 No same-bar foresight

If a state is determined using a closing price, the implementation must not assume that a trade was executed earlier at that same close with certainty. The execution convention must be explicit and consistent.

### 15.4 Costs are mandatory

Transaction costs cannot be omitted merely because the strategy trades infrequently. Any production replay should include:

- maker/taker fee assumptions;
- spread;
- slippage;
- partial fills where relevant;
- futures funding if the system is adapted to perpetual contracts.

---

## 16. Spot versus futures implications

Earlier synthetic work compared spot and futures architectures. Those simulations suggested that futures can provide greater capital efficiency because of lower nominal fee structures in some tiers, long/short capability and leverage. However, leverage amplifies model error and tail risk.

The empirical regime study in this document is intentionally separated from that leverage decision.

The regime gate answers:

> Should the strategy be allowed to operate?

Leverage answers:

> How much notional exposure should be allocated once operation is allowed?

These should not be conflated.

A robust deployment program would first validate the gate and base expectancy at low or unlevered exposure, then evaluate leverage separately with funding, liquidation distance, gap behavior and execution stress.

---

## 17. Metrics that matter

The project does not optimize solely for return.

Primary evaluation metrics include:

### Net return

All returns should be measured after modeled transaction costs.

### Maximum drawdown

```text
DD[t] = equity[t] / running_max_equity[t] - 1
```

The regime-gated model's major advantage in this study is drawdown compression.

### Return / maximum drawdown

A simple capital-efficiency diagnostic:

```text
return / abs(max_drawdown)
```

In the six-month reconstruction:

- baseline: approximately 0.80x;
- gated: approximately 2.15x.

### Turnover

Lower turnover is useful only when it preserves expectancy. In this study the gate reduced transactions from approximately 92 to 16.

### Invested time

The strategy was invested for a minority of the period. This matters because a system capable of remaining flat can allocate capital elsewhere or simply avoid unnecessary exposure.

### Win rate

Win rate is tracked but is not a primary objective. The research showed that a small number of large favorable moves can dominate many small losing trades.

### Profit factor and expectancy

Future detailed replays should prioritize:

```text
profit_factor = gross_profit / abs(gross_loss)
```

and per-trade net expectancy after all costs.

---

## 18. What the study does not establish

This research does **not** establish that the model will produce +20%, +23% or any positive return in the future.

It does not establish:

- statistical significance across independent market regimes;
- robustness across many cryptocurrencies;
- robustness across equities, commodities or FX;
- tick-level execution feasibility;
- capacity at large notional size;
- live fill quality;
- stable future Binance fees;
- future funding behavior;
- immunity to exchange outages;
- immunity to market gaps;
- profitability under leveraged futures execution;
- that the probation refinement improves unseen data.

The period is only six months. A single favorable trend episode can materially affect headline return.

---

## 19. Validation roadmap

The correct next research steps are intentionally narrower than adding new features.

### 19.1 Freeze before testing

The candidate state machine should be frozen before evaluating additional periods.

Frozen research parameters:

```text
EMA fast = 20
EMA slow = 50
Efficiency Ratio lookback = 10
Efficiency Ratio threshold = 0.35
Activation confirmations = 2 closes
Deactivation confirmations = 2 closes
Probation allocation = 25%
Probation length = 5 closes
```

These should not be changed after observing additional historical windows unless a new model version is declared.

### 19.2 Out-of-sample chronological extensions

Test immediately adjacent periods without re-optimization.

Preferred sequence:

1. preceding six months;
2. preceding 12 months;
3. multiple complete market cycles;
4. forward paper validation.

### 19.3 Cross-asset validation

Apply the same frozen parameters to liquid assets such as BTCUSDT, ETHUSDT and SOLUSDT.

The purpose is not to demand identical returns. The question is whether the regime-state behavior remains economically coherent.

### 19.4 Execution replay

A serious execution test should use at least minute-level data and preferably trades/order-book data if the deployed trading engine operates at microstructure horizons.

### 19.5 Cost stress

Results should be recomputed under multiple cost assumptions rather than a single optimistic fill model.

### 19.6 Parameter-neighborhood test

Robustness should be checked around the frozen point, not by selecting the best nearby value. For example, EMA and ER neighborhoods can reveal whether performance collapses immediately outside the chosen parameters.

A robust model should generally show a region of reasonable behavior rather than one isolated optimum.

---

## 20. Research discipline rules

To reduce overfitting, the project adopts the following rules.

1. New filters require a specific failure mechanism, not a desire for higher return.
2. Every new parameter creates a new model version.
3. Historical losses are not automatically defects.
4. A drawdown is acceptable if it is consistent with the expected payoff distribution and risk budget.
5. A filter that removes losses but also removes the right tail must be rejected.
6. Model changes should improve an interpretable failure mode.
7. Synthetic Monte Carlo results are risk illustrations, not empirical alpha evidence.
8. Counterfactual estimates are labeled as estimates until replayed.
9. Reconstructed results must state their data granularity and execution convention.
10. Live deployment requires forward paper validation.

---

## 21. Public versus private boundary

This document intentionally contains enough information to explain the research logic and reproduce the regime concept.

The private frozen package is intended to hold the operational specification, including the exact state transition implementation, execution interface, risk-engine wiring, production invariants, deployment configuration, model hash/version policy and any future exchange-specific execution logic.

The separation is deliberate:

- **Public:** research question, methodology, historical observations, limitations and general regime architecture.
- **Private:** deployable frozen specification and operational implementation details.

No API credentials or exchange secrets should ever be committed to either repository.

---

## 22. Current model status

### Research model

**Status:** promising historical result, not production validated.

### Core regime gate

**Status:** frozen for further validation.

### Probation refinement

**Status:** frozen candidate; exact six-month replay still required before its estimated improvement is promoted to a finalized historical metric.

### Real-money deployment

**Status:** not approved by this research record.

---

## 23. Summary of preserved results

| Model | Net return | Max DD | Transactions | Interpretation |
|---|---:|---:|---:|---|
| Ungated baseline | **+23.62%** | **-29.57%** | ~92 | Positive return, poor drawdown efficiency |
| Regime gate | **+20.17%** | **-9.37%** | ~16 | Most return retained, drawdown materially reduced |
| Regime gate + probation | **~+23.45% estimated** | Pending exact replay | Lower risk in fresh regimes | Frozen candidate, estimate only |

The strongest completed historical finding is therefore not the highest return number. It is the change in the relationship between return, drawdown and time in market after the regime gate was introduced.

---

## 24. Final research conclusion

The project began as a high-turnover microtrading problem and evolved into a market-state problem.

The six-month research suggests that the strategy's edge, if it exists, is not uniformly distributed through time. Attempting to trade continuously increased drawdown and turnover without being necessary to capture the most valuable price movement in the sample.

A simple three-variable gate materially improved the historical return-to-drawdown relationship. The gate did not need to know the calendar month, predict news or classify thousands of microstructure states. It only needed to identify when directional structure was sufficiently coherent.

The May false activation then exposed a more specific issue: a newly born positive EMA structure is different from a mature positive regime. The resulting probation state is intentionally narrow and interpretable. It does not redesign the strategy around one losing month; it reduces confidence during a structurally immature state.

The model should now be treated as frozen for out-of-sample validation. The next evidence should come from new data, not additional in-sample parameter tuning.

---

## Data and source notes

Historical price exploration used ADAUSDT market-history sources associated with Binance pricing during the research process. Future reproducibility work should prefer Binance's official public historical archives (`data.binance.vision`) and preserve checksums of every raw input archive.

Fee assumptions should be versioned by date and account tier because Binance spot and futures fee schedules can change.

Useful primary endpoints and references for future replication:

- Binance public historical data: https://data.binance.vision/
- Binance Spot API documentation: https://developers.binance.com/docs/binance-spot-api-docs
- Binance USD-M Futures API documentation: https://developers.binance.com/docs/derivatives/usds-margined-futures
- Binance trading fee schedule: https://www.binance.com/en/fee/trading

---

## Disclaimer

This repository is a research and engineering record. It is not investment advice, a promise of future performance, or evidence that a historical trading edge will persist. Cryptocurrency trading can result in substantial or total loss, particularly when leverage is used. Historical backtests and reconstructed simulations are sensitive to data quality, execution assumptions, transaction costs and market regime.