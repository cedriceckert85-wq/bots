# 16 — Reconciliation

Zurück: [[00_HOME]] · Verwandt: [[15_ORDER_STATE_MACHINE]], [[17_DUAL_LEDGER]]

Reconciliation ist die tägliche Beweisführung, dass interne Sicht und Broker-Realität
übereinstimmen. **Ohne grüne Reconciliation des Vortags startet kein neuer Handelstag**
(Risk-Check R-03/R-12/R-13 konsumieren nur reconciled Werte).

## 1. Abgleichstypen und Quellen

| Typ | Interne Quelle | Broker-Quelle (Alpaca) | Frequenz |
|---|---|---|---|
| Order-Recon | order_intents/broker_orders | `GET /v2/orders` (status=all, nested) + `orders:by_client_order_id` | nach jeder Auktion + 16:30 ET |
| Fill-Recon | fills | trade_updates-Stream, Backfill via `account/activities?activity_type=FILL` | Stream sofort, Batch 16:30 |
| Position-Recon | positions (berechnet aus fills) | `GET /v2/positions` | 16:30 + vor jedem Handelstag 08:30 |
| Cash-Recon | cash_balances (berechnet) | `GET /v2/account` + activities (Fees, Transfers) | dito |
| Corporate-Action-Recon | corporate_actions (2 Datenquellen) | activities (DIV, Splits) | täglich + am Ex-/Pay-Date |

## 2. Break-Klassifikation

| Klasse | Beispiel | Reaktion |
|---|---|---|
| legitim/erwartet | Rundungsdifferenz Cash < 0,01 USD; zeitlicher Versatz Stream vs REST < 5 min | auto-akzeptiert, geloggt |
| erklärbar | manueller Trade des Operators (external_fill); verspäteter Fill | automatisch zugeordnet, Audit-Vermerk |
| **Break Sev-2** | Positionsdifferenz ≤ 1 Whole Share; Cash-Diff < 10 USD ungeklärt | Trading des Portfolios pausiert bis Klärung am selben Tag (Runbook RB-05) |
| **Break Sev-1** | unbekannte Order beim Broker; Positionsdifferenz > 1 Share; Cash-Diff ≥ 10 USD; fehlende Corporate Action am Ex-Tag | **globaler Halt-Modus**, Kill offener Orders, manuelle Untersuchung, kein Neustart ohne dokumentierte Ursache |

## 3. Corporate-Action-Recon im Detail

Vor jedem Ex-Date (aus beiden CA-Quellen bekannt): erwartete Preis-/Stück-Wirkung
berechnen; am Ex-Tag: Positions-/Preisprüfung gegen Erwartung; am Pay-Date:
Dividenden-Cash in activities gegen Economic-Ledger-Accrual. Split ohne erwartete
Anpassung oder Dividende ohne Accrual ⇒ Sev-1 (ein nicht verarbeiteter Split
verfälscht jede Folgeentscheidung).

## 4. Unknown-Order-Auflösung (Timeout-Pfad)

1. Timeout nach Submission ⇒ Intent-State `Unknown`.
2. Poll `orders:by_client_order_id` (Backoff 2/4/8/16 s, dann 60-s-Loop bis Auktion).
3. Gefunden ⇒ Zustand adoptieren; nicht gefunden nach Budget UND vor 9:20 ET ⇒
   ein (1) erneuter Submissionsversuch; sonst DeadLetter + Auction-Miss-Prozedur.
4. Während `Unknown` gilt Cash/Position des Symbols als gesperrt (pessimistisch).

## 5. Restart-/Recovery-Reconciliation

Nach jedem Prozessstart, vor Aktivwerden: vollständige Order-/Position-/Cash-Recon
gegen Broker; erst `status=green` schaltet die Outbox-Verarbeitung frei
([[21_DISASTER_RECOVERY]] §4). Damit ist „System startet doppelt" + „Orderstatus
unbekannt" kombiniert abgedeckt (Lease verhindert Parallelbetrieb, Recon verhindert
blindes Weiterhandeln).
