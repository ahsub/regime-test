#!/usr/bin/env python
"""
Vergleicht Ihr bestehendes Regime-Modell mit dem neuen Framework
"""

import sys
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Projekt-Pfad
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ihre bestehenden Module
try:
    from regime_model import RegimeModel as YourModel
    print("✅ Ihr bestehendes Modell gefunden (regime_model.py)")
    YOUR_MODEL_AVAILABLE = True
except ImportError:
    print("⚠️ Ihr Modell nicht gefunden, verwende einfaches K-Means")
    YOUR_MODEL_AVAILABLE = False

try:
    from load_data import load_data
    print("✅ load_data gefunden")
    LOAD_DATA_AVAILABLE = True
except ImportError:
    print("⚠️ load_data nicht gefunden")
    LOAD_DATA_AVAILABLE = False

# Framework-Module
EXTERNAL_PATH = PROJECT_ROOT / "src" / "external" / "market_regime_detection"
if EXTERNAL_PATH.exists():
    sys.path.insert(0, str(EXTERNAL_PATH))
    try:
        from ml_service.regime_detector import RegimeDetector
        from ml_service.models import KMeansModel, GMMModel, HDBSCANModel
        print("✅ Framework-Module gefunden")
        FRAMEWORK_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ Framework-Module nicht verfügbar: {e}")
        FRAMEWORK_AVAILABLE = False
else:
    print(f"⚠️ Framework nicht gefunden in: {EXTERNAL_PATH}")
    FRAMEWORK_AVAILABLE = False

# Unsere Feature-Brücke
from src.features.base_features import FeatureBridge

