"""
rolling_hmm_enhanced.py – Rolling HMM mit erweiterten Features (VIX, VVIX, GEX, DIX)
====================================================================================

Dieses Skript erweitert das Rolling-HMM nach Pagliaro (2026) um zusätzliche Features:
- VIX (Volatilitätsindex)
- VVIX (Volatilität der Volatilität)
- GEX (Gamma Exposure)
- DIX (Dark Index)

Ziel: Verbesserung der Sharpe Ratio durch zusätzliche Informationsquellen.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from hmmlearn import hmm
import yfinance as yf
import json

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Parameter
RETRAIN_INTERVAL = 63          # Alle 63 Handelstage neu fitten
CONTEXT_WINDOW = 120           # 120-Tage-Kontextfenster für Viterbi
N_REGIMES = 3                  # Bull / Sideways / Bear

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data():
    """Lädt alle benötigten Daten (S&P 500, VIX, VVIX, GEX, DIX)."""
    print("📊 Lade Daten...")
    
    # 1. S&P 500
    sp500 = yf.download('^GSPC', start='1990-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    
    # 2. VIX
    vix = pd.read_csv(DATA_DIR / "VIX_History.csv", parse_dates=['DATE'])
    vix = vix.set_index('DATE').sort_index()
    vix = vix['CLOSE']
    
    # 3. VVIX (Volatilität der Volatilität)
    vvix = pd.read_csv(DATA_DIR / "VVIX_History.csv", parse_dates=['DATE'])
    vvix = vvix.set_index('DATE').sort_index()
    vvix = vvix['CLOSE']
    
    # 4. GEX & DIX (von SqueezeMetrics)
    dix = pd.read_csv(DATA_DIR / "DIX.csv", parse_dates=['date'])
    dix = dix.set_index('date').sort_index()
    
    # Spaltennamen normalisieren
    if 'DIX' in dix.columns:
        dix_data = dix['DIX']
    elif 'dix' in dix.columns:
        dix_data = dix['dix']
    else:
        dix_data = pd.Series(index=dix.index, data=np.nan)
    
    if 'GEX' in dix.columns:
        gex_data = dix['GEX']
    elif 'gex' in dix.columns:
        gex_data = dix['gex']
    else:
        gex_data = pd.Series(index=dix.index, data=np.nan)
    
    # 5. Alle Daten zusammenführen
    df = pd.DataFrame(index=sp500.index)
    df['returns'] = returns
    df['vix'] = vix.reindex(df.index, method='ffill')
    df['vvix'] = vvix.reindex(df.index, method='ffill')
    df['gex'] = gex_data.reindex(df.index, method='ffill')
    df['dix'] = dix_data.reindex(df.index, method='ffill')
    
    # 6. Features für das HMM (normalisiert)
    # Rendite-Features
    df['feature_returns'] = returns.rolling(20).mean()  # 20-Tage-Rendite
    df['feature_volatility'] = returns.rolling(20).std() * np.sqrt(252)  # 20-Tage-Volatilität
    
    # VIX-Features
    df['feature_vix'] = df['vix']
    df['feature_vix_delta'] = df['vix'].pct_change().rolling(5).mean()  # VIX-Änderung (geglättet)
    df['feature_vvix'] = df['vvix']
    
    # GEX-Features
    df['feature_gex'] = df['gex'] / 1e9  # Skalierung in Milliarden
    df['feature_gex_delta'] = df['gex'].pct_change().rolling(5).mean() / 1e9
    
    # DIX-Features
    df['feature_dix'] = df['dix']
    df['feature_dix_delta'] = df['dix'].pct_change().rolling(5).mean()
    
    # 7. Alle Features für das HMM (nur die, die wir verwenden)
    # Wir verwenden: returns, volatility, vix, vvix, gex, dix
    feature_columns = [
        'feature_returns',
        'feature_volatility',
        'feature_vix',
        'feature_vvix',
        'feature_gex',
        'feature_dix'
    ]
    
    # Standardisierung der Features (Z-Score)
    for col in feature_columns:
        mean = df[col].mean()
        std = df[col].std()
        if std > 0:
            df[f'{col}_std'] = (df[col] - mean) / std
        else:
            df[f'{col}_std'] = 0
    
    df = df.dropna()
    print(f"   ✅ {len(df)} Tage geladen ({df.index[0].date()} bis {df.index[-1].date()})")
    print(f"   📊 Features: {', '.join([c for c in df.columns if 'feature_' in c])}")
    
    return df

# =============================================================================
# 3. FEATURE-EXTRAKTION
# =============================================================================

def prepare_training_data(df: pd.DataFrame, end_idx: int) -> np.ndarray:
    """Bereitet die Trainingsdaten für das HMM vor (nur Vergangenheit)."""
    feature_cols = [
        'feature_returns_std',
        'feature_volatility_std',
        'feature_vix_std',
        'feature_vvix_std',
        'feature_gex_std',
        'feature_dix_std'
    ]
    
    train_df = df.iloc[:end_idx]
    features = np.column_stack([train_df[col].values for col in feature_cols])
    return features

# =============================================================================
# 4. ROLLING-HMM
# =============================================================================

def run_rolling_hmm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Führt das Rolling-HMM mit erweiterten Features durch.
    """
    print("\n🧠 Starte Rolling-HMM (erweitert)...")
    print(f"   Retrain-Intervall: {RETRAIN_INTERVAL} Tage")
    print(f"   Kontextfenster:    {CONTEXT_WINDOW} Tage")
    print(f"   Anzahl Regime:     {N_REGIMES}")
    print(f"   Features:          Rendite, Volatilität, VIX, VVIX, GEX, DIX")
    
    n = len(df)
    results = []
    model = None
    retrain_day = None
    
    for i in range(CONTEXT_WINDOW, n):
        train_end = i
        
        # Retrain alle 63 Tage
        if (i - CONTEXT_WINDOW) % RETRAIN_INTERVAL == 0 or i == CONTEXT_WINDOW:
            train_data = prepare_training_data(df, train_end)
            
            if len(train_data) < CONTEXT_WINDOW:
                continue
            
            model = hmm.GaussianHMM(
                n_components=N_REGIMES,
                covariance_type="full",
                n_iter=100,
                random_state=42
            )
            
            try:
                model.fit(train_data)
                retrain_day = df.index[i]
                is_retrain = True
            except Exception as e:
                if model is not None:
                    is_retrain = False
                else:
                    continue
        else:
            is_retrain = False
        
        if model is None:
            continue
        
        # Viterbi-Decodierung auf Kontextfenster
        try:
            context_data = prepare_training_data(df, i)
            if len(context_data) < CONTEXT_WINDOW:
                continue
            context_features = context_data[-CONTEXT_WINDOW:]
            hidden_states = model.predict(context_features)
            current_state = hidden_states[-1]
        except Exception as e:
            continue
        
        results.append({
            'date': df.index[i],
            'state': current_state,
            'is_retrain': is_retrain,
            'retrain_day': retrain_day if is_retrain else None
        })
        
        if i % 500 == 0:
            print(f"   Fortschritt: {i}/{n} ({i/n*100:.1f}%)")
    
    print(f"   ✅ Rolling-HMM abgeschlossen: {len(results)} Tage")
    
    results_df = pd.DataFrame(results)
    results_df = results_df.set_index('date')
    
    return results_df

