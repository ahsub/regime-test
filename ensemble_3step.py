"""
ensemble_3step.py – Drei-Stufen-Ensemble (VIX + HMM)
======================================================

Diese Strategie staffelt die Positionsgröße basierend auf der Übereinstimmung:
- Beide Bull: 100%
- VIX Bull + HMM Sideways: 50%
- VIX Bull + HMM Bear: 25%
- Kein VIX Bull: 0%
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
# 2. DREI-STUFEN-ENSEMBLE
# =============================================================================

def generate_3step_signals(vix_signals: pd.DataFrame, hmm_labels: pd.DataFrame) -> pd.DataFrame:
    """
    Generiert 3-Stufen-Ensemble-Signale.
    
    Position:
    - 100%: VIX Bull UND HMM Bull (state == 2)
    - 50%:  VIX Bull UND HMM Sideways (state == 1)
    - 25%:  VIX Bull UND HMM Bear (state == 0)
    - 0%:   VIX nicht Bull
    """
    print("\n🔧 Generiere 3-Stufen-Ensemble-Signale...")
    
    # VIX-Signal: position > 0.7 = Bull
    vix_bull = vix_signals['position'] > 0.7
    
    # HMM-Zustände: 0=Bear, 1=Sideways, 2=Bull
    hmm_bull = hmm_labels['state'] == 2
    hmm_sideways = hmm_labels['state'] == 1
    hmm_bear = hmm_labels['state'] == 0
    
    # Positionsgröße basierend auf Übereinstimmung
    position = pd.Series(0.0, index=vix_signals.index)
    
    # 100%: VIX Bull UND HMM Bull
    position[vix_bull & hmm_bull] = 1.0
    
    # 50%: VIX Bull UND HMM Sideways
    position[vix_bull & hmm_sideways] = 0.5
    
    # 25%: VIX Bull UND HMM Bear
    position[vix_bull & hmm_bear] = 0.25
    
    # 0%: Kein VIX Bull (bleibt bei 0)
    
    signals = pd.DataFrame(index=vix_signals.index)
    signals['position'] = position
    signals['vix_bull'] = vix_bull.astype(int)
    signals['hmm_state'] = hmm_labels['state']
    signals['regime'] = 'CASH'
    signals.loc[vix_bull & hmm_bull, 'regime'] = 'BULL_BULL'
    signals.loc[vix_bull & hmm_sideways, 'regime'] = 'BULL_SIDEWAYS'
    signals.loc[vix_bull & hmm_bear, 'regime'] = 'BULL_BEAR'
    
    print(f"   ✅ 3-Stufen-Ensemble-Signale generiert")
    print(f"   📊 Tage mit 100%: {(position == 1.0).sum():.0f}")
    print(f"   📊 Tage mit 50%:  {(position == 0.5).sum():.0f}")
    print(f"   📊 Tage mit 25%:  {(position == 0.25).sum():.0f}")
    print(f"   📊 Tage mit 0%:   {(position == 0.0).sum():.0f}")
    print(f"   📊 Ø Position:    {position.mean()*100:.1f}%")
    
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

def print_comparison(vix_perf, hmm_perf, ensemble_perf, three_step_perf):
    print("\n" + "=" * 80)
    print("📊 3-STUFEN-ENSEMBLE VERGLEICH")
    print("=" * 80)
    
    print(f"\n{'Kennzahl':<20} | {'VIX':<14} | {'HMM':<14} | {'2-Stufen Ens.':<14} | {'3-Stufen Ens.':<14}")
    print("-" * 95)
    print(f"{'Gesamtrendite':<20} | {vix_perf['total_return_strategy']:>13.2%} | {hmm_perf['total_return_strategy']:>13.2%} | {ensemble_perf['total_return_strategy']:>13.2%} | {three_step_perf['total_return_strategy']:>13.2%}")
    print(f"{'Sharpe Ratio':<20} | {vix_perf['sharpe_ratio']:>13.2f} | {hmm_perf['sharpe_ratio']:>13.2f} | {ensemble_perf['sharpe_ratio']:>13.2f} | {three_step_perf['sharpe_ratio']:>13.2f}")
    print(f"{'Max. Drawdown':<20} | {vix_perf['max_drawdown']:>13.2%} | {hmm_perf['max_drawdown']:>13.2%} | {ensemble_perf['max_drawdown']:>13.2%} | {three_step_perf['max_drawdown']:>13.2%}")
    print(f"{'Anzahl Trades':<20} | {vix_perf['num_trades']:>13} | {hmm_perf['num_trades']:>13} | {ensemble_perf['num_trades']:>13} | {three_step_perf['num_trades']:>13}")
    print(f"{'Ø Position':<20} | {vix_perf['avg_position']:>13.1%} | {hmm_perf['avg_position']:>13.1%} | {ensemble_perf['avg_position']:>13.1%} | {three_step_perf['avg_position']:>13.1%}")
    print(f"{'Tage':<20} | {vix_perf['n_days']:>13} | {hmm_perf['n_days']:>13} | {ensemble_perf['n_days']:>13} | {three_step_perf['n_days']:>13}")
    
    # Fazit
    print("\n" + "=" * 80)
    print("📋 FAZIT")
    print("=" * 80)
    
    # Vergleich 2-Stufen vs. 3-Stufen
    sr_2step = ensemble_perf['sharpe_ratio']
    sr_3step = three_step_perf['sharpe_ratio']
    dd_2step = ensemble_perf['max_drawdown']
    dd_3step = three_step_perf['max_drawdown']
    ret_2step = ensemble_perf['total_return_strategy']
    ret_3step = three_step_perf['total_return_strategy']
    
    if sr_3step > sr_2step:
        print(f"✅ Die 3-Stufen-Strategie verbessert die Sharpe Ratio: {sr_2step:.2f} → {sr_3step:.2f} (+{(sr_3step-sr_2step)*100:.1f}%)")
    else:
        print(f"⚠️ Die 3-Stufen-Strategie verschlechtert die Sharpe Ratio: {sr_2step:.2f} → {sr_3step:.2f} ({(sr_3step-sr_2step)*100:.1f}%)")
    
    if dd_3step > dd_2step:
        print(f"✅ Die 3-Stufen-Strategie reduziert den Drawdown: {dd_2step:.2%} → {dd_3step:.2%}")
    else:
        print(f"⚠️ Die 3-Stufen-Strategie verschlechtert den Drawdown: {dd_2step:.2%} → {dd_3step:.2%}")
    
    if ret_3step > ret_2step:
        print(f"✅ Die 3-Stufen-Strategie erhöht die Gesamtrendite: {ret_2step:.2%} → {ret_3step:.2%}")
    else:
        print(f"⚠️ Die 3-Stufen-Strategie reduziert die Gesamtrendite: {ret_2step:.2%} → {ret_3step:.2%}")
    
    # Gesamtbewertung
    print("\n💡 EMPFEHLUNG:")
    if sr_3step > 0.5 and dd_3step > dd_2step:
        print("   → Die 3-Stufen-Strategie ist die beste Wahl: Gute Sharpe Ratio + niedriger Drawdown.")
    elif sr_3step > sr_2step:
        print("   → Die 3-Stufen-Strategie verbessert die Sharpe Ratio – zur Optimierung geeignet.")
    elif dd_3step > dd_2step:
        print("   → Die 3-Stufen-Strategie reduziert den Drawdown – für konservative Anleger geeignet.")
    else:
        print("   → Die 2-Stufen-Strategie bleibt die bevorzugte Wahl.")

# =============================================================================
# 5. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE 3-STUFEN-ENSEMBLE")
    print("=" * 80)
    
    # Daten laden
    vix_signals, hmm_labels, returns = load_data()
    
    # 3-Stufen-Ensemble generieren
    three_step_signals = generate_3step_signals(vix_signals, hmm_labels)
    
    # Performance berechnen
    print("\n📊 Berechne Performance...")
    
    vix_perf = calculate_performance(vix_signals, returns, "VIX")
    
    hmm_signals = pd.DataFrame(index=hmm_labels.index)
    hmm_signals['position'] = hmm_labels['state'].map({0: 0.0, 1: 0.5, 2: 1.0}).fillna(0.0)
    hmm_perf = calculate_performance(hmm_signals, returns, "HMM")
    
    # 2-Stufen-Ensemble (aus vorheriger Datei)
    vix_bull = vix_signals['position'] > 0.7
    hmm_bull = hmm_labels['state'] == 2
    ensemble_signals = pd.DataFrame(index=vix_signals.index)
    ensemble_signals['position'] = (vix_bull & hmm_bull).astype(float)
    ensemble_perf = calculate_performance(ensemble_signals, returns, "Ensemble")
    
    # 3-Stufen-Ensemble
    three_step_perf = calculate_performance(three_step_signals, returns, "3-Stufen")
    
    # Vergleich
    print_comparison(vix_perf, hmm_perf, ensemble_perf, three_step_perf)
    
    # Speichern
    three_step_signals.to_csv(OUTPUT_DIR / 'ensemble_3step_signals.csv')
    print(f"\n💾 3-Stufen-Signale gespeichert: {OUTPUT_DIR / 'ensemble_3step_signals.csv'}")
    
    print("\n" + "=" * 80)
    print("🏁 3-STUFEN-ENSEMBLE ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
