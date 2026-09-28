# Literatur-Review: Carol Alexander, *Market Models — A Guide to Financial Data Analysis*

**Datum:** 28.09.2026
**Quelle:** Carol Alexander, *Market Models: A Guide to Financial Data Analysis*, John Wiley & Sons, Chichester 2001 (EPUB aus OCR, Seitenzahlen nicht zuverlässig)
**Ablage:** `regime-test/docs/literatur/` (Forschungsdokument)
**Zweck:** Einordnung für UIQ-Market-State-Analytik (MSE/regime_v2, MCM, DCE) und für die Regime-Forschung (`ahsub/regime-test`, Phase 4 „Prognose statt Timing“)
**Gelesen:** Kap. 1–6, 9 (Validierung, Stresstests), 10 (Nicht-Normalität, EVT, Normal-Mixture), 12 (Kointegration), 13 (Hochfrequenz, neuronale Netze, Chaos). Kap. 7–8 (Kovarianzmatrizen, Faktormodelle) und 11 (Zeitreihen-Grundlagen) nur überflogen.

Alle Aussagen über das Buch sind Paraphrasen. Wo eine Aussage **nicht** aus dem Buch stammt, sondern aus späterer Literatur oder eigener Prüfung, ist das gekennzeichnet.

---

## 1. Einordnung in einem Absatz

Ein Lehrbuch aus der Risikomanagement-Praxis um 2000: Volatilität und Korrelation als nicht beobachtbare Modellparameter, geschätzt über Moving Averages, EWMA und GARCH; Prognosebewertung; PCA für Zinskurven und Volatilitätsflächen; VaR, Extremwerttheorie und Normal-Mixture-Verteilungen; Kointegration; ein Ausblick auf neuronale Netze. Die methodischen Grundaussagen sind unverändert gültig und für UIQ gut anschlussfähig. **Nicht enthalten** sind die für UIQ zentralen neueren Themen: Markov-Regime-Switching wird nur als Lehrbuchverweis gestreift, der VIX in seiner heutigen Methodik (seit 2003) und die gesamte Nach-2008-Literatur fehlen (HAR-Modelle für realisierte Volatilität, DCC-Korrelation, Model Confidence Set, QLIKE-Verlustfunktion, Deflated Sharpe Ratio). Das Buch ist daher **Methodengrundlage, keine Quelle für den Stand der Forschung**.

---

## 2. Kernaussagen mit UIQ-Bezug

### 2.1 Volatilität ist ein Modellparameter, keine Messgröße (Kap. 1, 5)
**Buch:** Volatilität und Korrelation sind unbeobachtbar und existieren nur innerhalb eines Modells. Selbst im Nachhinein kennt man nur eine Schätzung der realisierten Volatilität, nie die „wahre“.
**UIQ-Bezug:** Stützt ADR-1 und AK-2. Jede öffentlich gezeigte Volatilitäts- oder Risikozahl (HVP, IVP, VaR, VIX-Zonen) ist ein Modellergebnis und muss mit Methode und Fenster ausgewiesen werden. Das gilt auch für die KI-Texte: „die Volatilität ist X“ ist genauer „der Schätzer Y ergibt X“.

### 2.2 Gleichgewichtete Fenster erzeugen Geisterausschläge (Kap. 3)
**Buch:** Bei gleichgewichteten n-Tage-Schätzern zählt ein Extremtag genau n Tage lang voll und fällt dann schlagartig heraus. Die Schätzung springt dadurch, obwohl sich am Markt nichts geändert hat. Kurze Fenster schwanken stark (Stichprobenfehler ~ 1/√n), lange Fenster reagieren zu träge. EWMA (Kap. 3.2) vermeidet den Sprung beim Herausfallen.
**UIQ-Bezug — direkt betroffen:** HV20/50/100 und HVP, `vvix_z20`/`gex_z20`/`skew_pct20` (20-Tage-Fenster), CUSUM-Puffer der DCE (50 Läufe), EVT-VaR (60 Tage), 52-Wochen-Kennzahlen. Konsequenz: Ein plötzlicher „Regimewechsel“ in einer dieser Größen kann bloß das Herausfallen eines alten Extremtags sein. **Prüfvorschlag für №72:** Invarianten-Regel im Snapshot-Prüfer, die große Tagesänderungen einer Fenstergröße gegen „Tag n+1 fiel heraus“ gegenprüft.

