# Pilot-Ergebnisse (Schritt 8)

- Fälle: **24**
- Accuracy: **0.958**
- Macro-F1: **0.961**

## Per Label

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| PASS | 1.000 | 0.889 | 0.941 | 9 |
| REVIEW | 0.889 | 1.000 | 0.941 | 8 |
| REJECT | 1.000 | 1.000 | 1.000 | 7 |

## Confusion Matrix (Truth x Pred)

| Truth \ Pred | PASS | REVIEW | REJECT |
|---|---:|---:|---:|
| PASS | 8 | 1 | 0 |
| REVIEW | 0 | 8 | 0 |
| REJECT | 0 | 0 | 7 |
