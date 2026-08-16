# 14 — Execution Engine und Broker Adapter

Zurück: [[00_HOME]] · Verwandt: [[15_ORDER_STATE_MACHINE]], [[16_RECONCILIATION]], [[13_RISK_ENGINE]]

## 1. Execution-Ansatz (geprüft gegen Brokerdoku)

**Default: Whole Shares, Alpaca, Opening-Auction (`opg`, MOO als Market-, LOO als
Limit-Variante).** Recherche-Ergebnis ([[03_RESEARCH_FINDINGS]] §2): umsetzbar —
`opg` mit market/limit unterstützt, Cut-off 9:28 ET, Fractional ist mit `opg`
inkompatibel (bestätigt Whole Shares). Zeitplan (ET):

```
16:10 (T−1)  Daily-Bars T−1 ingestiert/validiert
17:30        Features, Predictions, Target Portfolio, Risk-Checks (Batch, Dagster)
18:00        Order Intents erzeugt (approval_state=approved), Operator-Report
19:05        Submission-Fenster öffnet (opg-Queue für nächste Auktion; Alpaca: nach 19:00 ET)
08:30 (T)    Health-Recheck (R-03/05/15/23), letzte Abbruchmöglichkeit
09:20        harte Submissions-Deadline (8 min Puffer vor 9:28-Cut-off)
09:30+       Auction Fills via trade_updates-Stream; danach Fill-Reconciliation
16:30        Tages-Reconciliation, Ledger-Update, Report
```

**LOO statt MOO [EMPFEHLUNG, Confidence mittel]:** Limit-on-Open mit Limit =
letzter validierter Close ± Slippage-Budget (Buy: +75 bps, Sell: −75 bps [ANNAHME])
schützt gegen anomale Auktionspreise (Fat-Finger-Open, Feed-Fehler); Trade-off:
Nichtausführung bei Gap > Budget ⇒ Auction-Miss-Prozedur ([[13_RISK_ENGINE]] §2).
Paper-Phase testet MOO vs LOO empirisch.

## 2. Order Intents (transaktionale Quelle jeder Order)

Pflichtfelder (Schema in [[15_ORDER_STATE_MACHINE]] §5): deterministic intent_id
(uuid5 aus portfolio_id, symbol, decision_date, target_portfolio_id, side),
strategy_id+version, portfolio_id, decision_ts, target_ts (Auktionstag), symbol,
current_qty, current_weight, target_weight, target_qty, side (buy/sell), reason_code
(rebalance | risk_reduction | fallback | liquidation | manual), expected_price,
limit_logic, max_slippage_bps, risk_check_version, approval_state
(pending|approved|rejected|expired), broker_destination, execution_policy
(opg_loo | opg_moo | day_limit_fallback), expiry (Auktionszeit + Grace),
retry_status, reconciliation_status.

## 3. Transactional Outbox und Idempotenz

- Intent-Erzeugung, Risk-Decision und Outbox-Eintrag geschehen in **einer**
  DB-Transaktion (PostgreSQL). Der Submitter liest ausschließlich die Outbox.
- `client_order_id = intent_id` (Alpaca erlaubt clientseitige IDs [AL-12]). Vor jeder
  Submission: Lookup `GET /v2/orders:by_client_order_id`; existiert die Order bereits
  (z.B. nach Crash zwischen Send und Ack) ⇒ Zustand adoptieren statt neu senden.
  Da harte Broker-Duplikatablehnung unverifiziert ist, ist dieser
  Lookup-before-send + persistenter State der maßgebliche Duplicate-Schutz.
- **Keine Blind-Retries:** Retry nur nach explizitem Status-Lookup; Retry-Budget
  (3 Versuche, exponentiell 2/4/8 s) nur für idempotente Reads und für Submissions
  mit bestätigtem Nicht-Empfang; danach Dead-Letter (`order_intents.retry_status =
  dead_letter`) + Alert Sev-2 + Halt des betroffenen Portfolios.

## 4. Single-Writer-Garantie (genau eine aktive Execution-Instanz)

- **Lease-Tabelle in PostgreSQL:** `execution_leases(portfolio_id PK, leader_id,
  fencing_token BIGSERIAL, expires_at)`; Anmeldung via
  `INSERT ... ON CONFLICT ... WHERE expires_at < now()`; Lease-TTL 30 s,
  Heartbeat alle 10 s (Zeit aus DB `now()`, nicht lokale Uhr ⇒ Clock-Skew-resistent).
- **Fencing Token:** monoton steigend; jeder Schreibzugriff auf Outbox/Submission
  trägt das Token; Trigger verwerfen Schreibversuche mit veraltetem Token —
  ein „Zombie-Leader" nach Netzwerkpartition kann nichts mehr bewirken (Split-Brain-Schutz).
- Broker-seitige zweite Verteidigungslinie: `client_order_id`-Namespace enthält das
  Fencing-Token **nicht** (IDs bleiben deterministisch je Intent) — Duplikate durch
  zwei Leader kollidieren daher am selben client_order_id-Lookup.
- Verhalten bei Partition: Leader verliert Lease ⇒ stellt Submission sofort ein
  (lokaler Watchdog), geht in Read-only; kein automatischer Failover-Start neuer
  Orders ohne frische Reconciliation ([[21_DISASTER_RECOVERY]] §3). Es gibt keinen
  Auto-Standby in Variante A/B — Neustart ist manuell bzw. supervised (systemd),
  Leader-Election-Konzept ist damit bewusst trivial gehalten.

## 5. Broker Adapter (Port/Adapter-Muster, ADR-016)

Interface `BrokerPort`: submit(intent)→ack, cancel(order_ref), replace(...),
get_order(client_order_id), stream_updates(), get_positions(), get_account(),
get_activities(range). Implementierungen: `AlpacaPaperAdapter`, `AlpacaLiveAdapter`
(getrennte Credentials/Endpoints, [[18_SECURITY]]), später `IBAdapter`. Der Adapter
ist zustandslos; State lebt in der Order State Machine. Rate-Limit-Budget (200/min)
wird adapterintern mit Token-Bucket durchgesetzt; 429 ⇒ Backoff, zählt nicht als
Orderfehler.

## 6. Sonderfälle

- **Market Halt / Auktion verschoben:** Statusfeed meldet Halt ⇒ Intents zurückstellen
  (R-18), Neubewertung nach Resume; keine automatische Nachjagd.
- **Late Fills:** Fills nach Expiry werden akzeptiert und reconciled (nie ignoriert);
  Intent-Status `filled_late`, Folge-Entscheidungen rechnen mit Ist-Positionen.
- **Cancel/Replace:** nur vor 9:20 ET; danach ist die Auktions-Order unantastbar
  (Alpaca-Cut-off 9:28; eigener Puffer) — Replace = Cancel + neuer Intent (neue ID,
  Audit-Kette via `supersedes`).
- **Restart Recovery:** Beim Start liest die Engine `system_state`, offene Intents und
  Broker-Status (Orders/Positions/Activities), rekonstruiert die State Machine und
  geht erst nach erfolgreicher Konsistenzprüfung in den aktiven Modus
  ([[21_DISASTER_RECOVERY]] §4, Runbook RB-03).
- **Manuelle Eingriffe:** Operator kann Intents freigeben/stornieren und im
  Notfall manuell über das Alpaca-Dashboard handeln; manuelle Trades werden von der
  Reconciliation als `external_fill` erkannt und ins Ledger übernommen (nie verworfen).