### 2.3 Konfidenzbänder gehören zur Schätzung (Kap. 5.2)
**Buch:** Die Standardfehler kurzer Moving-Average-Schätzer sind groß. Bei GARCH werden die Prognosebänder nach einem unerwarteten Schock deutlich breiter — die Unsicherheit kommt dann vor allem vom Markt, weniger von der Parameterschätzung.
**UIQ-Bezug:** Stützt ADR-1, Technische Sperre 2 (`n/v` bei zu kleiner Stichprobe). Für die öffentliche DCE-Marktdiagnostik folgt: Werte ohne Unsicherheitsangabe eher nicht zeigen, zumindest in Stressphasen.

### 2.4 Mittelwertrückkehr und Laufzeitstruktur der Volatilität (Kap. 2.2, 4.4)
**Buch:** Die Laufzeitstruktur der impliziten Volatilität strebt zum langfristigen Mittel, weil Volatilität in Schüben auftritt und zurückkehrt. GARCH liefert aus einem Modell Prognosen für jede Laufzeit, inklusive Halbwertszeit der Rückkehr. Asymmetrische GARCH-Modelle unterscheiden sich vor allem kurzfristig nach starken Kursrückgängen.
**UIQ-Bezug:** (a) Liefert die Begründung für D2: VIX3M über VIX (Contango) ist der Normalzustand, weil kurzfristige Volatilität in ruhigen Phasen unter dem langfristigen Mittel liegt; Backwardation zeigt einen Schub über dem Mittel. (b) **Kandidat für Phase 4:** Halbwertszeit der Volatilitäts-Mittelwertrückkehr (z. B. aus einem GJR-GARCH auf SPY) als zusätzliche Prognosegröße neben dem VIX-Benchmark.

### 2.5 Markt-Regime nach Derman: seitwärts, trendend, sprunghaft (Kap. 2.3)
**Buch:** Nach Derman (1999) lassen sich drei Regime danach unterscheiden, wie die At-the-money-Volatilität auf Indexbewegungen reagiert: seitwärts begrenzt (Volatilität je Strike konstant, „sticky strike“), stabil trendend (Volatilität je Moneyness konstant, „sticky delta“) und sprunghaft (Volatilität steigt stark bei Kursrückgängen). Das Kapitel 6.3 zeigt, dass eine PCA auf Abweichungen der Volatilitätsfläche zwei solche Regime tatsächlich trennt, die Sensitivität aber eher stetig mit dem Indexniveau wandert als zu springen.
**UIQ-Bezug — neue Achse:** regime_v2 klassifiziert über **Niveau und Struktur** der Volatilität (VIX, VIX3M, VVIX, SKEW). Derman klassifiziert über die **Kopplung** von Kurs und Volatilität. Das passt zur bereits notierten „Zwei-Achsen-Hypothese“. **Forschungskandidat (H7, noch nicht präregistriert):** rollierende Spot-Vol-Sensitivität (Regression der VIX-Tagesänderung auf die SPX-Tagesrendite) als zweite Regime-Achse; prüfbar allein mit den vorhandenen Cboe-Daten.

### 2.6 Prognosebewertung: Verlustfunktion und Zeitraum entscheiden (Kap. 5.1)
**Buch:** Das Ergebnis eines Prognosevergleichs hängt stark von der gewählten Bewertungsmethode und vom Zeitraum ab. RMSE gegen realisierte Volatilität ist nur ein einfaches Abstandsmaß und für Varianzen methodisch schwach begründet; besser sind likelihood-basierte Kriterien, die die tatsächlich beobachtete Rendite unter der prognostizierten Verteilung bewerten. Daneben gibt es operative Kriterien (P&L einer Handelsregel). Entscheidend ist die Güte außerhalb der Schätzperiode.
**UIQ-Bezug — direkt für Phase 4 („Prognose statt Timing“, VIX als Benchmark):** In die Präregistrierung gehören **vor** jedem Code: (1) die Verlustfunktion (likelihood-basiert; aus späterer Literatur, nicht aus dem Buch: QLIKE als robuste Wahl gegen verrauschte Proxys), (2) die Bewertungsfenster einschließlich Stressphasen (2008, 2020, 2022), (3) die Out-of-sample-Aufteilung. Sonst lässt sich das Ergebnis im Nachhinein durch Fensterwahl „finden“.

