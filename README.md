# Marktforschung_Automatisierung – Governance & Pilot Evaluation (Schritt 7 + 8)

Dieses Repository enthält zwei zentrale Bausteine für den QA-/Freigabeprozess von Fragebögen:

1. **Governance-Layer (Schritt 7)**
   - Rollenbasierte Overrides (`editor` / `lead`)
   - Pflichtbegründung für Overrides
   - Revisionssicheres Audit-Logging
2. **Pilot-Evaluation (Schritt 8)**
   - Vergleich von automatischen Gate-Entscheidungen gegen Expert:innen-Labels
   - Kennzahlen (Accuracy, Macro-F1, Precision/Recall/F1)
   - Reports als JSON + Markdown

---

## Inhaltsverzeichnis

- [Projektstruktur](#projektstruktur)
- [Voraussetzungen](#voraussetzungen)
- [Schnellstart](#schnellstart)
- [Governance (Schritt 7)](#governance-schritt-7)
  - [Policy](#policy)
  - [Override CLI – genaue Bedienung](#override-cli--genaue-bedienung)
  - [Audit-Log](#audit-log)
- [Pilot Evaluation (Schritt 8)](#pilot-evaluation-schritt-8)
  - [Datensatzformat](#datensatzformat)
  - [Pilot Runner – genaue Bedienung](#pilot-runner--genaue-bedienung)
  - [Interpretation der Ergebnisse](#interpretation-der-ergebnisse)
- [Tests](#tests)
- [Fehlerbehebung](#fehlerbehebung)

---

## Projektstruktur

```text
.
├── governance/
│   ├── __init__.py
│   ├── audit_log.py
│   ├── override.py
│   └── policy.yaml
├── evaluation/
│   ├── __init__.py
│   ├── pilot_dataset.jsonl
│   ├── pilot_runner.py
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

## Voraussetzungen

- Python **3.10+**
- Keine externen Python-Abhängigkeiten notwendig (nur Standardbibliothek)

Empfohlen:

```bash
python3 --version
```

---

## Schnellstart

### 1) Tests ausführen

```bash
python3 -m unittest discover -v
```

### 2) Pilot-Evaluation neu berechnen

```bash
python3 evaluation/pilot_runner.py \
  evaluation/pilot_dataset.jsonl \
  --json-output evaluation/results.json \
  --md-output evaluation/results.md
```

### 3) Override-Durchlauf ausführen

```bash
python3 -m governance.override \
  examples/gate_decision.json \
  --user lead_anna \
  --role lead \
  --reason "Methodisch akzeptabel nach Teamreview und dokumentierter Abwägung." \
  --audit-log examples/audit_log.jsonl \
  --output examples/overridden_gate.json
```

---

## Governance (Schritt 7)

Der Governance-Layer stellt sicher, dass manuelle Freigaben nachvollziehbar und regelkonform passieren.

### Policy

Die Datei `governance/policy.yaml` steuert:

- welche Rollen overriden dürfen,
- minimale Länge der Begründung,
- aus welchen Entscheidungen ein Override erlaubt ist.

Aktuell:

- `editor`: darf **nicht** overriden
- `lead`: darf overriden
- Mindestlänge Grund: `12` Zeichen
- erlaubte Ausgangsentscheidungen: `REVIEW`, `REJECT`

### Override CLI – genaue Bedienung

**Befehl:**

```bash
python3 -m governance.override <gate_report.json> \
  --user <user_id> \
  --role <editor|lead> \
  --reason "<begründung>" \
  --policy governance/policy.yaml \
  --audit-log <audit_log_path.jsonl> \
  --output <overridden_gate.json>
```

#### Parameter im Detail

- `gate_report` (Pflicht): Eingangsentscheidung (JSON), z. B. `REVIEW`.
- `--user` (Pflicht): technische oder fachliche Kennung der Person.
- `--role` (Pflicht): Rolle gegen Policy geprüft.
- `--reason` (Pflicht): Begründungstext, muss Mindestlänge erfüllen.
- `--policy` (optional): Pfad zur Policy (Default: `governance/policy.yaml`).
- `--audit-log` (optional): Pfad zur JSONL-Audit-Datei (Default: `examples/audit_log.jsonl`).
- `--output` (Pflicht): Zielpfad für überschriebenes Gate-JSON.

#### Was passiert bei Erfolg?

1. Rolle wird geprüft.
2. Ausgangsentscheidung wird gegen Policy geprüft.
3. Begründung wird geprüft.
4. Entscheidung wird auf `PASS` gesetzt.
5. `override`-Metadaten werden angehängt.
6. Audit-Eintrag wird in JSONL gespeichert.

#### Typische Fehlerfälle

- `PermissionError`: Rolle darf kein Override.
- `ValueError`: Entscheidung laut Policy nicht überschreibbar.
- `ValueError`: Begründung zu kurz.

### Audit-Log

Das Audit-Log ist eine JSONL-Datei (eine JSON-Zeile pro Event).

Beispielinhalt (`examples/audit_log.jsonl`):

- `event_type`, `timestamp`, `user`, `role`, `reason`
- `before`: Zustand vor Override
- `after`: Zustand nach Override

Damit ist nachvollziehbar: **wer wann warum was geändert hat**.

---

## Pilot Evaluation (Schritt 8)

Die Pilot-Evaluation vergleicht automatische Entscheidungen mit Expert:innen-Labels.

### Datensatzformat

`evaluation/pilot_dataset.jsonl` ist JSONL mit einem Fall pro Zeile:

```json
{"questionnaire_id":"QNR-001","blockers":1,"warnings":0,"expert_decision":"REJECT"}
```

Pflichtfelder:

- `questionnaire_id` (string)
- `blockers` (int)
- `warnings` (int)
- `expert_decision` (`PASS|REVIEW|REJECT`)

### Pilot Runner – genaue Bedienung

**Befehl:**

```bash
python3 evaluation/pilot_runner.py <dataset.jsonl> \
  --json-output <results.json> \
  --md-output <results.md>
```

#### Entscheidungslogik (Baseline)

- `blockers > 0` ⇒ `REJECT`
- sonst `warnings > 0` ⇒ `REVIEW`
- sonst ⇒ `PASS`

#### Output-Dateien

1. `results.json`
   - `num_cases`, `accuracy`, `macro_f1`
   - `confusion_matrix`
   - `per_label` (Precision/Recall/F1/Support)
2. `results.md`
   - gleiche Kennzahlen in lesbarer Tabellenform

### Interpretation der Ergebnisse

- **Accuracy**: Gesamtanteil korrekter Entscheidungen.
- **Macro-F1**: mittlere F1 über alle Klassen (gleiches Gewicht pro Klasse).
- **Per-Label Recall**: wichtig für `REJECT` (kritische Fälle nicht verpassen).
- **Per-Label Precision**: wichtig für `REVIEW` (False Positives reduzieren).

Empfohlene Folgearbeit ist in `evaluation/v1.1_tuning_plan.md` dokumentiert.

---

## Tests

### Alle Tests

```bash
python3 -m unittest discover -v
```

### Nur Governance

```bash
python3 -m unittest -v tests/test_governance.py
```

### Nur Pilot Runner

```bash
python3 -m unittest -v tests/test_pilot_runner.py
```

---

## Fehlerbehebung

### `ModuleNotFoundError` bei CLI-Aufruf

- Stelle sicher, dass der Aufruf im Repo-Root erfolgt.
- Alternativ Modul-Aufruf nutzen (`python3 -m governance.override ...`).

### Keine Einträge im Audit-Log

- Prüfe den `--audit-log` Pfad.
- Prüfe Schreibrechte auf Zielordner.

### Unerwartete Metriken

- Prüfe `expert_decision` Schreibweise (`PASS|REVIEW|REJECT`).
- Prüfe, ob `blockers`/`warnings` numerisch sind.

---

## Hinweise

- `evaluation/results.json` und `evaluation/results.md` sind reproduzierbare Ergebnisartefakte.
- Für produktiven Einsatz sollten Datensätze aus echten Historienfällen gepflegt und versioniert werden.
