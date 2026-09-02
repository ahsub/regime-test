"""
load_data_enhanced_v2.py – Erweiterter Data Loader mit Framework-Features
===========================================================================

Diese Version implementiert die Framework-Features manuell,
da der FeatureExtractor des Repositories nicht wie erwartet funktioniert.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from load_data import DATA_DIR, load_and_validate

# =============================================================================
# 1. BASIS-DATEN LADEN (UNVERÄNDERT)
# =============================================================================

def load_base_data() -> pd.DataFrame:
    """Lädt alle ursprünglichen Daten – identisch zu load_data.py"""
    print("📊 Lade Basis-Daten...")
    
    data_files = {
        'VIX': DATA_DIR / "VIX_History.csv",
        'VVIX': DATA_DIR / "VVIX_History.csv",
        'SKEW': DATA_DIR / "SKEW_History.csv",
        'VIX3M': DATA_DIR / "VIX3M_History.csv",
        'PUT': DATA_DIR / "PUT_History.csv",
        'BXM': DATA_DIR / "BXM_History.csv",
        'CLL': DATA_DIR / "CLL_History.csv",
        'DIX': DATA_DIR / "DIX.csv",
    }
    
    dfs = {}
    for name, path in data_files.items():
        df = load_and_validate(path, name)
        if not df.empty:
            dfs[name] = df
    
    df_combined = pd.DataFrame(index=sorted(set().union(*[d.index for d in dfs.values()])))
    
    for name, df in dfs.items():
        if name in ['VIX', 'VVIX', 'SKEW', 'VIX3M', 'PUT', 'BXM', 'CLL']:
            if 'Close' in df.columns:
                df_combined[name] = df['Close']
        elif name == 'DIX':
            for col in df.columns:
                if col not in df_combined.columns:
                    df_combined[col] = df[col]
    
    df_combined = df_combined.sort_index()
    print(f"   ✅ Basis-Daten geladen: {len(df_combined)} Zeilen")
    return df_combined

# =============================================================================
# 2. FRAMEWORK-FEATURES MANUELL IMPLEMENTIEREN
# =============================================================================

def add_framework_features_manual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implementiert die Framework-Features manuell basierend auf
    der Methodik von market_regime_detection.
    """
    df = df.copy()
    
    print("   🔧 Füge Framework-Features hinzu (manuell)...")
    
    # 1. Basis-Features (aus dem Framework)
    # Volatilität (verschiedene Fenster)
    for period in [5, 10, 20, 50]:
        df[f'volatility_{period}d'] = df['VIX'].rolling(period).std()
    
    # VIX-Level-Kategorien
    df['vix_level'] = pd.cut(
        df['VIX'],
        bins=[0, 15, 20, 25, 30, 100],
        labels=['LOW', 'MEDIUM_LOW', 'MEDIUM', 'MEDIUM_HIGH', 'HIGH']
    )
    
    # VIX-Änderungsraten
    for period in [1, 5, 10, 20]:
        df[f'vix_change_{period}d'] = df['VIX'].pct_change(period)
    
    # 2. Volatilität der Volatilität (VVIX-basiert)
    if 'VVIX' in df.columns:
        df['vvix_ratio'] = df['VVIX'] / df['VIX']
        df['vvix_signal'] = np.where(df['vvix_ratio'] > 1.5, 'HIGH_VOL_OF_VOL', 'NORMAL')
    
    # 3. Termstruktur-Features (VIX3M-basiert)
    if 'VIX3M' in df.columns:
        df['term_spread'] = df['VIX3M'] - df['VIX']
        df['term_spread_pct'] = df['term_spread'] / df['VIX']
        df['term_regime'] = np.where(
            df['term_spread'] < -1, 'BACKWARDATION',
            np.where(df['term_spread'] > 1, 'CONTANGO', 'FLAT')
        )
    
    # 4. GEX-basierte Features
    if 'gex' in df.columns:
        df['gex_positive'] = (df['gex'] > 0).astype(int)
        df['gex_ma_20'] = df['gex'].rolling(20).mean()
        df['gex_ratio'] = df['gex'] / df['gex_ma_20']
        df['gex_signal'] = np.where(
            df['gex'] > df['gex_ma_20'] * 1.2, 'STRONG_GEX',
            np.where(df['gex'] < df['gex_ma_20'] * 0.8, 'WEAK_GEX', 'NEUTRAL_GEX')
        )
    
    # 5. DIX-basierte Features
    if 'dix' in df.columns:
        df['dix_ma_20'] = df['dix'].rolling(20).mean()
        df['dix_ratio'] = df['dix'] / df['dix_ma_20']
        df['dix_signal'] = np.where(
            df['dix_ratio'] > 1.05, 'STRONG_DIX',
            np.where(df['dix_ratio'] < 0.95, 'WEAK_DIX', 'NEUTRAL_DIX')
        )
    
    # 6. PUT-basierte Features (Put/Call Ratio Proxy)
    if 'PUT' in df.columns:
        df['put_ma_20'] = df['PUT'].rolling(20).mean()
        df['put_ratio'] = df['PUT'] / df['put_ma_20']
        df['put_signal'] = np.where(
            df['put_ratio'] > 1.1, 'HIGH_PUT',
            np.where(df['put_ratio'] < 0.9, 'LOW_PUT', 'NEUTRAL_PUT')
        )
    
    # 7. SKEW-basierte Features (Tail Risk)
    if 'SKEW' in df.columns:
        df['skew_ma_20'] = df['SKEW'].rolling(20).mean()
        df['skew_ratio'] = df['SKEW'] / df['skew_ma_20']
        df['skew_signal'] = np.where(
            df['SKEW'] > 145, 'HIGH_SKEW',
            np.where(df['SKEW'] < 130, 'LOW_SKEW', 'NEUTRAL_SKEW')
        )
    
    # 8. Momentum-Features (basierend auf VIX)
    for period in [5, 10, 20, 50]:
        df[f'vix_momentum_{period}d'] = df['VIX'] / df['VIX'].shift(period) - 1
    
    # 9. Volatilitäts-Regime (basierend auf VIX-Level und Momentum)
    df['vol_regime'] = np.where(
        (df['VIX'] > 25) & (df['vix_momentum_5d'] > 0.05), 'HIGH_VOL_UP',
        np.where(
            (df['VIX'] > 25) & (df['vix_momentum_5d'] < -0.05), 'HIGH_VOL_DOWN',
            np.where(
                (df['VIX'] <= 25) & (df['vix_momentum_5d'] > 0.05), 'LOW_VOL_UP',
                np.where(
                    (df['VIX'] <= 25) & (df['vix_momentum_5d'] < -0.05), 'LOW_VOL_DOWN',
                    'NEUTRAL_VOL'
                )
            )
        )
    )
    
    # 10. Kombinierte Signale (Ensemble-Ansatz)
    # GEX + DIX + PUT + SKEW zu einem kombinierten Signal
    signal_cols = []
    if 'gex_signal' in df.columns:
        signal_cols.append('gex_signal')
    if 'dix_signal' in df.columns:
        signal_cols.append('dix_signal')
    if 'put_signal' in df.columns:
        signal_cols.append('put_signal')
    if 'skew_signal' in df.columns:
        signal_cols.append('skew_signal')
    
    if signal_cols:
        # Zähle bullische Signale
        bull_signals = ['STRONG_GEX', 'STRONG_DIX', 'LOW_PUT', 'LOW_SKEW']
        bear_signals = ['WEAK_GEX', 'WEAK_DIX', 'HIGH_PUT', 'HIGH_SKEW']
        
        df['bull_signal_count'] = df[signal_cols].apply(
            lambda x: sum([1 for s in x if s in bull_signals]), axis=1
        )
        df['bear_signal_count'] = df[signal_cols].apply(
            lambda x: sum([1 for s in x if s in bear_signals]), axis=1
        )
        
        df['composite_signal'] = np.where(
            df['bull_signal_count'] > df['bear_signal_count'], 'BULLISH',
            np.where(
                df['bear_signal_count'] > df['bull_signal_count'], 'BEARISH',
                'NEUTRAL'
            )
        )
    
    print(f"   ✅ Framework-Features hinzugefügt: {len([col for col in df.columns if col not in ['VIX', 'VVIX', 'SKEW', 'VIX3M', 'PUT', 'BXM', 'CLL', 'price', 'dix', 'gex']])} neue Spalten")
    
    return df

