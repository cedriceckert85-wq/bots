# 26 — ADR-Index (Architecture Decision Records)

Zurück: [[00_HOME]] · Format je ADR: Problem, Anforderungen, Optionen, Kriterien,
Vor-/Nachteile, Security-/Kosten-Wirkung, Entscheidung, Begründung, Folgen,
Neubewertungs-Trigger. Vollversionen entstehen als `docs/adr/ADR-xxx.md` in Phase 0;
hier der beschlossene Kern mit Kurzbegründung und Confidence.

| ADR | Entscheidung | Kernbegründung / Alternativen | Neubewertung wenn | Conf. |
|---|---|---|---|---|
| 000 Sprache | Python 3.12+, strikt typisiert | Ökosystem (Daten/ML), Team-Skill; Alt.: Rust-Kern (später punktuell) | Latenzbedarf < 1 s entstünde | hoch |
| 001 Systemfrequenz | Daily-Entscheidung + Opening-Auction-Ausführung | eliminiert Latenz-/Intraday-Komplexität; Alt.: Intraday (verworfen: Kosten/Edge unbelegt) | belegter Intraday-Edge | hoch |
| 002 Backtest-Engine | Eigenbau schlank + vectorbt-Exploration + Zweit-Engine-Cross-Check | [[10_BACKTESTING]] §2; Alt.: LEAN (Lock-in), zipline (Bundle-Zwang) | Universum > 50 Instr. oder Intraday | hoch |
| 003 Orchestrierung | Dagster (Batch) + eigene Execution-State-Machine | Asset-Lineage first-class; Alt.: Airflow/Prefect/Temporal | Betriebsprobleme Dagster | mittel |
| 004 Validierung | Walk-Forward + Purged/Embargo-CV (skfolio) + DSR/PBO, Lockbox | Stand der Forschung; mlfinlab tot [LDP-1] | — | hoch |
| 005 Messaging | Postgres-Outbox + LISTEN/NOTIFY; kein Broker-Bus bis Var. C | 1 Entscheidung/Tag: Bus = Betriebslast ohne Nutzen; Contracts bleiben bus-fähig | > 10 Events/s dauerhaft | hoch |
| 006 Marktdaten | Massive (historisch) + Alpaca ATP (live) + Cross-Check; ALFRED/Treasury für Makro | [[07_MARKET_DATA]] §3; Alt.: nur Alpaca (Klumpenrisiko), Databento (Historie) | Preis-/Lizenzänderung, PIT-Bedarf Referenzdaten | hoch |
| 007 Storage | Postgres+Timescale (operativ/Bars), Parquet+DuckDB (Research), S3 (Raw/Datasets/Backup) | ein DB-System für OLTP+Zeitreihen; Alt.: ClickHouse (erst > 1 TB) | Datenvolumen/Latenz | hoch |
| 008 Dateiformat | Parquet (zstd), Schemas versioniert; Delta/Iceberg nicht in V1 | Einfachheit; Table-Format-Nutzen erst bei vielen Writern | Multi-Writer-Bedarf | hoch |
| 009 Feature Mgmt | Registry + versionierte Datasets; kein Feast | kein Online-Serving in V1 | Online-Inference | hoch |
| 010 Experiment/Registry | MLflow self-hosted | Standard, Registry-Stages; Alt.: W&B (SaaS) | Teamgröße/Cloud-Wechsel | hoch |
| 011 Repo | Monorepo | [[20_INFRASTRUCTURE]] §6 | > 4 Entwickler | hoch |
| 012 Deployment | Docker Compose (A/B), K8s erst C; IaC ab B (Terraform/Ansible) | Betriebslast minimieren | Skalierung/Team | hoch |
| 013 Monitoring | Prometheus/Grafana/Loki/Alertmanager + OTel + externer Dead-Man | selbst hostbar, Standard | Betriebslast | hoch |
| 014 Secrets | sops+age & Docker-Secrets (A/B); Vault/KMS (C) | angemessen zur Teamgröße; Rotation als Prozess | Team/Cloud | mittel |
| 015 Broker | Alpaca (V1) | OPG-Support, 0 Kommission, Paper-Env, API-Qualität; Alt.: IB (Fallback-Pfad) | Zuverlässigkeitsbefund Paper-Phase, DE-Onboarding-Problem | mittel-hoch |
| 016 Broker Adapter | Port/Adapter-Muster, brokeragnostische Domäne | Austauschbarkeit (IB) ohne Kernänderung | — | hoch |
| 017 Config | Pydantic-typisierte YAML, gehasht in configuration_versions, fail-closed | [[20_INFRASTRUCTURE]] §7 | — | hoch |
| 018 CI/CD & Tests | GitHub Actions; Testpyramide [[22_TEST_STRATEGY]]; kein Auto-Deploy in Prod | Kontrolle > Geschwindigkeit bei Geldsystemen | — | hoch |

Anti-Hype-Klausel (verbindlich): neue Technologie nur via ADR mit nachgewiesenem
Problem, das eine bestehende Komponente nicht löst; „moderner" ist kein Argument.
