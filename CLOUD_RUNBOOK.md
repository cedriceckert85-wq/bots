# Cloud-Runbook fuer das Bots-Repo

Ziel: SOLID, RISK, CODEX und DAYTRADER laufen ueber GitHub Actions, also ohne
laufenden PC.

Remote:

`https://github.com/cedriceckert85-wq/bots`

## Workflows

- `Quant-Snapshot`: Mo-Fr nach US-Schluss, schreibt `data/quant_snapshot.json`.
- `Trade-Auswertung SOLID+RISK+CODEX`: nach US-Schluss, sync/eval fuer
  SOLID/RISK und Yahoo-Fallback fuer CODEX.
- `Alpaca-Orders SOLID+RISK+CODEX`: platziert/synct Bracket-Orders fuer
  SOLID/RISK/CODEX.
- `CODEX Challenger`: schreibt maximal einen Paper-Trade je Snapshot.
- `DAYTRADER Signal`: prueft kurz nach US-Open ORB-Signale und platziert
  optionale Alpaca-Paper-Brackets.
- `DAYTRADER Auswertung`: synct DAYTRADER waehrend/nach US-Handel.
- `DAYTRADER Close Guard`: versucht im 15:45-15:59 New-York-Fenster offene
  DAYTRADER-Paper-Positionen zu schliessen.

## Secrets

Keys gehoeren niemals ins Repo. In GitHub unter
Settings -> Secrets and variables -> Actions -> New repository secret:

- `ALPACA_SOLID_KEY`
- `ALPACA_SOLID_SECRET`
- `ALPACA_RISK_KEY`
- `ALPACA_RISK_SECRET`
- `ALPACA_CODEX_KEY`
- `ALPACA_CODEX_SECRET`
- `ALPACA_DAYTRADER_KEY`
- `ALPACA_DAYTRADER_SECRET`

Zuordnung der neu gelieferten Paper-Konten:

- DAYTRADER-Screenshot: `ALPACA_DAYTRADER_KEY` und `ALPACA_DAYTRADER_SECRET`.
- Challenger-Screenshot: `ALPACA_CODEX_KEY` und `ALPACA_CODEX_SECRET`.
- Dritter Screenshot: zeigt nur den Key, aber keinen Secret. Ohne Secret ist
  er nicht aktiv nutzbar. Sobald der Secret da ist, kann er fuer SOLID oder RISK
  verwendet werden, je nachdem welches Paper-Konto dort noch fehlt.

Optional lokal setzen:

```powershell
.\scripts\setup_github_secrets.ps1
```

Das Script enthaelt keine Keys. Es fragt interaktiv nach den Werten und setzt
sie als GitHub Actions Secrets.

## Sicherheit

- `.gitignore` blockiert lokale Key-Dateien, `.env` und `config/secrets/`.
- Alle neuen DAYTRADER/CODEX-Orders sind Paper-only.
- Kein Live-Intraday-Trading ohne eigenen Review.
- DAYTRADER schreibt kein Signal, wenn der ORB-Trigger bereits passiert ist.
- GitHub-Cron kann verzoegern; deshalb prueft das Script das Signalfenster und
  der Close-Guard die echte New-York-Uhrzeit.

## Manuelle Ausloesung

Jeder Workflow hat `workflow_dispatch` und kann im GitHub-Tab "Actions" manuell
gestartet werden.
