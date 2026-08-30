### Die Design-Regel (fast heilig)

Jede neue Funktion muss genau eine dieser drei Fragen beantworten:

1. Hilft sie, **den Markt besser zu verstehen?**
2. Hilft sie, **die richtige Strategie auszuwählen?**
3. Hilft sie, **Fehler zu vermeiden?**

Wenn keine dieser drei Fragen mit Ja beantwortet werden kann — kommt die Idee nicht ins Produkt, oder muss heraus.

## -Grundgesetze (konsolidiert, für alle Module verbindlich)

1. **Streng-modularer Aufbau.** Kein Modul kennt Interna eines anderen; Austausch nur über definierte Kontrakte (JSON-Schemata, ko-* regime-Module). Fachlogik, die zwei Module brauchen, lebt in genau **einem** regime-Modul.
2. **ES6-Zielarchitektur.** Neuer Code ausschließlich ES6-konform (const/let, Arrow Functions, zentrale String-Objekte, keine Inline-Handler, JSDoc). Monolithen werden schrittweise migriert, nie big-bang.
3. **80/20-Vorbehalt.** Jedes Feature nur, wenn ≤ 20 % Aufwand ≥ 80 % Nutzerwert liefern. Randfälle werden dokumentierte Grenzen, keine Features.
4. **No-Hallucination auf allen Ebenen.** Zahlen entstehen deterministisch aus Daten + belegten Konstanten (GZ, Norm, Preisliste mit Standdatum). KI erklärt und formuliert — sie rechnet, schätzt und zitiert nie ohne Quelle. Näherungen sind sichtbar markiert (~). Gilt auch fürs Marketing („verifiziert" nur nach echtem Lauf). **Ergänzt 29.08.2026:** Gilt auch für Validierungssprache — "wissenschaftlich validiert" oder ein Backtest-Ergebnis als "Beweis" der Systemqualität sind nur zulässig, wenn tatsächlich eine externe wissenschaftliche Validierung stattgefunden hat. Bis dahin: "wissenschaftlich dokumentierte Methode", "empirisch getestetes Modell" oder "historisches Testergebnis unter definierten Modellannahmen" — nie "Beweis" oder "validiert" ohne diesen Beleg.
5. **Compliance by Design im Public-Bereich.** Je Modul die einschlägige Schranke: WpHG/BaFin (PO — Public/EIC-Split, „Statistische Kontext-Analyse"), StBerG (Refundex, PO, künftig Ruhestand — Rechenwerk mit Szenarien nebeneinander, nie Ratschlag). Empfehlungssprache existiert ausschließlich hinter dem EIC-PIN.
6. **Datensouveränität.** Browser-first; Depot- und Steuerdaten verlassen den Rechner des Nutzers nicht. Kein Suite-Server hält Nutzerdaten.
7. **Belegkette.** Jeder ausgewiesene Wert ist rückführbar auf Datenzeile, Modul und Rechts-/Datenquelle.
8. **Governance-Muster.** Jedes Modul führt `docs/STRATEGIE.md` + `docs/ROADMAP.md` (versioniert, Fortschreibung DeepSeek), Entscheidungen laufen durch den Vier-Fragen-Filter (Belegkette / 80-20 / ES6-Modularität / Compliance). Deploy nach Zwei-Vorgänge-Prinzip: GitHub = Quellcode, Cloudflare-Pages-Zip = Publikation.
9. **Debug-Protokoll (Laufzeit-Bugs).** Bei jedem Laufzeit-Bug gilt zwingend: **IMMER zuerst Konsolen-Check, dann Code anfassen. Kein Fix ohne bewiesene Root Cause.** Weder DeepSeek noch Axel tippen Code-Änderungen ins Blaue — erst das Symptom im Log sichern, dann gezielt fixen.
10. **Sync- und Versionierungs-Pflicht (Mehrfach-Session-Schutz).** Vor jeder Code-Änderung an einer bereits versionierten Datei: **zuerst `git fetch`/`git log origin/main` gegen den lokalen Stand prüfen**, nie blind auf einem möglicherweise veralteten lokalen/Kontext-Stand weiterarbeiten. Jede geänderte Datei bekommt zwingend im selben Schritt: (a) einen neuen Versions-Header/Meta-Tag, (b) einen Changelog-Eintrag nach bestehendem Muster, (c)
