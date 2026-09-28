#!/usr/bin/env python3
"""
fetch_cboe_pcr_daily.py – Cboe-Put/Call-Tagesdaten ab 07.10.2019 laden und als
unveränderlichen Snapshot ablegen (schließt die Lücke nach dem Ende der
Cboe-CSV-Dateien am 04.10.2019).

Ablauf
  1. Für jeden NYSE-Handelstag im Zeitraum die Seite
     https://www.cboe.com/us/options/market_statistics/daily/?dt=YYYY-MM-DD
     laden – höflich (Pause zwischen Abrufen), mit Wiederholungen.
     Rohseiten landen im Cache data/raw/_cache/cboe_daily_html/ (nicht im Git).
     Ein erneuter Lauf lädt nur fehlende Tage nach → auch als Tages-Update nutzbar.
  2. Jede Seite parsen und prüfen (src/datalayer/cboe_daily.py):
     Calls+Puts=Total, Index+ETP+Equity=Summe, Seiten-Ratio = Puts/Calls.
  3. Snapshot data/raw/cboe/<heute>_pcr_daily/ schreiben:
     totalpc_daily.csv, indexpc_daily.csv, equitypc_daily.csv, etppc_daily.csv,
     vixpc_daily.csv, spxpc_daily.csv (Cboe-CSV-Format), fetch_report.json
     (inkl. SHA-256 jeder Rohseite), SHA256SUMS.txt.
     run_phase1.py nimmt den Ordner automatisch mit.

Aufruf (auf einem Rechner mit Internetzugang, Laufzeit Erstlauf ca. 45–60 min):
    python scripts/fetch_cboe_pcr_daily.py
    python scripts/fetch_cboe_pcr_daily.py --start 2024-01-01 --end 2024-01-31 --no-snapshot
    python scripts/fetch_cboe_pcr_daily.py --offline      # nur Cache neu parsen

Exit-Code 0 = Snapshot geschrieben, 1 = Abbruch/Fehler (Details im Bericht).

Version: 1.0.0 (28.09.2026)
Changelog:
  1.0.0 (28.09.2026) – Erstfassung.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from datalayer import nyse_calendar  # noqa: E402
from datalayer.cboe_daily import (DAILY_URL, FIRST_DAILY_DATE, PRODUCTS,  # noqa: E402
                                  DailyParseError, parse_daily_html, to_frame,
                                  write_cboe_csv)

CACHE = ROOT / "data" / "raw" / "_cache" / "cboe_daily_html"
OUT_ROOT = ROOT / "data" / "raw" / "cboe"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 regime-test/pcr-daily")
RECENT_DAYS = 7      # „keine Daten“ bei jungen Tagen kann vorläufig sein → neu laden


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(session, day: str, retries: int = 4, timeout: int = 30) -> bytes:
    url = DAILY_URL.format(date=day)
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 200 and r.content:
                return r.content
            last = f"HTTP {r.status_code}"
            if r.status_code in (403, 404):
                break
        except Exception as e:  # Netzwerkfehler → erneut versuchen
            last = repr(e)
        time.sleep(5 * 2 ** attempt)
    raise RuntimeError(f"{day}: Abruf fehlgeschlagen ({last})")


def needs_download(path: Path, day: pd.Timestamp, today: pd.Timestamp) -> bool:
    if not path.exists():
        return True
    if (today - day).days <= RECENT_DAYS:
        txt = path.read_bytes().decode("utf-8", "replace").lower()
        return "no data available" in txt
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--start", default="2019-10-01",
                    help="Beginn (Standard 2019-10-01, dokumentiert den ersten Datentag)")
    ap.add_argument("--end", default=None, help="Ende inkl. (Standard: gestern)")
    ap.add_argument("--sleep", type=float, default=1.5, help="Pause je Abruf in s")
    ap.add_argument("--offline", action="store_true", help="nur Cache parsen, nichts laden")
    ap.add_argument("--no-snapshot", action="store_true", help="nur laden/prüfen")
    ap.add_argument("--allow-errors", action="store_true",
                    help="Snapshot trotz Parserfehlern schreiben (Fehltage bleiben leer)")
    a = ap.parse_args(argv)

    today = pd.Timestamp(dt.date.today())
    end = pd.Timestamp(a.end) if a.end else today - pd.Timedelta(days=1)
    cal = nyse_calendar(a.start, end)
    CACHE.mkdir(parents=True, exist_ok=True)

    session = None
    if not a.offline:
        import requests
        session = requests.Session()
        session.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.8"})

    todo = [d for d in cal if needs_download(CACHE / f"{d:%Y-%m-%d}.html", d, today)]
    if todo and a.offline:
        print(f"Offline: {len(todo)} Tage fehlen im Cache und werden übersprungen.")
    elif todo:
        eta = len(todo) * (a.sleep + 0.7) / 60
        print(f"Lade {len(todo)} Tage (ca. {eta:.0f} min) …")
        for i, d in enumerate(todo, 1):
            day = f"{d:%Y-%m-%d}"
            try:
                content = fetch(session, day)
            except RuntimeError as e:
                print(f"  ! {e}")
                continue
            (CACHE / f"{day}.html").write_bytes(content)
            if i % 50 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}  (zuletzt {day})")
            time.sleep(a.sleep)

    days, no_data, errors, warnings, not_cached, raw_sha = {}, [], {}, {}, [], {}
    for d in cal:
        day = f"{d:%Y-%m-%d}"
        f = CACHE / f"{day}.html"
        if not f.exists():
            not_cached.append(day)
            continue
        content = f.read_bytes()
        raw_sha[day] = sha256(content)
        try:
            st = parse_daily_html(content.decode("utf-8", "replace"))
        except DailyParseError as e:
            errors[day] = str(e)
            continue
        if st is None:
            no_data.append(day)
            continue
        days[d] = st
        if st.warnings:
            warnings[day] = st.warnings

    # Gleiches Tripel an zwei aufeinanderfolgenden Datentagen = Verdacht auf
    # ausgelieferte Fremdseite (z. B. Rückfall auf aktuellen Tag)
    repeats = []
    prev = None
    for d in sorted(days):
        v = days[d].volumes["total"]
        if prev is not None and v == prev[1]:
            repeats.append([f"{prev[0]:%Y-%m-%d}", f"{d:%Y-%m-%d}"])
        prev = (d, v)
    for a_, b_ in repeats:
        errors[b_] = (f"identische Gesamtvolumina wie {a_} – Seite vermutlich nicht "
                      "tagesgenau; Rohseite als .suspect beiseitegelegt, nächster Lauf lädt neu")
        days.pop(pd.Timestamp(b_), None)
        f = CACHE / f"{b_}.html"
        if f.exists():
            f.replace(CACHE / f"{b_}.html.suspect")

    first = min(days).strftime("%Y-%m-%d") if days else None
    last = max(days).strftime("%Y-%m-%d") if days else None
    gaps = [x for x in no_data if first and first <= x <= last]
    report = {
        "abgerufen": f"{today:%Y-%m-%d}",
        "quelle": DAILY_URL.format(date="YYYY-MM-DD"),
        "zeitraum_angefragt": [f"{cal.min():%Y-%m-%d}", f"{cal.max():%Y-%m-%d}"],
        "nyse_tage_angefragt": int(len(cal)),
        "erster_datentag": first,
        "letzter_datentag": last,
        "datentage": len(days),
        "erwarteter_erster_datentag": FIRST_DAILY_DATE,
        "keine_daten_vor_erstem_datentag": [x for x in no_data if first and x < first],
        "luecken_keine_daten": gaps,
        "nicht_geladen": not_cached,
        "parserfehler": errors,
        "hinweise": warnings,
        "rohseiten_sha256": raw_sha,
    }

    print(f"\nNYSE-Tage angefragt: {len(cal)}  ·  mit Daten: {len(days)}  "
          f"({first} – {last})")
    print(f"Lücken (keine Daten innerhalb des Zeitraums): {len(gaps)}"
          + (f"  z. B. {', '.join(gaps[:8])}" if gaps else ""))
    print(f"Nicht geladen: {len(not_cached)}  ·  Parserfehler: {len(errors)}  ·  "
          f"Tage mit Hinweisen: {len(warnings)}")
    for day, msg in list(errors.items())[:10]:
        print(f"  ✗ {day}: {msg}")
    if first and first != FIRST_DAILY_DATE and a.start <= FIRST_DAILY_DATE:
        print(f"  ! erster Datentag {first} ≠ erwartet {FIRST_DAILY_DATE}")

    if a.no_snapshot:
        return 1 if errors else 0
    if not days:
        print("ABBRUCH – keine Datentage.")
        return 1
    if (errors or not_cached) and not a.allow_errors:
        print("ABBRUCH – Snapshot nicht geschrieben (Fehler/fehlende Seiten). "
              "Erneut starten lädt fehlende/verdächtige Seiten nach; Parserfehler "
              "erfordern eine Parser-Anpassung (danach --offline); sonst --allow-errors.")
        return 1

    out = OUT_ROOT / f"{today:%Y-%m-%d}_pcr_daily"
    if out.exists():
        print(f"ABBRUCH – {out} existiert bereits (Snapshots sind unveränderlich).")
        return 1
    out.mkdir(parents=True)
    names = []
    for key, (_, fname, _) in PRODUCTS.items():
        df = to_frame(days, key)
        if df.empty:
            continue
        write_cboe_csv(df, key, out / fname, f"{today:%Y-%m-%d}")
        names.append(fname)
    (out / "fetch_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    names.append("fetch_report.json")
    (out / "SHA256SUMS.txt").write_text("".join(
        f"{sha256((out / n).read_bytes())}  {n}\n" for n in sorted(names)))
    shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"\nSnapshot: {shown}  ({len(names)} Dateien)")
    print("Weiter:   python run_phase1.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
