# Präregistrierung H4 – Makro-Achse (Initial Claims, Zinskurve) als Overlay

**Rev. 2** · 27.09.2026 · **vor** jeder Auswertung · Roadmap Phase 3, Hypothese H4
(Rev. 2 nach Review: Eligibility-Fälle 0/1/2/3 ausformuliert, kein Nachschieben von Schwellen,
Primärbegründung ohne Aussage über Signalaktivität)
(UIQ-Suite `docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md`). Design nach externem Review
(Eligibility-Regel, neutrale Primärbegründung, Timing-Definitionen). Architektur wie H1
(`H1_laufzeit_gate.md`, Commit `8e05c0a`) und H3 (`H3_implied_correlation.md`, Commit `e40226f`).
Änderungen nach dem Test nur als neue, separat nummerierte Hypothese (z. B. H4b).

## 1. Fragestellung

Liefern Makro-Informationen, die **nicht aus Optionsmärkten** stammen, einen vorab definierten
inkrementellen Nutzen gegenüber der unveränderten Baseline im Bestätigungsfenster?
Erfolg bemisst sich ausschließlich am Kriterium in Abschnitt 9 (Drawdown-/Tail-Schutz),
nicht an Sharpe oder CAGR.

## 2. Daten und Point-in-Time-Verfügbarkeit

Snapshots (SHA-256 geprüft, Commit `a18778f`):
- `data/raw/alfred/2026-09-27/ICSA_first.csv` – Initial Claims, **Erstveröffentlichung** je Woche
  mit ALFRED-Archivierungsdatum (`realtime_start`); Erstveröffentlichungen ab Beobachtung
  30.05.2009. ICSA wird revidiert (nur 7 % der Werte heute unverändert) → ausschließlich
  Erstveröffentlichungen.
- `data/raw/alfred/2026-09-27_DGS10-DGS3MO-DGS2/` – Treasury-Renditen 10J, 3M, 2J (Fed H.15),
  Erstveröffentlichung mit Archivierungsdatum ab 27.06.2005. Die fertigen Differenzreihen
  T10Y3M/T10Y2Y haben in ALFRED erst ab 01/2014 Vintages; die Kurve wird deshalb **aus den
  Bausteinen** rekonstruiert (nach Review: „nicht revidiert ≠ damals verfügbar“).
- Ausgeschlossen (Phase 0): BAA10Y (Baustein DBAA erst ab 02.04.2014 point-in-time nachweisbar),
  NFCI (point-in-time erst ab 06/2011, starke Revisionen), STLFSI4 (Vintages erst ab 11/2022).
- Cboe-Snapshot `data/raw/cboe/2026-09-27/` (Baseline), Renditen `data/raw/yahoo/2026-09-27/`.
- **Konservatives Verfügbarkeitsdatum:** das ALFRED-Archivierungsdatum `realtime_start`. Die
  tatsächliche Veröffentlichung lag teils früher; ein Wert wird also eher zu spät als zu früh
  genutzt.
- Deskriptiv vor Festlegung ermittelt (ohne Renditebezug, nur Entwicklungsfenster): 10J−3M im
  Entwicklungsfenster nie < 1,09, 10J−2J nie < 0,76; Claims-Anstieg (Abschnitt 3) ≥ 10 % in 8 %
  der Wochen, ≥ 15 % in 0,6 % der Wochen, ≥ 20 % nie (Maximum +17 %).
- **Transparenzhinweis:** Große historische Episoden (Kurveninversionen 2019 und 2022–2024,
  Claims-Anstieg 2020) sind dem Designer bekannt; eine blinde Präregistrierung ist nicht möglich.
  Deshalb werden ausschließlich einfache, feste Standarddefinitionen verwendet.

## 3. Signale (exakte Timing-Definition)

Handelstag t; ein Signal an t bestimmt die Position ab t+1.

**Initial Claims (Familie A).** Für jede Woche w: v_w = Erstveröffentlichungswert,
r_w = Archivierungsdatum. Bekannt an t: alle Wochen mit r_w ≤ t; w* = jüngste bekannte Woche.
- MA4(w) = Mittelwert der Erstveröffentlichungswerte v der Wochen w−3 … w.
- Basis(w*) = Minimum von MA4 über die 52 Wochen w*−52 … w*−1.
- C(t) = MA4(w*) / Basis(w*) − 1.
- C(t) ist nur definiert, wenn für alle Wochen w*−55 … w* Erstveröffentlichungen vorliegen
  (4 Wochen für MA4 + 52 Wochen Basis); sonst fehlt das Signal. Bei weniger als 52 Wochen
  Erstveröffentlichungshistorie gibt es kein Signal (kein Rückgriff auf revidierte Werte).
