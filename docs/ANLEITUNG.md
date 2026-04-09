# Anleitung: Skills Visualizer

## Was zeigt dieses Portal?

Alle installierten Claude Code Skills auf dem Butler-Server. Skills werden live gescannt und nach Quelle gruppiert.

## Klickpfad

Dashboard > Claude Zentrale > Skills-Tab > "Skills-Portal oeffnen"

## Skill-Quellen

| Quelle | Pfad | Beschreibung |
|--------|------|-------------|
| Eigene | ~/.claude/skills/*/SKILL.md | Selbst geschriebene Skills |
| Installiert | ~/.claude/plugins/marketplaces/ | Aus dem Marketplace |
| Anthropic | (im Marketplace) | Von Anthropic bereitgestellt |
| n8n | n8n-workflows-meta.json | n8n-Workflows als Skills |

## Bewertung

Jeder Skill kann auf zwei Achsen bewertet werden:
- **Verstehe** (0-5): Wie gut verstehe ich was der Skill tut?
- **Nutze** (0-5): Wie oft nutze ich den Skill?
