# Literatur-Review Market-State-Analytik — Stand 05.10.2026

**Ablage (Vorschlag):** `ahsub/regime-test/docs/literatur/LITERATUR-REVIEW-MARKETSTATE-2026-10-05.md`
**Status:** Entwurf, nicht committet.
**Zweck:** Bewertung von zwölf Quellen für die Regime-Forschung (H18, Phase 4, Modellwahl, Validierung).
**Einordnung:** Dieses Review ändert die Reihenfolge Phase 4 → D26-Klärung → Freeze → Test nicht.

## 1. Lesetiefe und Evidenzart

Die Tiefe der Lektüre ist je Quelle unterschiedlich. Aussagen sind nur so belastbar wie diese Tiefe.

| # | Quelle | Typ | Lesetiefe | Evidenzart |
|---|---|---|---|---|
| 1 | Harvey et al. (2018), The Impact of Volatility Targeting | Paper | Volltext | Empirisch, Out-of-Sample-Logik, lange Historie |
| 2 | Nystrup/Madsen/Lindström (2015), Stylised facts … HMM in continuous time | Paper | Volltext | In-Sample-Fit 1993–2013 |
| 3 | Guidolin/Timmermann (2007), Multivariate regime switching | Paper | Volltext | In-Sample und Out-of-Sample, Monatsdaten, vier Assets |
| 4 | Kritzman/Page/Turkington (2012), Regime Shifts | Paper | Volltext | Backtest, Tilts willkürlich gewählt |
| 5 | Hamilton (1994), Time Series Analysis, Kap. 22 | Lehrbuch (Scan, OCR) | Kap. 22.3–22.4 gelesen, Rest nicht | Methodik |
| 6 | Hamilton/Susmel (1994), ARCH and changes in regime | Paper | Modell, Tabellen 1–3, Schluss | In-Sample-Fit, wöchentliche Prognosen 1962–1987 |
| 7 | Ang/Timmermann (2012), Regime Changes and Financial Markets | Übersichtsartikel | Kernabschnitte (2.3, 2.7, 3.1, 3.5, 4) | Literaturüberblick |
| 8 | Ang (2014), Asset Management | Lehrbuch | Regimestellen, Kap. 3, 4, 8 | Überblick |
| 9 | López de Prado (2018), Advances in Financial ML | Buch (EPUB) | Inhaltsverzeichnis, Kap. 7, 11, 12, 17 punktuell | Methodik |
| 10 | López de Prado (2020), ML for Asset Managers | Buch | Kap. 5 und 8, Synthetik-Abschnitt | Methodik |
| 11 | López de Prado (2023), Causal Factor Investing | Buch | Abstract, Struktur, Schlüsselstellen | Konzeptionell |
| 12 | Time Series with Python | Einsteigerbuch | Stichwortsuche | — |

## 2. Quellen im Einzelnen

### 2.1 Harvey et al. (2018) — Volatilitätsskalierung
- **Design:** Skalierung mit Volatilität bis t−2, EWMA-Halbwertszeiten 10 bis 90 Tage. Beide Varianten werden auf dieselbe Gesamtvola normiert.
- **Sharpe:** US-Aktien ca. 0,40 → 0,5, S&P-Future ca. 0,50 → 0,6. Der robuste Effekt liegt bei Vol-of-Vol und Left Tail (1%-Shortfall −11,4% → −9,0%).
- **Warnungen:** Im Subsample 1958–1987 verbessert sich der Sharpe nicht. Ein Sharpe-Gewinn zeigt sich nur bei Risk Assets (Leverage-Effekt, implizites Momentum). Die Normierungskonstante ist ex post gewählt.
- **Bezug H18:** Primärreferenz für das Testdesign. Primärmetrik eher Tail und Vol-of-Vol als Sharpe. Inkrementellen Nutzen gegenüber classify_regime_v2() explizit testen, da der Mechanismus überlappen dürfte.

### 2.2 Nystrup et al. (2015) — HMM und stilisierte Fakten
- Zwei Zustände reichen für Kurtosis und langsam abklingende Autokorrelation der quadrierten Renditen nicht. Drei bis vier Zustände passen deutlich besser, fünf überfitten.
- t-verteilte Komponenten erhöhen Persistenz und Robustheit gegen Ausreißer, passen die Autokorrelationsfunktion aber schlechter.
- Zustandszahl per BIC. **Grenze:** reiner In-Sample-Fit, keine Prognose- oder Handelsevidenz.

