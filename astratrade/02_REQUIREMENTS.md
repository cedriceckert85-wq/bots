# 02 — Anforderungen und Annahmen (PHASE 1)

Zurück: [[00_HOME]] · Weiter: [[03_RESEARCH_FINDINGS]]

Dieses Dokument ist die verbindliche Anforderungs- und Annahmenbasis für ASTRATRADE.
Jede Position ist klassifiziert als **[FAKT]** (recherchiert, siehe [[29_SOURCE_LEDGER]]),
**[ANNAHME]** (konservativ getroffen, ausdrücklich gekennzeichnet), **[REGEL]** (vom
Auftraggeber vorgegeben, nicht stillschweigend änderbar) oder **[EMPFEHLUNG]**.

---

## 1. Zielbild

ASTRATRADE ist ein reproduzierbares, auditierbares Research- und Trading-System für
US-ETFs mit drei strikt getrennten Strategie-Tracks:

| Track | Universum | Ziel | Status |
|---|---|---|---|
| A — Market Exposure | SPY, BIL/CASH | Ziel-Marktexposure 0–100 % | **primärer V1-Track** |
| B — Sector Rotation | 11 Sector SPDRs + BIL | Rankings → Zielgewichte | Phase 4 |
| C — Multi Asset | SPY, IWM, TLT, IEF, GLD, BIL | taktische Allokation | Phase 4 |

Details: [[04_STRATEGY_TRACK_A]], [[05_STRATEGY_TRACK_B]], [[06_STRATEGY_TRACK_C]].

**[REGEL]** Phase-1-Invarianten (kritisch geprüft in Abschnitt 6, aber unverändert übernommen):

1. Keine Vermischung der Tracks in Phase 1 (getrennte Modelle, Benchmarks, Risikobudgets, Portfolios).
2. Kein Shorting, keine gehebelten Produkte.
3. `target_weight` ist die einzige Source of Truth für gewünschte Allokation.
4. SELL bedeutet ausschließlich Reduce/Exit (nie Short-Aufbau).
5. Ein Modell löst niemals direkt eine Brokerorder aus. Zwischen Modell und Broker liegen
   zwingend: Portfolio Construction → Pre-Trade Risk → Order Intent → Execution Gates
   (siehe [[13_RISK_ENGINE]], [[14_EXECUTION_ENGINE]]).
6. Neue Tracks werden separat vorgeschlagen und bewertet, nie stillschweigend ergänzt.

## 2. Funktionale Anforderungen (Kurzfassung)

- FR-01: Tägliche Ingestion von Minute- und Daily-Bars für das Gesamtuniversum inkl. Rohdatenarchiv ([[07_MARKET_DATA]], [[08_DATA_CONTRACTS]]).
- FR-02: Point-in-Time-Datasets, aus denen jeder Backtest exakt rekonstruieren kann, welche Daten zu Zeitpunkt *t* bekannt waren.
- FR-03: Corporate-Action-Verarbeitung (Dividenden, Splits, Symboländerungen) mit Audit Trail.
- FR-04: Backtest-Engine mit Auction-/Open-Ausführungssemantik, Kostenmodell und Determinismus ([[10_BACKTESTING]]).
- FR-05: Modelltraining, -registry und -governance inkl. Champion/Challenger ([[11_ML_ARCHITECTURE]]).
- FR-06: Tägliche Signal→Target-Portfolio→Risk→Order-Intent→Execution-Pipeline ([[12_PORTFOLIO_CONSTRUCTION]] ff.).
- FR-07: Dual Ledger (Broker + Economic) mit täglicher Reconciliation ([[16_RECONCILIATION]], [[17_DUAL_LEDGER]]).
- FR-08: Operator Control Plane inkl. Kill Switches, Halt-Modus, manueller Freigabe ([[14_EXECUTION_ENGINE]], [[28_RUNBOOKS]]).
- FR-09: Vollständige Observability (Metrics/Logs/Traces/Alerts) ([[19_OBSERVABILITY]]).
- FR-10: Paper Trading zuerst; Live nur nach Gates ([[23_IMPLEMENTATION_ROADMAP]]).

