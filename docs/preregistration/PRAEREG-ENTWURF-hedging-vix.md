# Präregistrierungsentwurf: Hedging-Signale aus einem Optionsbuch (Kandidaten H-FIN-11 bis H-FIN-13)

**Status:** Entwurf, kein Code. Geparkt bis nach Phase 4, wie H5/H6/H18 und H-FIN-4. Endgültige H-Nummern erst beim Freeze.
**Ablage:** `ahsub/regime-test/docs/preregistration/` (ohne Tickernamen von Einzelaktien; Indizes und Volatilitätsprodukte beschreibend benannt)
**Quelle:** Praxisbuch eines Optionshändlers zur Depotabsicherung (Stand Dez. 2021, Selbstverlag). Der Autor beschreibt es ausdrücklich als Erfahrungsbericht ohne systematischen Backtest; Belege sind zwei selbst gewählte Zeitfenster 2020.

## 1. Regeln aus der Quelle

| ID | Regel | Konkretheit | Selbstkritik der Quelle |
|---|---|---|---|
| R33 | Hedges reduzieren (nicht auflösen), wenn der VIX ein Hoch über 30 erreicht hat und danach das MACD-Histogramm (12/26/9) des VIX unter null fällt; Alternative: VIX schließt unter seinem 13-Tage-Durchschnitt | Schwellen genannt | Signal Okt. 2008 zu früh (danach weitere ca. 30 % Minus); Zukunft ungewiss |
| R34 | Volatilitäts-Hedge nur eröffnen bzw. wieder eröffnen bei VIX unter 25 | Schwelle genannt | – |
| R35 | Hedges vergrößern bei Warnsignalen: Hindenburg Omen (S&P 500 über 50-Tage-Linie; neue 52-Wochen-Hochs und -Tiefs je > 2,2 % aller Werte; McClellan-Oszillator negativ; Hochs ≤ 2 × Tiefs), negative RSI-14-Divergenz im Index, Put/Call Ratio unter 0,8, VIX über VIX3M; nur im Gesamtbild | Schwellen genannt, Bündelung qualitativ | Fehlsignale ausdrücklich eingeräumt; Put/Call Ratio „als Timing-Indikator ungeeignet“ |
| R36 | Dauerhafter Volatilitäts-Hedge: 3 gekaufte Straddles am Geld auf ein kurzfristiges VIX-Futures-ETN (≥ 120 Tage) + 1 verkaufter Call am Geld mit 1 Woche Laufzeit; Neuzentrierung alle 6 Wochen bei > 10 % Abstand oder < 60 Tagen Restlaufzeit; bei VIX > 30 laufen lassen; Ausstieg nach R33 | Schwellen genannt | Ohne Short Calls wäre das Crash-Ergebnis 2020 besser gewesen; Management „etwas komplex“ |

## 2. Hypothesen

### H-FIN-11 — VIX-Entwarnungssignal (günstig, zuerst)

- **Frage:** Markiert R33 zuverlässig, dass der größte Teil eines Rückgangs vorbei ist?
- **Daten:** VIX (Cboe, ab 1990), S&P 500 Total Return. Bereits vorhanden.
- **Ereignisse:** alle Episoden, in denen der VIX über 30 schließt; Signal = erster Tag danach mit MACD-Histogramm < 0 (Hauptvariante) bzw. VIX-Schluss unter 13-Tage-Durchschnitt (Variante 2). Wiederholte Signale innerhalb einer Episode zählen nur einmal.
- **Vergleich:** (a) Signal am ersten Tag mit VIX < 25 nach dem Hoch, (b) feste Wartezeit von 20 Handelstagen nach dem ersten Schluss über 30, (c) Signal aus `classify_regime_v2()` (Austritt aus dem Stressregime).
- **Messgrößen:** maximaler weiterer Rückgang des Index in 20 und 60 Handelstagen nach dem Signal; Anteil der Signale mit weiterem Rückgang ≥ 10 %; Rendite 60/120 Tage danach; verpasster Anstieg gegenüber (a).
- **Abbruch:** R33 zeigt keinen geringeren weiteren Rückgang in 60 Tagen als (a) und (c) → verwerfen.
- **Hinweis:** Wenige Episoden (Größenordnung 15–25 seit 1990); Ergebnis deskriptiv berichten, keine Signifikanz behaupten. Bezug zur offenen Phase-4-Frage „Prognose statt Timing“.

