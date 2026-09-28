# Präregistrierung H5 – Saisonale Renditeeffekte (Halloween, Turn-of-the-Month)

**Status: ENTWURF · GEPARKT** · erstellt 28.09.2026 · **nicht eingefroren**
Freigabe zur Implementierung erst nach Abschluss von Phase 4 der Regime-Roadmap, per
dokumentiertem Go/No-Go (Abschnitt 11). Audit №72 und der Go/No-Go-Termin Dezember 2026 bleiben
davon unberührt.

Architektur analog H1/H3/H4. Vor dem Einfrieren darf dieses Dokument frei überarbeitet werden,
**solange keine Daten des Testfensters ausgewertet wurden**. Nach dem Einfrieren gilt wie bisher:
Änderungen nur als neue, separat nummerierte Hypothese (H5b …), die bei n_trials mitzählt.

## 1. Fragestellung

Existieren ausgewählte, in der Literatur dokumentierte saisonale Renditeeffekte im S&P 500
**auch nach ihrer Veröffentlichung** – und haben sie gegenüber Buy & Hold einen ökonomisch
relevanten Wert?

Bewusst **nicht** Teil von H5:

- keine Regime-Konditionierung (weder `classify_regime_v2()` noch HMM-Zustände) – die
  Regime-Gates haben in Punkt 34 und Phase 3 keinen Vorsprung gegenüber Buy & Hold gezeigt;
- kein Scan rollierender Kalenderfenster, keine nachträgliche Fensterauswahl;
- keine Stop-Varianten, kein Nachbau der 15 Broschüren-Bausteine;
- keine Produktauswahl (UCITS), keine UIQ-Integration, kein Public-Output.

## 2. Hypothesen (Parameter aus der Literatur fixiert, nicht optimiert)

**H5a – Halloween-Effekt** (Bouman & Jacobsen 2002).
Für jedes Jahr y:
R_S(y) = ln(C_Okt(y) / C_Apr(y)) · R_W(y) = ln(C_Apr(y+1) / C_Okt(y)),
C_M(y) = Schlusskurs des letzten Handelstags im Monat M des Jahres y.
**D(y) = R_W(y) − R_S(y).** H0: E[D] ≤ 0 · H1: E[D] > 0.

**H5b – Turn-of-the-Month (ToM)** (Ariel 1987; Lakonishok & Smidt 1988).
ToM-Tage eines Monats m = letzter Handelstag von m−1 plus die ersten 3 Handelstage von m
(Fenster −1 … +3). Übrige Tage = Nicht-ToM.
**G(m) = Mittel der log-Tagesrenditen an ToM-Tagen − Mittel an Nicht-ToM-Tagen.**
H0: E[G] ≤ 0 · H1: E[G] > 0.

**H5c – Vor-Feiertags-Effekt: gestrichen** (nicht nur optional). Grund: Der historische
NYSE-Feiertagskalender müsste vollständig rekonstruiert werden (Samstagshandel bis 1952,
Sonderschließungen); Aufwand und Fehlerrisiko stehen in keinem Verhältnis. Eine spätere
Aufnahme wäre eine neue Hypothese mit eigener Präregistrierung.

## 3. Daten

- **Primär:** S&P 500 Kursindex (^GSPC), Tagesschlusskurse, neuer Snapshot mit Historie ab
  1928 unter `data/raw/<quelle>/<datum>/`, SHA-256 dokumentiert. Der vorhandene Snapshot
  `data/raw/yahoo/2026-09-27/GSPC.csv` beginnt erst 1990 und reicht für das
  Replikationsfenster nicht.
- **Kursindex statt Total Return als Primärreihe**, weil nur er die lange Historie bietet.
  H5a und H5b vergleichen Aktienrenditen untereinander; der Dividendenanteil verteilt sich
  näherungsweise gleichmäßig. Sensitivität mit ^SP500TR (ab 1988) wird berichtet.
- NYSE-Handelstage laut Datenreihe, **kein Forward-Fill**.
- **QC vor jeder Auswertung:** Lücken > 5 Handelstage außerhalb bekannter Schließungen,
  Tagesrenditen |r| > 25 %, Serien identischer Schlusskurse > 1 Tag → dokumentieren; nicht
  erklärbar → Abbruch (Abschnitt 10).

## 4. Zeitfenster

Da alle Parameter aus der Literatur stammen, gibt es **keine Auswahlphase und kein
Entwicklungsfenster**. Das Testfenster ist die Zeit **nach** Ende der Originalstichproben.

| Fenster | H5a (Jahre y) | H5b (Monate m) | Rolle |
|---|---|---|---|
| Replikation (vor Publikation) | 1928 – 1998 | 02/1928 – 12/1986 | nur berichtet |
| **Test (nach Publikation)** | **2000 – 2025** | **01/2000 – 08/2026** | **entscheidungsrelevant** |

H5a: y = 2025 benötigt C_Apr(2026) (vorhanden). Das Jahr 1999 bleibt als Puffer
ungenutzt; Lücke zwischen Replikation und Test bei H5b ebenfalls bewusst.

