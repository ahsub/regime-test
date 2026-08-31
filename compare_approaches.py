"""
compare_approaches.py – Vergleich classify_regime_v2() vs. 3-Stufen-Ensemble
============================================================================

Dieses Skript vergleicht zwei Ansätze auf dem gleichen Datensatz:
1. Ihre classify_regime_v2() (VIX + VIX3M + GEX)
2. Unser 3-Stufen-Ensemble (VIX-Strategie + Rolling HMM)

Zeitraum: 2011–2026 (3734 gemeinsame Tage)
Metriken: Sharpe Ratio, Drawdown, Rendite, Trades
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
# 1. Ihre classify_regime_v2() Logik
# =============================================================================

def classify_regime_v2(vix, vix3m, gex):
    """
    Ihre original classify_regime_v2() aus market_aggregator.py
    """
    if vix is None or vix3m is None or vix <= 0:
        return "NEUTRAL", None
    ratio = round(vix3m / vix, 3)
    if ratio < 0.98:
        regime = "STRESS_UNSTABLE"
    elif ratio < 1.05:
        regime = "POST_PANIC_REVERSION"
    else:
        regime = "BULL_FRAGILE" if vix > 25 else "BULL_QUIET"
        if gex is not None and gex < 0:
            regime = "STRESS_UNSTABLE"   # Override nur bei BULL_*
    return regime, ratio

# =============================================================================
# 2. Positionslogik für Ihre Regime
# =============================================================================

def regime_to_position(regime):
    """
    Mappt Ihre 5 Regime auf Positionsgrößen.
    """
    mapping = {
        "STRESS_UNSTABLE": 0.0,
        "POST_PANIC_REVERSION": 1.0,
        "BULL_FRAGILE": 0.7,
        "BULL_QUIET": 1.0,
        "NEUTRAL": 0.5
    }
    return mapping.get(regime, 0.0)

# =============================================================================
# 3. DATEN LADEN (gleiche Basis wie 3-Stufen-Ensemble)
# =============================================================================

def load_data():
    """Lädt die gleichen Daten wie das 3-Stufen-Ensemble."""
    print("📊 Lade Daten...")
    
    # 1. VIX-Signale (für Positionen)
    vix_signals = pd.read_csv(OUTPUT_DIR / 'trading_signals.csv', index_col=0, parse_dates=True)
    vix_signals.index = pd.to_datetime(vix_signals.index).tz_localize(None)
    
    # 2. HMM-Labels (für 3-Stufen-Ensemble)
    hmm_labels = pd.read_csv(OUTPUT_DIR / 'rolling_hmm_enhanced_labels.csv', index_col=0, parse_dates=True)
    hmm_labels.index = pd.to_datetime(hmm_labels.index).tz_localize(None)
    
    # 3. Rohdaten für Ihre Logik (VIX, VIX3M, GEX)
    market_data = pd.read_csv(DATA_DIR / "market_data.csv", index_col=0, parse_dates=True)
    
    # 4. S&P 500 Renditen
    sp500 = yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    returns.index = pd.to_datetime(returns.index).tz_localize(None)
    if isinstance(returns, pd.DataFrame):
        returns = returns.squeeze()
    
    # Gemeinsame Tage
    common_dates = vix_signals.index.intersection(hmm_labels.index).intersection(returns.index)
    common_dates = common_dates.intersection(market_data.index)
    
    vix_signals = vix_signals.loc[common_dates]
    hmm_labels = hmm_labels.loc[common_dates]
    returns = returns.loc[common_dates]
    market_data = market_data.loc[common_dates]
    
    print(f"   ✅ {len(common_dates)} gemeinsame Tage gefunden")
    
    return vix_signals, hmm_labels, returns, market_data

# =============================================================================
# 4. IHRE STRATEGIE
# =============================================================================

def your_strategy_signals(market_data):
    """Generiert Signale basierend auf classify_regime_v2()."""
    print("\n🔧 Generiere Ihre Strategie-Signale...")
    
    signals = pd.DataFrame(index=market_data.index)
    signals['regime'] = 'NEUTRAL'
    signals['ratio'] = None
    signals['position'] = 0.0
    
    for i, row in market_data.iterrows():
        vix = row.get('VIX', None)
        vix3m = row.get('VIX3M', None)
        gex = row.get('GEX', None)
        
        regime, ratio = classify_regime_v2(vix, vix3m, gex)
        signals.loc[i, 'regime'] = regime
        signals.loc[i, 'ratio'] = ratio
        signals.loc[i, 'position'] = regime_to_position(regime)
    
    print(f"   ✅ Signale generiert")
    print(f"   📊 Regime-Verteilung:")
    for regime in signals['regime'].value_counts().index:
        count = signals['regime'].value_counts()[regime]
        print(f"      {regime}: {count} ({count/len(signals)*100:.1f}%)")
    
    return signals

# =============================================================================
# 5. 3-STUFEN-ENSEMBLE (zum Vergleich)
# =============================================================================

def ensemble_3step_signals(vix_signals, hmm_labels):
    """Generiert die 3-Stufen-Ensemble-Signale."""
    print("\n🔧 Generiere 3-Stufen-Ensemble-Signale...")
    
    # Aggressive Parameter
    vix_bull = vix_signals['position'] > 0.85
    vix_bull_confirmed = vix_bull.rolling(3).sum() >= 3
    
    hmm_bull = hmm_labels['state'] == 2
    
    position = pd.Series(0.0, index=vix_signals.index)
    position[vix_bull_confirmed & hmm_bull] = 1.0
    position[vix_bull_confirmed & ~hmm_bull] = 0.5
    
    signals = pd.DataFrame(index=vix_signals.index)
    signals['position'] = position
    signals['regime'] = 'CASH'
    signals.loc[position == 1.0, 'regime'] = 'BULL_BULL'
    signals.loc[position == 0.5, 'regime'] = 'BULL_ONLY'
    
    print(f"   ✅ Signale generiert")
    print(f"   📊 Ø Position: {position.mean()*100:.1f}%")
    print(f"   📊 Tage mit 100%: {(position == 1.0).sum():.0f}")
    print(f"   📊 Tage mit 50%:  {(position == 0.5).sum():.0f}")
    print(f"   📊 Tage mit 0%:   {(position == 0.0).sum():.0f}")
    
    return signals

# =============================================================================
# 6. PERFORMANCE-BERECHNUNG
# =============================================================================

def calculate_performance(signals, returns, name):
    """Berechnet die Performance einer Strategie."""
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    if len(signals_aligned) < 10:
        return {'total_return': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown': 0.0,
                'num_trades': 0, 'avg_position': 0.0, 'n_days': 0}
    
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
    
    return {
        'total_return': float(last_strategy - 1),
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(dd_min) if dd_min is not None else 0.0,
        'num_trades': int((positions != positions.shift(1)).sum()),
        'avg_position': float(positions.mean()) if len(positions) > 0 else 0.0,
        'n_days': len(positions)
    }

# =============================================================================
# 7. TABELLARISCHER REPORT
# =============================================================================

def print_comparison(your_perf, ensemble_perf):
    """Gibt einen tabellarischen Vergleich aus."""
    print("\n" + "=" * 80)
    print("📊 VERGLEICH: Ihre classify_regime_v2() vs. 3-Stufen-Ensemble")
    print("=" * 80)
    
    print(f"\n{'Kennzahl':<25} | {'Ihre Strategie':<20} | {'3-Stufen-Ensemble':<20} | {'Differenz':<15}")
    print("-" * 85)
    
    # Rendite
    ret_diff = your_perf['total_return'] - ensemble_perf['total_return']
    print(f"{'Gesamtrendite':<25} | {your_perf['total_return']:>19.2%} | {ensemble_perf['total_return']:>19.2%} | {ret_diff:>+14.2%}")
    
    # Sharpe Ratio
    sr_diff = your_perf['sharpe_ratio'] - ensemble_perf['sharpe_ratio']
    print(f"{'Sharpe Ratio':<25} | {your_perf['sharpe_ratio']:>19.2f} | {ensemble_perf['sharpe_ratio']:>19.2f} | {sr_diff:>+14.2f}")
    
    # Drawdown
    dd_diff = your_perf['max_drawdown'] - ensemble_perf['max_drawdown']
    print(f"{'Max. Drawdown':<25} | {your_perf['max_drawdown']:>19.2%} | {ensemble_perf['max_drawdown']:>19.2%} | {dd_diff:>+14.2%}")
    
    # Trades
    trades_diff = your_perf['num_trades'] - ensemble_perf['num_trades']
    print(f"{'Anzahl Trades':<25} | {your_perf['num_trades']:>19} | {ensemble_perf['num_trades']:>19} | {trades_diff:>+14}")
    
    # Position
    pos_diff = your_perf['avg_position'] - ensemble_perf['avg_position']
    print(f"{'Ø Position':<25} | {your_perf['avg_position']:>19.1%} | {ensemble_perf['avg_position']:>19.1%} | {pos_diff:>+14.1%}")
    
    # Tage
    print(f"{'Tage':<25} | {your_perf['n_days']:>19} | {ensemble_perf['n_days']:>19} | {ensemble_perf['n_days'] - your_perf['n_days']:>+14}")
    
    # Fazit
    print("\n" + "=" * 80)
    print("📋 FAZIT")
    print("=" * 80)
    
    sr_your = your_perf['sharpe_ratio']
    sr_ens = ensemble_perf['sharpe_ratio']
    dd_your = your_perf['max_drawdown']
    dd_ens = ensemble_perf['max_drawdown']
    ret_your = your_perf['total_return']
    ret_ens = ensemble_perf['total_return']
    
    if sr_your > sr_ens:
        print(f"✅ Ihre Strategie hat die bessere Sharpe Ratio: {sr_your:.2f} vs. {sr_ens:.2f} (+{(sr_your-sr_ens)*100:.1f}%)")
    else:
        print(f"⚠️ Das 3-Stufen-Ensemble hat die bessere Sharpe Ratio: {sr_ens:.2f} vs. {sr_your:.2f} (+{(sr_ens-sr_your)*100:.1f}%)")
    
    if dd_your > dd_ens:
        print(f"✅ Ihre Strategie hat den geringeren Drawdown: {dd_your:.2%} vs. {dd_ens:.2%}")
    else:
        print(f"⚠️ Das 3-Stufen-Ensemble hat den geringeren Drawdown: {dd_ens:.2%} vs. {dd_your:.2%}")
    
    if ret_your > ret_ens:
        print(f"✅ Ihre Strategie hat die höhere Rendite: {ret_your:.2%} vs. {ret_ens:.2%} (+{(ret_your-ret_ens)*100:.1f}%)")
    else:
        print(f"⚠️ Das 3-Stufen-Ensemble hat die höhere Rendite: {ret_ens:.2%} vs. {ret_your:.2%} (+{(ret_ens-ret_your)*100:.1f}%)")
    
    # Empfehlung
    print("\n💡 EMPFEHLUNG:")
    if sr_your > sr_ens and dd_your > dd_ens:
        print("   → Ihre Strategie ist in beiden Dimensionen überlegen!")
        print("   → Sie sollte als Hauptstrategie verwendet werden.")
    elif sr_your > sr_ens:
        print("   → Ihre Strategie hat eine bessere Sharpe Ratio, aber höheren Drawdown.")
        print("   → Sie eignet sich für renditeorientierte Anleger.")
    elif dd_your > dd_ens:
        print("   → Ihre Strategie hat einen geringeren Drawdown, aber niedrigere Sharpe Ratio.")
        print("   → Sie eignet sich für konservative Anleger.")
    else:
        print("   → Das 3-Stufen-Ensemble ist in beiden Dimensionen überlegen.")
        print("   → Es sollte als Hauptstrategie verwendet werden.")

# =============================================================================
# 8. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE VERGLEICH: classify_regime_v2() vs. 3-Stufen-Ensemble")
    print("=" * 80)
    
    # Daten laden
    vix_signals, hmm_labels, returns, market_data = load_data()
    
    # Ihre Strategie
    your_signals = your_strategy_signals(market_data)
    your_perf = calculate_performance(your_signals, returns, "Ihre Strategie")
    
    # 3-Stufen-Ensemble
    ensemble_signals = ensemble_3step_signals(vix_signals, hmm_labels)
    ensemble_perf = calculate_performance(ensemble_signals, returns, "3-Stufen-Ensemble")
    
    # Vergleich
    print_comparison(your_perf, ensemble_perf)
    
    # Speichern
    your_signals.to_csv(OUTPUT_DIR / 'compare_your_strategy_signals.csv')
    print(f"\n💾 Ihre Signale gespeichert: {OUTPUT_DIR / 'compare_your_strategy_signals.csv'}")
    
    print("\n" + "=" * 80)
    print("🏁 VERGLEICH ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
