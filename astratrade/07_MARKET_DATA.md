# 07 — Marktdaten: Anbieterbewertung und Datenarchitektur-Entscheidung

Zurück: [[00_HOME]] · Verwandt: [[08_DATA_CONTRACTS]], [[24_COST_MODEL]], [[29_SOURCE_LEDGER]]

Alle Fakten mit Quellen-IDs im [[29_SOURCE_LEDGER]]; Abrufdatum 2026-08-15. Preise sind
änderungsanfällig und vor Vertragsabschluss direkt zu verifizieren.

## 1. Alpaca als Broker-Datenquelle (Kernbefunde)

- Zwei Pläne: **Basic** (kostenlos; Echtzeit nur IEX ≈ wenige % des Marktvolumens) und
  **Algo Trader Plus, 99 USD/Monat** (SIP-Echtzeit, CTA+UTP = 100 % Marktvolumen)
  [Ledger AL-1/AL-2].
- Historische SIP-Bars sind auch auf Basic abrufbar, **außer den letzten 15 Minuten**
  [AL-4]. Historie „7+ Jahre" belegt; exakter Start (~2016) unverifiziert [AL-5].
- Rate Limits: Market Data 200 req/min (Basic) / bis 10.000 req/min (ATP);
  Trading API 200 req/min [AL-3, AL-14].
- Websocket: 1 Verbindung pro Account; Basic max. 30 Symbole für Trades/Quotes [AL-6].
- IEX- vs SIP-Trennung ist real und muss im Datenmodell erzwungen werden
  ([[08_DATA_CONTRACTS]] §1.2).
- Lizenz: Non-Professional-Display-Agreements; interne Speicherung üblich zulässig,
  Redistribution verboten — Wortlaut der PDFs **vor Go-Live lesen** [AL-7, UNVERIFIZIERT im Detail].

**Bewertung:** Alpaca-Daten sind als *Execution-nahe* Quelle (Live-Stream, letzte Bars,
Konsistenz mit dem Fill-Environment) sinnvoll, aber als **alleinige** Research-Basis
riskant: Historientiefe begrenzt, Korrektur-/Revisionstransparenz gering, und
Broker+Daten aus einer Hand ist ein Klumpenrisiko (Feed-Fehler unerkennbar ohne
Zweitquelle).

## 2. Anbietervergleich (Zusammenfassung der Recherche)