**Stichprobengröße ehrlich benannt:** H5a hat im Testfenster **26 unabhängige
Jahresdifferenzen**, H5b rund **320 Monate**. H5a ist damit schwach gepowert (Abschnitt 6).

## 5. Teststatistik

- **Primär:** einseitiger t-Test auf den Mittelwert von D(y) bzw. G(m). Beobachtungen
  überlappen nicht; Einheiten sind Jahre bzw. Monate, nicht Tage.
- **Robustheit (berichtet):** Vorzeichentest; Bootstrap-Konfidenzintervall
  (10 000 Ziehungen, fester Seed); bei H5b zusätzlich Newey-West-Standardfehler (Lag 3).
- **Multiples Testen:** Holm-Korrektur über H5a und H5b, α = 0,05 familienweit.
- **n_trials:** H5 bildet eine eigene Familie (Saisonalität, nicht Regime). Zwei Tests; bei
  DSR-Nutzung für Strategievarianten (Abschnitt 7) zählen alle dort gerechneten Varianten mit.

## 6. Power (Freeze-Voraussetzung)

Vor dem Einfrieren wird die minimal nachweisbare Effektgröße (MDE, 80 % Power, einseitig
α = 0,025 nach Holm) **ausschließlich aus dem Replikationsfenster** geschätzt
(Streuung von D bzw. G), nicht aus dem Testfenster. Liegt die MDE für H5a über dem in der
Literatur berichteten Effekt, wird das vor dem Test festgehalten: Ein Nicht-Ergebnis heißt
dann „**nicht nachgewiesen**“, nicht „widerlegt“.

## 7. Ökonomischer Vergleich (sekundär, getrennt vom statistischen Ergebnis)

- **H5a-Strategie:** investiert vom letzten Handelstag Oktober bis letzten Handelstag April,
  sonst Kasse (Rendite 0; Sensitivität mit T-Bill-Satz).
- **H5b-Strategie:** investiert nur an ToM-Tagen, sonst Kasse.
- **Benchmark:** Buy & Hold, identisches Fenster. Zusätzlich **zufällige Kalenderfenster**
  gleicher Länge und Anzahl pro Jahr/Monat (1 000 Ziehungen, fester Seed) als Null-Referenz.
- Kosten 5 Bp × |ΔPos|, Sensitivität 0 / 10 / 20 Bp (ToM handelt rund 24-mal pro Jahr).
- Kennzahlen wie H1 Abschnitt 7: CAGR, Max Drawdown, Calmar, Sharpe (nur berichtet), CVaR 5 %,
  Zeit im Markt. Keine Steuern im Test, aber Hinweis auf die Relevanz.

## 8. Ergebnis und Entscheidung

- **Statistisch bestätigt:** H5a bzw. H5b gilt als bestätigt, wenn der primäre Test im
  Testfenster nach Holm signifikant ist **und** der Effekt im Replikationsfenster dasselbe
  Vorzeichen hat.
- **Ökonomisch relevant:** Calmar der Strategie > Buy & Hold **und** > 95 %-Quantil der
  zufälligen Kalenderfenster, nach 10 Bp Kosten.
- **Relevanz für UIQ nur, wenn beides erfüllt ist.** Ein statistisch bestätigter, ökonomisch
  aber irrelevanter Effekt wird so berichtet und führt zu keiner Integration.

## 9. Europa-Replikation (eigenständiger Bestätigungstest)

Nur wenn H5a oder H5b nach Abschnitt 8 bestätigt ist. Eigene Präregistrierung (H5-EU),
**eingefroren bevor europäische Daten angesehen werden**: identische Regeln und Parameter,
Index vorab festgelegt (Kandidat: DAX, Hinweis Performanceindex vs. Kursindex), keine
Anpassung an europäische Ergebnisse. Werden Hypothesen oder Parameter nach Sicht auf
europäische Daten verändert, ist die Replikation nicht mehr unabhängig und wird so gekennzeichnet.

## 10. Abbruchkriterien

- Lange Historie nicht mit dokumentierter Herkunft beschaffbar → H5a/H5b nur auf verfügbarer
  Historie, Replikationsfenster entfällt, Ergebnis ausdrücklich als eingeschränkt markiert.
- Daten-QC (Abschnitt 3) nicht bestanden → Abbruch vor Auswertung.
- MDE-Rechnung zeigt, dass H5a praktisch nicht entscheidbar ist → H5a nur deskriptiv,
  Holm-Familie reduziert sich auf H5b (vor dem Freeze festzuhalten).

## 11. Freeze- und Freigabe-Checkliste

- [ ] Phase 4 der Regime-Roadmap abgeschlossen, Go/No-Go für H5 dokumentiert
- [ ] Datenquelle für lange ^GSPC-Historie festgelegt, Snapshot + SHA-256
- [ ] QC-Bericht Replikationsfenster
- [ ] MDE-Rechnung (nur Replikationsfenster) eingetragen
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
