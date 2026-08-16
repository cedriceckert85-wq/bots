# 27 — Red-Team-Review und FMEA (PHASE 7)

Zurück: [[00_HOME]] · Ergebnisumsetzung: §4 und [[01_EXECUTIVE_SUMMARY]] §5

Methodik: Angriff auf den eigenen Entwurf in 14 Kategorien; je Szenario Ursache,
Eintrittswahrscheinlichkeit (O 1–5), Auswirkung (S 1–5), Erkennbarkeit (D 1–5, 5 =
schlecht erkennbar), vorhandene Kontrolle, zusätzliche Mitigation, Restrisiko,
Owner (bei Ein-Personen-Betrieb: Operator, mit externem Reviewer wo markiert).
**RPN = S×O×D**; Mitigation Priority: RPN ≥ 48 = P1, 24–47 = P2, < 24 = P3.

## 1. FMEA-Tabelle (42 Szenarien)

| # | Kategorie / Szenario | Ursache | S | O | D | RPN | Vorhandene Kontrolle | Zusätzliche Mitigation (→ = umgesetzt in §4) | Restrisiko |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Quant: Backtest-Overfitting trotz DSR | zu viele stille Trials (Notebook-Exploration unerfasst) | 5 | 4 | 4 | 80 **P1** | Trial-Zähler, PBO | → Pflicht: auch Notebook-Experimente via MLflow-Autolog; externer Quant-Review vor Gate | mittel |
| 2 | Quant: Regime-Bruch nach Go-Live | Edge war regimeabhängig | 4 | 4 | 3 | 48 P1 | Regime-Tests, CUSUM, Deleveraging | Erwartungsmanagement: Track A als Risiko-Timing definiert | mittel-hoch (nicht technisch lösbar) |
| 3 | Quant: Baseline-Leiter übersprungen | Ergebnisdruck | 4 | 3 | 3 | 36 P2 | Gate-Formalismus | Gate-Checkliste maschinell erzwungen (Report-Generator verweigert ohne Baseline-Vergleich) | niedrig |
| 4 | Leakage: Normalisierung über Gesamtzeitraum | Bequemlichkeit | 5 | 3 | 4 | 60 P1 | T-LEAK-05, Builder-API erzwingt Fold-Fit | Code-Review-Regel: kein sklearn-fit außerhalb Builder | niedrig |
| 5 | Leakage: Makro-Revisionen (FRED statt ALFRED) | falsche Serie gewählt | 5 | 3 | 4 | 60 P1 | ALFRED-only-Regel | → Ingestion-Allowlist: FRED-Serien ohne Vintage technisch geblockt | niedrig |
| 6 | Leakage: Universe-Backfill (XLC vor 2018) | statisches Universum | 4 | 3 | 4 | 48 P1 | universe_memberships, T-LEAK-04 | — | niedrig |
| 7 | Leakage: Lockbox schleichend verbraucht | „nur mal schauen" | 5 | 3 | 5 | 75 **P1** | lockbox_guard, Audit | → Öffnung nur mit signiertem Audit-Event + externem Reviewer; Touched-Kennzeichnung permanent | niedrig-mittel |
| 8 | Daten: Single-Feed-Fehler beide Quellen SIP-abgeleitet | Massive+Alpaca teilen SIP-Ursprung | 4 | 2 | 4 | 32 P2 | Cross-Check erkennt Aggregator-Fehler, nicht SIP-Fehler | → Option Databento (direkte Feeds) als dritte Quelle ab Live-Scale-up | mittel |
| 9 | Daten: stille Anbieter-Semantikänderung (Rebrand-API) | Massive-Migration | 3 | 4 | 3 | 36 P2 | Manifeste, semantic_drift-Job | Changelog-Monitoring (LLM-offline-Klassifikation, [[11_ML_ARCHITECTURE]] §8) | niedrig |
| 10 | Daten: fehlende Bar unbemerkt | Gap im Backfill | 3 | 3 | 2 | 18 P3 | Kalender-Vollständigkeitscheck | — | niedrig |
| 11 | Daten: Korrektur überschreibt Historie | UPDATE statt Revision | 4 | 2 | 4 | 32 P2 | append-only + revision, DB-Grants | — | niedrig |
| 12 | Daten: CA fehlt/falsch (Split nicht verarbeitet) | Anbieterlücke | 5 | 2 | 3 | 30 P2 | Zwei-Quellen-CA-Recon, Sev-1-Halt | T-CA-01-Fixtures je CA-Typ | niedrig |
| 13 | Markt: Auktionspreis-Anomalie (Gap/Fat Finger) | Marktstruktur | 4 | 2 | 2 | 16 P3 | LOO-Limits, Slippage-Guard | — | niedrig |
| 14 | Markt: Halt/LULD zur Auktion | Volatilität | 3 | 2 | 2 | 12 P3 | R-18, Auction-Miss-Prozedur | — | niedrig |
| 15 | Markt: ETF-NAV-Dislokation am Open | Stress (2015-08-24-Muster) | 4 | 2 | 3 | 24 P2 | Price Sanity, LOO | Auktions-Order-Volumen-Limit R-11 | mittel |
| 16 | Markt: Half-Day/Kalenderfehler | tzdata/Kalender veraltet | 3 | 2 | 3 | 18 P3 | market_calendar_version, T-CAL-01 | Kalender-Update-Pflicht im Monatspatch | niedrig |
| 17 | Execution: Doppelorder nach Timeout | Retry ohne Lookup | 5 | 2 | 3 | 30 P2 | Outbox, client_order_id-Lookup, State Machine | → Broker-Duplikat-Semantik empirisch testen (Phase-5-Task, T-EXE-01) | niedrig |
| 18 | Execution: Auction-Miss-Kaskade (jeden Tag verpasst) | Deadline-Fehler/Zeitzonenbug | 3 | 2 | 2 | 12 P3 | SLO-Metrik, T-TZ-01 | — | niedrig |
| 19 | Execution: Partial Fill falsch verbucht | Accounting-Bug | 4 | 2 | 3 | 24 P2 | T-EXE-03, Fill-Recon | — | niedrig |
| 20 | Execution: manuelle Trades kollidieren mit System | Operator handelt am System vorbei | 3 | 3 | 2 | 18 P3 | external_fill-Erkennung | Policy: manuelle Trades nur im Halt-Modus | niedrig |
| 21 | Broker: Alpaca-Ausfall zur Auktion | Anbieterrisiko, kein SLA | 3 | 3 | 1 | 9 P3 | fail-closed, Auction-Miss | IB-Adapter als mittelfristige Option (ADR-016) | mittel (Rest: verpasste Tage) |
| 22 | Broker: Paper→Live-Illusion (Fills zu gut) | Paper-Simulationsartefakte | 4 | 4 | 2 | 32 P2 | dokumentierte Verzerrungsliste [[17_DUAL_LEDGER]] §6, Shadow-Messung | Gate-Regel: Live-Erwartung = Paper − Artefaktabschlag | mittel |
| 23 | Broker: Konto-Restriktion (PDT-Übergang, Margin-Call-Logik) | Regeländerung 26-10 im Phase-in | 3 | 2 | 2 | 12 P3 | PDT-Guard konfigurierbar, R-15 | Alpaca-Umsetzung abfragen (Ledger OFFEN) | niedrig |
| 24 | Broker: Withdrawal durch Key-Dieb | Key-Leak | 5 | 1 | 3 | 15 P3 | Zonen, Rotation; Alpaca-API kann keine Auszahlungen an fremde Konten ohne Dashboard-Auth [zu verifizieren] | → OFFEN-Punkt: Key-Scopes klären; Dashboard mit MFA + separatem Passwort | mittel |
| 25 | Infra: VM-Ausfall + Backup defekt | doppelt Pech | 4 | 2 | 2 | 16 P3 | monatlicher Restore-Test | — | niedrig |
| 26 | Infra: Split Brain | Partition + Lease-Bug | 5 | 1 | 3 | 15 P3 | Fencing-Trigger, T-SPL-01 | — | niedrig |
| 27 | Infra: Disk voll (Bars wachsen) | fehlendes Kapazitätsmanagement | 3 | 3 | 1 | 9 P3 | disk_usage-Alert | Kapazitätsreview quartalsweise | niedrig |
| 28 | Infra: Clock-Drift ⇒ Deadline verfehlt/PIT falsch | NTP-Fehler | 4 | 2 | 3 | 24 P2 | chrony, R-23, DB-Zeit für Leases | — | niedrig |
| 29 | Security: Secrets im Notebook committed | menschlicher Fehler | 4 | 3 | 2 | 24 P2 | gitleaks pre-commit+CI, Z-R ohne Keys | — | niedrig |
| 30 | Security: Ransomware verschlüsselt Host+Backups | Angriff | 5 | 1 | 2 | 10 P3 | Object Lock, Offline-Anker | — | niedrig |
| 31 | Security: Supply-Chain (bösartiges Paket) | Dependency-Angriff | 4 | 2 | 4 | 32 P2 | Lockfiles, OSV/Trivy, Egress-Allowlist Z-E | → Paket-Quarantäne: neue Deps erst nach 14 Tagen + Review in Z-E | mittel |
| 32 | Mensch: Limit „mal eben" hochgesetzt | Emotion nach Verlust | 5 | 3 | 3 | 45 P2 | 4-Augen-Ersatz (Cooling-off, Codes) | → Risk-Limit-Erhöhungen: 24-h-Verzögerung technisch erzwungen | mittel |
| 33 | Mensch: Alert-Fatigue ⇒ Sev-1 übersehen | zu viele Alerts | 4 | 3 | 3 | 36 P2 | Severity-Disziplin, Runbooks | Alert-Review monatlich: jeder Alert ohne Aktion wird herabgestuft/entfernt | mittel |
| 34 | Mensch: Operator-Ausfall (Krankheit) | Ein-Personen-Risiko | 3 | 3 | 1 | 9 P3 | tote-Mann-Halt, Break-Glass-Doku für Angehörige | Notfallmappe (Konto schließen/liquidieren, Anwaltskontakt) | mittel |
| 35 | Compliance: DEA-/Erlaubnis-Fehleinschätzung | Recht komplex | 5 | 1 | 4 | 20 P3 | BL-04 Anwalt vor Live | — | niedrig nach Klärung |
| 36 | Compliance: Non-Pro-Status falsch deklariert | GmbH/Statuswechsel vergessen | 3 | 2 | 3 | 18 P3 | BL-02, Jahres-Review des Ledgers | — | niedrig |
| 37 | Compliance: InvStG-Steuerfehler (US-ETFs, Vorabpauschale) | Selbstveranlagung komplex | 3 | 4 | 3 | 36 P2 | StB-Mandat (BL-01), Steuer-Datenexport aus Ledger | → Ledger-Exportformat mit StB abstimmen (Phase 5 Task) | mittel |
| 38 | Kosten: Fixkosten fressen Kleinkapital | 24_COST_MODEL §2 | 3 | 5 | 1 | 15 P3 | fixed_cost_drag-Metrik im Gate-Report | bewusste Entscheidung: Live = Prozessnachweis | hoch, aber transparent |
| 39 | Skalierung: Auktionsvolumen-Impact bei Kapitalwachstum | Ordergröße wächst | 3 | 2 | 2 | 12 P3 | R-11 (Volumenanteil), Capacity-Analyse je Gate | — | niedrig |
| 40 | Modellrisiko: Champion still degradiert (langsamer Drift unter Schwellen) | Schwellen zu lax | 4 | 3 | 4 | 48 P1 | Drift-Suite | → zusätzlich: quartalsweiser Pflicht-Re-Validierungslauf gegen frische Daten, unabhängig von Alarmen | mittel |
| 41 | Performance-Interpretation: TWR vs Broker-P&L verwechselt / Paper als Live kommuniziert | Reporting-Unschärfe | 3 | 3 | 2 | 18 P3 | Dual-Ledger-Trennung, Pflicht-Fußnoten im Report-Template | — | niedrig |
| 42 | Performance-Interpretation: Glückssträhne als Skill gelesen ⇒ verfrühtes Scale-up | Varianz | 5 | 3 | 4 | 60 **P1** | Scale-up-Gate (6 Monate, ×2-Schritte) | → Gate ergänzt: Scale-up erfordert DSR-Update mit Live-Daten, nicht nur Kalenderzeit | mittel |

