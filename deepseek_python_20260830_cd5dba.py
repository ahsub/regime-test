"""
load_data.py – Daten-Loader für das Market Regime Analysis Tool
==============================================================

Dieses Skript lädt alle benötigten Rohdaten von den angegebenen Quellen
herunter und speichert sie im lokalen `data/`-Verzeichnis.

Enthaltene Datenquellen:
- CBOE: VIX, VVIX, SKEW, VIX3M, PUT, BXM, CLL
- SqueezeMetrics: DIX

Nach dem Download wird eine erste Visualisierung von VIX und S&P 500 erstellt.
"""

import pandas as pd
import requests
from pathlib import Path
import time
import matplotlib.pyplot as plt
import yfinance as yf
import sys

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

# Hauptverzeichnis für Daten
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)  # Ordner erstellen, falls nicht vorhanden

# Wartezeit zwischen Downloads (in Sekunden), um Server nicht zu überlasten
DOWNLOAD_DELAY = 0.5

# Dictionary mit allen Datenquellen
# Struktur: "lokaler_dateiname": "URL"
DATA_SOURCES = {
    # CBOE Volatilitäts-Indizes
    "VIX_History.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
    "VVIX_History.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv",
    "SKEW_History.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/SKEW_History.csv",
    "VIX3M_History.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv",
    
    # CBOE Options-Strategie-Indizes (als Proxies für Marktstimmung)
    "PUT_History.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/PUT_History.csv",
    "BXM_History.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/BXM_History.csv",
    "CLL_History.csv": "https://cdn.cboe.com/api/global/us_indices/daily_prices/CLL_History.csv",
    
    # SqueezeMetrics: Dark Index (DIX) und Gamma Exposure (GEX)
    # HINWEIS: Diese Datei enthält beide Indikatoren in einer CSV
    "DIX.csv": "https://squeezemetrics.com/monitor/static/DIX.csv",
}

# =============================================================================
# 2. HILFSFUNKTIONEN
# =============================================================================