## 3. Nicht-funktionale Anforderungen (NFR)

| ID | NFR | Messbare Zielgröße |
|---|---|---|
| NFR-01 | Reproduzierbarkeit | Jeder Backtest/Trainingslauf bit-identisch reproduzierbar aus (dataset_version, code_version, config_version, seed) |
| NFR-02 | Determinismus | Zwei Läufe derselben Pipeline-Version auf denselben Daten ⇒ identische Orders/Intents (Hash-Vergleich) |
| NFR-03 | Point-in-Time-Korrektheit | Kein Feature nutzt Daten mit `as_of > decision_time`; automatisierte Leakage-Tests in CI |
| NFR-04 | Ausfallsicherheit | Ausfall einer Komponente führt nie zu unkontrollierten Orders; Safe State = keine neuen Orders |
| NFR-05 | Beobachtbarkeit | Jeder Trade end-to-end tracebar (Daten→Feature→Modell→Prediction→Intent→Fill→P&L) |
| NFR-06 | Auditierbarkeit | Append-only Audit Events, 10 Jahre Aufbewahrung (GoBD-orientiert, [ANNAHME], juristisch zu bestätigen) |
| NFR-07 | Sicherheit | Keine Secrets in Code/Logs/Notebooks; Live-Keys nur im Execution-Segment ([[18_SECURITY]]) |
| NFR-08 | Recovery | RPO ≤ 15 min für operative Daten, RTO ≤ 4 h für Entscheidungs-Pipeline (Variante B, [[21_DISASTER_RECOVERY]]) |
| NFR-09 | Latenz | Kein Low-Latency-Anspruch: Entscheidungspipeline muss zwischen 16:00 ET Close (T−1) und 09:20 ET (T) fertig sein; Order-Submission ≥ 15 min vor Open |
| NFR-10 | Kostentransparenz | Alle laufenden Kosten pro Monat in [[24_COST_MODEL]] gepflegt; Kosten-Breakeven je Strategie ausgewiesen |

**Wichtige Konsequenz aus NFR-09:** ASTRATRADE ist ein *Daily-Frequency*-System mit
Auktions-Ausführung. Das eliminiert ganze Klassen von Latenz-, Kolokations- und
Microstruktur-Problemen und ist die wichtigste Komplexitätsentscheidung des Projekts
(ADR-001 in [[26_ADR_INDEX]]).

## 4. Annahmen (konservativ, ausdrücklich gekennzeichnet)

| ID | Annahme | Auswirkung | Alternative | Default-Empfehlung |
|---|---|---|---|---|
| AS-01 | Startkapital Live-Phase: 10.000–50.000 USD; Paper davor unbegrenzt | Whole-Share-Rundung erzeugt bei kleinen Konten relevante Tracking-Differenz (bei 10k USD und SPY ≈ 640 USD/Aktie ⇒ Granularität ≈ 6,4 %) | Fractional Shares (Alpaca unterstützt fractional nur für DAY-Orders, nicht OPG — siehe [[03_RESEARCH_FINDINGS]]) | Whole Shares + BIL als Cash-Puffer; Granularitätsfehler im Economic Ledger ausweisen |
| AS-02 | Ein Operator (der Nutzer), kein 24/7-Team | Automatische Safe-State-Reaktionen statt Eskalation an Menschen | Bereitschaftsdienst | fail-closed Automatik, tote-Mann-Schalter |
| AS-03 | Handel ausschließlich mit eigenem Kapital, Privatperson in DE | Nach Recherche ([[03_RESEARCH_FINDINGS]] §4) keine BaFin-Erlaubnispflicht; **durch Fachanwalt zu bestätigen** | Trading-GmbH (steuerlich ggf. günstiger ab ~100k p.a. Gewinn) | Privat starten, GmbH-Entscheidung an Steuerberater delegieren |
| AS-04 | Rebalancing-Frequenz: täglich entscheidbar, aber turnover-kontrolliert (erwartet: wenige Trades/Monat in Track A) | Kostenmodell und Kapazität unkritisch | wöchentlich/monatlich | täglicher Entscheidungszyklus, No-Trade-Band |
| AS-05 | Zeitzone Betrieb: Europe/Berlin; Markt: America/New_York | Alle Timestamps UTC + explizite Marktzeit; Sommerzeit-Divergenz (2 Wochen/Jahr) getestet | — | tz-aware überall, Tests in [[22_TEST_STRATEGY]] |
| AS-06 | Paper-Umgebung darf Cloud sein; Live-Keys bleiben auf dediziertem, gehärtetem Host | Security-Zonen in [[18_SECURITY]] | alles Cloud | Variante B in [[20_INFRASTRUCTURE]] |
| AS-07 | Benchmark Track A: Buy-and-Hold SPY (Total Return) UND 60/40 SPY/BIL als sekundäre Referenz | Ein Timing-Modell, das B&H nicht risikoadjustiert schlägt, wird nicht live geschaltet | nur SPY | beide, Gate auf risikoadjustierte Kennzahlen |
| AS-08 | Datenhistorie: mind. 2008 (inkl. GFC) für Daily, Minute soweit Anbieter liefert | Regime-Abdeckung; Minute-Historie < Daily-Historie akzeptiert | längere Historie via Zusatzanbieter | Daily ab 2000 (Zweitquelle), Minute ab Anbieterbeginn |

