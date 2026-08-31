"""
ensemble_strategy.py – Ensemble-Strategie (VIX + HMM) – ENDGÜLTIG FUNKTIONIEREND
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
    
    # Index glätten (falls MultiIndex)
    if isinstance(returns.index, pd.MultiIndex):
        returns.index = returns.index.get_level_values(0)
    returns.index = pd.to_datetime(returns.index).tz_localize(None)
    
    # Sicherstellen, dass returns eine Series ist (kein DataFrame)
    if isinstance(returns, pd.DataFrame):
        returns = returns.squeeze()
    
    print(f"   ✅ S&P 500 von Yahoo Finance geladen: {len(returns)} Tage")
    
    common_dates = vix_signals.index.intersection(hmm_labels.index).intersection(returns.index)
    vix_signals = vix_signals.loc[common_dates]
    hmm_labels = hmm_labels.loc[common_dates]
    returns = returns.loc[common_dates]
    
    print(f"   ✅ {len(common_dates)} gemeinsame Tage gefunden")
    return vix_signals, hmm_labels, returns

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

def main():
    print("=" * 80)
    print("📈 STARTE ENSEMBLE-STRATEGIE (ENDGÜLTIG)")
    print("=" * 80)
    
    vix_signals, hmm_labels, returns = load_data()
    
    print("\n🔧 Generiere Ensemble-Signale...")
    vix_bull = vix_signals['position'] > 0.7
    hmm_bull = hmm_labels['state'] == 2
    ensemble_bull = vix_bull & hmm_bull
    
    ensemble_signals = pd.DataFrame(index=vix_signals.index)
    ensemble_signals['position'] = ensemble_bull.astype(float)
    
    print(f"   ✅ Ensemble-Signale generiert")
    print(f"   📊 Tage investiert: {ensemble_signals['position'].sum():.0f} ({ensemble_signals['position'].mean()*100:.1f}%)")
    
    print("\n📊 Berechne Performance...")
    
    vix_perf = calculate_performance(vix_signals, returns, "VIX")
    hmm_signals = pd.DataFrame(index=hmm_labels.index)
    hmm_signals['position'] = hmm_labels['state'].map({0: 0.0, 1: 0.5, 2: 1.0}).fillna(0.0)
    hmm_perf = calculate_performance(hmm_signals, returns, "HMM")
    ensemble_perf = calculate_performance(ensemble_signals, returns, "Ensemble")
    
    print("\n" + "=" * 80)
    print("📊 ENSEMBLE-VERGLEICH")
    print("=" * 80)
    
    print(f"\n{'Kennzahl':<20} | {'VIX-Strategie':<18} | {'HMM-Strategie':<18} | {'Ensemble':<18}")
    print("-" * 80)
    print(f"{'Gesamtrendite':<20} | {vix_perf['total_return_strategy']:>17.2%} | {hmm_perf['total_return_strategy']:>17.2%} | {ensemble_perf['total_return_strategy']:>17.2%}")
    print(f"{'Sharpe Ratio':<20} | {vix_perf['sharpe_ratio']:>17.2f} | {hmm_perf['sharpe_ratio']:>17.2f} | {ensemble_perf['sharpe_ratio']:>17.2f}")
    print(f"{'Max. Drawdown':<20} | {vix_perf['max_drawdown']:>17.2%} | {hmm_perf['max_drawdown']:>17.2%} | {ensemble_perf['max_drawdown']:>17.2%}")
    print(f"{'Anzahl Trades':<20} | {vix_perf['num_trades']:>17} | {hmm_perf['num_trades']:>17} | {ensemble_perf['num_trades']:>17}")
    print(f"{'Ø Position':<20} | {vix_perf['avg_position']:>17.1%} | {hmm_perf['avg_position']:>17.1%} | {ensemble_perf['avg_position']:>17.1%}")
    print(f"{'Tage':<20} | {vix_perf['n_days']:>17} | {hmm_perf['n_days']:>17} | {ensemble_perf['n_days']:>17}")
    
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
    
    ensemble_signals.to_csv(OUTPUT_DIR / 'ensemble_signals.csv')
    print(f"\n💾 Ensemble-Signale gespeichert: {OUTPUT_DIR / 'ensemble_signals.csv'}")
    
    print("\n" + "=" * 80)
    print("🏁 ENSEMBLE-STRATEGIE ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
