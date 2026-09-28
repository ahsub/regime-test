# Präregistrierung H5 – Saisonale Renditeeffekte (Halloween, Turn-of-the-Month)

**Status: ENTWURF · GEPARKT · Rev. H5.1** · 28.09.2026 · **nicht eingefroren**
Rev. H5.1 (28.09.2026, nach externem Review, vor jeder Auswertung): Testfenster an
Stichprobenende bzw. Publikation der Originalarbeiten ausgerichtet; Kosten, Buy & Hold und
Zufallsfenster vollständig definiert; Power mit Abhängigkeitsannahmen; Datenherkunft als
Freeze-Voraussetzung.

Freigabe zur Implementierung erst nach Abschluss von Phase 4 der Regime-Roadmap, per
dokumentiertem Go/No-Go (Abschnitt 12). Audit №72 und der Go/No-Go-Termin Dezember 2026 bleiben
davon unberührt. Die Präregistrierung erzeugt **keine** automatische Implementierungsfreigabe.

Architektur analog H1/H3/H4. Vor dem Einfrieren darf dieses Dokument überarbeitet werden,
**solange keine Daten des Testfensters ausgewertet wurden**. Nach dem Einfrieren gilt:
Änderungen nur als neue, separat nummerierte Hypothese (H5b …), die bei n_trials mitzählt.
Ein nicht signifikantes Ergebnis darf weder durch ein günstigeres Zeitfenster ersetzt noch
durch Regime-Konditionierung „gerettet“ werden.

## 1. Fragestellung

Existieren ausgewählte, in der Literatur dokumentierte saisonale Renditeeffekte im S&P 500
**außerhalb der Originalstichproben** – und haben sie gegenüber Buy & Hold einen ökonomisch
relevanten Wert?

Bewusst **nicht** Teil von H5:

- keine Regime-Konditionierung (weder `classify_regime_v2()` noch HMM-Zustände);
- kein Scan rollierender Kalenderfenster, keine nachträgliche Fensterauswahl;
- keine Stop-Varianten, kein Nachbau der 15 Broschüren-Bausteine;
- keine Produktauswahl (UCITS), keine UIQ-Integration, kein Public-Output;
- keine weiteren Effekte: H5c (Vor-Feiertag) bleibt gestrichen; neue Effekte brauchen eine
  eigene Präregistrierung und zählen zur jeweiligen Testfamilie.

## 2. Hypothesen (Parameter aus der Literatur fixiert, nicht optimiert)

**H5a – Halloween-Effekt** (Bouman & Jacobsen 2002).
Zyklus y = Mai y bis April y+1. C_M(y) = Schlusskurs des letzten Handelstags im Monat M von y.

- **Sommerhalbjahr (Mai–Okt):** R_S(y) = ln(C_Okt(y) / C_Apr(y))
- **Winterhalbjahr (Nov–Apr):** R_W(y) = ln(C_Apr(y+1) / C_Okt(y))
- **D(y) = R_W(y) − R_S(y).** H0: E[D] ≤ 0 · H1: E[D] > 0.

Die Beschriftung wurde gegen die Zeitpunkte geprüft: R_S läuft von Ende April bis Ende
Oktober (Mai–Okt), R_W von Ende Oktober bis Ende April des Folgejahres (Nov–Apr).

**H5b – Turn-of-the-Month (ToM)** (Ariel 1987; Lakonishok & Smidt 1988).
ToM-Tage eines Monats m = letzter Handelstag von m−1 plus die ersten 3 Handelstage von m
(Fenster −1 … +3, Tagesrenditen jeweils Schluss-zu-Schluss). Übrige Tage = Nicht-ToM.
**G(m) = Mittel der log-Tagesrenditen an ToM-Tagen − Mittel an Nicht-ToM-Tagen.**
H0: E[G] ≤ 0 · H1: E[G] > 0.

## 3. Daten und Datenherkunft (Freeze-Voraussetzung)

- **Primär:** S&P-500-Kursindex, Tagesschlusskurse, neuer Snapshot unter
  `data/raw/<quelle>/<datum>/`. Der vorhandene Snapshot `data/raw/yahoo/2026-09-27/GSPC.csv`
  beginnt erst 1990 und reicht für das Replikationsfenster nicht.
