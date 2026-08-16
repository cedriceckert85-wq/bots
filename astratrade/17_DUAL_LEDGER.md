# 17 — Dual Ledger: Broker Ledger und Economic Ledger

Zurück: [[00_HOME]] · Verwandt: [[16_RECONCILIATION]], [[19_OBSERVABILITY]]

## 1. Warum zwei Ledger

Der **Broker Ledger** beantwortet: *Was ist auf dem Konto tatsächlich passiert?*
(Orders, Fills, Positionen, Cash, Gebühren — die beobachtbare Alpaca-Realität, Paper
oder Live). Der **Economic Ledger** beantwortet: *Wie gut ist die Strategie
wirtschaftlich?* (Total Returns inkl. Dividenden/Splits, Benchmark-Vergleich,
Soll-Performance des Modells, Kosten- und Verzerrungsaufriss). Ein einzelnes Ledger
kann beides nicht leisten: Paper-Konten simulieren keine Dividenden [AL-13], Broker-Cash
ignoriert Accruals, und die Modell-Soll-Sicht (fraktionale Idealgewichte, Fill zum
offiziellen Auktionspreis) existiert beim Broker gar nicht. Erst die Differenz beider
Ledger macht Ausführungsqualität und Paper-Verzerrungen messbar.

## 2. Sichten im Economic Ledger

1. **Actual-TR:** tatsächliche Positionen (aus Broker Ledger) + wirtschaftliche
   Ereignisse (Dividenden ab Ex-Date als Forderung, ab Pay-Date als Cash; Splits;
   Gebühren) ⇒ ökonomisch korrekte NAV-/Return-Reihe des realen Portfolios.
2. **Model-Ideal:** Soll-Portfolio (fraktionale target_weights, Fill = offizieller
   Auktionspreis, Kostenmodell) ⇒ theoretische Strategie-Performance.
3. **Benchmarks:** versionierte TR-Reihen je Track ([[04_STRATEGY_TRACK_A]] §6 usw.).

Differenzen = Implementation Shortfall, zerlegt in: Rundung (Whole Shares),
Auktions-Slippage, Auction-Misses, Timing (Fallback-Tage), Gebühren, Paper-Artefakte.

## 3. Kennzahlen und Berechnung

- **NAV:** Positionen × validierter Close (Zweitquellen-geprüft) + Cash + Accruals;
  Bewertungsquelle und -zeitpunkt im Ledger-Eintrag dokumentiert.
- **TWR:** täglich verkettete Returns, Cashflow-adjustiert (Modified Dietz intraday
  irrelevant, da Flows nur an Tagesgrenzen); **IRR** zusätzlich bei externen Ein-/
  Auszahlungen. P&L realisiert/unrealisiert getrennt, FIFO-Lots.
- Gebührenbehandlung: explizite Fees (SEC/TAF) als Kostenzeile; im Paper-Modus werden
  sie **synthetisch berechnet** und als `simulated_fee` gebucht, damit Paper-P&L nicht
  systematisch zu gut aussieht.

## 4. Schema (append-only)

```sql
CREATE TABLE ledger_entries (          -- ein Schema, zwei Ledger via ledger_type
  entry_id BIGSERIAL PRIMARY KEY,
  ledger_type TEXT NOT NULL,           -- 'broker' | 'economic'
  portfolio_id TEXT NOT NULL,
  entry_ts TIMESTAMPTZ NOT NULL,
  value_date DATE NOT NULL,
  entry_kind TEXT NOT NULL,            -- fill|fee|dividend_accrual|dividend_cash|split|
                                       -- valuation|transfer|simulated_fee|adjustment
  symbol TEXT, qty NUMERIC(18,6), price NUMERIC(18,6),
  amount NUMERIC(18,2) NOT NULL,       -- Cash-Wirkung (Dezimal, nie Float)
  currency TEXT NOT NULL DEFAULT 'USD',
  source_ref TEXT NOT NULL,            -- fill_id | activity_id | ca_id | valuation_run
  correction_of BIGINT,                -- Storno/Korrektur nur als Gegenbuchung
  metadata JSONB
);
CREATE UNIQUE INDEX ON ledger_entries (ledger_type, source_ref, entry_kind);
```

Korrekturen ausschließlich als Storno + Neubuchung (nie UPDATE) — GoBD-kompatible
Unveränderbarkeit ([[03_RESEARCH_FINDINGS]] §4).

## 5. Abgleich und Alarmgrenzen

| Vergleich | legitime Abweichung | Alarm |
|---|---|---|
| Broker-Cash vs Economic-Cash (ohne Accruals) | < 0,01 USD Rundung | ≥ 10 USD ⇒ Sev-1 (Handelstopp), sonst Sev-2 |
| Actual-TR vs Model-Ideal (täglich) | erklärter Shortfall (Zerlegung §2 vollständig) | unerklärter Rest > 5 bps/Tag ⇒ Sev-2 |
| Paper-NAV vs Economic-Actual | dokumentierte Paper-Artefakte (fehlende Dividenden etc.) | neue unerklärte Artefaktklasse ⇒ Review |

## 6. Paper-Trading-Verzerrungen (dokumentierte Liste, fortgeschrieben)

Initial bekannt aus der Recherche [AL-13]: unendliche NBBO-Liquidität, 10 % zufällige
Partials, keine Dividenden/Fees/Slippage-Simulation, OPG-Simulationsgüte unbekannt
(empirisch zu messen: Paper-OPG-Fillpreis vs offizieller Auktionspreis, Task in
Phase 5). Jede Verzerrung erhält einen Eintrag mit Messmethode und geschätztem Effekt;
der Paper-Gate-Report weist sie explizit aus, damit Paper-Ergebnisse nie unkorrigiert
als Live-Erwartung kommuniziert werden.
