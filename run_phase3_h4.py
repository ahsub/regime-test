"""
run_phase3_h4.py – Phase 3, Hypothese H4 (Makro-Achse) – strikt nach Präregistrierung
docs/preregistration/H4_makro_achse.md (Rev. 2, Commit dc6df73, 27.09.2026 14:34).

Simulation, Kennzahlen, Stressphasen und Baseline unverändert aus run_phase3_h1.py.
Ablauf: 1. Eligibility (nur Signalzählung, keine Performance) → 2. Auswahl von a im
Entwicklungsfenster → results/phase3/H4_auswahl.json (nie überschrieben) → 3. Bestätigung.

Aufruf:  python run_phase3_h4.py
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
import run_phase3_h1 as H1  # noqa: E402

PREREG = ROOT / "docs" / "preregistration" / "H4_makro_achse.md"
PREREG_SHA = "d6db37c8194187a14a56fa8575e1900390dd63a4a37d1421476475611b19925b"
ALF = ROOT / "data" / "raw" / "alfred" / "2026-09-27"
H15 = ROOT / "data" / "raw" / "alfred" / "2026-09-27_DGS10-DGS3MO-DGS2"
OUT = ROOT / "results" / "phase3"

A_GRID = [0.05, 0.10, 0.15]
MIN_TAGE = 20
KOSTEN, TIE = 0.0005, 0.01
DEV = ("2010-07-01", "2016-12-30")
CONF = ("2017-01-03", "2026-09-25")


def load():
    sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    if sha != PREREG_SHA:
        raise SystemExit(f"ABBRUCH: Präregistrierung H4 verändert (sha256 {sha})")
    for d in (ALF, H15, H1.YAHOO):
        verify_snapshot(d)
    panel, _ = build_panel(H1.CBOE)
    spx = pd.read_csv(H1.YAHOO / "GSPC.csv", index_col=0, parse_dates=True)["Close"]
    ret = spx.pct_change().rename("ret")
    idx = panel.index.intersection(ret.index)
    return panel.loc[idx], ret.loc[idx]


def first(path: Path) -> pd.DataFrame:
    f = pd.read_csv(path)
    f["value"] = pd.to_numeric(f["value"], errors="coerce")
    f = f.dropna(subset=["value"]).copy()
    f["od"] = pd.to_datetime(f["observation_date"])
    f["rs"] = pd.to_datetime(f["realtime_start"])
    return f.sort_values("od").reset_index(drop=True)


def claims_signal(days: pd.DatetimeIndex) -> tuple[pd.Series, dict]:
    """C(t) nach Präregistrierung Abschnitt 3 (nur Erstveröffentlichungen, Archivdatum ≤ t)."""
    f = first(ALF / "ICSA_first.csv")
    gaps = f["od"].diff().dt.days.dropna()
    if not (gaps == 7).all():
        raise SystemExit("ABBRUCH: Lücke in der wöchentlichen Erstveröffentlichungsreihe ICSA")
    if not f["rs"].is_monotonic_increasing:
        raise SystemExit("ABBRUCH: ICSA-Archivdaten nicht monoton")
    v = f["value"]
    ma4 = v.rolling(4).mean()
    basis = ma4.shift(1).rolling(52).min()        # MA4 der Wochen w−52 … w−1
    f["C"] = ma4 / basis - 1                       # braucht Wochen w−55 … w
    valid = f.dropna(subset=["C"])
    pos = np.searchsorted(valid["rs"].to_numpy(), days.to_numpy(), side="right") - 1
    C = pd.Series([valid["C"].iloc[i] if i >= 0 else np.nan for i in pos], index=days)
    wk = pd.Series([valid["od"].iloc[i] if i >= 0 else pd.NaT for i in pos], index=days)
    rs = pd.Series([valid["rs"].iloc[i] if i >= 0 else pd.NaT for i in pos], index=days)
    assert (rs.dropna() <= rs.dropna().index).all(), "Look-ahead: Archivdatum nach Handelstag"
    info = {"signal_gueltig_ab_beobachtung": valid["od"].min().strftime("%Y-%m-%d"),
            "median_alter_tage": float((days.to_series() - wk).dt.days.median())}
    return C, info


def curve_signal(days: pd.DatetimeIndex, short: str) -> tuple[pd.Series, dict]:
    a, b = first(H15 / "DGS10_first.csv"), first(H15 / f"{short}_first.csv")
    m = a[["od", "value", "rs"]].merge(b[["od", "value", "rs"]], on="od", suffixes=("_10", "_s"))
    m["avail"] = m[["rs_10", "rs_s"]].max(axis=1)
    m["spread"] = m["value_10"] - m["value_s"]
    m = m.sort_values("avail").reset_index(drop=True)
    m["d_best"] = m["od"].cummax()                # jüngster Beobachtungstag, der bis avail bekannt ist
    lookup = m.set_index("od")["spread"]
    pos = np.searchsorted(m["avail"].to_numpy(), days.to_numpy(), side="right") - 1
    d = pd.Series([m["d_best"].iloc[i] if i >= 0 else pd.NaT for i in pos], index=days)
    S = pd.Series([lookup.get(x, np.nan) if pd.notna(x) else np.nan for x in d], index=days)
    av = m.set_index("od")["avail"]
    used_avail = pd.Series([av.get(x) if pd.notna(x) else pd.NaT for x in d], index=days)
    assert (used_avail.dropna() <= used_avail.dropna().index).all(), "Look-ahead Kurve"
    return S, {"median_alter_tage": float((days.to_series() - d).dt.days.median())}


def overlay(riskoff: pd.Series, base: pd.Series) -> pd.Series:
    t = pd.Series(np.where(riskoff == 1, 0.0, base.reindex(riskoff.index)), index=riskoff.index)
    t[riskoff.isna()] = np.nan
    return t


def case(target, ret, w, which):
    r = H1.simulate(target, ret, w[0], w[1], KOSTEN)
    pos = target.loc[w[0]:w[1]].ffill().fillna(0.0)
    m = H1.metrics(r, pos)
    m["stress"] = H1.stress(r, which)
    return m


def episodes(ro: pd.Series, w) -> dict:
    x = ro.loc[w[0]:w[1]].fillna(0) == 1
    g = (x != x.shift()).cumsum()
    runs = x.groupby(g).agg(["first", "size"]).query("first")["size"]
    return {"risiko_aus_tage": int(x.sum()), "phasen": int(len(runs)),
            "mittlere_dauer": round(float(runs.mean()), 1) if len(runs) else 0}


def eigenstaendig(ro, base, w):
    x = ro.loc[w[0]:w[1]]
    days = x[x == 1].index
    if len(days) == 0:
        return {"risiko_aus_tage": 0, "M": None, "ueberlappung": None}
    M = float((base.reindex(days) > 0).mean())
    return {"risiko_aus_tage": int(len(days)), "M": round(M, 4), "ueberlappung": round(1 - M, 4)}


def dd_analysis(target, ret, w):
    r = H1.simulate(target, ret, w[0], w[1], KOSTEN)
    eq = (1 + r).cumprod(); dd = eq / eq.cummax() - 1
    tr = dd.idxmin(); pk = eq.loc[:tr].idxmax()
    rec = eq.loc[tr:][eq.loc[tr:] >= eq.loc[pk]]
    return {"max_dd": round(float(dd.min()), 5), "hoch": pk.strftime("%Y-%m-%d"),
            "tief": tr.strftime("%Y-%m-%d"),
            "erholt": rec.index.min().strftime("%Y-%m-%d") if len(rec) else None}


def verdict(m, ref):
    g = m["max_dd"] - ref["max_dd"]
    nw = sum(1 for k, x in m["stress"].items()
             if x is not None and ref["stress"][k] is not None and x >= ref["stress"][k] - 0.005)
    return {"dd_verbesserung": round(g, 5), "calmar": m["calmar"], "calmar_ref": ref["calmar"],
            "stress_nicht_schlechter": nw,
            "erfuellt": bool(g >= 0.03 and m["calmar"] >= ref["calmar"] and nw >= 4)}


def main() -> int:
    panel, ret = load()
    days = panel.index
    base = H1.baseline_target(panel)
    C, cinfo = claims_signal(days)
    K, kinfo = curve_signal(days, "DGS3MO")
    Z, zinfo = curve_signal(days, "DGS2")

    ro = {}
    for a in A_GRID:
        s = (C >= a).astype(float); s[C.isna()] = np.nan; ro[f"A-{a:.2f}"] = s
    s = (K < 0).astype(float); s[K.isna()] = np.nan; ro["K"] = s
    s = (Z < 0).astype(float); s[Z.isna()] = np.nan; ro["Z"] = s
    tg = {k: overlay(v, base) for k, v in ro.items()}
    for k, v in ro.items():
        miss = int(v.loc[DEV[0]:CONF[1]].isna().sum())
        if miss:
            print(f"Hinweis: {k} ohne Signal an {miss} Handelstagen (Vortagsposition bleibt)")
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- 1. Eligibility (reine Signalzählung im Entwicklungsfenster)
    elig = {f"A-{a:.2f}": int((ro[f"A-{a:.2f}"].loc[DEV[0]:DEV[1]] == 1).sum()) for a in A_GRID}
    zugelassen = [a for a in A_GRID if elig[f"A-{a:.2f}"] >= MIN_TAGE]
    print("Eligibility (Risiko-aus-Handelstage im Entwicklungsfenster):", elig,
          "→ zugelassen:", [f"{a:.2f}" for a in zugelassen])

    # ---- 2. Entwicklung + Auswahl
    dev = {k: case(t, ret, DEV, "dev") for k, t in tg.items()}
    ref_dev = {"baseline": case(base, ret, DEV, "dev")}
    if zugelassen:
        cs = [(a, dev[f"A-{a:.2f}"]["calmar"]) for a in zugelassen]
        best = max(c for _, c in cs)
        a_sel = max(a for a, c in cs if c >= best - TIE)
        primaer = f"A-{a_sel:.2f}"
        status = "auswertbar"
    else:
        a_sel, primaer, status = None, None, "nicht auswertbar wegen unzureichender Signalaktivität"
    auswahl = {"praeregistrierung_sha256": PREREG_SHA, "eligibility_tage": elig,
               "zugelassen": [f"{a:.2f}" for a in zugelassen],
               "a_gewaehlt": a_sel, "primaer": primaer, "status_A": status,
               "sekundaer": ["K", "Z"]}
    af = OUT / "H4_auswahl.json"
    if af.exists():
        if json.loads(af.read_text()) != auswahl:
            raise SystemExit("ABBRUCH: gespeicherte H4-Auswahl weicht ab – nicht überschreiben.")
        print("Auswahl existiert bereits und ist identisch → wird verwendet.")
    else:
        af.write_text(json.dumps(auswahl, indent=2, ensure_ascii=False))
        print(f"Auswahl festgeschrieben: {af.relative_to(ROOT)} · primär: {primaer} ({status})")

    # ---- 3. Bestätigung
    conf = {k: case(t, ret, CONF, "conf") for k, t in tg.items()}
    ref_conf = {"baseline": case(base, ret, CONF, "conf")}
    urteile = {k: verdict(conf[k], ref_conf["baseline"]) for k in conf}
    if primaer:
        entscheidung = "bestätigt" if urteile[primaer]["erfuellt"] else "nicht bestätigt"
    else:
        entscheidung = "nicht bestätigt (A nicht auswertbar wegen unzureichender Signalaktivität)"
    n_sek = sum(urteile[k]["erfuellt"] for k in ["K", "Z"])

    info = {k: {"dev": eigenstaendig(ro[k], base, DEV), "conf": eigenstaendig(ro[k], base, CONF)} for k in ro}
    epi = {k: {"dev": episodes(ro[k], DEV), "conf": episodes(ro[k], CONF)} for k in ro}
    sens = {}
    for k in ([primaer] if primaer else []) + ["K", "Z", "baseline"]:
        t = base if k == "baseline" else tg[k]
        for cost in (0.0, 0.0010):
            sens[f"{k} {int(cost*1e4)}Bp"] = H1.metrics(H1.simulate(t, ret, *CONF, cost))
    dd = {"baseline": dd_analysis(base, ret, CONF)}
    if primaer:
        dd[primaer] = dd_analysis(tg[primaer], ret, CONF)
    feststellung = None
    if primaer:
        ov = info[primaer]["conf"]["ueberlappung"]
        feststellung = ("keine Risiko-aus-Tage im Bestätigungsfenster" if ov is None else
                        "zusätzlicher Informationsgehalt begrenzt" if ov >= 0.80 else
                        "eigenständige Entscheidungen in nennenswertem Umfang")

    E = {"praeregistrierung_sha256": PREREG_SHA, "auswahl": auswahl, "entscheidung_H4": entscheidung,
         "primaer": {primaer: urteile[primaer]} if primaer else None,
         "sekundaer": {k: urteile[k] for k in ["K", "Z"]}, "sekundaer_erfuellt": f"{n_sek} von 2",
         "alle_urteile_bestaetigung": urteile,
         "informationsmehrwert": {"feststellung_primaer": feststellung, "je_signal": info},
         "risiko_aus_phasen": epi, "signal_info": {"claims": cinfo, "K": kinfo, "Z": zinfo},
         "drawdown_analyse": dd, "entwicklung": {"versuche": dev, "referenz": ref_dev},
         "bestaetigung": {"versuche": conf, "referenz": ref_conf}, "kosten_sensitivitaet": sens}
    (OUT / "H4_ergebnis.json").write_text(json.dumps(E, indent=2, ensure_ascii=False, default=str))
    (OUT / "H4_bericht.md").write_text(report(E, dev, conf, ref_dev, ref_conf, primaer, zugelassen, elig))
    print(f"\nH4 (primär {primaer}): {entscheidung.upper()} · sekundär erfüllt: {n_sek} von 2")
    if feststellung:
        print(f"Informationsmehrwert primär: {feststellung}")
    print(f"Bericht: {(OUT / 'H4_bericht.md').relative_to(ROOT)}")
    return 0


def pct(x):
    return "–" if x is None else f"{x:+.1%}"


def report(E, dev, conf, ref_dev, ref_conf, primaer, zugelassen, elig):
    L = ["# H4 – Makro-Achse (Initial Claims, Zinskurve) · Ergebnis", "",
         f"Präregistrierung: `docs/preregistration/H4_makro_achse.md` Rev. 2 (sha256 `{PREREG_SHA[:12]}…`, Commit `dc6df73`)", "",
         f"## Entscheidung: **H4 {E['entscheidung_H4']}**", "",
         "### Eligibility A (Risiko-aus-Handelstage im Entwicklungsfenster, Mindestwert 20)", "",
         "| Schwelle | Tage | zugelassen |", "|---|---|---|"]
    for k, n in elig.items():
        L.append(f"| {k} | {n} | {'✅' if n >= MIN_TAGE else '❌'} |")
    L += ["", f"Primärer Kandidat: **{primaer or '–'}** · Status A: {E['auswahl']['status_A']}", "",
          "### Urteile Bestätigungsfenster (gegen Baseline, 5 Bp)", "",
          "| Signal | Rolle | DD-Verbesserung | Calmar | Calmar Baseline | Stress nicht schlechter | Kriterium |",
          "|---|---|---|---|---|---|---|"]
    for k, u in E["alle_urteile_bestaetigung"].items():
        rolle = "**primär**" if k == primaer else ("sekundär" if k in ("K", "Z") else
                ("nicht zugelassen" if k.startswith("A-") and float(k[2:]) not in zugelassen else "nicht gewählt"))
        L.append(f"| {k} | {rolle} | {u['dd_verbesserung']*100:+.1f} Pp | {u['calmar']:.3f} | {u['calmar_ref']:.3f} | "
                 f"{u['stress_nicht_schlechter']} von 5 | {'✅' if u['erfuellt'] else '❌'} |")
    L += ["", f"Sekundär (K, Z) erfüllt: **{E['sekundaer_erfuellt']}** – ändern die Entscheidung nicht.", "",
          "## Informationsmehrwert (getrennt, Abschnitt 9a)", ""]
    if E["informationsmehrwert"]["feststellung_primaer"]:
        L.append(f"**Primär: {E['informationsmehrwert']['feststellung_primaer']}.**")
    L += ["", "| Signal | Fenster | Risiko-aus-Tage | Phasen | mittl. Dauer | M | Überlappung |", "|---|---|---|---|---|---|---|"]
    for k, d in E["informationsmehrwert"]["je_signal"].items():
        for w, x in d.items():
            e = E["risiko_aus_phasen"][k][w]
            m_txt = "–" if x["M"] is None else format(x["M"], ".0%")
            u_txt = "–" if x["ueberlappung"] is None else format(x["ueberlappung"], ".0%")
            L.append(f"| {k} | {w} | {x['risiko_aus_tage']} | {e['phasen']} | {e['mittlere_dauer']} | {m_txt} | {u_txt} |")
    L += ["", "## Max-Drawdown-Analyse Bestätigungsfenster", ""]
    for k, x in E["drawdown_analyse"].items():
        L.append(f"- {k}: {x['max_dd']:.1%} · Hoch {x['hoch']} → Tief {x['tief']} → erholt {x['erholt']}")

    def table(title, res, refs, which):
        names = [n for n, a, b, w in H1.STRESS if w == which and a >= DEV[0]]
        out = [f"## {title}", "", "| Signal | Zeitraum | CAGR | Max DD | Calmar | Sharpe | CVaR 5 % | Ulcer | im Markt | Trades | "
               + " | ".join(names) + " |", "|---|---|---|---|---|---|---|---|---|---|" + "---|" * len(names)]
        for k, m in list(refs.items()) + list(res.items()):
            out.append(f"| {k}{' ◀ primär' if k == primaer else ''} | {m['start']} – {m['ende']} | {m['cagr']:+.1%} | "
                       f"{m['max_dd']:.1%} | {m['calmar']:.3f} | {m['sharpe']:.2f} | {m['cvar5']:.2%} | {m['ulcer']:.3f} | "
                       f"{m.get('zeit_im_markt', 1):.0%} | {m.get('trades', '–')} | "
                       + " | ".join(pct(m['stress'].get(n)) for n in names) + " |")
        return out + [""]

    L += [""] + table("Entwicklungsfenster 01.07.2010 – 30.12.2016", dev, ref_dev, "dev")
    L += table("Bestätigungsfenster 2017–2026", conf, ref_conf, "conf")
    L += ["## Kosten-Sensitivität Bestätigungsfenster", "", "| Fall | CAGR | Max DD | Calmar |", "|---|---|---|---|"]
    for k, m in E["kosten_sensitivitaet"].items():
        L.append(f"| {k} | {m['cagr']:+.1%} | {m['max_dd']:.1%} | {m['calmar']:.3f} |")
    si = E["signal_info"]
    L += ["", "## Signal-Timing (Kontrolle)", "",
          f"- Claims-Signal gültig ab Beobachtung {si['claims']['signal_gueltig_ab_beobachtung']}; "
          f"Median-Alter der jüngsten bekannten Woche: {si['claims']['median_alter_tage']:.0f} Kalendertage",
          f"- Kurve 10J−3M / 10J−2J: Median-Alter des jüngsten bekannten Beobachtungstags "
          f"{si['K']['median_alter_tage']:.0f} / {si['Z']['median_alter_tage']:.0f} Kalendertage", "",
          "## Einschränkungen", "",
          "- Verfügbarkeitsdatum = ALFRED-Archivierungsdatum (konservativ). Claims-Signal nutzt Erstveröffentlichungen "
          "früherer Wochen, nicht deren zum Zeitpunkt t revidierte Stände.",
          "- Große historische Episoden waren dem Designer bekannt (Transparenzhinweis Präregistrierung).",
          "- Preisindex ohne Dividenden; Cash unverzinst. n_trials kumuliert 42 (konservativ); DSR in Phase 4."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
