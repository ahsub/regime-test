"""
test_model_with_new_features.py – Testet Ihr Markov-Modell mit den neuen Features
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Daten laden
DATA_DIR = Path(__file__).parent / "data"
df = pd.read_csv(DATA_DIR / "market_data_enhanced_v2.csv", index_col=0, parse_dates=True)

print("=" * 60)
print("🧠 TEST: MARKOV-MODELL MIT NEUEN FEATURES")
print("=" * 60)

print(f"\n📊 Daten: {len(df)} Zeilen, {len(df.columns)} Spalten")
print(f"   Zeitraum: {df.index[0].date()} bis {df.index[-1].date()}")

# 1. Original-Modell (nur VIX)
print("\n" + "-" * 40)
print("1. ORIGINAL-MODELL (nur VIX)")
print("-" * 40)

vix_returns = df['VIX'].pct_change().dropna()
print(f"   VIX-Renditen: {len(vix_returns)} Tage")

mod_original = sm.tsa.MarkovRegression(
    endog=vix_returns,
    k_regimes=3,
    trend='c',
    switching_variance=True,
    switching_trend=True
)
res_original = mod_original.fit(disp=False)
print(f"   AIC: {res_original.aic:.2f}")
print(f"   BIC: {res_original.bic:.2f}")

# 2. Erweitertes Modell (mit Framework-Features)
print("\n" + "-" * 40)
print("2. ERWEITERTES MODELL (mit Framework-Features)")
print("-" * 40)

# Wähle numerische Features aus
feature_cols = [
    'volatility_20d', 'vix_change_5d', 'term_spread_pct',
    'gex_ratio', 'dix_ratio', 'put_ratio', 'skew_ratio'
]

# Nur Zeilen mit allen Features
df_features = df[feature_cols].dropna()
print(f"   Zeilen mit allen Features: {len(df_features)}")

# Normalisieren
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_features)

# Verwende VIX-Renditen an den gleichen Tagen
vix_returns_aligned = df.loc[df_features.index, 'VIX'].pct_change().dropna()
X_aligned = X_scaled[1:]  # erste Zeile für pct_change verloren

print(f"   Für Modell: {len(vix_returns_aligned)} Zeilen")

# Markov-Modell mit Features als exogene Variablen
mod_enhanced = sm.tsa.MarkovRegression(
    endog=vix_returns_aligned,
    k_regimes=3,
    trend='c',
    switching_variance=True,
    switching_trend=True,
    exog=X_aligned
)
res_enhanced = mod_enhanced.fit(disp=False)
print(f"   AIC: {res_enhanced.aic:.2f}")
print(f"   BIC: {res_enhanced.bic:.2f}")

# 3. Vergleich
print("\n" + "=" * 60)
print("📊 VERGLEICH")
print("=" * 60)
print(f"   Original-Modell:  AIC={res_original.aic:.2f}, BIC={res_original.bic:.2f}")
print(f"   Erweitertes Modell: AIC={res_enhanced.aic:.2f}, BIC={res_enhanced.bic:.2f}")

aic_improvement = res_original.aic - res_enhanced.aic
bic_improvement = res_original.bic - res_enhanced.bic

print(f"\n   Verbesserung:")
print(f"      AIC: {aic_improvement:+.2f} ({'✅ besser' if aic_improvement > 0 else '❌ schlechter'})")
print(f"      BIC: {bic_improvement:+.2f} ({'✅ besser' if bic_improvement > 0 else '❌ schlechter'})")

if aic_improvement > 0 and bic_improvement > 0:
    print("\n   ✅ Die neuen Features verbessern das Modell!")
else:
    print("\n   ⚠️ Die neuen Features verbessern das Modell nicht signifikant.")

print("\n" + "=" * 60)
print("🏁 TEST ABGESCHLOSSEN")
