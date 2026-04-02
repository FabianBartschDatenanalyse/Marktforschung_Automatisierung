# AI-Fragebogen-Checker (Produktdokumentation)

## Was ist dieses Produkt?

Der **AI-Fragebogen-Checker** ist ein einsatzbereites Prüf- und Freigabesystem für von KI erstellte Fragebögen.

Ziel: Du gibst einen erzeugten Fragebogen in den Prüfprozess, und das System liefert:

1. eine **Gate-Entscheidung** (`PASS`, `REVIEW`, `REJECT`),
2. bei Bedarf einen **kontrollierten Override** (nur für berechtigte Rollen),
3. einen **vollständigen Audit-Trail** für Governance und Nachvollziehbarkeit,
4. sowie ein **Kalibrierungs-Setup** (Pilot-Evaluation), um die Qualität des Systems mit Expert:innen-Urteilen zu messen und zu verbessern.

---

## Für wen ist das gedacht?

- Research Ops / Marktforschungsteams
- Projektleitungen mit Freigabeverantwortung
- QA-Verantwortliche, die AI-generierte Fragebögen sicher ins Feld bringen möchten

---

## Ergebnis für den Alltag

Wenn du heute einen AI-generierten Fragebogen prüfen willst, bekommst du mit diesem Produkt:

- einen standardisierten Entscheidungsprozess statt Bauchgefühl,
- dokumentierte Freigaben/Overrides mit Begründung,
- reproduzierbare Qualität über Projekte hinweg,
- eine Basis für kontinuierliche Verbesserung (Pilot + Tuning).

---

## Produktumfang (fertiger Betriebsablauf)

### 1) Gate-Entscheidung liegt vor

Das System arbeitet mit einer Gate-Datei (z. B. aus deinem QA-Layer), in der die Entscheidung und Qualitätsindikatoren stehen, z. B. `examples/gate_decision.json`.

### 2) Manuelle Freigabe nur kontrolliert

Falls nötig, kann ein manueller Override durchgeführt werden – **rollenbasiert**, **mit Pflichtbegründung**, **auditierbar**.

### 3) Audit-Log wird automatisch geschrieben

Jede manuelle Änderung wird als Event in einer JSONL-Datei dokumentiert (`before`/`after`, User, Rolle, Grund, Zeitstempel).

### 4) Qualitätskalibrierung über Pilot

Mit dem Pilot-Runner vergleichst du automatische Entscheidungen mit Expert:innen-Labels und misst Accuracy/F1/Confusion-Matrix.

---

## Projektstruktur

```text
.
├── governance/
│   ├── audit_log.py
│   ├── override.py
│   └── policy.yaml
├── evaluation/
│   ├── pilot_runner.py
│   ├── pilot_dataset.jsonl
│   ├── results.json
│   ├── results.md
│   └── v1.1_tuning_plan.md
├── examples/
│   ├── gate_decision.json
│   ├── overridden_gate.json
│   └── audit_log.jsonl
└── tests/
    ├── test_governance.py
    └── test_pilot_runner.py
```

---

## Quick Start (so nutzt du das Produkt sofort)

## Schritt A – AI-Fragebogen freigeben/prüfen

Du startest mit einer vorhandenen Gate-Entscheidung (z. B. aus deinem Prüf-Layer):

```bash
cat examples/gate_decision.json
```

Wenn `REVIEW` oder `REJECT` vorliegt und du fachlich begründet freigeben willst, nutze den kontrollierten Override:

```bash
python3 -m governance.override \
  examples/gate_decision.json \
  --user lead_anna \
  --role lead \
  --reason "Methodisch akzeptabel nach Teamreview und dokumentierter Abwägung." \
  --audit-log examples/audit_log.jsonl \
  --output examples/overridden_gate.json
```

Danach:

- finale Entscheidung: `examples/overridden_gate.json`
- Audit-Nachweis: `examples/audit_log.jsonl`

---

## Schritt B – Qualität des Checkers kalibrieren (Pilot)

```bash
python3 evaluation/pilot_runner.py \
  evaluation/pilot_dataset.jsonl \
  --json-output evaluation/results.json \
  --md-output evaluation/results.md
```

Danach findest du:

- `evaluation/results.json` (maschinenlesbar)
- `evaluation/results.md` (management-/teamlesbar)

---

## Governance-Regeln (Produktivbetrieb)

In `governance/policy.yaml` wird zentral gesteuert:

- welche Rollen overriden dürfen,
- wie lang eine Begründung mindestens sein muss,
- aus welchen Entscheidungen ein Override erlaubt ist.

Aktueller Produktstandard:

- `editor`: kein Override
- `lead`: Override erlaubt
- Mindestbegründung: 12 Zeichen
- erlaubte Ausgangsentscheidungen: `REVIEW`, `REJECT`

---

## Datenformate

## Gate-Datei (Input für Governance)

Beispiel:

```json
{
  "decision": "REVIEW",
  "reason": "1 WARNING über Schwellwert 0",
  "counts": {
    "blockers": 0,
    "warnings": 1,
    "hints": 1
  },
  "score": 87
}
```

## Audit-Event (JSONL)

Pro Zeile ein Event mit:

- `event_type`, `timestamp`, `user`, `role`, `reason`
- `before` (vor Override)
- `after` (nach Override)

## Pilot-Datensatz (JSONL)

Pro Fall:

```json
{"questionnaire_id":"QNR-001","blockers":1,"warnings":0,"expert_decision":"REJECT"}
```

---

## KPI-Interpretation (Pilot)

- **Accuracy**: Wie oft das System insgesamt richtig liegt.
- **Macro-F1**: Balance über alle Klassen (`PASS`, `REVIEW`, `REJECT`).
- **Recall(REJECT)**: Kritisch, damit riskante Fragebögen nicht durchrutschen.
- **Precision(REVIEW)**: Wichtig zur Reduktion unnötiger manueller Nacharbeit.

---

## Betriebsempfehlung

1. AI-Fragebogen erzeugen lassen.
2. QA-Layer erzeugt Gate-Entscheidung.
3. Bei `PASS`: direkt freigeben.
4. Bei `REVIEW`/`REJECT`: fachliche Prüfung + ggf. Override durch `lead`.
5. Audit-Log revisionssicher speichern.
6. Monatlich Pilot-/Kalibrierungskennzahlen aktualisieren.

---

## Tests

```bash
python3 -m unittest -v tests/test_governance.py tests/test_pilot_runner.py
```

---

## Fehlerbehebung

### Rolle darf nicht overriden

- Prüfe `--role` und `governance/policy.yaml`.

### Override wird wegen Begründung abgelehnt

- Begründung verlängern (Policy `reason_min_chars`).

### Keine Audit-Einträge sichtbar

- `--audit-log` Pfad prüfen.
- Dateirechte/Zielordner prüfen.

### Pilot-Ergebnisse wirken unplausibel

- Datensatz auf korrekte Labels (`PASS|REVIEW|REJECT`) prüfen.
- Sicherstellen, dass `blockers`/`warnings` numerisch sind.

---

## Release-Status

✅ Dieses Repository beschreibt und implementiert den **produktiven Betriebsablauf für Governance + Pilot-Kalibrierung** zur Überprüfung AI-generierter Fragebögen.
