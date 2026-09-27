"""
datalayer – Phase 1 der Regime-Backtest-Roadmap (UIQ-Suite docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md)

Reproduzierbare, point-in-time-saubere Tagesdaten-Schicht:
  - Rohdaten-Snapshots mit SHA-256-Prüfung (data/raw/<quelle>/<datum>/SHA256SUMS.txt)
  - Parser für Cboe-Index-Historien und Cboe-Put/Call-Ratio-Dateien
  - NYSE-Handelskalender (Paket `holidays`), Zeitraum aus der VIX-Historie
  - Panel ohne Forward-Fill + Datenqualitätsbericht

Version: 1.1.0 (27.09.2026)
"""
from .snapshot import verify_snapshot, SnapshotError
from .cboe import parse_cboe_index, parse_cboe_pcr, detect_file_kind
from .panel import build_panel, quality_report, nyse_calendar, PCR_SEGMENTS

__all__ = [
    "verify_snapshot", "SnapshotError",
    "parse_cboe_index", "parse_cboe_pcr", "detect_file_kind",
    "build_panel", "quality_report", "nyse_calendar", "PCR_SEGMENTS",
]
__version__ = "1.1.0"
