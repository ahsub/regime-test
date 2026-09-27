"""
run_phase3_h1.py – Phase 3, Hypothese H1 (Laufzeit-Gate) – strikt nach Präregistrierung
docs/preregistration/H1_laufzeit_gate.md (Rev. 3, Commit 8e05c0a, 27.09.2026 13:40).

Ablauf (zweistufig, Reihenfolge erzwungen):
  1. Entwicklungsfenster: alle 16 Versuche rechnen, je (L, Variante) t wählen,
     primären Kandidaten bestimmen → results/phase3/H1_auswahl.json (wird nie überschrieben;
     existiert die Datei schon, wird sie geprüft und unverändert verwendet).
  2. Bestätigungsfenster: alle 16 Versuche protokollieren, Entscheidung nur über den
     primären Kandidaten; sekundäre Kandidaten als „x von 3“.

Aufruf:  python run_phase3_h1.py
Ergebnis: results/phase3/H1_auswahl.json, H1_ergebnis.json, H1_bericht.md

Version: 1.0.0 (27.09.2026)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from datalayer import build_panel, verify_snapshot  # noqa: E402
from compare_approaches_final_v2 import (  # noqa: E402  (Baseline unverändert)
    classify_regime_v2, regime_to_position_uniform)

PREREG = ROOT / "docs" / "preregistration" / "H1_laufzeit_gate.md"
PREREG_SHA = "63627e1f436248ed6e4c0c151befa040481cb67466ad3b8a4a0a032c6a602531"
CBOE = ROOT / "data" / "raw" / "cboe" / "2026-09-27"
YAHOO = ROOT / "data" / "raw" / "yahoo" / "2026-09-27"
OUT = ROOT / "results" / "phase3"

T_GRID = [0.95, 1.00, 1.05, 1.10]
LAUFZEITEN = {"6M": "VIX6M", "1Y": "VIX1Y"}
KOSTEN_HAUPT = 0.0005
KOSTEN_SENS = [0.0, 0.0010]
RF = 0.02 / 252
TIE = 0.01

DEV_END = "2016-12-30"
CONF = ("2017-01-03", "2026-09-25")
O_DEV_START = "2009-09-18"

STRESS = [  # (Name, Anfang, Ende, Fenster)
    ("Finanzkrise 2008", "2008-09-01", "2009-03-09", "dev"),
    ("Flash Crash / Euro 2010", "2010-04-23", "2010-07-02", "dev"),
    ("US-Downgrade 2011", "2011-07-22", "2011-10-03", "dev"),
    ("China / August 2015", "2015-08-17", "2015-09-30", "dev"),
    ("Volmageddon 2018", "2018-01-26", "2018-02-09", "conf"),
    ("2018 Q4", "2018-10-01", "2018-12-24", "conf"),
    ("Covid 2020", "2020-02-19", "2020-03-23", "conf"),
    ("Bärenmarkt 2022", "2022-01-03", "2022-10-12", "conf"),
    ("Yen-Carry 2024", "2024-07-16", "2024-08-07", "conf"),
]


# ---------------------------------------------------------------- Daten
def load():
    sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    if sha != PREREG_SHA:
        raise SystemExit(f"ABBRUCH: Präregistrierung verändert (sha256 {sha})")
    verify_snapshot(YAHOO)
    panel, _ = build_panel(CBOE)
    spx = pd.read_csv(YAHOO / "GSPC.csv", index_col=0, parse_dates=True)["Close"]
    ret = spx.pct_change().rename("ret")
    idx = panel.index.intersection(ret.index)
    return panel.loc[idx], ret.loc[idx]


def baseline_target(panel: pd.DataFrame) -> pd.Series:
    out = {}
    for d, v, v3 in zip(panel.index, panel["VIX"], panel["VIX3M"]):
        v = None if pd.isna(v) else float(v)
        v3 = None if pd.isna(v3) else float(v3)
        regime, _ = classify_regime_v2(v, v3, None)
        out[d] = regime_to_position_uniform(regime)
    return pd.Series(out, name="baseline")


# ---------------------------------------------------------------- Simulation
def simulate(target: pd.Series, ret: pd.Series, start, end, cost: float) -> pd.Series:
    """Tagesrenditen nach Präregistrierung Abschnitt 5/7.

    target: Zielposition je Tag (NaN = kein Signal → Vortagsposition bleibt).
    Position vor Fensterbeginn = 0; Position von Tag t gilt ab t+1;
    Kosten_t = cost × |Pos_t − Pos_(t−1)|.
    """
    tg = target.loc[start:end]
    rr = ret.loc[tg.index]
    pos = tg.ffill().fillna(0.0)
    prev = pos.shift(1).fillna(0.0)
    costs = cost * (pos - prev).abs()
    r = prev * rr.fillna(0.0) - costs
    return r


def metrics(r: pd.Series, pos: pd.Series | None = None) -> dict:
    eq = (1 + r).cumprod()
    n = len(r)
    cagr = float(eq.iloc[-1] ** (252 / n) - 1)
    dd_series = eq / eq.cummax() - 1
    mdd = float(dd_series.min())
    calmar = cagr / abs(mdd) if mdd < 0 else float("nan")
    ex = r - RF
    sharpe = float(np.sqrt(252) * ex.mean() / ex.std(ddof=0)) if ex.std(ddof=0) > 0 else 0.0
    k = max(1, int(round(0.05 * n)))
    cvar = float(np.sort(r.to_numpy())[:k].mean())
    ulcer = float(np.sqrt((dd_series ** 2).mean()))
    m = {"start": r.index.min().strftime("%Y-%m-%d"), "ende": r.index.max().strftime("%Y-%m-%d"),
         "tage": n, "cagr": round(cagr, 5), "max_dd": round(mdd, 5),
         "calmar": round(calmar, 4), "sharpe": round(sharpe, 4),
         "cvar5": round(cvar, 5), "ulcer": round(ulcer, 5)}
    if pos is not None:
        m["zeit_im_markt"] = round(float((pos > 0).mean()), 4)
        m["trades"] = int((pos != pos.shift(1)).sum())
    return m


def stress(r: pd.Series, which: str) -> dict:
    eq = (1 + r).cumprod()
    out = {}
    for name, a, b, w in STRESS:
        if w != which:
            continue
        pre = eq.loc[:pd.Timestamp(a) - pd.Timedelta(days=1)]
        seg = eq.loc[a:b]
        if len(pre) == 0 or len(seg) == 0:
            out[name] = None
            continue
        out[name] = round(float(seg.iloc[-1] / pre.iloc[-1] - 1), 5)
    return out


def run_case(target, ret, start, end, cost, which):
    r = simulate(target, ret, start, end, cost)
    pos = target.loc[start:end].ffill().fillna(0.0)
    m = metrics(r, pos)
    m["stress"] = stress(r, which)
    return m


# ---------------------------------------------------------------- Versuche
def targets(panel, base):
    tg = {}
    for L, col in LAUFZEITEN.items():
        R = panel[col] / panel["VIX"]
        for t in T_GRID:
            gate = pd.Series(np.where(R >= t, 1.0, 0.0), index=R.index)
            gate[R.isna()] = np.nan
            tg[("S", L, t)] = gate
            ov = pd.Series(np.where(R >= t, base, 0.0), index=R.index)
            ov[R.isna()] = np.nan
            tg[("O", L, t)] = ov
    return tg


def dev_window(var, L, panel):
    if var == "O":
        return O_DEV_START, DEV_END
    first = panel[LAUFZEITEN[L]].dropna().index.min().strftime("%Y-%m-%d")
    return first, DEV_END


def key(var, L, t):
    return f"{var}-{L}-t{t:.2f}"


def select(dev_res):
    chosen = {}
    for var in ["S", "O"]:
        for L in LAUFZEITEN:
            cands = [(t, dev_res[key(var, L, t)]["calmar"]) for t in T_GRID]
            best = max(c for _, c in cands)
            t_sel = max(t for t, c in cands if c >= best - TIE)   # Gleichstand → größeres t
            chosen[f"{var}-{L}"] = {"t": t_sel, "calmar_dev": dev_res[key(var, L, t_sel)]["calmar"]}
    o6, o1 = chosen["O-6M"]["calmar_dev"], chosen["O-1Y"]["calmar_dev"]
    primary = "O-6M" if o6 >= o1 - TIE else "O-1Y"   # Gleichstand → O-6M
    return chosen, primary


def main() -> int:
    panel, ret = load()
    base = baseline_target(panel)
    tg = targets(panel, base)
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------------- Stufe 1: Entwicklung
    dev = {}
    for (var, L, t), target in tg.items():
        a, b = dev_window(var, L, panel)
        dev[key(var, L, t)] = run_case(target, ret, a, b, KOSTEN_HAUPT, "dev")
    ref_dev = {"baseline_O": run_case(base, ret, O_DEV_START, DEV_END, KOSTEN_HAUPT, "dev")}
    for L in LAUFZEITEN:
        a, b = dev_window("S", L, panel)
        bh = pd.Series(1.0, index=panel.index)
        ref_dev[f"buy_hold_S-{L}"] = run_case(bh, ret, a, b, KOSTEN_HAUPT, "dev")

    chosen, primary = select(dev)
    auswahl = {"praeregistrierung_sha256": PREREG_SHA, "kandidaten": chosen, "primaer": primary}
    af = OUT / "H1_auswahl.json"
    if af.exists():
        stored = json.loads(af.read_text())
        if stored != auswahl:
            raise SystemExit("ABBRUCH: gespeicherte Auswahl weicht ab – nicht überschreiben.")
        print("Auswahl existiert bereits und ist identisch → wird verwendet.")
    else:
        af.write_text(json.dumps(auswahl, indent=2, ensure_ascii=False))
        print(f"Auswahl festgeschrieben: {af.relative_to(ROOT)}")
    print(f"  gewählt: {json.dumps(chosen)}\n  primär: {primary}")

    # ---------------- Stufe 2: Bestätigung (alle 16 protokolliert)
    a, b = CONF
    conf = {key(var, L, t): run_case(target, ret, a, b, KOSTEN_HAUPT, "conf")
            for (var, L, t), target in tg.items()}
    bh = pd.Series(1.0, index=panel.index)
    ref_conf = {"baseline_O": run_case(base, ret, a, b, KOSTEN_HAUPT, "conf"),
                "buy_hold": run_case(bh, ret, a, b, KOSTEN_HAUPT, "conf")}

    def verdict(cand):
        var, L = cand.split("-")
        t = chosen[cand]["t"]
        m = conf[key(var, L, t)]
        if var == "S":
            ref = ref_conf["buy_hold"]
            dd_gain = m["max_dd"] - ref["max_dd"]
            ok = dd_gain >= 0.10 and m["calmar"] > ref["calmar"]
            return {"t": t, "dd_verbesserung": round(dd_gain, 5), "calmar": m["calmar"],
                    "calmar_ref": ref["calmar"], "erfuellt": bool(ok), "gegen": "Buy & Hold"}
        ref = ref_conf["baseline_O"]
        dd_gain = m["max_dd"] - ref["max_dd"]
        not_worse = sum(1 for k, v in m["stress"].items()
                        if v is not None and ref["stress"][k] is not None
                        and v >= ref["stress"][k] - 0.005)
        ok = dd_gain >= 0.03 and m["calmar"] >= ref["calmar"] and not_worse >= 4
        return {"t": t, "dd_verbesserung": round(dd_gain, 5), "calmar": m["calmar"],
                "calmar_ref": ref["calmar"], "stress_nicht_schlechter": not_worse,
                "erfuellt": bool(ok), "gegen": "Baseline E"}

    urteile = {c: verdict(c) for c in chosen}
    sekundaer = [c for c in chosen if c != primary]
    n_sek = sum(urteile[c]["erfuellt"] for c in sekundaer)

    sens = {}
    for c in chosen:
        var, L = c.split("-")
        t = chosen[c]["t"]
        for cost in KOSTEN_SENS:
            sens[f"{c} {int(cost*1e4)}Bp"] = {
                "dev": metrics(simulate(tg[(var, L, t)], ret, *dev_window(var, L, panel), cost)),
                "conf": metrics(simulate(tg[(var, L, t)], ret, a, b, cost))}
    for cost in KOSTEN_SENS:
        sens[f"baseline_O {int(cost*1e4)}Bp"] = {"conf": metrics(simulate(base, ret, a, b, cost))}

    ergebnis = {"praeregistrierung_sha256": PREREG_SHA, "auswahl": auswahl,
                "entscheidung_H1": "bestätigt" if urteile[primary]["erfuellt"] else "nicht bestätigt",
                "primaer": {primary: urteile[primary]},
                "sekundaer": {c: urteile[c] for c in sekundaer},
                "sekundaer_erfuellt": f"{n_sek} von 3",
                "entwicklung": {"versuche": dev, "referenz": ref_dev},
                "bestaetigung": {"versuche": conf, "referenz": ref_conf},
                "kosten_sensitivitaet": sens}
    (OUT / "H1_ergebnis.json").write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False))
    (OUT / "H1_bericht.md").write_text(report(ergebnis, chosen, primary, dev, conf, ref_dev, ref_conf))
    print(f"\nH1 (primär {primary}, t={chosen[primary]['t']}): {ergebnis['entscheidung_H1'].upper()}")
    print(f"Sekundär erfüllt: {n_sek} von 3")
    print(f"Bericht: {(OUT / 'H1_bericht.md').relative_to(ROOT)}")
    return 0


def pct(x):
    return "–" if x is None else f"{x:+.1%}"


def report(E, chosen, primary, dev, conf, ref_dev, ref_conf):
    L = ["# H1 – Laufzeit-Gate · Ergebnis", "",
         f"Präregistrierung: `docs/preregistration/H1_laufzeit_gate.md` (sha256 `{PREREG_SHA[:12]}…`, Commit `8e05c0a`)", "",
         f"## Entscheidung: **H1 {E['entscheidung_H1']}**", "",
         f"Primärer Kandidat (vorab im Entwicklungsfenster bestimmt): **{primary}, t = {chosen[primary]['t']:.2f}**. "
         f"Sekundäre Kandidaten erfüllt: **{E['sekundaer_erfuellt']}** (ändern die Entscheidung nicht). "
         "Geprüft: 1 primärer + 3 sekundäre Kandidaten aus 16 Versuchen; Kosten 5 Bp je Positionswechsel.", "",
         "| Kandidat | Rolle | t | gegen | DD-Verbesserung | Calmar | Calmar Referenz | Stress nicht schlechter | Kriterium |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in chosen:
        u = E["primaer"].get(c) or E["sekundaer"][c]
        rolle = "**primär**" if c == primary else "sekundär"
        st = u.get("stress_nicht_schlechter")
        L.append(f"| {c} | {rolle} | {u['t']:.2f} | {u['gegen']} | {u['dd_verbesserung']*100:+.1f} Pp | "
                 f"{u['calmar']:.3f} | {u['calmar_ref']:.3f} | {'–' if st is None else f'{st} von 5'} | "
                 f"{'✅ erfüllt' if u['erfuellt'] else '❌ nicht erfüllt'} |")
    L += ["", "Kriterien: S – Max DD ≥ 10 Pp besser als B&H und Calmar > B&H; O – Max DD ≥ 3 Pp besser als Baseline, "
          "Calmar ≥ Baseline, ≥ 4 von 5 Stressphasen nicht schlechter (Toleranz 0,5 Pp).", ""]

    def table(title, res, refs, which):
        names = [n for n, _, _, w in STRESS if w == which]
        out = [f"## {title}", "",
               "| Versuch | Zeitraum | CAGR | Max DD | Calmar | Sharpe | CVaR 5 % | Ulcer | im Markt | Trades | "
               + " | ".join(names) + " |",
               "|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(names)]
        rows = list(refs.items()) + list(res.items())
        for k, m in rows:
            sel = ""
            for c, v in chosen.items():
                if k == key(c.split("-")[0], c.split("-")[1], v["t"]):
                    sel = " ◀" + (" primär" if c == primary else "")
            out.append(f"| {k}{sel} | {m['start']} – {m['ende']} | {m['cagr']:+.1%} | {m['max_dd']:.1%} | "
                       f"{m['calmar']:.3f} | {m['sharpe']:.2f} | {m['cvar5']:.2%} | {m['ulcer']:.3f} | "
                       f"{m.get('zeit_im_markt', 1):.0%} | {m.get('trades', '–')} | "
                       + " | ".join(pct(m['stress'].get(n)) for n in names) + " |")
        return out + [""]

    L += table("Entwicklungsfenster – alle 16 Versuche (Auswahl von t)", dev, ref_dev, "dev")
    L += table("Bestätigungsfenster 2017–2026 – alle 16 Versuche (protokolliert)", conf, ref_conf, "conf")
    L += ["## Kosten-Sensitivität (gewählte Kandidaten)", "",
          "| Fall | Dev CAGR | Dev Max DD | Dev Calmar | Best. CAGR | Best. Max DD | Best. Calmar |",
          "|---|---|---|---|---|---|---|"]
    for k, v in E["kosten_sensitivitaet"].items():
        d = v.get("dev")
        c = v["conf"]
        dv = ("–", "–", "–") if d is None else (
            format(d["cagr"], "+.1%"), format(d["max_dd"], ".1%"), format(d["calmar"], ".3f"))
        L.append(f"| {k} | {dv[0]} | {dv[1]} | {dv[2]} | "
                 f"{c['cagr']:+.1%} | {c['max_dd']:.1%} | {c['calmar']:.3f} |")
    L += ["", "## Einschränkungen", "",
          "- Daten-Vintage: VIX1Y bis ca. Mitte 2017 und VIX6M bis 26.11.2013 vermutlich nachträglich von Cboe berechnet "
          "(nur Schlusskurse) → Entwicklungsfenster ist Methodentest, keine damals umsetzbare Strategie.",
          "- Preisindex ohne Dividenden; Cash ohne Verzinsung in der Rendite (rf nur im Sharpe).",
          "- n_trials = 16 ist eine konservative Obergrenze (Versuche nicht unabhängig); DSR folgt in Phase 4."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
