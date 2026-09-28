# Literatur-Review: Carol Alexander, *Market Risk Analysis*, Band I und II

**Datum:** 28.09.2026
**Quellen:**
- Carol Alexander, *Market Risk Analysis, Volume I: Quantitative Methods in Finance*, John Wiley & Sons, 2008
- Carol Alexander, *Market Risk Analysis, Volume II: Practical Financial Econometrics*, John Wiley & Sons, 2008

(Textfassungen aus PDF-Extraktion; Abschnittsnummern wie im Buch, Seitenzahlen nicht geprüft.)

**Ablage:** `regime-test/docs/literatur/` (Forschungsdokument)
**Zweck:** Einordnung für die Regime-Forschung (`regime-test`, insbesondere Phase 4 „Prognose statt Timing“ und die Kandidaten H7/H8) und für die Validierungsregeln in UIQ.
**Verhältnis zu *Market Models* (2001):** Band II ist die aktualisierte und erweiterte Nachfolge des älteren Buchs derselben Autorin (siehe `LITERATUR-REVIEW-ALEXANDER-MARKET-MODELS-2026-09-28.md`). Neu gegenüber 2001 und für uns entscheidend: Markov-Switching (II.7.5), Quantilregression (II.7.2–7.3), Prognose- und Backtest-Methodik mit formalen Tests (II.8), Kointegration mit Volatilitätsfutures als Fallstudie (II.5). Band I ist Grundlagenmaterial; relevant sind vor allem die Abschnitte zu robusten Standardfehlern (I.4.5) und zu risikoadjustierten Kennzahlen (I.6.5).

**Gelesen:** Band II: II.3 (Auszüge), II.4 (Zusammenfassung, Markov-/Mixture-GARCH), II.5 (Stationarität, Volatilitätsfutures, Pairs-Fallstudie, Zusammenfassung), II.7.5–7.7, II.8 vollständig. Band I: I.3 (Zusammenfassung), I.4.5/I.4.7, I.6.5–6.6. Nicht gelesen: II.1 (Faktormodelle), II.2 (PCA-Fallstudien im Detail), II.6 (Copulas im Detail).

Alle Aussagen über die Bücher sind Paraphrasen. Wo etwas **nicht** aus den Büchern stammt, ist es gekennzeichnet.

---

## 1. Kernaussagen mit Bezug zu UIQ und `regime-test`

### 1.1 GARCH statt Moving Averages — und Regime innerhalb von GARCH (II.3, II.4)
**Buch:** Moving-Average-Schätzer haben einen einzigen, subjektiv gewählten Parameter (Fensterlänge bzw. Glättungskonstante) und eine flache Laufzeitstruktur, die der beobachteten Volatilitätsbündelung widerspricht; das Modellrisiko ist entsprechend groß. GARCH-Parameter werden per Maximum-Likelihood geschätzt und liefern Laufzeitstrukturen, die zum langfristigen Mittel konvergieren. Asymmetrische Varianten (E-GARCH nach Nelson passt oft am besten unter den Ein-Komponenten-Modellen) und Student-t-Innovationen verbessern Anpassung und Prognose. Hoch- und Niedrigvolatilitäts-Regime lassen sich auch **innerhalb** von GARCH abbilden: Normal-Mixture-GARCH und Markov-Switching-GARCH.
**Bezug:** Bestätigt Review 1, K2 (Fensterartefakte bei HV20/50/100, z20-Metriken, DCE-Fenstern). Für Phase 4 erweitert das die Vergleichsmenge: Neben dem Student-t-HMM gehören ein asymmetrisches GARCH-t und optional ein Markov-Switching-GARCH als Modellklassen in den Benchmark, damit „Regime“ nicht nur über eine Modellfamilie getestet wird.

### 1.2 Implizite Volatilität: stationär oder integriert? (II.5.3, Fallstudie Volatilitätsfutures)
**Buch:** Optionspreismodelle behandeln implizite Volatilität als mittelwert-rückkehrend; in diskreten Zeitreihen verhält sie sich statistisch oft wie ein integrierter Prozess. Die Fallstudie zu Vdax- und Vstoxx-Futures zeigt, dass das Ergebnis des Einheitswurzeltests von der Laggzahl abhängt: Ohne Lags erscheint die Reihe stationär, mit zwei Lags knapp nicht mehr — die Autorin nennt das Ergebnis selbst grenzwertig und verlangt mehr Daten. Der **Spread** der beiden Futures ist dagegen klar stationär; beide sind stark kointegriert, der Spread lässt sich handeln (Pairs-Fallstudie mit Fehlerkorrekturmodell).
**Bezug:** UIQ nutzt VIX-**Niveaus** mit festen Schwellen und z-Scores, die implizit Stationarität voraussetzen. Die Verhältnisse (VIX3M/VIX, VIX/VVIX) sind als Spread-artige Größen robuster. **Prüfvorschlag (K8):** In `regime-test` vor Phase 4 einmal Einheitswurzeltests (ADF mit Lag-Auswahl nach Informationskriterium, dazu KPSS; Letzteres nicht aus dem Buch) auf VIX, VIX3M, VVIX, SKEW und die verwendeten Verhältnisse über 2007–2026 fahren und dokumentieren, welche Größen als Niveau und welche nur als Verhältnis oder Änderung in Modelle eingehen dürfen.

