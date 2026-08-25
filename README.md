# Systematic Investment Research & Model Validation

A research project focused on systematic market modeling, model-selection discipline, robustness testing, and forward paper validation.

**Status:** historical model selection and validation completed; forward validation ongoing.

## What this repository demonstrates

- A six-seed ensemble built from two disjoint three-seed groups.
- A preserved historical research record of approximately 90-110 Optuna studies with 500 trials per study.
- A one-pass 2023-2026 holdout protocol after model selection.
- Between-seed dispersion reduced from 16.2% to 2.4% in the adopted ensemble design.
- A companion 2,000-simulation block bootstrap using 20-day blocks to characterize return and drawdown distributions.
- A recovered forward paper-validation engine that can run without order placement in `DRY_RUN=true` mode and, when explicitly configured, can interact only with Binance Spot Testnet.

The project is presented as research and validation work, not as a claim of guaranteed investment performance.

## Repository structure

```text
src/
  paper_validation_engine.py   Recovered forward paper-validation engine
config/
  model_params.json            Frozen six-seed parameter package
docs/
  methodology.md               Research design and architecture
  validation.md                Validation machinery and preserved results
  limitations.md               Reproducibility boundaries and unresolved work
.env.example                   Safe environment template
requirements.txt               Python dependencies
SECURITY.md                    Credential and execution-safety notes
```

## Research design

The model combines trend, momentum, and mean-reversion components with risk overlays. Production parameters are aggregated across six seeds. The research process used disjoint seed groups before adopting the union ensemble, then applied a one-pass holdout and block-bootstrap stress analysis.

The forward engine uses completed daily market data, shifts signal inputs where required to reduce look-ahead risk, tracks ensemble dispersion, applies drawdown and bear-regime controls, and records a shadow agreement-weighted variant for comparison.

See [`docs/methodology.md`](docs/methodology.md) and [`docs/validation.md`](docs/validation.md).

## Reproducibility status

This repository contains the recovered forward engine and frozen parameter package. It does **not** contain the original historical optimization driver or the original Cónclave result artifacts. Those files were lost after the historical research phase, so the recorded optimization count and Monte Carlo results are preserved research records rather than results that can currently be regenerated end-to-end from this repository alone.

For that reason, headline CAGR/MAR claims are intentionally omitted here. Preserved records contain a drawdown discrepancy between historical summaries, and full cost realism plus a formal Deflated Sharpe Ratio over the complete search process remain open validation items.

## Running safely

Create a virtual environment, install the dependencies, copy `.env.example` to `.env`, and leave `DRY_RUN=true` unless you intentionally want to test against Binance Spot Testnet.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/paper_validation_engine.py
```

No real-capital exchange endpoint is configured in the recovered engine. Never commit credentials.

## Disclaimer

This repository is for research, education, and portfolio demonstration. It is not investment advice and does not establish a validated predictive edge or future performance.
