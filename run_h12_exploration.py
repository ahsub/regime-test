#!/usr/bin/env python3
"""
run_h12_exploration.py – Explorationsaudit H12-E1: Marktbreite-Divergenz vor Regimewechseln

Version: 1.0.0 (29.09.2026, Claude + Axel)
Protokoll: docs/exploration/H12_E1_BREITE_VOR_REGIMEWECHSEL.md (Rev. 1) – dieses Skript
           setzt es 1:1 um und wurde VOR Abruf/Sichtung der ETF-Daten geschrieben und
           nur mit synthetischen Daten getestet (--selbsttest).

Rein deskriptiv: kein Renditetest, keine Schwellenoptimierung, keine p-Werte.

Aufruf:
    python3 run_h12_exploration.py --selbsttest
    python3 run_h12_exploration.py --yahoo data/raw/yahoo/<abrufdatum>
Ausgabe: results/h12_exploration/H12_E1.json und H12_E1.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

CBOE = ROOT / "data" / "raw" / "cboe" / "2026-09-27"
SQZ = ROOT / "data" / "raw" / "squeezemetrics" / "2026-08-30"
OUT = ROOT / "results" / "h12_exploration"

# ── Protokoll §2/§3 – fest ──────────────────────────────────────────────────
ETFS = ("SPY", "RSP", "IWM")
PAIRS = (("SPY", "RSP"), ("SPY", "IWM"))
HORIZONS = (5, 10, 20)
PCT_WINDOW = 252
PRE_WINDOW = 20
LEAD_LOOKBACK = 60
FA_HORIZON = 20
STATE_CUT = 0.90
WINDOW = ("2009-09-18", "2026-09-25")
PERIODS = {"gesamt": WINDOW,
           "2009-2016": ("2009-09-18", "2016-12-31"),
           "2017-2026": ("2017-01-01", "2026-09-25")}
BULL = {"BULL_QUIET", "BULL_FRAGILE"}
STRESS_SET = {"STRESS_UNSTABLE", "POST_PANIC_REVERSION"}
DECILE_EDGES = np.round(np.arange(0.0, 1.0001, 0.1), 1)


# ── Kernrechnung (rein, testbar) ────────────────────────────────────────────
def divergence(px: pd.DataFrame, a: str, b: str, h: int) -> pd.Series:
    """D_{a,b}(t,h) = R_a(t-h,t) - R_b(t-h,t); Shift in Handelstagen des gemeinsamen Kalenders."""
    ra = px[a] / px[a].shift(h) - 1.0
    rb = px[b] / px[b].shift(h) - 1.0
    return ra - rb


def pct_rank_252(d: pd.Series, n: int = PCT_WINDOW) -> pd.Series:
    """P(D_t) = (1/n) * #{i in t-n+1..t : D_i <= D_t}; nur mit vollständigem Fenster, kein Look-ahead."""
    def f(w: np.ndarray) -> float:
        if np.isnan(w).any():
            return np.nan
        return float((w <= w[-1]).sum()) / len(w)
    return d.rolling(n, min_periods=n).apply(f, raw=True)


def regime_series(vix: pd.Series, vix3m: pd.Series, gex: pd.Series | None) -> pd.Series:
    from compare_approaches_final_v2 import classify_regime_v2  # unverändert (7193f04)
    out = {}
    for d in vix.index:
        v, v3 = vix.get(d), vix3m.get(d)
        v = None if pd.isna(v) else float(v)
        v3 = None if pd.isna(v3) else float(v3)
        g = None
        if gex is not None and d in gex.index and not pd.isna(gex.loc[d]):
            g = float(gex.loc[d])
        out[d] = classify_regime_v2(v, v3, g)[0]
    return pd.Series(out, name="regime")


