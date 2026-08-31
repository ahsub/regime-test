"""
rolling_hmm.py – Rolling Hidden Markov Model nach Pagliaro (2026)
===================================================================

Dieses Skript implementiert einen Gaussian HMM mit K=3 Zuständen,
der alle 63 Tage neu gefittet wird (nur mit Vergangenheitsdaten).

Features:
- 20-Tage-Rendite
- 20-Tage-annualisierte Volatilität
- VIX-Level
- Marktbreite-Proxy (Advance-Decline-Linie)

Decodierung: Viterbi-Algorithmus auf 120-Tage-Kontextfenster

Ausgabe: Tabellarische Ergebnisse (keine Grafiken)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# hmmlearn muss installiert sein: pip install hmmlearn
from hmmlearn import hmm

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Parameter nach Pagliaro (2026)
RETRAIN_INTERVAL = 63          # Alle 63 Handelstage neu fitten
CONTEXT_WINDOW = 120           # 120-Tage-Kontextfenster für Viterbi
N_REGIMES = 3                  # Bull / Sideways / Bear
N_FEATURES = 4                 # Rendite, Volatilität, VIX, Marktbreite

# =============================================================================
# 2. DATEN LADEN
# =============================================================================

def load_data():
    """Lädt die benötigten Daten."""
    print("📊 Lade Daten...")
    
    # S&P 500 Daten
    import yfinance as yf
    sp500 = yf.download('^GSPC', start='1990-01-01', end='2026-08-28', progress=False)
    returns = sp500['Close'].pct_change()
    
    # VIX Daten
    vix = pd.read_csv(DATA_DIR / "VIX_History.csv", parse_dates=['DATE'])
    vix = vix.set_index('DATE').sort_index()
    vix = vix['CLOSE']
    
    # Marktbreite (Advance-Decline-Linie) – wir verwenden den S&P 500 als Proxy
    # In einer Produktionsumgebung würde man hier echte AD-Daten nehmen
    market_breadth = sp500['Close'].pct_change().rolling(20).mean()
    
    # Zusammenführen
    df = pd.DataFrame(index=sp500.index)
    df['returns'] = returns
    df['vix'] = vix.reindex(df.index, method='ffill')
    df['volatility'] = returns.rolling(20).std() * np.sqrt(252)
    df['market_breadth'] = market_breadth
    
    # Features für das HMM
    df['feature_returns'] = returns.rolling(20).mean()  # 20-Tage-Rendite
    df['feature_volatility'] = df['volatility']
    df['feature_vix'] = df['vix']
    df['feature_breadth'] = df['market_breadth']
    
    df = df.dropna()
    print(f"   ✅ {len(df)} Tage geladen ({df.index[0].date()} bis {df.index[-1].date()})")
    
    return df

# =============================================================================
# 3. FEATURE-EXTRAKTION
# =============================================================================

def extract_features(df: pd.DataFrame, idx: int) -> np.ndarray:
    """Extrahiert die 4 Features für einen bestimmten Zeitpunkt."""
    features = np.column_stack([
        df['feature_returns'].iloc[idx],
        df['feature_volatility'].iloc[idx],
        df['feature_vix'].iloc[idx],
        df['feature_breadth'].iloc[idx]
    ])
    return features.reshape(1, -1)

def prepare_training_data(df: pd.DataFrame, end_idx: int) -> np.ndarray:
    """Bereitet die Trainingsdaten für das HMM vor (nur Vergangenheit)."""
    train_df = df.iloc[:end_idx]
    features = np.column_stack([
        train_df['feature_returns'].values,
        train_df['feature_volatility'].values,
        train_df['feature_vix'].values,
        train_df['feature_breadth'].values
    ])
    return features

# =============================================================================
# 4. ROLLING-HMM
# =============================================================================

def run_rolling_hmm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Führt das Rolling-HMM nach Pagliaro (2026) durch.
    
    Alle 63 Tage wird das Modell neu gefittet (nur mit Vergangenheitsdaten).
    Die Regime-Decodierung erfolgt per Viterbi auf einem 120-Tage-Kontextfenster.
    """
    print("\n🧠 Starte Rolling-HMM...")
    print(f"   Retrain-Intervall: {RETRAIN_INTERVAL} Tage")
    print(f"   Kontextfenster:    {CONTEXT_WINDOW} Tage")
    print(f"   Anzahl Regime:     {N_REGIMES}")
    
    n = len(df)
    results = []
    
    # Erste Trainingsdaten (ab 120 Tagen)
    for i in range(CONTEXT_WINDOW, n):
        # 1. Trainingszeitraum bestimmen (nur Vergangenheit)
        train_end = i
        
        # 2. Prüfen, ob ein Retrain nötig ist (alle 63 Tage)
        if (i - CONTEXT_WINDOW) % RETRAIN_INTERVAL == 0 or i == CONTEXT_WINDOW:
            # 3. Modell fitten
            train_data = prepare_training_data(df, train_end)
            
            # Gaussian HMM mit 3 Zuständen
            model = hmm.GaussianHMM(
                n_components=N_REGIMES,
                covariance_type="full",
                n_iter=100,
                random_state=42
            )
            
            try:
                model.fit(train_data)
                is_retrain = True
                retrain_day = df.index[i]
            except Exception as e:
                print(f"   ⚠️ Fehler beim Fit für {df.index[i].date()}: {e}")
                # Fallback: Vorheriges Modell verwenden
                if 'model' in locals():
                    is_retrain = False
                else:
                    continue
        else:
            is_retrain = False
        
        # 4. Aktuelle Features für das 120-Tage-Kontextfenster
        context_start = max(0, i - CONTEXT_WINDOW)
        context_data = prepare_training_data(df, i)  # Alle Daten bis i
        if len(context_data) < CONTEXT_WINDOW:
            continue
        
        # 5. Viterbi-Decodierung auf dem Kontextfenster
        try:
            # Nur die letzten CONTEXT_WINDOW Tage für Viterbi verwenden
            context_features = context_data[-CONTEXT_WINDOW:]
            if len(context_features) < CONTEXT_WINDOW:
                continue
            hidden_states = model.predict(context_features)
            current_state = hidden_states[-1]
        except Exception as e:
            print(f"   ⚠️ Viterbi-Fehler für {df.index[i].date()}: {e}")
            continue
        
        # 6. Ergebnisse speichern
        results.append({
            'date': df.index[i],
            'state': current_state,
            'is_retrain': is_retrain,
            'retrain_day': retrain_day if is_retrain else None
        })
        
        # Fortschritt anzeigen
        if i % 500 == 0:
            print(f"   Fortschritt: {i}/{n} ({i/n*100:.1f}%)")
    
    print(f"   ✅ Rolling-HMM abgeschlossen: {len(results)} Tage")
    
    # Ergebnisse in DataFrame umwandeln
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
    # Aligniere Daten
    common_dates = results_df.index.intersection(returns.index)
    results_aligned = results_df.loc[common_dates]
    returns_aligned = returns.loc[common_dates]
    
    # HMM-Regime:
    # State 0 = Bear (keine Position)
    # State 1 = Sideways (teilweise Position)
    # State 2 = Bull (volle Position)
    position_map = {0: 0.0, 1: 0.5, 2: 1.0}
    positions = results_aligned['state'].map(position_map).fillna(0.0)
    
    # Strategie-Renditen
    strategy_returns = positions.shift(1).fillna(0) * returns_aligned
    strategy_cum = (1 + strategy_returns).cumprod()
    market_cum = (1 + returns_aligned).cumprod()
    
    # Sharpe Ratio
    excess_returns = strategy_returns - 0.02/252
    sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
    
    # Drawdown
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
    # 1. Regime-Labels
    results_df.to_csv(OUTPUT_DIR / 'rolling_hmm_labels.csv')
    print(f"💾 Regime-Labels gespeichert: {OUTPUT_DIR / 'rolling_hmm_labels.csv'}")
    
    # 2. Performance-Metriken (JSON)
    import json
    with open(OUTPUT_DIR / 'rolling_hmm_metrics.json', 'w') as f:
        json.dump(perf, f, indent=4)
    print(f"💾 Metriken gespeichert: {OUTPUT_DIR / 'rolling_hmm_metrics.json'}")
    
    # 3. CSV für tabellarische Auswertung
    df = pd.DataFrame([perf])
    df.to_csv(OUTPUT_DIR / 'rolling_hmm_performance.csv', index=False)
    print(f"💾 Performance-Tabelle gespeichert: {OUTPUT_DIR / 'rolling_hmm_performance.csv'}")

def print_report(perf: dict):
    """Gibt einen tabellarischen Report aus."""
    print("\n" + "=" * 60)
    print("📊 ROLLING-HMM PERFORMANCE-REPORT")
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
    print("📈 STARTE ROLLING-HMM (PAGLIARO 2026)")
    print("=" * 60)
    
    # Daten laden
    df = load_data()
    
    # Rolling-HMM durchführen
    results_df = run_rolling_hmm(df)
    
    # Performance berechnen
    perf = calculate_performance(results_df, df['returns'])
    
    # Speichern
    save_results(results_df, perf)
    
    # Report
    print_report(perf)
    
    print("\n" + "=" * 60)
    print("🏁 ROLLING-HMM ABGESCHLOSSEN")
    print("=" * 60)
    print("💡 Nächster Schritt: Ergebnisse mit bestehendem Modell vergleichen.")

if __name__ == "__main__":
    main()
