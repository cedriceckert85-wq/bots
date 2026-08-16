# 29 — Source Ledger

Zurück: [[00_HOME]] · Abrufdatum aller Quellen: **2026-08-15**. Spalten: ID · Thema ·
Behauptung · Quelle · Typ (P = Primär, P-IND = Primärquelle identifiziert, Inhalt nur
indirekt geprüft, S = Sekundär) · Veröffentlichungs-/Standdatum · Vertrauen (H/M/N) ·
Änderungsrisiko (ÄR) · Verwendung. UNVERIFIZIERTE Punkte stehen in §7.
Review-Zyklus: jährlich, sowie vor jedem Phase-Gate für die dort verwendeten Claims.

## 1. Alpaca (Verwendung: [[07_MARKET_DATA]], [[14_EXECUTION_ENGINE]], [[03_RESEARCH_FINDINGS]])

| ID | Behauptung | Quelle | Typ | Stand | V | ÄR |
|---|---|---|---|---|---|---|
| AL-1 | Datenpläne: Basic (frei) / Algo Trader Plus 99 $/M | docs.alpaca.markets/us/docs/about-market-data-api; alpaca.markets/data | P-IND | 2026 | H | mittel |
| AL-2 | Basic = IEX-Echtzeit; ATP = SIP (CTA+UTP, 100 % Volumen) | dito + alpaca-docs-Repo `market-data/_index.md` | P | ≤2025-04 | H | niedrig |
| AL-3 | Market-Data-Limits 200/min (Basic), bis 10.000/min (ATP) | about-market-data-api | P-IND | 2026 | H | mittel |
| AL-4 | SIP-Historie auch auf Basic abrufbar außer letzte 15 min | market-data-faq; historical-stock-data | P-IND | 2026 | H | niedrig |
| AL-5 | Historie „7+ Jahre"; Start ~2016 unbestätigt | alpaca.markets/data | P-IND | 2026 | M | niedrig |
| AL-6 | Websocket: 1 Verbindung/Account; Basic max 30 Symbole T/Q | alpaca-docs `realtime.md`; docs streaming | P | ≤2025-04 | H | mittel |
| AL-7 | SIP-Abo bindet Börsen-Subscriber-Agreements (Non-Pro-Display); Redistribution untersagt | files.alpaca.markets TermsAndConditions.pdf | P-IND | n/a | M | niedrig |
| AL-8 | TIF opg: Abgabe vor 9:28 ET (bzw. Queue nach 19:00 ET), nur market/limit, unfilled ⇒ Cancel; cls analog 15:50 | alpaca-docs `orders.md`; docs orders-at-alpaca | P | ≤2025-04 | H | niedrig-mittel |
| AL-9 | 24/5-Overnight via Blue Ocean ATS seit ~02/2026 | alpaca.markets Blog + docs 245-trading | P | 2026-02 | H | mittel |
| AL-11 | Fractional: TIF nur DAY ⇒ inkompatibel mit opg | alpaca-docs `fractional-trading.md`; Changelog | P | ≤2026 | H | mittel |
| AL-12 | client_order_id als eindeutige Client-ID + Lookup-Endpoint; harte Duplikat-Ablehnung unbelegt | alpaca-docs `orders.md` | P | ≤2025-04 | H/M | niedrig |
| AL-13 | Paper-Fills: NBBO-Simulation, unbegrenzte Liquidität, 10 % Zufalls-Partials, keine Dividenden/Fees/Slippage | alpaca-docs `paper-trading.md` | P | ≤2025-04 | H | niedrig |
| AL-14 | Trading-API-Limit 200 req/min/Key | alpaca-docs API-Ref; Support-FAQ | P | ≤2025-04 | H | mittel |
| AL-15 | Kein öffentliches Retail-SLA; regelmäßige kleinere Degradationen | Negativbefund docs/Terms; statusgator.com | P-IND/S | 2026 | M | hoch |
| AL-16 | Deutsche Privatpersonen können Live-Konten eröffnen (W-8BEN im Onboarding) | docs international-accounts; Support-Seiten | P-IND | 2026 | H | mittel |
| AL-17 | Reporting via 1042-S; kein deutscher Steuerabzug (Selbstdeklaration) | Support tax-documents; Inferenz DE-Recht | P-IND/S | 2026 | H/M | niedrig |
| AL-18 | SIPC 500k (250k Cash) + Excess-SIPC (2026 erweitert) | SIPC-PDF; Blog 02/2026 | P-IND | 2026-02 | H | mittel |
| AL-19 | Reconciliation-Endpoints: positions, account, activities (FILL/DIV/…), orders, portfolio/history; trade_updates-Stream empfohlen | alpaca-docs API-Referenzen | P | ≤2025-04 | H | niedrig |

