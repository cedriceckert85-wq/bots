# 12 — Portfolio Construction und Begriffshierarchie

Zurück: [[00_HOME]] · Verwandt: [[13_RISK_ENGINE]], [[14_EXECUTION_ENGINE]], [[04_STRATEGY_TRACK_A]]

## 1. Verbindliche Begriffskette (nie synonym verwenden)

| Begriff | Definition | Produzent | Persistiert in |
|---|---|---|---|
| **Signal** | roher Modelloutput vor Kalibrierung (Score, Logit) | Modell | predictions.raw |
| **Forecast** | kalibrierte Schätzung (μ̂, P(y>0), σ̂) mit Horizont | Kalibrierungsschicht | predictions |
| **Confidence** | Unsicherheitsmaß des Forecasts (Intervall, Abstention-Flag) | Kalibrierungsschicht | predictions |
| **Target Exposure** | gewünschter Anteil Risiko-Asset je Track ∈ [0,1] | Portfolio Construction | target_portfolios |
| **Target Weight** | Zielgewicht je Symbol, Σ=1 inkl. BIL/Cash — **Source of Truth** | Portfolio Construction | target_portfolios |
| **Target Quantity** | ganzzahlige Stückzahl aus Weight × NAV / Preis (floor) | Order Intent Builder | order_intents |
| **Order Intent** | transaktionale Handelsabsicht nach Risk-Freigabe | Order Intent Management | order_intents |
| **Broker Order** | tatsächlich beim Broker platzierte Order | Execution/Broker Adapter | broker_orders |

Datenfluss ausschließlich in dieser Richtung; kein Modul darf eine Stufe überspringen
(architektonisch erzwungen: Execution akzeptiert nur `order_intents` mit
`approval_state=approved`, der Risk Service ist der einzige Schreiber dieses Feldes).

## 2. Von Forecast zu Target Weights (je Track, deterministisch)

1. **Mapping:** trackspezifische, monotone Funktion Forecast→Raw Exposure/Gewichte
   ([[04_STRATEGY_TRACK_A]] §5, [[05_STRATEGY_TRACK_B]] §2, [[06_STRATEGY_TRACK_C]] §2).
2. **Constraints (hart, konfiguriert in `config/portfolio_constraints/{track}.yaml`):**
   long-only (w ≥ 0), Σw = 1, Positionsobergrenzen, Assetklassen-Limits, keine
   Instrumente außerhalb des Track-Universums.
3. **Glättung + No-Trade-Band:** EWMA über Roh-Exposure, dann Bandvergleich mit
   aktuellem Ist-Gewicht (aus Broker Ledger, nicht aus letztem Soll!) — Band initial
   5 pp [ANNAHME, per Turnover-Kosten-Analyse zu kalibrieren].
4. **Abstention:** Forecast unter Confidence-Schwelle ⇒ Target = aktuelles Ist
   (kein Trade), Flag `abstained=true` im target_portfolio.
5. **Fallback-Kaskade (fail-safe, deterministisch):**
   - fehlender/verspäteter Forecast ⇒ Target = letztes gültiges Target (max. 3
     Handelstage), danach ⇒ Baseline-Regel des Tracks (z.B. B1-200d-Regel),
   - Baseline nicht berechenbar (Datenproblem) ⇒ Ziel = Ist einfrieren (Halt-Modus,
     kein automatischer Verkauf), Alert Sev-2.

## 3. Whole-Share-Umsetzung (Order Intent Builder)

```
für jedes Symbol s (außer BIL):
  target_qty[s] = floor(target_weight[s] * NAV_available / ref_price[s])
BIL erhält den Rest: target_qty[BIL] = floor(residual_cash / ref_price[BIL]) 
Settlement-Puffer: min_cash_buffer = max(0.5% NAV, erwartete Gebühren)  [ANNAHME]
ref_price = letzter validierter Close (t−1), Sanity-gecheckt (R-15)
delta_qty = target_qty − current_qty (aus reconciled Broker Ledger)
|delta_qty| * ref_price < min_trade_notional (100 USD [ANNAHME]) ⇒ kein Intent
Reihenfolge: SELL-Intents vor BUY-Intents (Cash-Freisetzung; beide in derselben
Opening Auction ⇒ Cash-Check rechnet mit erwarteten SELL-Erlösen × Sicherheitsfaktor 0,98)
```

Rundungs-/Granularitätsfehler (Soll-Gewicht vs erreichbares Whole-Share-Gewicht) wird
je Lauf als `rounding_tracking_error` im Economic Ledger ausgewiesen ([[17_DUAL_LEDGER]]).

## 4. Multi-Track-Betrieb

Phase 1: getrennte Portfolios (eigene Portfolio-IDs, eigene Paper-Konten), keine
Netting-Schicht. Ein späterer Kombinations-Layer (Track-Kapitalallokation, Order-Netting
über Tracks) ist als eigenes Modul vorgesehen, aber bewusst **nicht** im MVP
([[23_IMPLEMENTATION_ROADMAP]] §10) — er wäre eine Vermischung im Sinne der Phase-1-Regeln.

## 5. target_portfolios (Schema-Auszug, vollständig in [[15_ORDER_STATE_MACHINE]] §5)

`target_portfolios(target_portfolio_id PK deterministisch = uuid5(track, portfolio_id,
decision_date, config_version), track, portfolio_id, decision_ts, prediction_id FK,
weights JSONB, exposures JSONB, abstained BOOL, fallback_level INT, model_version FK,
config_version, created_at)` — unveränderlich; Korrekturen nur als neue Zeile mit
`supersedes`-Referenz.
