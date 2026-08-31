"""
transaction_costs.py – Transaktionskosten-Test für 3-Stufen-Ensemble
====================================================================

Dieses Skript testet die 3-Stufen-Ensemble-Strategie mit realistischen
Transaktionskosten (Spread + Slippage).

Parameter:
- Spread: 0.05% (5 Basispunkte) pro Trade
- Slippage: 0.03% (3 Basispunkte) pro Trade
- Gesamtkosten pro Trade: 0.08% (8 Basispunkte)

Vergleich: Ohne Kosten vs. Mit Kosten
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

# Transaktionskosten-Parameter
SPREAD = 0.0005      # 0.05% Spread pro Trade
SLIPPAGE = 0.0003    # 0.03% Slippage pro Trade
COST_PER_TRADE = SPREAD + SLIPPAGE  # 0.08% pro Trade

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
    
    return signals

# =============================================================================
# 3. PERFORMANCE-BERECHNUNG (MIT/OHNE KOSTEN)
# =============================================================================

def safe_float(value):
    if isinstance(value, pd.Series):
        return float(value.iloc[0]) if len(value) > 0 else 0.0
    return float(value) if value is not None else 0.0

def calculate_performance_with_costs(signals, returns, name, cost_per_trade=0):
    """
    Berechnet die Performance mit Transaktionskosten.
    
    costs: Kosten pro Trade (z.B. 0.0008 für 0.08%)
    """
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {'total_return_strategy': 0.0, 'total_return_market': 0.0,
                'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'num_trades': 0,
                'avg_position': 0.0, 'n_days': 0, 'total_costs': 0.0}
    
    positions = signals_aligned['position'].shift(1).fillna(0)
    
    # Position-Änderungen erkennen (für Kosten)
    position_changes = (positions != positions.shift(1)).fillna(False).astype(int)
    num_trades = position_changes.sum()
    
    # Brutto-Renditen (ohne Kosten)
    gross_returns = positions * returns_aligned
    
    # Kosten pro Trade (nur wenn Position geändert wird)
    # Jeder Trade (Kauf oder Verkauf) verursacht Kosten
    costs = position_changes * cost_per_trade * 0.5  # 0.5 weil nur eine Seite des Trades?
    # Tatsächlich: Bei jedem Positionswechsel wird die gesamte Position umgeschichtet
    # Einfachere Methode: Kosten pro Trade als Prozentsatz der Positionsänderung
    position_diff = (positions - positions.shift(1)).abs()
    costs = position_diff * cost_per_trade
    
    # Netto-Renditen (mit Kosten)
    net_returns = gross_returns - costs
    
    # Kumulierte Renditen
    gross_cum = (1 + gross_returns).cumprod()
    net_cum = (1 + net_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    # Sharpe Ratio (Netto)
    excess_returns = net_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    # Drawdown (Netto)
    peak = net_cum.expanding().max()
    drawdown = (net_cum - peak) / peak
    dd_min = drawdown.min()
    if isinstance(dd_min, pd.Series):
        dd_min = dd_min.iloc[0] if len(dd_min) > 0 else 0.0
    
    last_gross = gross_cum.iloc[-1] if len(gross_cum) > 0 else 1.0
    last_net = net_cum.iloc[-1] if len(net_cum) > 0 else 1.0
    last_market = market_cum.iloc[-1] if len(market_cum) > 0 else 1.0
    
    return {
        'name': name,
        'total_return_gross': safe_float(last_gross) - 1,
        'total_return_net': safe_float(last_net) - 1,
        'total_return_market': safe_float(last_market) - 1,
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(dd_min) if dd_min is not None else 0.0,
        'num_trades': num_trades,
        'avg_position': float(positions.mean()) if len(positions) > 0 else 0.0,
        'n_days': len(positions),
        'total_costs': float(costs.sum())
    }

# =============================================================================
# 4. REPORT
# =============================================================================

def print_cost_comparison(no_cost_perf, cost_perf):
    print("\n" + "=" * 80)
    print("📊 TRANSaktIONSKOSTEN-VERGLEICH (3-STUFEN-ENSEMBLE)")
    print("=" * 80)
    print(f"\n💰 Transaktionskosten-Parameter:")
    print(f"   Spread:   {SPREAD*100:.2f}%")
    print(f"   Slippage: {SLIPPAGE*100:.2f}%")
    print(f"   Gesamt:   {COST_PER_TRADE*100:.2f}% pro Trade")
    
    print(f"\n{'Kennzahl':<25} | {'Ohne Kosten':<18} | {'Mit Kosten':<18} | {'Differenz':<18}")
    print("-" * 85)
    
    # Rendite
    ret_diff = cost_perf['total_return_net'] - no_cost_perf['total_return_net']
    print(f"{'Gesamtrendite':<25} | {no_cost_perf['total_return_net']:>17.2%} | {cost_perf['total_return_net']:>17.2%} | {ret_diff:>17.2%}")
    
    # Sharpe Ratio
    sr_diff = cost_perf['sharpe_ratio'] - no_cost_perf['sharpe_ratio']
    print(f"{'Sharpe Ratio':<25} | {no_cost_perf['sharpe_ratio']:>17.2f} | {cost_perf['sharpe_ratio']:>17.2f} | {sr_diff:>+17.2f}")
    
    # Drawdown
    dd_diff = cost_perf['max_drawdown'] - no_cost_perf['max_drawdown']
    print(f"{'Max. Drawdown':<25} | {no_cost_perf['max_drawdown']:>17.2%} | {cost_perf['max_drawdown']:>17.2%} | {dd_diff:>17.2%}")
    
    # Trades
    trades_diff = cost_perf['num_trades'] - no_cost_perf['num_trades']
    print(f"{'Anzahl Trades':<25} | {no_cost_perf['num_trades']:>17} | {cost_perf['num_trades']:>17} | {trades_diff:>+17}")
    
    # Position
    pos_diff = cost_perf['avg_position'] - no_cost_perf['avg_position']
    print(f"{'Ø Position':<25} | {no_cost_perf['avg_position']:>17.1%} | {cost_perf['avg_position']:>17.1%} | {pos_diff:>17.1%}")
    
    # Tage
    print(f"{'Tage':<25} | {no_cost_perf['n_days']:>17} | {cost_perf['n_days']:>17} | {cost_perf['n_days'] - no_cost_perf['n_days']:>+17}")
    
    # Kosten (nur mit Kosten)
    print(f"{'Kosten (absolut)':<25} | {'-':>17} | {cost_perf['total_costs']:>17.4f} | {'-':>17}")
    
    # Prozentsatz der Kosten
    if no_cost_perf['total_return_net'] != 0:
        cost_pct = (cost_perf['total_costs'] / no_cost_perf['total_return_net']) * 100
        print(f"{'Kosten (% der Rendite)':<25} | {'-':>17} | {cost_pct:>17.2f}% | {'-':>17}")
    
    print("\n" + "=" * 80)
    print("📋 FAZIT")
    print("=" * 80)
    
    # Auswirkung der Kosten beurteilen
    sr_impact = (cost_perf['sharpe_ratio'] - no_cost_perf['sharpe_ratio']) / no_cost_perf['sharpe_ratio'] * 100 if no_cost_perf['sharpe_ratio'] > 0 else 0
    
    print(f"\n💰 Auswirkung der Transaktionskosten:")
    print(f"   Sharpe Ratio: {no_cost_perf['sharpe_ratio']:.2f} → {cost_perf['sharpe_ratio']:.2f} ({sr_impact:+.1f}%)")
    print(f"   Rendite:      {no_cost_perf['total_return_net']:.2%} → {cost_perf['total_return_net']:.2%}")
    print(f"   Drawdown:     {no_cost_perf['max_drawdown']:.2%} → {cost_perf['max_drawdown']:.2%}")
    
    # Empfehlung
    print("\n💡 EMPFEHLUNG:")
    if sr_impact > -5:
        print("   ✅ Die Transaktionskosten haben nur einen geringen Einfluss auf die Performance.")
        print("   → Die Strategie ist robust gegenüber Transaktionskosten und kann live eingesetzt werden.")
    elif sr_impact > -15:
        print("   ⚠️ Die Transaktionskosten haben einen moderaten Einfluss auf die Performance.")
        print("   → Die Strategie kann live eingesetzt werden, aber eine Optimierung der Trade-Frequenz wird empfohlen.")
    else:
        print("   ⚠️ Die Transaktionskosten haben einen erheblichen Einfluss auf die Performance.")
        print("   → Die Strategie sollte überarbeitet werden (weniger Trades, größere Schwellwerte).")

# =============================================================================
# 5. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE TRANSaktIONSKOSTEN-TEST")
    print("=" * 80)
    
    # Daten laden
    vix_signals, hmm_labels, returns = load_data()
    
    # 3-Stufen-Signale generieren
    signals = generate_3step_signals(vix_signals, hmm_labels)
    
    print(f"\n💰 Transaktionskosten-Parameter:")
    print(f"   Spread:   {SPREAD*100:.2f}%")
    print(f"   Slippage: {SLIPPAGE*100:.2f}%")
    print(f"   Gesamt:   {COST_PER_TRADE*100:.2f}% pro Trade")
    
    # Performance ohne Kosten
    print("\n📊 Berechne Performance ohne Kosten...")
    no_cost_perf = calculate_performance_with_costs(signals, returns, "Ohne Kosten", cost_per_trade=0)
    
    # Performance mit Kosten
    print("📊 Berechne Performance mit Kosten...")
    cost_perf = calculate_performance_with_costs(signals, returns, "Mit Kosten", cost_per_trade=COST_PER_TRADE)
    
    # Vergleich
    print_cost_comparison(no_cost_perf, cost_perf)
    
    # Ergebnisse speichern
    results = pd.DataFrame({
        'Kennzahl': ['Gesamtrendite', 'Sharpe Ratio', 'Max. Drawdown', 'Anzahl Trades', 'Ø Position', 'Tage', 'Kosten (absolut)'],
        'Ohne Kosten': [
            f"{no_cost_perf['total_return_net']:.2%}",
            f"{no_cost_perf['sharpe_ratio']:.2f}",
            f"{no_cost_perf['max_drawdown']:.2%}",
            no_cost_perf['num_trades'],
            f"{no_cost_perf['avg_position']:.1%}",
            no_cost_perf['n_days'],
            '-'
        ],
        'Mit Kosten': [
            f"{cost_perf['total_return_net']:.2%}",
            f"{cost_perf['sharpe_ratio']:.2f}",
            f"{cost_perf['max_drawdown']:.2%}",
            cost_perf['num_trades'],
            f"{cost_perf['avg_position']:.1%}",
            cost_perf['n_days'],
            f"{cost_perf['total_costs']:.4f}"
        ]
    })
    results.to_csv(OUTPUT_DIR / 'transaction_costs_results.csv', index=False)
    print(f"\n💾 Ergebnisse gespeichert: {OUTPUT_DIR / 'transaction_costs_results.csv'}")
    
    print("\n" + "=" * 80)
    print("🏁 TRANSaktIONSKOSTEN-TEST ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