## 2. Marktdaten (Verwendung: [[07_MARKET_DATA]], [[24_COST_MODEL]])

| ID | Behauptung | Quelle | Typ | Stand | V | ÄR |
|---|---|---|---|---|---|---|
| C-0.1 | Polygon.io → Massive.com Rebrand 30.10.2025; API kompatibel, alte Base-URL „extended period" | massive.com/blog; Pressemitteilungen | P | 2025-10 | H | niedrig |
| C-1.1 | Massive Stocks: Starter 29 / Developer 79 / Advanced 199 $/M; unlimitierte Calls | massive.com/pricing | P-IND | 2026 | M-H | mittel |
| C-1.2 | 20+ J. Historie (Advanced), inkl. Delistings, SIP-basiert | massive.com/docs; S | P-IND/S | 2026 | M | niedrig |
| C-1.3 | Flat Files (S3-kompatibel) in allen bezahlten Plänen, ohne Rate Limit | massive.com/blog/flat-files | P | 2026 | H | niedrig |
| C-1.5 | ToS (Stand 2024-10): Redistribution/Derived-Weitergabe verboten; interne Nutzung ok | massive.com/terms market_data_terms.pdf | P-IND | 2024-10 | M | mittel |
| C-2.1 | Databento: direkte Börsen-Feeds (XNAS.ITCH ab 2018-05), EQUS-Bundle | databento.com/datasets, /catalog | P | 2026 | H | niedrig |
| C-2.2 | Databento Standard 199 $/M inkl. unbegrenzter 1s/1m-OHLCV-Historie; sonst usage-based ab ~0,45 $/GB | databento.com/pricing, Blog | P-IND | 2026 | M-H | mittel |
| C-2.3 | PIT-Corporate-Actions (~6 J.), Security Master ab 2005, point-in-time geführt | databento.com/corporate-actions, /security-master | P | 2026 | H | niedrig |
| C-3.x | Tiingo: EOD + IEX-Intraday; Power ~30 $/M, Business ~50 $/M; nur interne Nutzung | tiingo.com Produkt-/Pricing-Seiten | P-IND | 2026 | M | mittel |
| C-4.1 | Sharadar SEP: EOD ab ~2014, survivorship-frei; Preise nur nach Login | data.nasdaq.com/databases/SEP | P-IND | 2026 | M | mittel |
| C-5.x | Norgate: Daily-only, US inkl. Delistings ab 1950, PIT-Indexkonstituenten; Platinum ~630 $/J | norgatedata.com | P-IND | 2026 | H/M | mittel |
| C-6.1 | FRED: freie API mit Key; Serien-Lizenzen einzeln; ALFRED für Vintages | fred.stlouisfed.org/docs | P-IND | 2026 | M | niedrig |
| C-6.2 | Treasury FiscalData: API ohne Key, Public Domain | fiscaldata.treasury.gov/api-documentation | P | 2026 | H | sehr niedrig |
| C-7.x | SIP-Gebührenlogik: Non-Pro ~1 $/M; Pro ~23–45 $/Device; Non-Display/Redistribution vierstellig/M ⇒ AGB-Weitergabeverbote | utp-/cta-Fee-Schedules (PDF), SIFMA-Analyse | P-IND | teils 2015–2021 | M | mittel |

## 3. Backtesting/ML-Werkzeuge (Verwendung: [[10_BACKTESTING]], [[11_ML_ARCHITECTURE]])

