"""
ensemble_strategy.py – Ensemble-Strategie (VIX + HMM)
======================================================

Diese Strategie kombiniert die VIX-Strategie mit dem erweiterten HMM.
Sie investiert nur, wenn BEIDE Modelle ein "Bull"-Signal geben.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

HMM_BULL_THRESHOLD = 1.5
VIX_BULL_THRESHOLD = 0.50

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data():
    """Lädt die Signale beider Modelle."""
    print("📊 Lade Signale der Modelle...")
    
    vix_signals = pd.read_csv(OUTPUT_DIR / 'trading_signals.csv', index_col=0, parse_dates=True)
    hmm_labels = pd.read_csv(OUTPUT_DIR / 'rolling_hmm_enhanced_labels.csv', index_col=0, parse_dates=True)
    
    import yfinance as yf
    sp500 = yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    
    common_dates = vix_signals.index.intersection(hmm_labels.index).intersection(returns.index)
    vix_signals = vix_signals.loc[common_dates]
    hmm_labels = hmm_labels.loc[common_dates]
    returns = returns.loc[common_dates]
    
    print(f"   ✅ {len(common_dates)} gemeinsame Tage gefunden")
    return vix_signals, hmm_labels, returns

# =============================================================================
# 3. ENSEMBLE-SIGNALGENERIERUNG
# =============================================================================

def generate_ensemble_signals(vix_signals: pd.DataFrame, hmm_labels: pd.DataFrame) -> pd.DataFrame:
    """Generiert Ensemble-Signale."""
    print("\n🔧 Generiere Ensemble-Signale...")
    
    vix_bull = vix_signals['position'] > 0.7
    hmm_bull = hmm_labels['state'] == 2
    ensemble_bull = vix_bull & hmm_bull
    
    signals = pd.DataFrame(index=vix_signals.index)
    signals['position'] = ensemble_bull.astype(float)
    signals['vix_bull'] = vix_bull.astype(int)
    signals['hmm_bull'] = hmm_bull.astype(int)
    signals['ensemble_bull'] = ensemble_bull.astype(int)
    signals['regime'] = 'CASH'
    signals.loc[signals['ensemble_bull'] == 1, 'regime'] = 'ENSEMBLE_BULL'
    
    print(f"   ✅ Ensemble-Signale generiert")
    print(f"   📊 Tage investiert: {signals['position'].sum():.0f} ({signals['position'].mean()*100:.1f}%)")
    return signals

# =============================================================================
# 4. PERFORMANCE-BERECHNUNG (KORRIGIERT)
# =============================================================================

def calculate_performance(signals: pd.DataFrame, returns: pd.Series, name: str) -> dict:
    """Berechnet die Performance einer Strategie."""
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {'name': name, 'total_return_strategy': 0.0, 'total_return_market': 0.0,
                'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'num_trades': 0,
                'avg_position': 0.0, 'n_days': 0, 'strategy_cum': pd.Series(),
                'market_cum': pd.Series(), 'strategy_returns': pd.Series()}
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    
    # KORREKTUR: Sicherer Zugriff auf den letzten Wert
    def safe_last_value(series):
        if len(series) == 0:
            return 0.0
        val = series.iloc[-1]
        if isinstance(val, pd.Series):
            return float(val.iloc[0]) if len(val) > 0 else 0.0
        return float(val)
    
    return {
        'name': name,
        'total_return_strategy': safe_last_value(strategy_cum) - 1,
        'total_return_market': safe_last_value(market_cum) - 1,
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(drawdown.min()) if len(drawdown) > 0 else 0.0,
        'num_trades': int((positions != positions.shift(1)).sum()),
        'avg_position': float(positions.mean()) if len(positions) > 0 else 0.0,
        'n_days': len(positions),
        'strategy_cum': strategy_cum,
        'market_cum': market_cum,
        'strategy_returns': strategy_returns
    }

# =============================================================================
# 5. VISUALISIERUNG
# =============================================================================

def plot_comparison(vix_perf: dict, hmm_perf: dict, ensemble_perf: dict):
    """Vergleicht die drei Strategien."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    ax1 = axes[0, 0]
    if len(vix_perf['strategy_cum']) > 0:
        ax1.plot(vix_perf['strategy_cum'].index, vix_perf['strategy_cum'], 
                 label=f"VIX ({vix_perf['sharpe_ratio']:.2f})", color='blue', linewidth=1.5)
    if len(hmm_perf['strategy_cum']) > 0:
        ax1.plot(hmm_perf['strategy_cum'].index, hmm_perf['strategy_cum'], 
                 label=f"HMM ({hmm_perf['sharpe_ratio']:.2f})", color='green', linewidth=1.5)
    if len(ensemble_perf['strategy_cum']) > 0:
        ax1.plot(ensemble_perf['strategy_cum'].index, ensemble_perf['strategy_cum'], 
                 label=f"Ensemble ({ensemble_perf['sharpe_ratio']:.2f})", color='red', linewidth=2)
    if len(vix_perf['market_cum']) > 0:
        ax1.plot(vix_perf['market_cum'].index, vix_perf['market_cum'], 
                 label='Buy & Hold', color='grey', alpha=0.5, linestyle='--')
    ax1.set_title('Kumulierte Renditen', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[0, 1]
    names = ['VIX', 'HMM', 'Ensemble']
    sharpe_values = [vix_perf['sharpe_ratio'], hmm_perf['sharpe_ratio'], ensemble_perf['sharpe_ratio']]
    bars = ax2.bar(names, sharpe_values, color=['blue', 'green', 'red'], edgecolor='black')
    ax2.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='Schwelle 0.5')
    ax2.set_title('Sharpe Ratio Vergleich', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    for bar, val in zip(bars, sharpe_values):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
    
    ax3 = axes[1, 0]
    dd_values = [vix_perf['max_drawdown'] * -100, hmm_perf['max_drawdown'] * -100, ensemble_perf['max_drawdown'] * -100]
    bars = ax3.bar(names, dd_values, color=['blue', 'green', 'red'], edgecolor='black')
    ax3.set_title('Max. Drawdown (%)', fontsize=12)
    ax3.grid(True, alpha=0.3)
    for bar, val in zip(bars, dd_values):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    ax4 = axes[1, 1]
    if len(ensemble_perf['strategy_returns']) > 0:
        ax4.fill_between(ensemble_perf['strategy_returns'].index, 0, 
                         ensemble_perf['strategy_returns'], 
                         alpha=0.3, color='red', label='Ensemble Position')
    ax4.axhline(y=0.0, color='black', linestyle='-', alpha=0.3)
    ax4.set_title('Ensemble Positionsgrößen', fontsize=12)
    ax4.set_ylabel('Position')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'ensemble_comparison.png', dpi=150)
    plt.show()
    print(f"💾 Vergleichsgrafik gespeichert: {OUTPUT_DIR / 'ensemble_comparison.png'}")

