"""
prepare_data.py – Datenaufbereitung für das Market Regime Analysis Tool
======================================================================

Dieses Skript lädt alle heruntergeladenen CSV-Dateien, bereinigt sie,
führt sie zu einem einzigen DataFrame zusammen und speichert das Ergebnis.

Schritte:
1. Alle CSV-Dateien aus dem data/-Ordner laden
2. Datumsformate vereinheitlichen
3. Indikatoren zu einem DataFrame zusammenführen
4. Fehlende Werte behandeln
5. Ergebnis als 'market_data.csv' speichern
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. KONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "market_data.csv"

# Definiere die Spalten, die aus jeder Datei extrahiert werden sollen
# Format: "lokaler_dateiname": ("zu_extrahiertende_spalte", "neuer_spaltenname")
COLUMN_MAPPING = {
    "VIX_History.csv": ("CLOSE", "VIX"),
    "VVIX_History.csv": ("CLOSE", "VVIX"),
    "SKEW_History.csv": ("CLOSE", "SKEW"),
    "VIX3M_History.csv": ("CLOSE", "VIX3M"),
    "PUT_History.csv": ("CLOSE", "PUT"),
    "BXM_History.csv": ("CLOSE", "BXM"),
    "CLL_History.csv": ("CLOSE", "CLL"),
}

# DIX-Datei hat ein anderes Format mit mehreren Spalten
DIX_COLUMNS = {
    "DIX.csv": ["DIX", "GEX"],  # Wir extrahieren beide Spalten
}

# =============================================================================
# 2. HILFSFUNKTIONEN
# =============================================================================

def load_cboe_indicator(filepath: Path, col_name: str, new_name: str) -> pd.Series:
    """
    Lädt einen CBOE-Indikator aus einer CSV-Datei.
    
    Parameter:
    ----------
    filepath : Path
        Pfad zur CSV-Datei
    col_name : str
        Name der Spalte, die extrahiert werden soll
    new_name : str
        Neuer Name für die Spalte im finalen DataFrame
    
    Rückgabe:
    --------
    pd.Series : Die extrahierte Zeitreihe mit Datum als Index
    """
    # Datei laden – die Spalte 'DATE' wird automatisch als Datum erkannt
    df = pd.read_csv(filepath, parse_dates=['DATE'])
    df = df.set_index('DATE')
    df = df.sort_index()
    
    # Prüfen, ob die gewünschte Spalte existiert
    if col_name not in df.columns:
        # Fallback: Suche nach ähnlichen Spaltennamen
        for col in df.columns:
            if col.upper() == col_name.upper():
                col_name = col
                break
        else:
            raise ValueError(f"Spalte '{col_name}' nicht in {filepath.name} gefunden.")
    
    # Zeitreihe extrahieren
    series = df[col_name].copy()
    series.name = new_name
    
    return series


def load_dix_data(filepath: Path) -> pd.DataFrame:
    """
    Lädt die DIX-Datei von SqueezeMetrics.
    Diese enthält mehrere Indikatoren.
    """
    df = pd.read_csv(filepath, parse_dates=['date'])
    df = df.set_index('date')
    df = df.sort_index()
    
    # Wir extrahieren die Spalten 'DIX' und 'GEX'
    # Die Datei kann auch 'dix' und 'gex' in Kleinbuchstaben haben
    selected = pd.DataFrame(index=df.index)
    
    for col in ['DIX', 'dix']:
        if col in df.columns:
            selected['DIX'] = df[col]
            break
    
    for col in ['GEX', 'gex']:
        if col in df.columns:
            selected['GEX'] = df[col]
            break
    
    return selected


def merge_all_indicators(data_dir: Path) -> pd.DataFrame:
    """
    Lädt alle Indikatoren und führt sie zu einem DataFrame zusammen.
    """
    # Starte mit leerem DataFrame
    merged = None
    
    print("📊 Lade und füge Indikatoren zusammen...")
    
    # 1. CBOE-Indikatoren laden
    for filename, (col_name, new_name) in COLUMN_MAPPING.items():
        filepath = data_dir / filename
        
        if not filepath.exists():
            print(f"   ⚠️ Datei nicht gefunden: {filename} – übersprungen")
            continue
        
        try:
            series = load_cboe_indicator(filepath, col_name, new_name)
            
            if merged is None:
                merged = pd.DataFrame(series)
            else:
                merged = merged.join(series, how='outer')
            
            print(f"   ✅ {new_name} geladen: {len(series)} Einträge")
            
        except Exception as e:
            print(f"   ❌ Fehler beim Laden von {filename}: {e}")
    
    # 2. DIX-Daten laden
    dix_filepath = data_dir / "DIX.csv"
    if dix_filepath.exists():
        try:
            dix_data = load_dix_data(dix_filepath)
            
            if merged is None:
                merged = dix_data
            else:
                merged = merged.join(dix_data, how='outer')
            
            print(f"   ✅ DIX/GEX geladen: {len(dix_data)} Einträge")
            
        except Exception as e:
            print(f"   ❌ Fehler beim Laden von DIX.csv: {e}")
    
    return merged


def clean_and_fill(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bereinigt den DataFrame:
    - Sortiert nach Datum
    - Füllt Fehlstellen (vorwärts, dann rückwärts)
    - Entfernt extreme Ausreißer (optional)
    """
    print("\n🧹 Bereinige Daten...")
    
    # 1. Sortieren
    df = df.sort_index()
    print(f"   📅 Zeitraum: {df.index[0].date()} bis {df.index[-1].date()}")
    
    # 2. Fehlende Werte zählen
    missing = df.isnull().sum()
    print(f"   📊 Fehlende Werte pro Spalte:")
    for col, count in missing.items():
        if count > 0:
            print(f"      - {col}: {count} ({count/len(df)*100:.1f}%)")
    
    # 3. Fehlende Werte auffüllen (Vorwärtsfüllung, dann rückwärts)
    df = df.ffill().bfill()
    
    # 4. Prüfen, ob noch NaN existieren
    if df.isnull().any().any():
        print(f"   ⚠️ Es existieren noch NaN-Werte – Zeilen werden gelöscht.")
        df = df.dropna()
    
    # 5. Zeige finale Dimension
    print(f"   ✅ Finale Dimension: {df.shape[0]} Zeilen, {df.shape[1]} Spalten")
    
    return df


