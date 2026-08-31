## 8. Hinweise zur statistischen Validität (DSR / Deflated Sharpe Ratio)

Die im Rahmen dieses Vergleichs berechnete **Deflated Sharpe Ratio (DSR)** folgt der Methodik von Bailey & López de Prado (2014) und dient der Korrektur für **Mehrfachtest-Überoptimierung** bei der Auswahl zwischen mehreren Modellvarianten.

### 8.1 Was die DSR hier abbildet

Die hier berechnete DSR bewertet **die Auswahl zwischen den 5 getesteten Modellfamilien**:

| Modellfamilie | Sharpe Ratio (roh) |
| :--- | :--- |
| classify_regime_v2() | 0.76 |
| 3-Stufen-Ensemble | 0.60 |
| VIX-Strategie (optimiert) | 0.74 |
| HMM-Strategie | 0.25 |
| 2-Stufen-Ensemble | 0.20 |

**n_trials = 5** wird als Anzahl der unabhängigen Modellvarianten angesetzt, die in dieser Auswahl gegeneinander antreten.

### 8.2 Was die DSR hier **nicht** abbildet

Eine vollständige Mehrfachtest-Korrektur müsste zusätzlich berücksichtigen, dass mehrere dieser Modellfamilien selbst das Ergebnis **interner Grid-Searches** sind:

| Modellfamilie | Interne Parameterkombinationen (geschätzt) |
| :--- | :--- |
| VIX-Strategie (optimiert) | ~2.500 |
| 3-Stufen-Ensemble | ~1.000 |
| HMM-Strategie | ~500 |
| 2-Stufen-Ensemble | ~500 |

Diese interne Optimierung ist **nicht** in der hier berechneten DSR enthalten. Die Ergebnisse sind daher als **Indikation für die relative Performance der 5 Modellfamilien** zu verstehen, nicht als definitive statistische Validierung gegenüber einer vollständigen Mehrfachtest-Korrektur.

### 8.3 Interpretation der DSR-Werte

Die im Skript `compare_approaches_final_v2.py` ausgegebenen DSR-Werte sind wie folgt zu interpretieren:

- **DSR ≥ 0.95**: Die Modellfamilie besteht die Mehrfachtest-Korrektur auf dem Niveau der **Auswahl zwischen 5 Modellfamilien**.
- **DSR < 0.95**: Die Modellfamilie übersteht diese Auswahlkorrektur nicht.

**Wichtig:** Diese Werte sind kein Ersatz für eine vollständige zweistufige Korrektur (interne Grid-Search + Modellauswahl). Sie bieten jedoch eine **methodisch transparente und reproduzierbare** Grundlage für den Vergleich der Modellfamilien auf Augenhöhe.

### 8.4 Quellen und Methodik

- Bailey, D.H. & López de Prado, M. (2014). "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality." *Journal of Portfolio Management*, 40(5), 94-107.
- Lo, A.W. (2002). "The Statistics of Sharpe Ratios." *Financial Analysts Journal*, 58(4), 36-52.

Die Implementierung im Skript `compare_approaches_final_v2.py` verwendet:
- Lo (2002) Standardfehler der Sharpe Ratio (mit Korrektur für Schiefe und Exzess-Kurtosis)
- Bailey & López de Prado (2014) asymptotische Näherung für die erwartete maximale Sharpe unter n_trials Versuchen
- Eine konservative Dokumentationslinie, die die Grenzen der Methode explizit ausweist
