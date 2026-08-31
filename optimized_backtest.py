"""
optimized_backtest.py – Backtest mit den optimierten Parametern
================================================================

Dieses Skript:
1. Lädt die S&P 500 Daten und Regime-Wahrscheinlichkeiten
2. Wendet die optimierten Parameter an (aus der Grafik)
3. Führt einen Backtest durch
4. Vergleicht die Performance mit der vorherigen Strategie
5. Zeigt die Verbesserung der Sharpe Ratio
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Optimierte Parameter (aus der Grafik: Rang 1)
OPTIMIZED_PARAMS = {
    'bull_quiet': 0.50,
    'stress': 0.60,
    'bull_fragile': 0.35,
    'reversion': 0.30,
    'confirmation_days': 5,
    'max_position': 1.0,
    'min_position': 0.0
}

# Vorherige Parameter (zum Vergleich)
PREVIOUS_PARAMS = {
    'bull_quiet': 0.55,
    'stress': 0.40,
    'bull_fragile': 0.45,
    'reversion': 0.35,
    'confirmation_days': 3,
    'max_position': 1.0,
    'min_position': 0.0
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
    
    # S&P 500-Renditen aus market_data.csv
    if 'SP500_returns' in market_df.columns:
        returns = market_df['SP500_returns'].dropna()
    else:
        # Fallback: S&P 500 von Yahoo Finance laden
        import yfinance as yf
        sp500 = yf.download('^GSPC', start=prob_df.index[0], end=prob_df.index[-1], progress=False)
        returns = sp500['Close'].pct_change().dropna()
    
    return prob_df, returns

# =============================================================================
# 3. SIGNALGENERIERUNG
# =============================================================================

def generate_signals(prob_df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Generiert Handelssignale basierend auf Regime-Wahrscheinlichkeiten.
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
            signals.loc[signals.index[i], 'position'] = params['max_position']
            signals.loc[signals.index[i], 'regime'] = 'BULL_QUIET'
            
        # Stress: Ausstieg
        elif stress.iloc[start_idx:i+1].mean() > params['stress']:
            signals.loc[signals.index[i], 'position'] = params['min_position']
            signals.loc[signals.index[i], 'regime'] = 'STRESS'
            
        # Reversion: Wiedereinstieg
        elif has_reversion and prob_df['POST_PANIC_REVERSION'].iloc[start_idx:i+1].mean() > params['reversion']:
            signals.loc[signals.index[i], 'position'] = params['max_position']
            signals.loc[signals.index[i], 'regime'] = 'POST_PANIC_REVERSION'
            
        # BULL_FRAGILE: Reduzierte Position
        elif has_bull_fragile and prob_df['BULL_FRAGILE'].iloc[start_idx:i+1].mean() > params['bull_fragile']:
            signals.loc[signals.index[i], 'position'] = 0.7
            signals.loc[signals.index[i], 'regime'] = 'BULL_FRAGILE'
            
        else:
            if i > 0:
                signals.loc[signals.index[i], 'position'] = signals.loc[signals.index[i-1], 'position']
                signals.loc[signals.index[i], 'regime'] = signals.loc[signals.index[i-1], 'regime']
    
    signals['position'] = signals['position'].clip(params['min_position'], params['max_position'])
    
    return signals

# =============================================================================
# 4. PERFORMANCE-BERECHNUNG
# =============================================================================

def calculate_performance(signals: pd.DataFrame, returns: pd.Series) -> dict:
    """
    Berechnet die Performance der Strategie.
    """
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return None
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    # Kumulierte Renditen
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    # Sharpe Ratio (annualisiert)
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    # Drawdown
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    max_drawdown = drawdown.min()
    
    # Aktivität
    num_trades = (signals_aligned['position'] != signals_aligned['position'].shift(1)).sum()
    avg_position = signals_aligned['position'].mean()
    
    return {
        'strategy_cum': strategy_cum,
        'market_cum': market_cum,
        'strategy_returns': strategy_returns,
        'total_return_strategy': strategy_cum.iloc[-1] - 1,
        'total_return_market': market_cum.iloc[-1] - 1,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'num_trades': num_trades,
        'avg_position': avg_position
    }

# =============================================================================
# 5. VISUALISIERUNGEN
# =============================================================================

def plot_comparison(perf_optimized: dict, perf_previous: dict, 
                    signals_optimized: pd.DataFrame, signals_previous: pd.DataFrame):
    """
    Vergleicht die Performance der optimierten vs. vorherigen Strategie.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Kumulierte Renditen
    ax1 = axes[0, 0]
    ax1.plot(perf_optimized['strategy_cum'].index, perf_optimized['strategy_cum'], 
             label='Optimierte Strategie', color='green', linewidth=2)
    ax1.plot(perf_previous['strategy_cum'].index, perf_previous['strategy_cum'], 
             label='Vorherige Strategie', color='blue', linewidth=1.5, alpha=0.7)
    ax1.plot(perf_optimized['market_cum'].index, perf_optimized['market_cum'], 
             label='S&P 500 (Buy&Hold)', color='grey', alpha=0.5, linestyle='--')
    ax1.set_title('Kumulierte Renditen', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Sharpe Ratio Vergleich
    ax2 = axes[0, 1]
    sharpe_values = [perf_previous['sharpe_ratio'], perf_optimized['sharpe_ratio']]
    bars = ax2.bar(['Vorherige', 'Optimiert'], sharpe_values, 
                   color=['blue', 'green'], edgecolor='black', linewidth=0.8)
    ax2.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Schwelle 0.5')
    ax2.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='Schwelle 1.0')
    ax2.set_title('Sharpe Ratio Vergleich', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    for bar, val in zip(bars, sharpe_values):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Drawdown
    ax3 = axes[1, 0]
    dd_values = [
        perf_previous['max_drawdown'] * -100,
        perf_optimized['max_drawdown'] * -100
    ]
    bars = ax3.bar(['Vorherige', 'Optimiert'], dd_values, 
                   color=['blue', 'green'], edgecolor='black', linewidth=0.8)
    ax3.set_title('Max. Drawdown (%)', fontsize=12)
    ax3.grid(True, alpha=0.3)
    for bar, val in zip(bars, dd_values):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 4. Positionsgrößen
    ax4 = axes[1, 1]
    common_dates = signals_previous.index.intersection(signals_optimized.index)
    if len(common_dates) > 0:
        ax4.plot(signals_previous.loc[common_dates].index, 
                 signals_previous.loc[common_dates]['position'], 
                 label='Vorherige', color='blue', alpha=0.7, linewidth=0.8)
        ax4.plot(signals_optimized.loc[common_dates].index, 
                 signals_optimized.loc[common_dates]['position'], 
                 label='Optimiert', color='green', alpha=0.7, linewidth=0.8)
    ax4.axhline(y=1.0, color='black', linestyle='--', alpha=0.3, label='100%')
    ax4.axhline(y=0.0, color='red', linestyle='--', alpha=0.3, label='0%')
    ax4.set_title('Positionsgrößen über die Zeit', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'optimized_comparison.png', dpi=150)
    plt.show()
    print(f"💾 Vergleichsgrafik gespeichert: {OUTPUT_DIR / 'optimized_comparison.png'}")

# =============================================================================
# 6. REPORT
# =============================================================================

def print_report(name: str, perf: dict, params: dict):
    """Gibt einen Performance-Report aus."""
    print(f"\n📊 {name}")
    print("-" * 40)
    print(f"   Gesamtrendite:    {perf['total_return_strategy']:.2%}")
    print(f"   Buy & Hold:       {perf['total_return_market']:.2%}")
    print(f"   Mehrrendite:      {perf['total_return_strategy'] - perf['total_return_market']:.2%}")
    print(f"   Sharpe Ratio:     {perf['sharpe_ratio']:.2f}")
    print(f"   Max. Drawdown:    {perf['max_drawdown']:.2%}")
    print(f"   Anzahl Trades:    {perf['num_trades']}")
    print(f"   Ø Position:       {perf['avg_position']:.1%}")
    print(f"\n   🔧 Parameter:")
    print(f"      BULL_QUIET:    {params['bull_quiet']:.2f}")
    print(f"      STRESS:        {params['stress']:.2f}")
    print(f"      BULL_FRAGILE:  {params['bull_fragile']:.2f}")
    print(f"      REVERSION:     {params['reversion']:.2f}")
    print(f"      Bestätigung:   {params['confirmation_days']} Tage")

# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion für den optimierten Backtest."""
    print("=" * 60)
    print("📈 STARTE OPTIMIERTEN BACKTEST")
    print("=" * 60)
    
    # Daten laden
    prob_df, returns = load_data()
    print(f"📊 Daten geladen: {len(prob_df)} Wahrscheinlichkeiten, {len(returns)} Renditen")
    
    # 1. Optimierte Strategie
    print("\n🔧 Führe optimierte Strategie aus...")
    signals_optimized = generate_signals(prob_df, OPTIMIZED_PARAMS)
    perf_optimized = calculate_performance(signals_optimized, returns)
    if perf_optimized is None:
        print("❌ Optimierte Strategie konnte nicht berechnet werden.")
        return
    
    # 2. Vorherige Strategie (zum Vergleich)
    print("🔧 Führe vorherige Strategie aus...")
    signals_previous = generate_signals(prob_df, PREVIOUS_PARAMS)
    perf_previous = calculate_performance(signals_previous, returns)
    if perf_previous is None:
        print("❌ Vorherige Strategie konnte nicht berechnet werden.")
        return
    
    # 3. Vergleichsgrafik
    print("\n📊 Erstelle Vergleichsgrafik...")
    plot_comparison(perf_optimized, perf_previous, signals_optimized, signals_previous)
    
    # 4. Reports
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE-VERGLEICH")
    print("=" * 60)
    
    print_report("OPTIMIERTE STRATEGIE", perf_optimized, OPTIMIZED_PARAMS)
    print_report("VORHERIGE STRATEGIE", perf_previous, PREVIOUS_PARAMS)
    
    # 5. Verbesserung
    improvement = perf_optimized['sharpe_ratio'] - perf_previous['sharpe_ratio']
    print(f"\n📈 Verbesserung der Sharpe Ratio: {improvement:+.2f}")
    if improvement > 0:
        print("   ✅ Die Optimierung hat die Sharpe Ratio verbessert!")
    else:
        print("   ⚠️ Die Optimierung hat die Sharpe Ratio nicht verbessert.")
    
    print("\n" + "=" * 60)
    print("🏁 OPTIMIERTER BACKTEST ABGESCHLOSSEN")
    print("=" * 60)


if __name__ == "__main__":
    main()
