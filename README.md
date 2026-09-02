# Market Regime Analysis Tool

**Status:** ✅ Validierte, praxistaugliche Strategie  
**Sharpe Ratio:** 0.75 (klassifiziert) | **Drawdown:** -20.29%  
**Letzte Aktualisierung:** 2026-09-02

---

## 📊 Kern-Ergebnisse (Stand 2026-09-02)

| Kennzahl | Wert |
| :--- | :--- |
| **Sharpe Ratio** | **0.75** (klassifiziert) / 0.60 (Ensemble) |
| **Gesamtrendite** | **403.18%** (2011–2026) |
| **Max. Drawdown** | -20.29% (klassifiziert) / -16.32% (Ensemble) |
| **Anzahl Trades** | 261 (klassifiziert) / 163 (Ensemble) |
| **Modell-AIC (2011–2026)** | **-9.936,59** (Original) |
| **DSR (n_trials=5)** | **1.00** (statistisch signifikant) |

---

## 🏆 Strategie-Vergleich

| Strategie | Sharpe | Rendite | Drawdown | Trades | Sieger |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **classify_regime_v2()** | **0.75** | **403.18%** | -20.29% | 261 | 🏆 **Rendite** |
| 3-Stufen-Ensemble | 0.60 | 220.79% | **-16.32%** | **163** | 🏆 **Risiko** |

**Empfehlung:** 70% classify_regime_v2() + 30% Ensemble für optimale Balance.

---

## 🔬 Modell-Evaluierung (2026-09-02)

### Framework-Integration (market_regime_detection)

Im Rahmen der Evaluierung wurde das Repository **market_regime_detection** (k3tikvats) als mögliche Erweiterung untersucht.

| Modell | AIC | BIC | Zeilen | Ergebnis |
| :--- | :---: | :---: | :---: | :--- |
| **Original (nur VIX)** | **-9.936,59** | **-9.861,17** | 3.965 | ✅ **Besser** |
| Erweitert (mit Framework-Features) | -8.468,74 | -8.268,37 | 3.203 | ❌ Schlechter |

**Fazit:** Die Framework-Features führen zu einem **Datenverlust von 19,2%** und verschlechtern die Modellgüte signifikant. Die Integration wird **nicht empfohlen**.

---

## 📁 Projektstruktur
