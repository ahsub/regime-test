# Explorationsprotokoll H12-E1 – Marktbreite-Divergenz vor Regimewechseln

**Rev. 1** · 29.09.2026 · **eingefroren vor Abruf und Sichtung der ETF-Daten** ·
Bezug: Forschungsnotiz **H12** (UIQ-Suite `docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md`;
Kandidatenliste `docs/literatur/README.md`)

Dieses Dokument und das Auswertungsskript `run_h12_exploration.py` werden committet, **bevor**
die ETF-Kursreihen abgerufen oder angesehen werden. Änderungen an Definitionen, Maßen,
Fenstern oder Ausgaben nach dem Datenabruf nur als **Rev. 2 mit Begründung und Hinweis, dass
die Daten dann bereits bekannt waren** – nie stillschweigend.

## 0. Status und Abgrenzung

- **Das ist eine Exploration, kein Hypothesentest.** Sie beantwortet nur, ob die Datenlage eine
  präregistrierbare Hypothese überhaupt trägt. Es wird **keine neue Hypothesennummer vergeben**
  (H13–H17 sind bereits Kandidaten aus dem zweiten externen Review; diese Exploration gehört zu
  H12). Ob daraus eine präregistrierte Hypothese wird, entscheidet Axel **nach** dem Bericht.
- **Kein Renditetest, keine Handelsregel, keine Schwellenoptimierung, keine p-Werte.**
  Überlappende Fenster und starke Autokorrelation machen Signifikanztests hier nicht
  interpretierbar; berichtet werden ausschließlich Verteilungen und Häufigkeiten.
- **Ein negativer Befund ist ein vollwertiges Ergebnis** (Divergenz vor Wechseln nicht
  ungewöhnlich, oder häufig ohne anschließenden Wechsel) und wird genauso dokumentiert.
- `n_trials` (Roadmap: 42) wird durch diese Exploration **nicht** verändert. Wie die
  Vorexposition (§1) zu zählen ist, entscheidet Axel gesondert.

## 1. Vorexposition (offengelegt)

1. **Vier undokumentierte Breite-Versuche vom 01.09.2026** in diesem Repo:
   `test_breadth_distribution.py` (`9e500b2`), `test_breadth_distribution_aggressive.py`
   (`23d1af9`), `test_ad_ratio.py` (`4077112`), `test_ad_ratio_ma.py` (`333fe0b`). Ziel jeweils:
   2022er-Fehlklassifikationen von `classify_regime_v2()` beheben; Zeitraum 2011-01-01 –
   2026-08-28; als „Advance-Decline-Linie“ bzw. „AD-Ratio“ bezeichnet, tatsächlich aber
   **`^NYA`-Schlusskurse bzw. deren Tagesrendite** (NYSE Composite, kapitalgewichteter Index).
   **Das ist kein Breitenmaß.** RSP und IWM kamen nicht vor. Ergebnisse sind weder in
   `results/` noch in der Roadmap dokumentiert.
2. **Beobachtung 29.09.2026** (Anlass von H12): Für die Handelstage 13.08. → 28.09.2026 wurden
   SPY −1,6 %, RSP −5,8 %, IWM −7,7 % gesehen (UIQ-Snapshot-Archiv,
   `uiq-devtools/breadth-divergenz/analyze.py`). Dieser Abschnitt liegt **außerhalb** des
   Explorationsfensters (Cboe-Snapshot endet 25.09.2026) bis auf die Tage 13.08.–25.09.2026.
3. Das US-Fenster ist durch H1–H4 inhaltlich bekannt (Roadmap „Nächste Stufe“). Eine spätere
   Bestätigung müsste daher **vorwärts** (Shadow Mode auf neuen Daten) oder **extern**
   (anderer Markt) erfolgen, nicht auf diesem Fenster.

## 2. Daten

