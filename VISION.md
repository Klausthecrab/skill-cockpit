# Skill-Cockpit – Vision

## Warum gibt es das Projekt?

Hermes hat über 150 Skills mit Bundles, Reference-Dateien, Cron-Jobs und Rang-System. Ohne Übersicht verliert man den Überblick — welcher Skill ist aktuell, welche Bundles überschneiden sich, wo hängen verwaiste References? Skill-Cockpit schafft Klarheit auf einen Blick.

## Was soll es können?

- **Skills-Tab:** Alle Skills als durchsuchbares Raster mit Metadaten, Rang, Nutzung
- **Bundles-Tab:** Bundle-Übersicht mit Token-Gewicht, Skill-Listen, Überschneidungs-Markern
- **References-Tab:** Alle Reference-Dateien mit Traffic-Light-Ampel und Cron-Zuordnung
- Filter, Sortierung, Detail-Ansicht pro Skill — alles read-only

## Was ist NICHT geplant (Anti-Vision)

- ❌ **Skill-Code-Editor** — Skills bearbeiten gehört ins Config-Repo mit Git-Historie
- ❌ **Deployment/Start/Stop von Services** — Systemd-Job, kein Web-UI
- ❌ **Export-Funktionen** — Kein Bedarf auf Butler
- ❌ **Benutzer-Verwaltung / Auth** — Nur Max + Hermi, ein User
- ❌ **n8n-Konfiguration live editieren** — Gefährlich, gehört in n8n selbst

## Use Cases

- Max öffnet das Cockpit, um zu sehen welche Skills verfügbar sind und welche Bundles sich überschneiden
- Hermi prüft vor Skill-Änderungen welche Skills betroffen sind
- Max erkennt verwaiste References ohne Cron-Job auf einen Blick

## Wunsch-Features (Level 2)

- Echtes Usage-Chart statt Simulation (wenn `skill_stats` in `state.db` befüllt wird)
- Skill-Dependency-Visualisierung (welcher Skill lädt wen)
- Filter/Sortierung als URL-Parameter speicherbar
- Auto-Refresh/Polling statt manuellem Refresh