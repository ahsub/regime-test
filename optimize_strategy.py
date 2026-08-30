"""
optimize_strategy.py – Automatische Parameter-Optimierung für die Regime-Strategie
=================================================================================

Dieses Skript testet systematisch verschiedene Parameter-Kombinationen
und findet diejenige mit der besten Sharpe Ratio.

Getestet werden:
- BULL_QUIET-Schwelle: 0.30 – 0.60
- STRESS-Schwelle: 0.30 – 0.70
- BULL_FRAGILE-Schwelle: 0.25 – 0.55
- REVERSION-Schwelle: 0.20 – 0.50
- Bestätigungstage: 1 – 5
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
from itertools import product
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Parameter-Bereiche für die Optimierung
PARAM_GRID = {
    'bull_quiet': [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60],
    'stress': [0.30, 0.40, 0.50, 0.60, 0.70],
    'bull_fragile': [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55],
    'reversion': [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50],
    'confirmation_days': [1, 2, 3, 4, 5]
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
    
    # S&P 500-Renditen aus market_data.csv (wir haben sie dort gespeichert)
    # Falls nicht vorhanden, laden wir sie von Yahoo Finance
    if 'SP500_returns' in market_df.columns:
        returns = market_df['SP500_returns'].dropna()
    else:
        # Fallback: S&P 500 von Yahoo Finance laden
        import yfinance as yf
        sp500 = yf.download('^GSPC', start=prob_df.index[0], end=prob_df.index[-1], progress=False)
        returns = sp500['Close'].pct_change().dropna()
    
    return prob_df, returns

# =============================================================================
# 3. SIGNALGENERIERUNG & PERFORMANCE
# =============================================================================

def generate_signals_optimized(prob_df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Generiert Signale mit den übergebenen Parametern.
    """
    # Spalten identifizieren
    has_bull_quiet = 'BULL_QUIET' in prob_df.columns
    has_bull_fragile = 'BULL_FRAGILE' in prob_df.columns
    has_reversion = 'POST_PANIC_REVERSION' in prob_df.columns
    
    # STRESS aus den anderen berechnen
    stress = 1 - (prob_df['BULL_QUIET'] + prob_df['POST_PANIC_REVERSION'] + prob_df['BULL_FRAGILE'])
    stress = stress.clip(lower=0)
    
    signals = pd.DataFrame(index=prob_df.index)
    signals['position'] = 0.0
    signals['regime'] = 'UNKNOWN'
    
    conf = params['confirmation_days']
    
    for i in range(conf, len(signals)):
        start_idx = max(0, i - conf)
        
        # BULL_QUIET: Voll investiert
        if has_bull_quiet and prob_df['BULL_QUIET'].iloc[start_idx:i+1].mean() > params['bull_quiet']:
            signals.loc[signals.index[i], 'position'] = 1.0
            signals.loc[signals.index[i], 'regime'] = 'BULL_QUIET'
            
        # Stress: Ausstieg
        elif stress.iloc[start_idx:i+1].mean() > params['stress']:
            signals.loc[signals.index[i], 'position'] = 0.0
            signals.loc[signals.index[i], 'regime'] = 'STRESS'
            
        # Reversion: Wiedereinstieg
        elif has_reversion and prob_df['POST_PANIC_REVERSION'].iloc[start_idx:i+1].mean() > params['reversion']:
            signals.loc[signals.index[i], 'position'] = 1.0
            signals.loc[signals.index[i], 'regime'] = 'POST_PANIC_REVERSION'
            
        # BULL_FRAGILE: Reduzierte Position
        elif has_bull_fragile and prob_df['BULL_FRAGILE'].iloc[start_idx:i+1].mean() > params['bull_fragile']:
            signals.loc[signals.index[i], 'position'] = 0.7
            signals.loc[signals.index[i], 'regime'] = 'BULL_FRAGILE'
            
        else:
            if i > 0:
                signals.loc[signals.index[i], 'position'] = signals.loc[signals.index[i-1], 'position']
                signals.loc[signals.index[i], 'regime'] = signals.loc[signals.index[i-1], 'regime']
    
    signals['position'] = signals['position'].clip(0.0, 1.0)
    
    return signals


