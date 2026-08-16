# 25 — Team- und Skillmatrix

Zurück: [[00_HOME]]

Realität [AS-02]: eine Person (der Nutzer) + punktuelle externe Unterstützung. Die
Matrix zeigt, welche Rollen kombinierbar sind und wo externe/4-Augen-Pflicht gilt.

| Kompetenz | Kritikalität | kombinierbar mit | extern vergeben? | 4-Augen nötig bei |
|---|---|---|---|---|
| Quant Research | hoch | ML Engineering | teilweise (Review) | Gate-Entscheidungen, Lockbox-Öffnung |
| Python Engineering | hoch | alle Dev-Rollen | gut möglich | — |
| Data Engineering | hoch | Backend | gut möglich | Schema-Migrationen prod |
| Backend Engineering | mittel | Python/Data | gut möglich | Execution-Pfad-Änderungen |
| DevOps/SRE | mittel | Backend | gut möglich (Setup) | Prod-Deployments |
| Cloud/Infra | mittel | DevOps | gut möglich | — |
| Database Engineering | mittel | Data | punktuell | Restore-Prozeduren |
| ML Engineering | mittel | Quant | teilweise | Model-Approval |
| Financial Risk | hoch | Quant | Review empfohlen | Risk-Limit-Änderungen (Pflicht) |
| Market Microstructure | mittel | Quant | Literatur + Empirie | — |
| Security | hoch | DevOps | **Audit extern empfohlen** vor Live | Key-Prozesse, Break-Glass |
| Compliance/Recht/Steuern | hoch | — | **zwingend extern** (Anwalt/StB, BL-01..04) | jede Strukturänderung |
| QA/Test Automation | mittel | Python | teilweise | — |

**Wichtigste Eigenkompetenzen des Nutzers (Priorität):** 1. Python + Testdisziplin,
2. Validierungsmethodik (Leakage, DSR, Walk-Forward), 3. operative Disziplin
(Runbooks, Reconciliation ernst nehmen), 4. Risiko-Nüchternheit (Gates akzeptieren,
auch bei Negativergebnis). **Nicht ohne Spezialisten:** Aufsichts-/Steuerrecht,
externer Security-Review vor Live, unabhängiger Quant-Review der Gate-Reports
(bezahltes Peer-Review, ~2–3 PT — der wirksamste Schutz gegen Selbsttäuschung).

4-Augen-Ersatz im Ein-Personen-Betrieb: zeitversetztes Selbst-Review (Cooling-off
24 h zwischen Erstellung und Freigabe), Checklisten mit Pflicht-Artefakten,
technische Bestätigungscodes (Control Plane verlangt für Liquidation/Limit-Änderung
einen zweiten, zeitverzögert zugestellten Code).
