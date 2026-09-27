"""
Rohdaten-Snapshots: jeder Backtest referenziert einen unveränderlichen Ordner
data/raw/<quelle>/<datum>/ mit SHA256SUMS.txt (Format wie `shasum -a 256 *`).

Version: 1.0.0 (27.09.2026)
"""
from __future__ import annotations

import hashlib
from pathlib import Path


class SnapshotError(RuntimeError):
    """Snapshot unvollständig oder verändert – Backtest darf nicht laufen."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sums(sums_file: Path) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in sums_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, name = line.split(maxsplit=1)
        sums[name.lstrip("*")] = digest.lower()
    return sums


def verify_snapshot(snapshot_dir: str | Path) -> dict[str, str]:
    """Prüft alle Dateien gegen SHA256SUMS.txt.

    Liefert {dateiname: sha256}. Wirft SnapshotError bei fehlender Prüfsummen-
    datei, fehlender Datei, abweichendem Hash oder nicht registrierter Datei.
    """
    d = Path(snapshot_dir)
    sums_file = d / "SHA256SUMS.txt"
    if not sums_file.exists():
        raise SnapshotError(f"{sums_file} fehlt – Snapshot nicht registriert")
    sums = read_sums(sums_file)
    problems = []
    for name, expected in sums.items():
        f = d / name
        if not f.exists():
            problems.append(f"fehlt: {name}")
        elif sha256_file(f) != expected:
            problems.append(f"Hash abweichend (Datei verändert): {name}")
    unregistered = sorted(
        p.name for p in d.iterdir()
        if p.is_file() and p.name != "SHA256SUMS.txt" and not p.name.startswith(".")
        and p.name not in sums
    )
    for name in unregistered:
        problems.append(f"nicht in SHA256SUMS.txt: {name}")
    if problems:
        raise SnapshotError("Snapshot ungültig:\n  " + "\n  ".join(problems))
    return sums
