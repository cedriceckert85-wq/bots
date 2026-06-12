# SPEC CODEX - Challenger gegen SOLID und RISK (Paper, v0.1)

Status: DRYRUN/Paper. Keine Alpaca-Anbindung, keine echten Orders.

Ziel: CODEX soll SOLID und RISK risikoadjustiert outperformen. Outperformance
wird nicht durch stumpf mehr Hebel gesucht, sondern durch drei Dinge:

1. bessere Entry-Selektion als SOLIDs breiter Momentum-Korb,
2. weniger Klumpen-/Hebelrisiko als RISK,
3. harte Fail-closed-Disziplin wie beide Referenzbots.

Die Referenzbots bleiben unveraendert. CODEX ist ein Challenger im selben
Bot-Ordner und nutzt dieselbe Stufe-1-Abrechnung (`scripts/trade_eval.py`),
aber ein eigenes Journal: `data/codex_journal.json`.

## Gelernte Regeln aus SOLID/RISK

SOLID:
- Staerke: Evidenzdisziplin, Long-only, Risiko-Gates, weniger Drawdown.
- Schwaeche: sehr defensiv, viele No-Trade-Naechte, langsame Rotation,
  moeglicherweise zu wenig Beta in risk_on-Regimen.
- Wichtigste Lehre: Open-/Limit-Bias und Corporate-Action-Probleme duerfen
  nicht ignoriert werden; Zahlen muessen aus der Pipeline kommen.

RISK:
- Staerke: hoher Renditehebel in starken Regimen, klares TQQQ-Sleeve,
  Konzentration statt beliebiger Streuung.
- Schwaeche: High-Beta-Klumpen, TQQQ kann SOLID zwar schlagen, aber bei
  Regimebruch schnell viel Rueckstand erzeugen.
- Wichtigste Lehre: Kill-Switches duerfen nie am LLM haengen; Entry-Risiko
  muss schon vor dem Journal deterministisch begrenzt sein.

CODEX uebernimmt die Architektur beider Bots:

Quant-Snapshot -> Entscheider -> Journal -> Eval -> Review.

CODEX vermeidet Microcaps, IPOs, Buzz-Peaks, Averaging-down, Daytrading,
nicht dokumentierte Trades, selbst erfundene Kurse oder Levels und
Alpaca-Spiegelung vor explizitem Sign-off.

## Mandat

Sim-Konto: 100.000 USD.
Risiko pro Trade: 1,5 Prozent = 1.500 USD Stufe 1.
Maximal offene Positionen: 4.
Maximal neue Entries pro Lauf: 1.
Richtung: Long-only in Stufe 1.
Benchmark: SPY, SOLID und RISK.

CODEX soll aggressiver als SOLID, aber stabiler als RISK sein:

- In risk_on: konzentrierte Qualitaets-Momentum-Trades.
- In neutral: nur aussergewoehnlich gute Kandidaten oder kein Trade.
- In risk_off: keine neuen Entries.

## Hypothesen

H1: Ein enger, anti-crowding-gefilterter Momentum-Kern aus 3-4 liquiden
Large-Cap-Leadern hat bessere Expectancy als ein breiter Momentum-Korb, weil
er schwache Nachruecker, Buzz-Spikes und korrelierte Halbleiter-Klumpen meidet.

H2: Bestaetigungs-Entries per Stop ueber dem Schlusskurs reduzieren falsche
Pullback-Fills gegenueber Limit-Entries. Damit wird eher echte Fortsetzung als
fallendes Messer gekauft.

H3: CODEX schlaegt RISK risikoadjustiert, wenn TQQQ-Exposure nur als spaeterer
registrierter Trial aktiviert wird. Stufe 1 verzichtet bewusst auf TQQQ,
solange RISK diesen Beta-Hebel bereits testet.

Falsifikation:
- n < 30 abgeschlossene Trades: Rauschen.
- n >= 30: vorlaeufige Expectancy je Engine.
- n >= 60 und Expectancy <= 0R: Engine pausieren.
- Drawdown >= 15 Prozent: keine neuen Entries, Pflichtreview.
- Drawdown >= 20 Prozent: Bot-Stopp bis Freigabe.

