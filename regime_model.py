"""
regime_model.py – Markov-Switching Modell für Market Regime Analyse
===================================================================

Dieses Skript:
1. Lädt den bereinigten Datensatz (market_data.csv)
2. Fittet ein Markov-Switching-Modell mit 3 Regimen
3. Zeigt die geschätzten Parameter
4. Visualisiert die Regime-Wahrscheinlichkeiten
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "market_data.csv"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Modell-Parameter
N_REGIMES = 3  # 3 Regime: ruhig, volatil, Krise
LOOKBACK_DAYS = 252  # 1 Jahr für das Modell

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data(filepath: Path) -> pd.DataFrame:
    """Lädt den bereinigten Datensatz."""
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    print(f"📊 Daten geladen: {len(df)} Zeilen, {len(df.columns)} Spalten")
    print(f"   Zeitraum: {df.index[0].date()} bis {df.index[-1].date()}")
    return df

# =============================================================================
# 3. MODELL-FIT
# =============================================================================

def fit_markov_model(returns: pd.Series, n_regimes: int = 3) -> object:
    """
    Fittet ein Markov-Switching-Modell mit n Regimen.
    """
    mod = sm.tsa.MarkovRegression(
        endog=returns,
        k_regimes=n_regimes,
        trend='c',
        switching_variance=True,
        switching_trend=True
    )
    
    res = mod.fit()
    print(f"\n✅ Modell gefittet mit {n_regimes} Regimen")
    print(f"   AIC: {res.aic:.2f}")
    print(f"   BIC: {res.bic:.2f}")
    
    return res

# =============================================================================
# 4. REGIME-INTERPRETATION (KORRIGIERT)
# =============================================================================

def interpret_regimes(res: object) -> pd.DataFrame:
    """
    Interpretiert die Regime anhand der geschätzten Parameter.
    Ordnet sie nach Volatilität und Rendite.
    """
    n = res.k_regimes
    
    # KORREKTUR: .iloc[] statt direkter Index
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
    
    # Labels zuweisen (für 3 Regime)
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
    print("\n📊 Regime-Interpretation:")
    print(df[['regime', 'label', 'mean', 'std']].round(4))
    
    return df

# =============================================================================
# 5. VISUALISIERUNG
# =============================================================================

def plot_regime_probabilities(probabilities: np.ndarray, 
                              regime_labels: list,
                              dates: pd.DatetimeIndex,
                              returns: pd.Series):
    """Zeigt die Regime-Wahrscheinlichkeiten über die Zeit."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    colors = ['green', 'orange', 'red']
    dominant_regime = np.argmax(probabilities, axis=1)
    
    for i in range(len(regime_labels)):
        mask = (dominant_regime == i)
        ax1.scatter(dates[mask], returns[mask], 
                    color=colors[i % len(colors)], 
                    s=5, alpha=0.5, label=regime_labels[i])
    
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.set_ylabel('Tägliche Rendite')
    ax1.set_title('Marktrenditen nach Regime (dominantes Regime)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    for i in range(len(regime_labels)):
        ax2.fill_between(dates, 0, probabilities[:, i], 
                         alpha=0.4, label=regime_labels[i],
                         color=colors[i % len(colors)])
    
    ax2.set_ylabel('Wahrscheinlichkeit')
    ax2.set_xlabel('Datum')
    ax2.set_title('Regime-Wahrscheinlichkeiten über die Zeit')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regime_probabilities.png', dpi=150)
    plt.show()
    print(f"💾 Grafik gespeichert: {OUTPUT_DIR / 'regime_probabilities.png'}")


def plot_regime_distribution(probabilities: np.ndarray, 
                             regime_labels: list):
    """Zeigt die Verteilung der Regime-Wahrscheinlichkeiten als Boxplot."""
    fig, ax = plt.subplots(figsize=(10, 6))
    df_plot = pd.DataFrame(probabilities, columns=regime_labels)
    sns.boxplot(data=df_plot, ax=ax)
    ax.set_ylabel('Wahrscheinlichkeit')
    ax.set_title('Verteilung der Regime-Wahrscheinlichkeiten')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regime_distribution.png', dpi=150)
    plt.show()
    print(f"💾 Grafik gespeichert: {OUTPUT_DIR / 'regime_distribution.png'}")


def plot_regime_transitions(probabilities: np.ndarray, 
                            regime_labels: list):
    """Zeigt die Übergangswahrscheinlichkeiten zwischen Regimen als Heatmap."""
    dominant = np.argmax(probabilities, axis=1)
    n = len(regime_labels)
    transition_matrix = np.zeros((n, n))
    
    for t in range(1, len(dominant)):
        from_state = dominant[t-1]
        to_state = dominant[t]
        transition_matrix[from_state, to_state] += 1
    
    transition_matrix = transition_matrix / transition_matrix.sum(axis=1, keepdims=True)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(transition_matrix, annot=True, fmt='.2f', 
                xticklabels=regime_labels, 
                yticklabels=regime_labels,
                cmap='Blues', ax=ax)
    ax.set_title('Übergangswahrscheinlichkeiten zwischen Regimen')
    ax.set_xlabel('Zu Regime')
    ax.set_ylabel('Von Regime')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'regime_transitions.png', dpi=150)
    plt.show()
    print(f"💾 Grafik gespeichert: {OUTPUT_DIR / 'regime_transitions.png'}")