# =============================================================================
# 6. REPORT
# =============================================================================

def print_comparison(vix_perf: dict, hmm_perf: dict, ensemble_perf: dict):
    """Gibt einen Vergleichsreport aus."""
    print("\n" + "=" * 70)
    print("📊 ENSEMBLE-VERGLEICH")
    print("=" * 70)
    
    print(f"\n{'Kennzahl':<25} {'VIX-Strategie':<18} {'HMM-Strategie':<18} {'Ensemble':<18}")
    print("-" * 79)
    print(f"{'Gesamtrendite':<25} {vix_perf['total_return_strategy']:>17.2%} {hmm_perf['total_return_strategy']:>17.2%} {ensemble_perf['total_return_strategy']:>17.2%}")
    print(f"{'Sharpe Ratio':<25} {vix_perf['sharpe_ratio']:>17.2f} {hmm_perf['sharpe_ratio']:>17.2f} {ensemble_perf['sharpe_ratio']:>17.2f}")
    print(f"{'Max. Drawdown':<25} {vix_perf['max_drawdown']:>17.2%} {hmm_perf['max_drawdown']:>17.2%} {ensemble_perf['max_drawdown']:>17.2%}")
    print(f"{'Anzahl Trades':<25} {vix_perf['num_trades']:>17} {hmm_perf['num_trades']:>17} {ensemble_perf['num_trades']:>17}")
    print(f"{'Ø Position':<25} {vix_perf['avg_position']:>17.1%} {hmm_perf['avg_position']:>17.1%} {ensemble_perf['avg_position']:>17.1%}")
    print(f"{'Tage':<25} {vix_perf['n_days']:>17} {hmm_perf['n_days']:>17} {ensemble_perf['n_days']:>17}")
    
    print("\n" + "=" * 70)
    print("📋 FAZIT")
    print("=" * 70)
    
    if ensemble_perf['sharpe_ratio'] > vix_perf['sharpe_ratio']:
        print(f"✅ Ensemble hat Sharpe Ratio verbessert: {vix_perf['sharpe_ratio']:.2f} → {ensemble_perf['sharpe_ratio']:.2f}")
    else:
        print(f"⚠️ Ensemble hat Sharpe Ratio nicht verbessert: {vix_perf['sharpe_ratio']:.2f} → {ensemble_perf['sharpe_ratio']:.2f}")
    
    if ensemble_perf['max_drawdown'] > vix_perf['max_drawdown']:
        print(f"✅ Drawdown reduziert: {vix_perf['max_drawdown']:.2%} → {ensemble_perf['max_drawdown']:.2%}")
    else:
        print(f"⚠️ Drawdown verschlechtert: {vix_perf['max_drawdown']:.2%} → {ensemble_perf['max_drawdown']:.2%}")

# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 70)
    print("📈 STARTE ENSEMBLE-STRATEGIE")
    print("=" * 70)
    
    vix_signals, hmm_labels, returns = load_data()
    ensemble_signals = generate_ensemble_signals(vix_signals, hmm_labels)
    
    print("\n📊 Berechne Performance...")
    
    vix_perf = calculate_performance(vix_signals, returns, "VIX")
    hmm_signals = pd.DataFrame(index=hmm_labels.index)
    hmm_signals['position'] = hmm_labels['state'].map({0: 0.0, 1: 0.5, 2: 1.0}).fillna(0.0)
    hmm_perf = calculate_performance(hmm_signals, returns, "HMM")
    ensemble_perf = calculate_performance(ensemble_signals, returns, "Ensemble")
    
    print("\n📊 Erstelle Vergleichsgrafik...")
    plot_comparison(vix_perf, hmm_perf, ensemble_perf)
    
    print_comparison(vix_perf, hmm_perf, ensemble_perf)
    
    ensemble_signals.to_csv(OUTPUT_DIR / 'ensemble_signals.csv')
    print(f"\n💾 Ensemble-Signale gespeichert: {OUTPUT_DIR / 'ensemble_signals.csv'}")
    
    print("\n" + "=" * 70)
    print("🏁 ENSEMBLE-STRATEGIE ABGESCHLOSSEN")
    print("=" * 70)

if __name__ == "__main__":
    main()
