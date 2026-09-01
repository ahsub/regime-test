"""
intraday_backtest_yf.py – Intraday-Backtest mit Yahoo Finance
==============================================================

Dieses Skript testet 60-Minuten-Daten für SPY und VIX (letzte 730 Tage)
mit Yahoo Finance.

Basierend auf Pagliaro (2026): Intraday-HMM kann Sharpe um 0,15–0,20 verbessern.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# 1. DATEN LADEN
# =============================================================================

def load_intraday_data():
    """Lädt 60-Minuten-Daten von Yahoo Finance."""
    print("📊 Lade Intraday-Daten (60-Minuten, letzte 730 Tage)...")
    
    # SPY 60-Minuten-Daten (letzte 730 Tage)
    spy_intraday = yf.download('SPY', interval='60m', period='2y', progress=False)
    if len(spy_intraday) == 0:
        print("❌ Keine Intraday-Daten für SPY verfügbar.")
        return None
    
    print(f"   ✅ SPY Intraday: {len(spy_intraday)} Bars")
    
    # VIX 60-Minuten-Daten (letzte 730 Tage)
    vix_intraday = yf.download('^VIX', interval='60m', period='2y', progress=False)
    if len(vix_intraday) > 0:
        print(f"   ✅ VIX Intraday: {len(vix_intraday)} Bars")
    else:
        print("   ⚠️ Keine Intraday-Daten für VIX verfügbar.")
        vix_intraday = None
    
    return spy_intraday, vix_intraday

def load_daily_data():
    """Lädt tägliche Daten für Vergleich."""
    print("📊 Lade tägliche Daten für Vergleich...")
    daily_spy = yf.download('SPY', start='2011-01-01', end='2026-08-28', progress=False)
    daily_returns = daily_spy['Close'].pct_change()
    print(f"   ✅ Tägliche SPY: {len(daily_spy)} Tage")
    return daily_returns

# =============================================================================
# 2. INTRADAY-REGIME-ERKENNUNG
# =============================================================================

def intraday_regime_signal(row):
    """
    Einfache Intraday-Regime-Logik (basierend auf VIX-Spread + Volatilität).
    """
    # VIX-Spread (vereinfacht: VIX-Spot gegen den gleitenden Durchschnitt)
    vix_spread = row.get('vix_spread', 1.0)
    volatility = row.get('volatility', 0.2)
    
    if vix_spread < 0.98:
        return "STRESS_UNSTABLE"
    elif vix_spread < 1.05:
        return "POST_PANIC_REVERSION"
    else:
        if volatility > 0.30:
            return "BULL_FRAGILE"
        else:
            return "BULL_QUIET"

def backtest_intraday(spy_df, vix_df=None):
    """Führt Backtest auf Intraday-Basis durch."""
    print("\n🔧 Berechne Intraday-Features...")
    
    # 1. Renditen
    spy_df['returns'] = spy_df['Close'].pct_change()
    
    # 2. 20-Perioden-Volatilität (20 Stunden ≈ 5 Tage)
    spy_df['volatility'] = spy_df['returns'].rolling(20).std() * np.sqrt(252 * 6.5)
    
    # 3. Intraday-VIX
    if vix_df is not None and len(vix_df) > 0:
        vix_aligned = vix_df['Close'].reindex(spy_df.index, method='ffill')
        spy_df['vix'] = vix_aligned
        spy_df['vix_ma20'] = spy_df['vix'].rolling(20).mean()
        spy_df['vix_spread'] = spy_df['vix'] / spy_df['vix_ma20']
    else:
        spy_df['vix'] = 20
        spy_df['vix_ma20'] = 20
        spy_df['vix_spread'] = 1.0
    
    spy_df = spy_df.dropna()
    print(f"   ✅ {len(spy_df)} Intraday-Bars mit Features")
    
    # 4. Signale generieren
    print("🔧 Generiere Intraday-Signale...")
    signals = pd.DataFrame(index=spy_df.index)
    signals['regime'] = spy_df.apply(intraday_regime_signal, axis=1)
    signals['position'] = 0.0
    signals.loc[signals['regime'] != 'STRESS_UNSTABLE', 'position'] = 1.0
    
    # 5. Performance berechnen
    positions = signals['position'].shift(1).fillna(0)
    strategy_returns = positions * spy_df['returns']
    
    excess_returns = strategy_returns - 0.02/252/6.5
    sharpe = np.sqrt(252 * 6.5) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    strategy_cum = (1 + strategy_returns).cumprod()
    total_return = float(strategy_cum.iloc[-1] - 1) if len(strategy_cum) > 0 else 0.0
    
    return {
        'sharpe_ratio': float(sharpe),
        'total_return': total_return,
        'regime_counts': signals['regime'].value_counts().to_dict(),
        'n_days': len(signals)
    }

def daily_backtest(returns):
    """Täglicher Backtest zum Vergleich."""
    print("\n🔧 Führe täglichen Backtest durch...")
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
# 3. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 60)
    print("📈 INTRADAY-BACKTEST (YAHOO FINANCE)")
    print("=" * 60)
    
    # Daten laden
    spy_intraday, vix_intraday = load_intraday_data()
    if spy_intraday is None:
        print("❌ Abbruch wegen fehlender Daten.")
        return
    
    daily_returns = load_daily_data()
    
    # Intraday-Backtest
    intraday_result = backtest_intraday(spy_intraday, vix_intraday)
    
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