| Anbieter | Stärke | Schwäche | Kosten (Stand 08/2026) | Rolle für ASTRATRADE |
|---|---|---|---|---|
| Alpaca ATP | Live-SIP, brokernah, ein Vertrag | Historie ~2016+, PIT-Referenzdaten schwach, Klumpenrisiko | 99 $/M | Live-Stream + Execution-Konsistenz |
| Polygon/**Massive** (Rebrand 10/2025!) | 20+ J. Historie inkl. Delistings, **Flat Files ohne Rate Limit**, Corporate Actions | PIT-Versionierung der Referenzdaten nicht belegt; Rebrand-Deprecation-Risiko der alten API-Base | 29/79/199 $/M | **primäre historische Basis** (Advanced für Echtzeit optional) |
| Databento | direkte Börsen-Feeds, **PIT-Corporate-Actions + Security Master**, unbegrenzte 1m-OHLCV im Standardplan | Historie ab 2018 (Nasdaq), usage-based Kosten für Tick-Backfills | 199 $/M Standard + GB-Kosten | PIT-Goldstandard + echte Herkunfts-Redundanz |
| Tiingo | günstige EOD-Zweitmeinung | intraday nur IEX | 30–50 $/M | EOD-Cross-Check |
| Norgate | survivorship-freie Daily-Historie ab 1950, PIT-Indexmitgliedschaft | kein Intraday, Windows-Client-zentriert | ~630 $/Jahr (Platinum) | Option für lange Daily-Historie/Universe |
| Nasdaq Data Link (Sharadar), Intrinio | EOD/Fundamentals | Preise nicht öffentlich bzw. B2B | n/a | nur bei späterem Fundamentals-Bedarf |
| FRED/ALFRED + Treasury FiscalData | kostenlos; ALFRED = echte PIT-Vintages; Treasury = Public Domain | Serien-Lizenzen einzeln prüfen | 0 | Makro-/Zins-Features (nur ALFRED-Vintages!) |

## 3. Entscheidung (ADR-006, Confidence hoch)

**Zwei-Quellen-Prinzip von Anfang an:**

1. **Historische Research-Basis:** Massive/Polygon *Developer* (79 $/M; Upgrade auf
   Advanced 199 $/M erst wenn eigene Echtzeit-Zweitquelle gewünscht) — Bulk-Backfill
   der Daily+Minute-Bars und Corporate Actions über Flat Files ins Raw Archive.
2. **Live/Execution-Quelle:** Alpaca **Algo Trader Plus** (99 $/M) ab Paper-Phase 5 —
   damit Paper/Live-Signale auf SIP-Sicht laufen, nicht auf IEX-Restsicht. In
   Research-Phasen 1–4 genügt Alpaca Basic (SIP-Historie bis auf 15-Minuten-Fenster).
3. **Cross-Validierung:** täglicher Daily-Close-Diff Alpaca vs Massive (Toleranz 10 bps
   WARN / 25 bps BLOCK, [[08_DATA_CONTRACTS]] §5); Corporate Actions beider Quellen
   gegeneinander (Diff ⇒ manuelle Klärung vor Ex-Tag).
4. **Makro:** ausschließlich ALFRED-Vintage-Serien + Treasury FiscalData; FRED-Serien
   ohne Vintage sind für Features verboten (Revision Bias).
5. **Option (Neubewertung nach Phase 3):** Databento Standard als dritte Quelle, wenn
   Minute-Genauigkeit ab 2018 forschungskritisch wird; Norgate, falls Daily-Backtests
   vor 2003 oder PIT-Indexmitgliedschaften benötigt werden.

Trade-offs: +178 $/M Datenkosten in der Paper-Phase (Ledger in [[24_COST_MODEL]])
gegen Eliminierung des größten Einzelrisikos (unbemerkt fehlerhafter Single-Feed) und
saubere Trennung Research-Historie vs Live-Feed. Alternative „nur Alpaca" wurde wegen
Klumpenrisiko + Historientiefe verworfen; „nur Databento" wegen Historie ab 2018.

## 4. Feed-Semantik und Besonderheiten (für Engine und Validierung)

- **Timestamp-Semantik:** Bars werden mit Bar-*Open*-Zeit geführt; Anbieter-Konvention
  je Quelle im Manifest dokumentiert und im Normalizer vereinheitlicht (UTC).
- **Late Prints/Korrekturen:** SIP kennt Trade-Korrekturen und Late Prints; Daily-Bars
  gelten erst nach T+1-Finalisierungsfenster als `final` (Manifest:
  `expected_finalization_delay`); Minute-Bars des laufenden Tages sind `preliminary`.
- **Odd Lots** sind im NBBO nicht quotierungsrelevant — für unsere ETF-Größenordnung
  ohne Bedeutung, aber dokumentiert, damit Quote-basierte Features korrekt interpretiert werden.
- **Auction Data:** offizielle Opening/Closing-Prints (Auktionspreise) sind der
  Referenzpreis für OPG-Fill-Vergleiche; Verfügbarkeit je Anbieter unterschiedlich —
  Massive/Databento liefern Auktionsdaten, Alpaca-Daily-Open dient als Fallback
  [zu verifizieren in Phase 1, Ledger-Punkt OFFEN-3].
- **Halts/LULD:** Statusmeldungen (Massive Websocket: LULD-Kanal) werden gespeichert;
  Risk-Check R-18 (Market-Session/Halt) konsumiert sie ([[13_RISK_ENGINE]]).

## 5. Lizenz-Leitplanken (fail-closed)

- Keine Redistribution von Rohdaten oder abgeleiteten Preisreihen an Dritte (alle
  Anbieter-AGB; SIP-Vendor-Ökonomie erklärt in [[29_SOURCE_LEDGER]] C-7.4).
- Non-Professional-Status ist bei GmbH-Gründung oder Fremdkapital neu zu bewerten
  (Blocker BL-02, [[02_REQUIREMENTS]]).
- Vertragsende-Klauseln (Löschpflichten gespeicherter Daten) je Anbieter vor
  Vertragsabschluss prüfen (OFFEN im Ledger).
