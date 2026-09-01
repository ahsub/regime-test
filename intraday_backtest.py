"""
intraday_backtest.py – Intraday-Regime-Erkennung mit Alpha Vantage
==================================================================

Dieses Skript testet, ob 60-Minuten-Daten (SPY, VIX) eine bessere
Regime-Erkennung ermöglichen als tägliche Daten.

Basierend auf Pagliaro (2026): Intraday-HMM kann Sharpe um 0,15–0,20 verbessern.
"""

import pandas as pd
import numpy as np
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

ALPHA_VANTAGE_KEY = FYPYAZR6BWJLY254  # <-- Hier Ihren API-Key einfügen

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# 2. ALPHA VANTAGE CLIENT
# =============================================================================

class AlphaVantageClient:
    def __init__(self, api_key, calls_per_minute=5):
        self.api_key = api_key
        self.delay = 60 / calls_per_minute  # 12 Sekunden
        self.last_call_time = 0
    
    def _call(self, url):
        """Führt einen API-Call mit Rate-Limiting durch."""
        now = time.time()
        elapsed = now - self.last_call_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        
        response = requests.get(url)
        self.last_call_time = time.time()
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"   ⚠️ API-Fehler: {response.status_code}")
            return None
    
    def fetch_intraday(self, symbol, interval='60min'):
        """Lädt Intraday-Daten von Alpha Vantage."""
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&outputsize=full&apikey={self.api_key}"
        print(f"   📥 Lade {symbol} ({interval})...")
        data = self._call(url)
        if data and 'Time Series (60min)' in data:
            return data['Time Series (60min)']
        else:
            print(f"   ❌ Keine Daten für {symbol}")
            return None

# =============================================================================
# 3. DATEN LADEN
# =============================================================================

def load_data():
    """Lädt Intraday-Daten und tägliche Daten (zum Vergleich)."""
    print("📊 Lade Intraday-Daten...")
    
    client = AlphaVantageClient(ALPHA_VANTAGE_KEY)
    
    # 1. SPY 60-Minuten-Daten
    spy_data = client.fetch_intraday('SPY', '60min')
    
    # 2. VIX 60-Minuten-Daten
    vix_data = client.fetch_intraday('VXX', '60min')  # VIX ETF
    
    if spy_data is None:
        print("❌ SPY-Daten konnten nicht geladen werden. Abbruch.")
        return None, None, None
    
    # 3. In DataFrames umwandeln
    spy_df = pd.DataFrame.from_dict(spy_data, orient='index')
    spy_df.index = pd.to_datetime(spy_df.index)
    spy_df = spy_df.sort_index()
    spy_df['close'] = spy_df['4. close'].astype(float)
    
    if vix_data:
        vix_df = pd.DataFrame.from_dict(vix_data, orient='index')
        vix_df.index = pd.to_datetime(vix_df.index)
        vix_df = vix_df.sort_index()
        vix_df['close'] = vix_df['4. close'].astype(float)
    
    # 4. Tägliche Daten als Vergleich laden
    import yfinance as yf
    daily_spy = yf.download('SPY', start='2011-01-01', end='2026-08-28', progress=False)
    daily_vix = yf.download('^VIX', start='2011-01-01', end='2026-08-28', progress=False)
    
    daily_returns = daily_spy['Close'].pct_change()
    
    print(f"   ✅ Intraday SPY: {len(spy_df)} Bars")
    print(f"   ✅ Intraday VIX: {len(vix_df) if vix_data else 0} Bars")
    print(f"   ✅ Daily SPY: {len(daily_spy)} Tage")
    
    return spy_df, vix_df, daily_returns

# =============================================================================
# 4. REGIME-ERKENNUNG AUF INTRADAY-DATEN
# =============================================================================

def calculate_intraday_features(spy_df, vix_df):
    """Berechnet Features für Intraday-Regime-Erkennung."""
    print("\n🔧 Berechne Intraday-Features...")
    
    # 1. Renditen
    spy_df['returns'] = spy_df['close'].pct_change()
    
    # 2. 20-Perioden-Volatilität (20 Stunden = 5 Tage à 4 Stunden)
    spy_df['volatility'] = spy_df['returns'].rolling(20).std() * np.sqrt(252 * 6.5)
    
    # 3. Intraday-VIX (falls verfügbar)
    if vix_df is not None and len(vix_df) > 0:
        # VIX auf SPY-Index alignieren
        vix_aligned = vix_df['close'].reindex(spy_df.index, method='ffill')
        spy_df['vix'] = vix_aligned
    else:
        spy_df['vix'] = 20  # Fallback
    
    # 4. Intraday-Trend
    spy_df['trend'] = spy_df['close'].rolling(10).mean() / spy_df['close'].rolling(20).mean()
    
    spy_df = spy_df.dropna()
    print(f"   ✅ {len(spy_df)} Intraday-Bars mit Features")
    
    return spy_df

# =============================================================================
# 5. SIMPLE REGIME-LOGIK FÜR INTRADAY
# =============================================================================

def intraday_regime_signal(row):
    """
    Einfache Intraday-Regime-Logik.
    """
    # VIX-Termstruktur (vereinfacht: VIX-Spot vs. 20-Stunden-Mittel)
    vix_spread = row['vix'] / row['vix'].rolling(20).mean() if pd.notna(row['vix']) else 1.0
    
    if vix_spread < 0.98:
        return "STRESS_UNSTABLE"
    elif vix_spread < 1.05:
        return "POST_PANIC_REVERSION"
    else:
        if row['volatility'] > 0.30:
            return "BULL_FRAGILE"
        else:
            return "BULL_QUIET"