### 2.7 Unsichere Volatilität: Erwartungswert über die Verteilung, nicht Funktion des Erwartungswerts (Kap. 5.3, 10.3)
**Buch:** Ist die Volatilität selbst unsicher, muss der Optionswert als Erwartungswert über die Verteilung der Volatilitäten berechnet werden, nicht durch Einsetzen der erwarteten Volatilität. Ein großer Teil der beobachteten Konvexität impliziter Volatilitäten lässt sich schon durch diese Unsicherheit erklären (Normal-Mixture-Modell). Bei unsicherer Hedge-Volatilität ist ein höherer Wert der vorsichtigere.
**UIQ-Bezug:** Die Options-Strategien (CSP/Wheel, CC, Collar, ATM/NA) arbeiten mit Punktwerten (IVP, HVP, ATR-basierte Strike-Näherung). Für die deskriptiven Texte heißt das: Prämien- und Risikoaussagen auf Basis eines einzelnen Volatilitätspunkts unterschätzen systematisch die Unsicherheit — ein Grund mehr, dort keine konkreten Werte zu nennen (deckt sich mit der bestehenden Public-Regel).

### 2.8 Regime als Mischverteilung (Kap. 10.2–10.3)
**Buch:** Fette Ränder lassen sich durch eine Mischung mehrerer Normalverteilungen mit unterschiedlicher Varianz erzeugen; die Mischungsvarianz ist das wahrscheinlichkeitsgewichtete Mittel, die Kurtosis steigt mit der Spreizung. Anschaulich: zwei Gruppen von Marktteilnehmern mit unterschiedlichen Volatilitätserwartungen.
**UIQ-Bezug:** Die statistische Grundidee hinter den Student-t- und Gauß-HMM-Ansätzen in `regime-test`: Ein HMM ist eine Normal-Mixture mit zeitlicher Abhängigkeit der Mischungsgewichte. Das Buch liefert die Begründung, **warum** Regime-Modelle fette Ränder erklären, aber nicht die HMM-Schätzung selbst.

### 2.9 Extremwerttheorie und VaR-Validierung (Kap. 9.5, 9.6, 10.2)
**Buch:** Peaks-over-Threshold mit verallgemeinerter Pareto-Verteilung beschreibt die Verluste jenseits einer Schwelle. Weil solche Überschreitungen per Definition selten sind, braucht die Schätzung eigene Verfahren und ausreichend Daten. Der erwartete Verlust jenseits der Schwelle (bedingter VaR) ist aussagekräftiger als der VaR allein. Historische, Kovarianz- und Monte-Carlo-VaR weichen oft deutlich voneinander ab; ein VaR-Modell braucht einen Backtest der Überschreitungen.
**UIQ-Bezug — verifizierter Code-Befund (eigene Prüfung, nicht Buchinhalt):** `dce_layer.py` `_calculate_evt_var()` setzt die Schwelle beim 5-%-Quantil von **60** Tagesrenditen. Darunter liegen damit genau drei Werte; der GPD-Fit verlangt aber **mehr als drei**. Die Bedingung ist daher praktisch nie erfüllt (Simulation mit 2.000 Stichproben à 60 Renditen: Fit-Anteil 0 %). Die Funktion liefert in der Praxis immer den Fallback, das **empirische 1-%-Quantil der 60 Renditen** — im Wesentlichen den schlechtesten Tag der letzten drei Monate. Die Bezeichnung „EVT-VaR(95)“ ist damit doppelt unzutreffend (keine EVT, nicht 95 %). Für ADR-1 Stufe 1 bedeutet das: Dieser Messwert darf so nicht öffentlich werden, sondern braucht entweder ein ausreichendes Schätzfenster (mehrere Jahre) mit validiertem GPD-Fit und Überschreitungs-Backtest oder eine ehrliche Bezeichnung als „größter Tagesverlust der letzten 60 Handelstage“.

### 2.10 Kointegration statt Korrelation für Spreads (Kap. 12)
**Buch:** Korrelation beschreibt kurzfristige Gleichläufigkeit von Renditen, Kointegration eine langfristige Gleichgewichtsbeziehung der Preise mit mittelwert-rückkehrendem Spread. Korrelationen sind oft instabil (Kap. 1.4: gemeinsame Stationarität ist keine Selbstverständlichkeit), Terminstrukturen sind die am stärksten kointegrierten Systeme.
**UIQ-Bezug:** (a) Grundlage für die zurückgestellte „Pairs / Relative Value“-Strategie — dort Kointegrationstest statt Korrelationsschwelle. (b) Erklärt, warum H3 (COR1M) keine stabile Zusatzinformation gezeigt hat: implizite Korrelation ist selbst instabil. (c) Die VIX-Laufzeitpunkte (VIX9D … VIX1Y) sind als kointegriertes System zu behandeln — Verhältnisse wie VIX3M/VIX sind eine sinnvolle stationäre Transformation.