## 2. Die zehn wahrscheinlichsten Wege, trotz gutem Backtest real Geld zu verlieren

1. Overfitting durch unerfasste Exploration (#1) — der Backtest war nie echt.
2. Regime-Bruch: Edge existierte, ist aber vorbei (#2).
3. Paper-Live-Lücke: reale Auktions-Slippage/Misses übersteigen Modellannahmen (#22).
4. Fixkosten-Drag bei kleinem Kapital (#38) — mathematisch sicherste Verlustquelle.
5. Schleichender Modell-Drift unterhalb der Alarm-Schwellen (#40).
6. Verhaltensfehler des Operators: Limits lockern, Gates überstimmen (#32, #42).
7. Steuer-/Compliance-Nachzahlungen aus InvStG-Fehlern (#37).
8. Seltene Ausführungsfehler mit großem Einzelschaden (Doppelorder/CA-Fehler, #17/#12).
9. Datenfehler, der beide SIP-abgeleiteten Quellen teilt (#8).
10. Opportunitätsverlust durch Übervorsicht: fail-closed-Tage in Trendphasen
    (kein Bug, aber realer Tracking-Verlust — im Economic Ledger als
    `missed_auction_cost` gemessen).

## 3. Nicht technisch lösbare Risiken (ehrliche Liste)

Regime-Abhängigkeit jedes Timing-Edges; Varianz vs Skill bei kurzen Live-Historien;
Anbieter-Konzentration (Alpaca ohne SLA); Ein-Personen-Governance (nur abmilderbar);
Rechts-/Steuerrechtsänderungen; die Möglichkeit, dass nach sauberer Validierung
schlicht **kein** ausreichender Edge existiert — das Projektergebnis „Baseline B3 oder
gar nicht live" ist ein akzeptierter, ehrlicher Ausgang.

## 4. Überarbeitung der Architektur nach Red Team (umgesetzt)

1. MLflow-Autolog-Pflicht auch für Notebook-Exploration; Trial-Zähler speist DSR (#1).
2. Lockbox-Öffnung erfordert externen Reviewer + signiertes Audit-Event (#7).
3. Ingestion-Allowlist blockt Nicht-Vintage-Makroserien technisch (#5).
4. Risk-Limit-**Erhöhungen** mit erzwungener 24-h-Verzögerung; Reduktionen sofort (#32).
5. Scale-up-Gate um Live-Daten-DSR-Update ergänzt (#42).
6. Quartalsweise Pflicht-Re-Validierung des Champions unabhängig von Alarmen (#40).
7. Databento als dritte, herkunftsunabhängige Quelle fest im Scale-up-Gate verankert (#8).
8. Dependency-Quarantäne (14 Tage) für Z-E-Services (#31).
9. Monatliches Alert-Review gegen Fatigue (#33); Notfallmappe für Operator-Ausfall (#34).
10. OFFEN-Punkte präzisiert: Alpaca-Key-Scopes/Withdrawal-Schutz, opg-Paper-Semantik,
    client_order_id-Duplikatverhalten — alle als Phase-5-Pflichttests eingeplant (#17/#24).

Diese Änderungen sind in die betroffenen Dokumente ([[09_RESEARCH_PLATFORM]],
[[13_RISK_ENGINE]], [[18_SECURITY]], [[19_OBSERVABILITY]], [[23_IMPLEMENTATION_ROADMAP]])
eingearbeitet bzw. dort als Regeln formuliert; die finale Architektur in
[[01_EXECUTIVE_SUMMARY]] §5 beschreibt den Stand **nach** diesem Review.
