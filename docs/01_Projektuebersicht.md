# 1. Projektübersicht

## Zielsetzung

Entwicklung und Validierung einer **Market Regime-basierten Handelsstrategie** für den S&P 500.

## Methodik

### 1. VIX-basierte Regime-Erkennung
- Markov-Switching-Modell mit 3 Regimen
- Optimierte Parameter (BQ=0.50, S=0.60, BF=0.35, R=0.30, C=5)

### 2. Rolling Hidden Markov Model (HMM)
- Nach Pagliaro (2026)
- 3 Zustände: Bull, Sideways, Bear
- 6 Features: Rendite, Volatilität, VIX, VVIX, GEX, DIX

### 3. 3-Stufen-Ensemble
- Kombination beider Modelle
- 3 Positionsstufen: 0%, 50%, 100%
- Aggressive Optimierung für minimale Transaktionskosten

## Ergebnisse

| Kennzahl | Wert |
| :--- | :--- |
| **Sharpe Ratio** | 0.50 |
| **Gesamtrendite** | 163.18% |
| **Max. Drawdown** | -15.78% |
| **Anzahl Trades** | 163 |

## Wissenschaftliche Basis

- Pagliaro, A. (2026). "Regime-Aware LightGBM..." *Electronics*, 15(6), 1334.
- Hamilton, J.D. (1989). "A New Approach..." *Econometrica*, 57(2), 357-384.
