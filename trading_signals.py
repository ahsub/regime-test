"""
trading_signals.py – Handelssignale aus Regime-Wahrscheinlichkeiten
===================================================================

Dieses Skript:
1. Lädt die Regime-Wahrscheinlichkeiten aus dem vorherigen Schritt
2. Wendet Handelsregeln an, um Positionsgrößen zu bestimmen
3. Berechnet die Performance der Strategie
4. Visualisiert die Ergebnisse
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
PROB_FILE = DATA_DIR / "results" / "regime_probabilities.csv"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_probabilities(filepath: Path) -> pd.DataFrame:
    """Lädt die Regime-Wahrscheinlichkeiten."""
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    print(f"📊 Wahrscheinlichkeiten geladen: {len(df)} Zeilen")
    print(f"   Regime: {', '.join(df.columns)}")
    return df

def load_market_data() -> pd.DataFrame:
    """Lädt die ursprünglichen Marktdaten (für Renditen)."""
    filepath = DATA_DIR / "market_data.csv"
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    return df

# =============================================================================
# 3. SIGNALLOGIK
# =============================================================================

def generate_signals(prob_df: pd.DataFrame, 
                     thresholds: dict = None) -> pd.DataFrame:
    """
    Generiert Handelssignale basierend auf Regime-Wahrscheinlichkeiten.
    
    Parameter:
    ----------
    prob_df : pd.DataFrame
        DataFrame mit Wahrscheinlichkeiten für jedes Regime
    thresholds : dict
        Schwellwerte für die Signalgenerierung
    
    Rückgabe:
    --------
    pd.DataFrame : Signale und Positionsgrößen
    """
    if thresholds is None:
        thresholds = {
            'bull_quiet': 0.55,      # Schwellwert für volles Investment
            'bull_fragile': 0.45,    # Schwellwert für reduziertes Investment
            'stress': 0.40,          # Schwellwert für Ausstieg
            'reversion': 0.35,       # Schwellwert für Wiedereinstieg
            'max_position': 1.0,     # Maximale Positionsgröße (100%)
            'min_position': 0.0,     # Minimale Positionsgröße (Cash)
            'confirmation_days': 3   # Tage für Signalbestätigung
        }
    
    print("\n📊 Signal-Parameter:")
    for key, value in thresholds.items():
        print(f"   {key}: {value}")
    
    # Ergebnisse initialisieren
    signals = pd.DataFrame(index=prob_df.index)
    signals['position'] = 0.0  # Positionsgröße (0 bis 1)
    signals['regime'] = 'UNKNOWN'
    
    # Regime-Spalten extrahieren
    bull_quiet = prob_df['BULL_QUIET'].values
    bull_fragile = prob_df['BULL_FRAGILE'].values
    post_panic = prob_df['POST_PANIC_REVERSION'].values
    
    # STRESS_UNSTABLE gibt es nicht im 3-Regime-Modell
    # Wir nutzen stattdessen die Umkehrung der anderen Wahrscheinlichkeiten
    stress = 1 - (bull_quiet + bull_fragile + post_panic)
    # Korrigieren: Wenn stress negativ wird, auf 0 setzen
    stress = np.maximum(stress, 0)
    
    # Signalgenerierung mit Bestätigung
    conf = thresholds['confirmation_days']
    
    for i in range(conf, len(signals)):
        # Fenster für Bestätigung
        start_idx = max(0, i - conf)
        
        # 1. BULL_QUIET: Voll investiert
        if np.mean(bull_quiet[start_idx:i+1]) > thresholds['bull_quiet']:
            signals.loc[signals.index[i], 'position'] = thresholds['max_position']
            signals.loc[signals.index[i], 'regime'] = 'BULL_QUIET'
            
        # 2. Stress (hohe Unsicherheit): Ausstieg
        elif np.mean(stress[start_idx:i+1]) > thresholds['stress']:
            signals.loc[signals.index[i], 'position'] = thresholds['min_position']
            signals.loc[signals.index[i], 'regime'] = 'STRESS'
            
        # 3. POST_PANIC_REVERSION: Wiedereinstieg
        elif np.mean(post_panic[start_idx:i+1]) > thresholds['reversion']:
            signals.loc[signals.index[i], 'position'] = thresholds['max_position'] * 1.2
            signals.loc[signals.index[i], 'regime'] = 'POST_PANIC_REVERSION'
            
        # 4. BULL_FRAGILE: Reduzierte Position
        elif np.mean(bull_fragile[start_idx:i+1]) > thresholds['bull_fragile']:
            signals.loc[signals.index[i], 'position'] = 0.7
            signals.loc[signals.index[i], 'regime'] = 'BULL_FRAGILE'
            
        # 5. Kein klares Signal: Position halten
        else:
            if i > 0:
                signals.loc[signals.index[i], 'position'] = signals.loc[signals.index[i-1], 'position']
                signals.loc[signals.index[i], 'regime'] = signals.loc[signals.index[i-1], 'regime']
    
    # Positionsgrößen begrenzen
    signals['position'] = signals['position'].clip(
        thresholds['min_position'], 
        thresholds['max_position'] * 1.2
    )
    
    return signals

# =============================================================================
# 4. PERFORMANCE-BERECHNUNG
# =============================================================================

def calculate_performance(signals: pd.DataFrame, 
                          returns: pd.Series) -> dict:
    """
    Berechnet die Performance der Strategie.
    
    Parameter:
    ----------
    signals : pd.DataFrame
        DataFrame mit Positionsgrößen
    returns : pd.Series
        Tägliche Renditen des Marktes
    
    Rückgabe:
    --------
    dict : Performance-Metriken
    """
    # Aligniere Datumsindizes
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    # Strategie-Renditen berechnen
    # Position vom Vortag wird auf die heutige Rendite angewendet
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    # Kumulierte Renditen
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    # Metriken
    total_return_strategy = strategy_cum.iloc[-1] - 1
    total_return_market = market_cum.iloc[-1] - 1
    
    # Sharpe Ratio (annualisiert)
    excess_returns = strategy_returns - 0.02/252  # 2% risikofreier Zins
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    # Maximum Drawdown
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    max_drawdown = drawdown.min()
    
    # Anzahl der Trades (Positionswechsel)
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
# 5. VISUALISIERUNGEN
# =============================================================================

def plot_performance(performance: dict, signals: pd.DataFrame):
    """Zeigt die Performance der Strategie."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    # 1. Kumulierte Renditen
    ax1 = axes[0]
    ax1.plot(performance['strategy_cum'].index, 
             performance['strategy_cum'], 
             label='Strategie', color='blue', linewidth=2)
    ax1.plot(performance['market_cum'].index, 
             performance['market_cum'], 
             label='Buy & Hold', color='grey', alpha=0.7, linewidth=1.5)
    ax1.set_title('Kumulierte Renditen', fontsize=14)
    ax1.set_ylabel('Kumulierte Rendite')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Positionsgrößen
    ax2 = axes[1]
    ax2.fill_between(signals.index, 0, signals['position'], 
                     color='green', alpha=0.5, label='Positionsgröße')
    ax2.axhline(y=1.0, color='blue', linestyle='--', alpha=0.3, label='100% Investiert')
    ax2.axhline(y=0.0, color='red', linestyle='--', alpha=0.3, label='100% Cash')
    ax2.set_title('Positionsgrößen über die Zeit', fontsize=14)
    ax2.set_ylabel('Positionsgröße')
    ax2.set_ylim(-0.1, 1.3)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Drawdown
    ax3 = axes[2]
    peak = performance['strategy_cum'].expanding().max()
    drawdown = (performance['strategy_cum'] - peak) / peak
    ax3.fill_between(drawdown.index, 0, drawdown, 
                     color='red', alpha=0.3, label='Drawdown')
    ax3.set_title('Drawdown der Strategie', fontsize=14)
    ax3.set_ylabel('Drawdown')
    ax3.set_xlabel('Datum')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'trading_performance.png', dpi=150)
    plt.show()
    print(f"💾 Grafik gespeichert: {OUTPUT_DIR / 'trading_performance.png'}")