# =============================================================================
# 6. ZUSAMMENFASSUNG
# =============================================================================

def print_summary(res: object, regime_df: pd.DataFrame):
    """Gibt eine Zusammenfassung der Modell-Ergebnisse aus."""
    print("\n" + "=" * 60)
    print("📊 MODELL-ZUSAMMENFASSUNG")
    print("=" * 60)
    
    print("\n📈 Regime-Parameter:")
    for _, row in regime_df.iterrows():
        print(f"   {row['label']}: μ = {row['mean']:.4f}, σ = {row['std']:.4f}")
    
    print("\n🔄 Übergangsmatrix (bedingungslos):")
    trans = res.transition_matrix
    for i, row in enumerate(trans):
        print(f"   Regime {i}: {', '.join([f'{x:.2f}' for x in row])}")
    
    probabilities = res.filtered_marginal_probabilities
    dominant = np.argmax(probabilities, axis=1)
    frequencies = np.bincount(dominant) / len(dominant)
    
    print("\n📊 Regime-Häufigkeiten:")
    for i, label in enumerate(regime_df['label']):
        print(f"   {label}: {frequencies[i]:.1%}")


# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion für das Regime-Modell."""
    print("=" * 60)
    print("🧠 STARTE REGIME-MODELL")
    print("=" * 60)
    
    df = load_data(DATA_FILE)
    returns = df['VIX'].pct_change().dropna()
    print(f"📈 Renditen für Modell: {len(returns)} Tage")
    
    res = fit_markov_model(returns, n_regimes=N_REGIMES)
    regime_df = interpret_regimes(res)
    regime_labels = regime_df['label'].tolist()
    
    probabilities = res.filtered_marginal_probabilities
    
    print("\n📊 Erstelle Visualisierungen...")
    plot_regime_probabilities(probabilities, regime_labels, 
                              returns.index, returns)
    plot_regime_distribution(probabilities, regime_labels)
    plot_regime_transitions(probabilities, regime_labels)
    
    print_summary(res, regime_df)
    
    prob_df = pd.DataFrame(probabilities, 
                           index=returns.index, 
                           columns=regime_labels)
    prob_df.to_csv(OUTPUT_DIR / 'regime_probabilities.csv')
    print(f"\n💾 Wahrscheinlichkeiten gespeichert: {OUTPUT_DIR / 'regime_probabilities.csv'}")
    
    print("\n" + "=" * 60)
    print("🏁 REGIME-MODELL ABGESCHLOSSEN")
    print("=" * 60)
    print("💡 Nächster Schritt: Die Regime-Wahrscheinlichkeiten können nun für Handelssignale genutzt werden.")


if __name__ == "__main__":
    main()
