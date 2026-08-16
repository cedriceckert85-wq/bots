# 28 — Runbooks

Zurück: [[00_HOME]] · Jeder kritische Alert ([[19_OBSERVABILITY]] §5) referenziert
genau ein Runbook. Format: Zweck, Auslöser, Schritte, Verifikation, Eskalation.
Runbooks werden im Drill-Kalender geübt ([[22_TEST_STRATEGY]] §1).

## RB-01 — Täglicher Betriebs-Check (5 min, Handelstage)
1. Control Plane: Systemzustand NORMAL? Letzte Reconciliation grün? 2. Grafana-Board
„Daily": Pipeline-SLOs, offene Intents, NAV/DD. 3. Operator-Heartbeat bestätigen
(tote-Mann-Reset). Verifikation: Audit-Event `daily_check`. Eskalation: jeder rote
Punkt ⇒ zugehöriges Runbook.

## RB-02 — VM-/Systemwiederherstellung
Auslöser: Dead-Man-Alarm, VM tot. 1. Provider-Status prüfen. 2. `infra/` IaC:
Neu-Provisionierung. 3. pgBackRest-Restore (letztes WAL). 4. **RB-03 vollständig
durchlaufen.** Verifikation: RTO ≤ 4 h, Recon grün. Eskalation: Restore scheitert ⇒
Zweitregion-Backup; Handel bleibt im Halt.

## RB-03 — Wiederanlauf nach Neustart/Restore (Pflichtreihenfolge)
Siehe [[21_DISASTER_RECOVERY]] §4: Zeit-Sync → Restore-Validierung → Broker-Recon →
Config-Validierung → Lease → Backfill → Supervised-Modus (erste Entscheidung manuell
bestätigen). Kein Schritt überspringbar; Checkliste im Control Plane mit Pflicht-Häkchen.

## RB-04 — Dead-Letter-Intent
Auslöser: `dead_letter_total` > 0. 1. Intent + Broker-Status lesen (Lookup-Historie).
2. Entscheiden: verwerfen (Begründung) / manuell ausführen (Halt-Modus, dokumentiert)
/ neu einplanen (neuer Intent). 3. Ursachenanalyse (Netz? Reject-Grund?).
Verifikation: kein Intent > 24 h im Dead-Letter.

## RB-05 — Reconciliation-Break
Auslöser: Sev-1/Sev-2-Break. 1. Betroffenes Portfolio ist bereits pausiert/gehaltet —
bestätigen. 2. Break-Detail (`reconciliations.breaks`): Klasse bestimmen. 3. Quellen
vergleichen: activities vs fills vs ledger. 4. Ursache dokumentieren, Korrektur nur
als Gegenbuchung. 5. Wiederaufnahme nur bei erklärtem Break + grünem Re-Run.
Eskalation: unerklärbar > 24 h ⇒ Handel bleibt aus, externer Review.

## RB-06 — Monatlicher Restore-Test (automatisiert, Ergebnis prüfen)
1. CI-Job restauriert letztes Backup in Wegwerf-Container. 2. Checksummen-/Zeilen-
Vergleich + Audit-Hash-Kette. 3. Ergebnis im Audit-Log; Fehlschlag ⇒ BackupStale-Alarm
+ Scale-up-Sperre bis behoben.

## RB-07 — Key-Kompromittierung / Rotation
Auslöser: Verdacht, Anomalie, Plan-Rotation. 1. Bei Verdacht: **globaler Kill Switch**.
2. Alpaca-Dashboard (MFA): alten Key revoken, neuen erzeugen. 3. Secret-Store
aktualisieren, Services neu starten. 4. Vollständige Order-/Positions-Recon auf
unautorisierte Aktivität. 5. Audit-Event + ggf. Incident-Report. Verifikation:
alter Key liefert 401; Recon grün.

## RB-08 — Clock-Drift
Auslöser: `clock_drift_ms` > 500. 1. Submission ist bereits geblockt (R-23). 2. chrony
Quellen prüfen (`chronyc sources`), NTP-Erreichbarkeit (Egress-Allowlist!). 3. Nach
Sync < 100 ms: PIT-Kritikalität prüfen (liefen Jobs mit falscher Zeit? Manifeste
vergleichen). Verifikation: Drift-Metrik normal, betroffene Läufe validiert.

## RB-09 — Kill-Switch-Aktivierung und -Rücknahme
Aktivierung: Control Plane, Scope wählen, Grund Pflichtfeld; offene Orders werden
gecancelt; Zustand persistent. Rücknahme: Ursache dokumentiert + Recon grün +
Cooling-off 1 h + Bestätigungscode. Monatlicher Drill: Aktivierung+Rücknahme in
Paper messen (SLO: Wirkung < 60 s).

## RB-10 — Feed-Widerspruch (CrossSourceDiff)
1. Handel ist geblockt (R-05). 2. Drittquelle konsultieren (Tiingo-EOD / Broker-Quote).
3. Fehlerquelle identifizieren ⇒ Korrektur-Manifest für falsche Quelle; Anbieter-Ticket.
4. Freigabe erst nach Zwei-Quellen-Konsens. Verifikation: Diff < 10 bps am Folgetag.

## RB-11 — Auction Miss
1. Alert prüfen: Ursache (Submission spät? Reject? Halt?). 2. Auction-Miss-Prozedur-
Ergebnis kontrollieren (Folge-Intent oder Verschiebung). 3. `missed_auction_cost` im
Economic Ledger verifizieren. 4. Bei wiederholtem Miss (≥ 2 in 5 Tagen): Ursachen-
analyse als Incident.

## RB-12 — Notfallmappe Operator-Ausfall (offline, versiegelt)
Inhalt: Kontenliste, Break-Glass-Zugang ([[18_SECURITY]] §2), Anweisung „System in
Halt versetzen bzw. Konto über Broker-Support liquidieren", Kontakte (Broker-Support,
Anwalt, StB). Prüfung: jährlich aktualisieren.
