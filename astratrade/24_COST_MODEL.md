# 24 — Kostenmodell

Zurück: [[00_HOME]] · Preise Stand 2026-08-15, Quellen im [[29_SOURCE_LEDGER]];
Wechselkurs vereinfachend 1 USD ≈ 0,92 € [ANNAHME]. SaaS-Preise = mittleres
Änderungsrisiko, vor Vertragsabschluss verifizieren.

## 1. Laufende Kosten je Phase

| Posten | Phase 1–4 (Research) | Phase 5–6 (Paper/Shadow) | Phase 7+ (Live, Var. B) |
|---|---|---|---|
| Massive/Polygon Developer | 79 $/M | 79 $/M | 79 $/M |
| Alpaca Algo Trader Plus | 0 (Basic reicht) | 99 $/M | 99 $/M |
| Cloud-VM Execution (Hetzner) | 0 | 10–15 €/M | 10–15 €/M |
| Monitoring-VM / Dead-Man | 0–5 €/M | 5–10 €/M | 5–10 €/M |
| Backup-Storage (S3, ~200 GB) | 3–5 €/M | 5–8 €/M | 5–8 €/M |
| Strom lokal (Research-Läufe, ~300 W Spitzen) | 10–25 €/M | 10–25 €/M | 10–25 €/M |
| **Summe** | **≈ 90–110 €/M** | **≈ 200–250 €/M** | **≈ 200–260 €/M** |

Optional später: Databento Standard 199 $/M (Drittquelle), Norgate ~630 $/Jahr,
Twilio-Alarmierung ~5 €/M. Einmalig: USV ~150 €, 2-TB-SSD ~100 €, Anwalt/StB-
Erstberatung [ANNAHME: 1.500–4.000 € — einholen].

## 2. Kosten-Breakeven (Beispielrechnung, keine Performance-Prognose)

Bei 25.000 USD Live-Kapital kosten 250 €/M ≈ **13 % p.a. des Kapitals** — die
Fixkosten sind in der Startphase die größte „Underperformance-Quelle". Konsequenz
(ehrlich ausgewiesen): Controlled Live dient dem **Prozessnachweis**, nicht dem
Ertrag; wirtschaftlich sinnvoll wird das System erst ab ~150–250k USD Kapital
(Fixkostenquote < 2 %) oder mit reduziertem Datenstack. Diese Rechnung gehört in
jeden Gate-Report (Metrik `fixed_cost_drag_bps`).

## 3. Transaktionskosten

Alpaca: 0 Kommission (Retail-Aktien/ETF [FAKT, Kontotyp-abhängig zu verifizieren]);
regulatorische Gebühren (SEC-Fee, FINRA TAF) auf Verkäufe — im Backtest und Economic
Ledger modelliert ([[10_BACKTESTING]] §5); implizite Kosten (Spread/Slippage) je
Instrument parametrisiert und ab Phase 6 empirisch kalibriert.

## 4. Kostentransparenz-Regeln

Alle wiederkehrenden Kosten leben in `config/costs.yaml` (versioniert); der
Monats-Report des Economic Ledger weist Fixkosten, Transaktionskosten und
`fixed_cost_drag_bps` gegen NAV aus; jede neue Anbieter-Subscription braucht einen
Ledger-Eintrag + ADR-Notiz (Kosten sind Architekturentscheidungen).