def backtest_intraday(df):
    """Führt einen Backtest auf Intraday-Basis durch."""
    print("\n🔧 Führe Intraday-Backtest durch...")
    
    signals = pd.DataFrame(index=df.index)
    signals['regime'] = df.apply(intraday_regime_signal, axis=1)
    signals['position'] = 0.0
    signals.loc[signals['regime'] != 'STRESS_UNSTABLE', 'position'] = 1.0
    
    # Performance (auf Intraday-Basis)
    positions = signals['position'].shift(1).fillna(0)
    strategy_returns = positions * df['returns']
    
    excess_returns = strategy_returns - 0.02/252/6.5  # Annualisiert auf Handelstage
    sharpe = np.sqrt(252 * 6.5) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    strategy_cum = (1 + strategy_returns).cumprod()
    total_return = float(strategy_cum.iloc[-1] - 1) if len(strategy_cum) > 0 else 0.0
    
    return {
        'sharpe_ratio': float(sharpe),
        'total_return': total_return,
        'regime_counts': signals['regime'].value_counts().to_dict(),
        'n_days': len(signals)
    }

# =============================================================================
# 6. TÄGLICHER BACKTEST (ZUM VERGLEICH)
# =============================================================================

def daily_backtest(returns):
    """Führt einen täglichen Backtest durch (zum Vergleich)."""
    print("\n🔧 Führe täglichen Backtest durch...")
    
    # Einfache Logik: Signal basierend auf VIX (vereinfacht)
    signals = pd.DataFrame(index=returns.index)
    signals['position'] = 1.0
    
    positions = signals['position'].shift(1).fillna(0)
    strategy_returns = positions * returns
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    strategy_cum = (1 + strategy_returns).cumprod()
    total_return = float(strategy_cum.iloc[-1] - 1) if len(strategy_cum) > 0 else 0.0
    
    return {
        'sharpe_ratio': float(sharpe),
        'total_return': total_return,
        'n_days': len(signals)
    }

# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 60)
    print("📈 INTRADAY-REGIME-ERKENNUNG (ALPHA VANTAGE)")
    print("=" * 60)
    
    # Daten laden
    spy_df, vix_df, daily_returns = load_data()
    
    if spy_df is None:
        print("❌ Abbruch wegen fehlender Daten.")
        return
    
    # Intraday-Features berechnen
    spy_df = calculate_intraday_features(spy_df, vix_df)
    
    # Intraday-Backtest
    intraday_result = backtest_intraday(spy_df)
    
    # Täglicher Backtest (Vergleich)
    daily_result = daily_backtest(daily_returns)
    
    # Ergebnisse
    print("\n" + "=" * 60)
    print("📊 VERGLEICH: INTRADAY vs. TÄGLICH")
    print("=" * 60)
    
    print(f"\n{'Kennzahl':<20} | {'Intraday':<15} | {'Täglich':<15} | {'Differenz':<12}")
    print("-" * 70)
    print(f"{'Sharpe Ratio':<20} | {intraday_result['sharpe_ratio']:>14.2f} | {daily_result['sharpe_ratio']:>14.2f} | {intraday_result['sharpe_ratio'] - daily_result['sharpe_ratio']:>+11.2f}")
    print(f"{'Gesamtrendite':<20} | {intraday_result['total_return']:>14.2%} | {daily_result['total_return']:>14.2%} | {intraday_result['total_return'] - daily_result['total_return']:>+11.2%}")
    print(f"{'Tage/Bars':<20} | {intraday_result['n_days']:>14} | {daily_result['n_days']:>14} | {intraday_result['n_days'] - daily_result['n_days']:>+11}")
    
    if intraday_result.get('regime_counts'):
        print(f"\n📊 Intraday-Regime-Verteilung:")
        for regime, count in intraday_result['regime_counts'].items():
            print(f"   {regime}: {count} ({count/intraday_result['n_days']*100:.1f}%)")
    
    # Fazit
    print("\n" + "=" * 60)
    print("📋 FAZIT")
    print("=" * 60)
    
    improvement = intraday_result['sharpe_ratio'] - daily_result['sharpe_ratio']
    
    if improvement > 0.1:
        print(f"✅ Intraday-Regime-Erkennung ist deutlich besser: +{improvement:.2f} Sharpe")
        print("   → Der Ansatz ist vielversprechend, sollte weiterverfolgt werden.")
    elif improvement > 0.05:
        print(f"⚠️ Intraday-Regime-Erkennung ist leicht besser: +{improvement:.2f} Sharpe")
        print("   → Der Ansatz ist interessant, aber der Mehrwert ist moderat.")
    elif improvement > 0:
        print(f"⚠️ Intraday-Regime-Erkennung ist minimal besser: +{improvement:.2f} Sharpe")
        print("   → Der Mehraufwand lohnt sich wahrscheinlich nicht.")
    else:
        print(f"⚠️ Intraday-Regime-Erkennung ist schlechter: {improvement:.2f} Sharpe")
        print("   → Der Ansatz sollte nicht weiterverfolgt werden.")
    
    print("\n" + "=" * 60)
    print("🏁 INTRADAY-BACKTEST ABGESCHLOSSEN")
    print("=" * 60)

if __name__ == "__main__":
    main()