### 2.11 PCA auf Laufzeitstrukturen (Kap. 6.2)
**Buch:** Bei Laufzeitstrukturen haben alle Hauptkomponenten eine anschauliche Bedeutung: Niveau, Steigung, Krümmung. Die Daten müssen stationär sein (tägliche Änderungen, nicht Niveaus).
**UIQ-Bezug — Forschungskandidat (H8):** Statt eines einzelnen Verhältnisses VIX3M/VIX die gesamte Cboe-Kurve (VIX9D, VIX, VIX3M, VIX6M, VIX1Y — Historie liegt vor) per PCA auf Niveau, Steigung und Krümmung reduzieren. Das adressiert zugleich die Redundanzfrage der geplanten BN-Analyse (welche Felder tragen unabhängige Information).

### 2.12 Neuronale Netze: Überanpassung ist der Normalfall (Kap. 13.2–13.3)
**Buch:** Neuronale Netze sind universelle Approximatoren und passen sich den Trainingsdaten beliebig genau an; das führt ohne Gegenmaßnahmen zu schlechter Güte außerhalb der Stichprobe. Komplexitätsstrafen in der Fehlerfunktion und Abbruch vor der vollen Anpassung sind die Standardmittel. Die Belege für deterministisches Chaos in Kapitalmärkten hält die Autorin für schwach und methodisch oft unzureichend.
**UIQ-Bezug:** Bestätigt die fünf Leitplanken für das Dual-LSTM-Forschungsprojekt (exogene Features, inkrementeller Nachweis gegen die bestehende Vol-Struktur-Logik, Walk-Forward über mehrere Regime, Kennzahlen nur aus realisierten Trades, Persistenz-Baseline) und die DCE-Wiederaufnahmekriterien für die NN-Komponente.

---

## 3. Was das Buch **nicht** leistet

| Thema | Status im Buch | Wo stattdessen nachlesen (Hinweis, nicht geprüft) |
|---|---|---|
| Markov-Regime-Switching / HMM | nur Verweis auf Hamilton (1994) | Hamilton (1989); Ang & Timmermann (2012, Übersicht) |
| VIX-Methodik seit 2003, VIX-Futures, VVIX, SKEW | fehlt (Buch 2001) | Cboe-Whitepaper |
| Realisierte Volatilität, HAR-Modell | Ansätze zu Hochfrequenzdaten, kein HAR | Corsi (2009) |
| Dynamische Korrelation (DCC) | multivariates GARCH ja, DCC nein | Engle (2002) |
| Prognosevergleich mit verrauschtem Proxy (QLIKE, MCS) | Likelihood-Idee ja, Verfahren nein | Patton (2011); Hansen, Lunde & Nason (2011) |
| Mehrfachtests / Backtest-Überanpassung | fehlt | Bailey & López de Prado (2014, DSR) — in UIQ bereits genutzt |
| Finanzkrise 2008 und danach | fehlt | — |

---

## 4. Konsequenzen für UIQ (Vorschlag, nichts umgesetzt)

| # | Art | Inhalt | Ort |
|---|---|---|---|
| K1 | **Befund (verifiziert)** | „EVT-VaR(95)“ der DCE ist faktisch das empirische 1-%-Quantil von 60 Renditen; GPD-Fit greift nie | **erledigt:** Nachtrag D13 im UIQ-Befundregister (`UIQ-Suite` `d5058cc`), relevant für ADR-1 Stufe 1 |
| K2 | Prüfregel | Geisterausschläge gleichgewichteter Fenster als Invariante im Snapshot-Prüfer (№72) | `uiq-devtools` |
| K3 | Präregistrierung Phase 4 | Verlustfunktion, Bewertungsfenster inkl. Stressphasen und Out-of-sample-Aufteilung vorab festlegen | `regime-test/docs/preregistration/` |
| K4 | Forschungskandidat H7 | Spot-Vol-Kopplung als zweite Regime-Achse (Derman) | `regime-test`, nach Phase 4 |
| K5 | Forschungskandidat H8 | PCA der Cboe-VIX-Kurve (Niveau/Steigung/Krümmung) | `regime-test`, nach Phase 4 |
| K6 | Doku | Literaturverzeichnis (geplant seit 08.09.): Alexander (2001) als Methodenquelle für Volatilitätsschätzer, VaR und Kointegration | UIQ-Literaturverzeichnis |

**Priorität:** K1 gehört in den laufenden Audit, weil er eine öffentlich geplante Kennzahl betrifft. K3 muss vor dem ersten Phase-4-Code stehen. K4/K5 reihen sich hinter die bereits geparkten H5/H6 ein.
