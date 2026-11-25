# UIQ — Präregistrierung Track-Record-Runde 2: Basis-Gate-Auswahl gegen Zufallsauswahl

**Datum:** 24.11.2026 · **Fassung 8:** 25.11.2026
**Status:** Nach externem Review vom 25.11.2026 freigabefähig; Präzisierungen A–D, E–G, H–K, L–M, N–Q, R–T und U–W der Review-Runden sowie die Formulierung „dokumentierte Basis-Gate-Auswahl“ sind eingearbeitet (Vorfassungen SHA-256-Präfix `7fac6ff023a5feb8`, `d0d056e3dc8e6af4`, `629ec83fe6517d11`, `b5a5667e7058a56d`, `80958da5a3cabc82`, `bfeffeadfe0f1b8f`, `e2a6851fe25da74b`). Wird vor jeder Auswertung von Signalen ab dem 09.11.2026 committet und gehasht; ab dann keine Änderung mehr (nur Nachträge mit Datum, getrennt gekennzeichnet).
**Bezug:** `docs/AUDIT-TRACKRECORD-STRESS-2026-11-24.md` (v2, SHA-256-Präfix `f9060d33cbb8cd98`), externe Reviews vom 24.11. und 25.11.2026.
**Hinweis:** Keine Tickernamen von Einzeltiteln; einzige Ausnahme ist das Kürzel des Benchmark-ETFs, damit die Kursreihe eindeutig festgelegt ist. Keine Produktionsänderung aus dem Ergebnis, bevor die Mindeststichprobe erreicht ist.

## 1. Fragestellung (primär)

Erzielt die dokumentierte Basis-Gate-Auswahl von UIQ (Basistabelle je Regime, ohne MCM-Herabstufungen) einen besseren Ergebnisbeitrag als eine zufällige Auswahl mit gleicher Sperrquote, wenn die Zufallsauswahl innerhalb desselben Handelstags und derselben Handelsrichtung erfolgt?

Nicht Gegenstand: ob „grüne“ Strategien besser sind als „rote“. Das vermischt Strategiequalität und Gate-Auswahl. Ebenfalls nicht Gegenstand: die tatsächlich angewandte Gate-Auswahl einschließlich aller MCM-Faktoren (siehe Abschnitt 3).

## 2. Stichprobe (vorab fixiert)

| Teil | Signaltage | Zweck |
|---|---|---|
| Konfirmatorisch | ab **09.11.2026** (erster Signaltag nach dem letzten in Runde 1 bewerteten h7-Signaltag 06.11.) | einzige primäre Auswertung |
| Explorativ | 02.07.–06.11.2026 (in Runde 1 bereits gesichtet) | dasselbe Design, ausdrücklich in-sample, nicht entscheidend |

**Auswertungszeitpunkte** (Bewertungsfälligkeit laut Spec: Horizont + 3 Handelstage Puffer):

| Auswertung | Signaltage | frühestens auswertbar | Art |
|---|---|---|---|
| h7, 30 Tage | 09.11.–21.12.2026 | ca. 06.01.2027 | deskriptiv |
| h7, 60 auswertbare Tage (Hauptauswertung) | 09.11.2026 bis zum 60. auswertbaren Signaltag (frühestens 04.02., spätestens 26.02.2027) | ca. 19.02.–12.03.2027 | primärer Endpunkt |
| h30, 30 Tage | 09.11.–21.12.2026 | ca. 09.02.2027 | sekundär |

Zähltage nach US-Handelskalender (ohne 26.11., 25.12., 01.01., 18.01., 15.02.). Die Stichprobe endet mit dem 60. auswertbaren Signaltag (Definition §5a), spätestens jedoch mit dem Signaltag 26.02.2027 (75. Handelstag ab 09.11.2026). Werden bis dahin keine 60 auswertbaren Tage erreicht, lautet das Ergebnis „nicht entscheidbar“. Ob ein Tag auswertbar ist, wird per Skript nur aus Gate-Zuordnung und Kursverfügbarkeit bestimmt, ohne Einsicht in Renditen.

**Folge für den Go/No-Go-Termin Dezember 2026:** Ergebnisse von Runde 2 liegen frühestens im Januar (deskriptiv) bzw. Februar 2027 (primär) vor. Sie können die Dezember-Entscheidung nicht stützen.

## 3. Einheiten und Gate-Quelle