def compare_models(symbol: str = "SPY"):
    print("=" * 60)
    print("VERGLEICH: Ihr Modell vs. market_regime_detection")
    print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Daten laden
    print("\n📊 Lade Daten...")
    bridge = FeatureBridge()
    df = bridge.load_your_data(symbol)
    
    # Features hinzufügen
    print("\n🔧 Füge Features hinzu...")
    df = bridge.add_your_custom_features(df)
    
    # Für Modellierung vorbereiten
    df_clean, X = bridge.prepare_for_modeling(df)
    
    if len(X) == 0:
        print("❌ Keine Daten für Modellierung verfügbar")
        return None
    
    # 2. Ihr bestehendes Modell
    print("\n" + "=" * 40)
    print("IHR BESTEHENDES MODELL")
    print("=" * 40)
    
    your_regimes = None
    if YOUR_MODEL_AVAILABLE:
        try:
            print("   Führe regime_model.py aus...")
            your_model = YourModel()
            your_regimes = your_model.predict(df_clean)
            print(f"   ✅ {len(np.unique(your_regimes))} Regime gefunden")
            print(f"   Regime-Verteilung: {np.bincount(your_regimes)}")
        except Exception as e:
            print(f"   ⚠️ Fehler in Ihrem Modell: {e}")
    
    # Falls Ihr Modell nicht verfügbar ist
    if your_regimes is None:
        print("   Verwende einfaches K-Means (scikit-learn)...")
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        your_regimes = kmeans.fit_predict(X_scaled)
        print(f"   ✅ {len(np.unique(your_regimes))} Regime via K-Means")
    
    # 3. Framework-Modelle
    framework_results = {}
    if FRAMEWORK_AVAILABLE:
        print("\n" + "=" * 40)
        print("FRAMEWORK-MODELLE (market_regime_detection)")
        print("=" * 40)
        
        detector = RegimeDetector()
        
        # Teste verschiedene Modelle
        models = {
            'KMeans_3': KMeansModel(n_clusters=3),
            'KMeans_4': KMeansModel(n_clusters=4),
            'GMM': GMMModel(n_components=3),
            'HDBSCAN': HDBSCANModel(min_cluster_size=10)
        }
        
        for name, model in models.items():
            print(f"  - {name}...")
            try:
                labels = detector.fit_predict(X, model)
                framework_results[name] = labels
                n_regimes = len(np.unique(labels))
                print(f"    ✅ {n_regimes} Regime")
            except Exception as e:
                print(f"    ⚠️ Fehler: {e}")
                framework_results[name] = None
    
    # 4. Vergleich
    print("\n" + "=" * 40)
    print("VERGLEICH")
    print("=" * 40)
    
    from sklearn.metrics import adjusted_rand_score, v_measure_score
    
    comparison = {}
    for name, labels in framework_results.items():
        if labels is not None and len(labels) == len(your_regimes):
            # ARI: -1 bis 1, je höher desto ähnlicher
            ari = adjusted_rand_score(your_regimes, labels)
            # V-Measure: 0 bis 1, harmonisches Mittel von Homogenität und Vollständigkeit
            v_measure = v_measure_score(your_regimes, labels)
            comparison[name] = {'ARI': ari, 'V-Measure': v_measure}
            print(f"  {name:15}: ARI={ari:.4f}, V-Measure={v_measure:.4f}")
        else:
            print(f"  {name:15}: ⚠️ Nicht vergleichbar")
    
    # 5. Ergebnisse speichern
    results = {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'your_model': your_regimes,
        'framework': framework_results,
        'comparison': comparison,
        'data': df_clean,
        'features': X
    }
    
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    
    with open(results_dir / 'comparison_results.pkl', 'wb') as f:
        pickle.dump(results, f)
    print(f"\n✅ Ergebnisse gespeichert in results/comparison_results.pkl")
    
    # 6. Visualisierung
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Preis mit Regimen
        ax1 = axes[0, 0]
        ax1.plot(df_clean['close'].values, color='blue', alpha=0.7, label='Price')
        ax1_twin = ax1.twinx()
        ax1_twin.bar(range(len(your_regimes)), your_regimes, alpha=0.3, color='gray', width=1)
        ax1.set_title('Preis mit Ihren Regimen')
        ax1.legend(loc='upper left')
        ax1_twin.set_ylabel('Regime')
        
        # Ihre Regime Verteilung
        axes[0, 1].hist(your_regimes, bins=np.arange(-0.5, len(np.unique(your_regimes))+0.5, 1), 
                       edgecolor='black', alpha=0.7)
        axes[0, 1].set_title('Ihre Regime Verteilung')
        axes[0, 1].set_xlabel('Regime')
        axes[0, 1].set_ylabel('Häufigkeit')
        
        # Framework Vergleich
        if 'KMeans_3' in framework_results and framework_results['KMeans_3'] is not None:
            axes[1, 0].bar(range(len(framework_results['KMeans_3'])), 
                          framework_results['KMeans_3'], alpha=0.5, width=1)
            axes[1, 0].set_title('KMeans_3 Regime')
            axes[1, 0].set_ylabel('Regime')
        
        if 'GMM' in framework_results and framework_results['GMM'] is not None:
            axes[1, 1].bar(range(len(framework_results['GMM'])), 
                          framework_results['GMM'], alpha=0.5, width=1)
            axes[1, 1].set_title('GMM Regime')
            axes[1, 1].set_ylabel('Regime')
        
        plt.tight_layout()
        plt.savefig(results_dir / 'comparison_visualization.png', dpi=150)
        print("📈 Visualisierung: results/comparison_visualization.png")
        plt.close()
        
    except Exception as e:
        print(f"⚠️ Visualisierung fehlgeschlagen: {e}")
    
    # 7. Zusammenfassung
    print("\n" + "=" * 40)
    print("ZUSAMMENFASSUNG")
    print("=" * 40)
    if comparison:
        best_model = max(comparison, key=lambda x: comparison[x]['ARI'])
        print(f"  Beste Übereinstimmung: {best_model} (ARI={comparison[best_model]['ARI']:.3f})")
    else:
        print("  Keine Vergleichsdaten verfügbar")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, default='SPY', help='Symbol für Analyse')
    args = parser.parse_args()
    
    compare_models(args.symbol)