- **Vor dem Freeze zu dokumentieren** (in `data/raw/<quelle>/<datum>/PROVENIENZ.md`):
  1. Quelle, Abrufdatum, SHA-256.
  2. **Indexidentität je Zeitabschnitt:** Der S&P 500 existiert erst seit März 1957. Werte davor
     stammen aus einem Vorgängerindex (S&P Composite / S&P 90) und sind als solcher zu
     kennzeichnen. Die Zeitgrenze wird aus der Quelle belegt, nicht angenommen.
  3. **Verkettung:** ob und wie Vorgänger- und Nachfolgeindex auf eine einheitliche Basis
     verkettet sind; Prüfung auf Sprünge an der Verkettungsstelle.
  4. **Revisionen:** ob die Quelle nachträgliche Korrekturen dokumentiert; falls nicht, so
     vermerken.
- **Kursindex statt Total Return als Primärreihe**, weil nur er die lange Historie bietet.
  Sensitivität mit ^SP500TR (ab 1988) wird berichtet. Sie ist **keine unabhängige
  Replikation** (derselbe Markt, weitgehend überlappender Zeitraum), sondern prüft nur den
  Einfluss der Dividendenbehandlung.
- NYSE-Handelstage laut Datenreihe, **kein Forward-Fill**.
- **QC vor jeder Auswertung:** Lücken > 5 Handelstage außerhalb bekannter Schließungen,
  Tagesrenditen |r| > 25 %, Serien identischer Schlusskurse > 1 Tag, Sprünge an der
  Verkettungsstelle → dokumentieren; nicht erklärbar → Abbruch (Abschnitt 11).

## 4. Zeitfenster: Stichprobenende und Publikation getrennt

Nach McLean & Pontiff (2016) werden zwei Grenzen unterschieden: Ende der Originalstichprobe
(ab dann *out-of-sample*) und Veröffentlichung (ab dann *post-publication*). Da alle Parameter
aus der Literatur stammen, gibt es **keine Auswahlphase und kein Entwicklungsfenster**.

Stichprobenenden und Publikationsdaten sind vor dem Freeze an den Originalarbeiten zu
verifizieren. Arbeitsstand:

| Arbeit | Stichprobenende | Publikation |
|---|---|---|
| Bouman & Jacobsen | 1998 | AER, Dezember 2002 |
| Ariel | 1981 | JFE, März 1987 |
| Lakonishok & Smidt | 1986 | RFS, 1988 |

Für H5b gilt das spätere der beiden ToM-Papiere als Grenze.

| Fenster | H5a (Zyklen y) | H5b (Monate m) | Rolle |
|---|---|---|---|
| Replikation (in-sample) | 1928 – 1997 | 02/1928 – 12/1986 | nur berichtet |
| **Test (out-of-sample)** | **1998 – 2025** | **01/1987 – 08/2026** | **entscheidungsrelevant** |
| davon post-publication | 2003 – 2025 | 01/1989 – 08/2026 | berichtet, Vorzeichen muss übereinstimmen |

H5a: Zyklus y = 2025 benötigt C_Apr(2026) (vorhanden). Die Zuordnung eines Zyklus erfolgt nach
seinem Startjahr y. Der Zyklus 1998 beginnt Ende April 1998 und damit vor dem Stichprobenende
von Bouman & Jacobsen; er wird trotzdem dem Testfenster zugeordnet, sofern die Verifikation
ergibt, dass deren Daten vor Ende Oktober 1998 enden. Andernfalls beginnt das Testfenster mit
y = 1999. Diese Festlegung erfolgt vor dem Freeze anhand der Originalarbeit.

**Stichprobengröße:** H5a hat im Testfenster **27–28 Zyklen** (post-publication 23),
H5b rund **475 Monate** (post-publication rund 450). H5a ist schwach gepowert (Abschnitt 6).

## 5. Teststatistik

- **Primär:** einseitiger t-Test auf den Mittelwert von D(y) bzw. G(m) im Testfenster.
  Beobachtungseinheiten sind Zyklen bzw. Monate, nicht Tage; sie überlappen nicht.
- **Robustheit (berichtet, nicht entscheidungsrelevant):** Vorzeichentest;
  Bootstrap-Konfidenzintervall (10 000 Ziehungen, fester Seed 20260928); bei H5b zusätzlich
  Newey-West-Standardfehler (Lag 3); bei H5a Welch-Variante, um Volatilitätsunterschiede
  zwischen Halbjahren zu berücksichtigen.
- **Multiples Testen:** Holm-Korrektur über H5a und H5b, α = 0,05 familienweit.
- **n_trials:** H5 bildet eine eigene Familie (Saisonalität, nicht Regime): 2 statistische
  Tests. Im ökonomischen Vergleich (Abschnitt 7) werden genau 2 Strategien × 4
  Kostenstufen gerechnet; bei DSR-Nutzung zählen diese 8 Varianten mit.

