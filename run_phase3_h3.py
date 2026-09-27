"""
run_phase3_h3.py – Phase 3, Hypothese H3 (Implied Correlation COR1M) – strikt nach
Präregistrierung docs/preregistration/H3_implied_correlation.md (Rev. 2, Commit e40226f,
27.09.2026 13:54).

Simulation, Kennzahlen, Stressphasen und Baseline werden unverändert aus run_phase3_h1.py
übernommen (identische Rechenweise wie H1).

Ablauf: 1. Entwicklungsfenster → Auswahl + primärer Kandidat → results/phase3/H3_auswahl.json
(nie überschrieben); 2. Bestätigungsfenster (alle 16 protokolliert), Entscheidung nur über
den primären Kandidaten; 3. getrennt: Informationsmehrwert M, Live-Teilfenster, Redundanz.

Aufruf:  python run_phase3_h3.py
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
import run_phase3_h1 as H1  # noqa: E402  (simulate, metrics, stress, baseline_target, STRESS)

PREREG = ROOT / "docs" / "preregistration" / "H3_implied_correlation.md"
PREREG_SHA = "964f9f6e82bb61a91599dbf253c35c495ea7f01cffb99e3ab5c69d03e192bee9"
OUT = ROOT / "results" / "phase3"

LOOKBACK, MIN_OBS = 252, 227
GRID = {"A": [0.80, 0.85, 0.90, 0.95], "B": [0.10, 0.20, 0.30, 0.40]}
KOSTEN = 0.0005
TIE = 0.01
S_DEV = ("2007-01-03", "2016-12-30")
O_DEV = ("2009-09-18", "2016-12-30")
CONF = ("2017-01-03", "2026-09-25")
LIVE = ("2022-03-18", "2026-09-25")


def load():
    sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    if sha != PREREG_SHA:
        raise SystemExit(f"ABBRUCH: Präregistrierung H3 verändert (sha256 {sha})")
    verify_snapshot(H1.YAHOO)
    panel, _ = build_panel(H1.CBOE)
    spx = pd.read_csv(H1.YAHOO / "GSPC.csv", index_col=0, parse_dates=True)["Close"]
    ret = spx.pct_change().rename("ret")
    idx = panel.index.intersection(ret.index)
    return panel.loc[idx], ret.loc[idx]


def percentile(x: pd.Series) -> pd.Series:
    """Anteil der Werte in [t−251, t], die ≤ x(t) sind; nur mit ≥ 227 Werten; nur Vergangenheit."""
    a = x.to_numpy(dtype="float64")
    out = np.full(len(a), np.nan)
    for i in range(len(a)):
        if np.isnan(a[i]):
            continue
        w = a[max(0, i - LOOKBACK + 1): i + 1]
        w = w[~np.isnan(w)]
        if len(w) >= MIN_OBS:
            out[i] = float((w <= a[i]).mean())
    return pd.Series(out, index=x.index)


def build_targets(panel, base):
    pc, pv = percentile(panel["COR1M"]), percentile(panel["VIX"])
    D = pc - pv
    tg, riskoff = {}, {}
    for fam, grid in GRID.items():
        for p in grid:
            sig = (pc >= p) if fam == "A" else (D >= p)
            missing = pc.isna() if fam == "A" else D.isna()
            ro = sig.astype(float)
            ro[missing] = np.nan
            riskoff[(fam, p)] = ro
            s = pd.Series(np.where(ro == 1, 0.0, 1.0), index=ro.index); s[missing] = np.nan
            o = pd.Series(np.where(ro == 1, 0.0, base.reindex(ro.index)), index=ro.index); o[missing] = np.nan
            tg[("S", fam, p)] = s
            tg[("O", fam, p)] = o
    return tg, riskoff, pc, pv


def key(var, fam, p):
    return f"{var}-{fam}-{p:.2f}"


def win(var, which):
    if which == "dev":
        return S_DEV if var == "S" else O_DEV
    return CONF if which == "conf" else LIVE


def case(target, ret, w, which):
    r = H1.simulate(target, ret, w[0], w[1], KOSTEN)
    pos = target.loc[w[0]:w[1]].ffill().fillna(0.0)
    m = H1.metrics(r, pos)
    m["stress"] = H1.stress(r, which) if which in ("dev", "conf") else {}
    return m


def dd_analysis(target, ret, w):
    r = H1.simulate(target, ret, w[0], w[1], KOSTEN)
    eq = (1 + r).cumprod(); dd = eq / eq.cummax() - 1
    tr = dd.idxmin(); pk = eq.loc[:tr].idxmax()
    rec = eq.loc[tr:][eq.loc[tr:] >= eq.loc[pk]]
    return {"max_dd": round(float(dd.min()), 5), "hoch": pk.strftime("%Y-%m-%d"),
            "tief": tr.strftime("%Y-%m-%d"),
            "erholt": rec.index.min().strftime("%Y-%m-%d") if len(rec) else None}


def eigenstaendig(ro: pd.Series, base: pd.Series, w) -> dict:
    x = ro.loc[w[0]:w[1]]
    days = x[x == 1].index
    if len(days) == 0:
        return {"risiko_aus_tage": 0, "M": None, "ueberlappung": None}
    M = float((base.reindex(days) > 0).mean())
    return {"risiko_aus_tage": int(len(days)), "M": round(M, 4), "ueberlappung": round(1 - M, 4)}


def main() -> int:
    panel, ret = load()
    base = H1.baseline_target(panel)
    tg, riskoff, pc, pv = build_targets(panel, base)
    OUT.mkdir(parents=True, exist_ok=True)
    bh = pd.Series(1.0, index=panel.index)

    # ---- Stufe 1: Entwicklung
    dev = {key(v, f, p): case(t, ret, win(v, "dev"), "dev") for (v, f, p), t in tg.items()}
    ref_dev = {"baseline_O": case(base, ret, O_DEV, "dev"), "buy_hold_S": case(bh, ret, S_DEV, "dev")}
    chosen = {}
    for v in ["S", "O"]:
        for f, grid in GRID.items():
            cs = [(p, dev[key(v, f, p)]["calmar"]) for p in grid]
            best = max(c for _, c in cs)
            p_sel = max(p for p, c in cs if c >= best - TIE)
            chosen[f"{v}-{f}"] = {"param": p_sel, "calmar_dev": dev[key(v, f, p_sel)]["calmar"]}
    primary = "O-B" if chosen["O-B"]["calmar_dev"] >= chosen["O-A"]["calmar_dev"] - TIE else "O-A"
    auswahl = {"praeregistrierung_sha256": PREREG_SHA, "kandidaten": chosen, "primaer": primary}
    af = OUT / "H3_auswahl.json"
    if af.exists():
        if json.loads(af.read_text()) != auswahl:
            raise SystemExit("ABBRUCH: gespeicherte H3-Auswahl weicht ab – nicht überschreiben.")
        print("Auswahl existiert bereits und ist identisch → wird verwendet.")
    else:
        af.write_text(json.dumps(auswahl, indent=2, ensure_ascii=False))
        print(f"Auswahl festgeschrieben: {af.relative_to(ROOT)}")
    print(f"  gewählt: {json.dumps(chosen)}\n  primär: {primary}")

    # ---- Stufe 2: Bestätigung
    conf = {key(v, f, p): case(t, ret, CONF, "conf") for (v, f, p), t in tg.items()}
    ref_conf = {"baseline_O": case(base, ret, CONF, "conf"), "buy_hold": case(bh, ret, CONF, "conf")}

    def verdict(c):
        v, f = c.split("-"); p = chosen[c]["param"]; m = conf[key(v, f, p)]
        if v == "S":
            ref = ref_conf["buy_hold"]; g = m["max_dd"] - ref["max_dd"]
            return {"param": p, "gegen": "Buy & Hold", "dd_verbesserung": round(g, 5),
                    "calmar": m["calmar"], "calmar_ref": ref["calmar"],
                    "erfuellt": bool(g >= 0.10 and m["calmar"] > ref["calmar"])}
        ref = ref_conf["baseline_O"]; g = m["max_dd"] - ref["max_dd"]
        nw = sum(1 for k, x in m["stress"].items()
                 if x is not None and ref["stress"][k] is not None and x >= ref["stress"][k] - 0.005)
        return {"param": p, "gegen": "Baseline E", "dd_verbesserung": round(g, 5),
                "calmar": m["calmar"], "calmar_ref": ref["calmar"], "stress_nicht_schlechter": nw,
                "erfuellt": bool(g >= 0.03 and m["calmar"] >= ref["calmar"] and nw >= 4)}

    urteile = {c: verdict(c) for c in chosen}
    sek = [c for c in chosen if c != primary]
    n_sek = sum(urteile[c]["erfuellt"] for c in sek)
    entscheidung = "bestätigt" if urteile[primary]["erfuellt"] else "nicht bestätigt"

    # ---- 9a Informationsmehrwert (getrennt)
    info = {}
    for c in chosen:
        v, f = c.split("-"); p = chosen[c]["param"]
        info[c] = {w: eigenstaendig(riskoff[(f, p)], base, win(v, w) if w == "dev" else (CONF if w == "conf" else LIVE))
                   for w in ["dev", "conf", "live"]}
    ov = info[primary]["conf"]["ueberlappung"]
    info_fest = ("keine Risiko-aus-Tage im Bestätigungsfenster" if ov is None else
                 "zusätzlicher Informationsgehalt von COR1M gegenüber der Baseline begrenzt" if ov >= 0.80 else
                 "COR1M trifft in nennenswertem Umfang eigenständige Entscheidungen")

    # ---- 10 Sekundär
    live = {"baseline_O": case(base, ret, LIVE, "live"), "buy_hold": case(bh, ret, LIVE, "live")}
    for c in chosen:
        v, f = c.split("-"); p = chosen[c]["param"]
        live[key(v, f, p)] = case(tg[(v, f, p)], ret, LIVE, "live")
    red = {}
    for name, w in [("dev", O_DEV), ("conf", CONF)]:
        x = panel.loc[w[0]:w[1]]
        sp = lambda a, b: round(float(a.rank().corr(b.rank())), 3)
        red[name] = {"rho_COR1M_VIX": sp(x["COR1M"], x["VIX"]),
                     "rho_dCOR1M_dVIX_5T": sp(x["COR1M"].diff(5), x["VIX"].diff(5)),
                     "rho_COR1M_VIX3M_VIX": sp(x["COR1M"], x["VIX3M"] / x["VIX"])}
    v, f = primary.split("-")
    ddana = {"primaer": dd_analysis(tg[(v, f, chosen[primary]["param"])], ret, CONF),
             "baseline": dd_analysis(base, ret, CONF)}
    sens = {}
    for c in chosen:
        v, f = c.split("-"); p = chosen[c]["param"]
        for cost in (0.0, 0.0010):
            sens[f"{c} {int(cost*1e4)}Bp"] = H1.metrics(H1.simulate(tg[(v, f, p)], ret, *CONF, cost))
    for cost in (0.0, 0.0010):
        sens[f"baseline_O {int(cost*1e4)}Bp"] = H1.metrics(H1.simulate(base, ret, *CONF, cost))

    E = {"praeregistrierung_sha256": PREREG_SHA, "auswahl": auswahl, "entscheidung_H3": entscheidung,
         "primaer": {primary: urteile[primary]}, "sekundaer": {c: urteile[c] for c in sek},
         "sekundaer_erfuellt": f"{n_sek} von 3",
         "informationsmehrwert": {"feststellung": info_fest, "je_kandidat": info},
         "redundanz_niveau": red, "drawdown_analyse": ddana, "live_teilfenster": live,
         "entwicklung": {"versuche": dev, "referenz": ref_dev},
         "bestaetigung": {"versuche": conf, "referenz": ref_conf}, "kosten_sensitivitaet_best": sens}
    (OUT / "H3_ergebnis.json").write_text(json.dumps(E, indent=2, ensure_ascii=False))
    (OUT / "H3_bericht.md").write_text(report(E, chosen, primary, dev, conf, ref_dev, ref_conf))
    print(f"\nH3 (primär {primary}, Parameter {chosen[primary]['param']}): {entscheidung.upper()}")
    print(f"Sekundär erfüllt: {n_sek} von 3")
    print(f"Informationsmehrwert: {info_fest} (Überlappung {ov})")
    print(f"Bericht: {(OUT / 'H3_bericht.md').relative_to(ROOT)}")
    return 0


def pct(x):
    return "–" if x is None else f"{x:+.1%}"


def report(E, chosen, primary, dev, conf, ref_dev, ref_conf):
    L = ["# H3 – Implied Correlation (COR1M) · Ergebnis", "",
         f"Präregistrierung: `docs/preregistration/H3_implied_correlation.md` Rev. 2 (sha256 `{PREREG_SHA[:12]}…`, Commit `e40226f`)", "",
         f"## Entscheidung: **H3 {E['entscheidung_H3']}**", "",
         f"Primärer Kandidat (vorab im Entwicklungsfenster bestimmt): **{primary}, Parameter {chosen[primary]['param']:.2f}**. "
         f"Sekundär erfüllt: **{E['sekundaer_erfuellt']}** (ändern die Entscheidung nicht). 16 Versuche, Kosten 5 Bp.", "",
         "| Kandidat | Rolle | Parameter | gegen | DD-Verbesserung | Calmar | Calmar Referenz | Stress nicht schlechter | Kriterium |",
         "|---|---|---|---|---|---|---|---|---|"]
    for c in chosen:
        u = E["primaer"].get(c) or E["sekundaer"][c]
        st = u.get("stress_nicht_schlechter")
        L.append(f"| {c} | {'**primär**' if c == primary else 'sekundär'} | {u['param']:.2f} | {u['gegen']} | "
                 f"{u['dd_verbesserung']*100:+.1f} Pp | {u['calmar']:.3f} | {u['calmar_ref']:.3f} | "
                 f"{'–' if st is None else f'{st} von 5'} | {'✅ erfüllt' if u['erfuellt'] else '❌ nicht erfüllt'} |")
    I = E["informationsmehrwert"]
    L += ["", "## Informationsmehrwert (getrennt vom Erfolgskriterium, Abschnitt 9a)", "",
          f"**Feststellung (primärer Kandidat, Bestätigungsfenster): {I['feststellung']}.**", "",
          "| Kandidat | Fenster | Risiko-aus-Tage | M (Baseline noch investiert) | Überlappung |", "|---|---|---|---|---|"]
    for c, d in I["je_kandidat"].items():
        for w, x in d.items():
            m_txt = "–" if x["M"] is None else format(x["M"], ".0%")
            u_txt = "–" if x["ueberlappung"] is None else format(x["ueberlappung"], ".0%")
            L.append(f"| {c} | {w} | {x['risiko_aus_tage']} | {m_txt} | {u_txt} |")
    L += ["", "## Redundanz auf Niveauebene (deskriptiv, Spearman ρ)", "",
          "| Fenster | ρ(COR1M, VIX) | ρ(ΔCOR1M, ΔVIX) 5T | ρ(COR1M, VIX3M/VIX) |", "|---|---|---|---|"]
    for w, r in E["redundanz_niveau"].items():
        L.append(f"| {w} | {r['rho_COR1M_VIX']:.3f} | {r['rho_dCOR1M_dVIX_5T']:.3f} | {r['rho_COR1M_VIX3M_VIX']:.3f} |")
    d = E["drawdown_analyse"]
    L += ["", "## Max-Drawdown-Analyse Bestätigungsfenster", ""]
    for k, x in d.items():
        L.append(f"- {k}: {x['max_dd']:.1%} · Hoch {x['hoch']} → Tief {x['tief']} → erholt {x['erholt']}")

    def table(title, res, refs, which):
        names = [n for n, _, _, w in H1.STRESS if w == which]
        out = [f"## {title}", "", "| Versuch | Zeitraum | CAGR | Max DD | Calmar | Sharpe | CVaR 5 % | Ulcer | im Markt | Trades | "
               + " | ".join(names) + " |", "|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(names)]
        for k, m in list(refs.items()) + list(res.items()):
            sel = ""
            for c, v in chosen.items():
                if k == key(c.split("-")[0], c.split("-")[1], v["param"]):
                    sel = " ◀" + (" primär" if c == primary else "")
            out.append(f"| {k}{sel} | {m['start']} – {m['ende']} | {m['cagr']:+.1%} | {m['max_dd']:.1%} | {m['calmar']:.3f} | "
                       f"{m['sharpe']:.2f} | {m['cvar5']:.2%} | {m['ulcer']:.3f} | {m.get('zeit_im_markt', 1):.0%} | "
                       f"{m.get('trades', '–')} | " + " | ".join(pct(m['stress'].get(n)) for n in names) + " |")
        return out + [""]

    L += [""] + table("Entwicklungsfenster – alle 16 Versuche", dev, ref_dev, "dev")
    L += table("Bestätigungsfenster 2017–2026 – alle 16 Versuche", conf, ref_conf, "conf")
    L += ["## Live-Teilfenster 18.03.2022 – 25.09.2026 (sekundär)", "",
          "| Fall | CAGR | Max DD | Calmar | im Markt |", "|---|---|---|---|---|"]
    for k, m in E["live_teilfenster"].items():
        L.append(f"| {k} | {m['cagr']:+.1%} | {m['max_dd']:.1%} | {m['calmar']:.3f} | {m.get('zeit_im_markt', 1):.0%} |")
    L += ["", "## Kosten-Sensitivität Bestätigungsfenster", "", "| Fall | CAGR | Max DD | Calmar |", "|---|---|---|---|"]
    for k, m in E["kosten_sensitivitaet_best"].items():
        L.append(f"| {k} | {m['cagr']:+.1%} | {m['max_dd']:.1%} | {m['calmar']:.3f} |")
    L += ["", "## Einschränkungen", "",
          "- Daten-Vintage: COR1M bis 17.03.2022 vermutlich rückberechnet (nur Schlusskurse) – betrifft Entwicklung und "
          "Bestätigung bis 03/2022; Live-Teilfenster separat berichtet.",
          "- Preisindex ohne Dividenden; Cash unverzinst (rf nur im Sharpe). n_trials = 16 konservativ; DSR in Phase 4."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