def download_file(url: str, destination: Path) -> bool:
    """
    Lädt eine Datei von einer URL herunter und speichert sie.
    
    Parameter:
    ----------
    url : str
        Die vollständige URL der herunterzuladenden Datei.
    destination : Path
        Der Pfad, unter dem die Datei gespeichert werden soll.
    
    Rückgabe:
    --------
    bool : True bei Erfolg, False bei Fehler.
    """
    try:
        print(f"📥 Lade herunter: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Wirft Exception bei HTTP-Fehlern
        
        # Inhalt als Binärdatei speichern
        with open(destination, 'wb') as f:
            f.write(response.content)
        
        print(f"   ✅ Gespeichert als: {destination.name} ({response.headers.get('content-length', '?')} Bytes)")
        return True
        
    except requests.exceptions.Timeout:
        print(f"   ❌ Zeitüberschreitung: {url}")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP-Fehler {e.response.status_code}: {url}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Allgemeiner Fehler beim Download: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unerwarteter Fehler: {e}")
        return False


def load_cboe_csv(filepath: Path) -> pd.DataFrame:
    """
    Lädt eine CBOE-CSV-Datei mit Standardformat.
    
    Die CBOE-Dateien haben üblicherweise:
    - Eine Spalte 'Date' mit Datumsangaben
    - Eine Spalte 'Close' für den Schlusskurs
    """
    df = pd.read_csv(filepath, parse_dates=['Date'])
    df = df.set_index('Date')
    df = df.sort_index()
    return df


def load_dix_csv(filepath: Path) -> pd.DataFrame:
    """
    Lädt die DIX-CSV-Datei von SqueezeMetrics.
    Diese Datei hat ein etwas anderes Format mit mehreren Indikatoren.
    """
    df = pd.read_csv(filepath, parse_dates=['date'])
    df = df.set_index('date')
    df = df.sort_index()
    return df


def load_and_validate(filepath: Path, source_name: str) -> pd.DataFrame:
    """
    Lädt eine CSV-Datei mit dem passenden Parser basierend auf dem Dateinamen.
    Gibt einen leeren DataFrame zurück, falls die Datei nicht existiert.
    """
    if not filepath.exists():
        print(f"   ⚠️ Datei nicht gefunden: {filepath.name}")
        return pd.DataFrame()
    
    try:
        if "DIX" in filepath.name:
            df = load_dix_csv(filepath)
        else:
            df = load_cboe_csv(filepath)
        
        print(f"   ✅ {source_name} geladen: {len(df)} Einträge ({df.index[0].date()} bis {df.index[-1].date()})")
        return df
    except Exception as e:
        print(f"   ❌ Fehler beim Laden von {source_name}: {e}")
        return pd.DataFrame()

# =============================================================================
# 3. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion, die den gesamten Daten-Download und die Prüfung steuert."""
    
    print("=" * 60)
    print("🚀 STARTE DATEN-DOWNLOAD")
    print("=" * 60)
    
    # 3.1 Alle Daten herunterladen
    successful_downloads = 0
    failed_downloads = 0
    
    for filename, url in DATA_SOURCES.items():
        destination = DATA_DIR / filename
        if download_file(url, destination):
            successful_downloads += 1
        else:
            failed_downloads += 1
        time.sleep(DOWNLOAD_DELAY)
    
    # 3.2 Zusammenfassung der Downloads
    print("-" * 60)
    print(f"📊 DOWNLOAD-ZUSAMMENFASSUNG:")
    print(f"   ✅ Erfolgreich: {successful_downloads}")
    print(f"   ❌ Fehlgeschlagen: {failed_downloads}")
    print("-" * 60)
    
    # 3.3 Datenprüfung und erste Analyse
    print("\n🔍 PRÜFE HERUNTERGELADENE DATEN")
    print("-" * 60)
    
    # Lade VIX für die erste Prüfung
    vix_path = DATA_DIR / "VIX_History.csv"
    df_vix = load_and_validate(vix_path, "VIX")
    
    # Lade DIX für die erste Prüfung
    dix_path = DATA_DIR / "DIX.csv"
    df_dix = load_and_validate(dix_path, "DIX")
    
    # 3.4 Visualisierung: VIX und S&P 500
    if not df_vix.empty:
        print("\n📈 ERSTELLE VISUALISIERUNG: VIX vs. S&P 500")
        print("-" * 60)
        
        try:
            # Lade S&P 500 Daten von Yahoo Finance
            print("📥 Lade S&P 500 Daten von Yahoo Finance...")
            sp500 = yf.download(
                '^GSPC',
                start=df_vix.index[0],
                end=df_vix.index[-1],
                progress=False
            )
            sp500_close = sp500['Close']
            print(f"   ✅ S&P 500 geladen: {len(sp500_close)} Einträge")
            
            # Erstelle die Grafik mit zwei Achsen
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            
            # Obere Grafik: S&P 500
            ax1.plot(sp500_close.index, sp500_close, 
                    label='S&P 500', color='blue', linewidth=1.5)
            ax1.set_ylabel('S&P 500 Schlusskurs')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            ax1.set_title('S&P 500 Entwicklung')
            
            # Untere Grafik: VIX
            ax2.plot(df_vix.index, df_vix['Close'], 
                    label='VIX', color='red', linewidth=1.5)
            ax2.set_ylabel('VIX')
            ax2.set_xlabel('Datum')
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)
            ax2.set_title('VIX (Volatilitätsindex)')
            
            plt.suptitle('Marktdaten: VIX und S&P 500 (2008 - heute)', fontsize=14)
            plt.tight_layout()
            plt.show()
            
            print("   ✅ Visualisierung erfolgreich erstellt.")
            
        except Exception as e:
            print(f"   ❌ Fehler bei der Visualisierung: {e}")
    else:
        print("⚠️ Keine VIX-Daten vorhanden – Visualisierung wird übersprungen.")
    
    # 3.5 Abschlussmeldung
    print("\n" + "=" * 60)
    print("🏁 DATEN-LOADER ABGESCHLOSSEN")
    print("=" * 60)
    print(f"📁 Alle Daten wurden im Ordner '{DATA_DIR}' gespeichert.")
    print("💡 Nächster Schritt: Daten bereinigen und für das Modell vorbereiten.")

# =============================================================================
# 4. AUSFÜHRUNG
# =============================================================================

if __name__ == "__main__":
    main()