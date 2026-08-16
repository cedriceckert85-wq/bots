# 13 — Risk Engine: Pre-Trade-, In-Trade- und Post-Trade-Risikomatrix

Zurück: [[00_HOME]] · Verwandt: [[12_PORTFOLIO_CONSTRUCTION]], [[14_EXECUTION_ENGINE]], [[19_OBSERVABILITY]]

Der Risk Service ist der **einzige** Weg von `target_portfolios` zu freigegebenen
`order_intents`. Jeder Check schreibt ein `risk_decisions`-Audit-Event (Check-ID,
Formelversion, Inputwerte, Ergebnis, Grenzwert, Aktion). Grenzwerte leben in
`config/risk_limits/{track}.yaml` (versioniert, [[20_INFRASTRUCTURE]] §7); Werte unten
sind **initiale Defaults [ANNAHME]**, Kalibrierung in Phase 5.

## 1. Pre-Trade-Checks (blockierend, Reihenfolge fest)

| ID | Check | Formel/Regel | Datenquelle | Verstoß ⇒ |
|---|---|---|---|---|
| R-01 | Config gültig | Schema-Validierung + Vollständigkeit der Live-Config | config service | BLOCK (Handelsstart verhindert) |
| R-02 | Market Session | Zieltag ist Handelstag, keine Halbtags-Sonderregel verletzt | exchange_calendars (versioniert) | BLOCK |
| R-03 | Data Feed Health | letzte validierte Bars vollständig; Cross-Source-Diff ok | Validation-Metriken | BLOCK |
| R-04 | Stale Data | Alter der Entscheidungsdaten ≤ 24 h (Daily-Pfad) | Manifeste | BLOCK |
| R-05 | Price Sanity | ref_price in [0,5×, 2×] des 20d-Median; Diff zu Zweitquelle < 25 bps | bars beider Quellen | BLOCK |
| R-06 | Model Health | Champion nicht `Degraded`/`Retired`; Prediction vorhanden und frisch | Model Registry, [[11_ML_ARCHITECTURE]] §5 | Fallback-Kaskade ([[12_PORTFOLIO_CONSTRUCTION]] §2.5) |
| R-07 | Long-only / Universum | w ≥ 0; Symbole ∈ Track-Universum; keine Leverage-/Inverse-ETFs | target_portfolio | BLOCK |
| R-08 | Gross/Net Exposure | Gross = Net = Σw_risk ≤ 100 % NAV | target_portfolio | BLOCK |
| R-09 | Max Einzelposition | Track A: SPY ≤ 100 %; B: ≤ 30 %/Sektor; C: ≤ 40 %/Asset, Aktien ≤ 70 % | target_portfolio | BLOCK |
| R-10 | Turnover-Limit | Tages-Turnover ≤ 50 % NAV; rollierend 30d ≤ 200 % [ANNAHME] | intents vs Ledger | BLOCK + Review |
| R-11 | Order-Notional | je Intent ≤ 25 % NAV und ≤ 0,5 % des 20d-Ø-Auktionsvolumens des Symbols | intents + Volumendaten | BLOCK |
| R-12 | Cash Check | BUY-Summe ≤ verfügbares Cash + 0,98×SELL-Erlöse − Puffer | Broker Ledger (reconciled) | BLOCK |
| R-13 | Position Check | SELL-Menge ≤ reconciled Ist-Position (kein Short möglich) | Broker Ledger | BLOCK |
| R-14 | Duplicate Order | kein offener Intent/Order für (portfolio, symbol, decision_date) | order_intents/broker_orders | BLOCK |
| R-15 | Broker Health | Account-Status ok, API erreichbar, keine Restriktionen | Broker Adapter | HOLD (Retry-Fenster bis 9:20 ET), dann Auction-Miss-Prozedur |
| R-16 | Daily-Loss-Limit | Tages-P&L ≤ −2 % NAV ⇒ keine Exposure-**Erhöhung** heute | Economic Ledger | Teil-BLOCK (nur Buys) |
| R-17 | Drawdown-Limit | DD vom Peak > 15 % (Track A) ⇒ Deleveraging-Modus (Cap 50 %); > 20 % ⇒ Halt + manueller Review | Economic Ledger | Modus-Wechsel |
| R-18 | Halt/LULD | Symbol gehaltet/im LULD-Zustand zum Submissionszeitpunkt | Statusfeed | Intent zurückstellen |
| R-19 | Volatilitätsziel | prognostizierte Portfolio-Vol ≤ 1,25 × Track-Vol-Target | Kovarianz aus bars | WARN, bei 1,5× BLOCK der Erhöhung |
| R-20 | Konzentration/Korrelation | Track B/C: max. Beitrag eines Assets zur Portfolio-Varianz ≤ 60 % | Kovarianz | WARN/BLOCK analog |
| R-21 | Spread-Limit | letzter bekannter Spread ≤ 25 bps (ETF-Sanity) | quotes | WARN; BLOCK bei > 50 bps |
| R-22 | Kill-Switch-Status | globaler/Track-/Symbol-Kill-Switch inaktiv | emergency controls | BLOCK |
| R-23 | Clock Sanity | NTP-Offset < 500 ms; Entscheidungs- vor Submissionszeit | chrony-Metrik | BLOCK |
| R-24 | Leader/Fencing | dieser Prozess hält gültige Lease + Fencing Token | lease table | BLOCK ([[14_EXECUTION_ENGINE]] §4) |

