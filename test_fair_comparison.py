"""
test_fair_comparison.py – Fairer Vergleich: gleicher Zeitraum
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
df = pd.read_csv(DATA_DIR / "market_data_enhanced_v2.csv", index_col=0, parse_dates=True)

print("=" * 60)
print("📊 FAIRER VERGLEICH: GLEICHER ZEITRAUM")
print("=" * 60)

# 1. Gleicher Zeitraum: 2011–2026 (wo alle Features verfügbar sind)
df_limited = df[df.index >= '2011-01-01']
print(f"\n📊 Zeitraum: {df_limited.index[0].date()} bis {df_limited.index[-1].date()}")
print(f"   Zeilen: {len(df_limited)}")

# 2. Original-Modell (nur VIX) auf diesem Zeitraum
print("\n" + "-" * 40)
print("1. ORIGINAL-MODELL (nur VIX, 2011-2026)")
print("-" * 40)

vix_returns_limited = df_limited['VIX'].pct_change().dropna()
print(f"   VIX-Renditen: {len(vix_returns_limited)} Tage")

mod_original_limited = sm.tsa.MarkovRegression(
    endog=vix_returns_limited,
    k_regimes=3,
    trend='c',
    switching_variance=True,
    switching_trend=True
)
res_original_limited = mod_original_limited.fit(disp=False)
print(f"   AIC: {res_original_limited.aic:.2f}")
print(f"   BIC: {res_original_limited.bic:.2f}")

# 3. Erweitertes Modell (gleicher Zeitraum)
print("\n" + "-" * 40)
print("2. ERWEITERTES MODELL (mit Features, 2011-2026)")
print("-" * 40)

feature_cols = [
    'volatility_20d', 'vix_change_5d', 'term_spread_pct',
    'gex_ratio', 'dix_ratio', 'put_ratio', 'skew_ratio'
]

df_features = df_limited[feature_cols].dropna()
print(f"   Zeilen mit allen Features: {len(df_features)}")

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_features)

vix_returns_aligned = df_limited.loc[df_features.index, 'VIX'].pct_change().dropna()
X_aligned = X_scaled[1:]  # erste Zeile für pct_change verloren

print(f"   Für Modell: {len(vix_returns_aligned)} Zeilen")

mod_enhanced_limited = sm.tsa.MarkovRegression(
    endog=vix_returns_aligned,
    k_regimes=3,
    trend='c',
    switching_variance=True,
    switching_trend=True,
    exog=X_aligned
)
res_enhanced_limited = mod_enhanced_limited.fit(disp=False)
print(f"   AIC: {res_enhanced_limited.aic:.2f}")
print(f"   BIC: {res_enhanced_limited.bic:.2f}")

# 4. Fairer Vergleich
print("\n" + "=" * 60)
print("📊 FAIRER VERGLEICH (gleicher Zeitraum)")
print("=" * 60)
print(f"   Original (2011-2026):  AIC={res_original_limited.aic:.2f}, BIC={res_original_limited.bic:.2f}")
print(f"   Erweitert (2011-2026): AIC={res_enhanced_limited.aic:.2f}, BIC={res_enhanced_limited.bic:.2f}")

aic_improvement = res_original_limited.aic - res_enhanced_limited.aic
bic_improvement = res_original_limited.bic - res_enhanced_limited.bic

print(f"\n   Verbesserung:")
print(f"      AIC: {aic_improvement:+.2f} ({'✅ besser' if aic_improvement > 0 else '❌ schlechter'})")
print(f"      BIC: {bic_improvement:+.2f} ({'✅ besser' if bic_improvement > 0 else '❌ schlechter'})")

if aic_improvement > 0 and bic_improvement > 0:
    print("\n   ✅ Die neuen Features verbessern das Modell auf dem gleichen Zeitraum!")
elif aic_improvement < 0 and bic_improvement < 0:
    print("\n   ⚠️ Die neuen Features verschlechtern das Modell auf dem gleichen Zeitraum.")
else:
    print("\n   🔄 Gemischte Ergebnisse – nicht eindeutig.")

print("\n" + "=" * 60)
print("🏁 FAIRER VERGLEICH ABGESCHLOSSEN")
