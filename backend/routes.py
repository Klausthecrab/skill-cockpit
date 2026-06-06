"""Skills Visualizer – scannt installierte Claude Code Skills."""

import os
import re
import json
import glob
from datetime import datetime
from flask import Blueprint, jsonify, request

skills_visualizer_bp = Blueprint('skills_visualizer', __name__)

HOME = os.path.expanduser('~')
CLAUDE_SKILLS_DIR = os.path.join(HOME, '.claude', 'skills')
CLAUDE_PLUGINS_DIR = os.path.join(HOME, '.claude', 'plugins', 'marketplaces')
HERMES_SKILLS_DIR = os.path.join(HOME, '.hermes', 'skills')
HERMES_STATE_DB = os.path.join(HOME, '.hermes', 'state.db')
PERSONAS_DIR = None
DATA_DIR = None
RATINGS_FILE = os.path.join(
    HOME, 'data', 'projects', 'erster-skill-test-skills-visualisierer', 'ratings.json'
)

N8N_RELEVANT_CATEGORIES = {'research', 'bilder-app', 'voice', 'dashboard-projekte-ki', 'projekte'}

# n8n workflow ID -> Claude sister skill mapping
SISTER_SKILLS = {
    # research
    '6d6GKuccb51ARGNc': {'skill': 'research', 'relation': 'n8n orchestriert bis zu 3 Research-Runden automatisch. Der Claude-Skill macht einzelne, interaktive Recherchen mit Kontext-Verstaendnis.'},
    'IJ9Zg4P86gs1bmt1': {'skill': 'research', 'relation': 'Sub-Workflow fuer eine Research-Runde. Claude-Skill vereint Query-Generierung und Recherche in einem Schritt.'},
    '85Y0MmnrJGzUmRF3': {'skill': 'research', 'relation': 'Fuehrt einzelne Recherche aus. Pendant zum research-Skill, aber ohne interaktiven Dialog.'},
    'xXvFlhIfQQCsbmnq': {'skill': 'research', 'relation': 'Bereitet Queries vor. Claude-Skill generiert Queries kontextabhaengig im Gespraech.'},
    # voice
    'U6kpW7cagtIvSeps': {'skill': 'whisper-transkription', 'relation': 'n8n nutzt Venice.ai Cloud-Whisper. Der Claude-Skill nutzt den lokalen faster-whisper Server (Port 8026).'},
    'aXEzWMoeUy6rsNqF': {'skill': 'whisper-transkription', 'relation': 'n8n nutzt lokalen Whisper mit Start/Stop. Claude-Skill geht direkt ueber den laufenden Server.'},
    # bilder-app
    '64m5o5jjXRidsgGM': {'skill': 'bild-erstellen', 'relation': 'n8n routet nach Modell (Nano Banana, Z-Image). Claude-Skill nutzt direkt die Venice API.'},
    'O0YnGytDTXrKyVZI': {'skill': 'bild-erstellen', 'relation': 'Sub-Workflow fuer Nano Banana Pro. Claude-Skill kann dasselbe Modell direkt ansprechen.'},
    'CamENzKCjMs6mbSj': {'skill': 'bild-erstellen', 'relation': 'Sub-Workflow fuer Z-Image Turbo. Claude-Skill nutzt dasselbe Modell via Venice API.'},
    # research-queue (neue Workflows)
    '7Nb3idBY8qgiQbFn': {'skill': 'research-sofort', 'relation': 'n8n fuehrt die Research async aus (Venice.ai + Brave Search). Der Claude-Skill erstellt Queue-Eintrag und triggert den Workflow.'},
    'm5dXzI6uDvHMY9eQ': {'skill': 'research-queue', 'relation': 'n8n verarbeitet die Queue automatisch um 03:00 Uhr. Der Claude-Skill fuegt Themen zur Queue hinzu.'},
    'vi7BQszoOOEE4P75': {'skill': 'research-sofort', 'relation': 'Sub-Workflow fuer kumulative Growing-Research. Wird von research-sofort und nightly-pipeline aufgerufen.'},
    # dashboard-projekte-ki
    'f0dtthmJNRqv4AOt': {'skill': 'subnotizen-aggregieren', 'relation': 'n8n Webhook-Wrapper fuer die Flask API. Claude-Skill bietet interaktive Auswahl mit Tag-Filter und Bestaetigung.'},
    # projekte
    'bfvRJnoqD4aemUJF': {'skill': 'projekt-merge', 'relation': 'n8n Webhook-Wrapper fuer den Flask Merge-Endpoint. Claude-Skill bietet interaktive Projekt-Auswahl und Bestaetigung.'},
}

# n8n category -> secrets used (n8n manages credentials internally but we show which APIs)
N8N_SECRETS = {
    'research': [
        {'name': 'venice-api-key', 'level': 1, 'provider': 'n8n-credentials'},
        {'name': 'brave-api-key', 'level': 1, 'provider': 'n8n-hardcoded'},
    ],
    'bilder-app': [{'name': 'venice-api-key', 'level': 1, 'provider': 'n8n-credentials'}],
    'voice': [{'name': 'venice-api-key', 'level': 1, 'provider': 'n8n-credentials'}],
}

