"""
out_of_sample_test.py – Out-of-Sample Test der optimierten Strategie
====================================================================

Dieses Skript:
1. Teilt die Daten in Trainings- (1990-2019) und Testzeitraum (2020-2026)
2. Wendet die optimierten Parameter auf den Testzeitraum an
3. Speichert die Ergebnisse tabellarisch
4. Erstellt einen Vergleichsbericht
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Optimierte Parameter (aus der Grafik)
PARAMS = {
    'bull_quiet': 0.50,
    'stress': 0.60,
    'bull_fragile': 0.35,
    'reversion': 0.30,
    'confirmation_days': 5,
    'max_position': 1.0,
    'min_position': 0.0
}

# Zeiträume
TRAIN_END = "2019-12-31"
TEST_START = "2020-01-01"

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data():
    """Lädt die Daten und teilt sie in Trainings- und Testzeitraum."""
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
    
    # Aufteilen
    train_prob = prob_df[prob_df.index <= TRAIN_END]
    test_prob = prob_df[prob_df.index >= TEST_START]
    train_returns = returns[returns.index <= TRAIN_END]
    test_returns = returns[returns.index >= TEST_START]
    
    print(f"📊 Trainingszeitraum: {train_prob.index[0].date()} bis {train_prob.index[-1].date()} ({len(train_prob)} Tage)")
    print(f"📊 Testzeitraum:      {test_prob.index[0].date()} bis {test_prob.index[-1].date()} ({len(test_prob)} Tage)")
    
    return train_prob, test_prob, train_returns, test_returns

# =============================================================================
# 3. SIGNALGENERIERUNG
# =============================================================================

def generate_signals(prob_df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Generiert Handelssignale."""
    stress = 1 - (prob_df['BULL_QUIET'] + prob_df['POST_PANIC_REVERSION'] + prob_df['BULL_FRAGILE'])
    stress = stress.clip(lower=0)
    
    signals = pd.DataFrame(index=prob_df.index)
    signals['position'] = 0.0
    signals['regime'] = 'UNKNOWN'
    
    conf = params['confirmation_days']
    
    for i in range(conf, len(signals)):
        start_idx = max(0, i - conf)
        
        if prob_df['BULL_QUIET'].iloc[start_idx:i+1].mean() > params['bull_quiet']:
            signals.loc[signals.index[i], 'position'] = params['max_position']
            signals.loc[signals.index[i], 'regime'] = 'BULL_QUIET'
        elif stress.iloc[start_idx:i+1].mean() > params['stress']:
            signals.loc[signals.index[i], 'position'] = params['min_position']
            signals.loc[signals.index[i], 'regime'] = 'STRESS'
        elif prob_df['POST_PANIC_REVERSION'].iloc[start_idx:i+1].mean() > params['reversion']:
            signals.loc[signals.index[i], 'position'] = params['max_position']
            signals.loc[signals.index[i], 'regime'] = 'POST_PANIC_REVERSION'
        elif prob_df['BULL_FRAGILE'].iloc[start_idx:i+1].mean() > params['bull_fragile']:
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
    """Berechnet die Performance."""
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    
    # Hilfsfunktion: sicher einen einzelnen Float-Wert extrahieren
    def safe_float(value):
        if isinstance(value, pd.Series):
            return float(value.iloc[0]) if len(value) > 0 else 0.0
        return float(value)
    
    # Alle Werte sicher extrahieren
    total_return_strategy = safe_float(strategy_cum.iloc[-1]) - 1 if len(strategy_cum) > 0 else 0.0
    total_return_market = safe_float(market_cum.iloc[-1]) - 1 if len(market_cum) > 0 else 0.0
    max_drawdown = safe_float(drawdown.min()) if len(drawdown) > 0 else 0.0
    avg_position = safe_float(signals_aligned['position'].mean()) if len(signals_aligned) > 0 else 0.0
    sharpe_ratio = safe_float(sharpe)
    
    return {
        'total_return_strategy': total_return_strategy,
        'total_return_market': total_return_market,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'num_trades': int((signals_aligned['position'] != signals_aligned['position'].shift(1)).sum()),
        'avg_position': avg_position,
        'n_days': len(signals_aligned)
    }

# =============================================================================
# 5. SPEICHERUNG
# =============================================================================