# =============================================================================
# 5. PERFORMANCE-BERECHNUNG
# =============================================================================

def calculate_performance(results_df: pd.DataFrame, returns: pd.Series) -> dict:
    """
    Berechnet die Performance der HMM-basierten Strategie.
    """
    common_dates = results_df.index.intersection(returns.index)
    results_aligned = results_df.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    # HMM-Regime: 0=Bear (0% Position), 1=Sideways (50%), 2=Bull (100%)
    position_map = {0: 0.0, 1: 0.5, 2: 1.0}
    positions = results_aligned['state'].map(position_map).fillna(0.0)
    
    strategy_returns = positions.shift(1).fillna(0) * returns_aligned
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    peak = strategy_cum.expanding().max()
    drawdown = (strategy_cum - peak) / peak
    
    return {
        'total_return_strategy': float(strategy_cum.iloc[-1] - 1) if len(strategy_cum) > 0 else 0.0,
        'total_return_market': float(market_cum.iloc[-1] - 1) if len(market_cum) > 0 else 0.0,
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(drawdown.min()) if len(drawdown) > 0 else 0.0,
        'num_trades': int((positions != positions.shift(1)).sum()),
        'avg_position': float(positions.mean()) if len(positions) > 0 else 0.0,
        'n_days': len(positions)
    }

# =============================================================================
# 6. SPEICHERUNG & REPORT
# =============================================================================

def save_results(results_df: pd.DataFrame, perf: dict):
    """Speichert die Ergebnisse."""
    results_df.to_csv(OUTPUT_DIR / 'rolling_hmm_enhanced_labels.csv')
    print(f"💾 Regime-Labels gespeichert: {OUTPUT_DIR / 'rolling_hmm_enhanced_labels.csv'}")
    
    with open(OUTPUT_DIR / 'rolling_hmm_enhanced_metrics.json', 'w') as f:
        json.dump(perf, f, indent=4)
    print(f"💾 Metriken gespeichert: {OUTPUT_DIR / 'rolling_hmm_enhanced_metrics.json'}")

def print_report(perf: dict):
    """Gibt einen tabellarischen Report aus."""
    print("\n" + "=" * 60)
    print("📊 ROLLING-HMM (ERWEITERT) PERFORMANCE-REPORT")
    print("=" * 60)
    print(f"\n📈 Gesamtrendite:    {perf['total_return_strategy']:.2%}")
    print(f"📈 Buy & Hold:       {perf['total_return_market']:.2%}")
    print(f"📈 Mehrrendite:      {perf['total_return_strategy'] - perf['total_return_market']:.2%}")
    print(f"📉 Sharpe Ratio:     {perf['sharpe_ratio']:.2f}")
    print(f"📉 Max. Drawdown:    {perf['max_drawdown']:.2%}")
    print(f"🔄 Anzahl Trades:    {perf['num_trades']}")
    print(f"🔄 Ø Position:       {perf['avg_position']:.1%}")
    print(f"📅 Anzahl Tage:      {perf['n_days']}")

# =============================================================================
# 7. HAUPTPROGRAMM
# =============================================================================

def main():
    print("=" * 60)
    print("📈 STARTE ROLLING-HMM (ERWEITERT)")
    print("=" * 60)
    
    df = load_data()
    results_df = run_rolling_hmm(df)
    perf = calculate_performance(results_df, df['returns'])
    
    save_results(results_df, perf)
    print_report(perf)
    
    print("\n" + "=" * 60)
    print("🏁 ROLLING-HMM (ERWEITERT) ABGESCHLOSSEN")
    print("=" * 60)
    print("💡 Nächster Schritt: Ergebnisse mit dem einfachen HMM vergleichen.")

if __name__ == "__main__":
    main()
