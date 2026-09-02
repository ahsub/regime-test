"""
intraday_data_loader_v4.py – Korrigierter Intraday-Daten-Loader
"""

import pandas as pd
import yfinance as yf
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
INTRADAY_DIR = DATA_DIR / "intraday"
INTRADAY_DIR.mkdir(exist_ok=True, parents=True)

def load_intraday_data(symbols=['SPY', '^VIX'], period='2y', interval='60m'):
    """Lädt Intraday-Daten."""
    print("=" * 60)
    print("📊 LADE INTRADAY-DATEN (V4)")
    print("=" * 60)
    print(f"   Symbole: {symbols}")
    print(f"   Zeitraum: {period}")
    print(f"   Intervall: {interval}")
    
    dfs = {}
    for symbol in symbols:
        print(f"\n📥 Lade {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"   ⚠️ Keine Daten für {symbol}")
                continue
            
            df = df[['Close']].copy()
            df.columns = [symbol.replace('^', '')]
            df.index = df.index.floor('h')
            df = df[~df.index.duplicated(keep='first')]
            
            dfs[symbol] = df
            print(f"   ✅ {len(df)} Zeilen geladen")
            print(f"   Zeitraum: {df.index[0]} bis {df.index[-1]}")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {symbol}: {e}")
    
    if not dfs:
        print("\n❌ Keine Daten geladen!")
        return pd.DataFrame()
    
    # Zusammenführen
    all_times = pd.DatetimeIndex([])
    for df in dfs.values():
        all_times = all_times.union(df.index)
    all_times = all_times.sort_values()
    
    df_combined = pd.DataFrame(index=all_times)
    for symbol, df in dfs.items():
        col_name = symbol.replace('^', '')
        df_combined[col_name] = df.reindex(all_times, method='ffill')
    
    df_combined = df_combined.dropna()
    
    print("\n" + "=" * 60)
    print("📊 DATEN-ÜBERSICHT")
    print("=" * 60)
    print(f"   Zeilen: {len(df_combined)}")
    print(f"   Spalten: {list(df_combined.columns)}")
    if len(df_combined) > 0:
        print(f"   Zeitraum: {df_combined.index[0]} bis {df_combined.index[-1]}")
    
    csv_path = INTRADAY_DIR / f"intraday_{interval}_{period}.csv"
    df_combined.to_csv(csv_path)
    print(f"\n💾 Daten gespeichert: {csv_path}")
    
    return df_combined

def load_vix3m_proxy():
    """Lädt VIX3M mit korrekten Spaltennamen."""
    vix3m_path = DATA_DIR / "VIX3M_History.csv"
    
    if not vix3m_path.exists():
        print("⚠️ VIX3M-Datei nicht gefunden.")
        return pd.Series()
    
    print("   📥 Lade VIX3M...")
    
    # Mit korrekten Spaltennamen laden (GROSSBUCHSTABEN)
    df = pd.read_csv(vix3m_path, parse_dates=['DATE'])
    df = df.set_index('DATE')
    df = df.sort_index()
    
    # CLOSE-Spalte verwenden (GROSSBUCHSTABEN)
    if 'CLOSE' in df.columns:
        vix3m_series = df['CLOSE']
    elif 'Close' in df.columns:
        vix3m_series = df['Close']
    else:
        # Fallback: erste numerische Spalte
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            vix3m_series = df[numeric_cols[0]]
            print(f"   ⚠️ Verwende '{numeric_cols[0]}' als Close")
        else:
            print("   ❌ Keine Close-Spalte gefunden")
            return pd.Series()
    
    print(f"   ✅ VIX3M geladen: {len(vix3m_series)} Einträge")
    print(f"   Zeitraum: {vix3m_series.index[0]} bis {vix3m_series.index[-1]}")
    
    return vix3m_series

def main():
    """Hauptfunktion."""
    
    # 1. Intraday-Daten laden
    df = load_intraday_data(
        symbols=['SPY', '^VIX'],
        period='2y',
        interval='60m'
    )
    
    if df.empty:
        print("❌ Keine Daten geladen – Abbruch")
        return df
    
    # 2. VIX3M Proxy laden
    print("\n" + "=" * 60)
    print("📊 LADE VIX3M PROXY")
    print("=" * 60)
    
    vix3m = load_vix3m_proxy()
    
    if vix3m.empty:
        print("⚠️ VIX3M nicht verfügbar – erstelle fallback")
        df['VIX3M'] = df['VIX'] * 1.05
    else:
        print(f"   VIX3M: {len(vix3m)} tägliche Werte")
        
        # VIX3M auf Intraday-Index übertragen
        vix3m_intraday = pd.Series(index=df.index, dtype=float)
        
        for idx in df.index:
            date_only = idx.normalize()
            if date_only in vix3m.index:
                vix3m_intraday[idx] = vix3m.loc[date_only]
            else:
                vix3m_intraday[idx] = vix3m.asof(date_only)
        
        df['VIX3M'] = vix3m_intraday
    
    # 3. Daten speichern
    csv_path = INTRADAY_DIR / "intraday_with_vix3m.csv"
    df.to_csv(csv_path)
    print(f"\n💾 Daten mit VIX3M gespeichert: {csv_path}")
    
    # 4. Statistik
    print("\n" + "=" * 60)
    print("📊 FINALE DATEN-ÜBERSICHT")
    print("=" * 60)
    print(f"   Zeilen: {len(df)}")
    print(f"   Spalten: {list(df.columns)}")
    if len(df) > 0:
        vix3m_count = df['VIX3M'].notna().sum()
        print(f"   VIX3M Coverage: {vix3m_count}/{len(df)} ({vix3m_count/len(df)*100:.1f}%)")
    
    return df

if __name__ == "__main__":
    df = main()