def save_results(results: dict):
    """Speichert die Ergebnisse als JSON und CSV."""
    # 1. JSON mit allen Kennzahlen
    with open(OUTPUT_DIR / 'out_of_sample_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    print(f"💾 Ergebnisse gespeichert: {OUTPUT_DIR / 'out_of_sample_results.json'}")
    
    # 2. CSV für tabellarische Auswertung
    df = pd.DataFrame({
        'Zeitraum': ['Training', 'Test'],
        'Strategie_Rendite': [results['train']['total_return_strategy'], results['test']['total_return_strategy']],
        'Markt_Rendite': [results['train']['total_return_market'], results['test']['total_return_market']],
        'Sharpe_Ratio': [results['train']['sharpe_ratio'], results['test']['sharpe_ratio']],
        'Max_Drawdown': [results['train']['max_drawdown'], results['test']['max_drawdown']],
        'Anzahl_Trades': [results['train']['num_trades'], results['test']['num_trades']],
        'Ø_Position': [results['train']['avg_position'], results['test']['avg_position']],
        'Tage': [results['train']['n_days'], results['test']['n_days']]
    })
    df.to_csv(OUTPUT_DIR / 'out_of_sample_comparison.csv', index=False)
    print(f"💾 Vergleichstabelle gespeichert: {OUTPUT_DIR / 'out_of_sample_comparison.csv'}")

# =============================================================================
# 6. REPORT
# =============================================================================

def print_report(results: dict):
    """Gibt einen tabellarischen Report aus."""
    print("\n" + "=" * 70)
    print("📊 OUT-OF-SAMPLE TEST REPORT")
    print("=" * 70)
    
    # Tabelle
    print(f"\n{'Kennzahl':<25} {'Training (1990-2019)':<25} {'Test (2020-2026)':<25}")
    print("-" * 75)
    print(f"{'Gesamtrendite Strategie':<25} {results['train']['total_return_strategy']:>24.2%} {results['test']['total_return_strategy']:>24.2%}")
    print(f"{'Gesamtrendite Markt':<25} {results['train']['total_return_market']:>24.2%} {results['test']['total_return_market']:>24.2%}")
    print(f"{'Mehrrendite':<25} {results['train']['total_return_strategy'] - results['train']['total_return_market']:>24.2%} {results['test']['total_return_strategy'] - results['test']['total_return_market']:>24.2%}")
    print(f"{'Sharpe Ratio':<25} {results['train']['sharpe_ratio']:>24.2f} {results['test']['sharpe_ratio']:>24.2f}")
    print(f"{'Max. Drawdown':<25} {results['train']['max_drawdown']:>24.2%} {results['test']['max_drawdown']:>24.2%}")
    print(f"{'Anzahl Trades':<25} {results['train']['num_trades']:>24} {results['test']['num_trades']:>24}")
    print(f"{'Ø Position':<25} {results['train']['avg_position']:>24.1%} {results['test']['avg_position']:>24.1%}")
    print(f"{'Tage':<25} {results['train']['n_days']:>24} {results['test']['n_days']:>24}")
    
    # Fazit
    print("\n" + "=" * 70)
    print("📋 FAZIT")
    print("=" * 70)
    
    sharpe_train = results['train']['sharpe_ratio']
    sharpe_test = results['test']['sharpe_ratio']
    diff = sharpe_test - sharpe_train
    
    if diff > 0.1:
        print(f"✅ Die Strategie hat im Testzeitraum besser performt als im Training (+{diff:.2f}).")
    elif diff < -0.1:
        print(f"⚠️ Die Strategie hat im Testzeitraum schlechter performt als im Training ({diff:.2f}).")
    else:
        print(f"✅ Die Strategie ist robust – die Performance ist stabil (Differenz: {diff:.2f}).")
    
    if sharpe_test > 0.5:
        print(f"✅ Die Sharpe Ratio im Testzeitraum ({sharpe_test:.2f}) liegt über der 0.5-Schwelle.")
    else:
        print(f"⚠️ Die Sharpe Ratio im Testzeitraum ({sharpe_test:.2f}) liegt unter der 0.5-Schwelle.")

# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 70)
    print("📈 STARTE OUT-OF-SAMPLE TEST")
    print("=" * 70)
    
    # Daten laden
    train_prob, test_prob, train_returns, test_returns = load_data()
    
    # Trainings-Performance
    print("\n🔧 Berechne Trainings-Performance...")
    train_signals = generate_signals(train_prob, PARAMS)
    train_perf = calculate_performance(train_signals, train_returns)
    
    # Test-Performance
    print("🔧 Berechne Test-Performance...")
    test_signals = generate_signals(test_prob, PARAMS)
    test_perf = calculate_performance(test_signals, test_returns)
    
    # Ergebnisse zusammenfassen
    results = {
        'train': train_perf,
        'test': test_perf,
        'params': PARAMS,
        'train_period': f"{train_prob.index[0].date()} bis {train_prob.index[-1].date()}",
        'test_period': f"{test_prob.index[0].date()} bis {test_prob.index[-1].date()}"
    }
    
    # Speichern
    save_results(results)
    
    # Report
    print_report(results)
    
    print("\n" + "=" * 70)
    print("🏁 OUT-OF-SAMPLE TEST ABGESCHLOSSEN")
    print("=" * 70)
    print("💡 Nächster Schritt: Führen Sie 'plot_results.py' aus, um Grafiken zu erstellen.")

if __name__ == "__main__":
    main()
