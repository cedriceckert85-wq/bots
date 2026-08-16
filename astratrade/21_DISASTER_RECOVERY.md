# 21 — Business Continuity und Disaster Recovery

Zurück: [[00_HOME]] · Verwandt: [[19_OBSERVABILITY]], [[28_RUNBOOKS]]

**Leitprinzip:** Der sichere Zustand ist **„keine neuen Orders, Positionen halten"** —
ein Long-only-ETF-Portfolio ohne Leverage verträgt Tage ohne Eingriff. Kein Szenario
darf in automatische Panik-Liquidation führen; Liquidation ist immer manuell (4-Augen).

## 1. Ziele (Variante B)

| Datenklasse | RPO | RTO |
|---|---|---|
| Operative DB (Intents, Orders, Ledger) | ≤ 15 min (WAL-Archivierung) | 4 h |
| Raw Archive / Datasets | ≤ 24 h (tägl. Sync, Quelle re-fetchbar) | 24 h |
| Entscheidungsfähigkeit (Pipeline) | — | nächster Handelstag |
| Audit Events | ≤ 15 min | 24 h |

## 2. Szenarienkatalog (Auszug — vollständige Liste mit Reaktionen)

| Szenario | Erkennung | Sofortreaktion | Wiederanlauf |
|---|---|---|---|
| Internet/Strom lokal fällt aus (Variante A) | Dead-Man extern | System offline ⇒ keine Orders (safe) | Neustart, Recon, ggf. verpasste Auktion dokumentieren |
| Cloud-VM fällt aus | Dead-Man + Provider-Status | nichts nötig (fail-closed) | IaC-Reprovision + pgBackRest-Restore (RB-02) |
| Cloud-Region fällt aus | dito | dito | Restore in Zweitregion aus S3-Replikat |
| Datenanbieter (Massive) fällt aus | Ingestion-Alerts | Entscheidung mit Alpaca-Daten möglich? Nur wenn Cross-Check-Alternative existiert, sonst Fallback-Kaskade (kein Trade) | Backfill nach Rückkehr, Diff-Prüfung |
| Broker-API fällt aus | R-15, Ack-Latenz | HOLD bis 9:20 ET, dann Auction-Miss-Prozedur; niemals Blind-Queue | Status-Recon vor neuen Orders |
| Websocket „verbunden aber stumm" | Heartbeat-Timeout (10 s ohne Nachricht während Session) | Reconnect + REST-Backfill; Stale-Metrik | automatisch |
| Feed liefert falsche Preise | Cross-Source-Diff, Price Sanity | R-05 blockt; LOO-Limits begrenzen Schaden bereits platzierter Orders | Quelle klären, Korrektur-Manifest |
| DB korrupt | pg-Checks, Restore-Test-Alarm | Halt-Modus | Restore + **Datenvalidierung nach Restore** (Checksummen, Recon gegen Broker, Lückenanalyse) vor Freigabe |
| Outbox/Queue verliert Nachrichten | Outbox ist DB-Tabelle ⇒ verlustfrei; Backlog-Metrik | — | — |
| System startet doppelt | Lease/Fencing ([[14_EXECUTION_ENGINE]] §4) | zweiter Prozess bleibt passiv | — |
| Orderstatus unbekannt | Unknown-State | Symbol gesperrt, Lookup-Loop | [[16_RECONCILIATION]] §4 |
| Verspätete Fills | Recon | akzeptieren, Ledger nachbuchen | — |
| Zeitserver falsch | clock_drift-Metrik | R-23 blockt Submission | chrony-Fix, Drill RB-08 |
| Zertifikat läuft ab | cert_expiry-Alert 14 d vorher | — | Erneuerung (automatisiert, acme) |
| API-Key kompromittiert | Anomale Orders in Recon / Alpaca-Mail | globaler Kill + Rotation (RB-07) | Recon + Ursachenanalyse |
| Fehlerhaftes Deployment | Canary-Checks beim Start, Determinismus-Abweichung | Rollback auf voriges Image (Tags unveränderlich) | Post-Mortem |
| Modell erzeugt Extremgewichte | R-07/08/09 blocken; Prediction-Sanity (Forecast außerhalb historischer Spanne ⇒ Abstention) | Fallback-Kaskade | Review |
| Corporate Action nicht verarbeitet | CA-Recon Sev-1 | globaler Halt | Nachbuchung, Ursache, Regressionstest |
| Backup unbrauchbar | **monatlicher Restore-Test** (RB-06) schlägt an | — | Backup-Kette reparieren; bis dahin erhöhte Vorsicht (kein Risiko-Scale-up) |
| Operator nicht erreichbar | tote-Mann-Heartbeat | nach 5 Handelstagen automatischer Halt-Modus | Rückkehr + Recon |

## 3. Degraded Modes (definierte Zwischenzustände)

1. **DEGRADED_DATA:** nur eine Datenquelle verfügbar ⇒ Handel nur, wenn Vortagesdaten
   beider Quellen konsistent waren und heutige Einzelquelle Sanity-Checks besteht;
   sonst kein Trade.
2. **DEGRADED_BROKER:** API instabil ⇒ nur Reduktions-Intents zulässig.
3. **HALT:** keine neuen Orders; Monitoring läuft weiter.
4. **DELEVERAGE:** Cap 50 % Exposure, nur Reduktionen.
Übergänge automatisch (Trigger dokumentiert je Szenario) oder manuell; jeder Wechsel =
Audit + Alert.

## 4. Wiederanlaufreihenfolge (Runbook RB-03, geübt im Quartals-Drill)

1. Infrastruktur (DB, Storage, Zeit-Sync prüfen: chrony < 100 ms).
2. Restore-Validierung (falls Restore): Checksummen, letzte Manifeste, Audit-Kette.
3. **Order-/Position-/Cash-Reconciliation gegen Broker — Pflicht vor jedem Trading.**
4. Konfigurationsvalidierung (R-01), Lease neu erwerben.
5. Ingestion-Backfill fehlender Daten + Validierung.
6. Erst dann: Outbox-Verarbeitung freigeben; erste Entscheidung im Supervised-Modus
   (Operator bestätigt Intents manuell).

Bedingungen für **manuellen Handel** (Broker-Dashboard): System > 24 h nicht
wiederherstellbar UND Risikoreduktion nötig (z.B. R-17 verletzt); dokumentationspflichtig.
Bedingungen für **Handelsstopp**: jede Sev-1-Ursache ungeklärt, Recon nicht grün,
Audit-Kette verletzt.

## 5. Backups

pgBackRest (Full wöchentlich, Diff täglich, WAL kontinuierlich) → S3 versioniert +
Object Lock (Ransomware-Schutz); Raw Archive und Datasets: S3-Versionierung +
Zweitregion-Replikation; Konfig/Code: Git (GitHub + lokaler Mirror); **monatlicher
automatisierter Restore-Test** in Wegwerf-Container mit Checksummen-Vergleich —
ungetestete Backups gelten als nicht existent.