### 2.3 Guidolin/Timmermann (2007) — Multivariates Regime Switching
- Vier Regime: Crash, Slow Growth, Bull, Recovery. Crash und Recovery dauern nur zwei bis drei Monate und folgen aufeinander.
- Erklärt, warum Ausstiegsfilter schwer Mehrwert liefern: Wer im Crash aussteigt, verpasst die Recovery.
- Zustände werden als unbeobachtbar behandelt und gefiltert. Das entspricht der Unterscheidung Antizipation vs. Detektion.
- **Grenze:** Out-of-Sample-Evidenz gemischt (2000–2003 schneidet das reine Regimemodell auf 12 Monate schlechter ab). Monatsdaten, vier Assets.

### 2.4 Kritzman/Page/Turkington (2012) — Regime Shifts
- Idee: Regime auf Treibern (Turbulenz via Mahalanobis-Distanz, Inflation, Wachstum) schätzen statt auf Renditen, rekursiv kalibriert. Turbulenz aus Sektorrenditen wäre ein Kandidat neben COR1M.
- **Schwächen:** Tilts ausdrücklich willkürlich, Signale auf 20 bis 30% Event-Häufigkeit kalibriert, keine Mehrfachtest-Korrektur. Rendite fast unverändert (9,45% vs. 9,43%), der Gewinn ist reine Risikoreduktion.

### 2.5 Hamilton (1994), Kap. 22
- **Filter vs. Glättung:** Gefilterte Wahrscheinlichkeiten nutzen Daten bis t (Gl. 22.4.5). Geglättete (Kim-Algorithmus, Gl. 22.4.14) nutzen auch spätere Daten. Für jeden Backtest sind nur gefilterte Wahrscheinlichkeiten zulässig. Kim-Glättung gilt nur bei strikt exogenen Regressoren.
- **Schätzung:** ML per EM-Algorithmus. Jede Beobachtung geht mit ihrer Regimewahrscheinlichkeit gewichtet in eine OLS-Regression pro Regime ein (Gl. 22.4.20–22.4.23).
- **Zustandszahl:** Der Likelihood-Ratio-Test gegen N−1 Zustände ist nicht standardverteilt. Hamilton verweist auf eigene Tests (1993), Hansen (1992) und Goodwin (1993).
- **Grenzen:** Normalverteilung, Student-t ist eine Erweiterung. Das GNP-Beispiel (Tab. 22.1) wird nachträglich mit NBER-Daten verglichen und ist keine Prognoseevidenz.
- Lesehinweis: Der Scan ist per OCR gelesen, Gleichungsnummern wurden stichprobenartig geprüft.

### 2.6 Hamilton/Susmel (1994) — Markov-Switching-ARCH (SWARCH)
- **Spurious Persistenz:** GARCH(1,1) mit Student-t schätzt Persistenz 0,96; Gaussian-GARCH 0,99. Die SWARCH-Modelle kommen auf ca. 0,42 bis 0,59. Die Persistenz liegt in Niedrig-, Mittel- und Hochvolatilitätsregimen, die typischerweise mehrere Jahre dauern.
- **Student-t:** Freiheitsgrade ca. 4,7 (ARCH) bis 8,7 (SWARCH mit vier Regimen). Leverage-Effekt bestätigt, Hochvolatilitätsregime teilweise mit Rezessionen assoziiert.
- **Prognosegüte (Tab. 2):** Student-t-GARCH-L(1,1) liegt im MSE 8% *schlechter* als eine konstante Varianz. SWARCH verbessert den mittleren absoluten Fehler um 9 bis 13%. Im MSE ist nur SWARCH-L(4,2) positiv (+6%). Bei Horizonten von vier und acht Wochen liegen die Gewinne bei null bis sieben Prozent (Tab. 3).
- **Overfitting-Warnung:** Regime 4 beschreibt im Kern den Crash vom Oktober 1987 und die Wochen davor, mit rechnerisch nur etwa 3,6 Beobachtungen.
- **Grenzen:** Wöchentliche NYSE-Renditen 1962–1987 (T = 1327). Ob die Prognosen mit rollierend neu geschätzten Parametern entstanden, wurde nicht geprüft.
- **Bezug Phase 4:** Kein Beleg, dass ein reines Renditemodell den VIX als Benchmark schlägt. Als Hypothese weiterhin sinnvoll.

