# Validation record

## Preserved checks

The historical validation machinery records the following safeguards:

- look-ahead canary: perturbing the final close did not alter the final-day signal (`delta = 0.0`);
- median-semantics assertion for odd-sized seed groups;
- carry-identity check with numerical error of approximately `4.6e-15`;
- a 16-point semantic audit covering decision rules, holdout handling, disjoint seeds, carry reporting, partial-candle protection, exports, and dead-code checks.

## Ensemble result

Two disjoint three-seed ensembles were evaluated before the six-seed union was adopted. Preserved records report between-seed dispersion falling from **16.2% to 2.4%**.

## Holdout and bootstrap

The selected framework was evaluated once on a 2023-2026 holdout. A companion block-bootstrap analysis used **2,000 simulations** with **20-day blocks** to estimate the distribution of returns and drawdowns.

## What is not claimed

The public repository does not claim that these checks establish a deployable investment edge. In particular:

- the full historical search driver is missing;
- some historical performance summaries disagree on exact drawdown;
- full slippage/funding/tax realism was outside the original instrument;
- a formal Deflated Sharpe Ratio over the complete research search process remains pending;
- forward validation is ongoing.
