"""
test_breadth_distribution.py – Test Breadth & Distribution Days für 2022er-Lücke
================================================================================

Dieses Skript testet, ob Advance-Decline-Linie und Distribution Days die
2022er-Fehlklassifikationen von classify_regime_v2() beheben können.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import yfinance as yf
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# 1. Daten laden
# =============================================================================

def load_data():
    print("📊 Lade Daten...")
    
    # 1. S&P 500 Daten
    sp500 = yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    
    # 2. Advance-Decline-Linie (NYA als Proxy)
    try:
        nya = yf.download('^NYA', start='2011-01-01', end='2026-08-28', progress=False)
        ad_line = nya['Close']  # NYA als Proxy für Marktbreite
        print("   ✅ Advance-Decline-Daten (NYA) geladen")
    except Exception as e:
        print(f"   ⚠️ NYA nicht verfügbar, verwende S&P 500 als Proxy")
        ad_line = sp500['Close']
    
    # 3. VIX-Daten
    vix = pd.read_csv(DATA_DIR / "VIX_History.csv", parse_dates=['DATE'])
    vix = vix.set_index('DATE').sort_index()
    vix = vix['CLOSE']
    
    # 4. VIX3M-Daten
    vix3m = pd.read_csv(DATA_DIR / "VIX3M_History.csv", parse_dates=['DATE'])
    vix3m = vix3m.set_index('DATE').sort_index()
    vix3m = vix3m['CLOSE']
    
    # 5. GEX-Daten
    gex = pd.read_csv(DATA_DIR / "DIX.csv", parse_dates=['date'])
    gex = gex.set_index('date').sort_index()
    gex = gex['GEX'] if 'GEX' in gex.columns else gex['gex']
    
    # 6. Zusammenführen
    df = pd.DataFrame(index=sp500.index)
    df['returns'] = returns
    df['vix'] = vix.reindex(df.index, method='ffill')
    df['vix3m'] = vix3m.reindex(df.index, method='ffill')
    df['gex'] = gex.reindex(df.index, method='ffill')
    df['ad_line'] = ad_line.reindex(df.index, method='ffill')
    
    # 7. Distribution Days berechnen
    df['distribution_day'] = 0
    # Definition: Tag mit -1% oder mehr und Volumen > 50-Tage-Durchschnitt
    df['volume'] = sp500['Volume'] if 'Volume' in sp500.columns else pd.Series(0, index=sp500.index)
    df['volume_ma50'] = df['volume'].rolling(50).mean()
    df['distribution_day'] = ((df['returns'] < -0.01) & (df['volume'] > df['volume_ma50'])).astype(int)
    df['distribution_days_5'] = df['distribution_day'].rolling(5).sum()  # 5-Tage-Summe
    
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
# 3. Erweiterte Logik (mit Breadth + Distribution Days)
# =============================================================================

def classify_regime_v3(vix, vix3m, gex, ad_line, distribution_days,
                       ad_threshold=0.95, dd_threshold=3):
    """
    Erweiterte Logik: Breadth-Override + Distribution Days-Override.
    """
    # 1. Original-Logik
    regime = classify_regime_v2(vix, vix3m, gex)
    
    # 2. Nur bei NEUTRAL: Prüfen, ob Stress vorliegt
    if regime == "NEUTRAL":
        # AD-Linie: Wenn unter 95% des 20-Tage-Hochs
        ad_high_20 = ad_line.rolling(20).max()
        if len(ad_high_20) > 0 and ad_line.iloc[-1] < ad_high_20.iloc[-1] * ad_threshold:
            return "STRESS_UNSTABLE"
        
        # Distribution Days: Wenn 3+ in den letzten 5 Tagen
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
    
    for i in range(len(df)):
        row = df.iloc[i]
        # Regime bestimmen
        if kwargs:
            regime = regime_func(row['vix'], row['vix3m'], row['gex'], 
                                row['ad_line'], row['distribution_days_5'])
        else:
            regime = regime_func(row['vix'], row['vix3m'], row['gex'])
        signals.iloc[i, 0] = regime
        # Position: 0% bei STRESS_UNSTABLE, sonst 100%
        signals.iloc[i, 1] = 0.0 if regime == "STRESS_UNSTABLE" else 1.0
    
    # Performance
    positions = signals['position'].shift(1).fillna(0)
    strategy_returns = positions * df['returns']
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    strategy_cum = (1 + strategy_returns).cumprod()
    total_return = float(strategy_cum.iloc[-1] - 1)
    
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

def analyze_2022_miss(df, v2_signals, v3_signals):
    """Analysiert die 2022er-Fehlklassifikationen."""
    print("\n" + "=" * 60)
    print("📊 ANALYSE DER 2022ER-FEHLKLASSIFIKATIONEN")
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
            print(f"   AD-Linie: {row['ad_line']:.0f}")
            print(f"   Distribution Days (5d): {int(row['distribution_days_5'])}")
            print(f"   V2-Regime: {v2_regime}")
            print(f"   V3-Regime: {v3_regime}")

# =============================================================================
# 6. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 60)
    print("📈 TESTE BREADTH & DISTRIBUTION DAYS")
    print("=" * 60)
    
    # Daten laden
    df = load_data()
    
    # 1. V2 Backtest
    print("\n🔧 Führe V2-Backtest durch...")
    v2_result = backtest_strategy(df, classify_regime_v2, "V2")
    
    # 2. V3 Backtest
    print("🔧 Führe V3-Backtest durch (Breadth + Distribution Days)...")
    v3_result = backtest_strategy(df, classify_regime_v3, "V3")
    
    # 3. Ergebnisse vergleichen
    print("\n" + "=" * 60)
    print("📊 VERGLEICH V2 vs. V3")
    print("=" * 60)
    
    print(f"\n{'Kennzahl':<20} | {'V2':<15} | {'V3 (Breadth+DD)':<20}")
    print("-" * 60)
    print(f"{'Sharpe Ratio':<20} | {v2_result['sharpe_ratio']:>14.2f} | {v3_result['sharpe_ratio']:>19.2f}")
    print(f"{'Gesamtrendite':<20} | {v2_result['total_return']:>14.2%} | {v3_result['total_return']:>19.2%}")
    
    print(f"\n📊 Regime-Verteilung V2:")
    for regime, count in v2_result['regime_counts'].items():
        print(f"   {regime}: {count} ({count/len(df)*100:.1f}%)")
    
    print(f"\n📊 Regime-Verteilung V3:")
    for regime, count in v3_result['regime_counts'].items():
        print(f"   {regime}: {count} ({count/len(df)*100:.1f}%)")
    
    # 4. Analyse der 2022er-Fehltage
    analyze_2022_miss(df, v2_result['signals'], v3_result['signals'])
    
    print("\n" + "=" * 60)
    print("🏁 TEST ABGESCHLOSSEN")
    print("=" * 60)

if __name__ == "__main__":
    main()
