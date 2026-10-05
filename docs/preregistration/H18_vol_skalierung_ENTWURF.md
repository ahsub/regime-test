# Präregistrierung H18 – Reine Volatilitätsskalierung (Vol-Targeting ohne HMM/Regime)

**Status: ENTWURF · GEPARKT · Rev. H18.0** · 05.10.2026 · **nicht eingefroren · nicht freigegeben**
Nummer **vorläufig**: H18 ist in `main`, `h5-saisonalitaet-entwurf` und `pcr-daily-loader` nicht belegt (H13–H17 sind Kandidaten aus dem zweiten externen Review, `docs/literatur/README.md`). Vor dem Commit erneut gegen alle Branches prüfen.

**Forschungsentwurf. Keine Aussage über UIQ, keine Produktionsanforderung, keine UIQ-Integration, kein Public-Output.** Dieser Entwurf erzeugt keine Implementierungsfreigabe. Freigabe zur Implementierung erst nach Abschluss von Phase 4 der Regime-Roadmap („Prognose statt Timing“), nach der Klärung des UIQ-Befunds D26 (asynchrone Preis-/Volumenstände in Nachtsnapshots; betrifft nur Daten aus dem UIQ-Nachtarchiv, nicht die hier vorgesehenen Tagesdaten) und per dokumentiertem Go/No-Go (Abschnitt 12). Bis dahin: **kein Code, kein Auswertungs-Snapshot.**

Herkunft der Idee: externer Text zur Marketstate-Weiterentwicklung (04./05.10.2026). **Aus diesem Text wird keine Zahl und kein Erfolgskriterium übernommen** (insbesondere nicht „Sharpe 1,3–1,5 realistisch“ oder „>2 fast immer Overfitting“); die Aussage „der Sharpe-Uplift kommt fast ausschließlich über den Nenner“ ist hier eine **zu prüfende Frage**, keine Annahme.

Architektur analog H1/H3/H4/H6. Vor dem Einfrieren darf dieses Dokument überarbeitet werden, **solange keine Renditedaten des Evaluationsfensters ausgewertet wurden**. Nach dem Einfrieren: Änderungen nur als neue, separat nummerierte Hypothese (H18b …), die bei n_trials mitzählt.

## 1. Fragestellung

**Bringt eine Skalierung des Aktien-Exposures allein anhand beobachtbarer historischer Volatilität einen robusten Out-of-Sample-Risikonutzen gegenüber (A) einer unskalierten Position und (B) einem statischen Mischportfolio mit derselben durchschnittlichen Aktienquote?**

Die Frage trennt zwei Dinge, die ohne Kontrollen vermischt würden: Nutzen durch **zeitliche** Skalierung gegenüber bloßem **Entrisiken** (niedrigere durchschnittliche Quote).

Bewusst **nicht** Teil von H18:

- keine HMM-, Regime-, GEX-, VIX-Strukturkomponente und keine `classify_regime_v2()`-Einbindung;
- keine Zustandswahrscheinlichkeiten oder Übergangswahrscheinlichkeiten (diese wären eigene Hypothesen);
- keine Titelauswahl, keine Optionsstrategien, keine Strategiegates;
- keine Hebelung (Gewicht ≤ 1);
- keine Parameteroptimierung und keine nachträgliche Variantenwahl.

## 2. Regeln (konventionelle Werte, vor dem Freeze festzuschreiben, nicht optimiert)

Die folgenden Werte sind **Vorschläge** und gelten erst mit dem Freeze. Sie sind als gängige Konventionen gewählt, nicht anhand von Ergebnissen. Eine Änderung nach Sichtung von Renditedaten des Evaluationsfensters ist ausgeschlossen (siehe Kopf).

- **Risikoasset:** SPY (Total Return, dividendenbereinigt). Alternative Indexreihe nur, wenn die Datenherkunft nach Abschnitt 3 sie erzwingt.
- **Volatilitätsschätzer (ein einziger, fest):** annualisierte Standardabweichung der **logarithmischen Tagesrenditen der letzten 21 Handelstage** (Schluss-zu-Schluss), σ_t.
- **Zielvolatilität:** σ* = 10 % p.a. (fest, nicht aus der Stichprobe abgeleitet; die Bestimmung einer Skalierungskonstanten aus dem Gesamtzeitraum wäre Look-ahead).
- **Gewicht:** w_t = min(1, σ* / σ_t). Rest in der T-Bill-Reihe (Abschnitt 3).
- **Timing (konservativ):** σ_t wird am Schlusskurs von Tag t berechnet; w_t gilt für die Rendite von **Tag t+1**. Keine Umschichtung zum selben Schlusskurs, aus dem das Signal stammt.
- **Neugewichtung:** täglich. (Ein Monatsraster wäre eine eigene Variante und zählt bei n_trials mit.)

**Vergleichsreihen (alle mit identischer Kostenrechnung):**

