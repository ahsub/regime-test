"""
compare_approaches_final_v2.py – Fairer Vergleich mit korrigierter DSR-Formel
==============================================================================

Korrekturen:
1. Kurtosis: scipy.stats.kurtosis() gibt Exzess-Kurtosis zurück (Normalverteilung = 0)
   → Kein weiteres -3 in der Lo-Formel, da diese bereits die Exzess-Kurtosis erwartet.
2. n_trials = len(candidate_sharpes) für konsistente Mehrfachtest-Korrektur
3. Beide Strategien mit identischer 0/50/100-Positionslogik
4. Expositions-Normierung ohne Division-durch-Null (direkte Skalierung)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import yfinance as yf
from scipy.stats import norm, skew, kurtosis
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# 1. Ihre classify_regime_v2() Logik
# =============================================================================

def classify_regime_v2(vix, vix3m, gex):
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
            regime = "STRESS_UNSTABLE"
    return regime, ratio

def regime_to_position_uniform(regime):
    """Einheitliche 0/50/100-Positionslogik für beide Klassifikatoren."""
    mapping = {
        "STRESS_UNSTABLE": 0.0,
        "POST_PANIC_REVERSION": 1.0,
        "BULL_FRAGILE": 0.5,
        "BULL_QUIET": 1.0,
        "NEUTRAL": 0.5
    }
    return mapping.get(regime, 0.0)

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data():
    print("📊 Lade Daten...")

    vix_signals = pd.read_csv(OUTPUT_DIR / 'trading_signals.csv', index_col=0, parse_dates=True)
    vix_signals.index = pd.to_datetime(vix_signals.index).tz_localize(None)

    hmm_labels = pd.read_csv(OUTPUT_DIR / 'rolling_hmm_enhanced_labels.csv', index_col=0, parse_dates=True)
    hmm_labels.index = pd.to_datetime(hmm_labels.index).tz_localize(None)

    market_data = pd.read_csv(DATA_DIR / "market_data.csv", index_col=0, parse_dates=True)

    sp500 = yf.download('^GSPC', start='2011-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    returns.index = pd.to_datetime(returns.index).tz_localize(None)
    if isinstance(returns, pd.DataFrame):
        returns = returns.squeeze()

    common_dates = vix_signals.index.intersection(hmm_labels.index).intersection(returns.index)
    common_dates = common_dates.intersection(market_data.index)

    vix_signals = vix_signals.loc[common_dates]
    hmm_labels = hmm_labels.loc[common_dates]
    returns = returns.loc[common_dates]
    market_data = market_data.loc[common_dates]

    print(f"   ✅ {len(common_dates)} gemeinsame Tage gefunden")
    return vix_signals, hmm_labels, returns, market_data

# =============================================================================
# 3. STRATEGIE-FUNKTIONEN
# =============================================================================

def your_strategy_signals(market_data):
    print("\n🔧 Generiere Ihre Strategie-Signale (uniforme 0/50/100-Logik)...")
    signals = pd.DataFrame(index=market_data.index)
    signals['regime'] = 'NEUTRAL'
    signals['position'] = 0.0

    for i, row in market_data.iterrows():
        vix = row.get('VIX', None)
        vix3m = row.get('VIX3M', None)
        gex = row.get('GEX', None)
        regime, _ = classify_regime_v2(vix, vix3m, gex)
        signals.loc[i, 'regime'] = regime
        signals.loc[i, 'position'] = regime_to_position_uniform(regime)

    print(f"   ✅ Signale generiert")
    return signals

def ensemble_3step_signals(vix_signals, hmm_labels):
    print("\n🔧 Generiere 3-Stufen-Ensemble-Signale...")
    vix_bull = vix_signals['position'] > 0.85
    vix_bull_confirmed = vix_bull.rolling(3).sum() >= 3
    hmm_bull = hmm_labels['state'] == 2

    position = pd.Series(0.0, index=vix_signals.index)
    position[vix_bull_confirmed & hmm_bull] = 1.0
    position[vix_bull_confirmed & ~hmm_bull] = 0.5

    signals = pd.DataFrame(index=vix_signals.index)
    signals['position'] = position

    print(f"   ✅ Signale generiert")
    return signals

# =============================================================================
# 4. PERFORMANCE-BERECHNUNG
# =============================================================================

def calculate_performance(signals, returns, name):
    common_dates = signals.index.intersection(returns.index)
    signals_aligned = signals.loc[common_dates]
    returns_aligned = returns.loc[common_dates]

    if len(signals_aligned) < 10:
        return {'total_return': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown': 0.0,
                'num_trades': 0, 'avg_position': 0.0, 'n_days': 0,
                'strategy_returns': pd.Series()}

    positions = signals_aligned['position'].shift(1).fillna(0)
    strategy_returns = positions * returns_aligned
    strategy_cum = (1 + strategy_returns).cumprod()

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
        'n_days': len(positions),
        'strategy_returns': strategy_returns,
        'positions': positions
    }

# =============================================================================
# 5. KORREKTE DSR-FORMEL (Bailey & López de Prado, 2014)
# =============================================================================

def deflated_sharpe_ratio(strategy_returns, candidate_sharpes, n_trials=None, confidence=0.95):
    """
    Berechnet die Deflated Sharpe Ratio (DSR) nach Bailey & López de Prado (2014).

    KORREKTUREN:
    - scipy.stats.kurtosis() gibt Exzess-Kurtosis zurück → kein zusätzliches -3
    - n_trials = len(candidate_sharpes) für konsistente Mehrfachtest-Korrektur
    """
    if n_trials is None:
        n_trials = len(candidate_sharpes)

    n = len(strategy_returns)
    if n < 10 or n_trials < 1:
        return {'dsr': 0.0, 'is_significant': False}

    # 1. Rohe Sharpe Ratio
    excess_returns = strategy_returns - 0.02/252
    sr = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0

    # 2. Schiefe und Exzess-Kurtosis der Renditen
    # scipy.stats.kurtosis() mit fisher=True (Default) gibt Exzess-Kurtosis zurück
    # Normalverteilung → 0, also kein zusätzliches -3 in der Lo-Formel!
    skewness = skew(strategy_returns) if len(strategy_returns) > 0 else 0
    excess_kurtosis = kurtosis(strategy_returns, fisher=True) if len(strategy_returns) > 0 else 0

    # 3. Standardfehler der Sharpe Ratio (Lo, 2002)
    # Formel erwartet Exzess-Kurtosis (Normalverteilung → 0)
    se_sr = np.sqrt(
        (1 + 0.5 * sr**2 - skewness * sr + excess_kurtosis / 4 * sr**2) / n
    )

    # 4. Erwartete maximale Sharpe unter Mehrfachtest-Korrektur
    # Bailey & López de Prado (2014), Abschnitt 4.2
    if len(candidate_sharpes) > 0:
        var_sharpes = np.var(candidate_sharpes)
        var_sharpes = max(var_sharpes, 0.0001)  # Vermeidung von sqrt(0)
    else:
        var_sharpes = se_sr ** 2

    # sr_star = sqrt(2 * var_sharpes * log(n_trials))
    sr_star = np.sqrt(2 * var_sharpes * np.log(n_trials))

    # 5. Probabilistic Sharpe Ratio (PSR)
    if se_sr > 0:
        psr = norm.cdf((sr - sr_star) / se_sr)
    else:
        psr = 1.0 if sr > sr_star else 0.0

    return {
        'sharpe_ratio': sr,
        'psr': psr,
        'dsr': psr,
        'sr_star': sr_star,
        'se_sr': se_sr,
        'is_significant': psr >= confidence,
        'n_trials': n_trials,
        'confidence': confidence
    }

# =============================================================================
# 6. EXPOSTIONS-NORMIERUNG (OHNE DIVISION-DURCH-NULL)
# =============================================================================

def normalized_performance(strategy_returns, positions, target_position=0.75):
    """
    Normiert die Strategie auf eine Zielposition.
    KORREKT: Direkte Skalierung der Strategie-Renditen.
    """
    avg_pos = positions.mean()
    if avg_pos == 0:
        return {'normalized_return': 0.0, 'normalized_sharpe': 0.0, 'scaling_factor': 0.0}

    scaling = target_position / avg_pos
    scaled_returns = strategy_returns * scaling

    total_return = (1 + scaled_returns).prod() - 1
    excess_returns = scaled_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0

    return {
        'normalized_return': float(total_return),
        'normalized_sharpe': float(sharpe),
        'scaling_factor': float(scaling),
        'avg_position': avg_pos
    }

# =============================================================================
# 7. FAIRER VERGLEICH
# =============================================================================

def print_fair_comparison(your_perf, ensemble_perf, candidate_sharpes):
    """Fairer Vergleich mit korrekter DSR-Formel."""
    print("\n" + "=" * 80)
    print("📊 FAIRER VERGLEICH: classify_regime_v2() vs. 3-Stufen-Ensemble")
    print("=" * 80)

    # 1. DSR mit korrekter Formel
    dsr_your = deflated_sharpe_ratio(
        your_perf['strategy_returns'],
        candidate_sharpes,
        n_trials=len(candidate_sharpes)
    )
    dsr_ens = deflated_sharpe_ratio(
        ensemble_perf['strategy_returns'],
        candidate_sharpes,
        n_trials=len(candidate_sharpes)
    )

    # 2. Exposition normieren (ohne Division-durch-Null)
    norm_your = normalized_performance(
        your_perf['strategy_returns'],
        your_perf['positions'],
        target_position=0.75
    )
    norm_ens = normalized_performance(
        ensemble_perf['strategy_returns'],
        ensemble_perf['positions'],
        target_position=0.75
    )

    print(f"\n{'Kennzahl':<35} | {'Ihre Strategie':<20} | {'3-Stufen-Ensemble':<20} | {'Vergleich':<15}")
    print("-" * 95)

    print(f"{'Gesamtrendite (roh)':<35} | {your_perf['total_return']:>19.2%} | {ensemble_perf['total_return']:>19.2%} | {your_perf['total_return'] - ensemble_perf['total_return']:>+14.2%}")
    print(f"{'Sharpe Ratio (roh)':<35} | {your_perf['sharpe_ratio']:>19.2f} | {ensemble_perf['sharpe_ratio']:>19.2f} | {your_perf['sharpe_ratio'] - ensemble_perf['sharpe_ratio']:>+14.2f}")
    print(f"{'Max. Drawdown':<35} | {your_perf['max_drawdown']:>19.2%} | {ensemble_perf['max_drawdown']:>19.2%} | {your_perf['max_drawdown'] - ensemble_perf['max_drawdown']:>+14.2%}")
    print(f"{'Ø Position':<35} | {your_perf['avg_position']:>19.1%} | {ensemble_perf['avg_position']:>19.1%} | {your_perf['avg_position'] - ensemble_perf['avg_position']:>+14.1%}")
    print(f"{'Anzahl Trades':<35} | {your_perf['num_trades']:>19} | {ensemble_perf['num_trades']:>19} | {your_perf['num_trades'] - ensemble_perf['num_trades']:>+14}")

    print(f"\n{'📉 DEFLATED SHARPE RATIO (Bailey & López de Prado)':<35} | {'':<20} | {'':<20} | {'':<15}")
    print(f"{'Kandidaten-Sharpes':<35} | {str(candidate_sharpes):>19} | {'':<20} | {'':<15}")
    print(f"{'n_trials (Kandidaten)':<35} | {len(candidate_sharpes):>19} | {len(candidate_sharpes):>19} | {'':<15}")
    print(f"{'DSR (95% Konfidenz)':<35} | {dsr_your['dsr']:>19.2f} | {dsr_ens['dsr']:>19.2f} | {dsr_your['dsr'] - dsr_ens['dsr']:>+14.2f}")
    print(f"{'Signifikant (≥0.95)':<35} | {str(dsr_your['is_significant']):>19} | {str(dsr_ens['is_significant']):>19} | {'':<15}")
    print(f"{'SR* (erw. max. Sharpe)':<35} | {dsr_your['sr_star']:>19.2f} | {dsr_ens['sr_star']:>19.2f} | {dsr_your['sr_star'] - dsr_ens['sr_star']:>+14.2f}")

    print(f"\n{'📊 EXPOSITIONS-NORMIERT (75% Zielposition)':<35} | {'':<20} | {'':<20} | {'':<15}")
    print(f"{'Normalisierte Rendite':<35} | {norm_your['normalized_return']:>19.2%} | {norm_ens['normalized_return']:>19.2%} | {norm_your['normalized_return'] - norm_ens['normalized_return']:>+14.2%}")
    print(f"{'Normalisierte Sharpe':<35} | {norm_your['normalized_sharpe']:>19.2f} | {norm_ens['normalized_sharpe']:>19.2f} | {norm_your['normalized_sharpe'] - norm_ens['normalized_sharpe']:>+14.2f}")
    print(f"{'Skalierungsfaktor':<35} | {norm_your['scaling_factor']:>19.2f} | {norm_ens['scaling_factor']:>19.2f} | {norm_your['scaling_factor'] - norm_ens['scaling_factor']:>+14.2f}")

    # Fazit
    print("\n" + "=" * 80)
    print("📋 FAZIT (mit korrekter DSR-Formel)")
    print("=" * 80)

    if dsr_your['is_significant'] and dsr_ens['is_significant']:
        print("✅ Beide Strategien sind statistisch signifikant (DSR ≥ 0.95).")
    elif dsr_your['is_significant'] and not dsr_ens['is_significant']:
        print("✅ Ihre Strategie ist statistisch signifikant, das Ensemble nicht.")
        print("   → Ihre Strategie ist robuster.")
    elif not dsr_your['is_significant'] and dsr_ens['is_significant']:
        print("✅ Das Ensemble ist statistisch signifikant, Ihre Strategie nicht.")
        print("   → Das Ensemble ist robuster.")
    else:
        print("⚠️ Keine der Strategien ist statistisch signifikant (DSR < 0.95).")
        print("   → Die Ergebnisse könnten auf Überoptimierung zurückzuführen sein.")

    print(f"\n📊 Expositions-bereinigter Vergleich (gleiche Ø-Position):")
    if norm_your['normalized_sharpe'] > norm_ens['normalized_sharpe']:
        print(f"   ✅ Ihre Strategie hat bessere risikobereinigte Rendite: {norm_your['normalized_sharpe']:.2f} vs. {norm_ens['normalized_sharpe']:.2f}")
    else:
        print(f"   ✅ Das Ensemble hat bessere risikobereinigte Rendite: {norm_ens['normalized_sharpe']:.2f} vs. {norm_your['normalized_sharpe']:.2f}")

    print(f"\n💡 EMPFEHLUNG:")
    if dsr_your['is_significant'] and dsr_ens['is_significant']:
        print("   → Beide Strategien sind robust. Ihre Strategie hat die höhere rohe Sharpe Ratio,")
        print("     das Ensemble den geringeren Drawdown. Wahl hängt von Ihrer Risikopräferenz ab.")
    elif dsr_your['is_significant']:
        print("   → Ihre Strategie ist die einzig statistisch signifikante Wahl.")
        print("   → Sie sollte als Hauptstrategie verwendet werden.")
    elif dsr_ens['is_significant']:
        print("   → Das Ensemble ist die einzig statistisch signifikante Wahl.")
        print("   → Es sollte als Hauptstrategie verwendet werden.")
    else:
        print("   → Keine der Strategien ist statistisch robust.")
        print("   → Eine grundlegende Überarbeitung oder eine längere Backtest-Zeitreihe wird empfohlen.")

# =============================================================================
# 8. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 80)
    print("📈 STARTE FAIREN VERGLEICH (finale korrigierte DSR-Formel)")
    print("=" * 80)

    # Daten laden
    vix_signals, hmm_labels, returns, market_data = load_data()

    # Ihre Strategie
    your_signals = your_strategy_signals(market_data)
    your_perf = calculate_performance(your_signals, returns, "Ihre Strategie")

    # 3-Stufen-Ensemble
    ensemble_signals = ensemble_3step_signals(vix_signals, hmm_labels)
    ensemble_perf = calculate_performance(ensemble_signals, returns, "3-Stufen-Ensemble")

    # Alle Kandidaten-Sharpes aus bisherigen Vergleichen
    # Achtung: Diese Werte müssen alle tatsächlich ausprobierten Varianten abbilden!
    # Quelle: Ihre Doku (0.76), unsere Backtests (0.60, 0.74, 0.25, 0.20)
    candidate_sharpes = [0.76, 0.60, 0.74, 0.25, 0.20]

    print(f"\n📋 Kandidaten-Sharpes (alle getesteten Modelle):")
    print(f"   {candidate_sharpes}")
    print(f"   → n_trials = {len(candidate_sharpes)}")

    # Fairer Vergleich
    print_fair_comparison(your_perf, ensemble_perf, candidate_sharpes)

    print("\n" + "=" * 80)
    print("🏁 FAIRER VERGLEICH ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == "__main__":
    main()