- **Entscheidungsebene:** Das Gate entscheidet je **Strategie × Tag** (`calc_server_strategy_gates`). Gesperrt und gezogen werden deshalb Strategie-Tag-Einheiten, nicht einzelne Empfehlungen.
- **Universum:** die 12 einem Gate zugeordneten Strategien (Zuordnung wie Runde 1). VCP, Breakdown Short und Collar haben kein Gate und bleiben außen vor.
- **Gate-Quelle (primär):** Basistabelle `_MCM_REGIME_GATES` nach dem Regime des Snapshots (`tr:snap.regime`), Code-Stand Commit `b1728e8`. Für diese Auswertung wird ausschließlich die dokumentierte Basis-Gate-Tabelle verwendet.
- **Keine zweite historische Gate-Quelle:** Das Morning Briefing überschreibt `daily_market_snapshot` bzw. `daily_market_snapshot_us` bei jedem Lauf; diese Keys werden nicht im KV-Backup gesichert, und die Archiv-Snapshots enthalten kein `strategyGates`. Die tatsächlichen MCM-Herabstufungen sind deshalb für die historische Stichprobe nicht rekonstruierbar. Arm B bildet ausschließlich die dokumentierte Basis-Gate-Auswahl ab, nicht die tatsächliche Gate-Auswahl einschließlich aller MCM-Faktoren.
- **Keine zweite Gate-Quelle im konfirmatorischen Teil:** Die konfirmatorische Auswertung verwendet ausschließlich die dokumentierte Basis-Gate-Auswahl, auch wenn Backlog-Punkt B1 während der Stichprobe umgesetzt werden sollte. Tatsächlich protokollierte Gates ab dem Umsetzungsdatum dürfen nur in einer getrennten, explorativen Auswertung untersucht werden. Sie verändern weder die Stichprobe noch die primäre Entscheidungsregel.
- **Freigegeben (primär):** nur „grün“. **Sekundär:** „grün“ und „gelb“.

## 4. Vergleichsarme

| Arm | Auswahl |
|---|---|
| A – ungefiltert | alle Strategie-Tag-Einheiten des Universums |
| B – Basis-Gate | nur die nach der Basistabelle freigegebenen Einheiten |
| C – Zufallsgate | Je Handelstag und Richtung werden genau so viele Strategie-Tag-Einheiten zufällig gesperrt, wie das Basistabellen-Gate in B gesperrt hat. Die Zahl der freigegebenen Einheiten ist damit zwischen B und C identisch. 10.000 Ziehungen, Seed `20261124` |

- **Schichtung (primärer Test):** ausschließlich Handelstag × Richtung (long/short).
- **Strategiefamilie:** nur als vorab definierte explorative Sensitivitätsanalyse, nicht Teil des primären Tests. Dafür werden die Ziehungen zusätzlich nach Familie (Trend, Mean Reversion, Einkommen/Optionen, Value/Dividende) geschichtet; Schichten mit weniger als zwei Einheiten gelten als „nicht randomisierbar“ und bleiben unverändert.
- **Zu kleine Schichten:** keine Auffüllung über Tage oder Richtungen. Hat eine Schicht nur eine Einheit, ist C dort mit B identisch; die Schicht gilt als „nicht randomisierbar“ und wird ausgewiesen.
- **Strukturelle Grenze (aus Runde 1 bekannt):** Auf der Short-Seite gibt es genau eine zugeordnete Strategie (Fading Short), die an 94 % der Tage gesperrt war. Der konfirmatorische Vergleich B gegen C betrifft damit faktisch nur die Long-Seite. Die Short-Seite wird deskriptiv berichtet.
- **Gewichtung:** gleich je Strategie-Tag-Einheit, innerhalb der Einheit gleich je Empfehlung.

## 5. Messgrößen

1. **Primärendpunkt:** mittlerer h7-Überschuss je Handelstag auf der Long-Seite, Differenz B − Mittel(C). Die Short-Seite wird ausschließlich deskriptiv ausgewertet und geht nicht in den konfirmatorischen Test ein.
   - Überschuss = richtungsbereinigte Rendite minus richtungsbereinigte Rendite des gleichgewichteten S&P-500-ETF **RSP** (Invesco S&P 500 Equal Weight ETF) über dieselben Handelstage. Long: r − r_Index; Short: (−r_Aktie) − (−r_Index).
   - Dieselbe Regel für alle drei Arme; Aggregation nach §5a.