- **A – unskaliert:** 100 % SPY.
- **B – exposure-matched statisch:** konstante Quote q = mittlere Quote von H18 im Evaluationsfenster, Rest T-Bill. q ist ex post bekannt und dient ausdrücklich nur als Kontrolle, nicht als handelbare Regel.
- **C – VIX-only-Skalierer:** dieselbe Formel mit dem VIX-Schlusskurs (Vortag t) statt σ_t, übernommen als Referenz im Sinne der Phase-4-Vorgabe „VIX als Benchmark“. **Die genaue Definition von C folgt aus der Phase-4-Präregistrierung** (liegt in `docs/preregistration/` noch nicht vor); bis dahin Platzhalter.

## 3. Daten und Datenherkunft (Freeze-Voraussetzung)

- Tagesschlusskurse und Total Return für SPY, VIX-Schlusskurse (Cboe), T-Bill-Reihe wie in H6 (FRED DTB3, Konstruktion dort Abschnitt 3 prüfen und übernehmen).
- Vor dem Freeze je Quelle: Abrufdatum, SHA-256, `PROVENIENZ.md` unter `data/raw/<quelle>/<datum>/`; Indexidentität und Historienbeginn je Reihe; Behandlung von Feiertagen und Lücken.
- **Point-in-Time:** Nur zum jeweiligen Zeitpunkt verfügbare Daten. Dividenden-/Adjustierungslogik der Quelle dokumentieren (Rückwärtsadjustierung darf keine Zukunftsinformation in vergangene Preise tragen, die in die Regel eingeht).
- **Nicht** verwendet werden Tageswerte aus dem UIQ-Nachtarchiv (`uiq-archive`), solange D26 offen ist.

## 4. Zeitfenster und Grenzen der Evidenz

- **Entscheidungsrelevant:** ein einziges, vor dem Freeze festgelegtes Evaluationsfenster auf realen Instrumenten. Bis zur Phase-4-Präregistrierung **Platzhalter** (Fenster und Marktperioden werden von dort übernommen, damit alle Hypothesen dieselben Perioden verwenden).
- Weil die Parameter **nicht** an den Daten angepasst werden, ist das gesamte Fenster in Bezug auf die Regel nicht durch Anpassung verzerrt. Das macht es dennoch **nicht** zu einem unabhängigen Out-of-Sample-Test, wenn die Konventionswerte (21 Tage, 10 %) aus Arbeiten stammen, die auf überlappenden Daten entwickelt wurden. Daher durchgehend „Evaluation“, nicht „Validierung“.
- **Stressphasen** (z. B. 2020, 2022): rein deskriptiv, kein Entscheidungskriterium.

## 5. Kennzahlen und Kosten

r_t = w_(t−1) × SPY-Rendite_t + (1 − w_(t−1)) × T-Bill_t − Kosten_t.
Kosten: 5 Bp × |Δw| je Umschichtung (Sensitivität 0 / 10 / 20 Bp, wie H6 Abschnitt 5), inklusive Glattstellung am Fensterende. Eine explizite **Turnover-Regel** wird mitberichtet: mittlerer jährlicher |Δw|-Umsatz und Kostenbelastung in Prozentpunkten Rendite p. a.

## 6. Primärkriterium (vor dem Freeze festgelegt, nicht nach Ergebnis wählbar)

- **Primär:** Δ = SR(H18) − SR(B), Sharpe Ratios aus **monatlichen** Überschussrenditen (über die T-Bill-Reihe), nach 5 Bp Kosten. Test: paarweiser Sharpe-Differenz-Test nach **Ledoit & Wolf (2008)** mit Studentized Circular Block Bootstrap; Blocklänge 6 Monate, 10 000 Ziehungen, fester Seed (vor Freeze festschreiben). H0: Δ ≤ 0 · H1: Δ > 0, einseitig, α = 0,05.
- Begründung: B hat dieselbe mittlere Quote. Ein positives Δ bedeutet daher Nutzen durch die **zeitliche** Skalierung, nicht durch bloßes Entrisiken.
- **Ergebnisformulierung:** „Zusätzlicher Skalierungseffekt gegenüber exposure-matched statischer Quote statistisch nachgewiesen“ genau dann, wenn H0 abgelehnt wird; sonst „kein belastbarer statistischer Nachweis“ (ausdrücklich nicht „widerlegt“).
- **Vorbehalt:** Die Wahl von B als Primärvergleich ist ein Vorschlag und wird im externen Review des Entwurfs bestätigt oder ersetzt, **bevor** der Freeze erfolgt.

## 7. Sekundäre Kennzahlen (berichtet, ändern die Entscheidung nicht)

Für H18 gegen A, B und C jeweils mit Differenz und Block-Bootstrap-Konfidenzintervall (gleiche Einstellungen wie Abschnitt 6): CAGR, Volatilität, Sharpe, **Sortino**, Max Drawdown (Tagesschlusskurse), **Calmar**, CVaR 5 % (monatlich), **Downside-Deviation**, **Tail Loss**, Ulcer-Index, **mittlere Quote** und Zeit mit Gewicht < 1, Umsatz, Kostenbelastung, Trefferquote. Keine dieser Kennzahlen wird nach Sichtung der Ergebnisse zum Primärkriterium erklärt.

