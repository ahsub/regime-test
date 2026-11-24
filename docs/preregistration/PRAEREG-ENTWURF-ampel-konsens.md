# Präregistrierungsentwurf: Ampel-Konsens als Markttiming-Gate (Kandidat H-FIN-4)

**Status:** Entwurf, kein Code. Geparkt bis nach Phase 4, wie H5/H6/H18. Endgültige H-Nummer erst beim Freeze.
**Ablage:** `ahsub/regime-test/docs/preregistration/` (ohne Tickernamen)
**Quelle:** Video eines Finfluencers (Nov 2026, Solo-Format) zu drei kostenpflichtigen „Börsenampeln“, angewandt auf ein Echtgeld-Musterdepot

## 1. Regel aus der Quelle

| ID | Regel | Urheber | Konkretheit | Beleg (Transkript) |
|---|---|---|---|---|
| R7 | Ausstieg in 100 % Cash am nächsten Handelstag, sobald alle drei Ampeln rot sind | Moderator | Schwelle genannt (3 von 3) | „drei Börsenampeln auf Rot komplett raus“ (Z. 11) |
| R8 | Wiedereinstieg, sobald zwei der drei Ampeln wieder grün sind | Moderator | Schwelle genannt (2 von 3) | „zwei Börsenampel auf grün wieder einsteigen“ (Z. 11) |
| R9 | Die Ampeln dürfen nicht miteinander korrelieren; jede braucht eine eigene Logik (Trend/Momentum, Stimmung, taktische Allokation) | Moderator | qualitativ | „nicht miteinander korrelieren“ (Z. 37) |
| R10 | Aktienauswahl im Musterdepot quartalsweise nach den bestbewerteten Titeln einer Quant-Plattform, abgeglichen mit weiteren Plattformen | Moderator | qualitativ | (Z. 9), siehe H-FIN-1 |
| R11 | Ampelsignal auch für ETFs und Optionen nutzbar: Position reduzieren, Optionen schließen, Stopps setzen | Moderator | qualitativ | (Z. 13) |

**Selbstkritik der Quelle:** Fehlsignale (rot, obwohl der Markt weiter steigt); verspätetes Umschalten auf grün kostet Teile der Erholung; die Stimmungsampel schaltete „ein bisschen zu früh“ (Mitte September) auf rot.

**Behauptete Bilanz:** rund +30 Prozentpunkte gegenüber dem S&P 500 seit Oktober 2024, drei Cash-Phasen (2025, März 2026, seit 26.10.2026). Nicht prüfbar; Aktienauswahl und Timing sind darin nicht getrennt.

## 2. Hypothese

Ein Gate, das bei drei von drei roten Signalen aus unterschiedlichen Signalfamilien aussteigt und bei zwei von drei grünen wieder einsteigt, verbessert das Rendite-Risiko-Profil eines Aktienindex gegenüber Buy-and-Hold **und** gegenüber der bestehenden Baseline `classify_regime_v2()`.

**Vorwissen:** H1, H3 und H4 (zusätzliche Ausstiegsfilter) wurden nicht bestätigt. Die A-priori-Erwartung ist deshalb niedrig. Der Test lohnt sich vor allem, weil er mit bereits vorhandenen Indexdaten auskommt und auf Indexebene keinen Survivorship-Bias hat.

## 3. Operationalisierung

Die drei Originalampeln sind proprietär und haben keine öffentliche Historie. Getestet werden deshalb vorab festgelegte, öffentliche Ersatzampeln. Das Ergebnis gilt nur für die Logik, nicht für die Originalprodukte.

| Ampel | Original (laut Quelle) | Proxy (Hauptvariante) | grün, wenn … | Variante 2 |
|---|---|---|---|---|
| A Trend/Momentum | 32 Subindikatoren (Trend, Momentum, Volatilität, Marktbreite, Konjunktur) | 4 Subsignale: Index über 200-Tage-Linie · 12-1-Monats-Momentum > 0 · VIX < VIX3M · Arbeitslosenquote unter ihrem 12-Monats-Schnitt (ALFRED-Vintages) | ≥ 3 von 4 grün (**Annahme**) | ≥ 2 von 4 |
| B Stimmung/Risikobereitschaft | Risk-On/Risk-Off-Composite eines Sentiment-Anbieters | Kreditspread Baa minus 10-jährige US-Staatsanleihe (FRED, lange Historie) unter seinem 200-Tage-Schnitt | Spread unter Schnitt | Equity-Put/Call-Ratio (20-Tage-Schnitt) unter ihrem 1-Jahres-Median |
| C Taktische Allokation | Risk-On-Anteil vieler taktischer Strategien eines Strategie-Aggregators | Anteil von 4 öffentlichen TAA-Signalen im Risk-On: 10-Monats-Trend Aktienindex · absolutes Dual Momentum (12 Monate vs. Geldmarkt) · Canary inflationsgeschützte Anleihen (Momentum 1/3/6/12 > 0, vgl. H6) · Canary Schwellenländer-Aktien + Gesamtanleihen | ≥ 50 % Risk-On (**Annahme**) | ≥ 75 % |

