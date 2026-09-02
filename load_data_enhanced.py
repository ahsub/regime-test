"""
load_data_enhanced.py – Erweiterter Daten-Loader mit Framework-Features
=======================================================================

Dieses Skript erweitert den bestehenden Daten-Loader um:
1. Alle ursprünglichen Daten (unverändert)
2. Framework-Features aus market_regime_detection
3. Zusätzliche technische Indikatoren

Die neuen Features werden als zusätzliche Spalten hinzugefügt,
ohne die bestehenden Spalten zu überschreiben.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import der bestehenden Funktionen
from load_data import DATA_DIR, load_and_validate

# Framework-Pfad
FRAMEWORK_PATH = Path(__file__).parent / "src" / "external" / "market_regime_detection"
if FRAMEWORK_PATH.exists():
    import sys
    sys.path.insert(0, str(FRAMEWORK_PATH))
    from data_pipeline.feature_engineering.feature_extractor import FeatureExtractor
    from data_pipeline.feature_engineering.normalizer import Normalizer
    FRAMEWORK_AVAILABLE = True
    print("✅ Framework FeatureExtractor geladen")
else:
    FRAMEWORK_AVAILABLE = False
    print("⚠️ Framework nicht verfügbar – verwende eigene Features")

# =============================================================================
# 1. BESTEHENDE DATEN LADEN (UNVERÄNDERT)
# =============================================================================

def load_base_data() -> pd.DataFrame:
    """
    Lädt alle ursprünglichen Daten – identisch zu load_data.py
    """
    print("📊 Lade Basis-Daten...")
    
    # Alle Datenquellen laden
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
    
    # DataFrames laden und zusammenführen
    dfs = {}
    for name, path in data_files.items():
        df = load_and_validate(path, name)
        if not df.empty:
            dfs[name] = df
    
    # Alle Daten zusammenführen (outer join auf Datum)
    df_combined = pd.DataFrame(index=sorted(set().union(*[d.index for d in dfs.values()])))
    
    for name, df in dfs.items():
        # Für CBOE-Daten: Close-Spalte verwenden
        if name in ['VIX', 'VVIX', 'SKEW', 'VIX3M', 'PUT', 'BXM', 'CLL']:
            if 'Close' in df.columns:
                df_combined[name] = df['Close']
        # Für DIX: Alle Spalten übernehmen
        elif name == 'DIX':
            for col in df.columns:
                if col not in df_combined.columns:
                    df_combined[col] = df[col]
    
    # Datum sortieren
    df_combined = df_combined.sort_index()
    
    print(f"   ✅ Basis-Daten geladen: {len(df_combined)} Zeilen")
    print(f"   Spalten: {list(df_combined.columns)}")
    
    return df_combined

# =============================================================================
# 2. EIGENE TECHNISCHE FEATURES (IHR EXISTIERENDER ANSATZ)
# =============================================================================

def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt technische Indikatoren hinzu, die Sie bereits in Ihren Analysen verwenden.
    Diese basieren auf Ihrem existing_code/ Ansatz.
    """
    df = df.copy()
    
    # Renditen
    df['returns'] = df.get('SPY', df.get('Close', pd.Series(index=df.index))).pct_change()
    df['log_returns'] = np.log(df.get('SPY', df.get('Close', pd.Series(index=df.index))) / 
                                df.get('SPY', df.get('Close', pd.Series(index=df.index))).shift(1))
    
    # Volatilität (verschiedene Fenster)
    if 'VIX' in df.columns:
        df['vix_returns'] = df['VIX'].pct_change()
        df['vix_volatility'] = df['vix_returns'].rolling(20).std() * np.sqrt(252)
    
    # Momentum (verschiedene Fenster)
    price_col = 'SPY' if 'SPY' in df.columns else 'Close' if 'Close' in df.columns else None
    if price_col:
        for period in [5, 10, 20, 50, 200]:
            df[f'momentum_{period}'] = df[price_col] / df[price_col].shift(period) - 1
    
    # VIX-Termstruktur (Ihre Kernlogik)
    if 'VIX' in df.columns and 'VIX3M' in df.columns:
        df['vix_term_ratio'] = df['VIX3M'] / df['VIX']
        df['vix_term_structure'] = np.where(
            df['vix_term_ratio'] < 0.98, 'STRESS_UNSTABLE',
            np.where(
                df['vix_term_ratio'] < 1.05, 'POST_PANIC_REVERSION',
                np.where(
                    df['VIX'] > 25, 'BULL_FRAGILE', 'BULL_QUIET'
                )
            )
        )
    
    # GEX (falls vorhanden)
    if 'GEX' in df.columns:
        df['gex_positive'] = (df['GEX'] > 0).astype(int)
    
    # DIX (falls vorhanden)
    if 'DIX' in df.columns:
        df['dix_level'] = df['DIX']
        df['dix_ma'] = df['DIX'].rolling(20).mean()
        df['dix_ratio'] = df['DIX'] / df['dix_ma']
    
    return df

