# 03 — Wichtigste Erkenntnisse der Deep Research (PHASE 2)

Zurück: [[00_HOME]] · Quellen: [[29_SOURCE_LEDGER]] · Abrufdatum aller Quellen: 2026-08-15

Recherchemethodik: vier parallele Recherchestränge (Broker/Alpaca, Marktdaten, Backtesting-
Frameworks, Regulierung/Steuern) auf Basis von Primärquellen (offizielle Dokus, Gesetzes-
und Behördentexte, PyPI/GitHub, IRS/FINRA/ESMA). Einschränkung: mehrere Anbieter-Domains
waren nur indirekt (Suchindex/Doku-Repos) erreichbar; betroffene Claims sind im Source
Ledger als [P-INDIREKT] bzw. UNVERIFIZIERT markiert und vor Vertragsabschluss direkt zu
verifizieren. **Kein Claim in diesem Vault ist erfunden; unbelegte Punkte sind als offen markiert.**

## 1. Markt- und Handelsmechanik (Kernwissen, stabil)

- Regular Session 09:30–16:00 ET; Pre-Market ab 04:00, After-Hours bis 20:00 ET; Alpaca
  bietet zusätzlich seit 2026 24/5-Overnight via Blue Ocean ATS (nicht ASTRATRADE-relevant,
  explizit ausgeschlossen) [AL-9].
- Opening/Closing Auctions der Primärbörse liefern den offiziellen Open/Close-Print;
  MOO/LOO-Orders (Alpaca TIF `opg`) müssen **vor 9:28 ET** abgegeben werden, MOC/LOC
  (`cls`) vor 15:50 ET; nur market/limit; unfilled ⇒ Cancel [AL-8, hoch].
- Feiertage/Halbtage: exchange_calendars als versionierte Referenz; Half-Days (z.B. Tag
  nach Thanksgiving, Close 13:00 ET) verschieben die Closing Auction — Tests Pflicht.
- LULD-Bänder und marktweite Circuit Breaker (7/13/20 % S&P-Level) können Auktionen und
  Fills verzögern; Halt-Status muss als Datenpunkt vorliegen (Risk-Check R-18).
- ETF-Spezifika: Creation/Redemption hält Preise nahe NAV; in Stressphasen (z.B.
  24.08.2015) können ETF-Preise vom NAV abweichen — Price-Sanity-Checks gegen
  Referenzpreis nötig, besonders zur Eröffnung.

## 2. Broker (Alpaca) — entscheidungsrelevante Befunde

| Befund | Konsequenz | Ledger |
|---|---|---|
| OPG (MOO/LOO) nativ unterstützt, Cut-off 9:28 ET | Opening-Auction-Default ist umsetzbar; Submission-Deadline 9:20 ET mit Puffer | AL-8 |
| Fractional-Orders: nur TIF `day`, kein OPG | **Whole-Share-Trading ist für OPG zwingend** — bestätigt den Standardansatz | AL-11 |
| `client_order_id` als Idempotenz-/Lookup-Mechanismus; harte Duplikat-Ablehnung UNVERIFIZIERT | Duplicate-Schutz zusätzlich clientseitig (Outbox + State Machine); Semantik in Paper empirisch testen (Phase 5 Task) | AL-12 |
| Paper-Fills: Simulation gegen NBBO, **unendliche Liquidität**, 10 % zufällige Partials, keine Dividenden/Fees/Slippage; OPG-Simulationsgüte unbekannt | Paper beweist nur Prozess-Korrektheit, nie Ausführungsqualität; Paper-Verzerrungen werden im Economic Ledger dokumentiert ([[17_DUAL_LEDGER]] §6) | AL-13 |
| Trading-API-Limit 200 req/min; kein öffentliches SLA; regelmäßige kleinere Degradationen (Statusaggregator) | Retry-Budgets, eigene Order-State-Reconciliation, Degraded-Mode-Design sind Pflicht ([[14_EXECUTION_ENGINE]], [[21_DISASTER_RECOVERY]]) | AL-14/15 |
| Deutsche Privatpersonen können Konten eröffnen (W-8BEN, 1042-S, kein deutscher Steuerabzug ⇒ Anlage KAP) | Onboarding real testen (BL-03); Steuer-Selbstveranlagung inkl. InvStG-Thema US-ETFs an StB | AL-16/17 |
| SIPC 500k USD + Excess-SIPC | Verwahrrisiko dokumentiert, kein Blocker | AL-18 |
| Dividenden/Splits erscheinen in `account/activities`; zwei Corporate-Action-APIs | Reconciliation-Quelle definiert ([[16_RECONCILIATION]]) | AL-19 |

