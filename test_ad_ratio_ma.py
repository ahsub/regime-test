"""
test_ad_ratio_ma.py – Test AD-Ratio mit gleitendem Durchschnitt
=================================================================

Dieses Skript testet die AD-Ratio mit gleitenden Durchschnitten (3/5 Tage)
als Override für classify_regime_v2().
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import yfinance as yf
import inspect
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# 1. Daten laden
# =============================================================================

def load_market_returns():
    """
    Lädt S&P 500 Renditen mit automatischem Fallback.
    Versucht: ^GSPC → SPY → ^SPX
    """
    tickers = ['^GSPC', 'SPY', '^SPX']
    for ticker in tickers:
        try:
            data = yf.download(ticker, start='2011-01-01', end='2026-08-28', progress=False)
            if len(data) > 0:
                print(f"   ✅ {ticker} geladen (als Proxy für S&P 500)")
                return data['Close'].pct_change()
        except Exception as e:
            print(f"   ⚠️ {ticker} fehlgeschlagen: {e}")
            continue
    
    # Fallback: VIX-Renditen (warnen)
    print("   ⚠️ KEIN S&P 500-Ticker verfügbar! Verwende VIX-Renditen als Proxy.")
    vix = pd.read_csv(DATA_DIR / "VIX_History.csv", parse_dates=['DATE'])
    vix = vix.set_index('DATE').sort_index()
    return vix['CLOSE'].pct_change()

def load_data():
    print("📊 Lade Daten...")
    
    # 1. S&P 500 Renditen (mit Fallback)
    returns = load_market_returns()
    
    # 2. Advance-Decline (NYA) – weiterhin von yfinance
    try:
        nya = yf.download('^NYA', start='2011-01-01', end='2026-08-28', progress=False)
        ad_line = nya['Close']
        print("   ✅ NYA-Daten geladen")
    except Exception as e:
        print(f"   ⚠️ NYA nicht verfügbar, überspringe AD-Ratio")
        # Dummy-Index für Alignierung
        ad_line = pd.Series(index=returns.index, data=np.nan)
    
    ad_ratio = ad_line.pct_change()
    
    # 3. VIX
    vix = pd.read_csv(DATA_DIR / "VIX_History.csv", parse_dates=['DATE'])
    vix = vix.set_index('DATE').sort_index()
    vix = vix['CLOSE']
    
    # 4. VIX3M
    vix3m = pd.read_csv(DATA_DIR / "VIX3M_History.csv", parse_dates=['DATE'])
    vix3m = vix3m.set_index('DATE').sort_index()
    vix3m = vix3m['CLOSE']
    
    # 5. GEX
    gex = pd.read_csv(DATA_DIR / "DIX.csv", parse_dates=['date'])
    gex = gex.set_index('date').sort_index()
    gex = gex['GEX'] if 'GEX' in gex.columns else gex['gex']
    
    # 6. Zusammenführen
    df = pd.DataFrame(index=returns.index)
    df['returns'] = returns
    df['vix'] = vix.reindex(df.index, method='ffill')
    df['vix3m'] = vix3m.reindex(df.index, method='ffill')
    df['gex'] = gex.reindex(df.index, method='ffill')
    df['ad_ratio'] = ad_ratio.reindex(df.index, method='ffill')
    df['ad_ratio_ma3'] = df['ad_ratio'].rolling(3).mean()
    df['ad_ratio_ma5'] = df['ad_ratio'].rolling(5).mean()
    
    # 7. Distribution Days (vereinfacht ohne Volumen)
    df['distribution_day'] = (df['returns'] < -0.01).astype(int)
    df['distribution_days_5'] = df['distribution_day'].rolling(5).sum()
    
    df = df.dropna()
    print(f"   ✅ {len(df)} Tage geladen ({df.index[0].date()} bis {df.index[-1].date()})")
    
    return df

# =============================================================================
# 2. classify_regime_v2() (Original)
# =============================================================================

def classify_regime_v2(vix, vix3m, gex):
    if vix is None or vix3m is None or vix <= 0:
        return "NEUTRAL"
    ratio = round(vix3m / vix, 3)
    if ratio < 0.98:
        return "STRESS_UNSTABLE"
    elif ratio < 1.05:
        return "POST_PANIC_REVERSION"
    else:
        regime = "BULL_FRAGILE" if vix > 25 else "BULL_QUIET"
        if gex is not None and gex < 0:
            return "STRESS_UNSTABLE"
        return regime

# =============================================================================
# 3. Erweiterte Logik mit AD-Ratio-MA
# =============================================================================

def classify_regime_v3_ma(vix, vix3m, gex, ad_ratio_ma, distribution_days,
                           ad_threshold=-0.01, dd_threshold=3):
    """
    Erweiterte Logik: AD-Ratio mit gleitendem Durchschnitt.
    """
    regime = classify_regime_v2(vix, vix3m, gex)
    
    if regime in ["NEUTRAL", "POST_PANIC_REVERSION"]:
        if ad_ratio_ma < ad_threshold:
            return "STRESS_UNSTABLE"
        if distribution_days >= dd_threshold:
            return "STRESS_UNSTABLE"
    
    return regime

# =============================================================================
# 4. Backtest-Funktion
# =============================================================================

def backtest_strategy(df, regime_func, name, **kwargs):
    """Führt einen Backtest für eine Regime-Funktion durch."""
    signals = pd.DataFrame(index=df.index)
    signals['regime'] = 'NEUTRAL'
    signals['position'] = 0.0
    
    if 'ma_window' in kwargs:
        ma_window = kwargs.get('ma_window')
        ad_col = f'ad_ratio_ma{ma_window}'
    else:
        ad_col = 'ad_ratio'
    
    sig = inspect.signature(regime_func)
    num_params = len(sig.parameters)
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        if num_params == 3:
            regime = regime_func(row['vix'], row['vix3m'], row['gex'])
        else:
            if ad_col in df.columns:
                call_kwargs = {k: v for k, v in kwargs.items() if k != 'ma_window'}
                regime = regime_func(
                    row['vix'], row['vix3m'], row['gex'],
                    row[ad_col], row['distribution_days_5'],
                    **call_kwargs
                )
            else:
                regime = regime_func(row['vix'], row['vix3m'], row['gex'])
        
        signals.iloc[i, 0] = regime
        signals.iloc[i, 1] = 0.0 if regime == "STRESS_UNSTABLE" else 1.0
    
    positions = signals['position'].shift(1).fillna(0)
    strategy_returns = positions * df['returns']
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    strategy_cum = (1 + strategy_returns).cumprod()
    total_return = float(strategy_cum.iloc[-1] - 1) if len(strategy_cum) > 0 else 0.0
    
    return {
        'name': name,
        'sharpe_ratio': float(sharpe),
        'total_return': total_return,
        'regime_counts': signals['regime'].value_counts().to_dict(),
        'signals': signals
    }

# =============================================================================
# 5. Analyse der 2022er-Fehltage
# =============================================================================

def analyze_2022_miss(df, v2_signals, v3_signals, label):
    """Analysiert die 2022er-Fehlklassifikationen."""
    print("\n" + "=" * 60)
    print(f"📊 ANALYSE DER 2022ER-FEHLKLASSIFIKATIONEN ({label})")
    print("=" * 60)
    
    miss_dates = ['2022-09-13', '2022-10-13']
    
    for date_str in miss_dates:
        date = pd.to_datetime(date_str)
        if date in df.index:
            row = df.loc[date]
            v2_regime = v2_signals.loc[date, 'regime']
            v3_regime = v3_signals.loc[date, 'regime'] if date in v3_signals.index else 'N/A'
            
            print(f"\n📅 {date_str}:")
            print(f"   VIX: {row['vix']:.1f} | VIX3M: {row['vix3m']:.1f} | GEX: {row['gex']:.0f}")
            print(f"   AD-Ratio (Tageswert): {row['ad_ratio']:.4f}")
            print(f"   AD-Ratio (MA3): {row['ad_ratio_ma3']:.4f}")
            print(f"   AD-Ratio (MA5): {row['ad_ratio_ma5']:.4f}")
            print(f"   Distribution Days (5d): {int(row['distribution_days_5'])}")
            print(f"   V2-Regime: {v2_regime}")
            print(f"   V3-Regime: {v3_regime}")

# =============================================================================
# 6. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 60)
    print("📈 TESTE AD-RATIO MIT GLEITENDEM DURCHSCHNITT")
    print("=" * 60)
    
    df = load_data()
    
    print("\n🔧 Führe V2-Backtest durch...")
    v2_result = backtest_strategy(df, classify_regime_v2, "V2")
    
    print("🔧 Führe V3-Backtest durch (AD-Ratio MA3, threshold=-0.01)...")
    v3_ma3_result = backtest_strategy(
        df, classify_regime_v3_ma, "V3 MA3",
        ma_window=3, ad_threshold=-0.01, dd_threshold=3
    )
    
    print("🔧 Führe V3-Backtest durch (AD-Ratio MA5, threshold=-0.01)...")
    v3_ma5_result = backtest_strategy(
        df, classify_regime_v3_ma, "V3 MA5",
        ma_window=5, ad_threshold=-0.01, dd_threshold=3
    )
    
    print("\n" + "=" * 60)
    print("📊 VERGLEICH V2 vs. V3 (AD-RATIO MA)")
    print("=" * 60)
    
    print(f"\n{'Kennzahl':<20} | {'V2':<15} | {'MA3':<15} | {'MA5':<15}")
    print("-" * 70)
    print(f"{'Sharpe Ratio':<20} | {v2_result['sharpe_ratio']:>14.2f} | {v3_ma3_result['sharpe_ratio']:>14.2f} | {v3_ma5_result['sharpe_ratio']:>14.2f}")
    print(f"{'Gesamtrendite':<20} | {v2_result['total_return']:>14.2%} | {v3_ma3_result['total_return']:>14.2%} | {v3_ma5_result['total_return']:>14.2%}")
    
    print(f"\n📊 Regime-Verteilung V2:")
    for regime, count in v2_result['regime_counts'].items():
        print(f"   {regime}: {count} ({count/len(df)*100:.1f}%)")
    
    print(f"\n📊 Regime-Verteilung V3 (MA3):")
    for regime, count in v3_ma3_result['regime_counts'].items():
        print(f"   {regime}: {count} ({count/len(df)*100:.1f}%)")
    
    print(f"\n📊 Regime-Verteilung V3 (MA5):")
    for regime, count in v3_ma5_result['regime_counts'].items():
        print(f"   {regime}: {count} ({count/len(df)*100:.1f}%)")
    
    analyze_2022_miss(df, v2_result['signals'], v3_ma3_result['signals'], "MA3")
    
    print("\n" + "=" * 60)
    print("🏁 TEST ABGESCHLOSSEN")
    print("=" * 60)

if __name__ == "__main__":
    main()
