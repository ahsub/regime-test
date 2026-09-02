"""
intraday_backtest.py – Intraday-Backtest
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def calculate_performance(df: pd.DataFrame, price_col: str = 'SPY') -> dict:
    """Berechnet Performance-Kennzahlen."""
    df = df.copy()
    df = df.dropna(subset=[price_col, 'position'])
    
    if len(df) < 10:
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'trades': 0,
            'avg_position': 0,
            'n_days': len(df)
        }
    
    df['returns'] = df[price_col].pct_change()
    df['strategy_returns'] = df['position'].shift(1) * df['returns']
    df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
    
    total_return = df['cumulative_returns'].iloc[-1] - 1
    
    if df['strategy_returns'].std() > 0:
        sharpe = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252 * 6.5)
    else:
        sharpe = 0
    
    df['cummax'] = df['cumulative_returns'].cummax()
    df['drawdown'] = df['cumulative_returns'] / df['cummax'] - 1
    max_drawdown = df['drawdown'].min()
    
    df['position_change'] = df['position'].diff().fillna(0)
    trades = (df['position_change'].abs() > 0.01).sum()
    
    results = {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'trades': trades,
        'avg_position': df['position'].mean(),
        'n_days': len(df)
    }
    
    return results

def plot_intraday_results(df: pd.DataFrame, price_col: str = 'SPY'):
    """Erstellt Visualisierungen."""
    df = df.copy()
    df = df.dropna(subset=[price_col, 'position'])
    
    if len(df) < 10:
        print("⚠️ Zu wenige Daten für Visualisierung")
        return
    
    df['returns'] = df[price_col].pct_change()
    df['strategy_returns'] = df['position'].shift(1) * df['returns']
    df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    ax1 = axes[0]
    ax1.plot(df.index, df[price_col], label='SPY Preis', color='blue', alpha=0.7)
    
    regime_colors = {
        'STRESS_UNSTABLE': 'red',
        'POST_PANIC_REVERSION': 'orange',
        'BULL_FRAGILE': 'yellow',
        'BULL_QUIET': 'green',
        'NEUTRAL': 'gray'
    }
    
    for regime, color in regime_colors.items():
        mask = df['regime'] == regime
        if mask.any():
            ax1.fill_between(df.index, df[price_col].min(), df[price_col].max(), 
                            where=mask, color=color, alpha=0.1, label=regime)
    
    ax1.set_ylabel('Preis')
    ax1.set_title('Intraday-Preis mit Regimen')
    ax1.legend(loc='upper left')
    
    ax2 = axes[1]
    ax2.plot(df.index, df['position'], label='Position', color='purple', linewidth=1)
    ax2.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax2.set_ylabel('Position (0-1)')
    ax2.set_title('Intraday-Position')
    ax2.legend(loc='upper left')
    ax2.set_ylim(-0.1, 1.1)
    
    ax3 = axes[2]
    ax3.plot(df.index, df['cumulative_returns'], label='Strategie', color='green')
    ax3.axhline(y=1, color='black', linestyle='--', alpha=0.5)
    ax3.set_ylabel('Kumulative Rendite')
    ax3.set_title('Intraday-Strategie Performance')
    ax3.legend(loc='upper left')
    
    plt.tight_layout()
    
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'intraday_results.png', dpi=150)
    print(f"📈 Visualisierung gespeichert: results/intraday_results.png")
    plt.close()

def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("📊 INTRADAY-BACKTEST")
    print("=" * 60)
    
    data_path = Path(__file__).parent / "data" / "intraday" / "intraday_regimes.csv"
    
    if not data_path.exists():
        print(f"❌ Daten nicht gefunden: {data_path}")
        print("   Führen Sie zuerst intraday_regime.py aus")
        return
    
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"📊 Daten geladen: {len(df)} Zeilen")
    
    df_clean = df.dropna(subset=['position'])
    print(f"   Zeilen mit Position: {len(df_clean)}")
    
    if len(df_clean) < 10:
        print("❌ Zu wenige Daten für Backtest")
        return
    
    results = calculate_performance(df_clean, price_col='SPY')
    
    print("\n" + "=" * 60)
    print("📊 ERGEBNISSE")
    print("=" * 60)
    print(f"   Gesamtrendite:       {results['total_return']*100:.2f}%")
    print(f"   Sharpe Ratio:        {results['sharpe_ratio']:.2f}")
    print(f"   Max. Drawdown:       {results['max_drawdown']*100:.2f}%")
    print(f"   Anzahl Trades:       {results['trades']}")
    print(f"   Durchschn. Position: {results['avg_position']*100:.1f}%")
    print(f"   Handelstage:         {results['n_days']}")
    
    plot_intraday_results(df_clean, price_col='SPY')
    
    results_path = Path(__file__).parent / "results" / "intraday_results.csv"
    pd.DataFrame([results]).to_csv(results_path, index=False)
    print(f"\n💾 Ergebnisse gespeichert: {results_path}")
    
    return results

if __name__ == "__main__":
    results = main()
