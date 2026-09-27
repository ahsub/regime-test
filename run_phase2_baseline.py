"""
run_phase2_baseline.py – Phase 2 der Regime-Backtest-Roadmap: Baseline reproduzieren.

classify_regime_v2() und regime_to_position_uniform() werden UNVERÄNDERT aus
compare_approaches_final_v2.py importiert. Die Performance-Rechnung folgt exakt
calculate_performance() dort (Position t-1 × Rendite t, rf 2 % p. a., keine Kosten).

Varianten:
  A0 Exakte Replik     – wie compare_approaches_final_v2.load_data(): Schnittmenge mit
                          trading_signals.csv und rolling_hmm_enhanced_labels.csv
                          → tatsächliches Fenster 20.10.2011 … 27.08.2026 (HMM-Anlauf).
                          Muss Sharpe 0,753 / Rendite 403,18 % / DD −20,29 % / 261 Trades treffen.
  A  Reproduktion alt   – market_data.csv (wie bisher) + S&P-500-Renditen aus Snapshot,
                          2011-01-03 … 2026-08-28. Prüft, ob die Pipeline die bekannte
                          Sharpe ≈ 0,75 trifft.
  B  sauber, gleiches Fenster – Cboe-Snapshot (Phase 1) + echtes GEX (vor 02.05.2011
                          kein GEX → None statt rückwärts aufgefüllter Wert).
  C  sauber, GEX-Fenster – wie B, aber erst ab 02.05.2011 (echtes GEX vorhanden).
  D  sauber, ohne GEX    – gleiches Fenster wie C, gex=None → Beitrag des GEX-Filters.
  E  ohne GEX, lang      – ab Beginn der Cboe-VIX3M-Historie (18.09.2009) bis 25.09.2026.

Aufruf:  python run_phase2_baseline.py
Ergebnis: results/phase2/baseline_<datum>.md und .json

Version: 1.1.0 (27.09.2026) – Variante A0 (exakte Replik des alten Fensters)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from datalayer import build_panel, verify_snapshot  # noqa: E402
from compare_approaches_final_v2 import (  # noqa: E402  (unverändert übernommen)
    classify_regime_v2, regime_to_position_uniform)

CBOE = ROOT / "data" / "raw" / "cboe" / "2026-09-27"
YAHOO = ROOT / "data" / "raw" / "yahoo" / "2026-09-27"
SQZ = ROOT / "data" / "raw" / "squeezemetrics" / "2026-08-30"
OUT = ROOT / "results" / "phase2"
RF = 0.02 / 252
REFERENZ_SHARPE = 0.75  # README / 08_STRATEGY_COMPARISON.md, Stand 02.09.2026

STRESS = {
    "2011 US-Downgrade": ("2011-07-22", "2011-10-03"),
    "2015 China/Aug": ("2015-08-17", "2015-09-30"),
    "2018 Volmageddon": ("2018-01-26", "2018-02-09"),
    "2018 Q4": ("2018-10-01", "2018-12-24"),
    "2020 Covid": ("2020-02-19", "2020-03-23"),
    "2022 Bärenmarkt": ("2022-01-03", "2022-10-12"),
    "2024 Yen-Carry": ("2024-07-16", "2024-08-07"),
}


def load_inputs():
    verify_snapshot(YAHOO)
    verify_snapshot(SQZ)
    spx = pd.read_csv(YAHOO / "GSPC.csv", index_col=0, parse_dates=True)["Close"]
    ret = spx.pct_change().dropna().rename("ret")
    dix = pd.read_csv(SQZ / "DIX.csv", index_col=0, parse_dates=True)
    gex = dix["gex"].astype("float64").rename("GEX")
    panel, _ = build_panel(CBOE)
    return panel, ret, gex


def signals(vix: pd.Series, vix3m: pd.Series, gex: pd.Series | None) -> pd.DataFrame:
    rows = []
    for d in vix.index:
        v, v3 = vix.get(d), vix3m.get(d)
        v = None if pd.isna(v) else float(v)
        v3 = None if pd.isna(v3) else float(v3)
        g = None
        if gex is not None and d in gex.index and not pd.isna(gex.loc[d]):
            g = float(gex.loc[d])
        regime, _ = classify_regime_v2(v, v3, g)
        rows.append((d, regime, regime_to_position_uniform(regime)))
    return pd.DataFrame(rows, columns=["date", "regime", "position"]).set_index("date")


def perf(sig: pd.DataFrame, ret: pd.Series) -> dict:
    idx = sig.index.intersection(ret.index)
    pos = sig.loc[idx, "position"].shift(1).fillna(0)
    r = pos * ret.loc[idx]
    return _stats(r, pos, ret.loc[idx])


def _stats(r: pd.Series, pos: pd.Series | None, bench: pd.Series) -> dict:
    ex = r - RF
    sharpe = float(np.sqrt(252) * ex.mean() / ex.std(ddof=0)) if ex.std(ddof=0) > 0 else 0.0
    cum = (1 + r).cumprod()
    dd = float((cum / cum.cummax() - 1).min())
    out = {
        "start": r.index.min().strftime("%Y-%m-%d"),
        "ende": r.index.max().strftime("%Y-%m-%d"),
        "tage": int(len(r)),
        "sharpe": round(sharpe, 3),
        "rendite": round(float(cum.iloc[-1] - 1), 4),
        "max_drawdown": round(dd, 4),
    }
    if pos is not None:
        out["trades"] = int((pos != pos.shift(1)).sum())
        out["avg_position"] = round(float(pos.mean()), 3)
        years = {}
        for y, g in r.groupby(r.index.year):
            years[int(y)] = round(float((1 + g).prod() - 1), 4)
        out["jahre"] = years
        st = {}
        for name, (a, b) in STRESS.items():
            rr = r.loc[a:b]
            bb = bench.loc[a:b]
            if len(rr) > 3:
                st[name] = {"strategie": round(float((1 + rr).prod() - 1), 4),
                            "buy_hold": round(float((1 + bb).prod() - 1), 4)}
        out["stress"] = st
    return out


def main() -> int:
    panel, ret, gex = load_inputs()
    res = {}

    md = pd.read_csv(ROOT / "data" / "market_data.csv", index_col=0, parse_dates=True)

    # A0 – exakte Replik des alten Fensters (Schnittmenge mit HMM-Labels)
    def _idx(f):
        d = pd.read_csv(ROOT / "data" / "results" / f, index_col=0, parse_dates=True)
        return pd.to_datetime(d.index, utc=True).tz_localize(None).normalize()
    ret_old = ret.loc["2011-01-01":"2026-08-27"]  # yf end=2026-08-28 ist exklusiv
    common = (_idx("trading_signals.csv").intersection(_idx("rolling_hmm_enhanced_labels.csv"))
              .intersection(ret_old.index).intersection(md.index))
    res["A0 Exakte Replik (Fenster wie bisher, ab HMM-Start)"] = perf(
        signals(md.loc[common, "VIX"], md.loc[common, "VIX3M"], md.loc[common, "GEX"]),
        ret_old.loc[common])

    # A – Reproduktion mit altem market_data.csv (inkl. rückwärts aufgefülltem GEX)
    md = md.loc["2011-01-01":"2026-08-28"]
    idx = md.index.intersection(ret.index)
    sA = signals(md.loc[idx, "VIX"], md.loc[idx, "VIX3M"], md.loc[idx, "GEX"])
    res["A Reproduktion alt (2011-01, altes market_data)"] = perf(sA, ret)

    vix, vix3m = panel["VIX"], panel["VIX3M"]
    w_b = slice("2011-01-01", "2026-08-28")
    w_c = slice("2011-05-02", "2026-08-28")
    res["B sauber, gleiches Fenster (2011-01)"] = perf(
        signals(vix.loc[w_b], vix3m.loc[w_b], gex), ret)
    res["C sauber, GEX-Fenster (2011-05)"] = perf(
        signals(vix.loc[w_c], vix3m.loc[w_c], gex), ret)
    res["D sauber, ohne GEX (2011-05)"] = perf(
        signals(vix.loc[w_c], vix3m.loc[w_c], None), ret)
    first_v3 = vix3m.dropna().index.min()
    w_e = slice(first_v3, vix.dropna().index.max())
    res["E ohne GEX, lang (ab VIX3M-Beginn)"] = perf(
        signals(vix.loc[w_e], vix3m.loc[w_e], None), ret)

    bh = {}
    for k, v in res.items():
        r = ret.loc[v["start"]:v["ende"]]
        bh[k] = _stats(r, None, r)

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = "2026-09-27"
    (OUT / f"baseline_{stamp}.json").write_text(
        json.dumps({"varianten": res, "buy_hold": bh}, indent=2, ensure_ascii=False))

    L = [f"# Phase 2 – Baseline `classify_regime_v2()` ({stamp})", "",
         f"Referenz bisher: Sharpe {REFERENZ_SHARPE} (2011–2026, README 02.09.2026). "
         "Rechnung wie `calculate_performance()`: Position t-1 × S&P-500-Rendite t, "
         "rf 2 % p. a., ohne Kosten.", "",
         "| Variante | Zeitraum | Sharpe | Rendite | Max DD | Trades | Ø Pos. | B&H Sharpe | B&H DD |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, v in res.items():
        b = bh[k]
        L.append(f"| {k} | {v['start']} – {v['ende']} | **{v['sharpe']:.2f}** | "
                 f"{v['rendite']:.0%} | {v['max_drawdown']:.1%} | {v['trades']} | "
                 f"{v['avg_position']:.2f} | {b['sharpe']:.2f} | {b['max_drawdown']:.1%} |")
    L += ["", "## Stressphasen (Periodenrendite Strategie / Buy & Hold)", ""]
    names = list(STRESS)
    L.append("| Variante | " + " | ".join(names) + " |")
    L.append("|---|" + "---|" * len(names))
    for k, v in res.items():
        cells = []
        for n in names:
            s = v["stress"].get(n)
            cells.append("–" if s is None else f"{s['strategie']:+.1%} / {s['buy_hold']:+.1%}")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    L += ["", "## Jahresrenditen (Variante E)", ""]
    e = res["E ohne GEX, lang (ab VIX3M-Beginn)"]["jahre"]
    L.append("| " + " | ".join(str(y) for y in e) + " |")
    L.append("|" + "---|" * len(e))
    L.append("| " + " | ".join(f"{v:+.0%}" for v in e.values()) + " |")
    (OUT / f"baseline_{stamp}.md").write_text("\n".join(L) + "\n")

    for k, v in res.items():
        print(f"{k:52s} Sharpe {v['sharpe']:5.2f}  Rendite {v['rendite']:7.0%}  "
              f"DD {v['max_drawdown']:6.1%}  Trades {v['trades']:4d}  | B&H Sharpe {bh[k]['sharpe']:.2f}")
    print(f"\nBericht: {(OUT / f'baseline_{stamp}.md').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
