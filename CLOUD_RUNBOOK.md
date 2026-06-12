# Cloud-Runbook fuer das Bots-Repo

Ziel: SOLID, RISK, CODEX und DAYTRADER laufen ueber GitHub Actions, also ohne
laufenden PC.

Remote:

`https://github.com/cedriceckert85-wq/bots`

## Workflows

- `Quant-Snapshot`: Mo-Fr nach US-Schluss, schreibt `data/quant_snapshot.json`.
- `Trade-Auswertung SOLID+RISK+CODEX`: nach US-Schluss, sync/eval fuer
  SOLID/RISK und Yahoo-Fallback fuer CODEX.
- `Alpaca-Orders SOLID+RISK`: platziert/synct Bracket-Orders fuer SOLID/RISK.
- `CODEX Challenger`: schreibt maximal einen Paper-Trade je Snapshot.
- `DAYTRADER Signal`: prueft kurz nach US-Open ORB-Signale, Paper-only.
- `DAYTRADER Auswertung`: wertet DAYTRADER waehrend/nach US-Handel aus.

## Secrets

Keys gehoeren niemals ins Repo. In GitHub unter
Settings -> Secrets and variables -> Actions -> New repository secret:

- `ALPACA_SOLID_KEY`
- `ALPACA_SOLID_SECRET`
- `ALPACA_RISK_KEY`
- `ALPACA_RISK_SECRET`

Reserviert fuer spaeter, noch nicht live verdrahtet:

- `ALPACA_DAYTRADER_KEY`
- `ALPACA_DAYTRADER_SECRET`

CODEX bleibt in v0.1 ohne Alpaca.

## Sicherheit

- `.gitignore` blockiert lokale Key-Dateien, `.env` und `config/secrets/`.
- DAYTRADER ist Paper-only. Kein Live-Intraday-Trading ohne eigenen Review.
- DAYTRADER schreibt kein Signal, wenn der ORB-Trigger bereits passiert ist.
- GitHub-Cron kann verzoegern; deshalb sind alle Intraday-Live-Orders bis auf
  Weiteres deaktiviert.

## Manuelle Ausloesung

Jeder Workflow hat `workflow_dispatch` und kann im GitHub-Tab "Actions" manuell
gestartet werden.