| Reihe | Quelle | Snapshot |
|---|---|---|
| VIX, VIX3M | Cboe | `data/raw/cboe/2026-09-27/` (vorhanden, SHA256SUMS) |
| SPY, RSP, IWM (Tageskurse, `Adj Close`) | Yahoo Finance via yfinance | `data/raw/yahoo/<abrufdatum>/` – neu, erzeugt mit `scripts/fetch_yahoo_breadth_etfs.py`, `MANIFEST.json` + `SHA256SUMS.txt` |

- **Nur diese drei ETF.** Weitere Reihen (MDY, Sektor-ETF, eigene UIQ-Breite) sind in dieser
  Exploration **ausgeschlossen**, um die Zahl der Maße fest zu halten. Die UIQ-eigene Breite
  ist rückwirkend nicht rekonstruierbar (wechselndes Universum, Survivorship).
- **Explorationsfenster:** 18.09.2009 (Beginn VIX3M) – 25.09.2026 (Ende Cboe-Snapshot).
  ETF-Kurse werden ab 2007-01-01 abgerufen, damit Renditen und 252-Tage-Perzentile ab
  Fensterbeginn definiert sind.
- **Kalender:** Schnittmenge der Handelstage von SPY, RSP, IWM, VIX und VIX3M. Fehlende Tage
  werden **nicht** aufgefüllt.
- **Bekannte Grenze:** Yahoo-`Adj Close` wird rückwirkend angepasst (Dividenden, Splits) und
  ist nicht point-in-time. Für relative Renditen zweier ETF über ≤ 20 Tage ist der Effekt
  klein, wird aber im Bericht genannt.

## 3. Definitionen (vor Datensicht fixiert)

**Rendite** eines ETF X über h Handelstage bis Tag t (Handelstage des gemeinsamen Kalenders):

  R_X(t−h, t) = AdjClose_X(t) / AdjClose_X(t−h) − 1

**Divergenzmaße** (relative Performance, **nicht** Differenz der Indexstände), h ∈ {5, 10, 20}:

  D_SPY,RSP(t, h) = R_SPY(t−h, t) − R_RSP(t−h, t)
  D_SPY,IWM(t, h) = R_SPY(t−h, t) − R_IWM(t−h, t)

Positive Werte: der kapitalgewichtete Index läuft dem gleichgewichteten bzw. den Small Caps
voraus (Struktur der H12-Beobachtung). **Sechs Maße, keine weiteren.**

**Relatives 252-Tage-Perzentil** – ausschließlich mit der bis Tag t verfügbaren Historie
(kein Look-ahead):

  P252(D_t) = (1/252) · #{ i ∈ {t−251, …, t} : D_i ≤ D_t }

Wertebereich (0, 1]. Definiert nur, wenn alle 252 Werte D_{t−251}, …, D_t vorhanden sind;
sonst fehlend (kein Auffüllen, keine verkürzten Fenster).

**Regime:** `classify_regime_v2(vix, vix3m, gex)` unverändert aus
`compare_approaches_final_v2.py` (`7193f04`), Tageswerte aus dem Cboe-Snapshot.
- **Primär: ohne GEX** (`gex=None`) – entspricht Baseline-Variante „E“ (ganzes Fenster).
- **Sekundär (nur berichtet, keine Auswahl zwischen beiden):** mit GEX aus
  `data/raw/squeezemetrics/2026-08-30/DIX.csv`, nur wo GEX vorhanden (ab 02.05.2011, Ende des
  DIX-Snapshots); ohne GEX-Wert → `gex=None`.

**Ereignis (Regimewechsel)** an Tag t: Regime(t−1) ∈ {BULL_QUIET, BULL_FRAGILE} und
Regime(t) ∈ {STRESS_UNSTABLE, POST_PANIC_REVERSION}.
- **Primär:** alle Ereignisse.
- **Sekundär (vorab festgelegt):** nur Ereignisse, vor denen die 20 Handelstage t−20 … t−1
  vollständig BULL_* waren („sauberer Beginn“ – das Vorfenster enthält dann keinen früheren
  Wechsel).

