"""
fetch_alfred.py – H4 Phase 0: Makro-Rohdaten mit Veröffentlichungsdatum (ALFRED/FRED-API) als Snapshot.

Läuft auf dem Mac (FRED ist aus der Claude-Umgebung nicht erreichbar). API-Schlüssel wird NUR aus
der Umgebungsvariable FRED_API_KEY gelesen und nirgends gespeichert.

Aufruf:
    export FRED_API_KEY=dein_schluessel
    python fetch_alfred.py                        # Standardauswahl → data/raw/alfred/<heute>/
    python fetch_alfred.py DGS10 DGS3MO DGS2      # Zusatz-Snapshot → data/raw/alfred/<heute>_DGS10-DGS3MO-DGS2/

Je Reihe zwei Abrufe:
  *_first.csv   output_type=4 (Erstveröffentlichung): observation_date, value, realtime_start
                = Datum, an dem dieser Wert ERSTMALS veröffentlicht wurde → point-in-time-Basis
  *_latest.csv  heutiger Stand (realtime_start=realtime_end=heute) → nur zur Messung von Revisionen
Ablage: data/raw/alfred/<heute>/ + SHA256SUMS.txt (danach nie überschreiben).

Reihenauswahl (festgelegt 27.09.2026 vor jeder Sichtung der Makrodaten; nicht aus Optionsmärkten):
  T10Y3M   10J – 3M Treasury (Zinskurve, Rezessionsindikator)      täglich, Marktdaten
  T10Y2Y   10J – 2J Treasury (Zinskurve)                             täglich, Marktdaten
  BAA10Y   Moody's Baa – 10J Treasury (Kreditspread)                 täglich, Marktdaten
  ICSA     Erstanträge Arbeitslosenhilfe (Arbeitsmarkt)              wöchentlich, revidiert
  NFCI     Chicago Fed National Financial Conditions Index           wöchentlich, revidiert
  STLFSI4  St. Louis Fed Financial Stress Index                      wöchentlich, revidiert
Hinweis: NFCI und STLFSI4 enthalten auch Volatilitätskomponenten (Redundanz mit VIX wahrscheinlich).

Zusatz (27.09.2026, nach Review „nicht revidiert ≠ damals verfügbar“): T10Y3M/T10Y2Y haben in
ALFRED erst ab 01/2014 Vintages; ihre Bausteine DGS10, DGS3MO, DGS2 (Fed H.15) ab 28.06.2005.
Die Zinskurve wird deshalb aus den Erstveröffentlichungen der Bausteine rekonstruiert.
DBAA (Baustein von BAA10Y) hat Vintages erst ab 02.04.2014 → BAA10Y vor 2014 nicht point-in-time.

Version: 1.4.0 (27.09.2026) – Zusatz-Snapshots über Reihenliste als Argument
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SERIES = ["T10Y3M", "T10Y2Y", "BAA10Y", "ICSA", "NFCI", "STLFSI4"]
API = "https://api.stlouisfed.org/fred/series/observations"
ROOT = Path(__file__).resolve().parent


class FredError(RuntimeError):
    pass


def get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.loads(r.read().decode())
        except (TimeoutError, ConnectionResetError) as e:
            if attempt == 2:
                raise FredError(f"Zeitüberschreitung/Verbindungsabbruch: {e}") from None
            print(f"   Wiederholung nach Zeitüberschreitung ({attempt + 1}/3) …")
            time.sleep(10 * (attempt + 1))
            continue
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            try:
                msg = json.loads(body).get("error_message", body)
            except ValueError:
                msg = body[:300]
            if 400 <= e.code < 500:          # Anfragefehler: Wiederholen sinnlos
                raise FredError(f"HTTP {e.code}: {msg}") from None
            if attempt == 2:
                raise FredError(f"HTTP {e.code}: {msg}") from None
            print(f"   Wiederholung nach HTTP {e.code}")
            time.sleep(3)
        except urllib.error.URLError as e:
            if attempt == 2:
                raise FredError(f"Netzwerkfehler: {e.reason}") from None
            print(f"   Wiederholung nach Netzwerkfehler: {e.reason}")
            time.sleep(3)


def fetch_all(base: dict) -> list[dict]:
    rows, offset = [], 0
    while True:
        d = get({**base, "limit": 100000, "offset": offset})
        obs = d.get("observations", [])
        rows += obs
        if len(rows) >= int(d.get("count", 0)) or not obs:
            return rows
        offset = len(rows)


VINTAGE_API = "https://api.stlouisfed.org/fred/series/vintagedates"
MAX_VINTAGES = 1900   # FRED erlaubt höchstens 2000 Veröffentlichungsstände je Abruf
BLOCK = {"NFCI": 150, "STLFSI4": 150}   # wöchentlich voll revidiert → kleine Blöcke gegen Timeouts


def vintage_dates(base: dict, series: str) -> list[str]:
    out, offset = [], 0
    while True:
        url = VINTAGE_API + "?" + urllib.parse.urlencode(
            {**base, "series_id": series, "limit": 10000, "offset": offset})
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise FredError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from None
        out += d.get("vintage_dates", [])
        if len(out) >= int(d.get("count", 0)) or not d.get("vintage_dates"):
            return out
        offset = len(out)


def first_releases(base: dict, series: str) -> list[dict]:
    block = BLOCK.get(series, MAX_VINTAGES)
    """Erstveröffentlichung je Beobachtung, blockweise (≤ MAX_VINTAGES Stände je Abruf).

    Blöcke überlappen um genau einen Veröffentlichungstag: Block k = [v_a, v_b], Block k+1 beginnt
    bei v_b. In Block k > 0 zählen nur Werte mit realtime_start > v_a (echter Erstveröffentlichungstag
    im Block); Werte mit Erstveröffentlichung genau an v_a stammen aus Block k−1. So kann ein vor dem
    Block veröffentlichter (evtl. revidierter) Wert nie als Erstveröffentlichung gezählt werden.
    """
    vds = vintage_dates(base, series)
    if not vds:
        return []
    if len(vds) <= block:
        return fetch_all({**base, "series_id": series, "output_type": 4,
                          "realtime_start": "1776-07-04", "realtime_end": "9999-12-31"})
    best: dict[str, dict] = {}
    idx = 0
    first_block = True
    while idx < len(vds) - 1 or first_block:
        a = vds[idx]
        b_idx = min(idx + block - 1, len(vds) - 1)
        b = vds[b_idx]
        rs = "1776-07-04" if first_block else a
        re_ = "9999-12-31" if b_idx == len(vds) - 1 else b
        rows = fetch_all({**base, "series_id": series, "output_type": 4,
                          "realtime_start": rs, "realtime_end": re_})
        for o in rows:
            if not first_block and o["realtime_start"] <= a:
                continue
            if o["realtime_start"] > b and re_ != "9999-12-31":
                continue
            prev = best.get(o["date"])
            if prev is None or o["realtime_start"] < prev["realtime_start"]:
                best[o["date"]] = o
        print(f"   Block {a} … {b}: {len(rows)} Zeilen")
        first_block = False
        if b_idx == len(vds) - 1:
            break
        idx = b_idx
        time.sleep(1)
    return [best[k] for k in sorted(best)]


def write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["observation_date", "value", "realtime_start", "realtime_end"])
        for o in rows:
            w.writerow([o["date"], o["value"], o["realtime_start"], o["realtime_end"]])


def main() -> int:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        print("FRED_API_KEY fehlt. Erst:  export FRED_API_KEY=dein_schluessel")
        return 1
    today = dt.date.today().isoformat()
    global SERIES
    if len(sys.argv) > 1:                      # Zusatz-Snapshot für einzelne Reihen
        SERIES = [a.upper() for a in sys.argv[1:]]
        out = ROOT / "data" / "raw" / "alfred" / f"{today}_{'-'.join(SERIES)}"
    else:
        out = ROOT / "data" / "raw" / "alfred" / today
    if (out / "SHA256SUMS.txt").exists():
        print(f"{out} ist bereits abgeschlossen (SHA256SUMS.txt vorhanden) – wird nicht überschrieben.")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    base = {"api_key": key, "file_type": "json"}
    try:
        run(base, out, today)
    except FredError as e:
        print(f"\nFRED meldet: {e}")
        print("Bitte diese Zeile an Claude schicken (sie enthält keinen Schlüssel).")
        return 1
    return 0


def run(base, out, today):
    for s in SERIES:
        if (out / f"{s}_first.csv").exists() and (out / f"{s}_latest.csv").exists():
            print(f"→ {s}: bereits vorhanden, übersprungen")
            continue
        print(f"→ {s}")
        first = first_releases(base, s)
        latest = fetch_all({**base, "series_id": s, "realtime_start": today, "realtime_end": today})
        write(out / f"{s}_latest.csv.tmp", latest)
        write(out / f"{s}_first.csv.tmp", first)
        (out / f"{s}_latest.csv.tmp").rename(out / f"{s}_latest.csv")
        (out / f"{s}_first.csv.tmp").rename(out / f"{s}_first.csv")
        print(f"   Erstveröffentlichung: {len(first)} Werte · heutiger Stand: {len(latest)} Werte")
        time.sleep(1)
    sums = []
    for f in sorted(out.glob("*.csv")):
        sums.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    (out / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    print(f"\nFertig: {out.relative_to(ROOT)} ({len(sums)} Dateien, SHA256SUMS.txt geschrieben)")


if __name__ == "__main__":
    sys.exit(main())