def add_market_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt Marktrenditen hinzu (basierend auf S&P 500, den wir später laden).
    Hier erstmal Platzhalter – wird später mit echter Quelle ergänzt.
    """
    # TODO: S&P 500 Daten von Yahoo Finance laden
    # Für jetzt: Platzhalter-Spalten
    df['SP500'] = np.nan
    df['SP500_returns'] = np.nan
    
    return df


def save_data(df: pd.DataFrame, output_path: Path):
    """
    Speichert den bereinigten DataFrame als CSV.
    """
    df.to_csv(output_path)
    print(f"\n💾 Daten gespeichert: {output_path}")
    print(f"   📊 {len(df)} Zeilen, {len(df.columns)} Spalten")


def show_summary(df: pd.DataFrame):
    """
    Zeigt eine kurze statistische Zusammenfassung der Daten.
    """
    print("\n📊 STATISTISCHE ZUSAMMENFASSUNG")
    print("=" * 60)
    
    # Deskriptive Statistiken
    print(df.describe().round(2))
    
    # Korrelationsmatrix (optional, nur wenn nicht zu viele Spalten)
    if len(df.columns) <= 10:
        print("\n📈 KORRELATIONSMATRIX")
        print("=" * 60)
        print(df.corr().round(2))


# =============================================================================
# 3. HAUPTPROGRAMM
# =============================================================================

def main():
    """Hauptfunktion für die Datenaufbereitung."""
    
    print("=" * 60)
    print("📊 STARTE DATENAUFBEREITUNG")
    print("=" * 60)
    
    # 1. Alle Indikatoren laden und zusammenführen
    merged = merge_all_indicators(DATA_DIR)
    
    if merged is None or merged.empty:
        print("❌ Keine Daten geladen – Abbruch.")
        return
    
    print(f"\n📋 Rohdaten: {merged.shape[0]} Zeilen, {merged.shape[1]} Spalten")
    
    # 2. Daten bereinigen
    cleaned = clean_and_fill(merged)
    
    # 3. Marktrenditen hinzufügen
    # cleaned = add_market_returns(cleaned)  # Aktivieren, sobald S&P 500 integriert
    
    # 4. Statistische Zusammenfassung
    show_summary(cleaned)
    
    # 5. Daten speichern
    save_data(cleaned, OUTPUT_FILE)
    
    print("\n" + "=" * 60)
    print("🏁 DATENAUFBEREITUNG ABGESCHLOSSEN")
    print("=" * 60)
    print(f"💡 Nächster Schritt: Die Daten in 'market_data.csv' werden für das Regime-Modell verwendet.")


if __name__ == "__main__":
    main()
