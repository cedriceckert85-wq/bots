# Bot-Duo: SOLID + RISK — Status: 🟢 LIVE (Stufe 1, Paper) seit 12.06.2026

Zwei Trade-Bots, designt von einem 14-Agenten-Fable-5-Schwarm auf Basis von vier
Deep Researches (Medien-Einfluss, Strategien, Bot-Architektur, Medien-Signale) inklusive
adversarialer Prüfung. Vollständige Designs: `SPEC_SOLID.md` und `SPEC_RISK.md`.
**Aktuell gilt die vereinfachte Stufe 1 — alle Regeln und Spec-Abweichungen: `STUFE1.md`.**

| | 🤍 SOLID | 🔥 RISK |
|---|---|---|
| Mandat | Nur belegte Edges: Long-only-Momentum (12-1 + 52W-Hoch) + News-Drift-Satellit | Kontrolliert aggressiv: Engines A Momentum-Leader, B Volumen-Spike, C TQQQ-Sleeve (D Shorts deaktiviert) |
| Risiko/Trade | 1 % (1.000 $) | 2 % (2.000 $), max 5 Positionen |
| Alpaca-Paper | Konto Nr. 4 (echte Bracket-Orders) | Konto Nr. 5 (echte Bracket-Orders) |
| Benchmark | SPY (Pflicht) | SPY + SOLID |

## Bauphasen

**Phase 0 — Gerüst (✅):** Specs, Quant-Datenpipeline, Journale, GUI, Alpaca-Konten, Routinen.

**Stufe 1 — LIVE seit 12.06.2026 (✅):** Diskrete Bracket-Trades nach `STUFE1.md`,
abgerechnet von der erprobten Flotten-Maschinerie (`scripts/alpaca_sync.py` echte Fills,
`scripts/trade_eval.py` Yahoo-Fallback). Statistik wird bei Umstieg auf Phase 2 zurückgesetzt.

**Phase 2 — volle Spec (⬜ offen):** `eval_v2.py` (share-basierte Equity-Buchführung,
Mark-to-Market, Band-/Roll-Exits, Splits), `risk-gate`/`risk-eval`-Workflows (maschinelle
Eintrags-Validierung + Zwangs-Exits), EDGAR-/FINRA-Feeds, Grenzfall-Tests der
Aktivierungs-Checklisten.

## Architektur

```
GitHub Action (23:37) — quant_snapshot.json: Momentum-Ranking, Regime-Zonen, ATR, Spikes
        v liest
Cloud-Entscheider (SOLID 02:53 / RISK 03:08 — rechnet nie selbst, nur streichen/vetoen)
        v schreibt Journal-Trades (Entry/Stop/Ziel)
GitHub Action (03:26) — Bracket-Orders in die Alpaca-Paper-Konten
GitHub Action (22:16) — Fills syncen + Yahoo-Abrechnung + Statistik
```

Teil der EPMT-Flotte: https://cedriceckert85-wq.github.io/review/vergleich.html