## 6. Power mit realistischen Abhängigkeitsannahmen (Freeze-Voraussetzung)

Die minimal nachweisbare Effektgröße (MDE; 80 % Power; einseitig α = 0,025, die strengere
Holm-Stufe) wird **ausschließlich aus dem Replikationsfenster** geschätzt, nie aus dem
Testfenster. Zwei Varianten, beide berichtet, die **ungünstigere** gilt:

1. **iid-Näherung:** Streuung von D bzw. G, Stichprobenumfang des Testfensters.
2. **Abhängigkeit:** Simulation per Block-Bootstrap der Tagesrenditen des
   Replikationsfensters (Blocklänge 63 Handelstage für H5a, 21 für H5b), mit
   eingepflanztem Effekt, Umfang wie Testfenster, 2 000 Durchläufe, fester Seed. Erfasst
   Volatilitäts-Clustering, Fat Tails und Heteroskedastie zwischen Perioden.

Liegt die MDE für H5a über dem in der Literatur berichteten Effekt, wird vor dem Test
festgehalten: Ein Nicht-Ergebnis heißt dann „**nicht nachgewiesen**“, nicht „widerlegt“.

## 7. Ökonomischer Vergleich (sekundär, getrennt vom statistischen Ergebnis)

**Positions- und Kostenrechnung (für alle Reihen identisch):**
Pos_t ∈ {0, 1} ist die Position über den Tag t (Schluss t−1 bis Schluss t).
Tagesrendite der Strategie: r_t = Pos_t × (C_t / C_{t−1} − 1) − k × |Pos_t − Pos_{t−1}|.
Jede Reihe startet mit Pos = 0 vor dem ersten Handelstag des Fensters; am letzten Handelstag
T des Fensters wird eine offene Position glattgestellt: zusätzlicher Abzug k × Pos_T am
Tag T. Damit zählen **alle** tatsächlichen Positionswechsel
inklusive Ein- und Ausstieg. Kassenrendite = 0 (Sensitivität mit T-Bill-Satz, berichtet).
k ∈ {0; 5; 10; 20} Bp; Entscheidungsstufe **10 Bp**.

- **H5a-Strategie:** Pos_t = 1 an allen Handelstagen von Nov y bis Apr y+1 (Einstieg zum
  Schluss des letzten Oktober-Handelstags, Ausstieg zum Schluss des letzten April-Handelstags);
  2 Positionswechsel je Zyklus.
- **H5b-Strategie:** Pos_t = 1 an den 4 ToM-Tagen (Einstieg zum Schluss des vorletzten
  Handelstags von m−1, Ausstieg zum Schluss des 3. Handelstags von m); 2 Positionswechsel je
  Monat, rund 24 pro Jahr.
- **Buy & Hold:** Pos_t = 1 an allen Handelstagen, identisches Start- und Enddatum,
  identische Kursreihe, dieselbe Kostenformel (1 Einstieg, 1 Glattstellung).

**Zufällige Kalenderfenster (Null-Referenz), exakt definiert:**

- H5a: Zyklus c = Handelstage vom ersten Mai-Handelstag y bis zum letzten April-Handelstag
  y+1, N_c Tage; die echte Strategie ist in den letzten L_c Tagen investiert (Nov–Apr).
  Je Zyklus wird unabhängig ein zusammenhängender Block von L_c Tagen mit gleichverteiltem
  Start in {0, …, N_c − L_c} gezogen. Keine Überlappung zwischen Zyklen (per Konstruktion),
  gleiche Zeit im Markt, gleiche Zahl Positionswechsel.
- H5b: Zyklus m = Handelstage vom Tag nach dem letzten ToM-Tag von m−1 bis zum letzten
  ToM-Tag von m; die echte Strategie ist in den letzten 4 Tagen investiert. Je Zyklus ein
  zusammenhängender Block von 4 Tagen, Start gleichverteilt, analog.
- Je Hypothese **1 000 vollständige Portfoliopfade** über das Testfenster (fester Seed
  20260928), dieselbe Kostenformel. Für jede Kennzahl (Abschnitt 8) wird die Verteilung
  über die 1 000 Pfade gebildet; verglichen wird mit dem **95 %-Quantil derselben Kennzahl**.

## 8. Ergebnis und Entscheidung