## Engine A - Quality Momentum Confirmed

Quelle: `data/quant_snapshot.json`.

Kandidat muss alle Filter bestehen:

- `ueberSma200 == true`
- `mom12_1 >= 40`
- `-15 <= dist52wHochPct <= -0.2`
- `atrPct <= 8`
- `volRatio <= 2.5`
- `dollarVol20dMio >= 50`
- nicht bereits offen in CODEX
- nicht bereits als identischer aktiver Trade in SOLID/RISK, ausser der
  CODEX-Score ist aussergewoehnlich hoch

Scoring:

- Momentum-Rang: hoeher ist besser.
- 52W-Hoch-Naehe: ideal ist ein Leader nahe Hoch, aber nicht im Exact-Chase.
- Volatilitaet: moderate ATR wird bevorzugt; extreme ATR wird bestraft.
- Volumen: liquide Titel werden bevorzugt.
- Anti-Cluster: pro Korrelations-/Themencluster maximal 1 offener Trade.

Entry:

- `entryTyp = "stop"`
- `entry = close + 0.25 * ATR14`
- `stop = close - 2.25 * ATR14`
- `tp = entry + 2.5 * (entry - stop)`
- `maxHaltezeitTage = 12`
- 1R = 1.500 USD

Begruendung: CODEX will nicht in Schwaeche hinein limitiert werden. Ein Trade
soll erst starten, wenn der Titel nach dem Snapshot weiter Staerke zeigt.

## Engine B - Verified Drift

Stufe 1: nur Watchlist/Log, keine automatischen Entries.

Grund: Ohne frische, zweifach verifizierte Quellen waere News-Drift ein
Schein-Edge. CODEX darf hier nur handeln, wenn spaeter eine Pipeline
EDGAR-/Quellenfelder maschinell liefert oder ein manueller Review-Lauf mit
Quellen-URLs erfolgt. Bis dahin ist Engine B bewusst deaktiviert.

## Engine C - Regime Sleeve

Stufe 1: deaktiviert.

RISK testet bereits TQQQ. CODEX soll nicht nur eine zweite TQQQ-Kopie sein.
Ein spaeterer Trial darf QQQ/TQQQ aktivieren, aber erst nach 20 CODEX-A-Trades
oder 30 Kalendertagen, Review der RISK-TQQQ-Ergebnisse und dokumentiertem
Parameter-Reset.

## Risiko-Gates

Neue Entries sind verboten, wenn eines gilt:

- Snapshot fehlt oder hat kein `asOf`,
- `regime.spyZone != "risk_on"`,
- CODEX hat bereits 4 offene/wartende Trades,
- CODEX hat 3 Verluste in Folge,
- Drawdown seit Start >= 15 Prozent,
- Kandidat wuerde einen bestehenden Cluster verdoppeln,
- Ticker ist in einem der Referenzbots bereits aktiv und CODEX haette keinen
  klaren, andersartigen Entry-Grund.

Der Entscheider darf Kandidaten streichen, nie Risiko erhoehen.

## Betrieb

Dry-run:

`python scripts/codex_challenger.py`

Journal-Eintrag schreiben:

`python scripts/codex_challenger.py --write`

Abrechnung:

`python scripts/trade_eval.py`

## Outperformance-Regeln

CODEX gewinnt nicht durch einzelne Glueckstreffer. Bewertet wird Rendite vs.
SPY, SOLID und RISK, Max Drawdown, Erwartungswert in R, No-Trade-Qualitaet,
Anteil verfallener Entries und Korrelation zu RISK/TQQQ.

Wenn CODEX nur dieselben Trades wie RISK macht, hat CODEX sein Mandat verfehlt.
Wenn CODEX weniger verdient als SOLID bei hoeherem Drawdown, hat CODEX sein
Mandat ebenfalls verfehlt.
