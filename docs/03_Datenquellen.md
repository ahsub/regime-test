
### `docs/03_Datenquellen.md`

```markdown
# 3. Datenquellen

## Übersicht

| Daten | Quelle | Zeitraum |
| :--- | :--- | :--- |
| S&P 500 | Yahoo Finance | 1990–2026 |
| VIX | CBOE | 1990–2026 |
| VVIX | CBOE | 2006–2026 |
| DIX/GEX | SqueezeMetrics | 2011–2026 |

## CBOE-Daten
https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv

## SqueezeMetrics-Daten
https://squeezemetrics.com/monitor/static/DIX.csv


## Cboe Put/Call-Ratio (ergänzt 28.09.2026)

| Abschnitt | Quelle | Zeitraum | Abgrenzung |
| :--- | :--- | :--- | :--- |
| CSV (eingefroren) | https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/ `totalpc.csv`, `equitypc.csv`, `indexpc.csv` | 01.11.2006 – 04.10.2019 | nur Cboe-Börse; bis 31.05.2012 cleared (OCC), ab 11.06.2012 Equity ohne ETPs |
| Daily Market Statistics | https://www.cboe.com/us/options/market_statistics/daily/?dt=YYYY-MM-DD | ab 07.10.2019 | wie CSV ab 11.06.2012 (Equity ohne ETPs, Summe = Index + ETP + Equity) |

- Laden: `python scripts/fetch_cboe_pcr_daily.py` → Snapshot `data/raw/cboe/<datum>_pcr_daily/` (Cboe-CSV-Format + `fetch_report.json` mit SHA-256 jeder Rohseite). Rohseiten-Cache lokal in `data/raw/_cache/` (nicht im Git); `--offline` parst den Cache neu ohne Download.
- Panel: Spalten `pcr_<x>_daily` getrennt, `pcr_total_full` / `pcr_equity_full` / `pcr_index_full` = CSV bis 04.10.2019, danach Daily. Keine Überlappung beider Quellen (Seite liefert für 04.10.2019 „No data“) – Nahtstelle wird im QC-Bericht nur statistisch ausgewiesen (Mittel/σ je 60 Handelstage).
- Nicht verwendet: `TheSnoozer/putcallratio` (Intraday-Stände bis 15:15 CT, andere Equity-Abgrenzung; 01.04.2024 Equity 0,77 vs. Cboe final 0,65).