**Statistisch bestätigt:** H5a bzw. H5b gilt als bestätigt, wenn der primäre Test im
Testfenster nach Holm signifikant ist **und** der Effekt im Replikationsfenster und im
post-publication-Teilfenster dasselbe Vorzeichen hat.

**Ökonomisch relevant (vorab festgelegt, nach 10 Bp):**
- Entscheidungskennzahl bleibt **Calmar** (konsistent mit H1/H3/H4): Calmar der Strategie
  > Calmar Buy & Hold **und** > 95 %-Quantil der Zufallsfenster-Calmar.
- Stabilitätsregel: Hat die Strategie im Testfenster einen Max Drawdown < 5 %, gilt Calmar
  als instabil und das ökonomische Kriterium als **nicht entscheidbar** (so berichtet, kein
  Ersatz durch eine andere Kennzahl).
- **Pflichtberichte daneben:** CAGR, Max Drawdown, CVaR 5 %, Sharpe (rf 2 % p. a.), Zeit im
  Markt, Zahl Positionswechsel, alle vier Kostenstufen – jeweils mit Buy & Hold und den
  Zufallsfenster-Quantilen (5 %, 50 %, 95 %). Keine dieser Kennzahlen wird nach Sichtung
  der Ergebnisse zur Primärkennzahl erklärt.

**Relevanz für UIQ nur, wenn statistisch bestätigt und ökonomisch relevant.** Ein statistisch
bestätigter, ökonomisch irrelevanter Effekt wird so berichtet und führt zu keiner Integration.

## 9. Europa-Replikation (eigenständiger Bestätigungstest)

Nur wenn H5a oder H5b nach Abschnitt 8 bestätigt ist. Eigene Präregistrierung (H5-EU),
**eingefroren bevor europäische Daten angesehen werden**: identische Regeln und Parameter,
Index vorab festgelegt (Kandidat: DAX, Hinweis Performanceindex vs. Kursindex), keine
Anpassung an europäische Ergebnisse. Werden Hypothesen oder Parameter nach Sicht auf
europäische Daten verändert, ist die Replikation nicht mehr unabhängig und wird so gekennzeichnet.

## 10. Zusätzlich berichtet (nicht entscheidungsrelevant)

- Effekt je Jahrzehnt (deskriptiv, keine Tests).
- Vor-/nach-1957-Aufteilung im Replikationsfenster (Vorgängerindex vs. S&P 500).
- Sensitivität Total Return (^SP500TR, ab 1988) und T-Bill-Kassenrendite.

## 11. Abbruchkriterien

- Lange Historie nicht mit dokumentierter Herkunft beschaffbar → H5a/H5b nur auf verfügbarer
  Historie, Replikationsfenster entfällt, Ergebnis ausdrücklich als eingeschränkt markiert.
- Daten-QC (Abschnitt 3) nicht bestanden → Abbruch vor Auswertung.
- MDE-Rechnung zeigt, dass H5a praktisch nicht entscheidbar ist → H5a nur deskriptiv,
  Holm-Familie reduziert sich auf H5b (vor dem Freeze festzuhalten).

## 12. Freeze- und Freigabe-Checkliste

- [ ] Phase 4 der Regime-Roadmap abgeschlossen, Go/No-Go für H5 dokumentiert
- [ ] Datenquelle festgelegt, Snapshot + SHA-256 + `PROVENIENZ.md` (Abschnitt 3, Punkte 1–4)
- [ ] Stichprobenenden und Publikationsdaten an den Originalarbeiten verifiziert (Abschnitt 4)
- [ ] QC-Bericht Replikationsfenster
- [ ] MDE-Rechnung (beide Varianten, nur Replikationsfenster) eingetragen
- [ ] Externes Review des Entwurfs
- [ ] Status auf „eingefroren“ gesetzt, Commit **vor** jeder Auswertung des Testfensters

## Literatur

- Bouman, S. & Jacobsen, B. (2002). The Halloween Indicator, "Sell in May and Go Away":
  Another Puzzle. *American Economic Review* 92(5).
- Ariel, R. A. (1987). A Monthly Effect in Stock Returns. *Journal of Financial Economics* 18(1).
- Lakonishok, J. & Smidt, S. (1988). Are Seasonal Anomalies Real? A Ninety-Year Perspective.
  *Review of Financial Studies* 1(4).
- McLean, R. D. & Pontiff, J. (2016). Does Academic Research Destroy Stock Return
  Predictability? *Journal of Finance* 71(1).
