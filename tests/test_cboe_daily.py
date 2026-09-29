"""
Tests für src/datalayer/cboe_daily.py, die PCR-Nahtstelle in panel.py und den
Offline-Lauf von scripts/fetch_cboe_pcr_daily.py.

Die Fixture-Zahlen sind die realen Werte der Cboe-Seite für den 01.04.2024
(abgerufen 28.09.2026). Das Markup ist nachgebildet – der echte Seitenaufbau
wird beim ersten Lauf des Fetchers geprüft (Summen-/Ratio-Kontrollen je Tag).

Aufruf ohne pytest:   python tests/test_cboe_daily.py

Version: 1.1.0 (29.09.2026)
Changelog:
  1.1.0 (29.09.2026) – Fetcher-Test auf --snapshot umgestellt; Update-Lauf ohne Snapshot geprüft.
  1.0.0 (28.09.2026) – Erstfassung.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from datalayer import build_panel, parse_cboe_pcr, quality_report  # noqa: E402
from datalayer.cboe_daily import (DailyParseError, parse_daily_html,  # noqa: E402
                                  to_frame, write_cboe_csv)
from datalayer.panel import report_markdown  # noqa: E402

NAV = """<nav><ul><li><a href="#">Index Options</a></li>
<li><a href="#">Equity Options</a></li><li><a href="#">Volume Reports</a></li>
<li><a href="#">Cboe Volatility Index (VIX)</a></li></ul></nav>
<script>var x = {"INDEX OPTIONS": "VOLUME 1 2 3"};</script>"""


def _table(title: str, c: int, p: int) -> str:
    return (f"<h4>{title}</h4><table><thead><tr><th>Name</th><th>Call</th><th>Put</th>"
            f"<th>Total</th></tr></thead><tbody><tr><td>VOLUME</td><td>{c:,}</td>"
            f"<td>{p:,}</td><td>{c + p:,}</td></tr><tr><td>OPEN INTEREST</td>"
            f"<td>99,999,999</td><td>88,888,888</td><td>188,888,887</td></tr></tbody></table>")


def page(idx=(1452247, 1669576), etp=(782821, 758850), eq=(1137667, 741202),
         total=None, ratios=None) -> str:
    total = total or (idx[0] + etp[0] + eq[0], idx[1] + etp[1] + eq[1])
    ratios = ratios if ratios is not None else {
        "TOTAL PUT/CALL RATIO": "0.94", "INDEX PUT/CALL RATIO": "1.15",
        "EXCHANGE TRADED PRODUCTS PUT/CALL RATIO": "0.97",
        "EQUITY PUT/CALL RATIO": "0.65",
        "CBOE VOLATILITY INDEX (VIX) PUT/CALL RATIO": "0.20",
        "SPX + SPXW PUT/CALL RATIO": "1.41"}
    rt = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in ratios.items())
    body = (NAV + "<main><h3>Ratios</h3><table><tr><th>Name</th><th>Value</th></tr>"
            + rt + "</table>"
            + _table("SUM OF ALL PRODUCTS", *total)
            + _table("INDEX OPTIONS", *idx)
            + _table("EXCHANGE TRADED PRODUCTS", *etp)
            + _table("EQUITY OPTIONS", *eq)
            + _table("CBOE VOLATILITY INDEX (VIX)", 318813, 62854)
            + _table("SPX + SPXW", 1100763, 1547345)
            + _table("OEX", 16, 14) + "</main>")
    return f"<html><head><style>.a{{}}</style></head><body>{body}</body></html>"


NO_DATA = ("<html><body>" + NAV + "<main><p>No data available for the selected date."
           "</p></main></body></html>")


def test_parse_real_numbers():
    st = parse_daily_html(page())
    assert st.volumes["total"] == (3372735, 3169628, 6542363)
    assert st.volumes["index"] == (1452247, 1669576, 3121823)
    assert st.volumes["etp"] == (782821, 758850, 1541671)
    assert st.volumes["equity"] == (1137667, 741202, 1878869)
    assert st.volumes["vix"] == (318813, 62854, 381667)
    assert st.volumes["spx"] == (1100763, 1547345, 2648108)
    assert st.ratios["equity"] == 0.65 and st.ratios["total"] == 0.94
    assert st.pcr("equity") == (0.65, "seite")
    assert not st.warnings


def test_no_data_page():
    assert parse_daily_html(NO_DATA) is None


def test_missing_ratios_fall_back_to_computed():
    st = parse_daily_html(page(ratios={}))
    assert st.pcr("equity") == (round(741202 / 1137667, 2), "berechnet")
    assert any("keine Ratio" in w for w in st.warnings)


def _raises(html: str, text: str):
    try:
        parse_daily_html(html)
    except DailyParseError as e:
        assert text in str(e), str(e)
    else:
        raise AssertionError(f"kein DailyParseError ({text})")


def test_sum_mismatch_is_error():
    _raises(page(total=(3372736, 3169628)), "Summe Calls")


def test_ratio_mismatch_is_error():
    r = {"TOTAL PUT/CALL RATIO": "0.94", "EQUITY PUT/CALL RATIO": "0.80"}
    _raises(page(ratios=r), "equity: Ratio")


def test_missing_required_table_is_error():
    _raises(page().replace("EXCHANGE TRADED PRODUCTS</h4>", "ETPs</h4>"),
            "EXCHANGE TRADED PRODUCTS")


def _snap(d: Path, files: dict[str, str]):
    d.mkdir(parents=True)
    (d / "SHA256SUMS.txt").write_text("".join(
        f"{hashlib.sha256(c.encode()).hexdigest()}  {n}\n" for n, c in files.items()))
    for n, c in files.items():
        (d / n).write_text(c)


def test_roundtrip_and_splice():
    days = {pd.Timestamp("2019-10-07"): parse_daily_html(page()),
            pd.Timestamp("2019-10-08"): parse_daily_html(
                page(eq=(1000000, 700000), ratios={}))}
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        daily = {}
        for key, fname in (("total", "totalpc_daily.csv"), ("equity", "equitypc_daily.csv")):
            write_cboe_csv(to_frame(days, key), key, t / fname, "2026-09-28")
            daily[fname] = (t / fname).read_text()
        df = parse_cboe_pcr(t / "equitypc_daily.csv")
        assert df.loc["2019-10-07", "calls"] == 1137667 and df.loc["2019-10-08", "pcr"] == 0.7

        vix = "DATE,OPEN,HIGH,LOW,CLOSE\n" + "".join(
            f"{d:%m/%d/%Y},1,1,1,{15 + i}\n"
            for i, d in enumerate(pd.bdate_range("2019-10-01", "2019-10-08")))
        csv = ("Cboe Put/Call data\n, PRODUCT: EQUITY,,EXCHANGE: Cboe,\n"
               "DATE,CALL,PUT,TOTAL,P/C Ratio\n"
               "10/03/2019, 847645, 656572, 1504217, 0.77\n"
               "10/04/2019, 916877, 598296, 1515173, 0.65\n")
        _snap(t / "raw" / "2026-09-27", {"VIX_History.csv": vix, "equitypc.csv": csv})
        daily["fetch_report.json"] = json.dumps({"x": 1})
        _snap(t / "raw" / "2026-09-28_pcr_daily", daily)
        panel, info = build_panel([t / "raw" / "2026-09-27", t / "raw" / "2026-09-28_pcr_daily"])
        full = panel["pcr_equity_full"]
        assert full.loc["2019-10-04"] == 0.65 and full.loc["2019-10-07"] == 0.65
        assert full.loc["2019-10-08"] == 0.7 and pd.isna(full.loc["2019-10-02"])
        assert panel.loc["2019-10-07", "pcr_equity_full_volume"] == 1878869
        assert "pcr_total_full" not in panel          # keine totalpc.csv-Basis
        sp = info["pcr_splice"]["pcr_equity"]
        assert sp["csv_letzter_tag"] == "2019-10-04" and sp["daily_erster_tag"] == "2019-10-07"
        assert sp["ueberlappung_tage"] == 0
        qc = quality_report(panel, info)
        assert qc["pcr_splice"]["pcr_equity"]["handelstage_zwischen"] == 0
        assert qc["series"]["pcr_equity_full"]["rows"] == 4
        assert "PCR-Nahtstelle" in report_markdown(qc)


def test_fetcher_offline_writes_snapshot():
    spec = importlib.util.spec_from_file_location(
        "fetcher", ROOT / "scripts" / "fetch_cboe_pcr_daily.py")
    fx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fx)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        fx.CACHE, fx.OUT_ROOT = t / "cache", t / "out"
        fx.CACHE.mkdir()
        (fx.CACHE / "2019-10-04.html").write_text(NO_DATA)
        (fx.CACHE / "2019-10-07.html").write_text(page())
        (fx.CACHE / "2019-10-08.html").write_text(page(eq=(1000000, 700000), ratios={}))
        args = ["--start", "2019-10-04", "--end", "2019-10-08", "--offline"]
        assert fx.main(args) == 0                        # Update-Lauf: kein Snapshot
        assert not fx.OUT_ROOT.exists()
        rc = fx.main(args + ["--snapshot"])
        assert rc == 0
        out = next(fx.OUT_ROOT.iterdir())
        rep = json.loads((out / "fetch_report.json").read_text())
        assert rep["erster_datentag"] == "2019-10-07" and rep["datentage"] == 2
        assert rep["keine_daten_vor_erstem_datentag"] == ["2019-10-04"]
        from datalayer import verify_snapshot
        assert len(verify_snapshot(out)) == 7          # 6 CSV + Bericht
        # Wiederholter Lauf: Snapshot existiert → Abbruch statt Überschreiben
        assert fx.main(args + ["--snapshot"]) == 1
        # Doppelte Seite (identische Volumina) → Fehler, kein Snapshot
        (fx.CACHE / "2019-10-08.html").write_text(page())
        fx.OUT_ROOT = t / "out2"
        assert fx.main(args + ["--snapshot"]) == 1
        assert not fx.OUT_ROOT.exists()


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} Tests bestanden")