**Broker-Alternativen:** Interactive Brokers ist die naheliegendste Alternative
(breitere Ordertypen, deutsche Steuerreports über Drittanbieter, aber komplexere API und
Gebührenmodell). Entscheidung: **Alpaca für V1** (kostenfreie Orders, saubere REST/WS-API,
Paper-Umgebung, OPG-Support); der Broker Adapter wird als austauschbares Port/Adapter-
Interface gebaut, damit ein IB-Adapter später ohne Kernänderung möglich ist (ADR-016).
[EMPFEHLUNG, Confidence mittel-hoch; IB-Details nicht tief recherchiert — bewusst, um
Anbieterlisten klein zu halten.]

## 3. Marktdaten — entscheidungsrelevante Befunde

- **Polygon.io heißt seit 30.10.2025 Massive.com** (API-kompatibel, Deprecation-Risiko
  der alten Base-URL einplanen) [C-0.1].
- Massive-Pläne 29/79/199 USD/M, Flat Files (Bulk ohne Rate Limit) in allen bezahlten
  Plänen, 20+ Jahre Historie inkl. Delistings [C-1.x].
- **Databento** = PIT-Goldstandard (as-recorded Feeds, PIT-Corporate-Actions, Security
  Master), aber Historie ab 2018 [C-2.x].
- Alpaca: SIP-Historie auch im Gratisplan (außer letzte 15 min); Echtzeit-SIP nur mit
  Algo Trader Plus 99 USD/M [AL-1..4].
- FRED/ALFRED + Treasury FiscalData: kostenlose, für PIT geeignete Makro-/Zinsquellen
  (nur ALFRED-Vintages verwenden) [C-6.x].
- SIP-Lizenzökonomie: interne Nutzung ok, Redistribution/Non-Display gesondert bepreist
  und teuer — erklärt, warum alle Anbieter-AGB Weitergabe verbieten [C-7.x].

Entscheidung und Begründung: [[07_MARKET_DATA]] §3 (Zwei-Quellen-Prinzip).

## 4. Regulierung und Steuern (alles: durch Fachanwalt/StB zu bestätigen)

- **Eigenhandel mit ausschließlich eigenem Kapital (Privatperson, über Broker, ohne
  Börsenmitgliedschaft/DEA/HFT an inländischen Plätzen): nach Recherchestand keine
  BaFin-Erlaubnispflicht** (KWG/WpIG-Analyse, C1.1–C1.5; wichtigster offener Punkt:
  DEA-Abgrenzung des Broker-API-Zugangs, anwaltlich klären).
- **Trading-GmbH**: aufsichtsrechtlich ebenso erlaubnisfrei; steuerlich ~30 % auf
  ETF-Gewinne, 95%-Freistellung nur für Aktien (nicht ETFs), Ausschüttungsbelastung
  ~48 % — nach Streichung der Termingeschäft-Verlustdeckelung (JStG 2024, rückwirkend,
  C2.4) ist das frühere Hauptargument pro GmbH entfallen. **[EMPFEHLUNG] privat starten.**
- **Jede Öffnung für Dritte** (Verwaltung, personalisierte Signale, Copy Trading,
  automatische Fremddepot-Ausführung) triggert Erlaubnispflichten (BaFin-Praxis:
  Signal Following/Social Trading = Finanzportfolioverwaltung, C3.1; ESMA Copy-Trading-
  Briefing 2023, C3.4). Reines neutrales SaaS ist Grauzone (C3.5).
- **US-Seite:** W-8BEN, 15 % Treaty-Quellensteuer auf Dividenden, keine US-Steuer auf
  Kursgewinne für NRA; **FINRA-PDT-Regel (25.000-USD) seit 04.06.2026 abgeschafft**,
  Broker-Übergangsfristen bis 20.10.2027 — PDT-Guards konfigurierbar halten (C4.5).
