# Skills Visualizer (Portal)

Zeigt installierte Claude Code Skills mit Ratings, Details und Dataflow.

## Features

- Live-Scan aus 4 Quellen (eigene, installierte, anthropic, n8n)
- Gruppierte Skill-Liste
- Detail-Ansicht: Content, Description, Secrets, Dataflow
- Ratings-System (verstehe/nutze, 0-5)

## Architektur

- **Frontend:** Page.jsx (React), Page.module.css – nutzt Live-API
- **Backend:** routes.py (Flask Blueprint `skills_visualizer`, 7 Routes)
- **Daten:** ~/data/projects/erster-skill-test-skills-visualisierer/ratings.json
- **Scannt:** ~/.claude/skills/, ~/.claude/plugins/, Personas skills-lock.json, n8n-workflows-meta.json
- **Klickpfad:** Claude Zentrale > Skills-Tab

## API-Endpoints

| Route | Methode | Zweck |
|-------|---------|-------|
| /api/skills | GET | Alle Skills mit Stats |
| /api/skills/:id/detail | GET | Skill-Detail |
| /api/skills/n8n/:wf_id/detail | GET | n8n-Workflow-Detail |
| /api/skills/:id/ratings | GET | Ratings lesen |
| /api/skills/:id/ratings | POST | Ratings setzen |
| /api/skills/:id/settings | GET | Settings lesen |
| /api/skills/:id/settings | POST | Settings setzen |