**Handelsregel:** Signal zum Tagesschluss, Ausführung am nächsten Handelstag zur Eröffnung. Cash verzinst mit dem Geldmarktsatz (3-Monats-T-Bill). Investiert ist ein breiter US-Aktienindex (Total Return).

## 4. Testdesign

- **Zeitraum:** ab Januar 2008 (Verfügbarkeit VIX3M) bis heute. In-Sample bis Ende 2016, Out-of-Sample ab 2017 (**Annahme**, beim Freeze fixieren).
- **Kosten:** 10 Basispunkte je Umschichtung, Steuern nur als Hinweis.
- **Vergleich:**
  0. Buy-and-Hold
  1. jede Ampel einzeln
  2. symmetrische Mehrheit (raus bei 2 von 3 rot, rein bei 2 von 3 grün)
  3. **Regel der Quelle** (raus bei 3 von 3 rot, rein bei 2 von 3 grün)
  4. `classify_regime_v2()` (Baseline)
  5. exposure-gematchte statische Aktienquote (Kontrolle B, wie bei H18)
- **Messgrößen:** jährliche Rendite, Sharpe Ratio, maximaler Verlust vom Hoch, Ulcer-Index, Zeit im Markt, Umschichtungen pro Jahr, Fehlausstiege (Wiedereinstieg innerhalb von 20 Handelstagen zu höherem Kurs), verpasste Erholung (Rendite zwischen Tief und Wiedereinstieg), Deflated Sharpe Ratio.
- **Prüfung von R9:** paarweise Korrelation (Phi) der drei Ampelsignale und Anteil der Tage mit Übereinstimmung. Erwartung: A und C überlappen stark, weil beide überwiegend Trendsignale nutzen.
- **Aufteilung** nach Marktregime (Bull/Bear/High-Vol/Seitwärts) wie in `08_STRATEGY_COMPARISON.md`.

## 5. Abbruchkriterium

Variante 3 wird verworfen, wenn sie Out-of-Sample nach Kosten **weder** bei der Sharpe Ratio **noch** beim maximalen Verlust besser abschneidet als (4) **und** die beste Einzelampel. Zusätzlich gilt: Liegt die Phi-Korrelation zweier Proxy-Ampeln über 0,6, ist R9 mit diesen Proxys nicht erfüllt; das wird berichtet und nicht durch nachträgliches Austauschen von Proxys „repariert“.

## 6. Datenbedarf / vorab prüfen

- Vorhanden laut Regime-Datenquellen: VIX, VIX3M (Cboe), Put/Call-Ratio 2006–heute, ALFRED-Vintages.
- Zu prüfen: Baa-10Y-Spread (FRED) bis heute durchgehend; Total-Return-Reihen für die TAA-Signale (Schwellenländer, Gesamtanleihen, inflationsgeschützte Anleihen; Letztere ab 2003/2004 ausreichend).
- Point-in-Time-Risiko: gering bei Kursen und Spreads, mittel bei Makrodaten (deshalb ALFRED).

## 7. Warnhinweise

- Auswahlverzerrung: Die Bilanz der Quelle umfasst zwei Jahre und drei Cash-Phasen; das ist statistisch kein Beleg. Die Quelle vertreibt die Ampeln und den Börsendienst selbst.
- Ein Vergleich mit dem nach Börsenwert gewichteten S&P 500 misst bei einem Musterdepot aus Einzelaktien vor allem den Stilunterschied.
- Mehrfachtests: höchstens die oben genannten Varianten; Deflated Sharpe Ratio verpflichtend.
- Proxys sind nicht die Originale: Ein negatives Ergebnis widerlegt die Logik mit öffentlichen Daten, nicht zwingend die proprietären Produkte.

**Übernahmeregel:** Nur bei bestandenem Abbruchkriterium Out-of-Sample kommt das Gate als Kandidat neben `classify_regime_v2()` in Frage; öffentliche Texte nur als Prüfhinweis.