## 5. Offene Blocker (objektiv nicht vorab entscheidbar)

| ID | Blocker | Muss bestätigt werden von |
|---|---|---|
| BL-01 | Steuerliche Struktur (privat vs GmbH), Verlustverrechnung §20 Abs. 6 EStG aktueller Stand | Steuerberater |
| BL-02 | Non-Professional-Status für SIP-Marktdaten bei algorithmischem Eigenhandel | Datenanbieter/Broker schriftlich |
| BL-03 | Alpaca-Kontoeröffnung als deutsche Privatperson inkl. aktueller Onboarding-Anforderungen | Alpaca Support / eigener Test |
| BL-04 | Erlaubnisfreiheit des Eigenhandels in der konkret gewählten Struktur | Fachanwalt (Aufsichtsrecht) |

Keiner dieser Blocker verhindert Phase 0–6 (Research + Paper Trading); alle blockieren
erst **Controlled Live** (Phase 7, [[23_IMPLEMENTATION_ROADMAP]]).

## 6. Kritische Prüfung der vorgegebenen Regeln

Die Phase-1-Regeln wurden geprüft. Ergebnis: alle Regeln sind fachlich sinnvoll und
werden übernommen. Drei **separate Änderungsvorschläge** (nicht umgesetzt, nur empfohlen):

1. **V-01 (Empfehlung, geringe Dringlichkeit):** „CASH beziehungsweise BIL" in Track A
   präzisieren zu: *BIL ist das investierbare Cash-Proxy-Instrument; Broker-Cash dient nur
   als Settlement-Puffer (< 2 % NAV)*. Grund: BIL verzinst, Broker-Cash bei Alpaca nur
   teilweise; Backtest-Benchmark braucht ein investierbares Instrument.
2. **V-02 (Empfehlung):** Für Track B Benchmark **Equal-Weight-Mittel der 11 Sektoren**
   statt SPY als primären Cross-Section-Benchmark festlegen (Begründung in
   [[05_STRATEGY_TRACK_B]] §3); SPY bleibt sekundäre Kapital-Benchmark.
3. **V-03 (Empfehlung):** Die Regel „keine gehebelten Positionen" um „keine inversen ETFs
   und keine Derivate" ergänzen — schließt eine Umgehungslücke.

## 7. Scope-Abgrenzung (bewusst NICHT in V1/MVP)

- Intraday-Signale, HFT, Market Making
- Optionen, Futures, Krypto, Nicht-US-Märkte
- Shorting, Leverage, Margin-Nutzung
- Fremdkapital, Drittkunden, Signaldienste
- LLM als Live-Entscheider (nur Offline-Research/Monitoring, siehe [[11_ML_ARCHITECTURE]] §8)
- Eigenbau einer Tick-Level-Backtest-Engine

Vollständige MVP-Abgrenzung: [[23_IMPLEMENTATION_ROADMAP]] §10.