- **Market-Data-Status:** GmbH ⇒ Professional-Einstufung (teurer); Privatperson mit
  Eigenhandel kann grundsätzlich Non-Pro bleiben — Selbstauskunft muss korrekt sein;
  vor GmbH-Wechsel neu bewerten (C5.2, BL-02).
- **Aufbewahrung (GmbH-Fall):** 10 Jahre Bücher/Abschlüsse, 8 Jahre Buchungsbelege
  (BEG IV), GoBD-konforme unveränderbare Archivierung — das Audit-Log-Design
  ([[08_DATA_CONTRACTS]], [[19_OBSERVABILITY]]) erfüllt die technischen Anforderungen
  bereits (C6.x).

## 5. Backtesting-Frameworks

Siehe [[10_BACKTESTING]] §1–2. Kernbefunde: backtrader verwaist (2023), LEAN einziges
Framework mit nativer MOO-Order, zipline-reloaded bestes OSS-CA/PIT-Modell,
vectorbt jetzt „Community Edition" mit Commons-Clause-Lizenz, NautilusTrader in
v2-Migration, mlfinlab proprietär ⇒ **skfolio** für Purged-CV/DSR. Entscheidung:
Hybrid aus schlanker Eigenbau-Portfolio-Engine + vectorbt (Exploration) + Zweit-Engine-
Cross-Check (ADR-002).

## 6. Alternative Daten und NLP (Bewertung)

| Quelle | Urteil V1 | Begründung |
|---|---|---|
| Zinsstruktur (Treasury/ALFRED) | **JA** | kostenlos, PIT-fähig, ökonomisch begründet (Tracks A/C) |
| VIX/Termstruktur (CBOE via Anbieter) | JA, nach Lizenzprüfung | etablierter Risikoindikator; Publikationszeitpunkt sauber |
| HY-Kreditspreads (ALFRED) | JA | Risk-off-Indikator, Vintage-fähig |
| ETF-Flows, Optionsmarkt-Aggregate | SPÄTER | Kosten/Coverage/PIT unklar; erst nach Track-A-Baseline |
| News/Sentiment/Google Trends/Earnings-NLP | **NEIN in V1** | Für SPY/Sektor-ETFs schwacher, revisionsanfälliger Zusatznutzen; hoher PIT-/Lizenzaufwand |
| LLMs | nur offline | Research-Assistenz, Klassifikation von Incidents, Monitoring-Zusammenfassungen; **nie** Live-Entscheider ([[11_ML_ARCHITECTURE]] §8) |

## 7. Die zehn wichtigsten architekturprägenden Erkenntnisse

1. Whole Shares + OPG ist konsistent und umsetzbar (Fractional schließt OPG aus).
2. Paper Trading beweist Prozesse, nicht Ausführungsqualität — Slippage-Kalibrierung
   braucht Live-Vergleich Auktionspreis vs eigener Fill.
3. Zwei unabhängige Datenquellen sind Pflicht, nicht Luxus (Single-Feed = größtes
   unentdeckbares Risiko).
4. Bitemporalität (market_ts + as_of) muss von Tag 1 ins Schema, nachrüsten ist teuer.
5. Idempotenz darf nicht allein auf Broker-Semantik bauen (client_order_id-Verhalten
   unverifiziert) ⇒ Outbox + State Machine clientseitig.
6. Der Regulierungspfad „privat, eigenes Geld" ist frei (zu bestätigen); jede
   Drittöffnung ist ein Projekt-Stopper — Architektur erzwingt Single-Tenant.
7. Daily-Frequenz + Auktion eliminiert die teuersten Probleme (Latenz, Intraday-Fills,
   Non-Display-Lizenzen).
8. Makro-Features nur aus Vintage-Quellen (ALFRED) — sonst Revision Bias.
9. Framework-Landschaft instabil (Rebrands, Lizenzwechsel, verwaiste Projekte) ⇒
   dünne eigene Kernbibliothek mit austauschbaren Adaptern.
10. PDT-Abschaffung und Steuerrechtsänderungen zeigen: Compliance-Fakten haben hohe
    Änderungsrate ⇒ Source Ledger mit Änderungsrisiko-Spalte und jährlicher Review.
