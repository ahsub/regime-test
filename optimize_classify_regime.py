"""
optimize_classify_regime.py – Systematische Optimierung von classify_regime_v2()
================================================================================

Dieses Skript testet verschiedene Parameter-Kombinationen für Ihre
classify_regime_v2()-Logik, um die Sharpe Ratio zu maximieren.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import yfinance as yf
from itertools import product
import json
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# 1. Ihre classify_regime_v2() Logik (parametrisiert)
# =============================================================================

def classify_regime_v2_optimized(vix, vix3m, gex, 
                                 stress_threshold=0.98,
                                 reversion_threshold=1.05,
                                 vix_bull_fragile=25,
                                 gex_override=True):
    """
    Parametrisierte Version Ihrer classify_regime_v2().
    """
    if vix is None or vix3m is None or vix <= 0:
        return "NEUTRAL", None
    
    ratio = round(vix3m / vix, 3)
    
    if ratio < stress_threshold:
        regime = "STRESS_UNSTABLE"
    elif ratio < reversion_threshold:
        regime = "POST_PANIC_REVERSION"
    else:
        regime = "BULL_FRAGILE" if vix > vix_bull_fragile else "BULL_QUIET"
        if gex_override and gex is not None and gex < 0:
            regime = "STRESS_UNSTABLE"
    
    return regime, ratio

def regime_to_position_optimized(regime, pos_stress=0.0, pos_reversion=1.0, 
                                 pos_fragile=0.7, pos_quiet=1.0, pos_neutral=0.5):
    """
    Parametrisierte Positionslogik.
    """
    mapping = {
        "STRESS_UNSTABLE": pos_stress,
        "POST_PANIC_REVERSION": pos_reversion,
        "BULL_FRAGILE": pos_fragile,
        "BULL_QUIET": pos_quiet,
        "NEUTRAL": pos_neutral
    }
    return mapping.get(regime, 0.0)

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data():
    """Lädt die gleichen Daten wie der Vergleich."""
    print("📊 Lade Daten...")
    
    market_data = pd.read_csv(DATA_DIR / "market_data.csv", index_col=0, parse_dates=True)
    
    sp500 = yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    returns.index = pd.to_datetime(returns.index).tz_localize(None)
    if isinstance(returns, pd.DataFrame):
        returns = returns.squeeze()
    
    common_dates = market_data.index.intersection(returns.index)
    market_data = market_data.loc[common_dates]
    returns = returns.loc[common_dates]
    
    print(f"   ✅ {len(common_dates)} gemeinsame Tage gefunden")
    return market_data, returns

# =============================================================================
# 3. STRATEGIE-FUNKTION
# =============================================================================

def run_strategy(market_data, returns, params):
    """Führt die Strategie mit gegebenen Parametern aus."""
    signals = pd.DataFrame(index=market_data.index)
    signals['regime'] = 'NEUTRAL'
    signals['position'] = 0.0
    
    for i, row in market_data.iterrows():
        vix = row.get('VIX', None)
        vix3m = row.get('VIX3M', None)
        gex = row.get('GEX', None)
        
        regime, _ = classify_regime_v2_optimized(
            vix, vix3m, gex,
            stress_threshold=params['stress_threshold'],
            reversion_threshold=params['reversion_threshold'],
            vix_bull_fragile=params['vix_bull_fragile'],
            gex_override=params['gex_override']
        )
        signals.loc[i, 'regime'] = regime
        signals.loc[i, 'position'] = regime_to_position_optimized(
            regime,
            pos_stress=params['pos_stress'],
            pos_reversion=params['pos_reversion'],
            pos_fragile=params['pos_fragile'],
            pos_quiet=params['pos_quiet'],
            pos_neutral=params['pos_neutral']
        )
    
    # Performance berechnen
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    strategy_cum = (1 + strategy_returns).cumprod()
    last_val = strategy_cum.iloc[-1] if len(strategy_cum) > 0 else 1.0
if isinstance(last_val, pd.Series):
    last_val = last_val.iloc[0]
total_return = float(last_val - 1)
    
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    dd_min = drawdown.min()
    if isinstance(dd_min, pd.Series):
        dd_min = dd_min.iloc[0] if len(dd_min) > 0 else 0.0
    
    num_trades = int((positions != positions.shift(1)).sum())
    avg_position = float(positions.mean()) if len(positions) > 0 else 0.0
    
    return {
        'sharpe_ratio': float(sharpe),
        'total_return': total_return,
        'max_drawdown': float(dd_min) if dd_min is not None else 0.0,
        'num_trades': num_trades,
        'avg_position': avg_position,
        'n_days': len(positions)
    }

# =============================================================================
# 4. OPTIMIERUNG
# =============================================================================

def run_optimization(market_data, returns):
    """Führt die systematische Optimierung durch."""
    print("\n" + "=" * 60)
    print("🧠 STARTE SYSTEMATISCHE OPTIMIERUNG")
    print("=" * 60)
    
    # Parameter-Raster
    param_grid = {
        'stress_threshold': [0.90, 0.92, 0.94, 0.96, 0.98, 1.00],
        'reversion_threshold': [1.00, 1.02, 1.04, 1.06, 1.08, 1.10],
        'vix_bull_fragile': [15, 20, 25, 30, 35],
        'gex_override': [True, False],
        'pos_stress': [0.0, 0.1, 0.2],
        'pos_reversion': [0.8, 0.9, 1.0],
        'pos_fragile': [0.5, 0.6, 0.7, 0.8],
        'pos_quiet': [0.9, 1.0],
        'pos_neutral': [0.3, 0.5, 0.7]
    }
    
    # Kombinationen zählen
    total = 1
    for key, values in param_grid.items():
        total *= len(values)
    print(f"📊 Teste {total} Parameter-Kombinationen...")
    print(f"   ⚠️ Geschätzte Laufzeit: ~{total/1000:.1f} Minuten")
    
    # Grid durchlaufen
    results = []
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    
    for idx, combo in enumerate(product(*param_values)):
        params = dict(zip(param_names, combo))
        
        if idx % 50 == 0:
            print(f"   {idx+1}/{total} ...")
        
        perf = run_strategy(market_data, returns, params)
        results.append({
            **params,
            'sharpe_ratio': perf['sharpe_ratio'],
            'total_return': perf['total_return'],
            'max_drawdown': perf['max_drawdown'],
            'num_trades': perf['num_trades'],
            'avg_position': perf['avg_position']
        })
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('sharpe_ratio', ascending=False)
    
    return results_df

# =============================================================================
# 5. REPORT
# =============================================================================

def print_best_params(results_df):
    """Gibt die beste Parameter-Kombination aus."""
    best = results_df.iloc[0]
    
    print("\n" + "=" * 60)
    print("🏆 BESTE PARAMETER-KOMBINATION")
    print("=" * 60)
    
    print(f"\n📊 Sharpe Ratio:     {best['sharpe_ratio']:.2f}")
    print(f"📈 Gesamtrendite:    {best['total_return']:.2%}")
    print(f"📉 Max. Drawdown:    {best['max_drawdown']:.2%}")
    print(f"🔄 Anzahl Trades:    {int(best['num_trades'])}")
    print(f"📊 Ø Position:       {best['avg_position']:.1%}")
    
    print(f"\n🔧 Parameter:")
    print(f"   stress_threshold:     {best['stress_threshold']:.2f}")
    print(f"   reversion_threshold:  {best['reversion_threshold']:.2f}")
    print(f"   vix_bull_fragile:     {int(best['vix_bull_fragile'])}")
    print(f"   gex_override:         {best['gex_override']}")
    print(f"   pos_stress:           {best['pos_stress']:.1f}")
    print(f"   pos_reversion:        {best['pos_reversion']:.1f}")
    print(f"   pos_fragile:          {best['pos_fragile']:.1f}")
    print(f"   pos_quiet:            {best['pos_quiet']:.1f}")
    print(f"   pos_neutral:          {best['pos_neutral']:.1f}")
    
    # Vergleich mit Original
    print("\n" + "=" * 60)
    print("📊 VERGLEICH MIT ORIGINAL")
    print("=" * 60)
    
    original_params = {
        'stress_threshold': 0.98,
        'reversion_threshold': 1.05,
        'vix_bull_fragile': 25,
        'gex_override': True,
        'pos_stress': 0.0,
        'pos_reversion': 1.0,
        'pos_fragile': 0.7,
        'pos_quiet': 1.0,
        'pos_neutral': 0.5
    }
    
    # Original-Performance berechnen
    orig_perf = run_strategy(
        pd.read_csv(DATA_DIR / "market_data.csv", index_col=0, parse_dates=True),
        yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)['Close'].pct_change(),
        original_params
    )
    
    print(f"\n{'Kennzahl':<20} | {'Original':<15} | {'Optimiert':<15} | {'Veränderung':<12}")
    print("-" * 70)
    
    sr_change = (best['sharpe_ratio'] - orig_perf['sharpe_ratio']) / orig_perf['sharpe_ratio'] * 100 if orig_perf['sharpe_ratio'] > 0 else 0
    print(f"{'Sharpe Ratio':<20} | {orig_perf['sharpe_ratio']:>14.2f} | {best['sharpe_ratio']:>14.2f} | {sr_change:>+11.1f}%")
    
    ret_change = (best['total_return'] - orig_perf['total_return']) / orig_perf['total_return'] * 100 if orig_perf['total_return'] > 0 else 0
    print(f"{'Gesamtrendite':<20} | {orig_perf['total_return']:>14.2%} | {best['total_return']:>14.2%} | {ret_change:>+11.1f}%")
    
    dd_change = (best['max_drawdown'] - orig_perf['max_drawdown']) / abs(orig_perf['max_drawdown']) * 100 if orig_perf['max_drawdown'] < 0 else 0
    print(f"{'Drawdown':<20} | {orig_perf['max_drawdown']:>14.2%} | {best['max_drawdown']:>14.2%} | {dd_change:>+11.1f}%")
    
    # Speichern
    best_params = {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v) for k, v in best.items()}
    with open(OUTPUT_DIR / 'optimized_classify_regime_params.json', 'w') as f:
        json.dump(best_params, f, indent=4)
    print(f"\n💾 Beste Parameter gespeichert: {OUTPUT_DIR / 'optimized_classify_regime_params.json'}")
    
    return best_params

# =============================================================================
# 6. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE OPTIMIERUNG: classify_regime_v2()")
    print("=" * 80)
    
    market_data, returns = load_data()
    results_df = run_optimization(market_data, returns)
    
    # Ergebnisse speichern
    results_df.to_csv(OUTPUT_DIR / 'classify_regime_optimization_results.csv', index=False)
    print(f"\n💾 Alle Ergebnisse gespeichert: {OUTPUT_DIR / 'classify_regime_optimization_results.csv'}")
    
    # Beste Parameter anzeigen
    best_params = print_best_params(results_df)
    
    print("\n" + "=" * 80)
    print("🏁 OPTIMIERUNG ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
