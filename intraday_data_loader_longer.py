"""
intraday_data_loader_longer.py – Lädt längeren Intraday-Zeitraum
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
INTRADAY_DIR = DATA_DIR / "intraday"
INTRADAY_DIR.mkdir(exist_ok=True, parents=True)

def load_longer_intraday(period='5y', interval='60m'):
    """Lädt Intraday-Daten für längeren Zeitraum."""
    print("=" * 60)
    print(f"📊 LADE INTRADAY-DATEN ({period})")
    print("=" * 60)
    
    symbols = ['SPY', '^VIX']
    dfs = {}
    
    for symbol in symbols:
        print(f"\n📥 Lade {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"   ⚠️ Keine Daten für {symbol}")
                continue
            
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            df = df[['Close']].copy()
            df.columns = [symbol.replace('^', '')]
            df.index = df.index.floor('h')
            df = df[~df.index.duplicated(keep='first')]
            
            dfs[symbol] = df
            print(f"   ✅ {len(df)} Zeilen geladen")
            print(f"   Zeitraum: {df.index[0]} bis {df.index[-1]}")
            
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
    
    if not dfs:
        print("❌ Keine Daten geladen!")
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

if __name__ == "__main__":
    # Teste verschiedene Zeiträume
    print("🔍 TESTE VERFÜGBARE ZEITRÄUME")
    print("=" * 60)
    
    for period in ['2y', '5y']:
        df = load_longer_intraday(period=period, interval='60m')
        if not df.empty:
            print(f"\n✅ {period}: {len(df)} Zeilen")
        else:
            print(f"\n❌ {period}: Keine Daten verfügbar")
