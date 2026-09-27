# Präregistrierung H3 – Implied Correlation (COR1M) als zusätzliche Informationsachse

**Rev. 2** · 27.09.2026 · **vor** jeder Auswertung · Roadmap Phase 3, Hypothese H3
(Rev. 2 nach externem Review: Familie B mathematisch präzisiert mit Rechenbeispiel;
Informationsmehrwert/Redundanz vollständig vom Erfolgskriterium getrennt)
(UIQ-Suite `docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md`)

Architektur identisch zu H1 (`H1_laufzeit_gate.md`, Rev. 3, Commit `8e05c0a`). Dieses Dokument
wird committet, **bevor** der Test läuft. Änderungen nach dem Test nur als neue, separat
nummerierte Hypothese (z. B. H3b), die bei n_trials mitzählt.

## 1. Fragestellung

Liefert die implizite Korrelation der größten S&P-500-Werte **zusätzliche, außerhalb der
Entwicklungsdaten reproduzierbare Information** gegenüber der bestehenden Baseline – oder nur
eine andere Darstellung desselben Volatilitätsrisikos?

Erfolg heißt ausschließlich: vorab definierter **inkrementeller Nutzen gegenüber der
unveränderten Baseline im Bestätigungsfenster** (Abschnitt 9). Höherer Sharpe oder höhere CAGR
allein sind kein Erfolg. Eine starke Redundanz mit bestehenden Signalen ist ein
eigenständiges, berichtetes Ergebnis (Abschnitt 10).

## 2. Daten, Datenquelle und Datenverfügbarkeit

- **COR1M** = Cboe 1-Month Implied Correlation Index (erwartete durchschnittliche Korrelation
  der größten S&P-500-Werte über 1 Monat, aus Index- und Einzeloptionen). Quelle:
  `https://cdn.cboe.com/api/global/us_indices/daily_prices/COR1M_History.csv`, Snapshot
  `data/raw/cboe/2026-09-27/` (SHA-256 geprüft), Schlusskurs (CLOSE).
- VIX, VIX3M aus demselben Snapshot; S&P-500-Renditen aus `data/raw/yahoo/2026-09-27/GSPC.csv`.
- NYSE-Kalender, **kein Forward-Fill, keine Proxies**. Verfügbarkeit: 03.01.2006 – 25.09.2026,
  keine Lücken im Kalender (QC Phase 1). Keine Serien gleicher Schlusskurse (> 1 Tag).
- **Daten-Vintage (wesentliche Einschränkung):** COR1M enthält bis **17.03.2022** ausschließlich
  Schlusskurse (O = H = L = C), ab 18.03.2022 echtes OHLC. Die Historie vor 03/2022 ist daher sehr
  wahrscheinlich **nachträglich von Cboe berechnet** (aus zeitgleichen Optionspreisen, nach
  heutiger Methodik). Das betrifft das gesamte Entwicklungsfenster **und** den Teil 2017 –
  03/2022 des Bestätigungsfensters. Deshalb wird zusätzlich das **Live-Teilfenster
  18.03.2022 – 25.09.2026** berichtet (sekundär, nicht entscheidungsrelevant, Abschnitt 10).
- **Nicht-Stationarität:** Jahresmedian COR1M 2010: 61,5 · 2017: 18,9 · 2022: 44,8 · 2026: 10,5
  → feste Niveauschwellen sind ungeeignet; es werden ausschließlich **rollierende Perzentile**
  verwendet (Abschnitt 3).
- **Redundanz, vor Festlegung der Regeln ermittelt (deskriptiv, ohne Renditebezug, nur
  Entwicklungsfenster 18.09.2009 – 30.12.2016):** Spearman ρ(COR1M, VIX) = 0,845;
  ρ(5-Tages-Änderungen COR1M, VIX) = 0,759; ρ(COR1M, VIX3M/VIX) = −0,516. Wegen der hohen
  Niveau-Redundanz wird neben der Rohregel (Familie A) eine Regel getestet, die nur den über die
  Volatilität hinausgehenden Teil nutzt (Familie B).

## 3. Signale und Regeln (Form fest)

**Perzentil** P_X(t) für eine Reihe X: Anteil der Werte der letzten 252 Handelstage einschließlich
t, die ≤ X(t) sind. Gültig nur mit ≥ 227 vorhandenen Werten (90 %), sonst fehlend. Nutzt nur
Daten bis einschließlich t (kein Look-ahead). Lookback 252 fest (nicht optimiert).

