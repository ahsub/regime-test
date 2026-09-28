# Literatur-Reviews — Regime- und Market-State-Analytik

Paraphrasierende Reviews mit Bezug zu `regime-test` und UIQ. Keine Buchtexte im Repo.

| Datum | Review | Kernbeitrag |
|---|---|---|
| 28.09.2026 | [Alexander, *Market Models* (2001)](LITERATUR-REVIEW-ALEXANDER-MARKET-MODELS-2026-09-28.md) | Fensterartefakte gleichgewichteter Schätzer; Prognosebewertung hängt an Verlustfunktion und Zeitraum; Derman-Regime (Kurs-Vol-Kopplung); PCA der Vol-Laufzeitstruktur; Befund D13 (DCE-„EVT-VaR“) |
| 28.09.2026 | [Alexander, *Market Risk Analysis* I+II (2008)](LITERATUR-REVIEW-ALEXANDER-MARKET-RISK-ANALYSIS-I-II-2026-09-28.md) | Markov-Switching (Schätzung, Regime-Anzahl nur mit simulierten kritischen Werten); Quantilregression für Kurs-Vol-Randabhängigkeit; II.8 Prognose-/Backtest-Methodik (Mincer-Zarnowitz, Diebold-Mariano, Christoffersen); Einheitswurzel-Grenzfälle bei Vol-Indizes; Sharpe-Korrektur bei Autokorrelation |

## Offene Konsequenzen (K1–K12, Stand 28.09.2026)

| # | Inhalt | Status |
|---|---|---|
| K1 | DCE-„EVT-VaR“ = empirisches 1-%-Quantil von 60 Renditen | erledigt (UIQ-Befundregister D13) |
| K2 | Fensterartefakte als Invariante im Snapshot-Prüfer (№72) | offen, `uiq-devtools` |
| K3 + K7 | Phase-4-Präregistrierung: Verlustfunktion, Tests, Fenster, Stressphasen, Modellklassen | offen, **vor erstem Phase-4-Code** |
| K4 + K9 | H7 Kurs-Vol-Kopplung als zweite Regime-Achse, gemessen per Quantilregression | Kandidat, nach Phase 4 |
| K5 | H8 PCA der Cboe-VIX-Kurve | Kandidat, nach Phase 4 |
| K6 | Alexander als Methodenquelle ins UIQ-Literaturverzeichnis | offen |
| K8 | Einheitswurzeltests VIX-Niveaus vs. -Verhältnisse | offen, vor Phase 4 |
| K10 | Regime-Anzahl nicht nur per AIC/BIC; mehrere Startwerte | offen, künftige HMM-Vergleiche |
| K11 | Öffentlicher VaR nur mit Christoffersen-Test | offen, UIQ Batch 1b / ADR-1 |
| K12 | Sharpe-Autokorrelationskorrektur für SUITE №70(b) | offen |
