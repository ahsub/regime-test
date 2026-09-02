"""
intraday_regime.py – Intraday-Regime-Erkennung
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def classify_regime_intraday(row) -> str:
    """
    Intraday-Version der classify_regime_v2() Logik.
    """
    vix = row.get('VIX', np.nan)
    vix3m = row.get('VIX3M', np.nan)
    gex = row.get('gex', np.nan)
    
    if pd.isna(vix) or pd.isna(vix3m) or vix <= 0:
        return 'NEUTRAL'
    
    ratio = vix3m / vix
    
    if ratio < 0.98:
        return 'STRESS_UNSTABLE'
    elif 0.98 <= ratio < 1.05:
        return 'POST_PANIC_REVERSION'
    elif ratio >= 1.05 and vix > 25:
        if not pd.isna(gex) and gex < 0:
            return 'STRESS_UNSTABLE'
        return 'BULL_FRAGILE'
    elif ratio >= 1.05 and vix <= 25:
        if not pd.isna(gex) and gex < 0:
            return 'STRESS_UNSTABLE'
        return 'BULL_QUIET'
    else:
        return 'NEUTRAL'

def get_position_intraday(regime: str, base_position: float = 1.0) -> float:
    """Positionslogik basierend auf Regime."""
    position_map = {
        'STRESS_UNSTABLE': 0.0,
        'POST_PANIC_REVERSION': 1.0 * base_position,
        'BULL_FRAGILE': 0.7 * base_position,
        'BULL_QUIET': 1.0 * base_position,
        'NEUTRAL': 0.5 * base_position
    }
    return position_map.get(regime, 0.5 * base_position)

def detect_intraday_regimes(df: pd.DataFrame) -> pd.DataFrame:
    """Führt die Intraday-Regime-Erkennung durch."""
    df = df.copy()
    
    print("=" * 60)
    print("🔍 INTRADAY-REGIME-ERKENNUNG")
    print("=" * 60)
    print(f"   {len(df)} Zeilen zu klassifizieren")
    
    df['regime'] = df.apply(classify_regime_intraday, axis=1)
    df['position'] = df['regime'].apply(get_position_intraday)
    
    print("\n📊 REGIME-VERTEILUNG:")
    regime_counts = df['regime'].value_counts()
    for regime, count in regime_counts.items():
        pct = count / len(df) * 100
        print(f"   {regime:25} {count:6} ({pct:5.1f}%)")
    
    return df

def main():
    """Hauptfunktion."""
    data_path = Path(__file__).parent / "data" / "intraday" / "intraday_with_vix3m.csv"
    
    if not data_path.exists():
        print(f"❌ Daten nicht gefunden: {data_path}")
        print("   Führen Sie zuerst intraday_data_loader_v5.py aus")
        return
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"📊 Daten geladen: {len(df)} Zeilen")
    
    df = detect_intraday_regimes(df)
    
    output_path = Path(__file__).parent / "data" / "intraday" / "intraday_regimes.csv"
    df.to_csv(output_path)
    print(f"\n💾 Ergebnisse gespeichert: {output_path}")
    
    return df

if __name__ == "__main__":
    df = main()
