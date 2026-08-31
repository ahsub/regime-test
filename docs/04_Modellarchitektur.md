# 4. Modellarchitektur

## 1. VIX-Strategie (Markov-Switching)

```python
mod = sm.tsa.MarkovRegression(
    endog=returns,
    k_regimes=3,
    trend='c',
    switching_variance=True
)
