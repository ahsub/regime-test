"""
Parser für Cboe-Rohdateien.

1) Index-Historien  (cdn.cboe.com/api/global/us_indices/daily_prices/<SYMBOL>_History.csv)
   Kopf: DATE,OPEN,HIGH,LOW,CLOSE  – einige ältere Dateien nur DATE,<SYMBOL>
2) Put/Call-Ratio   (cdn.cboe.com/resources/options/volume_and_call_put_ratios/*.csv)
   mehrzeiliger Disclaimer-Kopf, Spaltenzeile DATE bzw. Trade_date,
   Werte mit führenden Leerzeichen.

Datumsformat überall MM/DD/YYYY. Keine Werte werden aufgefüllt oder verändert.

Version: 1.0.0 (27.09.2026)
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

_DATE_FMT = "%m/%d/%Y"


def detect_file_kind(path: str | Path) -> str:
    """'index' | 'pcr' anhand des Dateikopfs."""
    head = Path(path).read_text(errors="replace")[:4000]
    first = head.splitlines()[0].strip().upper() if head else ""
    if first.startswith("DATE,"):
        return "index"
    if "PUT/CALL" in head.upper() or "P/C RATIO" in head.upper():
        return "pcr"
    raise ValueError(f"Unbekanntes Cboe-Dateiformat: {path}")


def _parse_dates(s: pd.Series, path) -> pd.DatetimeIndex:
    idx = pd.to_datetime(s.astype(str).str.strip(), format=_DATE_FMT, errors="coerce")
    bad = int(idx.isna().sum())
    if bad:
        raise ValueError(f"{path}: {bad} nicht lesbare Datumswerte")
    return pd.DatetimeIndex(idx)


def parse_cboe_index(path: str | Path, name: str | None = None) -> pd.Series:
    """Schlusskurs-Reihe einer Cboe-Index-Historie (Series, DatetimeIndex)."""
    path = Path(path)
    df = pd.read_csv(path)
    df.columns = [str(c).strip().upper() for c in df.columns]
    if "DATE" not in df.columns:
        raise ValueError(f"{path}: keine DATE-Spalte")
    value_col = "CLOSE" if "CLOSE" in df.columns else [c for c in df.columns if c != "DATE"][-1]
    s = pd.Series(
        pd.to_numeric(df[value_col], errors="coerce").to_numpy(dtype="float64"),
        index=_parse_dates(df["DATE"], path),
        name=name or path.name.replace("_History.csv", ""),
    )
    s.index.name = "date"
    return s.sort_index()


def parse_cboe_pcr(path: str | Path) -> pd.DataFrame:
    """Put/Call-Datei → DataFrame[calls, puts, total, pcr] (DatetimeIndex)."""
    path = Path(path)
    lines = path.read_text(errors="replace").splitlines()
    hdr = next(
        (i for i, l in enumerate(lines)
         if l.strip().upper().startswith(("DATE,", "TRADE_DATE,"))),
        None,
    )
    if hdr is None:
        raise ValueError(f"{path}: keine Spaltenzeile (DATE/Trade_date) gefunden")
    df = pd.read_csv(io.StringIO("\n".join(lines[hdr:])), skipinitialspace=True)
    df.columns = [str(c).strip().upper() for c in df.columns]
    rename = {df.columns[0]: "date"}
    for c in df.columns[1:]:
        if c.startswith("CALL"):
            rename[c] = "calls"
        elif c.startswith("PUT"):
            rename[c] = "puts"
        elif c.startswith("TOTAL"):
            rename[c] = "total"
        elif "RATIO" in c:
            rename[c] = "pcr"
    df = df.rename(columns=rename)
    missing = {"calls", "puts", "total", "pcr"} - set(df.columns)
    if missing:
        raise ValueError(f"{path}: Spalten fehlen: {sorted(missing)}")
    df = df.dropna(subset=["date"])
    df = df[df["date"].astype(str).str.strip() != ""]
    out = pd.DataFrame(
        {c: pd.to_numeric(df[c], errors="coerce").to_numpy(dtype="float64")
         for c in ["calls", "puts", "total", "pcr"]},
        index=_parse_dates(df["date"], path),
    )
    out.index.name = "date"
    return out.sort_index()
