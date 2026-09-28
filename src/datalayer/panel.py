"""
Panel-Bau und Datenqualitätsbericht.

Regeln (Roadmap Phase 1):
  * Handelskalender = NYSE-Handelstage (Mo–Fr ohne NYSE-Feiertage und
    Sonderschließungen, Paket `holidays`, z. B. 9/11, Hurrikan Sandy,
    Trauertage). Zeitraum = erster bis letzter Tag der Anker-Reihe (VIX).
    Hinweis: Die Cboe-VIX-Historie enthält seit 2022 Zeilen an US-Börsen-
    feiertagen – sie ist daher NICHT als Kalender geeignet (Befund 27.09.2026).
  * Kein Forward-Fill. Fehlende Werte bleiben NaN; Zeilen außerhalb des
    Kalenders (Feiertage, Wochenenden) werden NICHT übernommen, sondern im
    Bericht gelistet.
  * Point-in-time: Cboe-Schlusswerte von Tag t sind nach Handelsschluss t
    bekannt. Das Panel verschiebt nichts – Signal-Lag (Ausführung frühestens
    t+1) gehört in die Strategie, nicht in die Datenschicht.
  * PCR-Strukturbrüche laut Cboe-Dateikopf: bis 31.05.2012 cleared volume
    (OCC), danach preliminary volume; ab 11.06.2012 Equity/Index ohne ETPs.
    Spalte `pcr_segment` kennzeichnet die Abschnitte.
  * PCR-Fortschreibung ab 07.10.2019 aus der Cboe-Seite „Daily Market
    Statistics“ (Snapshot data/raw/cboe/<datum>_pcr_daily/, erzeugt mit
    scripts/fetch_cboe_pcr_daily.py). Gleiche Abgrenzung wie Segment C
    (Equity ohne ETPs, nur Cboe-Börse). Spalten `pcr_<x>_daily` bleiben
    getrennt; zusätzlich `pcr_<x>_full` = CSV-Wert, wo vorhanden, sonst
    Daily-Wert (kein Überlapp: CSV endet 04.10.2019). Die Nahtstelle wird im
    QC-Bericht ausgewiesen.

Version: 1.2.0 (28.09.2026)
Changelog:
  1.2.0 (28.09.2026) – PCR-Daily-Dateien (*_daily.csv) eingebunden, gespleißte
                       Spalten pcr_total/equity/index_full, Nahtstellen-Prüfung
                       im QC-Bericht; Nicht-CSV-Beilagen im Snapshot
                       (fetch_report.json) werden geprüft, aber nicht geparst.
  1.1.0 (27.09.2026) – NYSE-Kalender statt VIX-Datumsliste
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import holidays as _holidays
except ImportError:  # pragma: no cover
    _holidays = None

from .cboe import detect_file_kind, parse_cboe_index, parse_cboe_pcr
from .snapshot import verify_snapshot

# (Beginn, Ende, Label) – Ende inklusiv
PCR_SEGMENTS = [
    ("1900-01-01", "2012-05-31", "A_cleared_OCC"),
    ("2012-06-01", "2012-06-10", "B_uebergang"),
    ("2012-06-11", "2100-12-31", "C_preliminary_ohne_ETP"),
]

PCR_FILE_NAMES = {
    "totalpc.csv": "pcr_total",
    "equitypc.csv": "pcr_equity",
    "indexpc.csv": "pcr_index",
    "totalpcarchive.csv": "pcr_total_archive",
    # Fortschreibung aus Cboe Daily Market Statistics (ab 07.10.2019)
    "totalpc_daily.csv": "pcr_total_daily",
    "equitypc_daily.csv": "pcr_equity_daily",
    "indexpc_daily.csv": "pcr_index_daily",
    "etppc_daily.csv": "pcr_etp_daily",
    "vixpc_daily.csv": "pcr_vix_daily",
    "spxpc_daily.csv": "pcr_spx_daily",
}

# Gespleißte Reihen: Basis-CSV (bis 04.10.2019) + Daily-Fortschreibung
PCR_SPLICE = {"pcr_total": "pcr_total_daily",
              "pcr_equity": "pcr_equity_daily",
              "pcr_index": "pcr_index_daily"}
SPLICE_WINDOW = 60   # Handelstage je Seite für den Nahtstellen-Vergleich

# Plausibilitätsgrenzen (außerhalb → im Bericht, Werte bleiben unverändert)
BOUNDS = {
    "VIX": (5, 150), "VIX9D": (3, 200), "VIX3M": (5, 120), "VIX6M": (5, 100),
    "VIX1Y": (5, 100), "VVIX": (40, 250), "SKEW": (90, 200),
    "COR1M": (0, 100), "COR3M": (0, 100), "COR6M": (0, 100), "COR1Y": (0, 100),
    "pcr_": (0.1, 5.0),
}

STRESS_DAYS = ["2008-10-27", "2008-11-20", "2011-08-08", "2015-08-24",
               "2018-02-05", "2020-03-16", "2022-06-13", "2024-08-05"]


def nyse_calendar(start, end) -> pd.DatetimeIndex:
    """NYSE-Handelstage zwischen start und end (inklusiv)."""
    if _holidays is None:
        raise ImportError(
            "Paket 'holidays' fehlt – installieren mit:  pip install holidays")
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    days = pd.bdate_range(start, end)
    closed = _holidays.financial_holidays(
        "NYSE", years=range(start.year, end.year + 1))
    mask = [d.date() not in closed for d in days]
    cal = pd.DatetimeIndex(days[mask])
    cal.name = "date"
    return cal


def _load_dir(snapshot_dir: Path) -> tuple[dict[str, pd.Series], dict]:
    sums = verify_snapshot(snapshot_dir)
    series: dict[str, pd.Series] = {}
    meta = {"snapshot": str(snapshot_dir), "files": {}}
    for name in sorted(sums):
        f = snapshot_dir / name
        if f.suffix.lower() != ".csv":
            # Beilage (z. B. fetch_report.json): Hash geprüft, nicht geparst
            meta["files"][name] = {"sha256": sums[name], "kind": "beilage", "columns": []}
            continue
        kind = detect_file_kind(f)
        if kind == "index":
            s = parse_cboe_index(f)
            series[s.name] = s
            cols = [s.name]
        else:
            col = PCR_FILE_NAMES.get(name, "pcr_" + name.replace(".csv", ""))
            df = parse_cboe_pcr(f)
            series[col] = df["pcr"].rename(col)
            series[col + "_volume"] = df["total"].rename(col + "_volume")
            ratio = df["puts"] / df["calls"]
            meta.setdefault("pcr_consistency", {})[col] = int(
                ((ratio - df["pcr"]).abs() > 0.011).sum())
            cols = [col, col + "_volume"]
        meta["files"][name] = {"sha256": sums[name], "kind": kind, "columns": cols}
    return series, meta


def build_panel(snapshot_dirs, calendar_series: str = "VIX"):
    # calendar_series = Anker-Reihe, die den Zeitraum des Kalenders festlegt
    """Liest einen oder mehrere Snapshot-Ordner und baut das Tages-Panel.

    Kommt eine Reihe in mehreren Snapshots vor, gewinnt der alphabetisch
    letzte Ordner (= jüngstes Datum bei Ordnernamen YYYY-MM-DD).

    Rückgabe: (panel: DataFrame, info: dict mit Metadaten und Rohreihen)
    """
    dirs = sorted(Path(d) for d in (
        [snapshot_dirs] if isinstance(snapshot_dirs, (str, Path)) else snapshot_dirs))
    all_series: dict[str, pd.Series] = {}
    source_of: dict[str, str] = {}
    metas = []
    for d in dirs:
        series, meta = _load_dir(d)
        metas.append(meta)
        for k, s in series.items():
            all_series[k] = s
            source_of[k] = str(d)
    if calendar_series not in all_series:
        raise ValueError(
            f"Kalender-Reihe {calendar_series} fehlt – {calendar_series}_History.csv "
            "in einen Snapshot aufnehmen")
    anchor = all_series[calendar_series].dropna().index
    cal = nyse_calendar(anchor.min(), anchor.max())

    cols = {}
    off_calendar = {}
    duplicates = {}
    for k, s in all_series.items():
        dup = s.index.duplicated(keep="last")
        if dup.any():
            duplicates[k] = [d.strftime("%Y-%m-%d") for d in s.index[dup]]
            s = s[~dup]
        extra = s.index.difference(cal)
        if len(extra):
            off_calendar[k] = [d.strftime("%Y-%m-%d") for d in extra]
        cols[k] = s.reindex(cal)  # kein Forward-Fill
    panel = pd.DataFrame(cols, index=cal)
    panel.index.name = "date"
    splice = {}
    for base, daily in PCR_SPLICE.items():
        if base not in panel or daily not in panel:
            continue
        both = panel[base].notna() & panel[daily].notna()
        diff = (panel.loc[both, base] - panel.loc[both, daily]).abs()
        for suffix in ("", "_volume"):
            panel[f"{base}_full{suffix}"] = panel[base + suffix].combine_first(
                panel[daily + suffix])   # CSV hat Vorrang
            all_series[f"{base}_full{suffix}"] = panel[f"{base}_full{suffix}"].dropna()
            source_of[f"{base}_full{suffix}"] = f"{source_of[base]} + {source_of[daily]}"
        last_csv = panel[base].last_valid_index()
        first_daily = panel[daily].first_valid_index()
        splice[base] = {
            "csv_letzter_tag": None if last_csv is None else last_csv.strftime("%Y-%m-%d"),
            "daily_erster_tag": None if first_daily is None else first_daily.strftime("%Y-%m-%d"),
            "ueberlappung_tage": int(both.sum()),
            "ueberlappung_max_abweichung": None if diff.empty else round(float(diff.max()), 4),
        }
    panel = panel[sorted(panel.columns, key=lambda c: (c.startswith("pcr"), c))]

    seg = pd.Series(pd.NA, index=cal, dtype="object")
    for start, end, label in PCR_SEGMENTS:
        seg[(cal >= pd.Timestamp(start)) & (cal <= pd.Timestamp(end))] = label
    panel["pcr_segment"] = seg

    info = {
        "calendar_series": f"NYSE (Zeitraum aus {calendar_series})",
        "calendar_start": cal.min().strftime("%Y-%m-%d"),
        "calendar_end": cal.max().strftime("%Y-%m-%d"),
        "calendar_days": int(len(cal)),
        "snapshots": metas,
        "source_of": source_of,
        "off_calendar": off_calendar,
        "duplicates": duplicates,
        "raw_series": all_series,
        "pcr_splice": splice,
    }
    return panel, info


def _bounds_for(col: str):
    if col.endswith("_volume"):
        return None
    if col.startswith("pcr_"):
        return BOUNDS["pcr_"]
    return BOUNDS.get(col)


def quality_report(panel: pd.DataFrame, info: dict) -> dict:
    """Maschinenlesbarer QC-Bericht; `status` = OK | WARN | ERROR."""
    cols = [c for c in panel.columns if c != "pcr_segment"]
    per = {}
    status = "OK"
    for c in cols:
        raw = info["raw_series"][c]
        s = panel[c]
        valid = s.dropna()
        if valid.empty:
            per[c] = {"status": "ERROR", "reason": "keine Werte im Kalender"}
            status = "ERROR"
            continue
        first, last = valid.index.min(), valid.index.max()
        inside = s.loc[first:last]
        missing = inside[inside.isna()].index
        b = _bounds_for(c)
        out_of_bounds = [] if b is None else [
            d.strftime("%Y-%m-%d") for d in valid.index[(valid < b[0]) | (valid > b[1])]]
        nonpos = int((valid <= 0).sum()) if not c.endswith("_volume") else 0
        entry = {
            "start": first.strftime("%Y-%m-%d"),
            "end": last.strftime("%Y-%m-%d"),
            "rows": int(valid.size),
            "raw_rows": int(raw.size),
            "missing_in_range": int(len(missing)),
            "missing_examples": [d.strftime("%Y-%m-%d") for d in missing[:10]],
            "off_calendar_dropped": len(info["off_calendar"].get(c, [])),
            "off_calendar_examples": info["off_calendar"].get(c, [])[:10],
            "duplicates": len(info["duplicates"].get(c, [])),
            "out_of_bounds": out_of_bounds[:20],
            "non_positive": nonpos,
            "source": info["source_of"].get(c),
        }
        st = "OK"
        if entry["duplicates"] or nonpos:
            st = "ERROR"
        elif entry["missing_in_range"] > 0.01 * valid.size or out_of_bounds \
                or entry["off_calendar_dropped"]:
            st = "WARN"
        entry["status"] = st
        per[c] = entry
        if st == "ERROR" or (st == "WARN" and status == "OK"):
            status = st

    stress = {}
    for d in STRESS_DAYS:
        ts = pd.Timestamp(d)
        if ts in panel.index:
            row = panel.loc[ts, cols]
            stress[d] = {k: (None if pd.isna(v) else round(float(v), 2))
                         for k, v in row.items() if not k.endswith("_volume")}
    consistency = {}
    for m in info["snapshots"]:
        consistency.update(m.get("pcr_consistency", {}))

    pcr_seg_means = {}
    for c in [c for c in cols if c.startswith("pcr_") and not c.endswith("_volume")]:
        g = panel.groupby("pcr_segment")[c].agg(["count", "mean"]).dropna()
        pcr_seg_means[c] = {k: {"n": int(v["count"]), "mittel": round(float(v["mean"]), 3)}
                            for k, v in g.iterrows()}

    return {
        "status": status,
        "calendar": {k: info[k] for k in
                     ["calendar_series", "calendar_start", "calendar_end", "calendar_days"]},
        "series": per,
        "stress_days": stress,
        "pcr_ratio_check_mismatches": consistency,
        "pcr_segment_means": pcr_seg_means,
        "pcr_splice": _splice_report(panel, info),
        "snapshots": [{"snapshot": m["snapshot"],
                       "files": {k: v["sha256"] for k, v in m["files"].items()}}
                      for m in info["snapshots"]],
    }


def _splice_report(panel: pd.DataFrame, info: dict) -> dict:
    """Nahtstelle CSV → Daily: Kennzahlen je SPLICE_WINDOW Handelstage davor/danach.

    Ohne Überlappung ist nur ein statistischer Vergleich möglich; ein deutlicher
    Niveausprung wäre ein Hinweis auf abweichende Abgrenzung (nicht automatisch
    ein Fehler – Marktphasen ändern sich auch).
    """
    out = {}
    for base, meta in info.get("pcr_splice", {}).items():
        full = panel.get(base + "_full")
        if full is None or meta["csv_letzter_tag"] is None or meta["daily_erster_tag"] is None:
            out[base] = dict(meta)
            continue
        before = panel[base].dropna().loc[:meta["csv_letzter_tag"]].tail(SPLICE_WINDOW)
        after = panel[PCR_SPLICE[base]].dropna().loc[
            meta["daily_erster_tag"]:].head(SPLICE_WINDOW)
        gap = panel.loc[meta["csv_letzter_tag"]:meta["daily_erster_tag"]].index
        out[base] = dict(meta, **{
            "handelstage_zwischen": int(max(len(gap) - 2, 0)),
            "mittel_davor": round(float(before.mean()), 3),
            "mittel_danach": round(float(after.mean()), 3),
            "std_davor": round(float(before.std()), 3),
            "std_danach": round(float(after.std()), 3),
            "fenster": SPLICE_WINDOW,
        })
    return out


def report_markdown(qc: dict) -> str:
    L = [f"# Datenqualitätsbericht – Status: **{qc['status']}**", ""]
    c = qc["calendar"]
    L += [f"Kalender: {c['calendar_series']} · {c['calendar_start']} – "
          f"{c['calendar_end']} · {c['calendar_days']} Handelstage", ""]
    L += ["| Reihe | Status | Zeitraum | Werte | Lücken im Zeitraum | "
          "außerhalb Kalender (verworfen) | Plausibilität |",
          "|---|---|---|---|---|---|---|"]
    for k, e in qc["series"].items():
        if e.get("status") == "ERROR" and "reason" in e:
            L.append(f"| {k} | ERROR | – | – | – | – | {e['reason']} |")
            continue
        L.append(f"| {k} | {e['status']} | {e['start']} – {e['end']} | {e['rows']} | "
                 f"{e['missing_in_range']} | {e['off_calendar_dropped']} | "
                 f"{len(e['out_of_bounds'])} außerhalb |")
    L += ["", "## Details zu Auffälligkeiten", ""]
    any_detail = False
    for k, e in qc["series"].items():
        parts = []
        if e.get("missing_examples"):
            parts.append("Lücken z. B. " + ", ".join(e["missing_examples"]))
        if e.get("off_calendar_examples"):
            parts.append("außerhalb Kalender z. B. " + ", ".join(e["off_calendar_examples"]))
        if e.get("out_of_bounds"):
            parts.append("außerhalb Plausibilität: " + ", ".join(e["out_of_bounds"][:10]))
        if parts:
            any_detail = True
            L.append(f"- **{k}:** " + "; ".join(parts))
    if not any_detail:
        L.append("- keine")
    L += ["", "## Stresstage (Stichprobe)", ""]
    for d, row in qc["stress_days"].items():
        vals = ", ".join(f"{k} {v}" for k, v in row.items() if v is not None)
        L.append(f"- {d}: {vals}")
    L += ["", "## Put/Call-Ratio", ""]
    for k, n in qc["pcr_ratio_check_mismatches"].items():
        L.append(f"- {k}: {n} Tage, an denen P/C-Ratio ≠ Puts/Calls (Toleranz 0,011)")
    for k, segs in qc["pcr_segment_means"].items():
        L.append(f"- {k} Mittel je Segment: " + "; ".join(
            f"{s} {v['mittel']} (n={v['n']})" for s, v in segs.items()))
    if qc.get("pcr_splice"):
        L += ["", "## PCR-Nahtstelle CSV → Daily", ""]
        for k, v in qc["pcr_splice"].items():
            txt = (f"- {k}: CSV bis {v['csv_letzter_tag']}, Daily ab {v['daily_erster_tag']}, "
                   f"Überlappung {v['ueberlappung_tage']} Tage")
            if "mittel_davor" in v:
                txt += (f", {v['handelstage_zwischen']} Handelstage dazwischen; "
                        f"Mittel {v['fenster']} Tage davor {v['mittel_davor']} "
                        f"(σ {v['std_davor']}) · danach {v['mittel_danach']} (σ {v['std_danach']})")
            L.append(txt)
    L += ["", "## Snapshots", ""]
    for s in qc["snapshots"]:
        L.append(f"- `{s['snapshot']}`: {len(s['files'])} Dateien, SHA-256 geprüft")
    return "\n".join(L) + "\n"


def write_outputs(panel: pd.DataFrame, qc: dict, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out / "panel.csv", float_format="%.6g")
    (out / "qc_report.json").write_text(json.dumps(qc, indent=2, ensure_ascii=False))
    (out / "qc_report.md").write_text(report_markdown(qc))
    return {"panel": str(out / "panel.csv"), "qc_json": str(out / "qc_report.json"),
            "qc_md": str(out / "qc_report.md")}
