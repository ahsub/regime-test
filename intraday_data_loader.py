"""
intraday_data_loader.py – Lädt Intraday-Daten für Regime-Erkennung
===========================================================================

Lädt SPY und VIX auf 60-Minuten-Basis von Yahoo Finance.
Zeitraum: 2 Jahre (ausreichend für Test, erweiterbar)
"""

import pandas as pd
import yfinance as yf
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

INTRADAY_DIR = DATA_DIR / "intraday"
INTRADAY_DIR.mkdir(exist_ok=True)

# Standard-Zeitraum: 2 Jahre (kann erweitert werden)
DEFAULT_PERIOD = "2y"
DEFAULT_INTERVAL = "60m"  # 60 Minuten

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_intraday_data(symbols=['SPY', '^VIX'], 
                       period=DEFAULT_PERIOD, 
                       interval=DEFAULT_INTERVAL) -> pd.DataFrame:
    """
    Lädt Intraday-Daten für angegebene Symbole.
    
    Parameter:
    ----------
    symbols : list
        Liste der Symbole (z.B. ['SPY', '^VIX'])
    period : str
        Zeitraum (z.B. '2y', '1y', '6mo')
    interval : str
        Intervall (z.B. '60m', '30m', '15m')
    
    Rückgabe:
    --------
    pd.DataFrame : Kombinierte Intraday-Daten
    """
    print("=" * 60)
    print("📊 LADE INTRADAY-DATEN")
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
            
            # Spalten umbenennen für einheitliches Format
            df = df.rename(columns={
                'Open': f'{symbol}_Open',
                'High': f'{symbol}_High',
                'Low': f'{symbol}_Low',
                'Close': f'{symbol}_Close',
                'Volume': f'{symbol}_Volume'
            })
            
            dfs[symbol] = df
            print(f"   ✅ {len(df)} Zeilen geladen")
            print(f"   Zeitraum: {df.index[0]} bis {df.index[-1]}")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {symbol}: {e}")
    
    if not dfs:
        print("\n❌ Keine Daten geladen!")
        return pd.DataFrame()
    
    # Alle Daten zusammenführen (inner join auf Index)
    df_combined = dfs[list(dfs.keys())[0]]
    for symbol in list(dfs.keys())[1:]:
        df_combined = pd.merge(df_combined, dfs[symbol], 
                               left_index=True, right_index=True, how='inner')
    
    # Spalten umbenennen für einfacheren Zugriff
    rename_map = {}
    for symbol in symbols:
        if symbol in dfs:
            rename_map[f'{symbol}_Close'] = symbol.replace('^', '')
    
    df_combined = df_combined.rename(columns=rename_map)
    
    print("\n" + "=" * 60)
    print("📊 DATEN-ÜBERSICHT")
    print("=" * 60)
    print(f"   Zeilen: {len(df_combined)}")
    print(f"   Spalten: {list(df_combined.columns)}")
    print(f"   Zeitraum: {df_combined.index[0]} bis {df_combined.index[-1]}")
    
    # Daten speichern
    csv_path = INTRADAY_DIR / f"intraday_{interval}_{period}.csv"
    df_combined.to_csv(csv_path)
    print(f"\n💾 Daten gespeichert: {csv_path}")
    
    return df_combined

# =============================================================================
# 3. VIX3M PROXY (für Intraday)
# =============================================================================

def load_vix3m_proxy() -> pd.Series:
    """
    Lädt VIX3M als täglichen Proxy für Intraday-Analysen.
    Der tägliche Wert wird mit ffill auf Intraday-Index übertragen.
    """
    vix3m_path = DATA_DIR / "VIX3M_History.csv"
    
    if not vix3m_path.exists():
        print("⚠️ VIX3M-Datei nicht gefunden. Lade von CBOE...")
        # Fallback: Lade von CBOE
        import requests
        url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv"
        response = requests.get(url)
        with open(vix3m_path, 'wb') as f:
            f.write(response.content)
    
    df = pd.read_csv(vix3m_path, parse_dates=['Date'])
    df = df.set_index('Date')
    df = df.sort_index()
    
    return df['Close']

# =============================================================================
# 4. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion zum Laden der Intraday-Daten"""
    
    # 1. Intraday-Daten laden
    df = load_intraday_data(
        symbols=['SPY', '^VIX'],
        period='2y',
        interval='60m'
    )
    
    if df.empty:
        print("❌ Keine Daten geladen – Abbruch")
        return
    
    # 2. VIX3M Proxy laden
    print("\n" + "=" * 60)
    print("📊 LADE VIX3M PROXY")
    print("=" * 60)
    
    vix3m = load_vix3m_proxy()
    print(f"   VIX3M: {len(vix3m)} tägliche Werte")
    
    # 3. VIX3M auf Intraday-Index übertragen
    # Extrahiere Datum aus Intraday-Index (nur Datum, ohne Uhrzeit)
    intraday_dates = df.index.normalize()
    
    # Erstelle leere Series mit Intraday-Index
    vix3m_intraday = pd.Series(index=df.index, dtype=float)
    
    # Für jeden Intraday-Index: fülle mit Tageswert
    for date in df.index:
        # Finde den täglichen VIX3M-Wert für dieses Datum
        date_only = date.normalize()
        if date_only in vix3m.index:
            vix3m_intraday[date] = vix3m.loc[date_only]
        else:
            # Fallback: nächster verfügbarer Wert (ffill)
            vix3m_intraday[date] = vix3m.asof(date_only)
    
    # 4. VIX3M zu Intraday-Daten hinzufügen
    df['VIX3M'] = vix3m_intraday
    
    # 5. Daten speichern
    csv_path = INTRADAY_DIR / "intraday_with_vix3m.csv"
    df.to_csv(csv_path)
    print(f"\n💾 Daten mit VIX3M gespeichert: {csv_path}")
    
    # 6. Statistik
    print("\n" + "=" * 60)
    print("📊 FINALE DATEN-ÜBERSICHT")
    print("=" * 60)
    print(f"   Zeilen: {len(df)}")
    print(f"   Spalten: {list(df.columns)}")
    print(f"   VIX3M Coverage: {df['VIX3M'].notna().sum()}/{len(df)} ({df['VIX3M'].notna().sum()/len(df)*100:.1f}%)")
    
    return df

if __name__ == "__main__":
    df = main()
