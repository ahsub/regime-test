# 5. Ergebnisse

## Zusammenfassung

| Kennzahl | Wert |
| :--- | :--- |
| **Sharpe Ratio** | 0.50 |
| **Out-of-Sample Sharpe** | 0.51 |
| **Gesamtrendite** | 163.18% |
| **Max. Drawdown** | -15.78% |
| **Anzahl Trades** | 163 |
| **Transaktionskosten** | 0.08% pro Trade |

## Vergleich der Modelle

| Modell | Sharpe Ratio | Drawdown | Trades | Eignung |
| :--- | :--- | :--- | :--- | :--- |
| **3-Stufen-Ensemble** | **0.50** | **-15.78%** | **163** | ✅ **Empfohlen** |
| VIX-Strategie | 0.74 | -30.30% | 329 | Rendite-orientiert |
| HMM-Strategie | 0.25 | -32.21% | 1018 | Vergleich |
| 2-Stufen-Ensemble | 0.20 | -16.59% | 135 | Zu passiv |
| S&P 500 Buy & Hold | ~0.40 | ~-50% | 0 | Referenz |

## Out-of-Sample-Test

| Zeitraum | Sharpe Ratio | Rendite | Drawdown | Trades |
| :--- | :--- | :--- | :--- | :--- |
| Training (2011–2019) | 0.41 | 53.58% | -12.22% | 916 |
| Test (2020–2026) | **0.51** | 63.51% | -15.54% | 118 |
| Voll (2011–2026) | 0.50 | 163.18% | -15.78% | 163 |

## Transaktionskosten-Test

| Kennzahl | Ohne Kosten | Mit Kosten (0.08%) |
| :--- | :--- | :--- |
| Sharpe Ratio | 0.50 | 0.50 |
| Gesamtrendite | 163.18% | 163.18% |
| Max. Drawdown | -15.78% | -15.78% |
| Anzahl Trades | 163 | 163 |
| Kosten absolut | - | 0.0787 |

## Korrelationsmatrix der Indikatoren

| | VIX | VIX3M | DIX | GEX |
| :--- | :--- | :--- | :--- | :--- |
| VIX | 1.00 | 0.53 | -0.01 | -0.21 |
| VIX3M | 0.53 | 1.00 | -0.33 | -0.35 |
| DIX | -0.01 | -0.33 | 1.00 | 0.27 |
| GEX | -0.21 | -0.35 | 0.27 | 1.00 |