# n8n workflow ID -> dataflow steps
N8N_DATAFLOWS = {
    '6d6GKuccb51ARGNc': [
        'Webhook empfaengt Forschungsfrage',
        'Evaluiert ob weitere Runden noetig (max 3)',
        'Ruft Sub-Workflow "deep-research-round" auf',
        'Aggregiert Ergebnisse aller Runden',
        'Bewertet Gesamtergebnis via LLM',
        'Liefert finalen Research-Report zurueck',
    ],
    'IJ9Zg4P86gs1bmt1': [
        'Empfaengt Forschungsfrage + bisherige Ergebnisse',
        'Generiert 6 Suchqueries via LLM',
        'Fuehrt parallele Recherchen ueber 6 Quellen aus',
        'Aggregiert Teilergebnisse zu einem Runden-Report',
    ],
    '85Y0MmnrJGzUmRF3': [
        'Empfaengt einzelne Suchquery',
        'Fuehrt Web-Recherche aus',
        'Extrahiert relevante Inhalte',
        'Liefert strukturiertes Ergebnis zurueck',
    ],
    'xXvFlhIfQQCsbmnq': [
        'Empfaengt Forschungsfrage',
        'Generiert optimierte Suchqueries via Venice.ai LLM',
        'Liefert Query-Set zurueck',
    ],
    'U6kpW7cagtIvSeps': [
        'Empfaengt Audio-Datei (Telegram Voice)',
        'Sendet an Venice.ai Whisper API',
        'Liefert Transkription zurueck',
    ],
    'aXEzWMoeUy6rsNqF': [
        'Startet lokales Whisper-Modul',
        'Empfaengt Audio-Datei',
        'Transkribiert lokal via Whisper',
        'Liefert Transkription zurueck',
        'Stoppt Whisper-Modul',
    ],
    '64m5o5jjXRidsgGM': [
        'Webhook POST /webhook/image-generate',
        'Switch: Prueft gewaehltes Modell',
        'Leitet an Sub-Workflow (Nano Banana / Z-Image)',
        'Liefert generiertes Bild zurueck',
    ],
    'O0YnGytDTXrKyVZI': [
        'Empfaengt Prompt + Parameter (resolution, aspect_ratio)',
        'Sendet an Venice.ai nano-banana-pro API',
        'Liefert Bild zurueck',
    ],
    'CamENzKCjMs6mbSj': [
        'Empfaengt Prompt + Parameter (width, height)',
        'Sendet an Venice.ai z-image-turbo API',
        'Liefert Bild zurueck',
    ],
    '7Nb3idBY8qgiQbFn': [
        'Webhook empfaengt Queue-Item',
        'Extrahiert Topic und Modus',
        'Switch: Routet nach Modus (Simple/Deep/Growing)',
        'Fuehrt Research aus (Venice.ai / Deep-Research / Growing)',
        'Postet Ergebnis in Inbox',
        'Entfernt Item aus Queue',
        'Sendet Webhook-Response',
    ],
    'm5dXzI6uDvHMY9eQ': [
        'Schedule Trigger (03:00 Uhr)',
        'Liest Research-Queue vom Dashboard',
        'Prueft ob Queue leer ist',
        'Switch: Routet jeden Eintrag nach Modus',
        'Fuehrt Research aus (Simple/Deep/Growing)',
        'Postet Ergebnis in Inbox',
        'Entfernt verarbeitetes Item aus Queue',
    ],
    'vi7BQszoOOEE4P75': [
        'Empfaengt Topic-Daten vom Parent-Workflow',
        'Liest bisherigen Topic-State vom Dashboard',
        'Generiert neue Suchqueries via Venice.ai LLM',
        'Fuehrt Web-Recherche via Brave Search aus',
        'Synthetisiert Ergebnisse via Venice.ai',
        'Liefert Research-Report zurueck',
    ],
}

# n8n workflow ID -> dataflow graph (structured, with branching)
N8N_DATAFLOW_GRAPHS = {
    '64m5o5jjXRidsgGM': {
        'nodes': [
            {'id': 's1', 'type': 'step', 'label': 'Webhook empfaengt Anfrage',
             'detail': 'POST /webhook/image-generate', 'icon': 'webhook', 'next': ['s2']},
            {'id': 's2', 'type': 'condition', 'label': 'Welches Modell?',
             'branches': [
                 {'label': 'Nano Banana', 'outcome': 'success', 'next': ['s3']},
                 {'label': 'Z-Image', 'outcome': 'neutral', 'next': ['s4']},
             ]},
            {'id': 's3', 'type': 'step', 'label': 'Nano Banana Pro',
             'detail': 'Sub-Workflow fuer Venice.ai nano-banana-pro', 'icon': 'image', 'next': ['s5']},
            {'id': 's4', 'type': 'step', 'label': 'Z-Image Turbo',
             'detail': 'Sub-Workflow fuer Venice.ai z-image-turbo', 'icon': 'image', 'next': ['s5']},
            {'id': 's5', 'type': 'step', 'label': 'Bild zurueckliefern',
             'icon': 'check', 'next': []},
        ]
    },
    '6d6GKuccb51ARGNc': {
        'nodes': [
            {'id': 's1', 'type': 'step', 'label': 'Forschungsfrage empfangen',
             'detail': 'Webhook empfaengt Frage', 'icon': 'webhook', 'next': ['s2']},
            {'id': 's2', 'type': 'step', 'label': 'Recherche-Runden evaluieren',
             'detail': 'Prueft ob weitere Runden noetig (max 3)', 'icon': 'brain', 'next': ['s3']},
            {'id': 's3', 'type': 'parallel', 'label': 'Parallele Recherchen',
             'branches': [
                 {'label': 'Query 1-3', 'next': ['s3a']},
                 {'label': 'Query 4-6', 'next': ['s3b']},
             ]},
            {'id': 's3a', 'type': 'step', 'label': 'Web-Recherche Batch 1',
             'detail': '3 parallele Suchanfragen', 'icon': 'search', 'next': ['s4']},
            {'id': 's3b', 'type': 'step', 'label': 'Web-Recherche Batch 2',
             'detail': '3 parallele Suchanfragen', 'icon': 'search', 'next': ['s4']},
            {'id': 's4', 'type': 'step', 'label': 'Ergebnisse aggregieren',
             'detail': 'Teilergebnisse zusammenfuehren', 'icon': 'merge', 'next': ['s5']},
            {'id': 's5', 'type': 'step', 'label': 'Research-Report erstellen',
             'detail': 'LLM bewertet und fasst zusammen', 'icon': 'check', 'next': []},
        ]
    },
    '7Nb3idBY8qgiQbFn': {
        'nodes': [
            {'id': 's1', 'type': 'step', 'label': 'Webhook empfaengt Item',
             'detail': 'POST /webhook/research-sofort', 'icon': 'webhook', 'next': ['s2']},
            {'id': 's2', 'type': 'condition', 'label': 'Welcher Modus?',
             'branches': [
                 {'label': 'Simple', 'outcome': 'success', 'next': ['s3']},
                 {'label': 'Deep', 'outcome': 'neutral', 'next': ['s4']},
                 {'label': 'Growing', 'outcome': 'neutral', 'next': ['s5']},
             ]},
            {'id': 's3', 'type': 'step', 'label': 'Venice.ai Recherche',
             'detail': 'Direktrecherche via LLM', 'icon': 'brain', 'next': ['s6']},
            {'id': 's4', 'type': 'sub-skill', 'label': 'Deep Research v2',
             'detail': 'Triggert deep-research-v2 (bis 3 Runden)', 'icon': 'puzzle', 'next': ['s6']},
            {'id': 's5', 'type': 'sub-skill', 'label': 'Growing Research',
             'detail': 'Ruft growing-research Sub-Workflow auf', 'icon': 'puzzle', 'next': ['s6']},
            {'id': 's6', 'type': 'step', 'label': 'In Inbox posten',
             'detail': 'POST /api/inbox', 'icon': 'check', 'next': ['s7']},
            {'id': 's7', 'type': 'step', 'label': 'Aus Queue entfernen',
             'detail': 'DELETE /api/research/queue/:id', 'icon': 'check', 'next': []},
        ]
    },
    'm5dXzI6uDvHMY9eQ': {
        'nodes': [
            {'id': 's1', 'type': 'step', 'label': 'Schedule 03:00',
             'detail': 'Taeglich um 03:00 Uhr', 'icon': 'webhook', 'next': ['s2']},
            {'id': 's2', 'type': 'step', 'label': 'Queue lesen',
             'detail': 'GET /api/research/queue', 'icon': 'search', 'next': ['s3']},
            {'id': 's3', 'type': 'condition', 'label': 'Queue leer?',
             'branches': [
                 {'label': 'Nein', 'outcome': 'success', 'next': ['s4']},
                 {'label': 'Ja', 'outcome': 'failure', 'next': ['s7']},
             ]},
            {'id': 's4', 'type': 'condition', 'label': 'Modus?',
             'branches': [
                 {'label': 'Simple', 'outcome': 'success', 'next': ['s5a']},
                 {'label': 'Deep', 'outcome': 'neutral', 'next': ['s5b']},
                 {'label': 'Growing', 'outcome': 'neutral', 'next': ['s5c']},
             ]},
            {'id': 's5a', 'type': 'step', 'label': 'Venice.ai Recherche',
             'icon': 'brain', 'next': ['s6']},
            {'id': 's5b', 'type': 'sub-skill', 'label': 'Deep Research v2',
             'icon': 'puzzle', 'next': ['s6']},
            {'id': 's5c', 'type': 'sub-skill', 'label': 'Growing Research',
             'icon': 'puzzle', 'next': ['s6']},
            {'id': 's6', 'type': 'step', 'label': 'Inbox + Queue Cleanup',
             'detail': 'Ergebnis posten, Item entfernen', 'icon': 'check', 'next': []},
            {'id': 's7', 'type': 'end', 'label': 'Nichts zu tun',
             'icon': 'stop', 'next': []},
        ]
    },
    'vi7BQszoOOEE4P75': {
        'nodes': [
            {'id': 's1', 'type': 'step', 'label': 'Topic-Daten empfangen',
             'detail': 'Vom Parent-Workflow', 'icon': 'webhook', 'next': ['s2']},
            {'id': 's2', 'type': 'step', 'label': 'State lesen',
             'detail': 'GET /api/research/topics', 'icon': 'search', 'next': ['s3']},
            {'id': 's3', 'type': 'step', 'label': 'Queries generieren',
             'detail': 'Venice.ai LLM generiert 3 neue Suchbegriffe', 'icon': 'brain', 'next': ['s4']},
            {'id': 's4', 'type': 'step', 'label': 'Brave Search',
             'detail': 'Web-Recherche mit generierten Queries', 'icon': 'search', 'next': ['s5']},
            {'id': 's5', 'type': 'step', 'label': 'Ergebnisse synthetisieren',
             'detail': 'Venice.ai fasst Suchergebnisse zusammen', 'icon': 'brain', 'next': ['s6']},
            {'id': 's6', 'type': 'step', 'label': 'Report zurueckliefern',
             'icon': 'check', 'next': []},
        ]
    },
}


