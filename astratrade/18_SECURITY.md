# 18 — Security-Architektur

Zurück: [[00_HOME]] · Verwandt: [[20_INFRASTRUCTURE]], [[21_DISASTER_RECOVERY]]

## 1. Zonenmodell (Netzwerksegmentierung)

| Zone | Inhalt | Regeln |
|---|---|---|
| **Z-R Research** | JupyterLab, Backtests, MLflow | read-only auf Datasets; **keine Broker-Keys, keine Live-DB**; Internet nur über Allowlist (Paketquellen, Datenanbieter) |
| **Z-D Data** | Ingestion, Raw Archive, TimescaleDB | Data-API-Keys (read-only-Scopes); kein Zugriff auf Z-E |
| **Z-E Execution** | Risk, Execution, Broker Adapter, operative Postgres | einziger Ort mit Broker-Keys; Egress-Allowlist: nur Alpaca-Endpoints + NTP; kein Inbound außer Control Plane über mTLS |
| **Z-O Operator** | Control Plane UI/CLI, Monitoring | MFA-Pflicht; Zugriff auf Z-E nur über definierte API, nie direkt auf DB |

Umsetzung Variante A/B: getrennte Docker-Netze + Host-Firewall (nftables) + WireGuard
für Remote-Zugriff; Variante C: getrennte VPCs/Subnets ([[20_INFRASTRUCTURE]]).

## 2. Secrets

- **Secret Manager:** Variante A/B: `sops`-verschlüsselte Dateien (age-Key auf
  Hardware-Token) für Bootstrap + Docker-Secrets zur Laufzeit; ab Variante B empfohlen,
  ab C Pflicht: HashiCorp Vault bzw. Cloud-KMS mit dynamischen Leases (ADR-014).
- Regeln: keine Secrets in Code, Notebooks, Logs, Chats, unverschlüsselten Configs
  (CI-Scan: gitleaks, pre-commit + Pipeline); Log-Scrubber maskiert Key-Muster;
  Paper- und Live-Keys sind **verschiedene Alpaca-Keys mit verschiedenen Konten**,
  Live-Key existiert nur in Z-E.
- **Rotation:** Broker-Keys 90 Tage bzw. sofort bei Verdacht (Runbook RB-07:
  neuen Key erzeugen → deployen → alten revoken → Audit-Event); Daten-API-Keys 180 Tage.
- **Break-Glass:** versiegelter Offline-Umschlag/Passwort-Manager-Notfallzugang mit
  Alpaca-Login (nicht API-Key) für manuelle Liquidation, wenn das System weg ist;
  Nutzung löst Pflicht-Audit + Rotation aus.

## 3. Supply Chain und Plattform

- Dependencies: Lockfiles (uv/poetry), Renovate-PRs, `pip-audit`/OSV-Scan in CI;
  Container: schlanke Basisimages, Digest-Pinning, Trivy-Scan, SBOM (syft) je Release,
  Image-Signierung (cosign) ab Variante B.
- Patch-Management: Host unattended-upgrades (Security), monatliches Patch-Fenster mit
  Runbook; Kernel-/Docker-Updates nie automatisch am Handelstag vor der Auktion.
- Least Privilege: Services laufen als eigene User, DB-Rollen minimal (Risk darf
  approval_state schreiben, sonst niemand; Ledger-Rollen INSERT-only auf append-only-
  Tabellen — DB-Grants erzwingen die Architekturregeln).
- MFA für: Broker-Dashboard, Cloud-Konten, GitHub, VPN, Grafana-Admin.

## 4. Bedrohungsszenarien (Auszug Threat Model; vollständige FMEA in [[27_RED_TEAM_REVIEW]])

| Szenario | Kontrollen |
|---|---|
| Gestohlener Broker-API-Key | Egress-Allowlist (Key nur aus Z-E nutzbar wäre Angreifer-seitig egal ⇒ entscheidend:) Alpaca-Key ohne Withdrawal-Berechtigung [zu verifizieren, ob Alpaca Scopes bietet — OFFEN], Anomalie-Alert auf unerwartete Orders via Reconciliation, Rotation, Kill Switch |
| Kompromittierter Datenfeed / falsche Preise | Zwei-Quellen-Diff (R-05), Price-Sanity, LOO-Limits statt MOO |
| Manipulierte Konfiguration | Config-Signierung (Hash in configuration_versions, 4-Augen für risk_limits), Startvalidierung R-01 |
| Kompromittiertes Modellartefakt | Registry-Hashes, Deployment nur signierter Artefakte, Shadow-Vergleich |
| Insider/Bedienfehler | 4-Augen für Liquidation & Limit-Änderungen, append-only Audit mit Hash-Kette, tägliche Reports |
| Ransomware | Offline-/Immutable-Backups (Object Lock), getestete Restores ([[21_DISASTER_RECOVERY]] §5), Zonen-Trennung |
| Notebook exfiltriert Live-Daten | Z-R hat keinerlei Route zu Z-E; Datasets enthalten keine Kontodaten |

## 5. Audit Logging

`audit_events` hash-verkettet (prev_hash), täglicher Anker-Hash extern gespeichert
(z.B. Commit in privates Git-Repo) ⇒ Manipulation nachweisbar; Retention 10 Jahre;
Zugriff read-only für Operator, Schreibzugriff nur systemisch. Struktur und Trace-
Verknüpfung: [[19_OBSERVABILITY]] §3.
