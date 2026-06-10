# Skill-Cockpit

Visualisierung des Hermes-Skill-Ökosystems auf Butler. Drei Ansichten (Skills, Bundles, References) zeigen alle installierten Skills mit Metadaten, Bundle-Zugehörigkeit, Nutzungsdaten und Aktualitäts-Ampel für Reference-Dateien.

**Wer baut es?** Max + Hermi Agent für den Butler-Homeserver.

**Wie starte / nutze ich's?** Das Web-UI läuft als systemd-Service auf Port 9123. Zugriff via Browser:

- **Vom Butler:** `http://192.168.178.62:9123/`
- **Von Windows (SSH-Tunnel):** `ssh -L 9123:127.0.0.1:9123 butleruser@192.168.178.62` → `http://127.0.0.1:9123/`

**Technologie:** Python Flask (Backend) + React (Frontend, Vite-Build). Datenquellen: `~/.hermes/skills/`, `~/.hermes/state.db`, `~/.hermes/bundles/`, Cron-Konfiguration.

## Weiterführend

- **VISION.md** – Wohin sich das Projekt entwickelt
- **Issues** – Offene Punkte und Pläne (https://github.com/Klausthecrab/skill-cockpit/issues)