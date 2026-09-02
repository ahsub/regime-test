"""
Feature-Brücke zwischen Ihren bestehenden Daten und market_regime_detection
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Optional, Tuple

# Pfad zum external Repository hinzufügen
EXTERNAL_PATH = Path(__file__).parent.parent / "external" / "market_regime_detection"
if EXTERNAL_PATH.exists():
    sys.path.insert(0, str(EXTERNAL_PATH))

class FeatureBridge:
    """
    Konvertiert Ihre Daten in das Format des market_regime_detection Frameworks
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = Path(data_path) if data_path else Path("data")
    
    def load_your_data(self, symbol: str = "SPY") -> pd.DataFrame:
        """
        Lädt Ihre bestehenden Daten aus dem data-Ordner
        """
        possible_paths = [
            self.data_path / f"{symbol}.csv",
            self.data_path / "ohlcv" / f"{symbol}.csv",
            self.data_path / "stock_data" / f"{symbol}.csv",
        ]
        
        df = None
        for path in possible_paths:
            if path.exists():
                df = pd.read_csv(path, parse_dates=['date'])
                print(f"✅ Daten geladen von: {path}")
                break
        
        if df is None:
            print("⚠️ Keine Daten gefunden, erstelle Beispieldaten...")
            df = self._create_sample_data()
        
        # Spalten standardisieren
        rename_map = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        
        # Datum sortieren
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"   {len(df)} Zeilen geladen ({df['date'].min()} bis {df['date'].max()})")
        return df
    
    def _create_sample_data(self) -> pd.DataFrame:
        """Erstellt Beispieldaten für Tests"""
        dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
        np.random.seed(42)
        
        # Simuliere Marktbewegungen
        n = len(dates)
        trend = np.linspace(0, 100, n) * 0.01
        cycle = np.sin(np.linspace(0, 4*np.pi, n)) * 20
        noise = np.random.randn(n) * 5
        
        price = 100 + trend + cycle + noise
        price = np.maximum(price, 50)
        
        return pd.DataFrame({
            'date': dates,
            'open': price + np.random.randn(n) * 0.5,
            'high': price + np.random.rand(n) * 3,
            'low': price - np.random.rand(n) * 3,
            'close': price,
            'volume': np.random.randint(100000, 1000000, n)
        })
    
    def add_your_custom_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fügt Ihre bestehenden Features hinzu
        """
        df = df.copy()
        
        # Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Volatilität
        df['volatility'] = df['returns'].rolling(20).std() * np.sqrt(252)
        df['volatility_5'] = df['returns'].rolling(5).std() * np.sqrt(252)
        df['volatility_50'] = df['returns'].rolling(50).std() * np.sqrt(252)
        
        # Momentum
        for period in [5, 10, 20, 50, 200]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
        
        # Volumen
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Spread
        df['spread'] = (df['high'] - df['low']) / df['close']
        df['spread_ma'] = df['spread'].rolling(20).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = ranges.rolling(14).mean()
        df['atr_ratio'] = df['atr'] / df['close']
        
        return df
    
    def get_enhanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Kombiniert Ihre Features mit denen aus market_regime_detection
        """
        # 1. Ihre Features
        df_with_features = self.add_your_custom_features(df)
        
        # 2. Versuche Features aus market_regime_detection
        try:
            from data_pipeline.feature_engineering import FeatureEngineer
            engineer = FeatureEngineer(df)
            framework_features = engineer.calculate_all_features()
            
            # Framework-Features hinzufügen (nur numerische)
            for col in framework_features.columns:
                if col not in df_with_features.columns:
                    df_with_features[col] = framework_features[col]
                    print(f"   + Added framework feature: {col}")
                    
        except ImportError as e:
            print(f"⚠️ Framework-Features nicht verfügbar: {e}")
        except Exception as e:
            print(f"⚠️ Fehler bei Framework-Features: {e}")
        
        return df_with_features
    
    def prepare_for_modeling(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Bereitet Daten für die Modellierung vor
        """
        # Feature-Spalten auswählen
        feature_cols = [col for col in df.columns if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
        
        # NaN entfernen
        df_clean = df.dropna()
        
        if len(df_clean) < 100:
            print(f"⚠️ Nur {len(df_clean)} Zeilen nach Bereinigung")
            return df, pd.DataFrame()
        
        # Features
        X = df_clean[feature_cols]
        
        print(f"   {len(X)} Zeilen für Modellierung, {len(feature_cols)} Features")
        
        return df_clean, X
