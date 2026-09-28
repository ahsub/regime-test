"""
Parser für die Cboe-Seite „Daily Market Statistics“ (ein Handelstag je Abruf).

Quelle:  https://www.cboe.com/us/options/market_statistics/daily/?dt=YYYY-MM-DD
Abdeckung (geprüft 28.09.2026): erster Tag mit Daten 07.10.2019 – also der
Handelstag direkt nach dem Ende der eingefrorenen Cboe-CSV-Dateien
(totalpc/equitypc/indexpc, letzter Tag 04.10.2019). Eine Überlappung beider
Quellen gibt es NICHT; für Tage ohne Daten (Wochenende, Feiertag, vor 07.10.2019)
liefert die Seite „No data available for the selected date.“ – keinen
stillen Rückfall auf den aktuellen Tag.

Abgrenzung wie in den CSV-Dateien ab 11.06.2012: Equity OHNE ETPs;
„Sum of All Products“ = Index + ETP + Equity (wird je Tag geprüft).
Es wird nur die Cboe-Options-Börse abgebildet, nicht der Gesamtmarkt (OCC).

Die Seite trägt kein Datum im Inhalt; das Datum ist ausschließlich der
Abrufparameter `dt`. Deshalb wird jede geladene Seite roh (mit SHA-256)
zwischengespeichert, damit der Parser jederzeit ohne neuen Download
wiederholt werden kann (Belegkette).

Parsing bewusst textbasiert (sichtbarer Text, Skripte/Styles entfernt),
damit kleine Markup-Änderungen nicht zu Fehlzuordnungen führen. Jede
Fehlzuordnung fällt über die Summenprüfung auf.

Version: 1.0.0 (28.09.2026)
Changelog:
  1.0.0 (28.09.2026) – Erstfassung: Parser, Plausibilitätsprüfungen,
                       Export im Cboe-CSV-Format (lesbar mit parse_cboe_pcr).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DAILY_URL = "https://www.cboe.com/us/options/market_statistics/daily/?dt={date}"
FIRST_DAILY_DATE = "2019-10-07"   # geprüft 28.09.2026 (04.10.2019: keine Daten)

NO_DATA_MARKER = "no data available for the selected date"

# Schlüssel → (Seitenüberschrift, Ausgabedatei, PRODUCT-Label im CSV-Kopf)
PRODUCTS = {
    "total":  ("SUM OF ALL PRODUCTS",          "totalpc_daily.csv",  "TOTAL"),
    "index":  ("INDEX OPTIONS",                "indexpc_daily.csv",  "INDEX"),
    "etp":    ("EXCHANGE TRADED PRODUCTS",     "etppc_daily.csv",    "EXCHANGE TRADED PRODUCTS"),
    "equity": ("EQUITY OPTIONS",               "equitypc_daily.csv", "EQUITY"),
    "vix":    ("CBOE VOLATILITY INDEX (VIX)",  "vixpc_daily.csv",    "VIX"),
    "spx":    ("SPX + SPXW",                   "spxpc_daily.csv",    "SPX + SPXW"),
}
REQUIRED = ("total", "index", "etp", "equity")

# Schlüssel → Beschriftung der Zeile in der Tabelle „Ratios“
RATIO_LABELS = {
    "total":  "TOTAL PUT/CALL RATIO",
    "index":  "INDEX PUT/CALL RATIO",
    "etp":    "EXCHANGE TRADED PRODUCTS PUT/CALL RATIO",
    "equity": "EQUITY PUT/CALL RATIO",
    "vix":    "CBOE VOLATILITY INDEX (VIX) PUT/CALL RATIO",
    "spx":    "SPX + SPXW PUT/CALL RATIO",
}

RATIO_TOL = 0.011   # wie panel.py: Rundung der Cboe-Ratio auf 2 Stellen


class DailyParseError(ValueError):
    """Seite enthält Daten, aber nicht in der erwarteten Struktur."""


@dataclass
class DailyStats:
    volumes: dict[str, tuple[int, int, int]]          # key → (calls, puts, total)
    ratios: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def pcr(self, key: str) -> tuple[float, str]:
        """Cboe-Ratio der Seite, sonst puts/calls gerundet – mit Herkunft."""
        if key in self.ratios:
            return self.ratios[key], "seite"
        c, p, _ = self.volumes[key]
        return (round(p / c, 2) if c else float("nan")), "berechnet"


def visible_text(html: str) -> str:
    """Sichtbarer Text der Seite, Leerraum normalisiert."""
    from lxml import html as lh
    doc = lh.fromstring(html)
    for bad in doc.xpath("//script|//style|//noscript|//template"):
        bad.drop_tree()
    # Zellen/Blöcke durch Leerzeichen trennen, damit Zahlen nicht verkleben
    for el in doc.iter():
        if el.tail is None:
            el.tail = " "
        else:
            el.tail = " " + el.tail
    return re.sub(r"\s+", " ", doc.text_content()).strip()


def _num(s: str) -> int:
    return int(s.replace(",", ""))


_STOP = "|".join(re.escape(v[0]) for v in PRODUCTS.values()) + r"|PUT/CALL RATIO"


def _volume_pattern(label: str) -> re.Pattern:
    # Überschrift, dann die Zeile VOLUME mit 3 Zahlen. Dazwischen weder Ziffern
    # noch eine andere Produkt-Überschrift: sonst würde ein gleichlautender
    # Menüpunkt (z. B. „Index Options“ in der Navigation) bis in die nächste
    # Tabelle („Sum of All Products“) weiterlaufen – Befund aus dem Test.
    return re.compile(
        re.escape(label) + r"(?:(?!" + _STOP + r")[^\d]){0,160}?\bVOLUME\b[^\d]{0,40}?"
        r"(\d[\d,]*)[^\d]{1,40}?(\d[\d,]*)[^\d]{1,40}?(\d[\d,]*)",
        re.IGNORECASE)


def _ratio_pattern(label: str) -> re.Pattern:
    return re.compile(re.escape(label) + r"[^\d]{0,20}?(\d+(?:\.\d+)?)", re.IGNORECASE)


def parse_daily_text(text: str) -> DailyStats | None:
    """Sichtbarer Seitentext → DailyStats; None = Seite meldet „keine Daten“."""
    if NO_DATA_MARKER in text.lower():
        return None
    volumes: dict[str, tuple[int, int, int]] = {}
    for key, (label, _, _) in PRODUCTS.items():
        hits = {tuple(_num(g) for g in m.groups())
                for m in _volume_pattern(label).finditer(text)}
        if len(hits) > 1:
            raise DailyParseError(f"{label}: mehrdeutige Volumen-Treffer {sorted(hits)}")
        if hits:
            volumes[key] = hits.pop()
    missing = [k for k in REQUIRED if k not in volumes]
    if missing:
        raise DailyParseError(
            "Pflicht-Tabellen nicht gefunden: " + ", ".join(PRODUCTS[k][0] for k in missing))

    ratios: dict[str, float] = {}
    for key, label in RATIO_LABELS.items():
        hits = {float(m.group(1)) for m in _ratio_pattern(label).finditer(text)}
        if len(hits) == 1:
            ratios[key] = hits.pop()
        elif len(hits) > 1:
            raise DailyParseError(f"{label}: mehrdeutige Werte {sorted(hits)}")

    st = DailyStats(volumes=volumes, ratios=ratios)
    check_stats(st)
    return st


def parse_daily_html(html: str) -> DailyStats | None:
    return parse_daily_text(visible_text(html))


def check_stats(st: DailyStats) -> None:
    """Harte Fehler → DailyParseError; weiche Befunde → st.warnings."""
    for key, (c, p, t) in st.volumes.items():
        if c + p != t:
            raise DailyParseError(f"{key}: Calls + Puts ({c}+{p}) ≠ Total ({t})")
    seen: dict[tuple, str] = {}
    for key, v in st.volumes.items():
        if v in seen:
            # typisches Symptom einer Fehlzuordnung (z. B. Menüpunkt statt Tabelle)
            raise DailyParseError(f"{key} und {seen[v]} haben identische Volumina {v}")
        seen[v] = key
    s = st.volumes["total"]
    parts = [st.volumes[k] for k in ("index", "etp", "equity")]
    for i, name in enumerate(("Calls", "Puts")):
        summe = sum(x[i] for x in parts)
        if summe != s[i]:
            # Harter Fehler: an den Stichtagen 07.10.2019 und 01.04.2024 exakt erfüllt.
            # Schlägt das künftig flächig fehl (neues Produkt?), Parser anpassen –
            # die Rohseiten liegen im Cache, erneutes Parsen braucht keinen Download.
            raise DailyParseError(
                f"Summe {name}: Index+ETP+Equity = {summe} ≠ Sum of All Products {s[i]}")
    for key, r in st.ratios.items():
        if key not in st.volumes:
            continue
        c, p, _ = st.volumes[key]
        if c and abs(p / c - r) > RATIO_TOL:
            raise DailyParseError(
                f"{key}: Ratio der Seite {r} passt nicht zu Puts/Calls {p / c:.3f}")
    for key in ("total", "index", "equity"):
        if key not in st.ratios:
            st.warnings.append(f"{key}: keine Ratio auf der Seite – aus Volumen berechnet")


def to_frame(days: dict[pd.Timestamp, DailyStats], key: str) -> pd.DataFrame:
    rows = []
    for d in sorted(days):
        st = days[d]
        if key not in st.volumes:
            continue
        c, p, t = st.volumes[key]
        rows.append((d, c, p, t, st.pcr(key)[0]))
    df = pd.DataFrame(rows, columns=["date", "calls", "puts", "total", "pcr"])
    return df.set_index("date")


def write_cboe_csv(df: pd.DataFrame, key: str, path: str | Path, fetched: str) -> None:
    """Schreibt im Format der Cboe-CSV-Dateien (lesbar mit parse_cboe_pcr)."""
    label = PRODUCTS[key][2]
    lines = [
        # Kopf enthält „Put/Call“ → detect_file_kind erkennt 'pcr'
        "Cboe Volume and Put/Call Ratio data – rekonstruiert aus Cboe Daily Market "
        f"Statistics ({DAILY_URL.format(date='YYYY-MM-DD')}); abgerufen {fetched}; "
        "Equity ohne ETPs; nur Cboe Options Exchange; Werte unverändert übernommen.,,,,",
        f", PRODUCT: {label},,EXCHANGE: Cboe,",
        "DATE,CALL,PUT,TOTAL,P/C Ratio",
    ]
    for d, r in df.iterrows():
        lines.append(f"{d:%m/%d/%Y}, {int(r.calls)}, {int(r.puts)}, {int(r.total)}, "
                     f"{r.pcr:.2f}")
    Path(path).write_text("\n".join(lines) + "\n")
