# Präregistrierung H1 – Laufzeit-Gate (VIX6M/VIX, VIX1Y/VIX)

**Festgelegt:** 27.09.2026, **vor** jeder Auswertung · Roadmap Phase 3, Hypothese H1
(UIQ-Suite `docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md`)
**Revision 2** (27.09.2026, vor Commit und vor jeder Auswertung): Präzisierungen nach externem
Review – Datenverfügbarkeit, Versuchsprotokoll, feste Stressphasen, Kennzahl-Definitionen.
**Revision 3** (27.09.2026, vor Commit und vor jeder Auswertung): ein vorab bestimmter
**primärer Kandidat**; übrige Kandidaten nur sekundär; keine Ersatzauswahl.

Dieses Dokument wird committet, **bevor** der Test läuft. Änderungen nach dem Test sind nur als
neue, separat nummerierte Hypothese zulässig (z. B. H1b) und zählen bei n_trials mit.

## 1. Fragestellung

Verbessert eine Inversion der längeren Vol-Laufzeitstruktur (VIX6M/VIX bzw. VIX1Y/VIX unter
Schwelle t) den **Drawdown-/Tail-Schutz** – (S) eigenständig gegenüber Buy & Hold inkl. 2008,
(O) als Zusatzfilter zur bestehenden Baseline `classify_regime_v2()`?

Motivation aus Phase 2: Die Baseline schützt bei langsamen Stressphasen (Covid, 2018 Q4, 2022),
aber nicht bei schnellen Schocks (2011, 08/2015, 08/2024); ihre VIX3M-Historie beginnt erst
18.09.2009, 2008 ist nicht abgedeckt.

## 2. Daten und Datenverfügbarkeit

- Snapshot `data/raw/cboe/2026-09-27/` (SHA-256 geprüft, `SHA256SUMS.txt`), NYSE-Kalender,
  kein Forward-Fill, **keine Proxies** (kein Ersatz von VIX6M/VIX1Y durch andere Reihen).
- S&P-500-Renditen: `data/raw/yahoo/2026-09-27/GSPC.csv` (Close, Preisindex, ohne Dividenden).
- Verfügbarkeit laut Snapshot: VIX1Y ab 03.01.2007, VIX6M ab 02.01.2008, beide bis 25.09.2026.
- **Fehlende Werte werden nicht aufgefüllt.** Fehlt R an Tag t (z. B. VIX1Y an Columbus/Veterans
  Day: 6 Tage 2007–2009), bleibt die Position des Vortags unverändert; es entsteht kein Signal.
- Prüfung vor dem Test: keine Serien gleicher Schlusskurse an Folgetagen (längste Serie = 1)
  → kein Hinweis auf Forward-Fill in den Rohdaten.
- **Einschränkung (Daten-Vintage):** VIX1Y enthält bis ca. Mitte 2017 und VIX6M bis 26.11.2013
  ausschließlich Schlusskurse (O = H = L = C). Das deutet auf **nachträglich von Cboe berechnete
  Historie** hin (aus zeitgleichen Optionspreisen, nach heutiger Methodik). Die Werte enthalten
  damit keine späteren Kursinformationen, waren aber zum jeweiligen Zeitpunkt vermutlich **nicht
  in Echtzeit beobachtbar**. H1 ist für diese Zeiträume daher ein Methodentest, kein Nachweis
  einer damals umsetzbaren Strategie. Das Ergebnis im Bestätigungsfenster (ab 2017) ist davon
  weitgehend frei (VIX6M vollständig live, VIX1Y ab Mitte 2017 mit Intraday-Daten).
- Deskriptiv (vor dem Test ermittelt, ohne Renditebezug): Anteil Tage mit R < 1,00:
  VIX6M/VIX 9,3 %, VIX1Y/VIX 11,2 %.

## 3. Regeln (Form fest, einziger Parameter t)

R = VIX_L / VIX am Schluss von Tag t, L ∈ {6M, 1Y}; Position gilt ab Tag t+1
(Rendite von Tag t+1 = Close(t+1)/Close(t) − 1).

- **H1-S (eigenständig):** Position = 1, wenn R ≥ t, sonst 0.
- **H1-O (Overlay):** Position = Baseline-Position, wenn R ≥ t, sonst 0.
- **Baseline (unveränderlich):** Variante E aus Phase 2 – `classify_regime_v2()` und
  `regime_to_position_uniform()` aus `compare_approaches_final_v2.py`, gex = None, VIX und VIX3M
  aus demselben Snapshot, Stand Commit `cfcab55`. Die Baseline wird für H1-O in jedem Versuch
  identisch berechnet und nicht verändert.

