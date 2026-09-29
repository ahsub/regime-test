# Literatur-Reviews — Regime- und Market-State-Analytik

Paraphrasierende Reviews mit Bezug zu `regime-test` und UIQ. Keine Buchtexte im Repo.

| Datum | Review | Kernbeitrag |
|---|---|---|
| 28.09.2026 | [Alexander, *Market Models* (2001)](LITERATUR-REVIEW-ALEXANDER-MARKET-MODELS-2026-09-28.md) | Fensterartefakte gleichgewichteter Schätzer; Prognosebewertung hängt an Verlustfunktion und Zeitraum; Derman-Regime (Kurs-Vol-Kopplung); PCA der Vol-Laufzeitstruktur; Befund D13 (DCE-„EVT-VaR“) |
| 28.09.2026 | [Alexander, *Market Risk Analysis* I+II (2008)](LITERATUR-REVIEW-ALEXANDER-MARKET-RISK-ANALYSIS-I-II-2026-09-28.md) | Markov-Switching (Schätzung, Regime-Anzahl nur mit simulierten kritischen Werten); Quantilregression für Kurs-Vol-Randabhängigkeit; II.8 Prognose-/Backtest-Methodik (Mincer-Zarnowitz, Diebold-Mariano, Christoffersen); Einheitswurzel-Grenzfälle bei Vol-Indizes; Sharpe-Korrektur bei Autokorrelation |
| 28.09.2026 | [Alexander, *Market Risk Analysis* III+IV (2008)](LITERATUR-REVIEW-ALEXANDER-MARKET-RISK-ANALYSIS-III-IV-2026-09-28.md) | Derman-Regime operational (Korrelation ATM-Vol ↔ Basiswert ≈ 0 / negativ / stark negativ); Laufzeitstruktur von Vol-Indizes als Regimeanzeiger; Varianz-Risikoprämie mit Crash-Asymmetrie; gefilterte historische Simulation und Präzision extremer Quantile (Lösungsweg D13); Stresstests ohne Wahrscheinlichkeit |

## Offene Konsequenzen (K1–K18, Stand 28.09.2026)

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
| K13 | Fix-Weg D13: gefilterte historische Simulation (mehrjährig, EWMA/GARCH-bereinigt) + Expected Tail Loss, oder ehrliche Umbenennung | mit UIQ Batch 1b entscheiden |
| K14 | H7 operational nach Derman: Korrelation VIX-Änderung ↔ SPX-Rendite, Klassen ≈ 0 / negativ / stark negativ, Schwellen out-of-sample | Kandidat, nach Phase 4 |
| K15 | H8 um Kurvenform (steigend / flach / invertiert) ergänzen | Kandidat, nach Phase 4 |
| K16 | UIQ-Optionstexte: Prämienaussagen stets mit asymmetrischem Verlustprofil | offen, UIQ Batch 3 |
| K17 | Backtests: Spot-VIX nie als handelbar werten | offen, Phase-4-Präregistrierung |
| K18 | Szenario-/Event-Aussagen nur hypothetisch, ohne Wahrscheinlichkeit/Obergrenze | bei Wiederaufnahme Event & Surprise Gate |

## Weitere Kandidaten aus externem Review (29.09.2026)

Nicht präregistriert, kein Code. Präregistrierung und Umsetzung erst nach Phase 4, analog H5/H6.
Bereits abgedeckt und daher **nicht** aufgenommen: VVIX/SKEW (im Panel), Zinskurve (H4), implizite Korrelation (H3), PCR (H2); NFCI bewusst ausgeschlossen (H4: Point-in-Time erst ab 06/2011, starke Revisionen).

| # | Kandidat | Vorbedingung / methodischer Vorbehalt |
|---|---|---|
| H9 | HY-OAS (`BAMLH0A0HYM2`) als Kredit-Achse | vorab prüfen: ALFRED-Vintages vorhanden? (BAA10Y scheiterte in H4 genau daran); ICE-Lizenz/Historienumfang auf FRED |
| H10 | Change-Point-Detection (z. B. PELT) als Methodenalternative zum HMM | Hypothese „stabiler als HMM“, **nicht** „schneller“: PELT braucht nach einem Bruch ≥ `min_size` Beobachtungen, kurze Schocks (z. B. Aug. 2024) sind damit strukturell nicht früher erkennbar; nur rollierend ohne Look-ahead |
| H11 | Hurst-Exponent (Trend vs. Mean-Reversion) auf Renditen | R/S bei 126–252 Tagen aufwärtsverzerrt → Bias-Korrektur (Anis-Lloyd) und Konfidenzband; Schätzstreuung liegt in der Größenordnung der Schwellen 0,45/0,55 |

Nur Forschung, nicht UIQ Public: Vol-Targeting / volatilitätsgesteuerte Positionsgröße (Positionsgrößen sind im Public-Pfad ausgeschlossen, UIQ ADR-1).