| ID | Behauptung | Quelle | Typ | Stand | V | ÄR |
|---|---|---|---|---|---|---|
| VBT-1/2 | vectorbt OSS v1.1.0 (2026-07); „Community Edition" von PRO; Apache-2.0 **mit Commons Clause** | pypi.org/pypi/vectorbt/json; GitHub README | P | 2026-07 | H | mittel |
| VBT-4 | PRO: Subscription ~20–25 $/M (privates Repo) | GitHub Sponsors; vectorbt.pro | P-IND | 2026 | M | mittel |
| BT-1/2 | backtrader: letztes Release 2023-04, faktisch verwaist; GPL-3.0 | PyPI-JSON; GitHub commits | P | 2023-04 | H | niedrig |
| ZL-1/2 | zipline-reloaded 3.1.1 (2025-07); CA via SQLite-Adjustment-Overlay (PIT-korrekt) | PyPI; zipline.ml4trading.io/bundles | P | 2025-07 | H | mittel |
| LEAN-1/3 | LEAN: Apache-2.0, sehr aktiv (CLI 2026-08); nativer MarketOnOpenOrder (Abgabe ≥ 2 min vor Open) | GitHub; quantconnect.com MOO-Doku | P | 2026-08 | H | niedrig |
| LEAN-4 | lokale Backtests brauchen LEAN-Datenformat (Factor-/Map-Files) | QC-Doku | P-IND | 2026 | M | mittel |
| NT-1/3 | NautilusTrader v1.231 + v2-RC (2026-08); OPG-TIF existiert, EOD-Equity-Pfad mit gemeldeten Bugs (#1476) | PyPI; GitHub; nautilustrader.io | P | 2026-08 | H/M | mittel |
| BTF-1/2 | bt 1.2 (2026-04, MIT) Weights-Backtester; qf-lib 4.0.6 event-driven, klein | PyPI; GitHub | P | 2026 | H | mittel |
| LDP-1 | mlfinlab proprietär, von PyPI entfernt | GitHub hudson-and-thames; PyPI 404 | P | 2026 | H | niedrig |
| LDP-2 | skfolio v0.20.2 (2026-08), BSD-3: CombinatorialPurgedCV, DSR | PyPI; skfolio.org | P | 2026-08 | H | niedrig |

## 4. Regulierung/Steuern DE+US (Verwendung: [[03_RESEARCH_FINDINGS]] §4; **alles durch Anwalt/StB zu bestätigen**)

| ID | Behauptung | Quelle | Typ | Stand | V | ÄR |
|---|---|---|---|---|---|---|
| R-C1.1-5 | Eigengeschäft (nur eigenes Kapital, via Broker, kein DEA/HFT-inländisch/keine Dienstleistung) i.d.R. erlaubnisfrei; kritischster Punkt: DEA-Abgrenzung § 15 Abs. 3 WpIG | BaFin-Merkblatt Eigenhandel/Eigengeschäft; § 2, 15 WpIG | P-IND | laufend | H (Norm) / M (Subsumtion) | niedrig-mittel |
| R-C2.2/6 | Trading-GmbH: ~30 % laufend (KSt+GewSt); Ausschüttung gesamt ~48 %; § 8b-95%-Freistellung nur Aktien | Sekundärquellen (Steuerkanzleien) | S | 2025/26 | H/M | mittel |
| R-C2.4 | § 20 Abs. 6 S. 5/6 EStG (Termingeschäft-Verlustdeckel) durch JStG 2024 **rückwirkend aufgehoben** | Haufe; CMS; LfSt Bayern; BFH VIII B 113/23 | S (übereinstimmend) | 2024-12 | H | niedrig |
| R-C2.5 | Aktienverlust-Verrechnungskreis (S. 4) besteht fort; BVerfG 2 BvL 3/21 anhängig | Handelsblatt; taxgate; BFH-Vorlage | S | 2026 | H | **hoch** |
| R-C3.1 | Signal Following/Social Trading mit Auto-Ausführung = Finanzportfolioverwaltung (erlaubnispflichtig) | BaFin FinTech-Seite | P-IND | laufend | H | niedrig |
| R-C3.4 | ESMA Supervisory Briefing Copy Trading (ESMA35-42-1428, 2023-03-30) | esma.europa.eu | P | 2023-03 | H | mittel |
| R-C3.5 | Reines neutrales Bot-SaaS ohne Kuratierung: Grauzone, keine spezifische BaFin-Aussage gefunden | Negativbefund | — | 2026 | N-M | hoch |
| R-C4.1-3 | W-8BEN (3 J. gültig); Dividenden 15 % Treaty; keine US-Steuer auf NRA-Kursgewinne | IRS iw8ben, Pub. 515 | P-IND | 2026 | H | niedrig |
| R-C4.5 | **PDT-Regel abgeschafft**: SEC-Genehmigung 14.04.2026 (SR-FINRA-2025-017), wirksam 04.06.2026, Broker-Phase-in bis 20.10.2027 (FINRA Notice 26-10) | finra.org Notice 26-10; Schwab/E*TRADE | P-IND + S | 2026-04 | H | mittel |
| R-C5.1/2 | Non-Pro-Definition (persönlich, nicht geschäftlich); GmbH ⇒ Professional; Default = Professional bis Nachweis | NYSE Non-Pro-Policy; Nasdaq Data Policies | P-IND | laufend | H/M | mittel |
| R-C6.1/2 | Aufbewahrung: 10 J. Bücher/Abschlüsse, 8 J. Buchungsbelege (BEG IV, ab 2025); GoBD: unveränderbar, maschinell auswertbar, Verfahrensdoku | Haufe; IHK; BBH | S (übereinstimmend) | 2025 | H | niedrig |

## 5. Strategie-Literatur (Verwendung: [[04_STRATEGY_TRACK_A]]ff.; wissenschaftliche Primärquellen aus Modellwissen, nicht neu abgerufen — Zitate vor Publikationen prüfen)

| ID | Referenz | Verwendung | V |
|---|---|---|---|
| LIT-1 | Moreira/Muir 2017, *Volatility-Managed Portfolios*, JF | Track A Vol-Timing | H (peer-reviewed) |
| LIT-2 | Faber 2007, *A Quantitative Approach to TAA*, JWM | Track A/C 10M-SMA-Baseline | H |
| LIT-3 | Moskowitz/Ooi/Pedersen 2012, *Time Series Momentum*, JFE | Track A/C | H |
| LIT-4 | Jegadeesh/Titman 1993; Moskowitz/Grinblatt 1999 | Track B Momentum | H |
| LIT-5 | Bailey/López de Prado 2014 (DSR); Bailey et al. 2015 (PBO/CSCV); López de Prado 2018 (Purged CV) | Validierung | H |
| LIT-6 | Harvey et al. 2018 (Vol Targeting); Cederburg et al. 2020 (kritische Replikation) | Track A Einordnung | H |
| LIT-7 | Antonacci 2014 (Dual Momentum) | Track B Absolute-Momentum-Gate | M (Buch/SSRN) |

## 6. Fondsauflagedaten (Verwendung: [[05_STRATEGY_TRACK_B]])

| ID | Behauptung | Quelle | V |
|---|---|---|---|
| ETF-1 | XLRE Auflage 10/2015; XLC Auflage 06/2018 (Universum zeitvariabel) | State-Street-Produktseiten [P-IND, aus Modellwissen — in Phase 1 gegen Factsheets verifizieren] | M-H |

## 7. Offene/unverifizierte Punkte (Verifikation eingeplant)

| ID | Punkt | Verifikation |
|---|---|---|
| OFFEN-1 | Alpaca: exakter Historienstart; client_order_id-Duplikatsemantik; ATP-Websocket-Anzahl; opg-Paper-Fill-Semantik; Key-Scopes/Withdrawal-Schutz | Phase-5-Sandbox-Tests + Support-Anfrage |
| OFFEN-2 | Massive: ToS-Wortlaut Speicherung nach Kündigung; 399-$-Tier | vor Vertragsabschluss PDF lesen |
| OFFEN-3 | Auktions-Print-Verfügbarkeit je Anbieter (offizieller Open) | Phase-1-Ingestion-Spike |
| OFFEN-4 | Databento Plus/Unlimited-Preise; SIP-Feed-Verfügbarkeit | Sales-Anfrage bei Bedarf |
| OFFEN-5 | Tiingo-/Sharadar-/Norgate-Preise aktuell | vor Abschluss |
| OFFEN-6 | DEA-Einordnung Broker-API (BL-04); GmbH-Steuerdetails (§ 8b Abs. 3/4); InvStG-Behandlung US-ETFs; Anrechnung § 32d Abs. 5 | Anwalt/StB-Mandat |
| OFFEN-7 | Alpaca-Umsetzung der PDT-Nachfolgeregeln (Intraday-Margin) | Support-Anfrage vor Phase 7 |
| OFFEN-8 | ETF-1 Auflagedaten gegen offizielle Factsheets | Phase 1 |