### 1.3 Kurs-Volatilitäts-Kopplung ist nichtlinear und im Rand am stärksten (II.7.2–7.3)
**Buch:** Die Fallstudie zu FTSE 100 und seinem Volatilitätsindex Vftse findet eine sehr starke Randabhängigkeit und eine nichtlineare Beziehung. Quantilregression (linear und über Copulas) liefert die bedingte Verteilung des Volatilitätsindex für einen angenommenen Indexrückgang — also ein Konfidenzintervall statt eines einzelnen Betas. Ein Chow-Test auf denselben Daten zeigt, wie sich ein Strukturbruch in dieser Beziehung prüfen lässt (II.7.5.1).
**Bezug — schärft H7:** Die in Review 1 vorgeschlagene zweite Regime-Achse (Spot-Vol-Kopplung nach Derman) sollte **nicht** als rollierendes OLS-Beta, sondern über Quantile gemessen werden: die Reaktion des VIX auf SPX-Rückgänge im unteren Rand (z. B. 5-%- und 10-%-Quantil) im Vergleich zur Mitte. Das ist die Größe, in der sich „sprunghafte“ von „trendenden“ Märkten tatsächlich unterscheiden.

### 1.4 Markov-Switching: stark, aber anspruchsvoll in der Schätzung (II.7.5, II.8.2)
**Buch:** Markov-Switching-Regressionen (nach Hamilton 1989) bilden mehrere Brüche und Regimewechsel systematisch ab; Anwendungen reichen von Volatilitätsregimen über Bull/Bear-Märkte bis zu Handelsregeln. Die Likelihood ist komplex, Startwerte sind für die Konvergenz kritisch, Parameterrestriktionen sind nötig, und für eine korrekte Identifikation braucht es eine ausreichend große Stichprobe. Der Likelihood-Quotiententest auf die **Zahl der Regime** folgt nicht der üblichen Chi-Quadrat-Verteilung; die kritischen Werte müssen per Simulation bestimmt werden.
**Bezug:** (a) In `docs/08_STRATEGY_COMPARISON.md` wurde die Framework-Integration über AIC/BIC verworfen. Das Urteil bleibt plausibel, aber für eine **Regime-Anzahl**-Entscheidung reichen Informationskriterien allein nicht; bei künftigen HMM-Vergleichen (2 vs. 3 vs. 4 Zustände) sollte ein simulierter LR-Test oder zumindest eine Out-of-sample-Likelihood ergänzt werden (K10). (b) Konvergenz: jede HMM-Schätzung mit mehreren Startwerten laufen lassen und die Streuung der Ergebnisse berichten — sonst ist ein „gefundenes Regime“ möglicherweise ein lokales Optimum.

### 1.5 Prognosebewertung: In-sample vs. Post-sample, formale Tests (II.8)
**Buch:**
- Gütekriterien innerhalb der Stichprobe sind der schwächere Test; entscheidend sind Post-sample-Kriterien, bei denen Daten-Schnüffeln ausgeschlossen ist.
- Für Volatilitätsprognosen ist RMSE gegen quadrierte Renditen bzw. realisierte Volatilität ein schwaches Kriterium. Besser: Out-of-sample-Likelihood, die Regression quadrierter Renditen auf die Varianzprognose (Achsenabschnitt 0, Steigung 1 bei unverzerrter Prognose; in der Literatur als Mincer-Zarnowitz-Regression bekannt) und formale Vergleichstests zweier Prognosen (Diebold-Mariano).
- Der strengste und praxisnächste Test ist die Prognose der **Verteilungsränder**: unbedingte und bedingte Coverage-Tests nach Christoffersen (1998). Der bedingte Test prüft zusätzlich, ob Überschreitungen gehäuft auftreten.
- Operative Backtests laufen in fünf Stufen; die Ergebnisse hängen von Schätzfenster und Umschichtungsfrequenz ab und müssen deshalb über mehrere Parameterwahlen und getrennt nach Marktregimen berichtet werden, inklusive Transaktionskosten.
**Bezug — direkt für die Phase-4-Präregistrierung (K7):** Festzulegen sind (1) Out-of-sample-Likelihood bzw. QLIKE (QLIKE aus späterer Literatur, Patton 2011) als Hauptkriterium, (2) Mincer-Zarnowitz-Regression als Unverzerrtheitsprüfung, (3) Diebold-Mariano gegen den VIX-Benchmark, (4) Christoffersen-Coverage-Tests für 5-%- und 1-%-Ränder, (5) Bericht getrennt nach Regimen und für mindestens zwei Schätzfensterlängen.