## 4. Versuche und Protokoll

t ∈ {0,95; 1,00; 1,05; 1,10} × L ∈ {6M, 1Y} × {S, O} = **16 Versuche**.

- **Alle 16 Versuche werden vollständig protokolliert** (Entwicklungs- und Bestätigungsfenster,
  alle Kennzahlen aus Abschnitt 7 und 8), auch erfolglose, in `results/phase3/H1_*.json` und `.md`.
- Je (L, Variante) wird im Entwicklungsfenster eine Schwelle gewählt → 4 Kandidaten
  (S-6M, S-1Y, O-6M, O-1Y). Davon wird **genau einer als primärer Kandidat** bestimmt
  (Abschnitt 6); nur er entscheidet über H1. Die übrigen drei sind **sekundär**.
- Die Versuche sind **nicht unabhängig** (gleiche Marktdaten, benachbarte Schwellen). n_trials = 16
  ist daher eine konservative Obergrenze für die Deflated Sharpe Ratio in Phase 4
  (zusätzlich 5 frühere Kandidaten → gesamt 21).

## 5. Zeitfenster

| Fenster | H1-S | H1-O |
|---|---|---|
| Entwicklung (Auswahl von t) | Datenbeginn L (VIX1Y 03.01.2007 / VIX6M 02.01.2008) – 30.12.2016 | 18.09.2009 – 30.12.2016 |
| Bestätigung (einmalig) | 03.01.2017 – 25.09.2026 | 03.01.2017 – 25.09.2026 |

**Warum H1-O erst ab 18.09.2009:** Die Baseline benötigt VIX3M; die Cboe-VIX3M-Historie im
Snapshot beginnt am 18.09.2009. Für H1-O werden daher **Baseline, O-6M und O-1Y auf exakt
denselben Handelstagen** (18.09.2009 – 30.12.2016 bzw. 03.01.2017 – 25.09.2026) berechnet,
mit derselben Baseline-Positionsreihe, denselben Renditen und denselben Kosten. Die Jahre
2007/2008 gehen nur in H1-S ein (sekundär). Der Ausdruck „Entwicklungsfenster 2007–2016“ meint
somit für H1-S den Beginn der jeweiligen Reihe, für H1-O den 18.09.2009.

Jedes Fenster startet mit Position 0 und Kapital 1; die erste Position wird aus dem Signal des
ersten Fenstertags gebildet (gilt ab Tag 2). Buy & Hold und Baseline im **jeweils identischen**
Fenster. Die gewählten t werden vor Auswertung des Bestätigungsfensters in
`results/phase3/H1_auswahl.json` geschrieben.

## 6. Auswahlregel (nur Entwicklungsfenster)

Je (L, Variante) das t mit der **höchsten Calmar-Ratio** nach 5 Bp Kosten (Definition Abschnitt 7).
**Gleichstand:** Unterschied < 0,01 in der Calmar-Ratio → das **größere t** (konservativer).
Hat kein t eine positive CAGR, wird trotzdem das t mit der höchsten Calmar-Ratio gewählt
(weniger negativ ist besser).

**Primärer Kandidat:** Unter den beiden Overlay-Kandidaten (O-6M, O-1Y) derjenige mit der
höheren Calmar-Ratio im Entwicklungsfenster (18.09.2009 – 30.12.2016, identisch für beide,
daher direkt vergleichbar). Gleichstand (Differenz < 0,01) → **O-6M** (längere
Live-Verfügbarkeit, geringeres Daten-Vintage-Risiko).
Begründung: H1-O beantwortet die operative Frage (verbessert der Filter die bestehende Logik?).
H1-S hat andere Fenster und eine andere Benchmark und ist daher nicht direkt mit H1-O
vergleichbar; H1-S dient als sekundäre Evidenz, insbesondere für 2008.
Der primäre Kandidat wird zusammen mit den gewählten t in `results/phase3/H1_auswahl.json`
geschrieben, **bevor** das Bestätigungsfenster ausgewertet wird.

## 7. Kennzahl-Definitionen

