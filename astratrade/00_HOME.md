# ASTRATRADE — Architektur- und Entwicklungsplan (HOME)

Deep Research & Professional Trading System Architecture · Stand: 2026-08-16 ·
Rechercheabruf: 2026-08-15 · Status: **v1.0 — alle Phasen 1–8 abgeschlossen,
Red-Team-überarbeitet**

## Leseanleitung

Einstieg: [[01_EXECUTIVE_SUMMARY]] (Kernentscheidungen + finale Architektur).
Für Umsetzer: [[23_IMPLEMENTATION_ROADMAP]] (inkl. der nächsten 20 Schritte).
Jede Tatsachenbehauptung ist über IDs mit dem [[29_SOURCE_LEDGER]] verknüpft;
Annahmen sind als [ANNAHME], vorgegebene Regeln als [REGEL] markiert.

## Dokumente

| Nr | Dokument | Inhalt |
|---|---|---|
| 01 | [[01_EXECUTIVE_SUMMARY]] | Zusammenfassung, Kern-Diagramme, finale Architektur, offene Entscheidungen |
| 02 | [[02_REQUIREMENTS]] | Anforderungen, NFRs, Annahmen, Blocker, Regel-Prüfung |
| 03 | [[03_RESEARCH_FINDINGS]] | Rechercheergebnisse aller vier Stränge + Alternative Daten/NLP |
| 04–06 | [[04_STRATEGY_TRACK_A]] · [[05_STRATEGY_TRACK_B]] · [[06_STRATEGY_TRACK_C]] | Hypothesen, Features, Modell-Leitern, Benchmarks, Gates je Track |
| 07 | [[07_MARKET_DATA]] | Anbieterbewertung, Zwei-Quellen-Entscheidung, Feed-Semantik |
| 08 | [[08_DATA_CONTRACTS]] | Manifeste, Bitemporalität, Feed-Trennung, Lineage |
| 09 | [[09_RESEARCH_PLATFORM]] | Validierungsprotokoll, Leakage-Tests, Lockbox, Gate-Katalog |
| 10 | [[10_BACKTESTING]] | Framework-Recherche, Build-vs-Buy, Engine-Design, Kostenmodell |
| 11 | [[11_ML_ARCHITECTURE]] | MLOps-Stack, Model Lifecycle, Drift, LLM-Grenzen |
| 12 | [[12_PORTFOLIO_CONSTRUCTION]] | Begriffskette, Constraints, Whole-Share-Logik |
| 13 | [[13_RISK_ENGINE]] | 24 Pre-Trade-Checks, In-/Post-Trade, Kill-Switch-Hierarchie |
| 14 | [[14_EXECUTION_ENGINE]] | OPG-Zeitplan, Outbox, Idempotenz, Lease/Fencing, Broker Adapter |
| 15 | [[15_ORDER_STATE_MACHINE]] | State Machine, Datenmodelle, Event- und API-Contracts |
| 16 | [[16_RECONCILIATION]] | Abgleichstypen, Break-Klassen, Unknown-Order-Auflösung |
| 17 | [[17_DUAL_LEDGER]] | Broker vs Economic Ledger, NAV/TWR, Paper-Verzerrungen |
| 18 | [[18_SECURITY]] | Zonen, Secrets, Supply Chain, Threat Model |
| 19 | [[19_OBSERVABILITY]] | Metriken, SLOs, Logs/Audit, Traces, Alert-Katalog |
| 20 | [[20_INFRASTRUCTURE]] | Varianten A/B/C, Deployment, Monorepo, Konfiguration |
| 21 | [[21_DISASTER_RECOVERY]] | Szenarien, RPO/RTO, Degraded Modes, Wiederanlauf |
| 22 | [[22_TEST_STRATEGY]] | Testpyramide, Given/When/Then-Fälle, Drill-Kalender |
| 23 | [[23_IMPLEMENTATION_ROADMAP]] | Phasen 0–8, kritischer Pfad, MVP, nächste 20 Schritte |
| 24 | [[24_COST_MODEL]] | Kosten je Phase, Fixkosten-Drag, Kostenregeln |
| 25 | [[25_TEAM_AND_SKILLS]] | Rollenmatrix, 4-Augen-Ersatz, externe Pflichten |
| 26 | [[26_ADR_INDEX]] | 19 Architekturentscheidungen mit Neubewertungs-Triggern |
| 27 | [[27_RED_TEAM_REVIEW]] | 42-Szenarien-FMEA, Top-10-Verlustwege, Überarbeitungen |
| 28 | [[28_RUNBOOKS]] | RB-01..12 für alle kritischen Alarme |
| 29 | [[29_SOURCE_LEDGER]] | alle Claims mit Quelle, Vertrauen, Änderungsrisiko, Offen-Liste |
| 30 | [[30_GLOSSARY]] | verbindliche Begriffsdefinitionen |