def calculate_performance_optimized(signals: pd.DataFrame, returns: pd.Series) -> dict:
    """
    Berechnet die Performance für gegebene Signale.
    """
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {'sharpe_ratio': -np.inf, 'total_return': -np.inf}
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    # Sharpe Ratio
    excess_returns = strategy_returns - 0.02/252
    if np.std(excess_returns) > 0:
        sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)
    else:
        sharpe = 0.0
    
    # Gesamtrendite
    total_return = (1 + strategy_returns).prod() - 1
    
    return {
        'sharpe_ratio': sharpe,
        'total_return': total_return,
        'num_trades': (signals_aligned['position'] != signals_aligned['position'].shift(1)).sum(),
        'avg_position': signals_aligned['position'].mean(),
        'strategy_returns': strategy_returns
    }

# =============================================================================
# 4. OPTIMIERUNG
# =============================================================================

def run_optimization(prob_df: pd.DataFrame, returns: pd.Series) -> pd.DataFrame:
    """
    Führt die Parameter-Optimierung durch.
    """
    print("=" * 60)
    print("🧠 STARTE PARAMETER-OPTIMIERUNG")
    print("=" * 60)
    
    # Alle Parameter-Kombinationen generieren
    param_names = list(PARAM_GRID.keys())
    param_values = [PARAM_GRID[name] for name in param_names]
    combinations = list(product(*param_values))
    
    total = len(combinations)
    print(f"📊 Teste {total} Parameter-Kombinationen...")
    
    results = []
    
    for idx, combo in enumerate(combinations):
        params = dict(zip(param_names, combo))
        
        # Fortschritt anzeigen
        if idx % 50 == 0:
            print(f"   {idx+1}/{total} ...")
        
        # Signale generieren
        signals = generate_signals_optimized(prob_df, params)
        
        # Performance berechnen
        perf = calculate_performance_optimized(signals, returns)
        
        # Ergebnisse speichern
        results.append({
            **params,
            'sharpe_ratio': perf['sharpe_ratio'],
            'total_return': perf['total_return'],
            'num_trades': perf['num_trades'],
            'avg_position': perf['avg_position']
        })
    
    # Ergebnisse als DataFrame
    results_df = pd.DataFrame(results)
    
    # Nach Sharpe Ratio sortieren
    results_df = results_df.sort_values('sharpe_ratio', ascending=False)
    
    return results_df

# =============================================================================
# 5. VISUALISIERUNGEN
# =============================================================================

