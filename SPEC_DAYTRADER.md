# SPEC DAYTRADER - Intraday ORB Paper-Bot (v0.1)

Status: DRYRUN/Paper. Keine Alpaca-Anbindung, keine echten Orders.

Ziel: Ein Daytrader-Bot, der nur dann handelt, wenn ein intraday-taugliches,
regelbasiertes Setup vorliegt. Der Bot soll nicht durch Aktivitaet gewinnen,
sondern durch sehr wenige, klar definierte Trades.

## Internet-Research, das in diese Spec eingeflossen ist

1. FINRA Notice 26-10 (20.04.2026): Die alte Pattern-Day-Trader-Logik und
   das 25.000-USD-Minimum werden durch neue Intraday-Margin-Standards ersetzt.
   Wichtig fuer uns: Intraday-Risiko bleibt explizit margin-/exposure-getrieben
   und muss laufend begrenzt werden. Quelle:
   https://www.finra.org/rules-guidance/notices/26-10
2. Heston/Korajczyk/Sadka (Journal of Finance 2010): Intraday-Returns zeigen
   wiederkehrende Muster; kurzfristige Reversals koennen durch Liquiditaet,
   Spread/Bid-Ask-Bounce und Timingkosten getrieben sein. Konsequenz: kein
   blindes Scalping, keine Mini-Ziele im Spread-Rauschen.
   https://arxiv.org/abs/1005.3535
3. Mesfin (arXiv 2026): Viele reine OHLCV-Intraday-Signale scheitern unter
   realistischen Kosten/Walk-forward-Kriterien. Konsequenz: DAYTRADER muss
   defensiv fail-closed sein und Kosten/Slippage als Kernrisiko behandeln.
   https://arxiv.org/abs/2605.04004
4. Zarattini/Aziz (SSRN 2023, rev. 2025): Opening Range Breakout (ORB) kann
   in QQQ/TQQQ-Tests profitabel sein, aber die Resultate haengen stark an
   Ausfuehrung, Hebel und Broker-Limits. Konsequenz: ORB ist der Startpunkt,
   aber ohne TQQQ-Hebel in v0.1.
   https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622
5. Zarattini/Barbon/Aziz (SSRN 2024, rev. 2025): 5-Minuten-ORB auf "Stocks in
   Play" war in ihrer US-Aktien-Studie deutlich staerker als beliebiges
   Daytrading. Konsequenz: DAYTRADER handelt nur abnormal aktive Titel.
   https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284

## Mandat

Sim-Konto: 100.000 USD.
Richtung: Long-only in v0.1.
Risiko pro Trade: 0,35 Prozent = 350 USD.
Max. Trades pro Tag: 1.
Max. Tagesverlust: 0,7 Prozent = 700 USD.
Max. offene Positionen: 1.
No overnight: Jede Position wird spaetestens am selben Handelstag geschlossen.

DAYTRADER tritt gegen SOLID, RISK und CODEX an, aber mit anderer Messlatte:
intraday Expectancy nach Slippage. Ein hoher Umsatz mit kleinen Verlusten ist
ein Scheitern, kein "aktiver Bot".

## Engine A - 5-Minuten-Opening-Range-Breakout auf Stocks in Play

Quelle: 5-Minuten-Kerzen von Yahoo Chart API, Paper-only.

Universum:

- Ticker aus `data/quant_snapshot.json`,
- plus SPY/QQQ/IWM/TQQQ nur als Kontext; TQQQ wird in v0.1 nicht gehandelt.

Ein Titel ist "in play", wenn mindestens eines gilt:

- Gap vom Vortagsschluss >= 1 Prozent,
- erste 15-Minuten-Volumen >= 8 Prozent des approximierten 20-Tage-Tagesvolumens,
- EOD-`volRatio` aus dem letzten Snapshot >= 2.

Entry-Setup:

- Opening Range = erste 5-Minuten-Kerze des regulaeren US-Handels.
- Long-Trigger = Opening-Range-High + 0,05 Prozent Preisbuffer.
- Stop = Opening-Range-Low - 0,05 Prozent Preisbuffer.
- Ziel = Entry + 2R.
- Kein Trade, wenn Risikodistanz < 0,15 Prozent oder > 2,0 Prozent des Entry.
- Kein Trade, wenn Preis aktuell unter VWAP liegt.
- Kein Trade nach 15:30 New-York-Zeit neu starten.

Exit:

- Stop oder Ziel, konservativ Stop zuerst wenn beides in gleicher Kerze.
- Zeit-Exit am Tagesende, keine Overnight-Position.
- Bei Datenfehler: kein neuer Trade; offene Paper-Position wird im Log als
  "needs_manual_review" markiert, nicht schoengerechnet.

## Risiko-Gates

Neue Trades sind verboten, wenn eines gilt:

- keine intraday Kerzen,
- weniger als 4 regulaere 5-Minuten-Kerzen,
- `data/quant_snapshot.json` fehlt,
- DAYTRADER hat heute bereits einen Trade geschrieben,
- `statistik.bremseAktiv == true`,
- aktuelle Verlustserie >= 2,
- ein Trade wuerde Tagesverlustlimit verletzen,
- Kandidat ist TQQQ oder ein gehebeltes/inverses Produkt.

## Journal

Eigenes Journal: `data/daytrader_journal.json`.

Statuswerte:

- `signal`: ORB-Signal wurde geschrieben, Entry noch nicht ausgeloest.
- `offen`: Entry wurde im Paper gefuellt.
- `gewonnen`: Ziel erreicht.
- `verloren`: Stop erreicht.
- `zeit_exit`: Tagesende-Exit.
- `verfallen`: Signal nicht ausgeloest.
- `needs_manual_review`: Datenlage unklar.

## Betrieb

Dry-run:

`python scripts/daytrader.py`

Journal schreiben:

`python scripts/daytrader.py --write`

Auswertung offener/signalisierter DAYTRADER-Trades:

`python scripts/daytrader.py --evaluate`

Beides:

`python scripts/daytrader.py --write --evaluate`

## Abbruchkriterien

- n < 30: keine Aussage.
- n >= 30 und Expectancy <= 0R: Engine pausieren.
- 2 Verluste in Folge: naechster Tag nur Dry-run.
- 3 Regelverstoesse in 30 Tagen: Bot pausiert bis Prompt-/Code-Review.

## Nicht-Ziele

- Kein Scalping.
- Keine Martingale-/Nachkauf-Logik.
- Keine echten Orders.
- Keine Broker-/Margin-Optimierung.
- Keine TQQQ-Kopie von RISK.