### H-FIN-12 — Warnsignal-Bündel

- **Frage:** Gehen R35-Signale Rückgängen häufiger voraus als zufällige Tage?
- **Daten:** S&P 500, VIX/VIX3M (vorhanden), Put/Call Ratio 2006–heute (vorhanden, Lücke geschlossen); **zu prüfen:** NYSE-Marktbreite (neue Hochs/Tiefs, steigende/fallende Werte) für Hindenburg Omen und McClellan-Oszillator — Verfügbarkeit, Lizenz, Point-in-Time.
- **Operationalisierung:** Bündel aktiv, wenn mindestens 2 der 4 Signale innerhalb von 20 Handelstagen auftreten (**Annahme**; Variante: 3 von 4). RSI-Divergenz: neues 60-Tage-Hoch im Index bei niedrigerem RSI-14 als beim vorherigen Hoch (**Annahme**).
- **Messgrößen:** Trefferquote und Abdeckung für Rückgänge ≥ 10 % innerhalb von 60 Handelstagen; Vergleich mit zufälligen Tagen gleicher Häufigkeit (Permutation); Einzelsignale getrennt.
- **Abbruch:** Bündel nicht besser als Zufall gleicher Häufigkeit → verwerfen.
- **Vorwissen:** H2 (Put/Call Ratio) zeigte nur Informationsmehrwert, VIX/VIX3M ist bereits in der Regimelogik. Neuer Beitrag wäre allein das Hindenburg Omen.

### H-FIN-13 — Volatilitäts-Straddle als Daueranker (teuer, zuletzt)

- **Frage:** Schützt R36 über einen ganzen Zyklus kostengünstiger als einfache Alternativen?
- **Vergleich auf Depotebene** (breiter US-Aktienindex): (a) R36, (b) R36 ohne Short Calls, (c) rollierender Put-Spread 5–15 % aus dem Geld, (d) exposure-gematchte statische Aktienquote (Kontrolle B wie H18), (e) ungesichert.
- **Messgrößen:** maximaler Depotverlust, Ulcer-Index, Kosten der Absicherung p. a. in ruhigen Phasen, Rendite gesamt; Stressphasen getrennt: Feb. 2018, Q4 2018, März 2020, 2022 (langsamer Bärenmarkt), April 2025.
- **Abbruch:** (a) hat keinen geringeren maximalen Depotverlust je Euro Absicherungskosten als (c) oder (d) → verwerfen.
- **Daten:** historische Optionsdaten auf das Volatilitäts-ETN (kostenpflichtig) — **nur wenn Kosten gerechtfertigt**. Produktrisiken mitmodellieren: Emittenten-Aussetzung der Ausgabe neuer Anteile (März 2022, Aufschlag zum inneren Wert zeitweise ~30 %), Rückwärts-Splits, Ausübung → ETN-Position, für deutsche Privatanleger kein Direkterwerb.

## 3. Reihenfolge

1. H-FIN-11 (vorhandene Daten, wenige Stunden).
2. Datenprüfung Marktbreite → H-FIN-12.
3. H-FIN-13 nur nach Kosten-Nutzen-Entscheidung zu Optionsdaten.

## 4. Warnhinweise

- Auswahlverzerrung: Die Belege der Quelle sind zwei 2020er-Fenster, eines davon der schnellste Crash der Geschichte — der günstigste Fall für Volatilitäts-Hedges.
- Rückschau: Die genannten Signaltermine wurden mit Kenntnis der Folgeentwicklung ausgewählt.
- Wenige Ereignisse: Crash-Episoden sind selten; Mehrfachtests streng begrenzen (höchstens die genannten Varianten).

**Übernahmeregel:** Nur ein Signal, das sein Abbruchkriterium besteht, kommt als Kandidat neben `classify_regime_v2()` in Frage; öffentliche Texte nur als Prüfhinweis.