def plot_optimization_results(results_df: pd.DataFrame):
    """
    Visualisiert die Optimierungsergebnisse.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Sharpe Ratio Verteilung
    ax1 = axes[0, 0]
    sharpe_values = results_df['sharpe_ratio'][results_df['sharpe_ratio'] > -np.inf]
    ax1.hist(sharpe_values, bins=30, color='blue', alpha=0.7, edgecolor='black')
    ax1.axvline(x=0.5, color='red', linestyle='--', label='Schwelle 0.5')
    ax1.axvline(x=1.0, color='orange', linestyle='--', label='Schwelle 1.0')
    ax1.set_title('Sharpe Ratio Verteilung')
    ax1.set_xlabel('Sharpe Ratio')
    ax1.set_ylabel('Häufigkeit')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Top 10 Parameter
    ax2 = axes[0, 1]
    top10 = results_df.head(10)
    ax2.barh(range(len(top10)), top10['sharpe_ratio'], color='green', alpha=0.7)
    ax2.set_yticks(range(len(top10)))
    ax2.set_yticklabels([f"BQ={row['bull_quiet']:.2f}, S={row['stress']:.2f}, BF={row['bull_fragile']:.2f}, R={row['reversion']:.2f}, C={row['confirmation_days']}" 
                         for _, row in top10.iterrows()], fontsize=8)
    ax2.set_title('Top 10 Parameter-Kombinationen')
    ax2.set_xlabel('Sharpe Ratio')
    ax2.grid(True, alpha=0.3)
    
    # 3. Einfluss der Parameter
    ax3 = axes[1, 0]
    # Mittelwert der Sharpe Ratio pro Parameter-Wert
    for param in ['bull_quiet', 'stress', 'bull_fragile', 'reversion']:
        means = results_df.groupby(param)['sharpe_ratio'].mean()
        ax3.plot(means.index, means.values, marker='o', label=param)
    ax3.set_title('Einfluss der Parameter auf die Sharpe Ratio')
    ax3.set_xlabel('Parameter-Wert')
    ax3.set_ylabel('Durchschnittliche Sharpe Ratio')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Bestätigungstage
    ax4 = axes[1, 1]
    conf_means = results_df.groupby('confirmation_days')['sharpe_ratio'].mean()
    ax4.bar(conf_means.index, conf_means.values, color='purple', alpha=0.7)
    ax4.set_title('Einfluss der Bestätigungstage')
    ax4.set_xlabel('Bestätigungstage')
    ax4.set_ylabel('Durchschnittliche Sharpe Ratio')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'optimization_results.png', dpi=150)
    plt.show()
    print(f"💾 Optimierungsgrafik gespeichert: {OUTPUT_DIR / 'optimization_results.png'}")


def print_best_params(results_df: pd.DataFrame):
    """
    Gibt die besten Parameter aus.
    """
    best = results_df.iloc[0]
    
    # Hilfsfunktion: Extrahiert einen einzelnen Wert
    def safe_value(value):
        if isinstance(value, pd.Series):
            return value.iloc[0] if len(value) > 0 else 0.0
        return value
    
    # Werte sicher extrahieren
    sharpe = safe_value(best['sharpe_ratio'])
    total_return = safe_value(best['total_return'])
    bull_quiet = safe_value(best['bull_quiet'])
    stress = safe_value(best['stress'])
    bull_fragile = safe_value(best['bull_fragile'])
    reversion = safe_value(best['reversion'])
    conf_days = safe_value(best['confirmation_days'])
    num_trades = safe_value(best['num_trades'])
    avg_position = safe_value(best['avg_position'])
    
    print("\n" + "=" * 60)
    print("🏆 BESTE PARAMETER-KOMBINATION")
    print("=" * 60)
    print(f"\n📊 Sharpe Ratio:     {sharpe:.2f}")
    print(f"📈 Gesamtrendite:    {total_return:.2%}")
    print(f"\n🔧 Parameter:")
    print(f"   BULL_QUIET:       {bull_quiet:.2f}")
    print(f"   STRESS:           {stress:.2f}")
    print(f"   BULL_FRAGILE:     {bull_fragile:.2f}")
    print(f"   REVERSION:        {reversion:.2f}")
    print(f"   Bestätigungstage: {int(conf_days)}")
    print(f"\n🔄 Aktivität:")
    print(f"   Anzahl Trades:    {int(num_trades)}")
    print(f"   Ø Position:       {avg_position:.1%}")
    
    # Speichern der besten Parameter
    best_params = {
        'bull_quiet': float(bull_quiet),
        'stress': float(stress),
        'bull_fragile': float(bull_fragile),
        'reversion': float(reversion),
        'confirmation_days': int(conf_days)
    }
    
    # In Datei speichern
    import json
    with open(OUTPUT_DIR / 'best_params.json', 'w') as f:
        json.dump(best_params, f, indent=4)
    print(f"\n💾 Beste Parameter gespeichert: {OUTPUT_DIR / 'best_params.json'}")
    
    return best_params

# =============================================================================
# 6. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion für die Optimierung."""
    print("=" * 60)
    print("🧠 STARTE STRATEGIE-OPTIMIERUNG")
    print("=" * 60)
    
    # Daten laden
    prob_df, returns = load_data()
    print(f"📊 Daten geladen: {len(prob_df)} Wahrscheinlichkeiten, {len(returns)} Renditen")
    
    # Optimierung durchführen
    results_df = run_optimization(prob_df, returns)
    
    # Ergebnisse visualisieren
    plot_optimization_results(results_df)
    
    # Beste Parameter anzeigen
    best_params = print_best_params(results_df)
    
    # Ergebnisse speichern
    results_df.to_csv(OUTPUT_DIR / 'optimization_results.csv')
    print(f"\n💾 Alle Ergebnisse gespeichert: {OUTPUT_DIR / 'optimization_results.csv'}")
    
    print("\n" + "=" * 60)
    print("🏁 OPTIMIERUNG ABGESCHLOSSEN")
    print("=" * 60)
    print("💡 Nächster Schritt: Die besten Parameter können in der Hauptstrategie verwendet werden.")


if __name__ == "__main__":
    main()