## 2. In-Trade-Checks (zwischen Submission und Fill)

- Auction-Miss: OPG-Order nach Open unfilled/canceled ⇒ **kein Blind-Retry**; Prozedur:
  Neubewertung des Intents (Preisabweichung vom erwarteten Open < max_slippage?) ⇒
  entweder Limit-DAY-Nachorder (limit = erwarteter Preis + Slippage-Budget) oder
  Verschieben auf nächsten Tag; Entscheidung deterministisch per `execution_policy`.
- Slippage-Guard: Fill-Preis vs offizieller Auktionspreis > 20 bps ⇒ Incident (Sev-3),
  > 50 bps ⇒ Trading-Pause des Symbols + Review.
- Partial-Fill-Handling: [[15_ORDER_STATE_MACHINE]] §3.
- Unbekannter Orderstatus (Timeout): Order gilt als **potenziell platziert**; keine
  neue Order für denselben Intent bis Status per `client_order_id`-Lookup geklärt
  (Reconciliation-Loop, [[16_RECONCILIATION]] §4). Safe State = nicht handeln.

## 3. Post-Trade-Checks (täglich, nach Reconciliation)

- Fill-, Position-, Cash-, Corporate-Action-Reconciliation grün ([[16_RECONCILIATION]]).
- Realisierte Slippage-Verteilung vs Modellannahme (Drift ⇒ Kostenmodell-Update).
- Limit-Auslastungen (Turnover, Exposure) Reporting; 80 %-Auslastung ⇒ WARN.
- Tote-Mann-Schalter: bleibt der tägliche Operator-Heartbeat (Bestätigung im Control
  Plane) > 5 Handelstage aus, wechselt das System in Halt-Modus (keine neuen Orders,
  keine automatische Liquidation) [AS-02].

## 4. Kill-Switch-Hierarchie und Modi

| Ebene | Wirkung | Auslöser |
|---|---|---|
| Global Kill | keine neuen Orders, offene Orders canceln, Halt-Modus | Operator; automatisch bei Reconciliation-Break Sev-1, Split-Brain-Verdacht, Feed-Widerspruch |
| Track Kill | wie oben, nur für einen Track | Operator; Modell-Degraded-Eskalation |
| Symbol Kill | Symbol wird eingefroren (keine Intents) | Operator; Halt/Datenanomalie |
| Deleveraging-Modus | Exposure-Cap 50 %, nur Reduktionen erlaubt | R-17, Modell-Degraded |
| Halt-Modus | Positionen einfrieren, **keine automatische Liquidation** | diverse; Default-Fehlerzustand |
| Kontrollierte Liquidation | geordneter Abbau über OPG/Limit über N Tage | **nur manuell**, 4-Augen (Operator + Bestätigungscode) |

Alle Modi sind persistente Systemzustände (`system_state`-Tabelle) und überleben
Neustarts; jede Änderung ist ein Audit Event + Alert.

## 5. Rollback-Trigger (automatisch)

- Champion-Rollback: 2× CUSUM-Bruch in 20 Tagen oder Kalibrierungsverfall ⇒
  Vorgänger-Champion reaktivieren (falls valide) sonst Baseline-Regel; Alert Sev-2.
- Config-Rollback: fehlgeschlagene Config-Validierung beim Start ⇒ letzte gültige
  Version laden, WARN; ist auch diese ungültig ⇒ kein Handelsstart (R-01).
