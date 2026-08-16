# 30 — Glossar

Zurück: [[00_HOME]]

| Begriff | Definition (projektverbindlich) |
|---|---|
| Abstention | bewusster No-Trade-Zustand bei unzureichender Forecast-Konfidenz |
| ADR | Architecture Decision Record ([[26_ADR_INDEX]]) |
| ALFRED | Archival FRED — Makrodaten mit Vintage-Ständen (PIT-fähig) |
| as_of | Wissenszeitpunkt: ab wann eine Information dem System bekannt/final war |
| Auction Miss | geplante Auktions-Order wurde nicht in der Auktion ausgeführt |
| Bitemporalität | getrennte Führung von Ereigniszeit (market_ts) und Wissenszeit (as_of) |
| BIL | SPDR 1-3 Month T-Bill ETF; investierbares Cash-Proxy |
| Break | Abweichung zwischen interner Sicht und Broker-Realität ([[16_RECONCILIATION]]) |
| Broker Ledger | Buchwerk der tatsächlichen Broker-Ereignisse ([[17_DUAL_LEDGER]]) |
| Champion/Challenger | produktives Modell vs Shadow-Kandidaten ([[11_ML_ARCHITECTURE]] §4) |
| CLS | Time-in-Force für Closing-Auction-Orders (MOC/LOC) |
| CUSUM | sequentieller Test auf Mittelwertbruch (Live-Performance-Überwachung) |
| Dead Letter | Intent, der nach erschöpftem Retry-Budget manuell behandelt werden muss |
| DEA | Direct Electronic Access — aufsichtsrechtlich relevanter Direktzugang (BL-04) |
| Deflated Sharpe Ratio (DSR) | Sharpe-Korrektur um Multiple Testing (Bailey/López de Prado) |
| Economic Ledger | wirtschaftliche Sicht inkl. Total Returns/Corporate Actions |
| Embargo | Ausschlusszeitraum nach Trainingsfenster gegen Label-Overlap-Leakage |
| Fencing Token | monotone Kennung, die veraltete Leader-Schreibzugriffe verwirft |
| Fill | (Teil-)Ausführung einer Broker-Order |
| Golden Dataset | handverifizierter Referenzdatensatz für Regressionstests |
| Intent | Order Intent — transaktionale Handelsabsicht vor Broker-Submission |
| LOO/MOO | Limit-/Market-on-Open (Opening-Auction-Ordertypen; Alpaca TIF `opg`) |
| Lockbox | unantastbares Holdout-Zeitfenster ([[09_RESEARCH_PLATFORM]] §7) |
| LULD | Limit Up/Limit Down — Preisbänder-Mechanismus der US-Börsen |
| Manifest | Metadatensatz eines Datenlaufs ([[08_DATA_CONTRACTS]] §3) |
| NBBO | National Best Bid and Offer |
| Outbox | transaktionale Tabelle, aus der der Submitter Orders liest |
| PBO | Probability of Backtest Overfitting (CSCV) |
| PIT | Point-in-Time — nur zum Entscheidungszeitpunkt bekannte Daten |
| PSI | Population Stability Index (Feature-Drift-Maß) |
| Purging | Entfernen von Trainingsbeispielen mit Label-Überlappung zum Testfenster |
| RPN | Risk Priority Number = Severity × Occurrence × Detectability (FMEA) |
| RPO/RTO | Recovery Point / Recovery Time Objective |
| Sev-1/2/3 | Incident-Schweregrade (1 = Handelsstopp) |
| Shadow Mode | Echtzeit-Entscheidungen ohne Orderabgabe |
| SIP | Securities Information Processor (CTA/UTP-konsolidierte Marktdaten) |
| Slippage | Differenz Fill-Preis vs Referenzpreis (hier: offizieller Auktionspreis) |
| Split Brain | zwei aktive Execution-Instanzen für dasselbe Portfolio |
| System of Record (SoR) | verbindliche Primärquelle eines Datums |
| Target Weight | Zielgewicht je Symbol — zentrale Source of Truth ([[12_PORTFOLIO_CONSTRUCTION]]) |
| TWR | Time-Weighted Return |
| Vintage | historischer Datenstand einer revidierbaren Serie zum Publikationszeitpunkt |
| Walk-Forward | sequenzielle Out-of-Sample-Validierung mit fortschreitendem Fenster |
| Whole Shares | ganzzahlige Stückzahlen (Voraussetzung für OPG bei Alpaca) |