# =============================================================================
# 3. HAUPTPUNKTION
# =============================================================================

def load_data_enhanced() -> pd.DataFrame:
    """Hauptfunktion: Lädt alle Daten + Framework-Features"""
    print("=" * 60)
    print("🚀 STARTE ENHANCED DATA LOADER V2")
    print("=" * 60)
    
    # 1. Basis-Daten laden
    df = load_base_data()
    
    # 2. Framework-Features hinzufügen
    print("\n🔧 Füge Framework-Features hinzu...")
    df = add_framework_features_manual(df)
    
    # 3. Statistik anzeigen
    print("\n" + "=" * 60)
    print("📊 DATEN-ÜBERSICHT (ENHANCED V2)")
    print("=" * 60)
    print(f"   Zeilen: {len(df)}")
    print(f"   Spalten: {len(df.columns)}")
    print(f"   Zeitraum: {df.index[0].date()} bis {df.index[-1].date()}")
    
    # Spalten kategorisieren
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    print(f"\n   📂 Spalten-Kategorien:")
    print(f"      Numerische Spalten: {len(numeric_cols)}")
    print(f"      Kategorische Spalten: {len(categorical_cols)}")
    
    # 4. Daten speichern
    output_path = DATA_DIR / "market_data_enhanced_v2.csv"
    df.to_csv(output_path)
    print(f"\n💾 Daten gespeichert: {output_path}")
    
    print("\n" + "=" * 60)
    print("🏁 ENHANCED DATA LOADER V2 ABGESCHLOSSEN")
    print("=" * 60)
    
    return df

# =============================================================================
# 4. TEST
# =============================================================================

if __name__ == "__main__":
    df = load_data_enhanced()
    
    print("\n📋 ERSTE 5 ZEILEN:")
    print(df.head())
    
    print("\n📊 SPALTEN-ÜBERSICHT:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"   {col:30} {non_null:6} / {len(df):6} ({non_null/len(df)*100:.1f}%)")
