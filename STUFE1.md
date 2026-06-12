# Stufe 1 — Live-Schaltung 12.06.2026 (datierte Präzisierung, Pre-Registration-Disziplin)

Auf Nutzer-Kommando vom 12.06.2026 sind SOLID und RISK **live (Paper)** — in einer
vereinfachten Stufe 1, die von der erprobten Flotten-Maschinerie (Bracket-Orders +
konservative Yahoo-Abrechnung) korrekt abgerechnet werden kann. Die volle Spec-Mechanik
(share-basierte Portfolio-Buchführung, Roll-Updates, risk-gate, EDGAR-Feed) bleibt
Phase 2. Abweichungen von den Specs sind hier vollständig dokumentiert — die Statistik
der Stufe 1 wird bei Umstieg auf Phase 2 zurückgesetzt (Regeländerung = Statistik-Reset).

## Stufe-1-Regeln SOLID (1R = 1.000 $ = 1 %)
- **Quelle:** ausschließlich `data/quant_snapshot.json` (fail-closed bei stale asOf).
- **Momentum-Kern (diskret statt Roll-Portfolio):** Bis zu 3 gleichzeitig offene
  Momentum-Trades. Kandidaten = Top 10 des `momentumRanking` (bereits gefiltert:
  über SMA200, Dollar-Volumen > 50 Mio.), zusätzlich `dist52wHochPct >= -10`.
  Entry: Limit = close × 1,01 (füllt zur Eröffnung; Gap > 1 % = kein Fill = Gap-Guard).
  Stop = close − 2,5 × ATR14. Ziel = close + 5 × ATR14 (CRV 2,0). maxHaltezeitTage = 20.
- **News-Drift-Satellit:** Max. 1 Trade/Nacht, nur bei via WebSearch ZWEIFACH verifizierter,
  fundamentaler Positiv-News (< 24 h) zu einem Universums-Ticker über SMA200.
  Entry Limit close × 1,01, Stop 2 × ATR, Ziel 4 × ATR, maxHaltezeitTage = 5.
- **Regime-Drossel:** spyZone risk_off → keine neuen Entries. neutral → max. 1 neuer Trade.
- **Kein Trade ist ein gültiges Ergebnis.** Buzz-/Spike-Titel (volRatio ≥ 3) sind für
  SOLID gesperrt (Attention-Spike-Evidenz).

## Stufe-1-Regeln RISK (1R = 2.000 $ = 2 %)
- **Caps (hart):** max. 5 offene Positionen gesamt, max. 2 neue Trades/Nacht,
  Verlustserien-Bremse (3 in Folge → keine neuen Trades bis Review).
- **Engine A — Momentum-Leader:** Kandidaten = Top 5 des Rankings mit dist52wHochPct ≥ −5.
  Entry: Stop-Order = close × 1,005 (Breakout-Bestätigung). Stop = close − 2 × ATR,
  Ziel = close + 5 × ATR (CRV 2,5). maxHaltezeitTage = 10.
- **Engine B — Volumen-Spike-Drift:** Kandidaten aus `volumenSpikes` (volRatio ≥ 2),
  nur mit positivem Schlusskurs-Tag UND per WebSearch verifizierter fundamentaler
  Ursache (kein Spike ohne Grund — Manipulationsschutz). Entry Limit close × 1,005,
  Stop 2 × ATR, Ziel 3 × ATR (CRV 1,5 — dokumentierte Abweichung lt. Spec).
  maxHaltezeitTage = 5. NIE wenn der Spike schon Tag 3+ der Story ist (Buzz-Peak).
- **Engine C — TQQQ-Sleeve:** Nur wenn ALLE Gates grün: spyZone = risk_on UND
  qqqZone = risk_on UND vixUnter25. Max. 1 TQQQ-Position. Entry Limit close × 1,01,
  Stop 2,5 × ATR, Ziel 5 × ATR, maxHaltezeitTage = 15. Gate-Bruch → risk-eval/Agent
  schließt am Folgelauf.
- **Engine D — Shorts: DEAKTIVIERT** (Datenquellen-Nachweis steht aus, siehe Spec).
- **Regime:** spyZone risk_off → nur Engine-B-Trades mit halbem Risiko, kein A/C.

## Gemeinsam
- **Journal-Schema — EXAKT dieses, keine eigenen Feldnamen erfinden** (Pflichtfelder,
  Abrechnung crasht sonst):
```json
{
  "id": "S-001 bzw. R-001 (fortlaufend)",
  "datumEmpfehlung": "YYYY-MM-DD",
  "aktie": "Firmenname",
  "ticker": "XXX",
  "yahooSymbol": "XXX",
  "richtung": "long",
  "engine": "momentum|newsdrift bzw. A|B|C",
  "entryTyp": "limit|stop",
  "entry": 0.0,
  "stop": 0.0,
  "tp": 0.0,
  "crv": 0.0,
  "maxHaltezeitTage": 0,
  "status": "wartet",
  "begruendung": "… (bei News-Trades mit Quellen-URLs)",
  "snapshotAsOf": "YYYY-MM-DD"
}
```
  `status` ist beim Anlegen IMMER "wartet" — Fills, Exits und Ergebnisse schreiben
  ausschließlich `scripts/alpaca_sync.py` (echte Bracket-Fills) bzw.
  `scripts/trade_eval.py` (Yahoo-Fallback). Status/Ergebnisse NIE von Hand ändern.
- Microcap-/IPO-Verbot ist durch das kuratierte Universum erzwungen. Earnings-Termine
  in den nächsten 2 Handelstagen → Ticker diese Nacht überspringen (WebSearch-Check).
- Schedule: Quant-Snapshot 23:37 → Entscheider SOLID 02:53 / RISK 03:08 → Orders 03:26
  → Auswertung 22:16 (alles Berlin-Zeit, Mo–Fr bzw. Di–Sa).