2. **Sekundär (nicht entscheidungsrelevant):**
   - h30, B − Mittel(C), Aggregation und Permutationstest wie primär; nur berichtet, wenn mindestens 30 auswertbare Tage mit reifem h30-Horizont vorliegen.
   - h7 und h30, B − A: Differenz der Tageswerte mit Standardfehler über Tage (h30 zusätzlich Newey-West, 30 Lags); kein Permutationstest, da A keine Zufallsauswahl ist; rein beschreibend.
   - Variante „grün + gelb“ wie primär.
3. **Risiko:** Standardabweichung der Tagesergebnisse, schlechtester Tag, Anteil negativer Tage je Arm.
4. **Diagnostik je Arm:** Zahl der Einheiten und Empfehlungen, Sperrquote, Strategiemix, Long-/Short-Anteil, mittleres Beta und Beta-Abdeckung (Schätzung nach §5a Nr. 10).

## 5a. Aggregation und auswertbare Tage (verbindlich für alle Arme)

1. **Empfehlung:** Überschuss = richtungsgerechte h7-Rendite (`r7` laut Spec) minus richtungsgerechte Rendite des gleichgewichteten S&P-500-ETF (RSP, wie §5) über dieselben Handelstage.
2. **Einheiten eines Tages:** alle Long-Einheiten (Strategie × Tag) des Universums mit mindestens einer Empfehlung im Snapshot. Strategien ohne Empfehlung an diesem Tag sind keine Einheit; sie gehen weder als Nullrendite noch als Lücke ein.
3. **Sperre und Ziehung** erfolgen auf diesen Einheiten, bevor Kurse bei Fälligkeit bekannt sind. Der Wegfall von Empfehlungen ohne Kurs bei Fälligkeit (`noData`) folgt danach und ist in allen Armen identisch.
4. **Wert einer Einheit:** Mittel der Überschüsse ihrer bewertbaren Empfehlungen.
5. **Tageswert eines Arms:** gleichgewichtetes Mittel der Werte seiner freigegebenen Einheiten.
6. **Auswertbarer Tag:** (a) Snapshot vorhanden, (b) mindestens eine freigegebene und mindestens eine gesperrte Long-Einheit (randomisierbar), (c) nach `noData` behält jede Long-Einheit des Tages mindestens eine bewertbare Empfehlung. Tage, die (b) oder (c) verfehlen, werden gezählt und mit Grund ausgewiesen, gehen aber nicht in den Test ein. Bedingung (c) ist eine bewusst strenge Complete-Case-Regel auf Tagesebene: Sie verhindert, dass sich die Zusammensetzung der Einheiten zwischen den Armen durch fehlende Kurse unterscheidet. Sie wird nachträglich nicht gelockert. Weil `noData` nicht zufällig auftreten muss, werden die ausgeschlossenen Tage nach Ausschlussgrund und nach betroffenen Strategien berichtet.
7. **Teststatistik:** T = Mittel über die auswertbaren Tage von (B_t − C̄_t), wobei C̄_t das Mittel des Tageswerts über die 10.000 Ziehungen ist. Für jede Ziehung j: T_j = Mittel über die Tage von (C_j,t − C̄_t). Zweiseitiges p = (1 + Anzahl der j mit |T_j| ≥ |T|) / 10.001.
8. Dieselben Regeln gelten sinngemäß für h30 und für die Variante „grün + gelb“.
9. **Mittleres Beta je Arm** (für die Bedingung in §6) mit derselben Gewichtung wie das Ergebnis: Beta einer Einheit = Mittel der Betas ihrer Empfehlungen mit verfügbarem Beta (Empfehlungen mit „n. v.“ entfallen nur hier); Tagesbeta eines Arms = gleichgewichtetes Mittel über seine freigegebenen Einheiten; Armbeta = Mittel über die auswertbaren Tage. β_B wird so für B berechnet. Für C erhält jede Ziehung j zunächst ihr eigenes Armbeta β_C,j nach derselben Regel; β_C ist das Mittel der β_C,j über die 10.000 Ziehungen. Eine Einheit, bei der keine Empfehlung ein Beta hat, erhält „n. v.“, zählt nicht als abgedeckt und entfällt nur aus dem Beta-Tagesmittel; sie wird nie mit Beta null angesetzt.
   - **Beta-Abdeckung** = Anteil der Einheiten mit mindestens einer Empfehlung mit Beta an allen Einheiten, die nach den Regeln des jeweiligen Arms in die Beta-Aggregation eingehen (freigegebene Einheiten der auswertbaren Tage). Für C wird die Abdeckung je Ziehung berechnet und dann gemittelt; die Verteilung über die Ziehungen (Minimum, 5. und 95. Perzentil, Maximum) wird berichtet. Fehlende Betas werden zusätzlich nach Strategien ausgewiesen.
   - **Mindestabdeckung:** 80 % in B und im Mittel der C-Ziehungen. Wird sie verfehlt, ist die Beta-Bedingung nicht prüfbar; das Gesamtergebnis lautet dann „nicht entscheidbar“, auch wenn der Permutationstest signifikant ist.