### 2.7 Ang/Timmermann (2012) — Übersicht
- **Zustandszahl:** Tests sind nicht standardverteilt (unidentifizierte Nuisance-Parameter unter der Nullhypothese; Davies 1977, Hansen 1992, Garcia 1998, Cho/White 2007). Empfehlung: ökonomisch begründen, oft auf zwei festlegen. Alternative: Residualtests (Hamilton 1996).
- **Volatilität vor Mittelwert:** Regime werden überwiegend über die Volatilität identifiziert. Gleiche Mittelwerte lassen sich nicht ablehnen, gleiche Volatilitäten klar. Das Hochvolatilitätsregime hat niedrige Renditen und entspricht Bärenmärkten.
- **Echtzeit:** Eine Simulation (p00 = 0,95, p11 = 0,80) zeigt gefilterte Wahrscheinlichkeiten, die Regimewechsel teils verpassen und Fehlalarme geben. Das ist strukturell.
- **Allokation:** Das Ignorieren von Regimen kostet nach Ang/Bekaert (2002) etwa zwei bis drei Cent pro Dollar Anfangsvermögen; Tu (2010) findet den Effekt auch bei Parameterunsicherheit. **Grenze:** modellbasierte Nutzenrechnungen, keine Out-of-Sample-Handelsergebnisse.
- **Ex-post-Interpretation:** Identifizierte Regime fallen oft mit Regulierungs- oder Politikwechseln zusammen und sind teils nur im Nachhinein deutbar.
- **Offene Frage des Artikels:** Hochfrequente Daten könnten Regime besser identifizieren. Das stützt die Intraday-Erweiterung.

### 2.8 Ang (2014) — Asset Management
- **Kap. 4:** Rebalancing ist „short Volatilität" und damit „short regime changes". Ang trennt seltene permanente von häufig wiederkehrenden Regimewechseln (Rezession/Expansion, Bull/Bear, hohe/niedrige Vola) und verweist für letztere auf Hamilton (1989) und Ang/Timmermann (2012).
- **Kap. 8:** Prädiktive Koeffizienten schwanken über die Zeit (Henkel/Martin/Nardari 2011: schwach in Expansionen, stark in Rezessionen). Nach Welch/Goyal (2008) schlägt der historische Mittelwert fast alle Prädiktoren out-of-sample. Das stützt die Persistenz-/Random-Walk-Baseline.
- **Kap. 3, Risk Parity:** Inverse-Vola-Gewichtung erreicht im Buch den höchsten Out-of-Sample-Sharpe (0,65). Ang warnt vor Prozyklik, Ignoranz gegenüber Bewertungen und einem Erfolg, der zum Teil aus 51% Treasuries (Marktgewicht 14%) stammt. Gegenargument für H18.
- Übrige Kapitel (Faktoren, Anleihen, Private Equity, Hedgefonds) sind für diese Fragestellung nicht relevant.

### 2.9 López de Prado (2018) — AFML
- **Purged K-Fold und Embargo (Kap. 7):** Überlappende Labels erzeugen Leakage. Überlappende Prognosehorizonte in Phase 4 machen Purging und Embargo zur Pflicht.
- **Backtesting (Kap. 11–14):** Backtest ist kein Forschungswerkzeug; jeder Backtest auf einem Datensatz ist zu protokollieren, damit die Anzahl der Versuche in die Deflation des Sharpe eingeht. Kap. 12 vergleicht Walk-Forward mit Combinatorial Purged CV.
- **Strukturbrüche (Kap. 17):** SADF, Chow-type Dickey-Fuller und CUSUM als Brüche-/Explosivitätstests. Als weitere Detektor-Kandidaten denkbar. Ein belegter Mehrwert für Regime-Gates ist daraus nicht ableitbar.
- **Meta-labeling:** Trennung von Richtung und Größe, analog zur Signal/Risiko-Trennung der Options-Coaching-Chain.
- Entropie-Features (Kap. 18): spekulativ, nicht priorisiert.

### 2.10 López de Prado (2020) — MLAM
- **Kap. 8:** False-Strategy-Theorem (der erwartete beste Sharpe aus K Versuchen ist bei wahrem Sharpe null positiv und hängt von K und der Varianz der Sharpes ab), Deflated Sharpe Ratio mit Korrektur für Schiefe, Kurtosis, Stichprobenlänge und Mehrfachtests, effektive Anzahl der Versuche (8.7.1) und Familywise Error Rate (8.8).
- **Kap. 5:** Triple-Barrier und Trend-Scanning als mögliche Zielgrößen für Phase 4.
- **Synthetische Daten:** Parametrische Monte-Carlo-Verfahren mit Regime-Switching-Modellen (Hamilton 1994) liefern Nullverteilungen.

### 2.11 López de Prado (2023) — Causal Factor Investing
- Faktorstudien machen assoziative Behauptungen ohne Kausalgraph. Folgen sind Fehlspezifikation und Backtest-Overfitting. Unterschieden werden zwei Typen von Scheinaussagen; Confounder und Collider werden ausführlich behandelt.
- **Bezug:** Mahnung bei Kontrollvariablen der Zwei-Achsen-Hypothese (VIX, PCR, Term-Structure): Collider nicht konditionieren. Ein kausaler Mechanismus erlaubt außerdem Überwachung, bevor Verluste auflaufen.
- **Grenze:** Faktor-, nicht Regimethema; keine Regimemodelle.

### 2.12 Time Series with Python
Einsteigerwerk ohne HMM, Markov-Switching und GARCH, nur einfache Volatilitätsmaße. **Nicht aufnehmen.**

