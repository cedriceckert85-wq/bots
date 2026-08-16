# 19 — Observability: Metrics, Logs, Traces, Alerts, SLOs

Zurück: [[00_HOME]] · Verwandt: [[21_DISASTER_RECOVERY]], [[28_RUNBOOKS]]

Stack (ADR-013): **Prometheus + Grafana + Loki + Alertmanager**, OpenTelemetry-SDK in
allen Services; Uptime-Fremdüberwachung (healthchecks.io o.ä.) als
Dead-Mans-Monitor für die Pipeline selbst. Begründung: Standard, selbst hostbar,
kostenarm; verworfen: ELK (Betriebslast), SaaS-APM (Datenabfluss, Kosten).

## 1. Metriken (Pflichtkatalog)

**Daten:** `feed_latency_seconds`, `ingestion_lag_seconds`, `missing_bars_total`,
`duplicate_bars_total`, `stale_symbols`, `correction_rate`, `semantic_drift_bps`,
`cross_source_diff_bps`.
**Entscheidung:** `prediction_latency_seconds`, `prediction_distribution` (Histogramm),
`target_turnover`, `abstention_rate`, `fallback_level`.
**Execution:** `order_submission_latency_seconds`, `broker_ack_latency_seconds`,
`fill_rate`, `rejection_rate`, `auction_miss_total`, `slippage_bps` (Histogramm),
`unknown_order_state`, `dead_letter_total`.
**Ledger/Recon:** `reconciliation_breaks{severity}`, `cash_mismatch_usd`,
`position_mismatch_shares`, `nav_usd`, `pnl_daily_usd`, `drawdown_pct`,
`rounding_tracking_error_bps`.
**Modell:** `feature_psi`, `prediction_drift_ks`, `calibration_brier`, `cusum_stat`.
**Plattform:** `job_failures_total`, `queue_depth` (Outbox-Backlog), `db_health`,
`disk_usage_pct`, `backup_age_hours`, `clock_drift_ms`, `execution_leader_info`,
`kill_switch_state`, `cert_expiry_days`.

## 2. SLIs/SLOs (Fehlerbudget je Quartal)

| SLI | SLO |
|---|---|
| Entscheidungspipeline fertig bis 08:30 ET | 99 % der Handelstage |
| Orders submitted bis 09:20 ET (wenn Intents existieren) | 99,5 % |
| Tages-Reconciliation grün bis 18:00 ET | 99 % |
| Daten-Vollständigkeit (Daily-Bars validiert bis 17:30 ET) | 99,5 % |
| Kill Switch wirksam (Testdrill) | 100 % (monatlicher Drill) |

Budget-Verbrauch > 100 % ⇒ Feature-Freeze, Reliability-Review (leichtgewichtiges
Error-Budget-Modell; bei Ein-Personen-Betrieb als Selbstverpflichtung + Checkliste).

## 3. Logs und Audit

Strukturierte JSON-Logs; Pflichtfelder: ts, service, level, correlation_id,
causation_id, portfolio_id, intent_id (falls zutreffend); Secrets-Scrubber
([[18_SECURITY]] §2); Retention: App-Logs 90 Tage (Loki), Audit-Events 10 Jahre
(Postgres + Backup, hash-verkettet); Zugriff: Logs read-only via Grafana, Audit nur
Operator.

## 4. End-to-End-Trace eines Trades

`correlation_id` wird beim täglichen Entscheidungslauf erzeugt und durch alle Events
gereicht: MarketDataValidated → FeatureDatasetPublished → PredictionGenerated →
TargetPortfolioGenerated → RiskCheckCompleted → OrderIntentCreated → OrderSubmitted →
OrderFilled → ReconciliationCompleted. Zusätzlich FK-Lineage ([[08_DATA_CONTRACTS]] §6):
`astra lineage <fill_id>` liefert Manifeste, dataset_version, model_version,
config_version, Risk-Entscheidungen und Ledger-Buchungen — jeder Trade ist auf Daten-,
Modell- und Konfigurationsversion zurückführbar (Abschlussprüfungs-Kriterium).

## 5. Alert-Katalog (Auszug; jeder Alert hat Runbook-Ref in [[28_RUNBOOKS]])

| Alert | Trigger | Sev | Kanal | Auto-Reaktion | Recovery-Kriterium |
|---|---|---|---|---|---|
| FeedStale | keine validierten Bars bis 17:30 ET | 2 | Push+Mail | Pipeline wartet; Fallback-Kaskade | Daten nachgeliefert + validiert |
| CrossSourceDiff | Diff > 25 bps | 1 | Push (persistent) | R-05 blockt Handel | Ursache dokumentiert, Quelle korrigiert |
| ReconBreakSev1 | siehe [[16_RECONCILIATION]] §2 | 1 | Push+Mail | globaler Halt | RB-05 abgeschlossen |
| UnknownOrder | > 10 min unknown | 1 | Push | Symbol gesperrt | Status geklärt |
| AuctionMiss | OPG unfilled | 3 | Mail | Auction-Miss-Prozedur | Folge-Intent entschieden |
| DrawdownLimit | R-17-Schwellen | 1–2 | Push | Deleveraging/Halt | manueller Review |
| ModelDrift | PSI/CUSUM-Schwellen | 2 | Mail | Degraded-Modus | Review + Retrain/Rollback |
| BackupStale | backup_age > 26 h | 2 | Mail | — | Backup erfolgreich |
| ClockDrift | > 500 ms | 1 | Push | R-23 blockt | NTP fix |
| CertExpiry | < 14 Tage | 3 | Mail | — | erneuert |
| LeaderLost | keine Lease > 60 s während Handelsfenster | 1 | Push | Submission stoppt (fail-closed) | Leader wieder aktiv + Recon grün |
| PipelineDeadMan | healthchecks.io kein Ping | 1 | Push extern | — | Pipeline läuft |

Eskalation (Ein-Operator-Modell): Push (Mobil) → nach 30 min unbestätigt: Anruf via
Twilio/Signal-Bot [ANNAHME: einzurichten] → nach 24 h unbestätigt: System bleibt/geht
in Halt-Modus (tote-Mann-Logik, [[13_RISK_ENGINE]] §3).