def _load_port_names():
    """Lade Port->Name Mapping aus ports.json."""
    if not DATA_DIR:
        return {}
    ports_file = os.path.join(DATA_DIR, 'ports.json')
    if not os.path.isfile(ports_file):
        return {}
    try:
        with open(ports_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            str(p['port']): p.get('name', f"Port {p['port']}")
            for p in data.get('ports', [])
        }
    except (OSError, json.JSONDecodeError):
        return {}


def _humanize_step(text, port_names=None):
    """Ersetze technische Kommandos durch lesbare Beschreibungen."""
    if not port_names:
        port_names = _load_port_names()

    # curl mit URL -> Service-Name aus Port ableiten
    curl_match = re.search(r'curl\s+.*?localhost:(\d+)(/\S*)?', text)
    if curl_match:
        port = curl_match.group(1)
        path = curl_match.group(2) or ''
        service = port_names.get(port, f'Dienst auf Port {port}')
        # Spezifische Pfade erkennen
        if '/transcribe' in path:
            return f'Audio an {service} senden (Transkription)'
        if '/api/generate' in path:
            return f'Anfrage an {service} (Bildgenerator) senden'
        if '/api/v1/workflows' in path:
            return f'n8n Workflow starten (Automation)'
        return f'Anfrage an {service} senden'

    # cat ~/.secrets-active/...
    cat_match = re.search(r'cat\s+~/\.secrets-active/([a-zA-Z0-9_-]+)\.env', text)
    if cat_match:
        return f'API-Schluessel lesen ({cat_match.group(1)})'

    # ls ~/.secrets-active/...
    ls_match = re.search(r'ls\s+~/\.secrets-active/([a-zA-Z0-9_-]+)\.env', text)
    if ls_match:
        return f'Pruefen ob Secret freigegeben ist ({ls_match.group(1)})'

    # sudo cp ~/.secrets/...
    if 'sudo cp ~/.secrets/' in text:
        return 'Manueller Kopier-Befehl fuer Secret'

    return text