### 1.6 Coverage-Tests für jeden veröffentlichten VaR (II.8.4)
**Bezug zu Befund D13 (UIQ-Befundregister):** Der DCE-„EVT-VaR“ ist faktisch das empirische 1-%-Quantil von 60 Renditen. Soll künftig überhaupt ein VaR als DCE-Marktdiagnostik öffentlich werden, gehört ein Christoffersen-Test (unbedingt und bedingt) über eine lange Historie zur Abnahme — als Ergänzung zu ADR-1 Stufe 1 (K11).

### 1.7 Sharpe Ratio: Grenzen und Autokorrelation (I.6.5)
**Buch:** Die Sharpe Ratio ist nur unter Normalverteilung bzw. exponentiellem Nutzen konsistent; bei nicht-normalen Renditen kann sie Anlagen falsch ordnen und verletzt sogar schwache stochastische Dominanz. Bei autokorrelierten Renditen skaliert die Standardabweichung nicht mit der Wurzel der Zeit; positive Autokorrelation lässt die annualisierte Sharpe Ratio zu hoch erscheinen, und das Buch zeigt die Korrektur. Alternativen: Sortino, Omega, Kappa (mit eigenen Schwächen, weil nur die Verlustseite zählt).
**Bezug:** (a) SUITE №70, Prüfung (b) „inflationiert der DCE-Backtest die Sharpe Ratio durch geglättete Renditen?“ — genau diese Korrektur ist der erste Prüfschritt (K12). (b) Stützt das neue Go-Kriterium 2: Sharpe/DSR nur berichtend, Hauptkennzahl Differenzrendite gegen Buy & Hold mit Newey-West.

### 1.8 Robuste Standardfehler (I.4.5)
**Buch:** Bei Autokorrelation und/oder Heteroskedastizität der Residuen sind OLS-Tests ungültig; Newey-West- (Autokorrelation) bzw. White-Standardfehler (Heteroskedastizität) stellen die Inferenz wieder her.
**Bezug:** Bestätigt die Wahl von Newey-West in `regime_gate_backtest_v2.py` (26.09.). Kein Handlungsbedarf.

---

## 2. Konsequenzen (Vorschlag, nichts umgesetzt; Nummerierung setzt Review 1 fort)

| # | Art | Inhalt | Ort | Priorität |
|---|---|---|---|---|
| K7 | Präregistrierung Phase 4 | Kriterien festschreiben: Out-of-sample-Likelihood/QLIKE, Mincer-Zarnowitz, Diebold-Mariano gegen VIX, Christoffersen 5 %/1 %, Bericht nach Regimen und für ≥ 2 Fensterlängen; Modellklassen: VIX (Benchmark), EWMA, GJR-/E-GARCH-t, Student-t-HMM, optional MS-GARCH | `docs/preregistration/` | **vor erstem Phase-4-Code** |
| K8 | Datenprüfung | Einheitswurzeltests (ADF mit Lag-Wahl, KPSS) auf VIX-Niveaus und -Verhältnissen 2007–2026 dokumentieren; festlegen, welche Größen nur als Verhältnis/Änderung verwendet werden | `regime-test` | vor Phase 4 |
| K9 | Methodik H7 | Spot-Vol-Kopplung über Quantilregression (unterer Rand vs. Mitte), nicht über OLS-Beta; Strukturbruchtest (Chow) als Vorprüfung | H7-Präregistrierung (nach Phase 4) | mittel |
| K10 | Methodik HMM | Regime-Anzahl nicht nur per AIC/BIC; simulierter LR-Test oder Out-of-sample-Likelihood; mehrere Startwerte mit Streuungsbericht | künftige HMM-Vergleiche | mittel |
| K11 | UIQ-Abnahme | Öffentlicher VaR nur mit Christoffersen-Test über lange Historie (Ergänzung ADR-1 Stufe 1, D13) | UIQ-Suite Befundregister | mit Batch 1b |
| K12 | UIQ-Prüfung | Autokorrelations-Korrektur der Sharpe Ratio als erster Schritt von SUITE №70(b) | UIQ-Suite | bei №70 |

## 3. Grenzen

Beide Bände stammen von 2008: realisierte Volatilität wird eingeführt, das HAR-Modell (Corsi 2009), das Model Confidence Set (Hansen, Lunde & Nason 2011), QLIKE als robuste Verlustfunktion (Patton 2011) und die Deflated Sharpe Ratio (Bailey & López de Prado 2014) fehlen zeitbedingt. Die Beispiele laufen überwiegend in Excel, einige Tests (Johansen, Markov-Switching) in EViews/Matlab. Für Umsetzungen in `regime-test` sind die Bücher Methodengrundlage, nicht Code-Vorlage.
