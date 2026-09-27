# H4 – Makro-Achse (Initial Claims, Zinskurve) · Ergebnis

Präregistrierung: `docs/preregistration/H4_makro_achse.md` Rev. 2 (sha256 `d6db37c81941…`, Commit `dc6df73`)

## Entscheidung: **H4 nicht bestätigt**

### Eligibility A (Risiko-aus-Handelstage im Entwicklungsfenster, Mindestwert 20)

| Schwelle | Tage | zugelassen |
|---|---|---|
| A-0.05 | 546 | ✅ |
| A-0.10 | 129 | ✅ |
| A-0.15 | 10 | ❌ |

Primärer Kandidat: **A-0.05** · Status A: auswertbar

### Urteile Bestätigungsfenster (gegen Baseline, 5 Bp)

| Signal | Rolle | DD-Verbesserung | Calmar | Calmar Baseline | Stress nicht schlechter | Kriterium |
|---|---|---|---|---|---|---|
| A-0.05 | **primär** | +8.3 Pp | 0.147 | 0.429 | 5 von 5 | ❌ |
| A-0.10 | nicht gewählt | +2.8 Pp | 0.212 | 0.429 | 5 von 5 | ❌ |
| A-0.15 | nicht zugelassen | +4.8 Pp | 0.364 | 0.429 | 5 von 5 | ❌ |
| K | sekundär | +0.0 Pp | 0.193 | 0.429 | 5 von 5 | ❌ |
| Z | sekundär | +4.4 Pp | 0.358 | 0.429 | 5 von 5 | ❌ |

Sekundär (K, Z) erfüllt: **0 von 2** – ändern die Entscheidung nicht.

## Informationsmehrwert (getrennt, Abschnitt 9a)

**Primär: eigenständige Entscheidungen in nennenswertem Umfang.**

| Signal | Fenster | Risiko-aus-Tage | Phasen | mittl. Dauer | M | Überlappung |
|---|---|---|---|---|---|---|
| A-0.05 | dev | 546 | 19 | 28.7 | 94% | 6% |
| A-0.05 | conf | 1565 | 17 | 92.1 | 94% | 6% |
| A-0.10 | dev | 129 | 7 | 18.4 | 100% | 0% |
| A-0.10 | conf | 965 | 19 | 50.8 | 96% | 4% |
| A-0.15 | dev | 10 | 2 | 5.0 | 100% | 0% |
| A-0.15 | conf | 676 | 10 | 67.6 | 95% | 5% |
| K | dev | 0 | 0 | 0 | – | – |
| K | conf | 742 | 27 | 27.5 | 96% | 4% |
| Z | dev | 0 | 0 | 0 | – | – |
| Z | conf | 546 | 5 | 109.2 | 99% | 1% |

## Max-Drawdown-Analyse Bestätigungsfenster

- baseline: -24.6% · Hoch 2022-01-03 → Tief 2022-10-12 → erholt 2024-01-23
- A-0.05: -16.3% · Hoch 2022-01-03 → Tief 2026-03-31 → erholt 2026-08-04

## Entwicklungsfenster 01.07.2010 – 30.12.2016

| Signal | Zeitraum | CAGR | Max DD | Calmar | Sharpe | CVaR 5 % | Ulcer | im Markt | Trades | US-Downgrade 2011 | China / August 2015 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2010-07-01 – 2016-12-30 | +9.8% | -21.5% | 0.454 | 0.63 | -1.96% | 0.054 | 96% | 80 | -20.1% | -10.4% |
| A-0.05 ◀ primär | 2010-07-01 – 2016-12-30 | +9.8% | -11.5% | 0.852 | 0.79 | -1.57% | 0.030 | 64% | 71 | +0.0% | -10.4% |
| A-0.10 | 2010-07-01 – 2016-12-30 | +8.0% | -21.5% | 0.372 | 0.51 | -1.95% | 0.055 | 88% | 94 | -20.1% | -10.4% |
| A-0.15 | 2010-07-01 – 2016-12-30 | +9.8% | -21.5% | 0.454 | 0.63 | -1.96% | 0.054 | 95% | 84 | -20.1% | -10.4% |
| K | 2010-07-01 – 2016-12-30 | +9.8% | -21.5% | 0.454 | 0.63 | -1.96% | 0.054 | 96% | 80 | -20.1% | -10.4% |
| Z | 2010-07-01 – 2016-12-30 | +9.8% | -21.5% | 0.454 | 0.63 | -1.96% | 0.054 | 96% | 80 | -20.1% | -10.4% |