- **Familie A (Rohsignal):** Risiko-aus, wenn P_COR1M(t) ≥ q.
- **Familie B (Zusatzachse):** Risiko-aus, wenn **D(t) = P_COR1M(t) − P_VIX(t) ≥ d**.
  D(t) ist die **Differenz zweier Perzentilränge am selben Handelstag t**, beide nach obiger
  Definition über dasselbe 252-Tage-Fenster [t−251, t] berechnet. Es wird **keine Veränderung
  über die Zeit**, kein Verhältnis und keine weitere Glättung verwendet. D(t) liegt in [−1, +1].
  Die Schwelle d stammt ausschließlich aus dem Raster in Abschnitt 4 und wird nur im
  Entwicklungsfenster gewählt (Abschnitt 6). Fehlt P_COR1M(t) oder P_VIX(t), fehlt D(t).
  *Rechenbeispiel:* COR1M(t) ist höher als 225 der **übrigen 251** Werte seines Fensters; mit
  dem eigenen Wert (≤ zählt) sind 226 von 252 Werten ≤ COR1M(t) → P_COR1M = 226/252 = 0,897.
  VIX(t) ist höher als 125 der übrigen 251 Werte → P_VIX = 126/252 = 0,500.
  D = 0,397 → Risiko-aus für d ∈ {0,10; 0,20; 0,30}, nicht für d = 0,40.

Anwendung (Position von Tag t gilt ab t+1):

- **H3-S (eigenständig):** Position = 0 bei Risiko-aus, sonst 1.
- **H3-O (Overlay):** Position = 0 bei Risiko-aus, sonst Baseline-Position.
- **Baseline (unveränderlich):** wie H1 – `classify_regime_v2()` / `regime_to_position_uniform()`
  aus `compare_approaches_final_v2.py`, gex = None, VIX/VIX3M aus demselben Snapshot, Stand
  Commit `cfcab55`. Für H3-O werden Baseline und alle Overlay-Varianten auf **exakt denselben
  Handelstagen** mit derselben Baseline-Positionsreihe, denselben Renditen und Kosten gerechnet.

Nicht getestet (bewusst, zur Begrenzung der Versuche): Signale bei *niedriger* Korrelation
(Dispersion), andere Laufzeiten (COR3M/6M/1Y), andere Lookbacks.

## 4. Versuche und Protokoll

Familie A: q ∈ {0,80; 0,85; 0,90; 0,95} · Familie B: d ∈ {0,10; 0,20; 0,30; 0,40}
× {S, O} = **16 Versuche**. Alle 16 werden in beiden Fenstern vollständig protokolliert
(`results/phase3/H3_*.json`, `.md`), auch erfolglose. Je (Familie, Variante) wird im
Entwicklungsfenster ein Parameter gewählt → 4 Kandidaten (S-A, S-B, O-A, O-B); genau einer ist
**primär** (Abschnitt 6). n_trials = 16 (nicht unabhängig, konservative Obergrenze); kumuliert
mit früheren Kandidaten und H1: 5 + 16 + 16 = 37.

## 5. Zeitfenster

| Fenster | H3-S | H3-O |
|---|---|---|
| Entwicklung (Auswahl) | 03.01.2007 – 30.12.2016 | 18.09.2009 – 30.12.2016 |
| Bestätigung (einmalig) | 03.01.2017 – 25.09.2026 | 03.01.2017 – 25.09.2026 |
| Live-Teilfenster (nur berichtet) | 18.03.2022 – 25.09.2026 | 18.03.2022 – 25.09.2026 |

H3-O beginnt am 18.09.2009, weil die Baseline VIX3M benötigt (Beginn der Cboe-Historie).
Perzentile sind ab 22.11.2006 gültig; H3-S startet deshalb einheitlich am 03.01.2007.
Jedes Fenster startet mit Position 0 und Kapital 1; Buy & Hold und Baseline im jeweils
identischen Fenster. Die Auswahl wird vor Auswertung des Bestätigungsfensters in
`results/phase3/H3_auswahl.json` geschrieben und danach nicht überschrieben.

## 6. Auswahlregel (nur Entwicklungsfenster)

Je (Familie, Variante) der Parameter mit der **höchsten Calmar-Ratio** nach 5 Bp Kosten.
Gleichstand (Differenz < 0,01) → der **konservativere** Parameter (größeres q bzw. größeres d =
seltener Risiko-aus). Auch bei durchweg negativer CAGR wird der beste Wert gewählt.

