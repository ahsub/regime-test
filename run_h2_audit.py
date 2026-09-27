"""
run_h2_audit.py – H2-Vorstufe: deskriptives Daten-/Informationsaudit echte Cboe-PCR vs. UIQ-PCR-Proxy.

KEIN Renditetest, keine Parameteroptimierung, keine Entscheidung für/gegen PCR.
Fragen (Reviewer 27.09.2026):
  1. Korrelation PCR ↔ Proxy im gemeinsamen Zeitraum
  2. getrennt nach ruhigen Phasen und Stressphasen
  3. Häufigkeit qualitativ unterschiedlicher Zustände (UIQ-Schwellen)
  4. Rauschen vs. systematische Unterschiede
  5. Verhalten in den für UIQ relevanten Stressphasen

Proxy: calc_pcr_proxy() aus ahsub/ko-aggregator market_aggregator.py (Commit 41a37fd, 27.09.2026)
wörtlich übernommen (nur Logging entfernt). Zustände wie in UIQ produktiv:
  Overlay (apply_macro_risk_overlay): < 0,75 „Gier“, > 1,10 „Panik“, sonst neutral
  Signal-Label (calc_pcr_proxy/fetch_pcr_cboe): < 0,70 ÜBERKAUFT, > 1,00 ÜBERVERKAUFT, sonst NEUTRAL
UIQ fragt produktiv totalpc.csv ab → Referenz: Total PCR (equity/index sekundär).

Aufruf: python run_h2_audit.py  → results/h2_audit/H2_audit.md, .json
Version: 1.0.0 (27.09.2026)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from datalayer import build_panel  # noqa: E402

CBOE = ROOT / "data" / "raw" / "cboe" / "2026-09-27"
OUT = ROOT / "results" / "h2_audit"
WINDOW = ("2009-09-18", "2019-10-04")   # VIX3M-Beginn … PCR-Ende
STRESS = [("Flash Crash / Euro 2010", "2010-04-23", "2010-07-02"),
          ("US-Downgrade 2011", "2011-07-22", "2011-10-03"),
          ("China / August 2015", "2015-08-17", "2015-09-30"),
          ("Volmageddon 2018", "2018-01-26", "2018-02-09"),
          ("2018 Q4", "2018-10-01", "2018-12-24")]   # identisch zu H1/H3, im PCR-Zeitraum


def calc_pcr_proxy(vix, vix3m, vvix):
    """Wörtlich aus UIQ calc_pcr_proxy() (ohne Logging); Defaults wie dort."""
    vix = 20.0 if vix is None else vix
    vix3m = 22.0 if vix3m is None else vix3m
    vvix = 90.0 if vvix is None else vvix
    if   vix >= 35:  pcr_base = 1.35
    elif vix >= 28:  pcr_base = 1.15
    elif vix >= 22:  pcr_base = 1.00
    elif vix >= 18:  pcr_base = 0.88
    elif vix >= 14:  pcr_base = 0.78
    else:            pcr_base = 0.68
    ratio = vix / vix3m if vix3m > 0 else 1.0
    if   ratio < 0.82:  pcr_base -= 0.10
    elif ratio < 0.90:  pcr_base -= 0.05
    elif ratio > 1.00:  pcr_base += 0.12
    elif ratio > 0.95:  pcr_base += 0.05
    if   vvix >= 120:  pcr_base += 0.12
    elif vvix >= 105:  pcr_base += 0.06
    elif vvix >= 95:   pcr_base += 0.02
    elif vvix <= 80:   pcr_base -= 0.05
    return round(max(0.50, min(1.40, pcr_base)), 3)


def state_overlay(x):
    return np.where(x < 0.75, "Gier", np.where(x > 1.10, "Panik", "neutral"))


def state_label(x):
    return np.where(x < 0.70, "ÜBERKAUFT", np.where(x > 1.00, "ÜBERVERKAUFT", "NEUTRAL"))


def kappa(a, b):
    cats = sorted(set(a) | set(b))
    ct = pd.crosstab(pd.Categorical(a, cats), pd.Categorical(b, cats), dropna=False).to_numpy()
    n = ct.sum(); po = np.trace(ct) / n
    pe = (ct.sum(0) * ct.sum(1)).sum() / n**2
    return round(float((po - pe) / (1 - pe)), 3) if pe < 1 else float("nan")


def rho(a, b):
    m = a.notna() & b.notna()
    return round(float(a[m].rank().corr(b[m].rank())), 3)


def runs(mask: pd.Series):
    """Längen zusammenhängender True-Serien."""
    g = (mask != mask.shift()).cumsum()
    return mask.groupby(g).agg(["first", "size"]).query("first")["size"]


def main():
    p, _ = build_panel(CBOE)
    x = p.loc[WINDOW[0]:WINDOW[1]].copy()
    x["proxy"] = [calc_pcr_proxy(None if pd.isna(a) else a, None if pd.isna(b) else b,
                                 None if pd.isna(c) else c)
                  for a, b, c in zip(x["VIX"], x["VIX3M"], x["VVIX"])]
    x = x[x["pcr_total"].notna()]
    R = {"fenster": [x.index.min().strftime("%Y-%m-%d"), x.index.max().strftime("%Y-%m-%d")],
         "tage": int(len(x))}

    # 1 Korrelation
    R["korrelation"] = {
        "rho_total_proxy": rho(x.pcr_total, x.proxy),
        "rho_equity_proxy": rho(x.pcr_equity, x.proxy),
        "rho_index_proxy": rho(x.pcr_index, x.proxy),
        "rho_total_VIX": rho(x.pcr_total, x.VIX),
        "rho_total_MA10_proxy": rho(x.pcr_total.rolling(10).mean(), x.proxy),
        "rho_total_MA10_proxy_MA10": rho(x.pcr_total.rolling(10).mean(), x.proxy.rolling(10).mean()),
        "rho_dtotal_dproxy_5T": rho(x.pcr_total.diff(5), x.proxy.diff(5)),
        "je_segment": {s: rho(g.pcr_total, g.proxy) for s, g in x.groupby("pcr_segment") if len(g) > 30},
    }
    R["verteilung"] = {c: {"mittel": round(float(x[c].mean()), 3),
                           "p05": round(float(x[c].quantile(.05)), 3),
                           "p95": round(float(x[c].quantile(.95)), 3)}
                       for c in ["pcr_total", "pcr_equity", "proxy"]}

    # 2 ruhig vs. Stress
    in_stress = pd.Series(False, index=x.index)
    for _, a, b in STRESS:
        in_stress.loc[a:b] = True
    R["ruhig_vs_stress"] = {
        "stressphasen": {"tage": int(in_stress.sum()), "rho_total_proxy": rho(x.pcr_total[in_stress], x.proxy[in_stress])},
        "uebrige": {"tage": int((~in_stress).sum()), "rho_total_proxy": rho(x.pcr_total[~in_stress], x.proxy[~in_stress])},
        "VIX_ueber_25": {"tage": int((x.VIX > 25).sum()), "rho_total_proxy": rho(x.pcr_total[x.VIX > 25], x.proxy[x.VIX > 25])},
        "VIX_bis_25": {"tage": int((x.VIX <= 25).sum()), "rho_total_proxy": rho(x.pcr_total[x.VIX <= 25], x.proxy[x.VIX <= 25])},
    }

    # 3 Zustände
    so_real, so_prx = state_overlay(x.pcr_total), state_overlay(x.proxy)
    sl_real, sl_prx = state_label(x.pcr_total), state_label(x.proxy)
    ct = pd.crosstab(pd.Series(so_prx, index=x.index, name="Proxy"), pd.Series(so_real, index=x.index, name="echte Total-PCR"))
    R["zustaende_overlay"] = {"uebereinstimmung": round(float((so_real == so_prx).mean()), 4),
                              "kappa": kappa(so_real, so_prx),
                              "kreuztabelle": {r: {c: int(ct.loc[r, c]) for c in ct.columns} for r in ct.index},
                              "anteile_echt": pd.Series(so_real).value_counts(normalize=True).round(4).to_dict(),
                              "anteile_proxy": pd.Series(so_prx).value_counts(normalize=True).round(4).to_dict()}
    R["zustaende_label"] = {"uebereinstimmung": round(float((sl_real == sl_prx).mean()), 4),
                            "kappa": kappa(sl_real, sl_prx),
                            "anteile_echt": pd.Series(sl_real).value_counts(normalize=True).round(4).to_dict(),
                            "anteile_proxy": pd.Series(sl_prx).value_counts(normalize=True).round(4).to_dict()}
    # gleiche Anteile: echte PCR mit eigenen Perzentilen auf Proxy-Anteile abbilden (Skalenunabhängig)
    q_lo = float((x.proxy < 0.75).mean()); q_hi = float((x.proxy > 1.10).mean())
    lo, hi = x.pcr_total.quantile(q_lo), x.pcr_total.quantile(1 - q_hi)
    so_real_q = np.where(x.pcr_total < lo, "Gier", np.where(x.pcr_total > hi, "Panik", "neutral"))
    R["zustaende_overlay_skalenbereinigt"] = {
        "schwellen_echt": [round(float(lo), 3), round(float(hi), 3)],
        "uebereinstimmung": round(float((so_real_q == so_prx).mean()), 4), "kappa": kappa(so_real_q, so_prx)}

    # 4 Rauschen vs. systematisch
    ac = lambda s, k: round(float(s.autocorr(k)), 3)
    diff = (x.pcr_total.rank(pct=True) - x.proxy.rank(pct=True))
    dis = pd.Series(so_real_q != so_prx, index=x.index)
    rl = runs(dis)
    R["rauschen"] = {
        "autokorr_total_1T": ac(x.pcr_total, 1), "autokorr_total_20T": ac(x.pcr_total, 20),
        "autokorr_proxy_1T": ac(x.proxy, 1), "autokorr_proxy_20T": ac(x.proxy, 20),
        "autokorr_rangdifferenz_1T": ac(diff, 1), "autokorr_rangdifferenz_20T": ac(diff, 20),
        "abweichungsserien_skalenbereinigt": {"anzahl": int(len(rl)), "median_tage": float(rl.median()) if len(rl) else 0,
                                              "anteil_tage_in_serien_ab_5": round(float(rl[rl >= 5].sum() / max(1, rl.sum())), 3)},
        "rangdifferenz_jahresmittel": {int(y): round(float(v), 3) for y, v in diff.groupby(diff.index.year).mean().items()},
    }

    # 5 Stressphasen
    st = {}
    for name, a, b in STRESS:
        g = x.loc[a:b]
        st[name] = {"tage": int(len(g)),
                    "proxy_mittel": round(float(g.proxy.mean()), 3), "total_mittel": round(float(g.pcr_total.mean()), 3),
                    "proxy_max": round(float(g.proxy.max()), 3), "total_max": round(float(g.pcr_total.max()), 3),
                    "anteil_panik_proxy": round(float((g.proxy > 1.10).mean()), 3),
                    "anteil_panik_echt": round(float((g.pcr_total > 1.10).mean()), 3),
                    "anteil_panik_echt_skalenbereinigt": round(float((g.pcr_total > hi).mean()), 3),
                    "erster_paniktag_proxy": (g.index[g.proxy > 1.10].min().strftime("%Y-%m-%d") if (g.proxy > 1.10).any() else None),
                    "erster_paniktag_echt_skalenbereinigt": (g.index[g.pcr_total > hi].min().strftime("%Y-%m-%d") if (g.pcr_total > hi).any() else None)}
    R["stressphasen"] = st

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "H2_audit.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=str))
    print(json.dumps(R, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
