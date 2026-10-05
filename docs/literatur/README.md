# Literatur-Reviews — Regime- und Market-State-Analytik

Paraphrasierende Reviews mit Bezug zu `regime-test` und UIQ. Keine Buchtexte im Repo.

| Datum | Review | Kernbeitrag |
|---|---|---|
| 28.09.2026 | [Alexander, *Market Models* (2001)](LITERATUR-REVIEW-ALEXANDER-MARKET-MODELS-2026-09-28.md) | Fensterartefakte gleichgewichteter Schätzer; Prognosebewertung hängt an Verlustfunktion und Zeitraum; Derman-Regime (Kurs-Vol-Kopplung); PCA der Vol-Laufzeitstruktur; Befund D13 (DCE-„EVT-VaR“) |
| 28.09.2026 | [Alexander, *Market Risk Analysis* I+II (2008)](LITERATUR-REVIEW-ALEXANDER-MARKET-RISK-ANALYSIS-I-II-2026-09-28.md) | Markov-Switching (Schätzung, Regime-Anzahl nur mit simulierten kritischen Werten); Quantilregression für Kurs-Vol-Randabhängigkeit; II.8 Prognose-/Backtest-Methodik (Mincer-Zarnowitz, Diebold-Mariano, Christoffersen); Einheitswurzel-Grenzfälle bei Vol-Indizes; Sharpe-Korrektur bei Autokorrelation |
| 28.09.2026 | [Alexander, *Market Risk Analysis* III+IV (2008)](LITERATUR-REVIEW-ALEXANDER-MARKET-RISK-ANALYSIS-III-IV-2026-09-28.md) | Derman-Regime operational (Korrelation ATM-Vol ↔ Basiswert ≈ 0 / negativ / stark negativ); Laufzeitstruktur von Vol-Indizes als Regimeanzeiger; Varianz-Risikoprämie mit Crash-Asymmetrie; gefilterte historische Simulation und Präzision extremer Quantile (Lösungsweg D13); Stresstests ohne Wahrscheinlichkeit |
| 05.10.2026 | [Marketstate-Review: Harvey et al., Nystrup et al., Guidolin/Timmermann, Kritzman et al., Hamilton, Hamilton/Susmel, Ang/Timmermann, Ang, López de Prado (AFML, MLAM, CFI)](LITERATUR-REVIEW-MARKETSTATE-2026-10-05.md) | Volatilitätsskalierung (Tail/Vol-of-Vol statt Sharpe); spurious Persistenz in GARCH vs. Regime-Persistenz; Student-t; Zustandszahl-Tests nicht standardverteilt; Filter vs. Glättung (Look-ahead); Echtzeit-Fehlalarme; Purging/Embargo bei überlappenden Prognosehorizonten; Deflated Sharpe und Versuchszählung; Kausalität/Collider bei Kontrollvariablen |

## Offene Konsequenzen (K1–K21, Stand 05.10.2026)

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
| K19 | Purging und Embargo bei überlappenden Prognosehorizonten (Leakage über Labels; AFML Kap. 7) – Ergänzung zu K3 + K7 | offen, Phase-4-Präregistrierung, **vor erstem Phase-4-Code** |
| K20 | Nur gefilterte Regimewahrscheinlichkeiten in Backtests, keine geglätteten (Kim-Algorithmus nutzt spätere Daten; Hamilton Kap. 22) | offen, Phase-4-Präregistrierung; gilt auch für H10 und künftige HMM-Läufe |
| K21 | Zustandszahl vorab festlegen und begründen, nicht per Likelihood-Ratio-Test wählen (Tests nicht standardverteilt; Hamilton, Ang/Timmermann) – Ergänzung zu K10 | offen, künftige HMM-Vergleiche |

## Weitere Kandidaten aus externem Review (29.09.2026)

Nicht präregistriert, kein Code. Präregistrierung und Umsetzung erst nach Phase 4, analog H5/H6.
Bereits abgedeckt und daher **nicht** aufgenommen: VVIX/SKEW (im Panel), Zinskurve (H4), implizite Korrelation (H3), PCR (H2); NFCI bewusst ausgeschlossen (H4: Point-in-Time erst ab 06/2011, starke Revisionen).

| # | Kandidat | Vorbedingung / methodischer Vorbehalt |
|---|---|---|
| H9 | HY-OAS (`BAMLH0A0HYM2`) als Kredit-Achse | vorab prüfen: ALFRED-Vintages vorhanden? (BAA10Y scheiterte in H4 genau daran); ICE-Lizenz/Historienumfang auf FRED |
| H10 | Change-Point-Detection (z. B. PELT) als Methodenalternative zum HMM | Hypothese „stabiler als HMM“, **nicht** „schneller“: PELT braucht nach einem Bruch ≥ `min_size` Beobachtungen, kurze Schocks (z. B. Aug. 2024) sind damit strukturell nicht früher erkennbar; nur rollierend ohne Look-ahead |
| H11 | Hurst-Exponent (Trend vs. Mean-Reversion) auf Renditen | R/S bei 126–252 Tagen aufwärtsverzerrt → Bias-Korrektur (Anis-Lloyd) und Konfidenzband; Schätzstreuung liegt in der Größenordnung der Schwellen 0,45/0,55 |

