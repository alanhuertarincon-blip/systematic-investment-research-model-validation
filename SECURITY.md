# Security

## Credentials

No API keys or secrets belong in this repository. Use environment variables through a local `.env` file, which is ignored by Git.

A recovered private environment file was explicitly excluded from the public package during the publication audit. Treat any historical testnet credential that existed in backups as compromised and rotate it before further use.

## Execution scope

The recovered exchange code creates a Binance client with `testnet=True`. The safe default in `.env.example` is `DRY_RUN=true`.

Do not modify this repository to target real-capital endpoints without an independent security, execution, and regulatory review.
