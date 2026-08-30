"""
sp500_regime.py – S&P 500-basiertes Regime-Modell
==================================================

Dieses Skript:
1. Lädt S&P 500-Daten von Yahoo Finance
2. Fittet ein Markov-Switching-Modell mit 3 Regimen
3. Generiert Handelssignale aus den Regime-Wahrscheinlichkeiten
4. Berechnet die Performance und vergleicht mit VIX-basierter Strategie
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Parameter
N_REGIMES = 3
START_DATE = "1990-01-01"
END_DATE = "2026-08-28"

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_sp500_data() -> pd.DataFrame:
    """Lädt S&P 500-Daten von Yahoo Finance."""
    print(f"📥 Lade S&P 500 Daten von {START_DATE} bis {END_DATE}...")
    df = yf.download('^GSPC', start=START_DATE, end=END_DATE, progress=False)
    print(f"   ✅ {len(df)} Tage geladen")
    return df

def load_vix_probabilities() -> pd.DataFrame:
    """Lädt die VIX-basierten Regime-Wahrscheinlichkeiten zum Vergleich."""
    filepath = DATA_DIR / "results" / "regime_probabilities.csv"
    if filepath.exists():
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        print(f"   ✅ VIX-Wahrscheinlichkeiten geladen: {len(df)} Zeilen")
        return df
    else:
        print(f"   ⚠️ VIX-Wahrscheinlichkeiten nicht gefunden")
        return None

# =============================================================================
# 3. REGIME-MODELL (S&P 500)
# =============================================================================

def fit_sp500_regime_model(returns: pd.Series, n_regimes: int = 3) -> object:
    """Fittet ein Markov-Switching-Modell auf S&P 500-Renditen."""
    print(f"\n🧠 Fitte Modell mit {n_regimes} Regimen...")
    mod = sm.tsa.MarkovRegression(
        endog=returns,
        k_regimes=n_regimes,
        trend='c',
        switching_variance=True,
        switching_trend=True
    )
    res = mod.fit()
    print(f"   ✅ AIC: {res.aic:.2f}, BIC: {res.bic:.2f}")
    return res

def interpret_sp500_regimes(res: object) -> pd.DataFrame:
    """Interpretiert die Regime basierend auf den Parametern."""
    n = res.k_regimes
    means = res.params.iloc[:n].values
    stds = np.sqrt(res.params.iloc[n:2*n].values)
    
    regime_data = []
    for i in range(n):
        regime_data.append({
            'regime': i,
            'mean': means[i],
            'std': stds[i],
            'label': f'Regime {i}'
        })
    
    # Sortieren nach Volatilität (niedrig zu hoch)
    sorted_regimes = sorted(regime_data, key=lambda x: x['std'])
    
    for idx, data in enumerate(sorted_regimes):
        if idx == 0 and data['mean'] > 0:
            data['label'] = 'BULL_QUIET'
        elif idx == 1 and data['mean'] > 0:
            data['label'] = 'BULL_FRAGILE'
        elif idx == 2 and data['mean'] < 0:
            data['label'] = 'STRESS_UNSTABLE'
        elif idx == 2 and data['mean'] > 0:
            data['label'] = 'POST_PANIC_REVERSION'
        else:
            data['label'] = f'REGIME_{idx}'
    
    df = pd.DataFrame(regime_data)
    print("\n📊 S&P 500 Regime-Interpretation:")
    print(df[['regime', 'label', 'mean', 'std']].round(4))
    return df

# =============================================================================
# 4. HANDELSSIGNALE
# =============================================================================

def generate_sp500_signals(prob_df: pd.DataFrame, 
                           thresholds: dict = None) -> pd.DataFrame:
    """Generiert Handelssignale basierend auf S&P 500 Regimen."""
    if thresholds is None:
        thresholds = {
            'bull_quiet': 0.55,
            'bull_fragile': 0.45,
            'stress': 0.40,
            'reversion': 0.35,
            'max_position': 1.0,
            'min_position': 0.0,
            'confirmation_days': 3
        }
    
    # Spalten identifizieren
    has_stress = 'STRESS_UNSTABLE' in prob_df.columns
    has_bull_quiet = 'BULL_QUIET' in prob_df.columns
    has_bull_fragile = 'BULL_FRAGILE' in prob_df.columns
    has_reversion = 'POST_PANIC_REVERSION' in prob_df.columns
    
    # Wenn kein STRESS_UNSTABLE, aus den anderen berechnen
    if not has_stress:
        stress = 1 - (prob_df['BULL_QUIET'] + prob_df['POST_PANIC_REVERSION'] + prob_df['BULL_FRAGILE'])
        stress = stress.clip(lower=0)
    else:
        stress = prob_df['STRESS_UNSTABLE']
    
    signals = pd.DataFrame(index=prob_df.index)
    signals['position'] = 0.0
    signals['regime'] = 'UNKNOWN'
    
    conf = thresholds['confirmation_days']
    
    for i in range(conf, len(signals)):
        start_idx = max(0, i - conf)
        
        # BULL_QUIET: Voll investiert
        if has_bull_quiet and prob_df['BULL_QUIET'].iloc[start_idx:i+1].mean() > thresholds['bull_quiet']:
            signals.loc[signals.index[i], 'position'] = thresholds['max_position']
            signals.loc[signals.index[i], 'regime'] = 'BULL_QUIET'
            
        # Stress: Ausstieg
        elif stress.iloc[start_idx:i+1].mean() > thresholds['stress']:
            signals.loc[signals.index[i], 'position'] = thresholds['min_position']
            signals.loc[signals.index[i], 'regime'] = 'STRESS'
            
        # Reversion: Wiedereinstieg
        elif has_reversion and prob_df['POST_PANIC_REVERSION'].iloc[start_idx:i+1].mean() > thresholds['reversion']:
            signals.loc[signals.index[i], 'position'] = thresholds['max_position'] * 1.2
            signals.loc[signals.index[i], 'regime'] = 'POST_PANIC_REVERSION'
            
        # BULL_FRAGILE: Reduzierte Position
        elif has_bull_fragile and prob_df['BULL_FRAGILE'].iloc[start_idx:i+1].mean() > thresholds['bull_fragile']:
            signals.loc[signals.index[i], 'position'] = 0.7
            signals.loc[signals.index[i], 'regime'] = 'BULL_FRAGILE'
            
        else:
            if i > 0:
                signals.loc[signals.index[i], 'position'] = signals.loc[signals.index[i-1], 'position']
                signals.loc[signals.index[i], 'regime'] = signals.loc[signals.index[i-1], 'regime']
    
    signals['position'] = signals['position'].clip(
        thresholds['min_position'], 
        thresholds['max_position'] * 1.2
    )
    
    return signals

# =============================================================================
# 5. PERFORMANCE-BERECHNUNG
# =============================================================================

def calculate_performance(signals: pd.DataFrame, 
                          returns: pd.Series) -> dict:
    """Berechnet die Performance der Strategie."""
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    total_return_strategy = strategy_cum.iloc[-1] - 1
    total_return_market = market_cum.iloc[-1] - 1
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    max_drawdown = drawdown.min()
    
    position_changes = (signals_aligned['position'] != signals_aligned['position'].shift(1)).sum()
    
    return {
        'strategy_cum': strategy_cum,
        'market_cum': market_cum,
        'strategy_returns': strategy_returns,
        'total_return_strategy': total_return_strategy,
        'total_return_market': total_return_market,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'num_trades': position_changes,
        'avg_position': signals_aligned['position'].mean()
    }

# =============================================================================
# 6. VISUALISIERUNGEN
# =============================================================================

def plot_comparison(vix_perf: dict, sp500_perf: dict, 
                    vix_signals: pd.DataFrame, sp500_signals: pd.DataFrame):
    """
    Professioneller Vergleich der VIX- und S&P 500-basierten Strategien.
    Mit sauberen Achsen, Legenden und optimierter Darstellung.
    """
    # Daten sicher extrahieren
    def safe_float(value):
        if isinstance(value, pd.Series):
            return float(value.iloc[0])
        return float(value)
    
    vix_sharpe = safe_float(vix_perf['sharpe_ratio'])
    sp500_sharpe = safe_float(sp500_perf['sharpe_ratio'])
    vix_dd = safe_float(vix_perf['max_drawdown']) * -100
    sp500_dd = safe_float(sp500_perf['max_drawdown']) * -100
    vix_return = safe_float(vix_perf['total_return_strategy']) * 100
    sp500_return = safe_float(sp500_perf['total_return_strategy']) * 100
    
    # Figure mit besserer Aufteilung
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # 1. Kumulierte Renditen (Hauptplot – größer)
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.plot(vix_perf['strategy_cum'].index, vix_perf['strategy_cum'], 
             label='VIX-Strategie', color='#1f77b4', linewidth=1.5)
    ax1.plot(sp500_perf['strategy_cum'].index, sp500_perf['strategy_cum'], 
             label='S&P 500-Strategie', color='#2ca02c', linewidth=1.5)
    ax1.plot(vix_perf['market_cum'].index, vix_perf['market_cum'], 
             label='VIX Buy&Hold', color='#1f77b4', linestyle='--', alpha=0.5, linewidth=1)
    ax1.plot(sp500_perf['market_cum'].index, sp500_perf['market_cum'], 
             label='S&P 500 Buy&Hold', color='#2ca02c', linestyle='--', alpha=0.5, linewidth=1)
    ax1.axhline(y=1.0, color='black', linestyle='-', alpha=0.2, linewidth=0.5)
    ax1.set_title('Kumulierte Renditen (logarithmische Skala)', fontsize=13)
    ax1.set_ylabel('Kumulative Rendite (log)')
    ax1.set_yscale('log')
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 2. Sharpe Ratio (Balken)
    ax2 = fig.add_subplot(gs[0, 2])
    bars = ax2.bar(['VIX', 'S&P 500'], [vix_sharpe, sp500_sharpe], 
                   color=['#1f77b4', '#2ca02c'], edgecolor='black', linewidth=0.8)
    ax2.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, linewidth=1.2, label='Schwelle 0.5')
    ax2.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, linewidth=1.2, label='Schwelle 1.0')
    ax2.set_title('Sharpe Ratio', fontsize=13)
    ax2.set_ylabel('Sharpe Ratio')
    ax2.set_ylim(0, max(1.5, max(vix_sharpe, sp500_sharpe) * 1.2))
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
    # Werte über Balken
    for bar, val in zip(bars, [vix_sharpe, sp500_sharpe]):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.03,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 3. Drawdown (Balken)
    ax3 = fig.add_subplot(gs[1, 0])
    bars = ax3.bar(['VIX', 'S&P 500'], [vix_dd, sp500_dd], 
                   color=['#1f77b4', '#2ca02c'], edgecolor='black', linewidth=0.8)
    ax3.set_title('Max. Drawdown (%)', fontsize=13)
    ax3.set_ylabel('Drawdown (%)')
    ax3.grid(True, alpha=0.3, axis='y', linestyle='--')
    for bar, val in zip(bars, [vix_dd, sp500_dd]):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 4. Gesamtrendite (Balken)
    ax4 = fig.add_subplot(gs[1, 1])
    bars = ax4.bar(['VIX', 'S&P 500'], [vix_return, sp500_return], 
                   color=['#1f77b4', '#2ca02c'], edgecolor='black', linewidth=0.8)
    ax4.set_title('Gesamtrendite (%)', fontsize=13)
    ax4.set_ylabel('Rendite (%)')
    ax4.grid(True, alpha=0.3, axis='y', linestyle='--')
    for bar, val in zip(bars, [vix_return, sp500_return]):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 5,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 5. Positionsgrößen (kleiner Plot)
    ax5 = fig.add_subplot(gs[1, 2])
    common_dates = vix_signals.index.intersection(sp500_signals.index)
    if len(common_dates) > 0:
        # Nur jeden 20. Tag anzeigen für bessere Lesbarkeit
        step = max(1, len(common_dates) // 200)
        dates_sample = common_dates[::step]
        ax5.plot(vix_signals.loc[dates_sample].index, 
                 vix_signals.loc[dates_sample]['position'], 
                 label='VIX', color='#1f77b4', alpha=0.7, linewidth=0.8)
        ax5.plot(sp500_signals.loc[dates_sample].index, 
                 sp500_signals.loc[dates_sample]['position'], 
                 label='S&P 500', color='#2ca02c', alpha=0.7, linewidth=0.8)
    else:
        step = max(1, len(sp500_signals) // 200)
        ax5.plot(sp500_signals.index[::step], sp500_signals['position'][::step], 
                 label='S&P 500', color='#2ca02c', alpha=0.7)
    ax5.axhline(y=1.0, color='black', linestyle='--', alpha=0.3, linewidth=0.8, label='100%')
    ax5.axhline(y=0.0, color='red', linestyle='--', alpha=0.3, linewidth=0.8, label='0%')
    ax5.set_title('Positionsgrößen (gefiltert)', fontsize=13)
    ax5.set_xlabel('Datum')
    ax5.set_ylabel('Position')
    ax5.set_ylim(-0.05, 1.3)
    ax5.legend(loc='upper left', fontsize=8)
    ax5.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sp500_comparison_professional.png', dpi=200, bbox_inches='tight')
    plt.show()
    print(f"💾 Professionelle Grafik gespeichert: {OUTPUT_DIR / 'sp500_comparison_professional.png'}")


def print_performance_report(name: str, perf: dict):
    """Gibt einen Performance-Report aus."""
    # Hilfsfunktion: Extrahiert einen einzelnen Wert aus einem dict
    def safe_value(value):
        if isinstance(value, pd.Series):
            return value.iloc[0] if len(value) > 0 else 0.0
        return value
    
    # Werte sicher extrahieren
    total_return = safe_value(perf['total_return_strategy'])
    market_return = safe_value(perf['total_return_market'])
    sharpe = safe_value(perf['sharpe_ratio'])
    max_dd = safe_value(perf['max_drawdown'])
    num_trades = safe_value(perf['num_trades'])
    avg_pos = safe_value(perf['avg_position'])
    
    print(f"\n📊 {name} PERFORMANCE-REPORT")
    print("-" * 40)
    print(f"   Gesamtrendite:    {total_return:.2%}")
    print(f"   Buy & Hold:       {market_return:.2%}")
    print(f"   Mehrrendite:      {total_return - market_return:.2%}")
    print(f"   Sharpe Ratio:     {sharpe:.2f}")
    print(f"   Max. Drawdown:    {max_dd:.2%}")
    print(f"   Anzahl Trades:    {int(num_trades) if num_trades is not None else 0}")
    print(f"   Ø Position:       {avg_pos:.1%}")

# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion für das S&P 500-Regime-Modell."""
    print("=" * 60)
    print("📈 STARTE S&P 500 REGIME-MODELL")
    print("=" * 60)
    
    # 1. S&P 500 Daten laden
    sp500_df = load_sp500_data()
    sp500_returns = sp500_df['Close'].pct_change().dropna()
    print(f"📈 Renditen: {len(sp500_returns)} Tage")
    
    # 2. VIX-Wahrscheinlichkeiten laden (zum Vergleich)
    vix_prob = load_vix_probabilities()
    
    # 3. S&P 500 Regime-Modell fitten
    res_sp500 = fit_sp500_regime_model(sp500_returns, N_REGIMES)
    regime_df_sp500 = interpret_sp500_regimes(res_sp500)
    
    # 4. Wahrscheinlichkeiten extrahieren
    prob_sp500 = res_sp500.filtered_marginal_probabilities
    if hasattr(prob_sp500, 'values'):
        prob_array_sp500 = prob_sp500.values
    else:
        prob_array_sp500 = np.array(prob_sp500)
    
    prob_df_sp500 = pd.DataFrame(prob_array_sp500, 
                                 index=sp500_returns.index, 
                                 columns=regime_df_sp500['label'].tolist())
    prob_df_sp500.to_csv(OUTPUT_DIR / 'sp500_regime_probabilities.csv')
    print(f"\n💾 S&P 500 Wahrscheinlichkeiten gespeichert: {OUTPUT_DIR / 'sp500_regime_probabilities.csv'}")
    
    # 5. Signale generieren
    print("\n📊 Generiere S&P 500-Signale...")
    signals_sp500 = generate_sp500_signals(prob_df_sp500)
    
    # 6. Performance berechnen
    perf_sp500 = calculate_performance(signals_sp500, sp500_returns)
    
    # 7. VIX-Performance laden (falls vorhanden)
    if vix_prob is not None:
        # Lade ursprüngliche VIX-Signale (vereinfacht)
        # Wir laden die bereits gespeicherten Signale
        signals_path = DATA_DIR / "results" / "trading_signals.csv"
        if signals_path.exists():
            signals_vix = pd.read_csv(signals_path, index_col=0, parse_dates=True)
            # Lade VIX-Renditen aus den ursprünglichen Daten
            market_data = pd.read_csv(DATA_DIR / "market_data.csv", index_col=0, parse_dates=True)
            vix_returns = market_data['VIX'].pct_change().dropna()
            perf_vix = calculate_performance(signals_vix, vix_returns)
            
            # Vergleichsgrafik
            plot_comparison(perf_vix, perf_sp500, signals_vix, signals_sp500)
        else:
            print("⚠️ VIX-Signale nicht gefunden – überspringe Vergleich")
    else:
        # Nur S&P 500 Performance anzeigen
        plot_sp500_only(perf_sp500, signals_sp500, sp500_returns)
    
    # 8. Performance-Reports
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE-VERGLEICH")
    print("=" * 60)
    
    print_performance_report("S&P 500", perf_sp500)
    
    if 'perf_vix' in locals():
        print_performance_report("VIX", perf_vix)
    
    print("\n" + "=" * 60)
    print("🏁 S&P 500 REGIME-MODELL ABGESCHLOSSEN")
    print("=" * 60)


def plot_sp500_only(perf: dict, signals: pd.DataFrame, returns: pd.Series):
    """Zeigt nur die S&P 500 Performance (ohne Vergleich)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
    
    # Kumulierte Renditen
    ax1.plot(perf['strategy_cum'].index, perf['strategy_cum'], 
             label='S&P 500-Strategie', color='green', linewidth=2)
    ax1.plot(perf['market_cum'].index, perf['market_cum'], 
             label='S&P 500 (Buy&Hold)', color='grey', alpha=0.7)
    ax1.set_title('S&P 500 Strategie Performance', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Positionsgrößen
    ax2.fill_between(signals.index, 0, signals['position'], 
                     color='green', alpha=0.5, label='Positionsgröße')
    ax2.axhline(y=1.0, color='black', linestyle='--', alpha=0.3)
    ax2.set_title('Positionsgrößen über die Zeit', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sp500_performance.png', dpi=150)
    plt.show()
    print(f"💾 Grafik gespeichert: {OUTPUT_DIR / 'sp500_performance.png'}")


if __name__ == "__main__":
    main()
