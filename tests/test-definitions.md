# Test-Definitionen: Skills Visualizer

## API-Tests

### GET /api/skills
- Erwartung: 200, JSON mit skills-Array
- **Status:** Nicht getestet

### GET /api/skills/:id/detail
- Erwartung: 200, JSON mit name, description, content
- **Status:** Nicht getestet

### GET /api/skills/:id/ratings
- Erwartung: 200, JSON mit verstehe/nutze
- **Status:** Nicht getestet

### POST /api/skills/:id/ratings
- Body: `{"verstehe":5,"nutze":3}`
- Erwartung: 200
- **Status:** Nicht getestet

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
