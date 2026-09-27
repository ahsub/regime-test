"""
Tests für src/datalayer (Positiv-/Negativfälle mit kleinen Fixtures).

Aufruf ohne pytest:   python tests/test_datalayer.py
Mit pytest ebenfalls lauffähig.

Version: 1.1.0 (27.09.2026)
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from datalayer import (SnapshotError, build_panel, parse_cboe_index,  # noqa: E402
                       parse_cboe_pcr, quality_report, verify_snapshot)

VIX = """DATE,OPEN,HIGH,LOW,CLOSE
05/28/2012,20,21,19,19.0
05/29/2012,20,21,19,19.5
05/30/2012,20,21,19,20.0
05/31/2012,20,21,19,21.0
06/01/2012,20,21,19,22.0
06/04/2012,20,21,19,23.0
06/11/2012,20,21,19,24.0
06/12/2012,20,21,19,25.0
"""
# 05/28/2012 = Memorial Day (NYSE geschlossen) → VIX-Zeile muss verworfen werden
# 06/02/2012 = Samstag (muss verworfen werden)
# Kalender 28.05.–12.06.2012 = 11 NYSE-Tage; VIX1Y fehlt u. a. 05.–08.06. (Lücken)
VIX1Y = """DATE,OPEN,HIGH,LOW,CLOSE
05/30/2012,25,25,25,25.0
05/31/2012,26,26,26,26.0
06/01/2012,27,27,27,27.0
06/02/2012,27,27,27,27.0
06/11/2012,28,28,28,28.0
06/12/2012,29,29,29,29.0
"""
PCR = """Disclaimer Zeile mit Put/Call Hinweis, keine Daten
,,,,
PRODUCT: EQUITY,,EXCHANGE: Cboe,
DATE,CALL,PUT,TOTAL,P/C Ratio
05/30/2012, 1000, 600, 1600, 0.60
05/31/2012, 1000, 700, 1700, 0.70
06/01/2012, 1000, 800, 1800, 0.80
06/11/2012, 1000, 650, 1650, 0.65
"""


def _write_snapshot(d: Path, files: dict[str, str]) -> None:
    d.mkdir(parents=True, exist_ok=True)
    lines = []
    for name, content in files.items():
        (d / name).write_text(content)
        lines.append(f"{hashlib.sha256(content.encode()).hexdigest()}  {name}")
    (d / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def test_parsers():
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "VIX_History.csv"
        p.write_text(VIX)
        s = parse_cboe_index(p)
        assert s.name == "VIX" and len(s) == 8 and s.iloc[-1] == 25.0
        q = Path(t) / "equitypc.csv"
        q.write_text(PCR)
        df = parse_cboe_pcr(q)
        assert list(df.columns) == ["calls", "puts", "total", "pcr"]
        assert len(df) == 4 and df["pcr"].iloc[0] == 0.60


def test_panel_no_ffill_and_calendar():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "2026-01-01"
        _write_snapshot(d, {"VIX_History.csv": VIX, "VIX1Y_History.csv": VIX1Y,
                            "equitypc.csv": PCR})
        panel, info = build_panel(d)
        assert len(panel) == 11                                  # NYSE-Tage 29.05.–12.06.
        assert pd.Timestamp("2012-05-28") not in panel.index     # Feiertag verworfen
        assert info["off_calendar"]["VIX"] == ["2012-05-28"]
        assert pd.Timestamp("2012-06-02") not in panel.index     # Samstag verworfen
        assert pd.isna(panel.loc["2012-06-05", "VIX"])           # echte Lücke bleibt NaN
        assert info["off_calendar"]["VIX1Y"] == ["2012-06-02"]
        assert pd.isna(panel.loc["2012-06-04", "VIX1Y"])         # kein Forward-Fill
        assert pd.isna(panel.loc["2012-06-04", "pcr_equity"])
        assert panel.loc["2012-05-31", "pcr_segment"] == "A_cleared_OCC"
        assert panel.loc["2012-06-01", "pcr_segment"] == "B_uebergang"
        assert panel.loc["2012-06-11", "pcr_segment"] == "C_preliminary_ohne_ETP"
        qc = quality_report(panel, info)
        assert qc["series"]["VIX"]["status"] == "WARN"           # Feiertagszeile + Lücken
        assert qc["series"]["VIX1Y"]["status"] == "WARN"         # Lücke + Samstag
        assert qc["pcr_ratio_check_mismatches"]["pcr_equity"] == 0


def test_nyse_calendar_special_closures():
    from datalayer import nyse_calendar
    cal = nyse_calendar("2012-10-26", "2012-11-01")
    assert pd.Timestamp("2012-10-29") not in cal and pd.Timestamp("2012-10-30") not in cal
    cal = nyse_calendar("2001-09-10", "2001-09-18")
    assert [d.strftime("%m-%d") for d in cal] == ["09-10", "09-17", "09-18"]
    cal = nyse_calendar("2007-10-08", "2007-10-08")               # Columbus Day: offen
    assert len(cal) == 1


def test_snapshot_tamper_detected():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "2026-01-01"
        _write_snapshot(d, {"VIX_History.csv": VIX})
        verify_snapshot(d)
        (d / "VIX_History.csv").write_text(VIX + "06/13/2012,1,1,1,1\n")
        try:
            verify_snapshot(d)
        except SnapshotError as e:
            assert "Hash abweichend" in str(e)
        else:
            raise AssertionError("Manipulation nicht erkannt")


def test_unregistered_file_detected():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "2026-01-01"
        _write_snapshot(d, {"VIX_History.csv": VIX})
        (d / "extra.csv").write_text("x")
        try:
            verify_snapshot(d)
        except SnapshotError as e:
            assert "nicht in SHA256SUMS.txt" in str(e)
        else:
            raise AssertionError("unregistrierte Datei nicht erkannt")


def test_missing_calendar_series():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t) / "2026-01-01"
        _write_snapshot(d, {"VIX1Y_History.csv": VIX1Y})
        try:
            build_panel(d)
        except ValueError as e:
            assert "Kalender-Reihe VIX fehlt" in str(e)
        else:
            raise AssertionError("fehlende Kalender-Reihe nicht erkannt")


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"OK  {fn.__name__}")
    print(f"\n{len(tests)} Tests bestanden")
