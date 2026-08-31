"""
optimize_sensitive.py – Optimierung mit sensibleren Parametern
================================================================

Dieses Skript testet niedrigere Schwellwerte, um die Strategie
aktiver und reaktionsschneller zu machen.

Getestet werden:
- BULL_QUIET: 0.25 – 0.50 (bisher: 0.30 – 0.60)
- STRESS: 0.30 – 0.60 (bisher: 0.30 – 0.70)
- BULL_FRAGILE: 0.20 – 0.45 (bisher: 0.25 – 0.55)
- REVERSION: 0.15 – 0.40 (bisher: 0.20 – 0.50)
- Bestätigungstage: 1 – 3 (bisher: 1 – 5)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from pathlib import Path
from itertools import product
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Sensiblere Parameter-Bereiche
PARAM_GRID = {
    'bull_quiet': [0.25, 0.30, 0.35, 0.40, 0.45, 0.50],
    'stress': [0.30, 0.40, 0.50, 0.60],
    'bull_fragile': [0.20, 0.25, 0.30, 0.35, 0.40, 0.45],
    'reversion': [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
    'confirmation_days': [1, 2, 3]
}

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data():
    """Lädt die S&P 500 Regime-Wahrscheinlichkeiten und Renditen."""
    prob_file = OUTPUT_DIR / "sp500_regime_probabilities.csv"
    market_file = DATA_DIR / "market_data.csv"
    
    prob_df = pd.read_csv(prob_file, index_col=0, parse_dates=True)
    market_df = pd.read_csv(market_file, index_col=0, parse_dates=True)
    
    # S&P 500-Renditen
    if 'SP500_returns' in market_df.columns:
        returns = market_df['SP500_returns'].dropna()
    else:
        import yfinance as yf
        sp500 = yf.download('^GSPC', start=prob_df.index[0], end=prob_df.index[-1], progress=False)
        returns = sp500['Close'].pct_change().dropna()
    
    return prob_df, returns

# =============================================================================
# 3. SIGNALGENERIERUNG
# =============================================================================

def generate_signals(prob_df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Generiert Handelssignale mit den übergebenen Parametern."""
    stress = 1 - (prob_df['BULL_QUIET'] + prob_df['POST_PANIC_REVERSION'] + prob_df['BULL_FRAGILE'])
    stress = stress.clip(lower=0)
    
    signals = pd.DataFrame(index=prob_df.index)
    signals['position'] = 0.0
    
    conf = params['confirmation_days']
    
    for i in range(conf, len(signals)):
        start_idx = max(0, i - conf)
        
        if prob_df['BULL_QUIET'].iloc[start_idx:i+1].mean() > params['bull_quiet']:
            signals.loc[signals.index[i], 'position'] = 1.0
        elif stress.iloc[start_idx:i+1].mean() > params['stress']:
            signals.loc[signals.index[i], 'position'] = 0.0
        elif prob_df['POST_PANIC_REVERSION'].iloc[start_idx:i+1].mean() > params['reversion']:
            signals.loc[signals.index[i], 'position'] = 1.0
        elif prob_df['BULL_FRAGILE'].iloc[start_idx:i+1].mean() > params['bull_fragile']:
            signals.loc[signals.index[i], 'position'] = 0.7
        else:
            if i > 0:
                signals.loc[signals.index[i], 'position'] = signals.loc[signals.index[i-1], 'position']
    
    signals['position'] = signals['position'].clip(0.0, 1.0)
    return signals

# =============================================================================
# 4. PERFORMANCE-BERECHNUNG
# =============================================================================

def calculate_performance(signals: pd.DataFrame, returns: pd.Series) -> dict:
    """Berechnet die Performance."""
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {'sharpe_ratio': -np.inf, 'total_return': -np.inf}
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    return {
        'sharpe_ratio': sharpe,
        'total_return': (1 + strategy_returns).prod() - 1,
        'num_trades': (signals_aligned['position'] != signals_aligned['position'].shift(1)).sum(),
        'avg_position': signals_aligned['position'].mean()
    }

