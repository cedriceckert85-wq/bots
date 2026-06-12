# Bot-Flotte: SOLID + RISK + CODEX + DAYTRADER

SOLID und RISK sind live in Stufe 1 (Paper) seit 12.06.2026. Beide wurden aus
den Deep-Researches zu Medien-Einfluss, Strategien, Bot-Architektur und
Medien-Signalen abgeleitet. Vollstaendige Designs: `SPEC_SOLID.md` und
`SPEC_RISK.md`. Aktuell gilt fuer beide die vereinfachte Stufe 1 in
`STUFE1.md`.

CODEX ist der neue Paper-Challenger gegen SOLID/RISK. Ziel ist
risikoadjustierte Outperformance durch Quality-Momentum, Anti-Crowding und
Bestaetigungs-Entries. Details: `SPEC_CODEX.md`, `AGENT_CODEX.md`.

DAYTRADER ist ein separater Intraday-Paper-Bot auf Basis von 5-Minuten-Opening-
Range-Breakout und "Stocks in Play". Details: `SPEC_DAYTRADER.md`,
`AGENT_DAYTRADER.md`.

| | SOLID | RISK | CODEX | DAYTRADER |
|---|---|---|---|---|
| Mandat | Nur belegte Edges: Long-only-Momentum (12-1 + 52W-Hoch) + News-Drift-Satellit | Kontrolliert aggressiv: Engines A Momentum-Leader, B Volumen-Spike, C TQQQ-Sleeve (D Shorts deaktiviert) | Challenger: Quality-Momentum, Anti-Crowding, bestaetigte Entries | Intraday ORB auf Stocks in Play |
| Risiko/Trade | 1 % (1.000 $) | 2 % (2.000 $), max 5 Positionen | 1,5 % (1.500 $), max 4 Positionen | 0,35 % (350 $), max 1 Trade/Tag |
| Alpaca-Paper | Konto Nr. 4 (Bracket-Orders) | Konto Nr. 5 (Bracket-Orders) | Eigene Paper-Bracket-Orders via `ALPACA_CODEX_*` | Eigene Intraday-Paper-Bracket-Orders via `ALPACA_DAYTRADER_*` |
| Benchmark | SPY | SPY + SOLID | SPY + SOLID + RISK | SPY + SOLID + RISK + CODEX |

## Bauphasen

Phase 0: Specs, Quant-Datenpipeline, Journale, GUI, Alpaca-Konten und Routinen
fuer SOLID/RISK stehen.

Stufe 1: Diskrete Bracket-Trades nach `STUFE1.md`, abgerechnet von der
erprobten Flotten-Maschinerie (`scripts/alpaca_sync.py` echte Fills,
`scripts/trade_eval.py` Yahoo-Fallback). Statistik wird bei Umstieg auf
Phase 2 zurueckgesetzt.

CODEX v0.2: Paper-Alpaca bereit. Der Challenger schreibt
`data/codex_journal.json`; `scripts/alpaca_sync.py` platziert/synct Bracket-
Orders, sobald `ALPACA_CODEX_KEY` und `ALPACA_CODEX_SECRET` als Secrets gesetzt
sind.

DAYTRADER v0.2: Paper-Alpaca bereit. Der Bot schreibt
`data/daytrader_journal.json`, platziert optionale Intraday-Bracket-Orders via
`--alpaca` und nutzt einen Close-Guard gegen Overnight-Positionen.

Phase 2: volle Specs mit `eval_v2.py`, share-basierter Equity-Buchfuehrung,
Mark-to-Market, Band-/Roll-Exits, Splits, `risk-gate`/`risk-eval`,
EDGAR-/FINRA-Feeds und Grenzfalltests.

## Architektur

```
GitHub Action (23:37) -> quant_snapshot.json: Momentum-Ranking, Regime, ATR, Spikes
        v liest
Cloud-Entscheider SOLID/RISK bzw. CODEX-Skript
        v schreibt Journal-Trades (Entry/Stop/Ziel)
GitHub Action (03:26) -> Bracket-Orders fuer SOLID/RISK/CODEX
GitHub Action (22:16) -> Fills syncen + Yahoo-Abrechnung + Statistik
```

Teil der EPMT-Flotte:
https://cedriceckert85-wq.github.io/review/vergleich.html

## CODEX dry-run

```
python scripts/codex_challenger.py
python scripts/codex_challenger.py --write
python scripts/trade_eval.py
```

## DAYTRADER dry-run

```
python scripts/daytrader.py
python scripts/daytrader.py --write
python scripts/daytrader.py --evaluate
python scripts/daytrader.py --write --evaluate --alpaca
python scripts/daytrader.py --evaluate --alpaca --flatten
```
