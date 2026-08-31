"""
ensemble_strategy.py – Ensemble-Strategie (VIX + HMM) – NUR TABELLARISCHE AUSGABE
================================================================================

Diese Strategie kombiniert die VIX-Strategie mit dem erweiterten HMM.
Sie investiert nur, wenn BEIDE Modelle ein "Bull"-Signal geben.

Ausgabe: Tabellarischer Report (keine Grafiken)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

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
    
    print(f"   ✅ Ensemble-Signale generiert")
    print(f"   📊 Tage investiert: {signals['position'].sum():.0f} ({signals['position'].mean()*100:.1f}%)")
    return signals

# =============================================================================
# 4. PERFORMANCE-BERECHNUNG (ROBUST)
# =============================================================================

def safe_float(value):
    """Sicherer Konverter zu float."""
    if isinstance(value, pd.Series):
        return float(value.iloc[0]) if len(value) > 0 else 0.0
    return float(value) if value is not None else 0.0

def calculate_performance(signals: pd.DataFrame, returns: pd.Series, name: str) -> dict:
    """Berechnet die Performance einer Strategie."""
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {
            'name': name,
            'total_return_strategy': 0.0,
            'total_return_market': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'num_trades': 0,
            'avg_position': 0.0,
            'n_days': 0
        }
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    
    dd_min = drawdown.min()
    if isinstance(dd_min, pd.Series):
        dd_min = dd_min.iloc[0] if len(dd_min) > 0 else 0.0
    
    return {
        'name': name,
        'total_return_strategy': safe_float(strategy_cum.iloc[-1]) - 1 if len(strategy_cum) > 0 else 0.0,
        'total_return_market': safe_float(market_cum.iloc[-1]) - 1 if len(market_cum) > 0 else 0.0,
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(dd_min) if dd_min is not None else 0.0,
        'num_trades': int((positions != positions.shift(1)).sum()),
        'avg_position': float(positions.mean()) if len(positions) > 0 else 0.0,
        'n_days': len(positions)
    }

# =============================================================================
# 5. TABELLARISCHER REPORT
# =============================================================================

def print_comparison(vix_perf: dict, hmm_perf: dict, ensemble_perf: dict):
    """Gibt einen tabellarischen Vergleichsreport aus."""
    print("\n" + "=" * 80)
    print("📊 ENSEMBLE-VERGLEICH (Tabellarisch)")
    print("=" * 80)
    
    # Tabelle
    headers = ['Kennzahl', 'VIX-Strategie', 'HMM-Strategie', 'Ensemble']
    rows = [
        ['Gesamtrendite', 
         f"{vix_perf['total_return_strategy']:.2%}",
         f"{hmm_perf['total_return_strategy']:.2%}",
         f"{ensemble_perf['total_return_strategy']:.2%}"],
        ['Sharpe Ratio', 
         f"{vix_perf['sharpe_ratio']:.2f}",
         f"{hmm_perf['sharpe_ratio']:.2f}",
         f"{ensemble_perf['sharpe_ratio']:.2f}"],
        ['Max. Drawdown', 
         f"{vix_perf['max_drawdown']:.2%}",
         f"{hmm_perf['max_drawdown']:.2%}",
         f"{ensemble_perf['max_drawdown']:.2%}"],
        ['Anzahl Trades', 
         f"{vix_perf['num_trades']}",
         f"{hmm_perf['num_trades']}",
         f"{ensemble_perf['num_trades']}"],
        ['Ø Position', 
         f"{vix_perf['avg_position']:.1%}",
         f"{hmm_perf['avg_position']:.1%}",
         f"{ensemble_perf['avg_position']:.1%}"],
        ['Tage', 
         f"{vix_perf['n_days']}",
         f"{hmm_perf['n_days']}",
         f"{ensemble_perf['n_days']}"]
    ]
    
    # Tabellarische Ausgabe
    print(f"\n{'Kennzahl':<20} | {'VIX-Strategie':<18} | {'HMM-Strategie':<18} | {'Ensemble':<18}")
    print("-" * 80)
    for row in rows:
        print(f"{row[0]:<20} | {row[1]:>18} | {row[2]:>18} | {row[3]:>18}")
    
    # Fazit
    print("\n" + "=" * 80)
    print("📋 FAZIT")
    print("=" * 80)
    
    sr_vix = vix_perf['sharpe_ratio']
    sr_ens = ensemble_perf['sharpe_ratio']
    dd_vix = vix_perf['max_drawdown']
    dd_ens = ensemble_perf['max_drawdown']
    
    if sr_ens > sr_vix:
        print(f"✅ Ensemble verbessert Sharpe Ratio: {sr_vix:.2f} → {sr_ens:.2f} (+{(sr_ens-sr_vix)*100:.1f}%)")
    else:
        print(f"⚠️ Ensemble verschlechtert Sharpe Ratio: {sr_vix:.2f} → {sr_ens:.2f} ({(sr_ens-sr_vix)*100:.1f}%)")
    
    if dd_ens > dd_vix:
        print(f"✅ Ensemble reduziert Drawdown: {dd_vix:.2%} → {dd_ens:.2%}")
    else:
        print(f"⚠️ Ensemble verschlechtert Drawdown: {dd_vix:.2%} → {dd_ens:.2%}")
    
    # Handlungsempfehlung
    print("\n💡 HANDLUNGSEMPFEHLUNG:")
    if sr_ens > sr_vix and dd_ens > dd_vix:
        print("   → Die Ensemble-Strategie ist der VIX-Strategie in beiden Dimensionen überlegen.")
        print("   → Sie sollte als neue Basisstrategie verwendet werden.")
    elif sr_ens > sr_vix:
        print("   → Die Ensemble-Strategie hat eine bessere Sharpe Ratio, aber höheren Drawdown.")
        print("   → Sie eignet sich für risikobewusste Anleger.")
    elif dd_ens > dd_vix:
        print("   → Die Ensemble-Strategie hat einen geringeren Drawdown, aber niedrigere Sharpe Ratio.")
        print("   → Sie eignet sich für konservative Anleger.")
    else:
        print("   → Die Ensemble-Strategie ist der VIX-Strategie in beiden Dimensionen unterlegen.")
        print("   → Die VIX-Strategie bleibt die bevorzugte Wahl.")

# =============================================================================
# 6. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE ENSEMBLE-STRATEGIE (TABELLARISCH)")
    print("=" * 80)
    
    # Daten laden
    vix_signals, hmm_labels, returns = load_data()
    
    # Ensemble-Signale generieren
    ensemble_signals = generate_ensemble_signals(vix_signals, hmm_labels)
    
    # Performance berechnen
    print("\n📊 Berechne Performance...")
    
    vix_perf = calculate_performance(vix_signals, returns, "VIX")
    
    hmm_signals = pd.DataFrame(index=hmm_labels.index)
    hmm_signals['position'] = hmm_labels['state'].map({0: 0.0, 1: 0.5, 2: 1.0}).fillna(0.0)
    hmm_perf = calculate_performance(hmm_signals, returns, "HMM")
    
    ensemble_perf = calculate_performance(ensemble_signals, returns, "Ensemble")
    
    # Tabellarischen Report ausgeben
    print_comparison(vix_perf, hmm_perf, ensemble_perf)
    
    # Signale speichern
    ensemble_signals.to_csv(OUTPUT_DIR / 'ensemble_signals.csv')
    print(f"\n💾 Ensemble-Signale gespeichert: {OUTPUT_DIR / 'ensemble_signals.csv'}")
    
    print("\n" + "=" * 80)
    print("🏁 ENSEMBLE-STRATEGIE ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