10. **Beta-Schätzung je Ticker und Signaltag:**
   - Benchmark: **RSP** (Invesco S&P 500 Equal Weight ETF), derselbe wie beim Überschuss.
   - Kurse: dividenden- und splitbereinigte Tagesschlusskurse aus derselben Quelle wie der Aggregator (yfinance, `auto_adjust=True`), einmalig nach Ende der Stichprobe für alle benötigten Ticker und den Benchmark geladen und als Datei mit SHA-256 eingefroren. Nicht verwendet werden die Archiv-Snapshots: Datierte Schlusskurse je Ticker gibt es dort erst ab 11.09.2026, und als unvollständig markierte letzte Zeilen sind Intraday-Werte.
   - Fenster: Es werden die 60 US-Handelstagessitzungen vor dem Signaltag als Renditebeobachtungen verwendet, endend mit der Sitzung t−1. Dafür werden 61 Schlusskursbeobachtungen benötigt, beginnend mit t−61. Es werden ausschließlich Renditen verwendet, deren beide Schlusskurse vor dem Signaltag liegen; höchstens 60 Renditepaare.
   - Datenstand: Die Beta-Berechnung verwendet ausschließlich Renditebeobachtungen aus dem vor dem Signaltag endenden 60-Handelstage-Fenster. Die spätere Beschaffung und das Einfrieren der Kursdatei erzeugen keinen zeitlichen Vorgriff auf Kursbeobachtungen nach dem Signaltag. Nachträgliche historische Datenkorrekturen durch den Datenanbieter sind damit jedoch nicht ausgeschlossen; die eingefrorene Datei dokumentiert den verwendeten Datenstand (Datenvintage-Risiko). Das Einfrieren sichert Reproduzierbarkeit, nicht Point-in-Time-Authentizität.
   - Zum eingefrorenen Datensatz werden festgehalten: exakter Benchmark-Ticker, verwendete Ticker und Datumsbereiche, Abrufzeitpunkt, `auto_adjust=True`, yfinance-Version, SHA-256 der vollständigen Kursdatei.
   - Die Kursdatei darf nach Ende der Stichprobe beschafft werden; die Regeln ihrer Verarbeitung (diese Nr. 10) stehen mit dem Commit dieser Präregistrierung fest.
   - Renditen: einfache Tagesrenditen; verwendet werden nur gepaarte Renditen, bei denen Aktie und Benchmark an beiden aufeinanderfolgenden Handelstagen einen Schlusskurs haben.
   - Beta = Steigung einer linearen Regression (kleinste Quadrate, mit Achsenabschnitt) der Aktienrenditen auf die Benchmarkrenditen; mindestens 40 gepaarte Renditen, sonst „n. v.“.
   - Benötigt nur für Long-Einheiten (Primärtest).
11. **Umsetzung:** Das Auswertungsskript wird vor der ersten Auswertung von Signalen ab dem 09.11.2026 committet und vor dem Lauf gegen §5a geprüft (insbesondere: jede Ziehung umfasst dieselben auswertbaren Tage; Zentrierung nach Nr. 7). Die Präregistrierung belegt nicht, dass ein Skript dies bereits umsetzt. Zufallszahlen: `numpy.random.default_rng(20261124)` (Generator PCG64); das Skript protokolliert Python-, numpy- und pandas-Version.

## 6. Statistik und Entscheidungsregel

- **Test:** Permutationstest gegen die 10.000 Zufallsziehungen (Statistik §5a Nr. 7), zweiseitig, α = 0,05. Dazu Standardfehler über Tage (Cluster Tag); bei h30 zusätzlich Newey-West mit 30 Lags wegen überlappender Fenster.
- **„Vorteil der dokumentierten Basis-Gate-Auswahl“** nur wenn:
  1. B − C > 0 und Permutations-p < 0,05,
  2. der Betrag der Differenz im mittleren Beta, |β_B − β_C|, unter 0,10 liegt (Berechnung nach §5a Nr. 9),
  3. mindestens 60 auswertbare Signaltage im Sinne von §5a vorliegen.