def plot_regime_allocation(signals: pd.DataFrame):
    """Zeigt die Verteilung der Zeit in jedem Regime."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Zähle Tage pro Regime
    regime_counts = signals['regime'].value_counts()
    
    # Farben definieren
    colors = {
        'BULL_QUIET': 'green',
        'BULL_FRAGILE': 'orange',
        'POST_PANIC_REVERSION': 'blue',
        'STRESS': 'red',
        'UNKNOWN': 'grey'
    }
    
    # Plot
    bars = ax.bar(regime_counts.index, regime_counts.values, 
                  color=[colors.get(r, 'grey') for r in regime_counts.index])
    
    ax.set_title('Verteilung der Handelsregime', fontsize=14)
    ax.set_ylabel('Anzahl der Tage')
    ax.set_xlabel('Regime')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Werte über den Balken
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 10,
                f'{int(height)} Tage', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regime_allocation.png', dpi=150)
    plt.show()
    print(f"💾 Grafik gespeichert: {OUTPUT_DIR / 'regime_allocation.png'}")


def print_report(performance: dict):
    """Gibt einen Performance-Report aus."""
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE-REPORT")
    print("=" * 60)
    
    print(f"\n📈 Renditen:")
    print(f"   Strategie:        {performance['total_return_strategy']:.2%}")
    print(f"   Buy & Hold:       {performance['total_return_market']:.2%}")
    print(f"   Mehrrendite:      {performance['total_return_strategy'] - performance['total_return_market']:.2%}")
    
    print(f"\n📉 Risiko:")
    print(f"   Sharpe Ratio:     {performance['sharpe_ratio']:.2f}")
    print(f"   Max. Drawdown:    {performance['max_drawdown']:.2%}")
    
    print(f"\n🔄 Aktivität:")
    print(f"   Anzahl Trades:    {performance['num_trades']}")
    print(f"   Ø Position:       {performance['avg_position']:.1%}")


# =============================================================================
# 6. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion für die Signalgenerierung."""
    print("=" * 60)
    print("📈 STARTE TRADING-SIGNALE")
    print("=" * 60)
    
    # 1. Daten laden
    prob_df = load_probabilities(PROB_FILE)
    market_data = load_market_data()
    
    # 2. Renditen berechnen (basierend auf VIX, als Proxy für Marktbewegungen)
    returns = market_data['VIX'].pct_change().dropna()
    print(f"📈 Renditen: {len(returns)} Tage")
    
    # 3. Signale generieren
    signals = generate_signals(prob_df)
    
    # 4. Performance berechnen
    performance = calculate_performance(signals, returns)
    
    # 5. Visualisierungen
    print("\n📊 Erstelle Visualisierungen...")
    plot_performance(performance, signals)
    plot_regime_allocation(signals)
    
    # 6. Report
    print_report(performance)
    
    # 7. Ergebnisse speichern
    signals.to_csv(OUTPUT_DIR / 'trading_signals.csv')
    print(f"\n💾 Signale gespeichert: {OUTPUT_DIR / 'trading_signals.csv'}")
    
    print("\n" + "=" * 60)
    print("🏁 TRADING-SIGNALE ABGESCHLOSSEN")
    print("=" * 60)
    print("💡 Nächster Schritt: Die Signale können nun für einen Backtest oder Live-Trading genutzt werden.")


if __name__ == "__main__":
    main()
