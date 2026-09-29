"""
run_h2_extension.py – H2-Ext: Replikation des H2-Informationsaudits auf 07.10.2019 – 25.09.2026.

Präregistrierung: docs/preregistration/H2_EXTENSION_2020_2026.md, Rev. 3 (Commit d9fe86f),
committet VOR der Auswertung. Deskriptiv – kein Renditetest, keine Parameteroptimierung,
keine Gesamtbewertung von H2 (§7b).

Code-Identität (§3): calc_pcr_proxy, state_overlay, state_label, kappa, rho, runs werden
UNVERÄNDERT aus run_h2_audit.py importiert. audit() folgt Zeile für Zeile run_h2_audit.main();
abweichend sind nur Fenster, Datenspalten (Daily-PCR), Stressphasen und der Ausschluss
fehlender Proxy-Eingänge (§2).

    python run_h2_extension.py --selftest   # Identitätsprüfung: audit() auf dem Original-
                                            # fenster muss H2_audit.json exakt reproduzieren
                                            # (berührt KEINE Daten nach 04.10.2019)
    python run_h2_extension.py              # der eine präregistrierte Lauf (erst nach Freigabe)

Ausgabe: results/h2_extension/H2_ext.json, H2_ext.md

Version: 1.0.0 (29.09.2026)
Changelog:
  1.0.0 (29.09.2026) – Erstfassung zur Code-Review (noch nicht auf neuen Daten ausgeführt).
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
from datalayer import build_panel, verify_snapshot  # noqa: E402
from run_h2_audit import (calc_pcr_proxy, kappa, rho, runs,  # noqa: E402  – unverändert
                          state_label, state_overlay)

AUDIT_SHA256 = "b9fac74d579e37f1a3e223b658ead053893ef7a6159c83969866470341f42e9f"
AUDIT_JSON_SHA256 = "2a220c4eb4ad3575723ae11244de40ddc42d93124386b171dd4de0bb5d1fce19"
SNAP_IDX = ROOT / "data" / "raw" / "cboe" / "2026-09-27"
SNAP_PCR = ROOT / "data" / "raw" / "cboe" / "2026-09-28_pcr_daily"
SNAP_SUMS = {SNAP_IDX: "49d10cbb954e65fad1b8707780959e340618dbbaf0931b00f2122048670dad21",
             SNAP_PCR: "dde0c099de34b721f491ef4c25ec275715c72317ab1240f0354a91eceb322e4c"}
OUT = ROOT / "results" / "h2_extension"

# §2 / §5 / §4 – fest
WINDOW = ("2019-10-07", "2026-09-25")
SUBWINDOWS = [("2019-10-07", "2022-12-31"), ("2023-01-01", "2026-09-25")]
STRESS = [("Covid 2020", "2020-02-19", "2020-03-23"),
          ("Bärenmarkt 2022", "2022-01-03", "2022-10-12"),
          ("Yen-Carry 2024", "2024-07-16", "2024-08-07")]
ORIG_THRESHOLDS = (0.93, 1.16)          # skalenbereinigt aus 2009–2019 (H2_audit.json)
MIN_DAYS_MAIN = 1000                    # §7 Grenzfall
MIN_DAYS_PART = 60                      # §7a Stressphasen

# Original-Parameter für die Selbstprüfung
ORIG_WINDOW = ("2009-09-18", "2019-10-04")
ORIG_STRESS = [("Flash Crash / Euro 2010", "2010-04-23", "2010-07-02"),
               ("US-Downgrade 2011", "2011-07-22", "2011-10-03"),
               ("China / August 2015", "2015-08-17", "2015-09-30"),
               ("Volmageddon 2018", "2018-01-26", "2018-02-09"),
               ("2018 Q4", "2018-10-01", "2018-12-24")]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def add_proxy(x: pd.DataFrame) -> pd.DataFrame:
    """Wie run_h2_audit.main(): NaN → None → UIQ-Defaults."""
    x = x.copy()
    x["proxy"] = [calc_pcr_proxy(None if pd.isna(a) else a, None if pd.isna(b) else b,
                                 None if pd.isna(c) else c)
                  for a, b, c in zip(x["VIX"], x["VIX3M"], x["VVIX"])]
    return x


def audit(x: pd.DataFrame, stress) -> dict:
    """Abschnitte 1–5, Zeile für Zeile wie run_h2_audit.main() (x enthält bereits 'proxy')."""
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
    for _, a, b in stress:
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
    q_lo = float((x.proxy < 0.75).mean()); q_hi = float((x.proxy > 1.10).mean())
    lo, hi = x.pcr_total.quantile(q_lo), x.pcr_total.quantile(1 - q_hi)
    so_real_q = np.where(x.pcr_total < lo, "Gier", np.where(x.pcr_total > hi, "Panik", "neutral"))
    R["zustaende_overlay_skalenbereinigt"] = {
        "schwellen_echt": [round(float(lo), 3), round(float(hi), 3)],
        "uebereinstimmung": round(float((so_real_q == so_prx).mean()), 4), "kappa": kappa(so_real_q, so_prx)}

    # 4 Rauschen vs. systematisch
    ac = lambda s, k: round(float(s.autocorr(k)), 3)  # noqa: E731
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
    for name, a, b in stress:
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
    return R


# ---------- §7 Einstufung --------------------------------------------------------------

CATS = ["repliziert", "abgeschwächt", "nicht repliziert"]   # günstig → ungünstig


def _nan(v) -> bool:
    return v is None or (isinstance(v, float) and np.isnan(v))


def metrics3(x: pd.DataFrame, col: str = "pcr_total") -> dict:
    """Die drei Einstufungskennzahlen (§7) für eine PCR-Spalte; x enthält 'proxy'."""
    x = x[x[col].notna()]
    n = int(len(x))
    r = rho(x[col], x.VIX) if n > 2 else float("nan")
    so_real, so_prx = state_overlay(x[col]), state_overlay(x.proxy)
    k = kappa(so_real, so_prx) if n else float("nan")
    if n:
        a_prx = float((so_prx == "Gier").mean())          # ungerundet (§7, Rev. 3)
        a_real = float((so_real == "Gier").mean())
        d = round(100.0 * (a_prx - a_real), 3)
    else:
        a_prx = a_real = d = float("nan")
    return {"tage": n, "rho_VIX": r, "rho_VIX_betrag": (float("nan") if _nan(r) else round(abs(r), 3)),
            "kappa_overlay": k, "delta_gier_pp": d,
            "anteil_gier_proxy": (None if _nan(a_prx) else round(a_prx, 4)),
            "anteil_gier_echt": (None if _nan(a_real) else round(a_real, 4))}


def classify(m: dict, min_days: int) -> dict:
    if m["tage"] < min_days:
        return {k: "nicht bestimmbar" for k in ("1", "2a", "2b")}
    out = {}
    r = m["rho_VIX_betrag"]
    out["1"] = ("nicht bestimmbar" if _nan(r) else
                "repliziert" if r < 0.5 else "abgeschwächt" if r < 0.8 else "nicht repliziert")
    k = m["kappa_overlay"]
    out["2a"] = ("nicht bestimmbar" if _nan(k) else
                 "repliziert" if k < 0.2 else "abgeschwächt" if k < 0.4 else "nicht repliziert")
    d = m["delta_gier_pp"]
    out["2b"] = ("nicht bestimmbar" if _nan(d) else
                 "repliziert" if d >= 20.0 else "abgeschwächt" if d >= 10.0 else "nicht repliziert")
    return out


def deviation(main_cls: str, part_cls: str) -> str:
    """§7a: 'Abweichung' nur bei ungünstigerer Kategorie; NaN → 'nicht bestimmbar'."""
    if part_cls == "nicht bestimmbar":
        return "nicht bestimmbar"
    if main_cls == "nicht bestimmbar":
        return "–"
    return "Abweichung" if CATS.index(part_cls) > CATS.index(main_cls) else "–"


# ---------- Laden ---------------------------------------------------------------------

def load_panel(orig: bool = False) -> pd.DataFrame:
    for d, expected in SNAP_SUMS.items():
        if orig and d == SNAP_PCR:
            continue
        verify_snapshot(d)
        got = sha256(d / "SHA256SUMS.txt")
        if got != expected:
            raise SystemExit(f"ABBRUCH – {d}/SHA256SUMS.txt weicht von der Präregistrierung ab: {got}")
    if orig:
        p, _ = build_panel(SNAP_IDX)
        return p
    p, _ = build_panel([SNAP_IDX, SNAP_PCR])
    # Nur Daily-Spalten (§2), unter den Namen des Originals, damit audit() unverändert bleibt
    p = p.drop(columns=[c for c in ("pcr_total", "pcr_equity", "pcr_index") if c in p])
    return p.rename(columns={"pcr_total_daily": "pcr_total", "pcr_equity_daily": "pcr_equity",
                             "pcr_index_daily": "pcr_index"})


def selftest() -> int:
    if sha256(ROOT / "run_h2_audit.py") != AUDIT_SHA256:
        print("ABBRUCH – run_h2_audit.py weicht vom präregistrierten Stand ab."); return 1
    orig_json = ROOT / "results" / "h2_audit" / "H2_audit.json"
    if sha256(orig_json) != AUDIT_JSON_SHA256:
        print("ABBRUCH – H2_audit.json weicht vom präregistrierten Stand ab."); return 1
    p = load_panel(orig=True)
    x = add_proxy(p.loc[ORIG_WINDOW[0]:ORIG_WINDOW[1]])
    R = json.loads(json.dumps(audit(x, ORIG_STRESS), ensure_ascii=False, default=str))
    ref = json.loads(orig_json.read_text())
    if R != ref:
        diffs = [k for k in ref if R.get(k) != ref[k]]
        print(f"SELBSTTEST FEHLGESCHLAGEN – abweichende Abschnitte: {diffs}"); return 1
    print("SELBSTTEST OK – audit() reproduziert H2_audit.json exakt (Fenster 2009–2019).")
    return 0


# ---------- Hauptlauf -----------------------------------------------------------------

def main() -> int:
    if selftest():
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "H2_ext.json").exists():
        print("ABBRUCH – Ergebnis existiert bereits (präregistriert ist genau ein Lauf)."); return 1

    p = load_panel()
    w = p.loc[WINDOW[0]:WINDOW[1]]
    w = w[w["pcr_total"].notna()]
    missing = w[["VIX", "VIX3M", "VVIX"]].isna().any(axis=1)
    excluded = [d.strftime("%Y-%m-%d") for d in w.index[missing]]
    x = add_proxy(w[~missing])                       # Hauptlauf: Ausschluss (§2)
    x_def = add_proxy(w)                             # Zusatz: UIQ-Defaults (§2)

    R = {"praeregistrierung": "docs/preregistration/H2_EXTENSION_2020_2026.md Rev. 3",
         "ausgeschlossen_fehlende_proxy_eingaenge": {"anzahl": len(excluded), "tage": excluded},
         "audit": audit(x, STRESS)}

    # §7 Einstufung (Hauptfenster, Total-PCR)
    m_main = metrics3(x)
    cls = classify(m_main, MIN_DAYS_MAIN)
    R["einstufung"] = {"kennzahlen": m_main, "aussagen": cls}

    # §7a Teilbefunde
    parts = {}
    for name, a, b in STRESS:
        parts[f"Stressphase {name}"] = (x.loc[a:b], "pcr_total", MIN_DAYS_PART)
    for a, b in SUBWINDOWS:
        parts[f"Teilfenster {a[:4]}–{b[:4]}"] = (x.loc[a:b], "pcr_total", 0)
    parts["Equity-PCR"] = (x, "pcr_equity", 0)
    parts["Index-PCR"] = (x, "pcr_index", 0)
    parts["UIQ-Defaults statt Ausschluss"] = (x_def, "pcr_total", 0)
    tb = {}
    for name, (df, col, mind) in parts.items():
        m = metrics3(df, col)
        c = classify(m, mind)
        tb[name] = {"kennzahlen": m, "einstufung": c,
                    "abweichung": {k: deviation(cls[k], c[k]) for k in cls}}
    R["teilbefunde"] = tb
    R["uneinheitlich"] = {k: sum(v["abweichung"][k] == "Abweichung" for v in tb.values()) > 1 for k in cls}

    # §4 Zusatz: eingefrorene Original-Schwellen 0,93 / 1,16
    lo, hi = ORIG_THRESHOLDS
    so_prx = state_overlay(x.proxy)
    so_o = np.where(x.pcr_total < lo, "Gier", np.where(x.pcr_total > hi, "Panik", "neutral"))
    R["skalenbereinigt_originalschwellen"] = {
        "schwellen": [lo, hi], "uebereinstimmung": round(float((so_o == so_prx).mean()), 4),
        "kappa": kappa(so_o, so_prx)}
    # §4 Zusatz: vollständiges Audit je Teilfenster
    R["audit_teilfenster"] = {f"{a}–{b}": audit(x.loc[a:b], STRESS) for a, b in SUBWINDOWS}

    (OUT / "H2_ext.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=str))
    (OUT / "H2_ext.md").write_text(report_md(R))
    print((OUT / "H2_ext.md").read_text())
    return 0


def report_md(R: dict) -> str:
    e = R["einstufung"]; m = e["kennzahlen"]; a = e["aussagen"]
    L = ["# H2-Ext · Replikation H2-Informationsaudit 07.10.2019 – 25.09.2026", "",
         f"Präregistrierung: `{R['praeregistrierung']}`. Deskriptiv, kein Renditetest, "
         "keine Gesamtbewertung (§7b). Rohwerte: `H2_ext.json`.", "",
         f"Auswertbare Tage: {m['tage']} · ausgeschlossen (fehlende VIX/VIX3M/VVIX): "
         f"{R['ausgeschlossen_fehlende_proxy_eingaenge']['anzahl']}", "",
         "## Einstufung (§7, Total-PCR, Hauptfenster)", "",
         "| Aussage | Kennzahl | Wert | Einstufung | uneinheitlich |", "|---|---|---|---|---|",
         f"| 1 Rangassoziation mit dem VIX | \\|ρ(Total-PCR, VIX)\\| (ρ = {m['rho_VIX']}) | {m['rho_VIX_betrag']} | {a['1']} | {'ja' if R['uneinheitlich']['1'] else 'nein'} |",
         f"| 2a Proxy bildet PCR nicht ab | κ Overlay | {m['kappa_overlay']} | {a['2a']} | {'ja' if R['uneinheitlich']['2a'] else 'nein'} |",
         f"| 2b Skalenproblem | Δ Anteil „Gier“ Proxy − echt (Pp) | {m['delta_gier_pp']} (Proxy {m['anteil_gier_proxy']}, echt {m['anteil_gier_echt']}) | {a['2b']} | {'ja' if R['uneinheitlich']['2b'] else 'nein'} |",
         "", "Zulässige Interpretation nur gemäß §7c.", "",
         "## Teilbefunde (§7a – ändern die Einstufung nicht)", "",
         "| Teilbefund | Tage | \\|ρ\\| VIX | κ | Δ Pp | 1 | 2a | 2b |", "|---|---|---|---|---|---|---|---|"]
    for name, v in R["teilbefunde"].items():
        k = v["kennzahlen"]; c = v["einstufung"]; d = v["abweichung"]
        cell = lambda q: c[q] + (" ⚠ Abweichung" if d[q] == "Abweichung" else "")  # noqa: E731
        L.append(f"| {name} | {k['tage']} | {k['rho_VIX_betrag']} | {k['kappa_overlay']} | "
                 f"{k['delta_gier_pp']} | {cell('1')} | {cell('2a')} | {cell('2b')} |")
    o = R["skalenbereinigt_originalschwellen"]
    L += ["", "## Zusätzlich (§4, neu gegenüber Original)", "",
          f"- Skalenbereinigt mit Original-Schwellen {o['schwellen']}: Übereinstimmung "
          f"{o['uebereinstimmung']}, κ {o['kappa']}",
          "- Vollständige Audit-Abschnitte 1–5 für Hauptfenster und Teilfenster: siehe JSON."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