**Vorfenster:** die 20 Handelstage t−20 … t−1 vor einem Ereignis (Tag t selbst nicht).

**Divergenzzustand** (einzige feste Schwelle, nicht optimiert; nur für Vorlauf und
Fehlalarme nötig): Maß m ist an Tag d „auffällig“, wenn P252(D_m,d) ≥ 0,90.
Episode = maximale Folge aufeinanderfolgender auffälliger Tage; Episodenbeginn = erster Tag.
Um die Abhängigkeit von 0,90 sichtbar zu machen, wird zusätzlich die **vollständige
Dezilverteilung** berichtet (§4.1) – die Schwelle wird nicht variiert oder gewählt.

## 4. Ausgaben (vollständig, je Maß m = 6 Maße, je Regime-Variante)

1. **Vorfenster vs. unbedingt:** Verteilung von P252 über alle Vorfenster-Tage (gepoolt) und
   über alle Tage des Fensters: Anzahl, Median, Anteile je Dezil, Anteil ≥ 0,90. Zusätzlich
   je Ereignis das Maximum von P252 im Vorfenster (Liste mit Datum).
2. **Vorlaufzeiten:** je Ereignis der Abstand in Handelstagen vom letzten Episodenbeginn in
   t−60 … t−1 bis t; „kein Vorlauf“, wenn keiner. Verteilung der Abstände und Anteil „kein
   Vorlauf“.
3. **Fehlalarme:** Anteil der Episodenbeginne ohne Ereignis in den folgenden 20 Handelstagen
   (d+1 … d+20); dazu die **Grundrate**: Anteil aller Tage d mit einem Ereignis in d+1 … d+20.
4. **Stabilität (deskriptiv):** 1.–3. getrennt für 18.09.2009 – 31.12.2016 und
   01.01.2017 – 25.09.2026 (Aufteilung wie Entwicklungs-/Bestätigungsfenster der Roadmap).
5. **Rahmendaten:** Anzahl Ereignisse je Variante, Dauer der Stress-/Post-Panic-Phasen nach
   Ereignis (Median, Anteil Ein-Tages-Episoden), Anzahl gemeinsamer Handelstage, fehlende
   Tage je Reihe.

Ausgabe nach `results/h12_exploration/` als `H12_E1.json` und `H12_E1.md`, jeweils mit den
SHA-256 der verwendeten Snapshots und dem Commit des Skripts.

## 5. Zulässige Aussagen im Bericht

- Nur beschreibend: „Im Vorfenster lag P252 von m im Median bei x gegenüber y unbedingt“;
  „z % der Episodenbeginne hatten keinen Wechsel in 20 Tagen (Grundrate w %)“.
- **Nicht zulässig:** Aussagen über Renditen, Handelbarkeit, Prognosegüte, „Frühindikator“,
  Kausalität; Auswahl eines „besten“ Maßes oder Horizonts; Ergebnisse nur für die günstigere
  Regime-Variante oder das günstigere Teilfenster.
- Der Bericht endet mit einer Empfehlung **an Axel**, ob eine präregistrierte Hypothese
  sinnvoll ist – mit Nennung der dann nötigen Bestätigungsbasis (vorwärts oder extern, §1.3).

## 6. Ablauf

1. Dieses Protokoll + `run_h12_exploration.py` (mit synthetischem Selbsttest) committen.
2. Axel führt `scripts/fetch_yahoo_breadth_etfs.py` am Mac aus und lädt den neuen Ordner
   `data/raw/yahoo/<abrufdatum>/` hoch.
3. Prüfung des Snapshots (`verify_snapshot`, Manifest) – **erst danach** ein einziger Lauf
   von `run_h12_exploration.py`; Bericht committen.
4. Entscheidung Axel über eine präregistrierte Hypothese.