def _parse_dataflow_graph_from_skill(filepath):
    """Parse SKILL.md und erzeuge strukturierten Dataflow-Graph mit Nodes."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    # Ablauf-Sektion finden
    ablauf_match = re.search(
        r'#+\s*(?:Ablauf|Workflow|Flow|Schritte|Steps|Vorgehensweise)(.*?)(?=\n#+\s|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    if not ablauf_match:
        return None

    section = ablauf_match.group(1).strip()
    lines = section.split('\n')

    port_names = _load_port_names()
    nodes = []
    node_counter = [0]

    def next_id():
        node_counter[0] += 1
        return f's{node_counter[0]}'

    # Code-Bloecke entfernen und inline-code extrahieren
    # Zuerst: fenced code blocks zu einer Zeile kollabieren
    cleaned_lines = []
    in_code_block = False
    code_content = []
    for line in lines:
        if line.strip().startswith('```'):
            if in_code_block:
                # End of code block - humanize the content
                raw = ' '.join(code_content)
                humanized = _humanize_step(raw, port_names)
                if humanized != raw:
                    cleaned_lines.append(f'  CODE_HUMANIZED:{humanized}')
                in_code_block = False
                code_content = []
            else:
                in_code_block = True
                code_content = []
            continue
        if in_code_block:
            code_content.append(line.strip())
        else:
            cleaned_lines.append(line)

    # Parse nummerierte Steps
    i = 0
    pending_nodes = []
    while i < len(cleaned_lines):
        line = cleaned_lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Nummerierter Step: "1. ...", "2. ..."
        step_match = re.match(r'^\d+[\.\)]\s*(.*)', line)
        if not step_match:
            # Code-humanized Zeile (gehoert zum vorherigen Step)
            code_match = re.match(r'CODE_HUMANIZED:(.*)', line.strip())
            if code_match and pending_nodes:
                pending_nodes[-1]['detail'] = code_match.group(1)
            i += 1
            continue

        step_text = step_match.group(1)

        # Inline-Code humanisieren
        inline_code = re.findall(r'`([^`]+)`', step_text)
        raw_text = step_text
        for code in inline_code:
            humanized = _humanize_step(code, port_names)
            if humanized != code:
                # Wenn der Step-Text "Label: `code`" ist, verwende nur die humanisierte Version
                if re.match(r'^[^:]+:\s*`' + re.escape(code) + r'`\s*$', step_text):
                    step_text = humanized
                else:
                    step_text = step_text.replace(f'`{code}`', humanized)
            else:
                step_text = step_text.replace(f'`{code}`', code)

        # Sub-Skill erkennen
        sub_skill_match = re.search(r'\(?\s*Skill:\s*([a-zA-Z0-9_-]+)', step_text)
        if sub_skill_match:
            skill_name = sub_skill_match.group(1)
            # Label bereinigen
            label = re.sub(r'\s*\(?\s*Skill:\s*[a-zA-Z0-9_-]+[,\s]*(?:Secret:\s*[a-zA-Z0-9_-]+)?\s*\)?\s*', '', step_text).strip()
            if not label:
                label = f'Skill: {skill_name}'
            nid = next_id()
            pending_nodes.append({
                'id': nid, 'type': 'sub-skill',
                'label': label,
                'detail': f'Skill: {skill_name}',
                'icon': 'puzzle', 'next': [],
            })
            i += 1
            continue

        # Condition erkennen: "Wenn vorhanden", "Wenn nicht"
        if re.match(r'Wenn\s+(nicht\s+)?vorhanden', step_text):
            # Sammle die naechsten Unter-Punkte als Branches
            nid = next_id()
            condition_label = 'Secret freigegeben?'

            # Success branch (Wenn vorhanden)
            yes_nodes = []
            no_nodes = []

            if 'nicht' not in step_text:
                # "Wenn vorhanden: ..."
                rest = re.sub(r'^Wenn\s+vorhanden:\s*', '', step_text).strip()
                if rest:
                    yid = next_id()
                    yes_nodes.append({
                        'id': yid, 'type': 'step',
                        'label': rest, 'icon': 'check', 'next': [],
                    })

                # Naechste Zeile: "Wenn nicht vorhanden:"
                i += 1
                if i < len(cleaned_lines):
                    next_line = cleaned_lines[i].strip()
                    no_match = re.match(r'^\d+[\.\)]\s*Wenn\s+nicht\s+vorhanden:', next_line)
                    if no_match:
                        # Sammle Sub-Items fuer den Nein-Pfad
                        i += 1
                        no_label = 'Abbruch -- Secret fehlt'
                        no_details = []
                        while i < len(cleaned_lines):
                            sub = cleaned_lines[i].strip()
                            if re.match(r'^\d+[\.\)]', sub):
                                break
                            sub_item = re.sub(r'^\s*[-*]\s*', '', sub)
                            if sub_item and len(sub_item) > 3:
                                # Humanisiere Level-Beschreibungen
                                sub_item = _humanize_step(sub_item, port_names)
                                no_details.append(sub_item)
                            i += 1

                        noid = next_id()
                        no_node = {
                            'id': noid, 'type': 'step',
                            'label': no_label, 'icon': 'stop', 'next': [],
                        }
                        if no_details:
                            no_node['details'] = no_details
                        no_nodes.append(no_node)
                    else:
                        i -= 1  # Nicht konsumiert
            else:
                # "Wenn nicht vorhanden:" zuerst
                i += 1
                no_label = 'Abbruch -- Secret fehlt'
                no_details = []
                while i < len(cleaned_lines):
                    sub = cleaned_lines[i].strip()
                    if re.match(r'^\d+[\.\)]', sub):
                        break
                    sub_item = re.sub(r'^\s*[-*]\s*', '', sub)
                    if sub_item and len(sub_item) > 3:
                        no_details.append(_humanize_step(sub_item, port_names))
                    i += 1

                noid = next_id()
                no_node = {
                    'id': noid, 'type': 'step',
                    'label': no_label, 'icon': 'stop', 'next': [],
                }
                if no_details:
                    no_node['details'] = no_details
                no_nodes.append(no_node)

            # Condition-Node zusammenbauen
            branches = []
            if yes_nodes:
                branches.append({
                    'label': 'Ja', 'outcome': 'success',
                    'next': [n['id'] for n in yes_nodes],
                })
            if no_nodes:
                branches.append({
                    'label': 'Nein', 'outcome': 'failure',
                    'next': [n['id'] for n in no_nodes],
                })

            cond_node = {
                'id': nid, 'type': 'condition',
                'label': condition_label,
                'branches': branches,
            }
            pending_nodes.append(cond_node)
            pending_nodes.extend(yes_nodes)
            pending_nodes.extend(no_nodes)
            continue

        # Normaler Step
        nid = next_id()
        # Icon bestimmen
        icon = 'step'
        lower = step_text.lower()
        if any(w in lower for w in ['ergebnis', 'zeigen', 'fertig', 'liefert']):
            icon = 'check'
        elif any(w in lower for w in ['lesen', 'key', 'schluessel', 'token']):
            icon = 'key'
        elif any(w in lower for w in ['senden', 'generieren', 'bild']):
            icon = 'image'
        elif any(w in lower for w in ['pruefen', 'check', 'freigabe']):
            icon = 'shield'

        # Trailing Doppelpunkt entfernen
        step_text = step_text.rstrip(':').strip()

        node = {
            'id': nid, 'type': 'step',
            'label': step_text, 'icon': icon, 'next': [],
        }
        pending_nodes.append(node)
        i += 1

    if not pending_nodes:
        return None

    # Next-Pointer setzen (linear, ausser bei Conditions)
    condition_ids = {n['id'] for n in pending_nodes if n['type'] == 'condition'}
    # IDs die Condition-Branches referenzieren
    branch_target_ids = set()
    for n in pending_nodes:
        if n['type'] == 'condition':
            for b in n.get('branches', []):
                branch_target_ids.update(b.get('next', []))

    # Lineare Verkettung fuer Nicht-Branch-Nodes
    main_flow = [n for n in pending_nodes if n['id'] not in branch_target_ids]
    for idx, node in enumerate(main_flow):
        if node['type'] == 'condition':
            continue  # Branches sind schon gesetzt
        if idx + 1 < len(main_flow):
            node['next'] = [main_flow[idx + 1]['id']]

    return {'nodes': pending_nodes}


# Skills installed via `npx skills add` land in .agents/skills/ directories
# and/or are tracked in skills-lock.json files.
# We also keep a set of known installed skill IDs from lock files.
_installed_skill_ids = set()


def init_skills_visualizer(data_dir=None):
    """Initialize with data_dir for n8n-workflows-meta.json."""
    global PERSONAS_DIR, DATA_DIR
    PERSONAS_DIR = os.path.expanduser('~/repos/butler-dashboard-v3/personas')
    DATA_DIR = data_dir
    _load_installed_skill_ids()


def _load_installed_skill_ids():
    """Collect all skill IDs from skills-lock.json files."""
    global _installed_skill_ids
    _installed_skill_ids = set()
    if not PERSONAS_DIR or not os.path.isdir(PERSONAS_DIR):
        return
    for lock_file in glob.glob(os.path.join(PERSONAS_DIR, '*', 'skills-lock.json')):
        try:
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
            for skill_id in lock_data.get('skills', {}):
                _installed_skill_ids.add(skill_id)
        except (OSError, json.JSONDecodeError):
            continue


def _parse_skill_frontmatter(filepath):
    """Parse YAML frontmatter from a SKILL.md file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {'raw_content': content}

    frontmatter = {}
    for line in match.group(1).strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            frontmatter[key.strip()] = val.strip()

    body = content[match.end():].strip()
    lines = body.split('\n')
    summary_lines = []
    for line in lines:
        if line.startswith('#'):
            continue
        if line.strip() == '' and summary_lines:
            break
        if line.strip():
            summary_lines.append(line.strip())
    if summary_lines:
        frontmatter['summary'] = ' '.join(summary_lines[:2])

    return frontmatter