- Es werden stets die **Erstveröffentlichungswerte** früherer Wochen verwendet (nicht deren zum
  Zeitpunkt t schon revidierte Stände); alle verwendeten Werte waren an t veröffentlicht →
  kein Look-ahead.
- Ein neu veröffentlichter Wochenwert kann die Position frühestens am Handelstag **nach** seinem
  Archivierungsdatum beeinflussen.

**Zinskurve (Familien K, Z).** Bekannt an t: Beobachtungstage d, für die DGS10 **und** DGS3MO
(bzw. DGS2) Erstveröffentlichungen mit Archivierungsdatum ≤ t vorliegen; d* = jüngster solcher Tag.
- K(t) = DGS10_first(d*) − DGS3MO_first(d*); Z(t) = DGS10_first(d*) − DGS2_first(d*).

**Fehlende Signale:** Fehlt das Signal an t, bleibt die Position des Vortags (kein Auffüllen).

## 4. Regeln, Versuche, Eligibility

Nur **Overlay** (Position = 0 bei Risiko-aus, sonst Baseline-Position):

| Familie | Regel | Parameter | Auswahl |
|---|---|---|---|
| **A · Initial-Claims-Rezessionssignal** | Risiko-aus, wenn C(t) ≥ a | a ∈ {0,05; 0,10; 0,15} | im Entwicklungsfenster (Abschnitt 6) |
| **K · Zinskurve 10J−3M** | Risiko-aus, wenn K(t) < 0 | fest, keine Optimierung | – |
| **Z · Zinskurve 10J−2J** | Risiko-aus, wenn Z(t) < 0 | fest, keine Optimierung | – |

A ist konzeptionell an Schwellen-/Tiefpunkt-Rezessionsindikatoren angelehnt, entspricht aber
**nicht** der Sahm-Regel (diese nutzt die Arbeitslosenquote, 3-Monats-Mittel ggü. Minimum der
vorherigen 12 Monate). K und Z folgen der Standarddefinition der Inversion (Literatur u. a.
Estrella/Mishkin).

**Versuche:** 3 (A) + 1 (K) + 1 (Z) = **5**, alle vollständig protokolliert (beide Fenster).
Kumuliert mit früheren Kandidaten, H1 und H3: 5 + 16 + 16 + 5 = 42 (konservative Obergrenze,
Versuche nicht unabhängig).

**Eligibility (nur A):** Ein Parameter a ist nur dann **auswählbarer Kandidat**, wenn er im
Entwicklungsfenster an **mindestens 20 Handelstagen** Risiko-aus signalisiert. Die Regel
entscheidet nicht über Erfolg, sondern nur darüber, ob ein Parameter überhaupt als testbarer
Kandidat gilt; sie wird vor jeder Performanceauswertung mechanisch angewandt. Welche Werte
zugelassen werden, ist vor dem Lauf **nicht** bekannt (nur Wochenanteile wurden gezählt).
Für jede Schwelle a ∈ {0,05; 0,10; 0,15} wird **ausschließlich im festen Entwicklungsfenster**
gezählt, an wie vielen Handelstagen Risiko-aus signalisiert worden wäre:
- **≥ 20 Handelstage:** Schwelle ist zugelassen (eligible).
- **< 20 Handelstage:** Schwelle ist nicht zugelassen und nimmt an der Auswahl nicht teil.

Fälle:
- **3 zugelassen:** Auswahl nach Abschnitt 6 unter allen drei.
- **2 zugelassen:** Auswahl nach Abschnitt 6 zwischen diesen beiden.
- **1 zugelassen:** diese Schwelle ist der primäre A-Kandidat.
- **0 zugelassen:** H4-A wird als **„nicht auswertbar wegen unzureichender Signalaktivität“**
  dokumentiert; H4 gilt damit als **nicht bestätigt**. K und Z werden sekundär berichtet.

**Keine Erweiterung des Parameterraums:** Scheiden Schwellen aus, werden **keine weiteren
Schwellen ergänzt** – weder vor noch nach dem Lauf. Die gewählte Schwelle wird auch nicht
aufgrund der späteren Auslösung im Bestätigungsfenster verändert.

## 5. Zeitfenster

| Fenster | Zeitraum |
|---|---|
| Entwicklung (Auswahl von a, Eligibility) | 01.07.2010 – 30.12.2016 |
| Bestätigung (einmalig) | 03.01.2017 – 25.09.2026 |

