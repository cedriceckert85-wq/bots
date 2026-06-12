# Bot-Duo: SOLID + RISK â€” Status: â›” NICHT LIVE

Zwei neue Trade-Bots, designt von einem 14-Agenten-Fable-5-Schwarm auf Basis von vier
Deep Researches (Medien-Einfluss, Strategien, Bot-Architektur, Medien-Signale) inklusive
adversarialer PrÃ¼fung. VollstÃ¤ndige Designs: `SPEC_SOLID.md` und `SPEC_RISK.md`.

| | ðŸ¤ SOLID | ðŸ”¥ RISK |
|---|---|---|
| Mandat | Nur belegte Edges: Long-only-Momentum (12-1 + 52W-Hoch) + News-Drift-Satellit | Kontrolliert aggressiv: 4-Engine-Stack (Momentum-Leader, Volumen-Spike-Drift, TQQQ-Regime-Sleeve, Shorts deaktiviert) |
| Risiko/Trade | 1 % | 2 % (Caps: max 8 % Gesamt, Beta â‰¤ 1,3Ã—) |
| Alpaca-Paper | Konto Nr. 4 (verbunden) | Konto Nr. 5 (verbunden) |
| Benchmark | SPY (Pflicht) | SPY + SOLID |

## Bauphasen

**Phase 0 â€” GerÃ¼st (âœ… fertig):**
Specs, Repo, Quant-Datenpipeline (`scripts/quant_snapshot.py` + nÃ¤chtliche Action:
Momentum-Ranking, 52W-Hoch, SMA200/Regime-Zonen mit Hysterese, ATR, Volumen-Spikes,
VIX â€” die Entscheider rechnen NIE selbst), Journale, GUI, Alpaca-Konten verbunden,
Entscheider-Routinen angelegt (deaktiviert).

**Phase 1 â€” vor Aktivierung Pflicht (â¬œ offen, aus den Specs):**
1. `eval_v2.py`: share-basierte Equity-BuchfÃ¼hrung, Mark-to-Market, Band-/Roll-Exits,
   Split-Adjustierung (das einfache R-Eval-Skript der Flotte kann diese Specs NICHT abrechnen)
2. `risk-gate`-Workflow (SOLID R11) bzw. `risk-eval` (RISK): maschinelle Validierung jedes
   Journal-Eintrags + deterministische Zwangs-Exits â€” kein Prompt-Versprechen, sondern Code
3. Alpaca-Order-Anbindung (Bracket-Orders, Reconciliation, Kill-Switch)
4. EDGAR-Filing-Feed fÃ¼r den News-Drift-Satelliten (SOLID) bzw. FINRA-SI-Feed (RISK)
5. Grenzfall-Tests der Aktivierungs-Checklisten (Injection, Splits, Fail-Closed, Datenausfall)

**Aktivierung:** Nur per ausdrÃ¼cklichem Nutzer-Kommando, nach abgehakter Checkliste
(siehe jeweilige Spec, Abschnitt â€žAktivierungs-Checkliste").

## Architektur (Kurzfassung)

```
GitHub Action (nachts, volle Internet-Rechte)
  â””â”€ quant_snapshot.json  â†  einzige Wahrheitsquelle, vorgerechnet
        â†“ liest
Cloud-Entscheider (Sonnet, nur WebSearch â€” rechnet nie, darf nur streichen/vetoen)
  â””â”€ Journal-EintrÃ¤ge (Entry/Stop/Ziel, Pre-Registration-konform)
        â†“ validiert
risk-gate / risk-eval (Action, deterministisch â€” Phase 1)
        â†“ platziert/rechnet ab
Alpaca-Paper (echte Bracket-Orders) + Eval v2 (Yahoo-Abrechnung)
```

Teil der EPMT-Flotte: https://cedriceckert85-wq.github.io/review/vergleich.html