- Tagesrendite Strategie: r_t = Position_(t−1) × Rendite_t − Kosten_t
- **Kosten:** 5 Bp × |Position_t − Position_(t−1)| (Hauptrechnung); Sensitivität 0 und 10 Bp.
- Equity: E_t = ∏ (1 + r_i), E_0 = 1
- **CAGR:** E_N^(252/N) − 1, N = Anzahl Handelstage im Fenster
- **Max Drawdown:** min_t (E_t / max_(s≤t) E_s − 1), auf Tagesschlusskursen, inkl. Kosten
- **Calmar-Ratio:** CAGR / |Max Drawdown|. Negative CAGR ergibt eine negative Calmar-Ratio und
  wird so verglichen (jede positive schlägt jede negative). Max Drawdown = 0 ist nicht definiert
  und schließt den Versuch aus (tritt bei den Regeln praktisch nicht auf).
- Sharpe (nur berichtet): √252 × Mittel(r − 0,02/252) / Stdabw(r − 0,02/252), wie Phase 2.
- CVaR 5 %: Mittelwert der schlechtesten 5 % Tagesrenditen. Ulcer-Index: √(Mittel(DD_t²)).

## 8. Stressphasen (fest, inklusive Anfangs- und Enddatum)

Periodenrendite = E am Enddatum / E am Handelstag vor dem Anfangsdatum − 1.

| Phase | Anfang | Ende | Fenster |
|---|---|---|---|
| Finanzkrise 2008 | 2008-09-01 | 2009-03-09 | Entwicklung |
| Flash Crash / Euro 2010 | 2010-04-23 | 2010-07-02 | Entwicklung |
| US-Downgrade 2011 | 2011-07-22 | 2011-10-03 | Entwicklung |
| China / August 2015 | 2015-08-17 | 2015-09-30 | Entwicklung |
| Volmageddon 2018 | 2018-01-26 | 2018-02-09 | Bestätigung |
| 2018 Q4 | 2018-10-01 | 2018-12-24 | Bestätigung |
| Covid 2020 | 2020-02-19 | 2020-03-23 | Bestätigung |
| Bärenmarkt 2022 | 2022-01-03 | 2022-10-12 | Bestätigung |
| Yen-Carry 2024 | 2024-07-16 | 2024-08-07 | Bestätigung |

Die Bestätigungs-Stressphasen stimmen mit `run_phase2_baseline.py` (Commit `cfcab55`) überein und
wurden vor jeder H1-Auswertung festgelegt. Weitere Phasen dürfen nachträglich nur berichtet,
nicht für die Entscheidung verwendet werden.

## 9. Erfolgskriterien (Bestätigungsfenster, nach 5 Bp Kosten)

- **H1-S bestätigt**, wenn Max Drawdown um **≥ 10 Prozentpunkte** besser als Buy & Hold **und**
  Calmar-Ratio > Calmar-Ratio Buy & Hold.
- **H1-O bestätigt**, wenn gegenüber der Baseline (gleiches Fenster, gleiche Kosten)
  Max Drawdown um **≥ 3 Prozentpunkte** besser **und** Calmar-Ratio ≥ Baseline **und** in
  mindestens **4 von 5** Bestätigungs-Stressphasen (Abschnitt 8) nicht schlechter als die
  Baseline (Toleranz 0,5 Prozentpunkte Periodenrendite).

Alles andere gilt als **nicht bestätigt** – auch wenn Sharpe oder Rendite besser sind.

**Entscheidung über H1:**
- **Primär:** H1 gilt als **bestätigt** genau dann, wenn der primäre Kandidat (Abschnitt 6) das
  Kriterium für H1-O erfüllt; andernfalls als **nicht bestätigt**.
- **Sekundär:** Die übrigen drei Kandidaten werden mit demselben Kriterium (S gegen Buy & Hold,
  O gegen Baseline) vollständig berichtet, als „x von 3 sekundären Kandidaten erfüllt“. Sie
  ändern die Primärentscheidung nicht.
- **Keine Ersatzauswahl:** Scheitert der primäre Kandidat, darf kein anderer Kandidat
  nachträglich an seine Stelle treten. Ein auffälliges sekundäres Ergebnis kann nur als neue,
  separat präregistrierte Hypothese (z. B. H1b) mit neuem Bestätigungsdesign weiterverfolgt werden.
- Die Berichtsformulierung nennt stets den primären Kandidaten (L, t), sein Ergebnis und die
  Zahl der geprüften Kandidaten (1 primär + 3 sekundär, aus 16 Versuchen).

## 10. Zusätzlich berichtet (nicht entscheidungsrelevant)

Sharpe, CVaR 5 %, Ulcer-Index, Zeit im Markt, Trades, Kosten-Sensitivität (0 / 10 Bp),
Stressphasen des Entwicklungsfensters sowie alle 16 Versuche in beiden Fenstern.