## 3. Konsequenzen für die Roadmap

### 3.1 Phase 4 (Prognose statt Timing)
1. **Purging und Embargo** in der Präregistrierung, da Prognosehorizonte überlappen (AFML Kap. 7).
2. **Nur gefilterte Wahrscheinlichkeiten** in allen Backtests, keine Kim-Glättung (Hamilton Kap. 22).
3. **VIX-Benchmark ernst nehmen:** Hamilton/Susmel zeigen, dass selbst gute Regimemodelle bei Varianzprognosen nur knapp über einer konstanten Varianz liegen. Die Baseline-Pflicht (Persistenz/Random Walk) wird durch Ang (Welch/Goyal) gestützt.
4. **Zustandszahl vorab festlegen**, nicht per Likelihood-Ratio-Test (Hamilton, Ang/Timmermann).
5. **Zielgrößen:** Triple-Barrier und Trend-Scanning (MLAM Kap. 5) als Optionen prüfen.

### 3.2 H18 (Volatilitätsskalierung)
1. Harvey et al. als Primärreferenz für das Design.
2. Primärmetrik Tail und Vol-of-Vol, nicht Sharpe.
3. Inkrementellen Nutzen gegenüber classify_regime_v2() explizit testen.
4. Gegenargument Risk Parity (Ang, Kap. 3) in der Hypothesenbegründung aufführen.

### 3.3 Mehrfachtests (alle H-Hypothesen)
1. **Anzahl der Versuche K** über die gesamte Hypothesenfamilie führen (H1–H6, H13–H18, Parametervarianten), nicht nur je Test (MLAM Kap. 8).
2. Familywise-Korrektur über die Familie dokumentieren.
3. Jeden Lauf auf einem Datensatz protokollieren (AFML Kap. 11).

### 3.4 Modellwahl
1. Student-t-Komponenten sind gut belegt (Hamilton/Susmel, Nystrup).
2. Drei bis vier Zustände als Arbeitsbereich, fünf überfitten (Nystrup). Seltene Spike-Regime wie Regime 4 bei Hamilton/Susmel kritisch prüfen.
3. Volatilitätsachse robust, Drift-/Renditeachse nur mit Vorsicht (Ang/Timmermann).

### 3.5 Intraday
Ang/Timmermann nennen hochfrequente Daten als möglichen Identifikationsvorteil. Das stützt die offene Beschaffung einer längeren Intraday-Historie mit Stressphase.

## 4. Offene Punkte
- Hamilton (1989) als Originalquelle fehlt in der Sammlung.
- Hansen (1992) und Garcia (1998) als Primärquellen zur Testproblematik der Zustandszahl fehlen.
- Hamilton (1996) zu Residualtests fehlt.
- Hamilton Kap. 22 nur in den Abschnitten 22.3 bis 22.4 gelesen; Abschnitt 22.2 und die Übungen stehen aus.
- Kritzman et al. und Guidolin/Timmermann: Die Aussagen in 2.3 und 2.4 stammen aus der ersten Sichtung dieser Sitzung und sollten vor einer Übernahme in Präregistrierungen gegen die Originalstellen geprüft werden.
- AFML ist nur punktuell gelesen (Kap. 7, 11, 12, 17).

## 5. Quellenverzeichnis
1. Harvey, C. R., Hoyle, E., Korgaonkar, R., Rattray, S., Sargaison, M., Van Hemert, O. (2018). The Impact of Volatility Targeting. *Journal of Portfolio Management*.
2. Nystrup, P., Madsen, H., Lindström, E. (2015). Stylised facts of financial time series and hidden Markov models in continuous time. *Quantitative Finance*.
3. Guidolin, M., Timmermann, A. (2007). Asset allocation under multivariate regime switching. *Journal of Economic Dynamics and Control*.
4. Kritzman, M., Page, S., Turkington, D. (2012). Regime Shifts: Implications for Dynamic Strategies. *Financial Analysts Journal*.
5. Hamilton, J. D. (1994). *Time Series Analysis*. Princeton University Press.
6. Hamilton, J. D., Susmel, R. (1994). Autoregressive conditional heteroskedasticity and changes in regime. *Journal of Econometrics* 64, 307–333.
7. Ang, A., Timmermann, A. (2012). Regime Changes and Financial Markets. *Annual Review of Financial Economics* 4, 313–337.
8. Ang, A. (2014). *Asset Management: A Systematic Approach to Factor Investing*. Oxford University Press.
9. López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
10. López de Prado, M. (2020). *Machine Learning for Asset Managers*. Cambridge University Press.
11. López de Prado, M. (2023). *Causal Factor Investing*. Cambridge University Press.
12. *Time Series with Python* (Einsteigerbuch; nicht aufgenommen).
