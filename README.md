# Market Regime Analysis Tool

**Status:** 🔎 In Überprüfung – Regime-Backtest-Roadmap (UIQ-Suite `docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md`)
**Kernaussage (Stand 27.09.2026):** `classify_regime_v2()` liefert **Drawdown-Schutz**, aber **keinen belastbaren Sharpe-Vorteil** gegenüber Buy & Hold.
**Letzte Aktualisierung:** 2026-09-27

---

## 📊 Kern-Ergebnisse (Stand 2026-09-27, Phase 2 der Roadmap)

Reproduzierbar mit `python run_phase2_baseline.py` → `results/phase2/baseline_2026-09-27.md`.
Rechnung: Position t-1 × S&P-500-Rendite t, rf 2 % p. a., **ohne Transaktionskosten**.
Buy & Hold (B&H) jeweils im **selben** Zeitfenster.

| Zeitfenster | Sharpe Strategie | Sharpe B&H | Max. DD Strategie | Max. DD B&H | Trades |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 20.10.2011 – 27.08.2026 (bisheriges Fenster) | 0.75 | 0.71 | -20.3% | -33.9% | 261 |
| 03.01.2011 – 28.08.2026 (inkl. US-Downgrade 2011) | 0.66 | 0.65 | -20.3% | -33.9% | 285 |
| 18.09.2009 – 25.09.2026 (ohne GEX, ab VIX3M-Beginn) | 0.62 | 0.65 | -23.8% | -33.9% | 265 |

**Stressphasen (Periodenrendite Strategie / B&H):** Covid 2020 −7,1 % / −33,6 % · 2018 Q4 −12,6 % / −19,3 % ·
2022 −19,8 % / −24,9 % – aber **kein Schutz** bei schnellen Schocks: 2011 −19,5 % / −18,2 %,
Aug. 2015 −10,2 % / −8,2 %, Aug. 2024 −7,9 % / −7,7 %.

**Befunde der Überprüfung (27.09.2026):**
- Die bisherigen Zahlen sind **exakt reproduziert** (Sharpe 0,753 · Rendite 403,18 % · DD −20,29 % · 261 Trades).
- Das bisherige Fenster begann wegen der HMM-Anlaufzeit erst am **20.10.2011** (nicht 2011-01), also nach dem Einbruch vom August 2011.
- Der GEX-Filter bringt ca. +0,02 Sharpe und schützt v. a. 2022 (DD −20 % statt −24 %).
- `data/market_data.csv` ist vor Datenbeginn **rückwärts aufgefüllt** (VIX3M bis 2009-09, DIX/GEX bis 2011-05) und enthält 33 NYSE-Feiertagszeilen. Auf die bisherigen Ergebnisse ohne Einfluss (Schnittmenge mit Yahoo-Handelstagen; aufgefülltes GEX > 0 wirkt wie „kein GEX“), für neue Arbeiten aber **nicht mehr verwenden** → stattdessen `src/datalayer` (Phase 1).
- `PUT_History.csv` ist der **Cboe PutWrite-Index**, keine Put/Call-Ratio. Er wurde nur in der verworfenen Framework-Integration als Feature genutzt.
- Die bisher genannte **DSR 1,00** misst gegen die Streuung der eigenen Kandidaten-Sharpes, nicht gegen B&H. Sie ist **kein Beleg für Überlegenheit** gegenüber B&H; neue Signifikanzprüfung in Phase 4.

---

## 📜 Historische Ergebnisse (Stand 2026-09-02, Kontext siehe oben)

| Kennzahl | classify_regime_v2() | 3-Stufen-Ensemble |
| :--- | :---: | :---: |
| Sharpe Ratio | 0.75 | 0.60 |
| Gesamtrendite | 403.18% | 220.79% |
| Max. Drawdown | -20.29% | -16.32% |
| Anzahl Trades | 261 | 163 |

Zeitfenster beider Zeilen: 20.10.2011 – 27.08.2026 (B&H dort: Sharpe 0,71, DD −33,9 %).
Die frühere Empfehlung „70 % classify_regime_v2() + 30 % Ensemble“ ist **ausgesetzt**, bis die Roadmap-Phasen 3–4
(Hypothesentests, Walk-Forward, Transaktionskosten) abgeschlossen sind.

---

## 🔬 Modell-Evaluierung (2026-09-02)

### Framework-Integration (market_regime_detection)

Im Rahmen der Evaluierung wurde das Repository **market_regime_detection** (k3tikvats) als mögliche Erweiterung untersucht.

| Modell | AIC | BIC | Zeilen | Ergebnis |
| :--- | :---: | :---: | :---: | :--- |
| **Original (nur VIX)** | **-9.936,59** | **-9.861,17** | 3.965 | ✅ **Besser** |
| Erweitert (mit Framework-Features) | -8.468,74 | -8.268,37 | 3.203 | ❌ Schlechter |

**Fazit:** Die Framework-Features führen zu einem **Datenverlust von 19,2%** und verschlechtern die Modellgüte signifikant. Die Integration wird **nicht empfohlen**.

> **Korrektur (29.09.2026):** AIC/BIC sind nur auf identischer Stichprobe vergleichbar. Beide Modelle liefen auf unterschiedlich vielen Zeilen (3.965 vs. 3.203), der Vergleich ist daher **nicht aussagekräftig** – weder für noch gegen die Framework-Features. Die Nicht-Empfehlung bleibt aus den übrigen Gründen bestehen (Datenverlust, Phase-3-Befunde). Vgl. `docs/literatur/README.md` (K10).

---

## 🧭 Roadmap-Stand

| Phase | Inhalt | Status |
| :--- | :--- | :---: |
| 0 | Datenverfügbarkeit | ✅ 27.09.2026 |
| 1 | Datenschicht (`src/datalayer`, `run_phase1.py`) | ✅ 27.09.2026 |
| 2 | Baseline reproduzieren (`run_phase2_baseline.py`) | ✅ 27.09.2026 |
| 3 | Hypothesentests H1–H5 – Zielgröße: Drawdown-/Tail-Schutz ggü. B&H | ⏭ |
| 4 | Validierung (Walk-Forward, Kosten, DSR) | offen |

---

## 📁 Projektstruktur

| Pfad | Inhalt |
| :--- | :--- |
| `data/raw/<quelle>/<datum>/` | Rohdaten-Snapshots mit `SHA256SUMS.txt` (Cboe, Yahoo, SqueezeMetrics) – nie überschreiben |
| `src/datalayer/` | Parser, Snapshot-Prüfung, NYSE-Kalender, Panel ohne Forward-Fill, QC-Bericht |
| `run_phase1.py` | Datenschicht ausführen → `data/processed/` (nicht versioniert) |
| `run_phase2_baseline.py` | Baseline-Varianten A0–E → `results/phase2/` |
| `tests/test_datalayer.py` | Tests (`python tests/test_datalayer.py`) |
| `compare_approaches_final_v2.py` | ursprüngliche Vergleichslogik (`classify_regime_v2()` unverändert hier definiert) |
| `docs/` | Auswertungen, u. a. `08_STRATEGY_COMPARISON.md` |
| übrige `*.py` im Hauptordner | frühere Explorationsskripte (Stand bis 02.09.2026) |