def find_events(reg: pd.Series, clean: bool) -> list:
    """Ereignis an Position t: reg[t-1] in BULL und reg[t] in STRESS_SET.
    clean=True: zusätzlich reg[t-20..t-1] vollständig in BULL."""
    r = reg.tolist()
    ev = []
    for t in range(1, len(r)):
        if r[t - 1] in BULL and r[t] in STRESS_SET:
            if clean:
                if t < PRE_WINDOW or not all(x in BULL for x in r[t - PRE_WINDOW:t]):
                    continue
            ev.append(t)
    return ev


def episode_starts(p: pd.Series) -> list:
    s = (p >= STATE_CUT).fillna(False).to_numpy()
    return [i for i in range(len(s)) if s[i] and (i == 0 or not s[i - 1])]


def summarize(vals: np.ndarray) -> dict:
    vals = vals[~np.isnan(vals)]
    if len(vals) == 0:
        return {"n": 0}
    hist, _ = np.histogram(vals, bins=DECILE_EDGES)
    return {"n": int(len(vals)), "median": round(float(np.median(vals)), 4),
            "anteil_ge_0_90": round(float((vals >= STATE_CUT).mean()), 4),
            "dezile": [round(float(x) / len(vals), 4) for x in hist]}


def analyze(frame: pd.DataFrame, regime: pd.Series, period_mask: dict, clean: bool) -> dict:
    """frame: gemeinsamer Kalender, Spalten P252 je Maß. regime: gleicher Index.
    period_mask: {name: bool-Array} – Zugehörigkeit nach Datum (Ereignis-/Episoden-/Tagesdatum)."""
    idx = frame.index
    events = find_events(regime, clean)
    in_win = period_mask["gesamt"]
    events = [t for t in events if in_win[t]]
    res = {"ereignisse": {}, "masse": {}}
    for per, m in period_mask.items():
        res["ereignisse"][per] = [idx[t].strftime("%Y-%m-%d") for t in events if m[t]]
    ev_set = set(events)
    n = len(idx)
    # Grundrate: Tage d im Fenster mit d+FA_HORIZON im Fenster, Ereignis in d+1..d+FA_HORIZON
    ev_arr = np.zeros(n, dtype=bool)
    ev_arr[list(ev_set)] = True
    for col in frame.columns:
        p = frame[col].to_numpy(dtype=float)
        starts = [s for s in episode_starts(frame[col]) if in_win[s]]
        out = {}
        for per, m in period_mask.items():
            ev_p = [t for t in events if m[t]]
            pre_vals, per_event = [], []
            for t in ev_p:
                w = p[max(0, t - PRE_WINDOW):t]
                pre_vals.extend(w.tolist())
                wv = w[~np.isnan(w)]
                per_event.append({"datum": idx[t].strftime("%Y-%m-%d"),
                                  "max_p252_vorfenster": None if len(wv) == 0 else round(float(wv.max()), 4)})
            uncond = p[m]
            leads = []
            for t in ev_p:
                cands = [s for s in starts if t - LEAD_LOOKBACK <= s <= t - 1]
                leads.append(None if not cands else int(t - max(cands)))
            st_p = [s for s in starts if m[s] and s + FA_HORIZON < n and in_win[s + FA_HORIZON]]
            fa = [not ev_arr[s + 1:s + FA_HORIZON + 1].any() for s in st_p]
            days = [d for d in range(n) if m[d] and d + FA_HORIZON < n and in_win[d + FA_HORIZON]]
            base = [bool(ev_arr[d + 1:d + FA_HORIZON + 1].any()) for d in days]
            lv = [x for x in leads if x is not None]
            out[per] = {
                "vorfenster": summarize(np.array(pre_vals, dtype=float)),
                "unbedingt": summarize(uncond.astype(float)),
                "je_ereignis": per_event,
                "vorlauf": {"n_ereignisse": len(leads),
                            "ohne_vorlauf": int(sum(1 for x in leads if x is None)),
                            "abstaende": lv,
                            "median": None if not lv else float(np.median(lv))},
                "fehlalarme": {"episodenbeginne": len(st_p),
                               "ohne_ereignis_20T": int(sum(fa)),
                               "anteil": None if not st_p else round(sum(fa) / len(st_p), 4),
                               "grundrate_ereignis_20T": None if not days else round(sum(base) / len(days), 4)},
            }
        res["masse"][col] = out
    return res


