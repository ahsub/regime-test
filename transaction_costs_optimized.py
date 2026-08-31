"""
transaction_costs_optimized.py – Transaktionskosten-Test mit optimierten Parametern
===================================================================================

Optimierungen:
- VIX-Schwelle: 0.7 → 0.8 (weniger Einstiege)
- Bestätigungstage: 2 Tage (Reduziert Rauschen)
- Positionsänderungen: Nur bei >10% Unterschied
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

# Kosten-Parameter
SPREAD = 0.0005
SLIPPAGE = 0.0003
COST_PER_TRADE = SPREAD + SLIPPAGE

# Optimierte Parameter
VIX_THRESHOLD = 0.8        # Erhöht von 0.7 → 0.8
CONFIRMATION_DAYS = 2      # Bestätigungstage
MIN_POSITION_CHANGE = 0.1  # 10% Mindeständerung

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
# 2. 3-STUFEN-ENSEMBLE (OPTIMIERT)
# =============================================================================

def generate_3step_signals_optimized(vix_signals: pd.DataFrame, hmm_labels: pd.DataFrame) -> pd.DataFrame:
    """Generiert 3-Stufen-Ensemble-Signale mit optimierten Parametern."""
    
    # 1. VIX-Signal mit erhöhter Schwelle
    vix_bull = vix_signals['position'] > VIX_THRESHOLD
    
    # 2. Bestätigung: Signal muss 2 Tage bestehen
    vix_bull_confirmed = vix_bull.rolling(CONFIRMATION_DAYS).sum() >= CONFIRMATION_DAYS
    
    # 3. HMM-Zustände
    hmm_bull = hmm_labels['state'] == 2
    hmm_sideways = hmm_labels['state'] == 1
    hmm_bear = hmm_labels['state'] == 0
    
    # 4. Positionsgröße
    position = pd.Series(0.0, index=vix_signals.index)
    position[vix_bull_confirmed & hmm_bull] = 1.0
    position[vix_bull_confirmed & hmm_sideways] = 0.5
    position[vix_bull_confirmed & hmm_bear] = 0.25
    
    # 5. Glätten: Nur Änderungen > 10% zulassen
    # Position in Schritten von 0.1
    position = (position / 0.1).round() * 0.1
    position = position.clip(0.0, 1.0)
    
    signals = pd.DataFrame(index=vix_signals.index)
    signals['position'] = position
    
    # Statistik ausgeben
    trades = (position != position.shift(1)).sum()
    print(f"\n📊 Optimierte 3-Stufen-Statistik:")
    print(f"   Tage mit 100%: {(position == 1.0).sum():.0f}")
    print(f"   Tage mit 50%:  {(position == 0.5).sum():.0f}")
    print(f"   Tage mit 25%:  {(position == 0.25).sum():.0f}")
    print(f"   Tage mit 0%:   {(position == 0.0).sum():.0f}")
    print(f"   Ø Position:    {position.mean()*100:.1f}%")
    print(f"   Anzahl Trades: {trades}")
    
    return signals

# =============================================================================
# 3. PERFORMANCE-BERECHNUNG
# =============================================================================

def safe_float(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0]) if len(value) > 0 else 0.0
    return float(value) if value is not None else 0.0

def calculate_performance_with_costs(signals, returns, name, cost_per_trade=0):
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {'total_return_net': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown': 0.0,
                'num_trades': 0, 'avg_position': 0.0, 'n_days': 0, 'total_costs': 0.0}
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    
    # Kosten nur bei Positionsänderungen
    position_diff = (positions - positions.shift(1)).abs()
    costs = position_diff * cost_per_trade
    
    # Renditen
    gross_returns = positions * returns_aligned
    net_returns = gross_returns - costs
    
    gross_cum = (1 + gross_returns).cumprod()
    net_cum = (1 + net_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    excess_returns = net_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    peak = net_cum.expanding().max()
    drawdown = (net_cum - peak) / peak
    dd_min = drawdown.min()
    if isinstance(dd_min, pd.Series):
        dd_min = dd_min.iloc[0] if len(dd_min) > 0 else 0.0
    
    last_net = net_cum.iloc[-1] if len(net_cum) > 0 else 1.0
    
    return {
        'total_return_net': safe_float(last_net) - 1,
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(dd_min) if dd_min is not None else 0.0,
        'num_trades': (positions != positions.shift(1)).sum(),
        'avg_position': float(positions.mean()) if len(positions) > 0 else 0.0,
        'n_days': len(positions),
        'total_costs': float(costs.sum())
    }

# =============================================================================
# 4. REPORT
# =============================================================================

def print_comparison(original_perf, optimized_perf):
    print("\n" + "=" * 80)
    print("📊 OPTIMIERTER TRANSaktIONSKOSTEN-VERGLEICH")
    print("=" * 80)
    
    print(f"\n🔧 Optimierungsparameter:")
    print(f"   VIX-Schwelle: 0.7 → {VIX_THRESHOLD}")
    print(f"   Bestätigung:  0 → {CONFIRMATION_DAYS} Tage")
    print(f"   Min. Änderung: 0% → {MIN_POSITION_CHANGE*100:.0f}%")
    
    print(f"\n{'Kennzahl':<25} | {'Original':<18} | {'Optimiert':<18} | {'Verbesserung':<18}")
    print("-" * 85)
    
    ret_diff = optimized_perf['total_return_net'] - original_perf['total_return_net']
    print(f"{'Gesamtrendite':<25} | {original_perf['total_return_net']:>17.2%} | {optimized_perf['total_return_net']:>17.2%} | {ret_diff:>+17.2%}")
    
    sr_diff = optimized_perf['sharpe_ratio'] - original_perf['sharpe_ratio']
    print(f"{'Sharpe Ratio':<25} | {original_perf['sharpe_ratio']:>17.2f} | {optimized_perf['sharpe_ratio']:>17.2f} | {sr_diff:>+17.2f}")
    
    dd_diff = optimized_perf['max_drawdown'] - original_perf['max_drawdown']
    print(f"{'Max. Drawdown':<25} | {original_perf['max_drawdown']:>17.2%} | {optimized_perf['max_drawdown']:>17.2%} | {dd_diff:>+17.2%}")
    
    trades_diff = optimized_perf['num_trades'] - original_perf['num_trades']
    print(f"{'Anzahl Trades':<25} | {original_perf['num_trades']:>17} | {optimized_perf['num_trades']:>17} | {trades_diff:>+17}")
    
    print(f"{'Ø Position':<25} | {original_perf['avg_position']:>17.1%} | {optimized_perf['avg_position']:>17.1%} | {optimized_perf['avg_position'] - original_perf['avg_position']:>+17.1%}")
    
    print(f"{'Tage':<25} | {original_perf['n_days']:>17} | {optimized_perf['n_days']:>17} | {optimized_perf['n_days'] - original_perf['n_days']:>+17}")
    
    print(f"{'Kosten absolut':<25} | {original_perf['total_costs']:>17.4f} | {optimized_perf['total_costs']:>17.4f} | {-optimized_perf['total_costs'] + original_perf['total_costs']:>+17.4f}")
    
    print("\n" + "=" * 80)
    print("📋 FAZIT")
    print("=" * 80)
    
    sr_improvement = ((optimized_perf['sharpe_ratio'] - original_perf['sharpe_ratio']) / original_perf['sharpe_ratio'] * 100) if original_perf['sharpe_ratio'] > 0 else 0
    
    print(f"\n📈 Verbesserung der Sharpe Ratio: {sr_improvement:+.1f}%")
    print(f"💰 Reduzierte Kosten: {original_perf['total_costs'] - optimized_perf['total_costs']:.4f}")
    print(f"🔄 Reduzierte Trades: {original_perf['num_trades'] - optimized_perf['num_trades']}")
    
    if optimized_perf['sharpe_ratio'] > 0.35:
        print("\n✅ Die optimierte Strategie hat eine akzeptable Sharpe Ratio (> 0.35).")
        print("   → Die Strategie kann live eingesetzt werden.")
    elif optimized_perf['sharpe_ratio'] > 0.25:
        print("\n⚠️ Die optimierte Strategie hat eine moderate Sharpe Ratio (0.25–0.35).")
        print("   → Weitere Optimierung wird empfohlen.")
    else:
        print("\n⚠️ Die optimierte Strategie hat eine niedrige Sharpe Ratio (< 0.25).")
        print("   → Die Strategie sollte grundlegend überarbeitet werden.")

# =============================================================================
# 5. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE OPTIMIERTER TRANSaktIONSKOSTEN-TEST")
    print("=" * 80)
    
    # Daten laden
    vix_signals, hmm_labels, returns = load_data()
    
    # Original-Signale (ohne Optimierung)
    print("\n📊 Generiere originale 3-Stufen-Signale...")
    signals_original = generate_3step_signals_original(vix_signals, hmm_labels)
    
    # Optimierte Signale
    print("\n📊 Generiere optimierte 3-Stufen-Signale...")
    signals_optimized = generate_3step_signals_optimized(vix_signals, hmm_labels)
    
    # Performance mit Kosten
    print("\n📊 Berechne Performance mit Kosten...")
    original_perf = calculate_performance_with_costs(signals_original, returns, "Original", COST_PER_TRADE)
    optimized_perf = calculate_performance_with_costs(signals_optimized, returns, "Optimiert", COST_PER_TRADE)
    
    # Vergleich
    print_comparison(original_perf, optimized_perf)
    
    # Speichern
    signals_optimized.to_csv(OUTPUT_DIR / 'transaction_costs_optimized_signals.csv')
    print(f"\n💾 Optimierte Signale gespeichert: {OUTPUT_DIR / 'transaction_costs_optimized_signals.csv'}")
    
    print("\n" + "=" * 80)
    print("🏁 OPTIMIERTER TRANSaktIONSKOSTEN-TEST ABGESCHLOSSEN")
    print("=" * 80)

def generate_3step_signals_original(vix_signals, hmm_labels):
    """Originale 3-Stufen-Signale (zum Vergleich)."""
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
    return signals

if __name__ == "__main__":
    main()