- **„Dokumentierte Basis-Gate-Auswahl schlechter als Zufall“**, wenn B − C < 0 und p < 0,05 (gleiche Bedingungen 2–3).
- **Sonst: „nicht entscheidbar“.** Keine nachträgliche Vereinfachung.
- **Reichweite jeder Aussage:** Ein Ergebnis gilt nur für die dokumentierte Basis-Gate-Auswahl, nicht für die tatsächliche Gate-Auswahl einschließlich aller MCM-Faktoren.
- **Ausschlüsse:** nur Empfehlungen ohne Kurs bei Fälligkeit (`noData`), gezählt und ausgewiesen. Tage mit veralteten Daten (D26) bleiben drin; Empfindlichkeit ohne diese Tage wird zusätzlich berichtet.
- **Einmalige primäre Auswertung.** Jede weitere Variante heißt explorativ.

## 7. Machbarkeit (aus den Daten von Runde 1 abgeschätzt)

Grobe Schätzung der minimal erkennbaren Effektgröße unter vereinfachenden Annahmen (80 % Power, α = 0,05 zweiseitig, Faktor 2,8 × Streuung / √Tage), abgeleitet aus der Streuung der täglichen Differenz „nur grün minus alle“ in Runde 1. Keine formale Powerberechnung für den neuen B-gegen-C-Test. Die tatsächliche Streuung von B − C ist vorab unbekannt. Die angegebenen Werte dienen deshalb nur der groben Orientierung und können die tatsächliche Nachweisgrenze über- oder unterschätzen. Die Stress-Streuung beruht auf nur 10 Tagen.

| Marktphase | Streuung je Tag | 30 Tage | 60 Tage |
|---|---|---|---|
| ruhig (vor 26.10.) | 0,63 Pp | 0,32 Pp | 0,23 Pp |
| Stress (ab 26.10.) | 1,25 Pp | 0,64 Pp | 0,45 Pp |
| h30 (ohne Überlappungskorrektur) | 1,46 Pp | 0,74 Pp | — |

- **Einordnung:** In Runde 1 betrug der Unterschied „nur grün minus alle“ −0,19 Pp (ruhig) bzw. −0,37 Pp (Stress). Effekte dieser Größe lägen nach dieser groben Schätzung mit 60 Tagen in ruhigen Phasen knapp im erkennbaren Bereich, in Stressphasen nicht.
- **Konsequenz:** Ergibt die Hauptauswertung „nicht entscheidbar“, ist das ein erwartbares Ergebnis und kein Mangel. Eine Verlängerung der Stichprobe wird dann als **neue** Präregistrierung beschlossen, nicht als Fortschreibung.
- **Schichtgrößen Runde 1:** Long-Seite im Mittel 9,3 Einheiten je Tag (3–11), davon 1,2 gesperrt und 1,6 gelb; Short-Seite 1 Einheit.

## 8. Was nicht passiert

- Keine Änderung von Strategiezuordnung, Benchmark, Sperrquote, Seed, Ausschlussregeln oder Stichprobenende nach Sichtung.
- Keine Produktions- oder Gate-Änderung aus Runde 2 vor Erreichen der Mindeststichprobe. B8 (Mean Reversion und Fading Short in BULL_QUIET) bleibt Hypothese.
- h7 ersetzt nicht h30.

## 9. Änderungen gegenüber den Vorfassungen (`7fac6ff023a5feb8` → `d0d056e3dc8e6af4` → `629ec83fe6517d11` → `b5a5667e7058a56d` → `80958da5a3cabc82` → `bfeffeadfe0f1b8f` → `e2a6851fe25da74b` → Fassung 8)