# =============================================================================
# 3. FRAMEWORK-FEATURES (AUS market_regime_detection)
# =============================================================================

def add_framework_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt Features aus dem market_regime_detection Framework hinzu.
    """
    if not FRAMEWORK_AVAILABLE:
        print("   ⚠️ Framework nicht verfügbar – überspringe Framework-Features")
        return df
    
    df = df.copy()
    
    try:
        # Feature Extractor initialisieren
        extractor = FeatureExtractor()
        
        # Framework-Features extrahieren
        print("   🔧 Extrahiere Framework-Features...")
        framework_features = extractor.extract_all_features(df)
        
        # Features hinzufügen (nur neue Spalten)
        for col in framework_features.columns:
            if col not in df.columns:
                df[col] = framework_features[col]
                print(f"      + {col}")
        
        print(f"   ✅ {len(framework_features.columns)} Framework-Features hinzugefügt")
        
    except Exception as e:
        print(f"   ⚠️ Fehler bei Framework-Features: {e}")
    
    return df

# =============================================================================
# 4. HAUPTPUNKTION: ENHANCED DATA LOADER
# =============================================================================

def load_data_enhanced(include_framework: bool = True) -> pd.DataFrame:
    """
    Hauptfunktion: Lädt alle Daten + Framework-Features.
    
    Parameter:
    ----------
    include_framework : bool
        Ob Framework-Features hinzugefügt werden sollen.
    
    Rückgabe:
    --------
    pd.DataFrame : Vollständiger Datensatz mit allen Features
    """
    print("=" * 60)
    print("🚀 STARTE ENHANCED DATA LOADER")
    print("=" * 60)
    
    # 1. Basis-Daten laden
    df = load_base_data()
    
    # 2. Eigene technische Features hinzufügen
    print("\n🔧 Füge eigene technische Features hinzu...")
    df = add_technical_features(df)
    
    # 3. Framework-Features hinzufügen (optional)
    if include_framework:
        print("\n🔧 Füge Framework-Features hinzu...")
        df = add_framework_features(df)
    
    # 4. Statistik anzeigen
    print("\n" + "=" * 60)
    print("📊 DATEN-ÜBERSICHT (ENHANCED)")
    print("=" * 60)
    print(f"   Zeilen: {len(df)}")
    print(f"   Spalten: {len(df.columns)}")
    print(f"   Zeitraum: {df.index[0].date()} bis {df.index[-1].date()}")
    
    # Spalten gruppieren
    base_cols = ['VIX', 'VVIX', 'SKEW', 'VIX3M', 'PUT', 'BXM', 'CLL', 'DIX', 'GEX']
    tech_cols = [col for col in df.columns if col.startswith(('returns', 'momentum', 'vix_', 'gex_', 'dix_'))]
    framework_cols = [col for col in df.columns if col not in base_cols + tech_cols + ['Close']]
    
    print(f"\n   📂 Spalten-Kategorien:")
    print(f"      Basis-Daten: {len([c for c in base_cols if c in df.columns])}")
    print(f"      Technische Features: {len(tech_cols)}")
    print(f"      Framework-Features: {len(framework_cols)}")
    
    # 5. Daten speichern (optional)
    output_path = DATA_DIR / "market_data_enhanced.csv"
    df.to_csv(output_path)
    print(f"\n💾 Daten gespeichert: {output_path}")
    
    print("\n" + "=" * 60)
    print("🏁 ENHANCED DATA LOADER ABGESCHLOSSEN")
    print("=" * 60)
    
    return df

# =============================================================================
# 5. TEST-FUNKTION
# =============================================================================

def test_enhanced_loader():
    """
    Testet den erweiterten Data Loader und zeigt die ersten Zeilen.
    """
    df = load_data_enhanced(include_framework=True)
    
    print("\n📋 ERSTE 5 ZEILEN:")
    print(df.head())
    
    print("\n📊 SPALTEN-ÜBERSICHT:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"   {col:20} {non_null:6} / {len(df):6} ({non_null/len(df)*100:.1f}%)")
    
    return df

# =============================================================================
# 6. AUSFÜHRUNG
# =============================================================================

if __name__ == "__main__":
    test_enhanced_loader()