## Bestätigungsfenster 2017–2026

| Signal | Zeitraum | CAGR | Max DD | Calmar | Sharpe | CVaR 5 % | Ulcer | im Markt | Trades | Volmageddon 2018 | 2018 Q4 | Covid 2020 | Bärenmarkt 2022 | Yen-Carry 2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 2017-01-03 – 2026-09-25 | +10.6% | -24.6% | 0.429 | 0.67 | -2.11% | 0.082 | 95% | 162 | -6.8% | -12.9% | -7.2% | -24.1% | -7.9% |
| A-0.05 ◀ primär | 2017-01-03 – 2026-09-25 | +2.4% | -16.3% | 0.147 | 0.09 | -1.26% | 0.110 | 35% | 64 | -6.8% | -9.1% | -4.3% | -12.7% | +0.0% |
| A-0.10 | 2017-01-03 – 2026-09-25 | +4.6% | -21.8% | 0.212 | 0.31 | -1.71% | 0.095 | 57% | 98 | -6.8% | -11.3% | -4.3% | -15.1% | +0.0% |
| A-0.15 | 2017-01-03 – 2026-09-25 | +7.2% | -19.8% | 0.364 | 0.53 | -1.79% | 0.069 | 69% | 90 | -6.8% | -12.9% | -4.3% | -10.6% | +0.0% |
| K | 2017-01-03 – 2026-09-25 | +4.8% | -24.6% | 0.193 | 0.30 | -1.91% | 0.135 | 66% | 186 | -6.8% | -12.9% | -2.6% | -24.1% | +0.0% |
| Z | 2017-01-03 – 2026-09-25 | +7.2% | -20.2% | 0.358 | 0.50 | -1.95% | 0.098 | 73% | 157 | -6.8% | -12.9% | -7.2% | -14.6% | +0.0% |

## Kosten-Sensitivität Bestätigungsfenster

| Fall | CAGR | Max DD | Calmar |
|---|---|---|---|
| A-0.05 0Bp | +2.7% | -15.5% | 0.175 |
| A-0.05 10Bp | +2.1% | -17.1% | 0.122 |
| K 0Bp | +5.5% | -23.8% | 0.232 |
| K 10Bp | +4.0% | -25.9% | 0.154 |
| Z 0Bp | +7.9% | -18.9% | 0.417 |
| Z 10Bp | +6.6% | -21.7% | 0.304 |
| baseline 0Bp | +11.2% | -23.8% | 0.472 |
| baseline 10Bp | +9.9% | -25.4% | 0.390 |

## Signal-Timing (Kontrolle)

- Claims-Signal gültig ab Beobachtung 2010-06-19; Median-Alter der jüngsten bekannten Woche: 9 Kalendertage
- Kurve 10J−3M / 10J−2J: Median-Alter des jüngsten bekannten Beobachtungstags 1 / 1 Kalendertage

## Einschränkungen

- Verfügbarkeitsdatum = ALFRED-Archivierungsdatum (konservativ). Claims-Signal nutzt Erstveröffentlichungen früherer Wochen, nicht deren zum Zeitpunkt t revidierte Stände.
- Große historische Episoden waren dem Designer bekannt (Transparenzhinweis Präregistrierung).
- Preisindex ohne Dividenden; Cash unverzinst. n_trials kumuliert 42 (konservativ); DSR in Phase 4.
