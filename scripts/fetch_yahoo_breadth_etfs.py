#!/usr/bin/env python3
"""
fetch_yahoo_breadth_etfs.py – unveränderlicher Rohdaten-Snapshot SPY/RSP/IWM

Version: 1.0.0 (29.09.2026, Claude + Axel)
Zweck:   Datenbeschaffung für das Explorationsaudit H12-E1
         (docs/exploration/H12_E1_BREITE_VOR_REGIMEWECHSEL.md). Ausführen auf
         Axels Mac (die Claude-Sandbox erreicht Yahoo nicht).

Legt an: data/raw/yahoo/<YYYY-MM-DD>/  (Abrufdatum UTC; bricht ab, wenn der
         Ordner schon existiert – Snapshots sind unveränderlich)
  SPY.csv, RSP.csv, IWM.csv  – Spalten wie GSPC.csv im Snapshot 2026-09-27:
                                DATE,Open,High,Low,Close,Adj Close,Volume
  MANIFEST.json              – je Ticker: Quelle, yfinance-Version, Abrufzeit,
                                angefragter Zeitraum, Datei, SHA-256, Zeilen,
                                erste/letzte Beobachtung, fehlende Werte,
                                Handelstage, die bei einem anderen der drei
                                Ticker vorkommen, hier aber fehlen
  SHA256SUMS.txt             – Format wie `shasum -a 256 *`, inkl. MANIFEST.json
                                (kompatibel mit src/datalayer.verify_snapshot)

Aufruf (im Repo-Root von regime-test):
    python3 -m pip install --user yfinance pandas      # falls noch nicht vorhanden
    python3 scripts/fetch_yahoo_breadth_etfs.py

Nichts wird bereinigt, aufgefüllt oder angepasst; es werden nur die Rohwerte
gespeichert und beschrieben. Liefert Yahoo für einen Ticker keine Daten, bricht
das Skript ohne Snapshot ab.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"
TICKERS = ["SPY", "RSP", "IWM"]          # fest, s. Protokoll §2 – keine weiteren
START = "2007-01-01"                       # Protokoll §2: Renditen/Perzentile ab 18.09.2009 definiert
COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    try:
        import pandas as pd
        import yfinance as yf
    except ImportError as e:
        sys.exit(f"Fehlendes Paket: {e}. Installieren: python3 -m pip install --user yfinance pandas")

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d")
    out = ROOT / "data" / "raw" / "yahoo" / stamp
    if out.exists():
        sys.exit(f"{out} existiert bereits – Snapshots sind unveränderlich. Abbruch ohne Änderung.")

    frames = {}
    for t in TICKERS:
        # end exklusiv bei yfinance -> morgen, damit der letzte verfügbare Handelstag enthalten ist
        end = (now + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        df = yf.download(t, start=START, end=end, auto_adjust=False, actions=False,
                         progress=False, threads=False)
        if df is None or df.empty:
            sys.exit(f"Keine Daten für {t} von Yahoo erhalten – Abbruch, kein Snapshot angelegt.")
        if isinstance(df.columns, pd.MultiIndex):          # neuere yfinance-Versionen
            df.columns = df.columns.get_level_values(0)
        missing_cols = [c for c in COLUMNS if c not in df.columns]
        if missing_cols:
            sys.exit(f"{t}: Spalten fehlen {missing_cols} – Abbruch, kein Snapshot angelegt.")
        df = df[COLUMNS].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df.index.name = "DATE"
        if df.index.has_duplicates:
            sys.exit(f"{t}: doppelte Datumszeilen – Abbruch, kein Snapshot angelegt.")
        frames[t] = df.sort_index()

    union = sorted(set().union(*[set(f.index) for f in frames.values()]))
    out.mkdir(parents=True)
    manifest = {
        "manifest_version": 1,
        "script": f"scripts/fetch_yahoo_breadth_etfs.py {VERSION}",
        "purpose": "H12-E1 (docs/exploration/H12_E1_BREITE_VOR_REGIMEWECHSEL.md)",
        "source": "Yahoo Finance via yfinance",
        "yfinance_version": getattr(yf, "__version__", "unbekannt"),
        "pandas_version": pd.__version__,
        "python_version": sys.version.split()[0],
        "fetched_at_utc": now.isoformat(timespec="seconds"),
        "requested_start": START,
        "requested_end_exclusive": (now + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        "auto_adjust": False,
        "note": "Adj Close von Yahoo wird rueckwirkend angepasst (nicht point-in-time).",
        "files": [],
    }
    for t, df in frames.items():
        path = out / f"{t}.csv"
        df.to_csv(path, date_format="%Y-%m-%d")
        dates = set(df.index)
        manifest["files"].append({
            "ticker": t,
            "file": path.name,
            "sha256": sha256_file(path),
            "rows": int(len(df)),
            "first_date": df.index.min().strftime("%Y-%m-%d"),
            "last_date": df.index.max().strftime("%Y-%m-%d"),
            "missing_values": {c: int(df[c].isna().sum()) for c in COLUMNS},
            "dates_missing_vs_other_tickers": [d.strftime("%Y-%m-%d") for d in union if d not in dates],
        })
    (out / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    names = sorted(p.name for p in out.iterdir() if p.is_file())
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256_file(out / n)}  {n}\n" for n in names))

    print(f"Snapshot angelegt: {out.relative_to(ROOT)}")
    for f in manifest["files"]:
        gaps = len(f["dates_missing_vs_other_tickers"])
        print(f"  {f['ticker']}: {f['rows']} Zeilen, {f['first_date']} … {f['last_date']}, "
              f"fehlende Werte Adj Close {f['missing_values']['Adj Close']}, "
              f"fehlende Handelstage ggü. anderen {gaps}")
    print("Bitte den kompletten Ordner hochladen (alle 5 Dateien), nichts daran ändern.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