def durations(regime: pd.Series, events: list) -> dict:
    r = regime.tolist()
    ds = []
    for t in events:
        k = t
        while k < len(r) and r[k] in STRESS_SET:
            k += 1
        ds.append(k - t)
    return {"n": len(ds), "median_tage": None if not ds else float(np.median(ds)),
            "anteil_ein_tag": None if not ds else round(sum(1 for d in ds if d == 1) / len(ds), 4)}


def build_frame(px: pd.DataFrame) -> pd.DataFrame:
    cols = {}
    for a, b in PAIRS:
        for h in HORIZONS:
            cols[f"D_{a}_{b}_{h}T"] = pct_rank_252(divergence(px, a, b, h))
    return pd.DataFrame(cols, index=px.index)


def masks(index: pd.DatetimeIndex) -> dict:
    return {k: ((index >= pd.Timestamp(a)) & (index <= pd.Timestamp(b))) for k, (a, b) in PERIODS.items()}


def run(px: pd.DataFrame, vix: pd.Series, vix3m: pd.Series, gex: pd.Series) -> dict:
    cal = px.dropna().index.intersection(vix.dropna().index).intersection(vix3m.dropna().index)
    px, vix, vix3m = px.loc[cal], vix.loc[cal], vix3m.loc[cal]
    frame = build_frame(px)
    mk = masks(cal)
    out = {"gemeinsame_handelstage": int(len(cal)),
           "kalender": [cal.min().strftime("%Y-%m-%d"), cal.max().strftime("%Y-%m-%d")],
           "varianten": {}}
    reg_prim = regime_series(vix, vix3m, None)
    g0, g1 = gex.dropna().index.min(), gex.dropna().index.max()
    sec_idx = cal[(cal >= g0) & (cal <= g1)]
    reg_sec = regime_series(vix.loc[sec_idx], vix3m.loc[sec_idx], gex)
    for vname, reg, fr in (("primaer_ohne_GEX", reg_prim, frame),
                            ("sekundaer_mit_GEX", reg_sec, frame.loc[sec_idx])):
        mkv = masks(fr.index)
        vres = {"fenster": [fr.index.min().strftime("%Y-%m-%d"), fr.index.max().strftime("%Y-%m-%d")],
                "regime_tage": {k: int(v) for k, v in reg.value_counts().items()}}
        for ename, clean in (("alle_ereignisse", False), ("sauberer_beginn", True)):
            a = analyze(fr, reg, mkv, clean)
            ev_all = [t for t in find_events(reg, clean) if mkv["gesamt"][t]]
            a["dauer_nach_ereignis"] = durations(reg, ev_all)
            vres[ename] = a
        out["varianten"][vname] = vres
    return out


# ── Laden echter Daten ──────────────────────────────────────────────────────
def load(yahoo_dir: Path):
    from datalayer import build_panel, verify_snapshot
    hashes = {"cboe": verify_snapshot(CBOE), "yahoo": verify_snapshot(yahoo_dir),
              "squeezemetrics": verify_snapshot(SQZ)}
    manifest = json.loads((yahoo_dir / "MANIFEST.json").read_text())
    panel, _ = build_panel(CBOE)
    px = {}
    for t in ETFS:
        df = pd.read_csv(yahoo_dir / f"{t}.csv", index_col=0, parse_dates=True)
        px[t] = df["Adj Close"].astype(float)
    px = pd.DataFrame(px)
    dix = pd.read_csv(SQZ / "DIX.csv", index_col=0, parse_dates=True)
    gex = dix["gex"].astype(float)
    missing = {t: int(px[t].isna().sum()) for t in ETFS}
    return px, panel["VIX"], panel["VIX3M"], gex, hashes, manifest, missing


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                                       text=True).strip()
    except Exception:
        return "unbekannt"