**Primärer Kandidat:** unter O-A und O-B der mit höherer Calmar-Ratio im Entwicklungsfenster
(identisches Fenster, direkt vergleichbar). Gleichstand (< 0,01) → **O-B**, weil O-B die
Fragestellung (zusätzliche Information über die Volatilität hinaus) direkt prüft.
Keine Ersatzauswahl: scheitert der primäre Kandidat, tritt kein anderer an seine Stelle.

## 7. Kennzahl-Definitionen

Identisch zu H1 Abschnitt 7: r_t = Pos_(t−1) × Rendite_t − Kosten_t; Kosten 5 Bp × |ΔPos|
(Sensitivität 0 / 10 Bp); CAGR = E_N^(252/N) − 1; Max Drawdown auf Tagesschlusskursen inkl.
Kosten; Calmar = CAGR / |Max DD| (negative CAGR → negative Calmar, so verglichen); Sharpe mit
rf 2 % p. a. (nur berichtet); CVaR 5 %; Ulcer-Index. Fehlendes Signal an Tag t → Vortagsposition.

## 8. Stressphasen (fest, identisch zu H1)

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

## 9. Erfolgskriterien und Entscheidung (Bestätigungsfenster, nach 5 Bp Kosten)

- **O-Kandidaten:** gegenüber der Baseline Max Drawdown ≥ 3 Prozentpunkte besser **und**
  Calmar ≥ Baseline **und** in ≥ 4 von 5 Bestätigungs-Stressphasen nicht schlechter
  (Toleranz 0,5 Prozentpunkte).
- **S-Kandidaten:** Max Drawdown ≥ 10 Prozentpunkte besser als Buy & Hold **und**
  Calmar > Buy & Hold.
- **Entscheidung:** H3 **bestätigt** genau dann, wenn der **primäre** Kandidat sein Kriterium
  erfüllt. Sekundäre Kandidaten werden als „x von 3“ berichtet und ändern die Entscheidung nicht.
- Die Entscheidung über H3 hängt **ausschließlich** von diesem Primärkriterium ab. Der
  Informationsmehrwert (Abschnitt 9a) ist eine **getrennte Fragestellung** und verändert die
  Entscheidung nicht.

## 9a. Informationsmehrwert (getrennt vom Erfolgskriterium, vorab definiert)

Frage: Trifft COR1M **eigene** Entscheidungen, oder bestätigt es nur, was die Baseline ohnehin tut?

- **Kennzahl M (eigenständige Ausstiege):** Anteil der Risiko-aus-Tage des primären Kandidaten
  im Bestätigungsfenster, an denen die Baseline-Position (Signal desselben Tages t) **> 0** ist.
  Überlappung = 1 − M.
- **Feststellung:** Überlappung ≥ 80 % (M ≤ 20 %) → Bericht stellt fest: „zusätzlicher
  Informationsgehalt von COR1M gegenüber der Baseline begrenzt“. Überlappung < 80 % →
  „COR1M trifft in nennenswertem Umfang eigenständige Entscheidungen“.
- M wird zusätzlich für alle 4 gewählten Kandidaten, im Entwicklungsfenster und im
  Live-Teilfenster berichtet.
- Die Feststellung wird **unabhängig** vom Ergebnis des Primärkriteriums getroffen und
  gemeinsam mit diesem berichtet (vier mögliche Kombinationen: wirksam/nicht wirksam ×
  eigenständig/begrenzt).

## 10. Zusätzlich berichtet (nicht entscheidungsrelevant)

- **Redundanz auf Niveauebene (deskriptiv):** Spearman ρ(COR1M, VIX), ρ(ΔCOR1M, ΔVIX)
  (5-Tages-Änderungen), ρ(COR1M, VIX3M/VIX) in Entwicklungs- und Bestätigungsfenster;
  Kennzeichnung „hoch redundant auf Niveauebene“ bei ρ ≥ 0,80. Diese Werte dienen nur der
  Beschreibung, nicht dem Erfolgskriterium.
- **Live-Teilfenster** 18.03.2022 – 25.09.2026 für alle 4 gewählten Kandidaten und Baseline.
- Sharpe, CVaR 5 %, Ulcer, Zeit im Markt, Trades, Kosten-Sensitivität, Stressphasen des
  Entwicklungsfensters, alle 16 Versuche in beiden Fenstern.
- Fehleranalyse des maximalen Drawdowns (Hoch, Tief, Erholung) für primären Kandidaten und
  Baseline – insbesondere 2022 (Anschluss an H1-Befund).