| Review-Punkt | Stelle | Änderung |
|---|---|---|
| Basis-Gate-Formulierung (Review 24.11.) | Titel, §1, §4 Arm B, §6 | „Gate-Auswahl“ → „dokumentierte Basis-Gate-Auswahl“; Reichweite der Aussage ergänzt |
| A – historische Gate-Quelle | §3 | technische Ursache der Nicht-Rekonstruierbarkeit ergänzt |
| B – Zufallssperre | §4 Arm C | Sperrzahl statt Freigabezahl eindeutig definiert |
| C – Strategiefamilie | §4 | nicht mehr optional; nur explorative Sensitivitätsanalyse |
| D – Nachweisgrenze | §7 | als grobe Schätzung ohne formale Powerberechnung benannt; Formel und Stress-Stichprobe (10 Tage) offengelegt |
| E – Primärtest nur Long (Fassung 3) | §5 | Primärendpunkt ausdrücklich auf die Long-Seite beschränkt; Short nur deskriptiv |
| F – sekundäre Gate-Quelle (Fassung 3) | §3 | protokollierte Gates nach B1 nur explorativ und getrennt; keine Vermischung im konfirmatorischen Teil |
| G – Streuung B − C (Fassung 3) | §7 | Annahme „voraussichtlich kleiner“ ersetzt: vorab unbekannt, Über- oder Unterschätzung möglich |
| H – Beta-Differenz (Fassung 4) | §6 | Betrag |β_B − β_C| < 0,10; β_C als Mittel über die Ziehungen |
| I – Aggregation (Fassung 4) | neu §5a | Einheit, Tageswert, Umgang mit fehlenden Empfehlungen und `noData`, Teststatistik und p-Wert eindeutig definiert |
| J – h30 und B gegen A (Fassung 4) | §5 | h30 erst ab 30 auswertbaren Tagen; B − A rein beschreibend ohne Permutationstest |
| K – auswertbare Tage (Fassung 4) | §2, §5a, §6 | Definition „auswertbar“; Stichprobenende am 60. auswertbaren Tag, Obergrenze Signaltag 26.02.2027 |
| L – Beta-Gewichtung (Fassung 5) | §5a Nr. 9, §6 | mittleres Beta mit derselben Einheiten- und Tagesgewichtung wie das Ergebnis; β_C je Ziehung, dann gemittelt |
| M – Complete-Case-Regel (Fassung 5) | §5a Nr. 6 | Bedingung (c) ausdrücklich als bewusste, nicht zu lockernde Festlegung gekennzeichnet |
| N – Beta „n. v.“ und Abdeckung (Fassung 6) | §5a Nr. 9 | Einheit ohne Beta = „n. v.“; Abdeckung je Arm und Ziehung; Mindestabdeckung 80 %, sonst „nicht entscheidbar“ |
| O – Beta-Schätzung (Fassung 6) | §5a Nr. 10, §5 Nr. 4 | Benchmark, Kursquelle, Fenster, Renditeart, Regression und Mindestbeobachtungen festgelegt; Archiv-Snapshots als Kursquelle ersetzt |
| P – Ausschlussbericht (Fassung 6) | §5a Nr. 6 | ausgeschlossene Tage nach Grund und betroffenen Strategien |
| Q – Umsetzung (Fassung 6) | §5a Nr. 11 | Auswertungsskript vor erster Auswertung committen und gegen §5a prüfen |
| R – Abdeckungsdefinition (Fassung 7) | §5a Nr. 9 | abgedeckt = mindestens eine Empfehlung mit Beta; C je Ziehung, dann gemittelt; Verteilung und Fehlende nach Strategie berichtet; fehlendes Beta nie null |
| S – Unterschrittene Abdeckung (Fassung 7) | §5a Nr. 9 | „nicht entscheidbar“ auch bei signifikantem Permutationstest |
| T – Datenvintage (Fassung 7) | §5a Nr. 10 | Wortlaut zu späterer Beschaffung und Datenkorrekturen; Metadaten des eingefrorenen Datensatzes; Verarbeitungsregeln stehen mit Commit fest |
| U – Benchmark-Identität (Fassung 8) | Kopf, §5, §5a Nr. 10 | Benchmark-ETF für Überschuss und Beta mit Kürzel festgelegt |
| V – Beta-Fenster (Fassung 8) | §5a Nr. 10 | 60 Renditebeobachtungen aus 61 Schlusskursen (t−61 bis t−1) |
| W – Zufallszahlen (Fassung 8) | §5a Nr. 11 | Generator und protokollierte Bibliotheksversionen |

Keine Änderung an Stichprobenbeginn, Primärendpunkt, Seed, Signifikanz- und Beta-Schwelle. Geändert in Fassung 4: das Stichprobenende (60 auswertbare statt 60 vorhandene Signaltage, mit Obergrenze), damit die Mindestzahl nicht schon durch nicht randomisierbare Tage unerreichbar wird. Festgelegt vor jeder Einsicht in Ergebnisse ab dem 09.11.2026.
