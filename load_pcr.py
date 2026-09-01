"""
load_pcr.py – Put/Call-Ratio von Yahoo Finance laden
=====================================================

Dieses Skript lädt die Put/Call-Ratio (^PCC) von Yahoo Finance
und speichert sie als PCR.csv im data-Ordner.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data"
PCR_FILE = DATA_DIR / "PCR.csv"

def load_pcr():
    """Lädt die Put/Call-Ratio von Yahoo Finance."""
    print("📥 Lade Put/Call-Ratio (^PCC) von Yahoo Finance...")
    
    try:
        pcr = yf.download('^PCC', start='2011-01-01', end='2026-08-28', progress=False)
        if len(pcr) == 0:
            print("   ⚠️ Keine Daten für ^PCC gefunden.")
            return None
        
        # Wir verwenden den Schlusskurs als Put/Call-Ratio
        pcr_series = pcr['Close']
        print(f"   ✅ {len(pcr_series)} Tage geladen ({pcr_series.index[0].date()} bis {pcr_series.index[-1].date()})")
        return pcr_series
    
    except Exception as e:
        print(f"   ❌ Fehler beim Laden: {e}")
        return None

def main():
    print("=" * 60)
    print("📈 LADE PUT/CALL-RATIO (^PCC)")
    print("=" * 60)
    
    pcr = load_pcr()
    
    if pcr is not None:
        # Speichern
        pcr.to_csv(PCR_FILE)
        print(f"\n💾 Put/Call-Ratio gespeichert: {PCR_FILE}")
        print(f"   📊 {len(pcr)} Tage, {pcr.isna().sum()} NaN-Werte")
        print(f"   📈 Letzte Werte:\n{pcr.tail()}")
    else:
        print("❌ Put/Call-Ratio konnte nicht geladen werden.")
    
    print("\n" + "=" * 60)
    print("🏁 LADEVORGANG ABGESCHLOSSEN")
    print("=" * 60)

if __name__ == "__main__":
    main()
