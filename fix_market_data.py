"""
fix_market_data.py – SP500_returns in market_data.csv ergänzen
================================================================

Dieses Skript lädt S&P 500-Daten und fügt sie als SP500_returns
in die bestehende market_data.csv ein.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
MARKET_DATA_FILE = DATA_DIR / "market_data.csv"

def load_market_data():
    """Lädt die bestehende market_data.csv."""
    df = pd.read_csv(MARKET_DATA_FILE, index_col=0, parse_dates=True)
    print(f"📊 market_data.csv geladen: {len(df)} Zeilen")
    return df

def load_sp500_returns():
    """Lädt S&P 500 Renditen (SPY)."""
    print("📥 Lade S&P 500 (SPY) Daten...")
    spy = yf.download('SPY', start='2011-01-01', end='2026-08-28', progress=False)
    returns = spy['Close'].pct_change()
    print(f"   ✅ {len(returns)} Tage geladen ({returns.index[0].date()} bis {returns.index[-1].date()})")
    return returns

def main():
    print("=" * 60)
    print("📈 FIX: SP500_returns in market_data.csv")
    print("=" * 60)
    
    # 1. Daten laden
    df = load_market_data()
    sp500_returns = load_sp500_returns()
    
    # 2. SP500_returns auf den Index von market_data alignieren
    df['SP500_returns'] = sp500_returns.reindex(df.index, method='ffill')
    
    # 3. Prüfen, ob die Spalte korrekt hinzugefügt wurde
    print(f"\n📊 SP500_returns hinzugefügt:")
    print(f"   {df['SP500_returns'].notna().sum()} von {len(df)} Tagen haben Werte")
    print(f"   Erste 5 Werte:\n{df['SP500_returns'].head()}")
    
    # 4. Speichern
    df.to_csv(MARKET_DATA_FILE)
    print(f"\n💾 market_data.csv aktualisiert: {MARKET_DATA_FILE}")
    
    print("\n" + "=" * 60)
    print("✅ SP500_returns erfolgreich hinzugefügt")
    print("=" * 60)

if __name__ == "__main__":
    main()