# =============================================================================
# 5. OPTIMIERUNG
# =============================================================================

def run_optimization(prob_df: pd.DataFrame, returns: pd.Series) -> pd.DataFrame:
    """Führt die Parameter-Optimierung durch."""
    print("=" * 60)
    print("🧠 STARTE SENSIBLE PARAMETER-OPTIMIERUNG")
    print("=" * 60)
    
    param_names = list(PARAM_GRID.keys())
    param_values = [PARAM_GRID[name] for name in param_names]
    combinations = list(product(*param_values))
    
    total = len(combinations)
    print(f"📊 Teste {total} Parameter-Kombinationen...")
    
    results = []
    for idx, combo in enumerate(combinations):
        params = dict(zip(param_names, combo))
        
        if idx % 100 == 0:
            print(f"   {idx+1}/{total} ...")
        
        signals = generate_signals(prob_df, params)
        perf = calculate_performance(signals, returns)
        
        results.append({
            **params,
            'sharpe_ratio': perf['sharpe_ratio'],
            'total_return': perf['total_return'],
            'num_trades': perf['num_trades'],
            'avg_position': perf['avg_position']
        })
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('sharpe_ratio', ascending=False)
    return results_df

# =============================================================================
# 6. SPEICHERUNG & REPORT
# =============================================================================

def save_and_report(results_df: pd.DataFrame):
    """Speichert die Ergebnisse und gibt einen Report aus."""
    best = results_df.iloc[0]
    
    # JSON speichern
    best_params = {
        'bull_quiet': float(best['bull_quiet']),
        'stress': float(best['stress']),
        'bull_fragile': float(best['bull_fragile']),
        'reversion': float(best['reversion']),
        'confirmation_days': int(best['confirmation_days'])
    }
    
    with open(OUTPUT_DIR / 'sensitive_best_params.json', 'w') as f:
        json.dump(best_params, f, indent=4)
    
    # CSV speichern
    results_df.to_csv(OUTPUT_DIR / 'sensitive_optimization_results.csv', index=False)
    
    # Report
    print("\n" + "=" * 60)
    print("🏆 BESTE PARAMETER-KOMBINATION (SENSIBEL)")
    print("=" * 60)
    print(f"\n📊 Sharpe Ratio:     {best['sharpe_ratio']:.2f}")
    print(f"📈 Gesamtrendite:    {best['total_return']:.2%}")
    print(f"\n🔧 Parameter:")
    print(f"   BULL_QUIET:       {best['bull_quiet']:.2f}")
    print(f"   STRESS:           {best['stress']:.2f}")
    print(f"   BULL_FRAGILE:     {best['bull_fragile']:.2f}")
    print(f"   REVERSION:        {best['reversion']:.2f}")
    print(f"   Bestätigungstage: {int(best['confirmation_days'])}")
    print(f"\n🔄 Aktivität:")
    print(f"   Anzahl Trades:    {int(best['num_trades'])}")
    print(f"   Ø Position:       {best['avg_position']:.1%}")
    
    print(f"\n💾 Gespeichert: {OUTPUT_DIR / 'sensitive_best_params.json'}")
    print(f"💾 Ergebnisse: {OUTPUT_DIR / 'sensitive_optimization_results.csv'}")

# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 60)
    print("📈 STARTE SENSIBLE OPTIMIERUNG")
    print("=" * 60)
    
    prob_df, returns = load_data()
    print(f"📊 Daten geladen: {len(prob_df)} Wahrscheinlichkeiten, {len(returns)} Renditen")
    
    results_df = run_optimization(prob_df, returns)
    save_and_report(results_df)
    
    print("\n" + "=" * 60)
    print("🏁 SENSIBLE OPTIMIERUNG ABGESCHLOSSEN")
    print("=" * 60)

if __name__ == "__main__":
    main()