def _parse_secrets_from_skill(filepath):
    """Extract secret requirements from SKILL.md content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    secrets = []
    skip_names = {
        'manager', 'freigabe', 'active', 'handling', 'name', 'ls',
        'secret', 'secrets', 'key', 'token', 'file', 'wert',
    }

    # Pattern: Benoetigt Secret `discord-bot-token` (Level 3)
    # Or: Secret: `venice-api-key`
    secret_patterns = re.findall(
        r'[Bb]enoetigt\s+Secret\s+`([a-zA-Z0-9_-]+)`\s*(?:\(([^)]*)\))?',
        content
    )
    for name, extra in secret_patterns:
        if name.lower() in skip_names:
            continue
        level = None
        level_match = re.search(r'[Ll]evel\s*(\d)', extra or '')
        if level_match:
            level = int(level_match.group(1))
        if not any(s['name'] == name for s in secrets):
            secrets.append({'name': name, 'level': level or 1})

    # Check for cat ~/.secrets-active/NAME.env patterns (actual usage)
    active_refs = re.findall(
        r'cat\s+~/\.secrets-active/([a-zA-Z0-9_-]+)\.env', content
    )
    for name in active_refs:
        if name.lower() not in skip_names and not any(s['name'] == name for s in secrets):
            secrets.append({'name': name, 'level': 1})

    # Check for explicit "Secret:" or "API Key:" declarations
    explicit = re.findall(
        r'(?:Secret|API[- ]?Key|Token)\s*:\s*`?([a-zA-Z][a-zA-Z0-9_-]{3,})`?',
        content
    )
    for name in explicit:
        if name.lower() not in skip_names and not any(s['name'] == name for s in secrets):
            secrets.append({'name': name, 'level': 1})

    return secrets


def _parse_dataflow_from_skill(filepath):
    """Extract data flow steps from SKILL.md content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    steps = []

    # Look for numbered list items under "Ablauf" or similar sections
    ablauf_match = re.search(
        r'#+\s*(?:Ablauf|Workflow|Flow|Schritte|Steps|Vorgehensweise)(.*?)(?=\n#+|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    if ablauf_match:
        section = ablauf_match.group(1)
        for line in section.strip().split('\n'):
            step = re.sub(r'^\s*\d+[\.\)]\s*', '', line.strip())
            step = re.sub(r'^\s*[-*]\s*', '', step)
            if step and len(step) > 5:
                steps.append(step)

    return steps[:6]


def _get_file_date(filepath):
    """Get modification date of a file."""
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except OSError:
        return None


def _is_installed_skill(entry, skill_dir):
    """Check if a skill in ~/.claude/skills/ was installed externally."""
    # Check if it's in the lock file
    if entry in _installed_skill_ids:
        return True
    # Check if the actual directory is inside .agents/skills/ (symlink target)
    real_path = os.path.realpath(skill_dir)
    if '.agents' in real_path or 'agents/skills' in real_path:
        return True
    # Check if it's a symlink pointing to .agents/
    if os.path.islink(skill_dir):
        link_target = os.readlink(skill_dir)
        if '.agents' in link_target or 'agents/skills' in link_target:
            return True
    return False


def _scan_hermes_skills():
    """Scan ~/.hermes/skills/ for Hermes Agent skills with rank metadata."""
    skills = []
    if not os.path.isdir(HERMES_SKILLS_DIR):
        return skills

    # Try to load load-counts from Hermes state.db (skill load events)
    load_counts = {}
    if os.path.isfile(HERMES_STATE_DB):
        try:
            import sqlite3
            conn = sqlite3.connect(HERMES_STATE_DB)
            cur = conn.cursor()
            # Look for skill_load events in tool_call_log or session data
            # Use a broad search across the DB
            tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            for tbl in tables:
                tname = tbl[0]
                try:
                    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({tname})").fetchall()]
                    if 'tool_name' in cols and 'created_at' in cols:
                        rows = cur.execute(f"SELECT tool_name, COUNT(*) as cnt FROM {tname} WHERE tool_name LIKE '%skill_view%' OR tool_name LIKE '%skills_list%' GROUP BY tool_name").fetchall()
                        for r in rows:
                            skill_id = r[0].replace('skill_view:', '').replace('skills_list:', '')
                            if skill_id:
                                load_counts[skill_id] = load_counts.get(skill_id, 0) + r[1]
                except Exception:
                    pass
            conn.close()
        except Exception:
            pass

    ratings = _load_ratings()

    for category in sorted(os.listdir(HERMES_SKILLS_DIR)):
        cat_path = os.path.join(HERMES_SKILLS_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        for entry in sorted(os.listdir(cat_path)):
            skill_path = os.path.join(cat_path, entry)
            skill_file = os.path.join(skill_path, 'SKILL.md')
            if not os.path.isfile(skill_file):
                continue

            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse YAML-like frontmatter
            frontmatter = {}
            fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if fm_match:
                import yaml
                try:
                    frontmatter = yaml.safe_load(fm_match.group(1)) or {}
                except Exception:
                    # Fallback: simple line-by-line parse
                    for line in fm_match.group(1).strip().split('\n'):
                        if ':' in line:
                            key, val = line.split(':', 1)
                            frontmatter[key.strip()] = val.strip()

            name = frontmatter.get('name', entry)
            description = frontmatter.get('description', '')
            version = str(frontmatter.get('version', '')) if frontmatter.get('version') else ''

            # Extract tags from metadata.hermes.tags
            tags = []
            metadata = frontmatter.get('metadata', {})
            if isinstance(metadata, dict):
                hermes_meta = metadata.get('hermes', {})
                if isinstance(hermes_meta, dict):
                    tags = hermes_meta.get('tags', []) or []
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.strip('[]').split(',') if t.strip()]

            # Count references/
            ref_dir = os.path.join(skill_path, 'references')
            ref_count = 0
            ref_files = []
            if os.path.isdir(ref_dir):
                ref_files = [f for f in os.listdir(ref_dir) if f.endswith('.md')]
                ref_count = len(ref_files)

            # Get file mtime as last_load
            try:
                mtime = os.path.getmtime(skill_file)
                last_load = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            except OSError:
                last_load = ''

            # Derive load count: custom rating field + heuristic
            stored_ratings = ratings.get(entry, {})
            load_count = stored_ratings.get('load_count', 0)
            # Fallback: use reference count as proxy for quality/engagement
            if load_count == 0:
                load_count = load_counts.get(entry, 0)
            if load_count == 0:
                load_count = ref_count  # heuristic proxy

            # Determine rank
            has_version = bool(version and version != '0')
            is_archived = category == '.archive'

            if is_archived:
                rank = 'archived'
            elif load_count > 50 or (has_version and ref_count >= 10):
                rank = 'gold'
            elif load_count >= 10 or (has_version and ref_count >= 3) or ref_count >= 5:
                rank = 'silver'
            else:
                rank = 'bronze'

            skills.append({
                'id': entry,
                'name': name,
                'description': description,
                'version': version,
                'category': category,
                'source': 'hermes',
                'source_detail': f'~/.hermes/skills/{category}/{entry}/',
                'rank': rank,
                'load_count': load_count,
                'last_load': last_load,
                'bundle_count': 1 if category and not category.startswith('.') else 0,
                'references_count': ref_count,
                'has_skill_file': True,
                'tags': tags,
                'installed': last_load,
                'secrets': _parse_secrets_from_skill(skill_file),
                'dataflow': _parse_dataflow_from_skill(skill_file),
            })

    return skills


def _scan_own_skills():
    """Scan ~/.claude/skills/ for custom and installed skills."""
    eigen = []
    installiert = []
    if not os.path.isdir(CLAUDE_SKILLS_DIR):
        return eigen, installiert

    for entry in sorted(os.listdir(CLAUDE_SKILLS_DIR)):
        skill_dir = os.path.join(CLAUDE_SKILLS_DIR, entry)
        if not os.path.isdir(skill_dir):
            continue
        # Skip .agents directory itself
        if entry.startswith('.'):
            continue

        skill_file = os.path.join(skill_dir, 'SKILL.md')
        # For symlinks, resolve to find actual SKILL.md
        if os.path.islink(skill_dir):
            real_dir = os.path.realpath(skill_dir)
            skill_file = os.path.join(real_dir, 'SKILL.md')

        meta = _parse_skill_frontmatter(skill_file) if os.path.isfile(skill_file) else {}
        secrets = _parse_secrets_from_skill(skill_file) if os.path.isfile(skill_file) else []
        dataflow = _parse_dataflow_from_skill(skill_file) if os.path.isfile(skill_file) else []

        is_installed = _is_installed_skill(entry, skill_dir)

        skill_data = {
            'id': entry,
            'name': meta.get('name', entry),
            'description': meta.get('description', ''),
            'summary': meta.get('summary', ''),
            'source': 'installiert' if is_installed else 'eigen',
            'source_detail': f'~/.claude/skills/{entry}/',
            'installed': _get_file_date(skill_dir),
            'has_skill_file': os.path.isfile(skill_file),
            'secrets': secrets,
            'dataflow': dataflow,
        }

        if is_installed:
            installiert.append(skill_data)
        else:
            eigen.append(skill_data)

    return eigen, installiert


def _scan_external_skills():
    """Scan personas/*/skills-lock.json for externally installed skills."""
    skills = []
    if not PERSONAS_DIR or not os.path.isdir(PERSONAS_DIR):
        return skills

    for lock_file in glob.glob(os.path.join(PERSONAS_DIR, '*', 'skills-lock.json')):
        persona = os.path.basename(os.path.dirname(lock_file))
        try:
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        for skill_id, info in lock_data.get('skills', {}).items():
            skill_md_paths = glob.glob(
                os.path.join(os.path.dirname(lock_file), '**', skill_id, 'SKILL.md'),
                recursive=True
            )
            meta = {}
            secrets = []
            dataflow = []
            if skill_md_paths:
                meta = _parse_skill_frontmatter(skill_md_paths[0]) or {}
                secrets = _parse_secrets_from_skill(skill_md_paths[0])
                dataflow = _parse_dataflow_from_skill(skill_md_paths[0])

            # Check if this skill is already captured via _scan_own_skills
            # (it might be symlinked into ~/.claude/skills/ too)
            own_path = os.path.join(CLAUDE_SKILLS_DIR, skill_id)
            if os.path.isdir(own_path):
                continue  # Already captured as 'installiert'

            skills.append({
                'id': skill_id,
                'name': meta.get('name', skill_id),
                'description': meta.get('description', ''),
                'summary': meta.get('summary', ''),
                'source': 'installiert',
                'source_detail': info.get('source', ''),
                'installed': _get_file_date(lock_file),
                'persona': persona,
                'has_skill_file': bool(skill_md_paths),
                'secrets': secrets,
                'dataflow': dataflow,
            })

    return skills


def _scan_anthropic_plugins():
    """Scan ~/.claude/plugins/marketplaces/ for Anthropic plugin skills."""
    skills = []
    if not os.path.isdir(CLAUDE_PLUGINS_DIR):
        return skills

    for skill_file in glob.glob(
        os.path.join(CLAUDE_PLUGINS_DIR, '**', 'skills', '*', 'SKILL.md'),
        recursive=True
    ):
        skill_dir = os.path.dirname(skill_file)
        skill_id = os.path.basename(skill_dir)
        meta = _parse_skill_frontmatter(skill_file) or {}
        secrets = _parse_secrets_from_skill(skill_file)
        dataflow = _parse_dataflow_from_skill(skill_file)

        parts = skill_file.split(os.sep)
        plugin_name = ''
        for keyword in ('plugins', 'external_plugins'):
            indices = [i for i, p in enumerate(parts) if p == keyword]
            for idx in reversed(indices):
                if idx + 1 < len(parts) and parts[idx + 1] not in ('marketplaces', 'cache'):
                    plugin_name = parts[idx + 1]
                    break
            if plugin_name:
                break

        skills.append({
            'id': f'{plugin_name}/{skill_id}' if plugin_name else skill_id,
            'name': meta.get('name', skill_id),
            'description': meta.get('description', ''),
            'summary': meta.get('summary', ''),
            'source': 'anthropic',
            'source_detail': plugin_name or 'anthropic-plugin',
            'installed': _get_file_date(skill_file),
            'has_skill_file': True,
            'secrets': secrets,
            'dataflow': dataflow,
        })

    return skills


def _scan_n8n_skills():
    """Scan n8n-workflows-meta.json for workflow-based skills."""
    skills = []
    if not DATA_DIR:
        return skills

    meta_file = os.path.join(DATA_DIR, 'n8n-workflows-meta.json')
    if not os.path.isfile(meta_file):
        return skills

    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return skills

    workflows = data.get('workflows', {})
    settings = _load_settings()

    for wf_id, wf in workflows.items():
        category = wf.get('category', '')
        if category not in N8N_RELEVANT_CATEGORIES:
            continue

        status = wf.get('status', '')
        in_use = wf.get('inUse', False)
        # Only LIVE, or PROTO with inUse=true
        if status == 'LIVE' or (status == 'PROTO' and in_use):
            skill_id = f'n8n/{wf_id}'
            skills.append({
                'id': skill_id,
                'name': wf.get('name', wf_id),
                'description': wf.get('description', ''),
                'source': 'n8n',
                'source_detail': category,
                'n8n_id': wf_id,
                'node_count': wf.get('nodeCount', 0),
                'status': status,
                'installed': wf.get('updatedAt', '')[:10] if wf.get('updatedAt') else None,
                'has_skill_file': False,
                'secrets': N8N_SECRETS.get(category, []),
                'dataflow': [],
                'show_in_all': settings.get(skill_id, {}).get('show_in_all', False),
            })

    return skills


def _load_settings():
    """Load skill settings from settings section of ratings file."""
    ratings = _load_ratings()
    return ratings.get('_settings', {})


def _save_settings(settings):
    """Save skill settings into ratings file under _settings key."""
    ratings = _load_ratings()
    ratings['_settings'] = settings
    _save_ratings(ratings)


def _load_ratings():
    """Load ratings from JSON file."""
    if os.path.isfile(RATINGS_FILE):
        try:
            with open(RATINGS_FILE, 'r') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _save_ratings(ratings):
    """Save ratings to JSON file."""
    os.makedirs(os.path.dirname(RATINGS_FILE), exist_ok=True)
    with open(RATINGS_FILE, 'w') as f:
        json.dump(ratings, f, indent=2)


@skills_visualizer_bp.route('/skills', methods=['GET'])
def get_skills():
    """Return all installed skills from all sources."""
    eigen, installiert_from_own = _scan_own_skills()
    installiert_from_lock = _scan_external_skills()
    anthropic = _scan_anthropic_plugins()
    n8n = _scan_n8n_skills()
    hermes = _scan_hermes_skills()

    installiert = installiert_from_own + installiert_from_lock
    all_skills = eigen + installiert + anthropic + n8n + hermes

    # Build reverse mapping: claude_skill_id -> best n8n workflow
    sister_reverse = {}
    for n8n_skill in n8n:
        wf_id = n8n_skill.get('n8n_id', '')
        sister = SISTER_SKILLS.get(wf_id)
        if sister:
            claude_id = sister['skill']
            # Prefer LIVE over PROTO
            if claude_id not in sister_reverse or n8n_skill.get('status') == 'LIVE':
                sister_reverse[claude_id] = {
                    'id': n8n_skill['n8n_id'],
                    'name': n8n_skill['name'],
                }

    # Attach ratings and sister info to each skill
    ratings = _load_ratings()
    for skill in all_skills:
        skill['ratings'] = ratings.get(skill['id'], {})
        # Add n8n sister link for regular skills
        if skill['source'] != 'n8n' and skill['id'] in sister_reverse:
            skill['n8n_sister'] = sister_reverse[skill['id']]

    return jsonify({
        'skills': all_skills,
        'stats': {
            'total': len(eigen) + len(installiert) + len(anthropic) + len(hermes),
            'eigen': len(eigen),
            'installiert': len(installiert),
            'anthropic': len(anthropic),
            'n8n': len(n8n),
            'hermes': len(hermes),
        }
    }), 200


@skills_visualizer_bp.route('/skills/<path:skill_id>/detail', methods=['GET'])
def get_skill_detail(skill_id):
    """Return extended skill details including content, secrets, dataflow."""
    # Search across all sources for the skill
    content = None
    skill_file = None

    # Own/installed skills
    own_path = os.path.join(CLAUDE_SKILLS_DIR, skill_id, 'SKILL.md')
    if os.path.islink(os.path.join(CLAUDE_SKILLS_DIR, skill_id)):
        real_dir = os.path.realpath(os.path.join(CLAUDE_SKILLS_DIR, skill_id))
        own_path = os.path.join(real_dir, 'SKILL.md')
    if os.path.isfile(own_path):
        skill_file = own_path

    # External skills (personas)
    if not skill_file and PERSONAS_DIR:
        for match in glob.glob(
            os.path.join(PERSONAS_DIR, '**', skill_id, 'SKILL.md'),
            recursive=True
        ):
            skill_file = match
            break

    # Anthropic plugins (skill_id might be "plugin/skill")
    if not skill_file:
        search_id = skill_id.split('/')[-1] if '/' in skill_id else skill_id
        for match in glob.glob(
            os.path.join(CLAUDE_PLUGINS_DIR, '**', 'skills', search_id, 'SKILL.md'),
            recursive=True
        ):
            skill_file = match
            break

    if not skill_file:
        return jsonify({'error': 'Skill not found'}), 404

    with open(skill_file, 'r', encoding='utf-8') as f:
        content = f.read()

    meta = _parse_skill_frontmatter(skill_file) or {}
    secrets = _parse_secrets_from_skill(skill_file)
    dataflow = _parse_dataflow_from_skill(skill_file)
    dataflow_graph = _parse_dataflow_graph_from_skill(skill_file)
    ratings = _load_ratings().get(skill_id, {})

    # Check for n8n sister workflow
    n8n_sister = None
    sister_reverse = {}
    for wf_id, sister_def in SISTER_SKILLS.items():
        if sister_def['skill'] == skill_id:
            sister_reverse[wf_id] = sister_def
    if sister_reverse:
        # Pick best: prefer LIVE workflows
        best_wf_id = next(iter(sister_reverse))
        if DATA_DIR:
            meta_file = os.path.join(DATA_DIR, 'n8n-workflows-meta.json')
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    n8n_data = json.load(f)
                for wid in sister_reverse:
                    wf = n8n_data.get('workflows', {}).get(wid, {})
                    if wf.get('status') == 'LIVE':
                        best_wf_id = wid
                        break
                best_wf = n8n_data.get('workflows', {}).get(best_wf_id, {})
                n8n_sister = {
                    'id': best_wf_id,
                    'name': best_wf.get('name', best_wf_id),
                }
            except (OSError, json.JSONDecodeError):
                pass

    result = {
        'id': skill_id,
        'name': meta.get('name', skill_id),
        'description': meta.get('description', ''),
        'summary': meta.get('summary', ''),
        'content': content,
        'secrets': secrets,
        'dataflow': dataflow,
        'dataflow_graph': dataflow_graph,
        'ratings': ratings,
    }
    if n8n_sister:
        result['n8n_sister'] = n8n_sister

    return jsonify(result), 200


@skills_visualizer_bp.route('/skills/n8n/<wf_id>/detail', methods=['GET'])
def get_n8n_detail(wf_id):
    """Return extended details for an n8n workflow skill."""
    if not DATA_DIR:
        return jsonify({'error': 'n8n data not configured'}), 404

    meta_file = os.path.join(DATA_DIR, 'n8n-workflows-meta.json')
    if not os.path.isfile(meta_file):
        return jsonify({'error': 'n8n meta not found'}), 404

    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return jsonify({'error': 'Failed to read n8n meta'}), 500

    wf = data.get('workflows', {}).get(wf_id)
    if not wf:
        return jsonify({'error': 'Workflow not found'}), 404

    category = wf.get('category', '')
    settings = _load_settings()
    skill_id = f'n8n/{wf_id}'

    # Sister skill info
    sister_info = None
    sister_def = SISTER_SKILLS.get(wf_id)
    if sister_def:
        # Try to find the Claude skill name from scan
        sister_name = sister_def['skill']
        # Quick scan to get display name
        eigen, installiert_from_own = _scan_own_skills()
        all_claude = eigen + installiert_from_own + _scan_external_skills()
        for s in all_claude:
            if s['id'] == sister_def['skill']:
                sister_name = s['name']
                break
        sister_info = {
            'skill_id': sister_def['skill'],
            'name': sister_name,
            'relation': sister_def['relation'],
        }

    return jsonify({
        'id': skill_id,
        'n8n_id': wf_id,
        'name': wf.get('name', wf_id),
        'description': wf.get('description', ''),
        'notes': wf.get('notes', ''),
        'category': category,
        'status': wf.get('status', ''),
        'node_count': wf.get('nodeCount', 0),
        'active': wf.get('active', False),
        'updated_at': wf.get('updatedAt', ''),
        'in_use': wf.get('inUse', False),
        'dev_status': wf.get('devStatus', ''),
        'secrets': N8N_SECRETS.get(category, []),
        'dataflow': N8N_DATAFLOWS.get(wf_id, []),
        'dataflow_graph': N8N_DATAFLOW_GRAPHS.get(wf_id),
        'sister_skill': sister_info,
        'show_in_all': settings.get(skill_id, {}).get('show_in_all', False),
    }), 200


@skills_visualizer_bp.route('/skills/<path:skill_id>/ratings', methods=['GET'])
def get_skill_ratings(skill_id):
    """Get ratings for a skill."""
    ratings = _load_ratings()
    return jsonify(ratings.get(skill_id, {})), 200


@skills_visualizer_bp.route('/skills/<path:skill_id>/ratings', methods=['POST'])
def set_skill_ratings(skill_id):
    """Set ratings for a skill."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    ratings = _load_ratings()
    if skill_id not in ratings:
        ratings[skill_id] = {}

    if 'verstehe' in data:
        ratings[skill_id]['verstehe'] = max(0, min(5, int(data['verstehe'])))
    if 'nutze' in data:
        ratings[skill_id]['nutze'] = max(0, min(5, int(data['nutze'])))

    _save_ratings(ratings)
    return jsonify(ratings[skill_id]), 200


@skills_visualizer_bp.route('/skills/<path:skill_id>/settings', methods=['GET'])
def get_skill_settings(skill_id):
    """Get settings for a skill."""
    settings = _load_settings()
    return jsonify(settings.get(skill_id, {})), 200


@skills_visualizer_bp.route('/skills/<path:skill_id>/settings', methods=['POST'])
def set_skill_settings(skill_id):
    """Set settings for a skill (e.g. show_in_all toggle)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    settings = _load_settings()
    if skill_id not in settings:
        settings[skill_id] = {}

    if 'show_in_all' in data:
        settings[skill_id]['show_in_all'] = bool(data['show_in_all'])

    _save_settings(settings)
    return jsonify(settings[skill_id]), 200
