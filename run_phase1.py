"""
run_phase1.py – Phase 1 (Datenschicht) der Regime-Backtest-Roadmap ausführen.

Aufruf (im Ordner regime-test):
    python run_phase1.py                       # alle Snapshots unter data/raw/cboe/
    python run_phase1.py data/raw/cboe/2026-09-27

Ergebnis: data/processed/phase1_<jüngster Snapshot>/
    panel.csv        Tages-Panel (Kalender = Cboe-VIX-Handelstage, kein Forward-Fill)
    qc_report.md     Datenqualitätsbericht (lesbar)
    qc_report.json   derselbe Bericht maschinenlesbar
Exit-Code 1, wenn ein Snapshot ungültig ist oder der Bericht ERROR meldet.

Version: 1.0.0 (27.09.2026)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from datalayer import SnapshotError, build_panel, quality_report  # noqa: E402
from datalayer.panel import write_outputs  # noqa: E402


def main(argv: list[str]) -> int:
    if argv:
        dirs = [Path(a) for a in argv]
    else:
        base = ROOT / "data" / "raw" / "cboe"
        dirs = sorted(p for p in base.iterdir() if p.is_dir())
    if not dirs:
        print("Keine Snapshot-Ordner gefunden (data/raw/cboe/<datum>/).")
        return 1
    print("Snapshots:", ", ".join(d.name for d in dirs))
    try:
        panel, info = build_panel(dirs)
    except SnapshotError as e:
        print(f"\nABBRUCH – {e}")
        return 1
    except ValueError as e:
        print(f"\nABBRUCH – {e}")
        return 1
    qc = quality_report(panel, info)
    out_dir = ROOT / "data" / "processed" / f"phase1_{dirs[-1].name}"
    paths = write_outputs(panel, qc, out_dir)
    print(f"\nKalender: {qc['calendar']['calendar_start']} – "
          f"{qc['calendar']['calendar_end']} ({qc['calendar']['calendar_days']} Handelstage)")
    for k, e in qc["series"].items():
        if "start" in e:
            print(f"  {e['status']:5s} {k:22s} {e['start']} – {e['end']}  "
                  f"Lücken {e['missing_in_range']}, verworfen {e['off_calendar_dropped']}")
        else:
            print(f"  {e['status']:5s} {k:22s} {e.get('reason')}")
    print(f"\nGesamtstatus: {qc['status']}")
    print(f"Bericht: {Path(paths['qc_md']).relative_to(ROOT)}")
    print(f"Panel:   {Path(paths['panel']).relative_to(ROOT)}")
    return 1 if qc["status"] == "ERROR" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