## Zuordnung zur geforderten Endausgabe-Struktur

1 Executive Summary → 01 · 2 Recherche-Erkenntnisse → 03 · 3 Quellen-/Evidenzbewertung
→ 29 (+03 Methodik) · 4–5 Anforderungen/NFR → 02 · 6 Strategietracks → 04–06 ·
7 Anbieter-/Technologievergleich → 07, 10, 26 · 8–10 Architektur/Diagramme/Katalog →
01, 15, 20 (Diagramm-Verzeichnis in 01 §4) · 11–12 Datenarchitektur/-modelle → 08, 15 ·
13–14 Event-/API-Contracts → 15 · 15 Research/Backtesting → 09, 10 · 16 ML-Governance
→ 11 · 17 Portfolio/Risiko → 12, 13 · 18 Execution/Order-SM → 14, 15 · 19 Recon/Dual
Ledger → 16, 17 · 20 Security → 18 · 21 Observability → 19 · 22 BC/DR → 21 ·
23–24 Infrastruktur/Kosten → 20, 24 · 25 Repo → 20 §6 · 26 Tests → 22 · 27 Roadmap →
23 · 28 Team → 25 · 29–30 Red Team/finale Architektur → 27, 01 §5 · 31 Offene
Entscheidungen → 01 §6 · 32 nicht technisch lösbare Risiken → 27 §3 · 33 nächste 20
Schritte → 23 · 34 Source Ledger → 29 · 35 Glossar → 30.

## Interne Konsistenzprüfung (Abschlussprüfung, durchgeführt)

- Diagramme ↔ Text: Container-Diagramm (01) deckt Servicekatalog (15/20) und
  Repo-Struktur (20 §6) deckungsgleich ab. ✔
- Trade-Rückverfolgbarkeit: FK-Lineage-Kette 08 §6 + correlation_id 19 §4. ✔
- Kein Pfad Modell→Order ohne Risk: nur Risk schreibt approval_state (DB-Grant,
  18 §3); Execution liest nur approved Outbox (14 §3). ✔
- Doppelte Orders: deterministische intent_id + UQ-Constraint + Lookup-before-send +
  Fencing (14 §3/§4, T-EXE-01/02). ✔
- Split Brain: Lease+Fencing+Trigger (14 §4, T-SPL-01). ✔
- Fehlerhafter Feed: Zwei-Quellen-Diff R-05 fail-closed (07 §3, 13). ✔
- Research-/Live-Daten-Verwechslung: Zonen (18 §1), getrennte Credentials, Datasets
  read-only. ✔
- Holdout-Mehrfachnutzung: lockbox_guard + Touched-Status + externer Reviewer (09 §7,
  27 §4). ✔
- Ledger-Trennung: ein Schema, hartes ledger_type-Feld, getrennte Abgleiche (17). ✔
- Kritische Fehler alarmiert + Runbook je Alarm: Alert-Katalog 19 §5 ↔ RB-01..12. ✔
- Restart-Zustand eindeutig: persistente State Machine + RB-03-Pflichtreihenfolge. ✔
- Unbekannter Brokerstatus ⇒ kein Weiterhandeln: Unknown-State sperrt Symbol (16 §4). ✔
- Kosten/Abhängigkeiten sichtbar: 24 + configs. ✔ · Regulatorische Blocker markiert:
  BL-01..04 (02 §5). ✔ · Keine erfundenen Performancewerte: bestätigt — das Vault
  enthält ausschließlich Methoden und Schwellen, keine Ergebnisse. ✔
