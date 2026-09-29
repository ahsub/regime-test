# H12-E1 – Befund (deskriptiv) und Empfehlung

Stand 29.09.2026 · ein Lauf von `run_h12_exploration.py` 1.0.0 (Code unverändert seit `d1fa77c`)
auf Yahoo-Snapshot `data/raw/yahoo/2026-09-29` (Commit `8051f47`, SHA256SUMS + Manifest geprüft).
Rohergebnis: `H12_E1.md` / `H12_E1.json` in diesem Ordner. Nur Aussagen nach Protokoll §5.

## Befund

**Ergebnis: negativ.** Eine Marktbreite-Divergenz im Sinne der H12-Struktur (SPY läuft RSP bzw.
IWM voraus) war in den 20 Handelstagen vor Regimewechseln BULL_* → STRESS_UNSTABLE /
POST_PANIC_REVERSION im Fenster 18.09.2009 – 25.09.2026 **nicht ungewöhnlich**, und
auffällige Divergenz-Episoden wurden **nicht häufiger** von einem Wechsel gefolgt als
beliebige Tage.

1. **Vorfenster vs. unbedingt** (Gesamtfenster; alle 6 Maße, beide Regime-Varianten, beide
   Ereignismengen): Median-P252 im Vorfenster 0,49–0,56, unbedingt 0,50–0,53. Anteil der Tage
   mit P252 ≥ 0,90 im Vorfenster 0,08–0,12, unbedingt 0,11–0,12 – bei den 20-Tage-Maßen im
   Vorfenster eher **niedriger** (z. B. SPY−IWM 20T, primär, alle Ereignisse: 0,084 vs. 0,117).
   Die obersten zwei Dezile sind im Vorfenster nicht angereichert (z. B. 0,201 vs. 0,229 bei
   SPY−RSP 20T).
2. **Fehlalarme ≈ Grundrate:** Anteil der Episodenbeginne (P252 ≥ 0,90) **ohne** Wechsel in
   20 Tagen (Gesamtfenster): alle Ereignisse 0,47–0,53 bei einer Grundrate „Wechsel in 20 Tagen“ von 0,48
   (primär) bzw. 0,52 (mit GEX); saubere Ereignisse 0,73–0,77, d. h. 23–27 % gefolgt, bei
   einer Grundrate von 0,25–0,26. Episoden sagen einen Wechsel damit nicht häufiger voraus
   als ein zufälliger Tag.
3. **Vorlaufzeiten sind nicht aussagekräftig:** Die meisten Ereignisse haben einen
   Episodenbeginn in den 60 Tagen davor (Median 10–26 Tage), aber Episoden sind häufig
   (105–184 im Fenster), sodass das auch zufällig zu erwarten ist – siehe Punkt 2.
4. **Stabilität:** Die Teilfenster 2009–2016 und 2017–2026 zeigen kein gleichgerichtetes
   Muster; Abweichungen einzelner Zellen gehen in beide Richtungen.
5. **Nebenbeobachtung, nicht interpretiert:** Bei „sauberem Beginn“ (Variante primär) sind die untersten zwei
   Dezile im Vorfenster etwas seltener (0,15–0,18 vs. 0,19–0,20), d. h. etwas weniger Tage, an
   denen RSP/IWM deutlich vor SPY lagen. Das ist nicht die H12-Richtung, beruht auf ~50
   Ereignissen mit überlappenden Fenstern und wird hier nur festgehalten.

## Rahmen und Grenzen

- **Die Ereignisse sind überwiegend kurz:** Median-Dauer der Stress-/Post-Panic-Phase nach
  einem Wechsel 2 Tage, 34–47 % Ein-Tages-Phasen; 173 Wechsel (primär) in 17 Jahren. Das
  Baseline-Regime „flackert“ – ein Teil der Ereignisse ist Rauschen des Klassifikators, nicht
  Marktgeschehen. Das Protokoll hat das bewusst nicht gefiltert (feste Definition); die
  Menge „sauberer Beginn“ (≥ 20 BULL-Tage davor) zeigt dasselbe Bild.
- Yahoo-`Adj Close` ist rückwirkend angepasst (nicht point-in-time). Die letzte Snapshot-Zeile
  (29.09.2026) ist ein Intraday-Stand, liegt aber außerhalb des Fensters.
- Nur SPY/RSP/IWM; keine Sektoren, keine UIQ-eigene Breite (Protokoll §2).
- Das Ergebnis betrifft nur die Frage **„Breite-Divergenz vor Wechseln des VIX-Term-Regimes“**.
  Es sagt nichts darüber, ob Breite eine eigene Information über langsame Abwärtsphasen (wie
  2022) oder über Zielgrößen wie künftige Drawdowns enthält.

## Empfehlung an Axel

- **Keine präregistrierte Hypothese „Breite-Divergenz kündigt Regimewechsel an“.** Die Daten
  tragen sie nicht; mehr Varianten (andere Schwellen, Horizonte, Paare) zu suchen wäre genau
  das Nachjustieren, das vermieden werden soll.
- H12 als **deskriptive Marktdiagnostik** bleibt davon unberührt (öffentliche „Signalbreite“
  nach ADR-1 beschreibt einen Zustand, sie behauptet keine Vorhersage).
- Falls Breite weiter verfolgt wird, dann nur als **neue, eigens präregistrierte Frage** im
  Rahmen von Phase 4 („Prognose statt Timing“): inkrementeller Informationswert für eine
  vorab gewählte Zielgröße (z. B. P(Drawdown ≥ 5 % in 20 Tagen)) gegenüber dem VIX-Benchmark –
  mit der Einschränkung, dass das US-Fenster jetzt auch für Breite bekannt ist (Bestätigung
  nur vorwärts oder extern). Nicht priorisiert.
- **n_trials:** Diese Exploration war protokollgemäß kein Test; ob sie – und die vier
  NYA-Versuche vom 01.09. – mitgezählt werden, bleibt Axels Entscheidung.
