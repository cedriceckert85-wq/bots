# 22 — Teststrategie

Zurück: [[00_HOME]] · Verwandt: [[09_RESEARCH_PLATFORM]], [[21_DISASTER_RECOVERY]]

## 1. Testpyramide und Gates

| Ebene | Werkzeuge | Läuft wann |
|---|---|---|
| Unit + Property-Based (Hypothesis) | pytest | **jeder Commit (blockierend)** |
| Schema-/Contract-Tests (Events, Configs, DDL-Migrationen) | jsonschema, alembic-check | jeder Commit (blockierend) |
| Leakage-/Determinismus-Tests (T-LEAK-01..05, T-DET-01/02) | pytest + Golden Hashes | jeder Commit auf libraries/ (blockierend) |
| Integration (Service↔DB↔Outbox, Docker Compose) | pytest + testcontainers | jeder PR (blockierend) |
| Golden-Dataset-Backtests ([[10_BACKTESTING]] §6) | astra-backtest | jeder PR auf Engine/Strategie (blockierend) |
| Broker-Sandbox-Tests (Alpaca Paper: Ordertypen, opg-Semantik, client_order_id-Duplikate, Partial Fills) | pytest live gegen Paper-API | **nächtlich** |
| Replay-Tests (aufgezeichnete Feed-Tage durch Live-Pfad) | Replay-Harness | nächtlich |
| Chaos-/Restart-/Partition-Tests (Prozess-Kill mitten in Submission, DB-Failover, Netz-Drop, Duplicate-Message-Injection) | toxiproxy, Skripte | wöchentlich + **vor jedem Deployment** |
| Load (Ingestion-Backfill, 10× Symbolzahl) | Skripte | vor Skalierungsschritten |
| Security (gitleaks, pip-audit/OSV, Trivy) | CI | jeder Commit + nächtlich |
| DR-/Restore-Tests | RB-06-Automation | monatlich |
| Reconciliation-E2E (synthetische Breaks jeder Klasse) | Harness | wöchentlich |
| End-to-End Paper (voller Tageszyklus) | Staging-Paper-Konto | **vor jedem Deployment** |
| Vor Modellfreigabe | kompletter Gate-Satz [[09_RESEARCH_PLATFORM]] §8 + Reproduzierbarkeit (T-DET-02) | je model_version |
| In Produktion regelmäßig | Kill-Switch-Drill (monatlich), Restore-Test (monatlich), Wiederanlauf-Drill (quartalsweise), Cross-Source-Diff (täglich, ohnehin) | Kalender |
| Manual Acceptance | Checklisten je Phase-Gate | je Phase |

## 2. Ausgewählte Testfälle (Given/When/Then)

**T-EXE-01 Idempotente Submission nach Crash**
Given ein approved Intent, Submission gesendet, Prozess stirbt vor Ack.
When die Engine neu startet und Recovery-Recon läuft.
Then findet der `client_order_id`-Lookup die Order, der Intent wird auf `Submitted`
adoptiert, und es existiert **genau eine** Broker-Order.

**T-EXE-02 Duplicate-Message**
Given ein `OrderFilled`-Event wurde verarbeitet.
When dasselbe Event (gleiche event_id) erneut zugestellt wird.
Then ändern sich fills, positions und ledger_entries nicht (Dedup-Constraint greift).

**T-EXE-03 Partial Fill an der Auktion**
Given OPG-Order über 10 Stück, Paper füllt 4.
When die Auktion endet.
Then Status `PartiallyFilled→Canceled(Rest)`, Auction-Miss-Prozedur bewertet die
Restmenge, Ledger bucht exakt 4 Stück, Recon ist grün.

**T-RSK-01 Cash-Check mit SELL-Erlösen**
Given gleichzeitige SELL- (Erlös erwartet 5.000) und BUY-Intents (Bedarf 5.500), Cash 800.
When R-12 läuft.
Then BUY wird zugelassen nur bis 800 + 0,98×5.000 = 5.700 ≥ 5.500 ⇒ pass; bei Bedarf
5.800 ⇒ BLOCK des übersteigenden Intents.

**T-LEAK-02 Zeitmaschine** ([[09_RESEARCH_PLATFORM]] §5)
Given Entscheidungstag t und eine später eingespielte Korrektur der Bar von t−1.
When das Dataset für t mit `as_of=t` gebaut wird.
Then enthält es die Originalbar, nicht die Korrektur; mit `as_of=heute` die Korrektur.

**T-CAL-01 Half-Day**
Given der Handelstag nach Thanksgiving (Close 13:00 ET).
When ein `cls`-Intent geplant würde bzw. Session-Checks laufen.
Then verwendet das System die korrekten Auktionszeiten aus market_sessions und die
Submission-Deadlines verschieben sich entsprechend.

**T-TZ-01 DST-Divergenz**
Given eine US-Sommerzeit-Woche, in der Europa noch Winterzeit hat.
When der Scheduler die 9:20-ET-Deadline berechnet.
Then liegt sie korrekt in UTC (Test mit beiden DST-Übergängen und tzdata-Pin).

**T-CA-01 Split**
Given ein 4:1-Split eines gehaltenen ETF am Ex-Tag.
When CA-Verarbeitung + Recon laufen.
Then Stückzahl ×4, Kostenbasis /4, NAV unverändert (±0,01 USD), Economic Ledger
bucht das Ereignis, kein Break.

**T-SPL-01 Split-Brain**
Given zwei Execution-Prozesse, Netzwerkpartition, alter Leader hält abgelaufene Lease.
When der alte Leader eine Submission versucht.
Then verwirft der Fencing-Trigger den Schreibzugriff; keine Order erreicht den Broker;
Alert LeaderLost feuert.

**T-DR-01 Restore-Validierung**
Given ein pgBackRest-Restore in frischem Container.
When die Validierung läuft.
Then stimmen Zeilenzahlen+Checksummen definierter Tabellen mit dem Quellsystem-Stand
des Backup-Zeitpunkts überein und die Audit-Hash-Kette ist intakt.