def render_md(res: dict) -> str:
    L = [f"# H12-E1 – Marktbreite-Divergenz vor Regimewechseln (Exploration, run_h12_exploration.py {VERSION})", "",
         "Rein deskriptiv, Protokoll `docs/exploration/H12_E1_BREITE_VOR_REGIMEWECHSEL.md` Rev. 1. "
         "Kein Renditetest, keine Schwellenoptimierung, keine p-Werte.", "",
         f"Skript-Commit: `{res['skript_commit']}` · gemeinsame Handelstage: {res['gemeinsame_handelstage']} "
         f"({res['kalender'][0]} … {res['kalender'][1]})", "",
         "Snapshots (SHA-256): " + "; ".join(f"{k}: {len(v)} Dateien" for k, v in res['snapshots'].items()), ""]
    for vname, v in res["varianten"].items():
        L += [f"## Variante {vname} ({v['fenster'][0]} … {v['fenster'][1]})", "",
              "Regime-Tage: " + ", ".join(f"{k} {n}" for k, n in v["regime_tage"].items()), ""]
        for ename in ("alle_ereignisse", "sauberer_beginn"):
            e = v[ename]
            L += [f"### Ereignisse: {ename}", "",
                  "Anzahl je Teilfenster: " + ", ".join(f"{p} {len(x)}" for p, x in e["ereignisse"].items())
                  + f" · Dauer nach Ereignis: Median {e['dauer_nach_ereignis']['median_tage']} Tage, "
                    f"Anteil Ein-Tages-Phasen {e['dauer_nach_ereignis']['anteil_ein_tag']}", "",
                  "| Maß | Teilfenster | P252 Median Vorfenster | unbedingt | Anteil ≥ 0,90 Vorfenster | unbedingt | "
                  "Ereignisse ohne Vorlauf | Median Vorlauf (T) | Episodenbeginne | ohne Ereignis in 20T | Grundrate |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
            for m, per in e["masse"].items():
                for p, x in per.items():
                    vf, ub, vl, fa = x["vorfenster"], x["unbedingt"], x["vorlauf"], x["fehlalarme"]
                    L.append(f"| {m} | {p} | {vf.get('median')} | {ub.get('median')} | {vf.get('anteil_ge_0_90')} | "
                             f"{ub.get('anteil_ge_0_90')} | {vl['ohne_vorlauf']}/{vl['n_ereignisse']} | {vl['median']} | "
                             f"{fa['episodenbeginne']} | {fa['anteil']} | {fa['grundrate_ereignis_20T']} |")
            L.append("")
    L += ["Dezilverteilungen, Einzelereignisse und Vorlaufabstände: `H12_E1.json`.", "",
          "**Zulässige Aussagen:** nur beschreibend (Protokoll §5). Keine Aussagen über Renditen, Prognosegüte, "
          "„Frühindikator“ oder ein „bestes“ Maß."]
    return "\n".join(L) + "\n"


# ── Selbsttest (synthetisch) ────────────────────────────────────────────────
def selbsttest() -> int:
    ok = True
    # 1. Perzentil-Definition an bekanntem Beispiel
    s = pd.Series([3.0, 1.0, 2.0, 5.0, 4.0])
    r = pct_rank_252(s, n=3).tolist()
    exp = [np.nan, np.nan, 2 / 3, 1.0, 2 / 3]
    ok &= all((np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-12 for a, b in zip(r, exp))
    print(f"  Perzentil-Definition: {'OK' if ok else 'FEHLER'} {r}")
    # 2. kein Look-ahead: Veränderung der Zukunft ändert P252 der Vergangenheit nicht
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("2005-01-03", periods=1600)
    base = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, (1600, 3)), axis=0))
    px = pd.DataFrame(base, index=idx, columns=list(ETFS))
    f1 = build_frame(px)
    px2 = px.copy()
    px2.iloc[1200:] *= 1.5
    px2.iloc[1300:, 1] *= 0.5
    f2 = build_frame(px2)
    la = f1.iloc[:1200].equals(f2.iloc[:1200])
    print(f"  Kein Look-ahead (Zukunft verändert, Vergangenheit identisch): {'OK' if la else 'FEHLER'}")
    ok &= la
    # 3. Divergenz = Renditedifferenz, nicht Indexstand-Differenz
    d = divergence(px, "SPY", "RSP", 5)
    t = 500
    exp_d = px["SPY"].iloc[t] / px["SPY"].iloc[t - 5] - px["RSP"].iloc[t] / px["RSP"].iloc[t - 5]
    dk = abs(d.iloc[t] - exp_d) < 1e-12
    print(f"  Divergenz-Formel: {'OK' if dk else 'FEHLER'}")
    ok &= dk
    # 4. Ereigniserkennung
    reg = pd.Series(["BULL_QUIET"] * 25 + ["STRESS_UNSTABLE"] + ["BULL_FRAGILE"] * 3 + ["POST_PANIC_REVERSION"])
    ea, ec = find_events(reg, False), find_events(reg, True)
    ek = ea == [25, 29] and ec == [25]
    print(f"  Ereignisse alle={ea} sauber={ec}: {'OK' if ek else 'FEHLER'}")
    ok &= ek
    # 5. Pipeline end-to-end mit eingebautem Vorlauf (Plausibilität, keine Aussage über echte Daten)
    n = len(idx)
    vix = pd.Series(15.0, index=idx)
    vix3m = pd.Series(17.0, index=idx)
    ev_pos = list(range(400, n - 50, 120))
    spy = px["SPY"].to_numpy().copy()
    for e in ev_pos:
        vix3m.iloc[e:e + 3] = 13.0          # Ratio < 0,98 -> STRESS
        spy[e - 10:] *= 1.03                # SPY läuft 10 Tage vorher voraus
    pxs = px.copy()
    pxs["SPY"] = spy
    gex = pd.Series(1.0, index=idx[600:1500])
    res = run(pxs, vix, vix3m, gex)
    x = res["varianten"]["primaer_ohne_GEX"]["alle_ereignisse"]["masse"]["D_SPY_RSP_20T"]["gesamt"]
    pk = (x["vorfenster"]["median"] or 0) > (x["unbedingt"]["median"] or 1)
    print(f"  End-to-end: {res['gemeinsame_handelstage']} Tage, Ereignisse "
          f"{len(res['varianten']['primaer_ohne_GEX']['alle_ereignisse']['ereignisse']['gesamt'])}, "
          f"eingebauter Vorlauf sichtbar: {'OK' if pk else 'FEHLER'}")
    ok &= pk
    json.dumps(res)  # serialisierbar
    render_md({**res, "skript_commit": "test", "snapshots": {}})
    print("SELBSTTEST", "BESTANDEN" if ok else "FEHLGESCHLAGEN")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yahoo", type=Path, help="data/raw/yahoo/<abrufdatum>")
    ap.add_argument("--selbsttest", action="store_true")
    a = ap.parse_args()
    if a.selbsttest:
        return selbsttest()
    if not a.yahoo:
        ap.error("--yahoo erforderlich (oder --selbsttest)")
    yd = a.yahoo if a.yahoo.is_absolute() else ROOT / a.yahoo
    px, vix, vix3m, gex, hashes, manifest, missing = load(yd)
    res = run(px, vix, vix3m, gex)
    res.update({"version": VERSION, "skript_commit": git_commit(), "snapshots": hashes,
                "yahoo_manifest": manifest, "fehlende_werte_etf": missing,
                "protokoll": "docs/exploration/H12_E1_BREITE_VOR_REGIMEWECHSEL.md Rev. 1"})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "H12_E1.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    (OUT / "H12_E1.md").write_text(render_md(res))
    print(f"Geschrieben: {OUT / 'H12_E1.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