**Zerlegung des Uplifts (deskriptiv, vorab festgelegt):** Differenz H18 − A zerlegt in (i) Renditebeitrag, (ii) Volatilitätsbeitrag, (iii) Tail-Beitrag (CVaR/Tail Loss). Ziel ist die Frage, ob der Nutzen im Wesentlichen aus dem Nenner (Volatilität) stammt; dies wird **gemessen, nicht vorausgesetzt.**

## 8. Mehrfachtest- und DSR-Regel

- H18 zählt innerhalb von `regime-test` mit **1 Kandidaten** zur kumulierten Gate-Familie; gemeinsamer `n_trials`-Zähler (Bezug: H1, dort n_trials = 16 als konservative Obergrenze für Phase 4).
- Werden H18 und weitere Skalierungs-/Regime-Hypothesen (z. B. eine spätere Regime-Risikobudget- oder Persistenz-Hypothese) **gemeinsam** untersucht, gilt: gemeinsamer `n_trials`, Korrektur der Primär-p-Werte nach einer **vor dem Freeze** festgelegten Regel (Vorschlag: Holm), und DSR als Selektionskontext (kein Entscheidungskriterium, analog H6 Abschnitt 6).
- Parameter-Varianten (andere Fenster, andere Zielvolatilität, Monatsraster, EWMA) sind **keine** freien Alternativen, sondern nur als neue, separat nummerierte Hypothesen zulässig.

## 9. Prior Research und Selektionskontext (Freeze-Voraussetzung)

Vor dem Freeze in `docs/preregistration/H18_prior_research.md` zu dokumentieren (alle Angaben **vor Verwendung gegen die Originale prüfen**, hier nur als Suchhinweis, nicht belegt): Arbeiten zu volatilitätsgesteuerten Portfolios und deren Replikationen bzw. Kritik (u. a. Moreira & Muir; kritische Gegenarbeiten zur Out-of-Sample-Performance), mit Datenzeitraum, Schätzerfenster, Zielvolatilität und Regel zur Skalierungskonstante. Daraus eine **Spanne** der implizit getesteten Varianten (N_min, N_max). Die DSR wird dafür berichtet.

## 10. Abbruchkriterien

- SPY-Total-Return-, VIX- oder T-Bill-Historie nicht mit dokumentierter Herkunft beschaffbar → Abbruch.
- Look-ahead im Skalierungsgewicht (Timing t → t+1 nicht eingehalten) → Abbruch vor Auswertung.
- Prior-Research-Dokumentation (Abschnitt 9) nicht erstellbar → kein Freeze.
- Primärvergleich B nicht eindeutig definierbar (mittlere Quote abhängig von nachträglicher Wahl) → kein Freeze.

## 11. Abgrenzung zu Phase 4 und zu H13–H17

H18 beantwortet nicht die Phase-4-Frage (Prognose von Volatilität/Regime gegen den VIX), sondern eine Allokationsfrage mit beobachtbarer Volatilität. Sie ist die einfachste Vergleichsbasis, an der sich spätere, aufwendigere Skalierungs- oder Regime-Risikobudget-Hypothesen messen lassen müssten. Keine Überschneidung mit H13–H17 (Amihud, Kupfer/Gold bzw. Dollar, MOVE, TRIN, AAII).

## 12. Freeze- und Freigabe-Checkliste

- [ ] Phase 4 der Regime-Roadmap abgeschlossen, Go/No-Go für H18 dokumentiert
- [ ] D26 (UIQ) geklärt bzw. unabhängig von den hier verwendeten Daten bestätigt
- [ ] Nummer H18 gegen alle Branches bestätigt
- [ ] Definition von C (VIX-only) aus der Phase-4-Präregistrierung übernommen; Evaluationsfenster und Marktperioden übernommen
- [ ] Parameter (21 Tage, 10 %, Gewicht ≤ 1, Timing t+1, tägliche Neugewichtung) im externen Review bestätigt
- [ ] `H18_prior_research.md` mit N_min/N_max
- [ ] Datenquellen belegt, Snapshot + SHA-256 + `PROVENIENZ.md`
- [ ] Ledoit-Wolf-Implementierung gegen Referenzimplementierung verifiziert
- [ ] Mehrfachtest-Regel (Abschnitt 8) festgeschrieben
- [ ] QC-Bericht
- [ ] Externes Review des Entwurfs
- [ ] Status auf „eingefroren“ gesetzt, Commit **vor** jeder Auswertung des Evaluationsfensters

## Literatur

- Ledoit, O. & Wolf, M. (2008). Robust Performance Hypothesis Testing with the Sharpe Ratio. *(Angaben vor dem Freeze prüfen.)*
- Weitere Arbeiten zu volatilitätsgesteuerten Portfolios mit vollständigen Angaben in `H18_prior_research.md` *(vor dem Freeze zu erstellen; hier bewusst nicht aus dem Gedächtnis zitiert)*.
