# Test-Definitionen: Skills Visualizer

## API-Tests

### GET /api/skills
- Erwartung: 200, JSON mit skills-Array aus 4 Quellen
- **Status: PASS** (2026-04-09, 80 Skills)

### GET /api/skills/:id/detail
- Erwartung: 200, JSON mit name, content, description
- **Status: PASS** (2026-04-09, discord-nachricht)

### GET /api/skills/:id/ratings
- Erwartung: 200, JSON mit verstehe/nutze
- **Status: PASS** (2026-04-09)

### GET /api/skills/:id/settings
- Erwartung: 200, JSON (leer oder mit show_in_all)
- **Status: PASS** (2026-04-09)

### POST /api/skills/:id/ratings
- Body: `{"verstehe":5,"nutze":3}`
- Erwartung: 200
- **Status:** Nicht getestet (wuerde bestehende Ratings ueberschreiben)

## UI-Tests (manuell)

### T1: Skill-Liste
- Pruefung: Skills werden gruppiert nach Quelle angezeigt
- Status: Manuell

### T2: Detail-Ansicht
- Pruefung: Klick auf Skill zeigt Content, Secrets, Dataflow
- Status: Manuell

### T3: Ratings
- Pruefung: Sterne klickbar, Wert wird gespeichert
- Status: Manuell

### T4: Claude Zentrale Link
- Pruefung: Claude Zentrale > Skills zeigt Link zum Portal
- Status: Manuell
