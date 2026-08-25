# Methodology

## Model architecture

The recovered research records describe a 28-parameter engine per seed with three principal signal components:

1. **Trend:** double moving-average and z-score structure.
2. **Momentum:** multiple horizons combined with volatility targeting.
3. **Mean reversion:** RSI-based oversold exposure.

The signal layer is supplemented by a bear scaler and stress kill-switch. The adopted production package contains six seeds: `42, 137, 777, 7, 1001, 2024`.

## Ensemble design

The validation protocol split the seeds into two disjoint groups:

- Group A: `42, 137, 777`
- Group B: `7, 1001, 2024`

The groups were evaluated independently before the six-seed union was adopted. The preserved results record a reduction in between-seed dispersion from **16.2% to 2.4%**.

## Historical search

The preserved execution record reports approximately **90-110 Optuna studies x 500 trials**. Decision rules were frozen before the final data decisions, and the process included a one-pass 2023-2026 holdout.

The original historical optimization driver is no longer available, so this search cannot currently be reproduced byte-for-byte from the public repository.

## Risk overlays

The recovered forward engine includes:

- drawdown governor;
- bear-regime exposure reduction;
- rolling Sharpe-decay multiplier;
- maximum exposure cap;
- ensemble-dispersion tracking;
- shadow agreement-weighted signal tracking.

## Forward validation

`src/paper_validation_engine.py` is a recovered daily paper-validation engine. With `DRY_RUN=true`, it calculates signals and simulates balances without interacting with Binance. With `DRY_RUN=false`, the recovered code creates a client with `testnet=True` and therefore targets Binance Spot Testnet rather than a real-capital endpoint.
