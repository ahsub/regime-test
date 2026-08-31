"""
out_of_sample_3step.py – Out-of-Sample Test für 3-Stufen-Ensemble
==================================================================

Dieses Skript testet die 3-Stufen-Ensemble-Strategie auf einem separaten
Testzeitraum (2020–2026), um die Robustheit zu überprüfen.

Training: 2011-01-01 bis 2019-12-31
Test:     2020-01-01 bis 2026-08-28
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import yfinance as yf
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

TRAIN_END = "2019-12-31"
TEST_START = "2020-01-01"

# =============================================================================
# 1. DATEN LADEN
# =============================================================================

def load_data():
    print("📊 Lade Signale der Modelle...")
    
    vix_signals = pd.read_csv(OUTPUT_DIR / 'trading_signals.csv', index_col=0, parse_dates=True)
    vix_signals.index = pd.to_datetime(vix_signals.index).tz_localize(None)
    print(f"   📊 VIX-Signale: {len(vix_signals)} Tage")
    
    hmm_labels = pd.read_csv(OUTPUT_DIR / 'rolling_hmm_enhanced_labels.csv', index_col=0, parse_dates=True)
    hmm_labels.index = pd.to_datetime(hmm_labels.index).tz_localize(None)
    print(f"   📊 HMM-Labels: {len(hmm_labels)} Tage")
    
    sp500 = yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    
    if isinstance(returns.index, pd.MultiIndex):
        returns.index = returns.index.get_level_values(0)
    returns.index = pd.to_datetime(returns.index).tz_localize(None)
    if isinstance(returns, pd.DataFrame):
        returns = returns.squeeze()
    
    print(f"   ✅ S&P 500 von Yahoo Finance geladen: {len(returns)} Tage")
    
    common_dates = vix_signals.index.intersection(hmm_labels.index).intersection(returns.index)
    vix_signals = vix_signals.loc[common_dates]
    hmm_labels = hmm_labels.loc[common_dates]
    returns = returns.loc[common_dates]
    
    print(f"   ✅ {len(common_dates)} gemeinsame Tage gefunden")
    return vix_signals, hmm_labels, returns

# =============================================================================
# 2. 3-STUFEN-ENSEMBLE
# =============================================================================

def generate_3step_signals(vix_signals: pd.DataFrame, hmm_labels: pd.DataFrame) -> pd.DataFrame:
    """Generiert 3-Stufen-Ensemble-Signale."""
    vix_bull = vix_signals['position'] > 0.7
    
    hmm_bull = hmm_labels['state'] == 2
    hmm_sideways = hmm_labels['state'] == 1
    hmm_bear = hmm_labels['state'] == 0
    
    position = pd.Series(0.0, index=vix_signals.index)
    position[vix_bull & hmm_bull] = 1.0
    position[vix_bull & hmm_sideways] = 0.5
    position[vix_bull & hmm_bear] = 0.25
    
    signals = pd.DataFrame(index=vix_signals.index)
    signals['position'] = position
    signals['vix_bull'] = vix_bull.astype(int)
    signals['hmm_state'] = hmm_labels['state']
    
    return signals

# =============================================================================
# 3. PERFORMANCE-BERECHNUNG
# =============================================================================

def safe_float(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0]) if len(value) > 0 else 0.0
    return float(value) if value is not None else 0.0

def calculate_performance(signals, returns, name):
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {'total_return_strategy': 0.0, 'total_return_market': 0.0,
                'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'num_trades': 0,
                'avg_position': 0.0, 'n_days': 0}
    
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
    
    last_strategy = strategy_cum.iloc[-1] if len(strategy_cum) > 0 else 1.0
    last_market = market_cum.iloc[-1] if len(market_cum) > 0 else 1.0
    
    return {
        'total_return_strategy': safe_float(last_strategy) - 1,
        'total_return_market': safe_float(last_market) - 1,
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(dd_min) if dd_min is not None else 0.0,
        'num_trades': int((positions != positions.shift(1)).sum()),
        'avg_position': float(positions.mean()) if len(positions) > 0 else 0.0,
        'n_days': len(positions)
    }

# =============================================================================
# 4. REPORT
# =============================================================================

def print_comparison(train_perf, test_perf, full_perf):
    print("\n" + "=" * 80)
    print("📊 OUT-OF-SAMPLE TEST: 3-STUFEN-ENSEMBLE")
    print("=" * 80)
    
    print(f"\n{'Kennzahl':<25} | {'Training (2011-2019)':<22} | {'Test (2020-2026)':<22} | {'Voll (2011-2026)':<22}")
    print("-" * 95)
    print(f"{'Gesamtrendite':<25} | {train_perf['total_return_strategy']:>21.2%} | {test_perf['total_return_strategy']:>21.2%} | {full_perf['total_return_strategy']:>21.2%}")
    print(f"{'Buy & Hold':<25} | {train_perf['total_return_market']:>21.2%} | {test_perf['total_return_market']:>21.2%} | {full_perf['total_return_market']:>21.2%}")
    print(f"{'Sharpe Ratio':<25} | {train_perf['sharpe_ratio']:>21.2f} | {test_perf['sharpe_ratio']:>21.2f} | {full_perf['sharpe_ratio']:>21.2f}")
    print(f"{'Max. Drawdown':<25} | {train_perf['max_drawdown']:>21.2%} | {test_perf['max_drawdown']:>21.2%} | {full_perf['max_drawdown']:>21.2%}")
    print(f"{'Anzahl Trades':<25} | {train_perf['num_trades']:>21} | {test_perf['num_trades']:>21} | {full_perf['num_trades']:>21}")
    print(f"{'Ø Position':<25} | {train_perf['avg_position']:>21.1%} | {test_perf['avg_position']:>21.1%} | {full_perf['avg_position']:>21.1%}")
    print(f"{'Tage':<25} | {train_perf['n_days']:>21} | {test_perf['n_days']:>21} | {full_perf['n_days']:>21}")
    
    print("\n" + "=" * 80)
    print("📋 FAZIT")
    print("=" * 80)
    
    sr_train = train_perf['sharpe_ratio']
    sr_test = test_perf['sharpe_ratio']
    sr_full = full_perf['sharpe_ratio']
    
    # Vergleich Train vs. Test
    diff = sr_test - sr_train
    
    if diff > 0.1:
        print(f"✅ Die Strategie hat im Testzeitraum besser performt als im Training: Sharpe {sr_train:.2f} → {sr_test:.2f} (+{diff:.2f})")
    elif diff < -0.1:
        print(f"⚠️ Die Strategie hat im Testzeitraum schlechter performt als im Training: Sharpe {sr_train:.2f} → {sr_test:.2f} ({diff:.2f})")
    else:
        print(f"✅ Die Strategie ist robust – die Performance ist stabil: Sharpe {sr_train:.2f} → {sr_test:.2f} (Differenz: {diff:.2f})")
    
    # Schwellwert-Check
    if sr_test > 0.4:
        print(f"✅ Die Sharpe Ratio im Testzeitraum ({sr_test:.2f}) liegt über der 0.4-Schwelle.")
    elif sr_test > 0.3:
        print(f"⚠️ Die Sharpe Ratio im Testzeitraum ({sr_test:.2f}) liegt unter der 0.4-Schwelle, aber über 0.3.")
    else:
        print(f"⚠️ Die Sharpe Ratio im Testzeitraum ({sr_test:.2f}) liegt unter der 0.3-Schwelle – Verbesserungsbedarf.")
    
    # Gesamtbewertung
    print("\n💡 EMPFEHLUNG:")
    if sr_test > 0.4 and sr_test >= sr_train * 0.8:
        print("   → Die 3-Stufen-Ensemble-Strategie ist robust und kann verwendet werden.")
        print("   → Die Performance im Testzeitraum bestätigt die Validität der Strategie.")
    elif sr_test > 0.3:
        print("   → Die 3-Stufen-Ensemble-Strategie zeigt im Testzeitraum eine moderate Performance.")
        print("   → Eine Optimierung der Parameter (Schwellwerte) könnte die Stabilität verbessern.")
    else:
        print("   → Die 3-Stufen-Ensemble-Strategie zeigt im Testzeitraum eine schwache Performance.")
        print("   → Die Strategie ist möglicherweise überoptimiert – eine Vereinfachung wird empfohlen.")

# =============================================================================
# 5. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE OUT-OF-SAMPLE TEST (3-STUFEN-ENSEMBLE)")
    print("=" * 80)
    
    # Daten laden
    vix_signals, hmm_labels, returns = load_data()
    
    # Daten aufteilen
    train_mask = returns.index <= TRAIN_END
    test_mask = returns.index >= TEST_START
    
    print(f"\n📅 Zeiträume:")
    print(f"   Training: {returns.index[train_mask].min().date()} bis {returns.index[train_mask].max().date()} ({train_mask.sum()} Tage)")
    print(f"   Test:     {returns.index[test_mask].min().date()} bis {returns.index[test_mask].max().date()} ({test_mask.sum()} Tage)")
    
    # 3-Stufen-Signale generieren (für gesamten Zeitraum)
    signals_full = generate_3step_signals(vix_signals, hmm_labels)
    
    # Performance auf Training/Test/Full
    train_perf = calculate_performance(
        signals_full.loc[train_mask], 
        returns.loc[train_mask], 
        "Training"
    )
    test_perf = calculate_performance(
        signals_full.loc[test_mask], 
        returns.loc[test_mask], 
        "Test"
    )
    full_perf = calculate_performance(signals_full, returns, "Voll")
    
    # Report
    print_comparison(train_perf, test_perf, full_perf)
    
    # Speichern
    signals_full.to_csv(OUTPUT_DIR / 'out_of_sample_3step_signals.csv')
    print(f"\n💾 Signale gespeichert: {OUTPUT_DIR / 'out_of_sample_3step_signals.csv'}")
    
    # Zusammenfassung speichern
    summary = pd.DataFrame({
        'Zeitraum': ['Training', 'Test', 'Voll'],
        'Sharpe_Ratio': [train_perf['sharpe_ratio'], test_perf['sharpe_ratio'], full_perf['sharpe_ratio']],
        'Gesamtrendite': [train_perf['total_return_strategy'], test_perf['total_return_strategy'], full_perf['total_return_strategy']],
        'Drawdown': [train_perf['max_drawdown'], test_perf['max_drawdown'], full_perf['max_drawdown']],
        'Trades': [train_perf['num_trades'], test_perf['num_trades'], full_perf['num_trades']],
        'Ø_Position': [train_perf['avg_position'], test_perf['avg_position'], full_perf['avg_position']],
        'Tage': [train_perf['n_days'], test_perf['n_days'], full_perf['n_days']]
    })
    summary.to_csv(OUTPUT_DIR / 'out_of_sample_3step_summary.csv', index=False)
    print(f"💾 Zusammenfassung gespeichert: {OUTPUT_DIR / 'out_of_sample_3step_summary.csv'}")
    
    print("\n" + "=" * 80)
    print("🏁 OUT-OF-SAMPLE TEST ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