Start 01.07.2010, weil das Claims-Signal (55 Wochen Erstveröffentlichungshistorie) erst ab
Beobachtung 19.06.2010 gültig ist. Baseline und alle Varianten auf **exakt denselben
Handelstagen**, mit derselben Baseline-Positionsreihe, denselben Renditen und Kosten. Jedes Fenster
startet mit Position 0 und Kapital 1. Die Auswahl wird vor Auswertung des Bestätigungsfensters in
`results/phase3/H4_auswahl.json` geschrieben und danach nicht überschrieben.

## 6. Auswahl und primärer Kandidat

- **A:** unter den zugelassenen Werten die höchste Calmar-Ratio im Entwicklungsfenster (5 Bp
  Kosten); Gleichstand (< 0,01) → größeres a (konservativer). Danach eingefroren.
- **K, Z:** keine Auswahl.
- **Primäre Hypothesenfamilie: A** (vorab festgelegt, ohne Wirkungsannahme). Initial Claims sind
  ein direkter, hochfrequenter Arbeitsmarktindikator. Ihre Kandidatenschwellen werden anhand der
  vorab definierten Mindestaktivität von ≥ 20 Handelstagen im Entwicklungsfenster auf Eligibility
  geprüft (Abschnitt 4). K und Z werden sekundär als nicht optimierte, literaturbasierte
  Makro-Overlays untersucht.
- Keine Ersatzauswahl: Scheitert A, tritt weder K noch Z an seine Stelle – auch dann nicht, wenn
  K oder Z im Bestätigungsfenster das Kriterium erfüllen.

## 7. Kennzahlen und Kosten

Identisch zu H1/H3 (Abschnitt 7 dort): r_t = Pos_(t−1) × Rendite_t − 5 Bp × |ΔPos|; CAGR;
Max Drawdown auf Tagesschlusskursen inkl. Kosten; Calmar = CAGR/|Max DD| (negativ zulässig);
Sharpe (rf 2 %), CVaR 5 %, Ulcer nur berichtet; Kosten-Sensitivität 0 und 10 Bp.

## 8. Stressphasen (unverändert H1/H3)

Entwicklung (im Fenster): US-Downgrade 2011 (22.07.–03.10.2011), China/August 2015
(17.08.–30.09.2015). Flash Crash 2010 und Finanzkrise 2008 liegen vor dem Fensterbeginn.
Bestätigung: Volmageddon 2018 (26.01.–09.02.2018), 2018 Q4 (01.10.–24.12.2018), Covid 2020
(19.02.–23.03.2020), Bärenmarkt 2022 (03.01.–12.10.2022), Yen-Carry 2024 (16.07.–07.08.2024).
Periodenrendite = E am Enddatum / E am Handelstag vor Anfangsdatum − 1.

## 9. Erfolgskriterium und Entscheidung (Bestätigungsfenster, 5 Bp)

Gegenüber der Baseline: Max Drawdown **≥ 3 Prozentpunkte besser** **und** Calmar ≥ Baseline
**und** in **≥ 4 von 5** Bestätigungs-Stressphasen nicht schlechter (Toleranz 0,5 Prozentpunkte).
- **H4 bestätigt** genau dann, wenn der primäre Kandidat A dieses Kriterium erfüllt. Ist A nach
  Abschnitt 4 nicht auswertbar, gilt H4 als nicht bestätigt (Begründung: unzureichende
  Signalaktivität), nicht als widerlegt.
- K und Z werden mit demselben Kriterium sekundär berichtet („x von 2“) und ändern die
  Entscheidung nicht.

## 9a. Informationsmehrwert (getrennt, wie H3)

Kennzahl M = Anteil der Risiko-aus-Tage im Bestätigungsfenster, an denen die Baseline-Position
(Signal desselben Tages) > 0 ist; Überlappung = 1 − M. Überlappung ≥ 80 % → „zusätzlicher
Informationsgehalt begrenzt“, sonst „eigenständige Entscheidungen in nennenswertem Umfang“.
Für A, K, Z in beiden Fenstern berichtet; unabhängig von der Entscheidung in Abschnitt 9.

## 10. Zusätzlich berichtet

Alle 5 Versuche in beiden Fenstern (inkl. nicht zugelassener A-Werte, gekennzeichnet),
Eligibility-Zählung je a, Anzahl und Dauer der Risiko-aus-Phasen, Zeit im Markt, Trades,
Kosten-Sensitivität, Max-Drawdown-Analyse (Hoch/Tief/Erholung) für A und Baseline.