Nur Forschung, nicht UIQ Public: Vol-Targeting / volatilitätsgesteuerte Positionsgröße (Positionsgrößen sind im Public-Pfad ausgeschlossen, UIQ ADR-1).

## Kandidaten aus zweitem externem Review (29.09.2026, nachmittags)

Gleicher Status: nicht präregistriert, kein Code, frühestens nach Phase 4. Jeder Kandidat muss die Phase-4-H0 schlagen (inkrementeller Prognosewert **über den eingefrorenen VIX-Benchmark hinaus**); n_trials unverändert 42.
H12 = Marktbreite-Divergenz (Forschungsnotiz in UIQ-Suite `docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md`, ursprünglich als H6 notiert, umbenannt wegen Kollision mit H6 TIP-Canary).

| # | Kandidat | Vorbedingung / methodischer Vorbehalt |
|---|---|---|
| H13 | Amihud-Illiquidität **aus Tagesdaten** (\|r\| / Dollar-Volumen, SPY) | Steigt mechanisch mit \|r\| → misst großteils realisierte Vola; Nutzen nur, wenn er über den VIX hinaus trägt. SPY-Dollarvolumen wächst über 2011–2026 um ein Vielfaches → nur trendbereinigt bzw. als rollierender z-Score. Offen, ob ETF-Volumen Marktliquidität abbildet. Review-Angabe „Korrelation Daily/Intraday-Amihud ≈ 0,42“ ohne Quelle, nicht übernommen. Intraday-Variante nur 2 Jahre (kein Stress) → nicht als Testbasis |
| H14 | Cross-Asset-Risikoappetit: Kupfer/Gold-Verhältnis und US-Dollar-Momentum (20T-Rendite, z-Score) | **Eine** Hypothese mit vorab gewählter Einzelreihe je Achse, nicht beide Varianten frei wählen (Multiple Testing). Dollar: FRED `DTWEXBGS` (Broad Index) statt ICE-DXY prüfen (frei, lange Historie). Kupfer/Gold: Futures-Rollkontrakte bzw. ETFs – Rollartefakte und Point-in-Time-Fähigkeit klären |
| H15 | MOVE-Index (Anleihe-Vola) als Zins-Stressachse | ICE-Lizenz; freie Historie nur über Yahoo `^MOVE`, Lückenlosigkeit und Nutzungsrecht prüfen. Abgrenzung zu H4 (Zinskurve ❌): Vola der Zinsen ≠ Niveau/Steigung |
| H16 | NYSE-TRIN (Arms-Index), Up-/Down-Volumen | Freie, lückenlose Tageshistorie ab ≤ 2011 **nicht belegt** → erst Quelle finden, sonst streichen. Überschneidung mit H12 (Breite) vor Präregistrierung klären |
| H17 | AAII Bull-Bear-Spread (wöchentlich) | Point-in-Time: Stempel = Veröffentlichungstag (Donnerstag), Forward-Fill nur ab dann; Bezug der Historie (Mitgliederbereich?) und Lizenz prüfen. Nur als Kontrarian-Kontext, nicht als Timing-Signal |

**Geprüft und nicht aufgenommen (29.09.2026):**
- **Gamma-Flip, Charm, Net-GEX-Nullpunkt:** keine freie Historie vor ca. 2022; frei ist nur das Net-GEX-Niveau von SqueezeMetrics (bereits genutzt). Weg nur über (a) bezahlte EOD-Ketten (ThetaData/ORATS; Umfang/Preis ungeprüft; nur interne Forschung, nicht UIQ Public) oder (b) ein **eigenes Forward-Archiv** delayed Cboe-Ketten nach Muster des UIQ-IV-Archivs (№15/№70) – Entscheidung auf UIQ-Seite, Nutzungsbedingungen der Cboe-Endpunkte vorher prüfen; Fremd-Repos (`traders-edge-mcp`, `global-stock-data`) ungeprüft, nicht als Datenquelle einbinden.
- **0DTE-Anteil:** Historie erst ab 2022, darin genau eine schnelle Stressepisode (Aug. 2024) → als Gate bei n = 1 kalibriert; höchstens beschreibend im Snapshot.
- **Zwei-Ebenen-Modell mit „Panik-Gate → sofort flat“:** Ausstiegsfilter auf Verdacht (Phase-3-Konsequenz); zudem strukturell wirkungslos gegen Übernacht-Gaps (Position t−1 × Rendite t; 24.08.2015, 05.08.2024).
- **PCA über gemischte Features → HMM:** schwer interpretierbar; die sinnvolle Variante (PCA der VIX-Kurve) ist H8.
- **Durchschnittliche realisierte Einzeltitel-Korrelation:** braucht survivorship-freie Indexzusammensetzung; implizites Gegenstück COR1M in H3 bereits ❌.
- **Methodik-Hinweis aus dem Review, korrigiert:** Der AIC/BIC-Vergleich der Framework-Integration (README) lief auf unterschiedlichen Stichproben (3.965 vs. 3.203 Zeilen) und ist damit **nicht aussagekräftig** – in keine Richtung (vgl. K10). White's Reality Check / Hansen SPA sind für die Prognosevergleiche in Phase 4 nicht das passende Werkzeug (dort Diebold-Mariano / Giacomini-White), aber als Ergänzung zur DSR für die wirtschaftliche Prüfung (Phase 5, alle 42+ Versuche) vormerken.
