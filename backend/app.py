"""
Skill Cockpit — Standalone Flask App.
Port 9123. Serviert React-Frontend (Vite Build) + API-Endpunkte.
"""

import os
import json
import sqlite3
import yaml
import glob
import re
import subprocess
from datetime import datetime
from flask import Flask, Blueprint, jsonify, request, send_from_directory

HOME = os.path.expanduser('~')
HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(os.path.dirname(HERE), 'frontend', 'dist')

# ── Blueprint ──
skills_bp = Blueprint('skills', __name__)

# ── Helpers (from routes.py minimal) ──

HERMES_SKILLS_DIR = os.path.join(HOME, '.hermes', 'skills')
HERMES_STATE_DB = os.path.join(HOME, '.hermes', 'state.db')
BUNDLES_DIR = os.path.join(HOME, '.hermes', 'bundles')

RANK_ORDER = {'gold': 0, 'silver': 1, 'bronze': 2}
RANK_CONFIG = {
    'gold': {'label': 'Gold', 'color': '#f5b800'},
    'silver': {'label': 'Silber', 'color': '#94a3b8'},
    'bronze': {'label': 'Bronze', 'color': '#cd7f32'},
}


def _load_skill_usage():
    """Lade usage-Daten aus state.db."""
    if not os.path.isfile(HERMES_STATE_DB):
        return {}
    try:
        conn = sqlite3.connect(f'file:{HERMES_STATE_DB}?mode=ro', uri=True)
        cur = conn.cursor()
        cur.execute(
            "SELECT key, load_count, last_loaded FROM skill_stats "
            "ORDER BY load_count DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return {r[0]: {'load_count': r[1], 'last_load': r[2]} for r in rows}
    except Exception:
        return {}


def _parse_frontmatter(filepath):
    """Parse YAML frontmatter from a SKILL.md."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {}, ''
    if not content.startswith('---'):
        return {}, content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except Exception:
        meta = {}
    return meta, parts[2].strip()


def _get_file_date(filepath):
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return None


def _count_references(skill_dir):
    ref_dir = os.path.join(skill_dir, 'references')
    if os.path.isdir(ref_dir):
        return len([f for f in os.listdir(ref_dir)
                    if os.path.isfile(os.path.join(ref_dir, f))])
    return 0


def _scan_skills():
    """Scan all Hermes skills."""
    usage = _load_skill_usage()
    skills = []
    if not os.path.isdir(HERMES_SKILLS_DIR):
        return skills
    for cat_dir in sorted(os.listdir(HERMES_SKILLS_DIR)):
        cat_path = os.path.join(HERMES_SKILLS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith('.'):
            continue
        for entry in sorted(os.listdir(cat_path)):
            skill_dir = os.path.join(cat_path, entry)
            skill_file = os.path.join(skill_dir, 'SKILL.md')
            if not os.path.isfile(skill_file):
                continue
            meta, body = _parse_frontmatter(skill_file)
            refs = _count_references(skill_dir)
            key = f'{cat_dir}/{entry}'
            stats = usage.get(key, {})
            skills.append({
                'id': key,
                'name': meta.get('name', entry),
                'description': meta.get('description', ''),
                'version': meta.get('metadata', {}).get('version', ''),
                'category': cat_dir,
                'rank': meta.get('rank', 'bronze'),
                'load_count': stats.get('load_count', 0),
                'last_load': stats.get('last_load', None),
                'references_count': refs,
                'source': 'hermes',
            })
    return skills


def _scan_cron_jobs():
    """Scan Hermes cron jobs and build skill→cron mapping."""
    cron_path = os.path.join(HOME, '.hermes', 'cron', 'jobs.json')
    if not os.path.isfile(cron_path):
        return {}
    try:
        with open(cron_path, 'r') as f:
            data = json.load(f)
    except Exception:
        return {}
    # Format: {"jobs": [...], "updated_at": "..."}
    jobs_list = data.get('jobs', []) if isinstance(data, dict) else data
    if isinstance(jobs_list, dict):
        jobs_list = jobs_list.values()
    # Build map: skill_name → list of cron jobs
    skill_map = {}
    for job in jobs_list:
        if not isinstance(job, dict):
            continue
        if not job.get('enabled', True):
            continue
        # Collect skill names: from 'skills' (list) and 'skill' (singular)
        all_skills = job.get('skills', []) or []
        if isinstance(all_skills, str):
            all_skills = [all_skills]
        singular = job.get('skill')
        if singular and singular not in all_skills:
            all_skills.append(singular)
        if not all_skills:
            continue
        # Format schedule display
        sched_display = job.get('schedule_display', '')
        if not sched_display:
            sched = job.get('schedule', {})
            if isinstance(sched, dict):
                sched_display = sched.get('display', '')
        for sn in all_skills:
            if sn not in skill_map:
                skill_map[sn] = []
            skill_map[sn].append({
                'job_id': job.get('id', ''),
                'name': job.get('name', ''),
                'schedule': sched_display,
                'last_run_at': job.get('last_run_at', None),
                'next_run_at': job.get('next_run_at', None),
            })
    return skill_map


def _traffic_light(mtime_ts):
    """Return traffic light status based on last modified time."""
    if not mtime_ts:
        return 'gray', 'Unbekannt'
    now = datetime.now()
    diff = now - datetime.fromtimestamp(mtime_ts)
    if diff.days == 0:
        return 'green', 'Heute aktualisiert'
    elif diff.days <= 3:
        return 'yellow', '1–3 Tage alt'
    else:
        return 'red', '>3 Tage alt'


def _scan_all_references():
    """Scan ALL skills for references/ and return metadata with traffic light + cron mapping."""
    cron_map = _scan_cron_jobs()
    refs = []
    if not os.path.isdir(HERMES_SKILLS_DIR):
        return refs

    for cat_dir in sorted(os.listdir(HERMES_SKILLS_DIR)):
        cat_path = os.path.join(HERMES_SKILLS_DIR, cat_dir)
        if not os.path.isdir(cat_path) or cat_dir.startswith('.'):
            continue
        for entry in sorted(os.listdir(cat_path)):
            skill_dir = os.path.join(cat_path, entry)
            ref_dir = os.path.join(skill_dir, 'references')
            skill_file = os.path.join(skill_dir, 'SKILL.md')
            if not os.path.isdir(ref_dir) or not os.path.isfile(skill_file):
                continue

            # Read skill name from frontmatter
            meta, _ = _parse_frontmatter(skill_file)
            skill_name = meta.get('name', entry)

            # Check for cron association by skill_name or entry name
            cron_info = cron_map.get(skill_name) or cron_map.get(f'{cat_dir}/{entry}') or cron_map.get(f'{cat_dir}-{entry}') or []

            for fname in sorted(os.listdir(ref_dir)):
                fpath = os.path.join(ref_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                try:
                    st = os.stat(fpath)
                    mtime_ts = st.st_mtime
                    size = st.st_size
                except Exception:
                    mtime_ts = None
                    size = 0
                light, light_label = _traffic_light(mtime_ts)
                last_update = datetime.fromtimestamp(mtime_ts).strftime('%Y-%m-%d %H:%M') if mtime_ts else '—'

                refs.append({
                    'name': fname,
                    'skill_id': f'{cat_dir}/{entry}',
                    'skill_name': skill_name,
                    'category': cat_dir,
                    'path': fpath,
                    'size': size,
                    'size_formatted': _format_size(size),
                    'last_update': last_update,
                    'last_update_ts': mtime_ts,
                    'traffic_light': light,
                    'traffic_light_label': light_label,
                    'cron': cron_info[0] if cron_info else None,
                    'cron_count': len(cron_info),
                    'has_cron': len(cron_info) > 0,
                })
    return refs


def _format_size(bytes_val):
    if bytes_val < 1024:
        return f'{bytes_val} B'
    elif bytes_val < 1024 * 1024:
        return f'{bytes_val / 1024:.1f} KB'
    else:
        return f'{bytes_val / (1024*1024):.1f} MB'


def _scan_bundles():
    """Scan bundles from ~/.hermes/bundles/ and state.db weights."""
    if not os.path.isdir(BUNDLES_DIR):
        return [], {}
    bundles = []
    overlap = {}
    for fname in sorted(os.listdir(BUNDLES_DIR)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(BUNDLES_DIR, fname)
        meta, body = _parse_frontmatter(fpath)
        slug = fname.replace('.md', '')
        skill_slugs = [
            s.strip() for s in
            meta.get('skills', '').split(',') if s.strip()
        ]
        # track overlap
        for s in skill_slugs:
            if s not in overlap:
                overlap[s] = []
            overlap[s].append(slug)

        bundles.append({
            'slug': slug,
            'name': meta.get('name', slug),
            'description': meta.get('description', ''),
            'instruction': body.strip(),
            'skills': skill_slugs,
            'created': _get_file_date(fpath),
            'last_modified': _get_file_date(fpath),
            'file_path': fpath,
            'weight': {
                'skill_count': len(skill_slugs),
                'total_estimated_tokens': len(skill_slugs) * 250,
                'missing_skills': [],
            },
        })
    return bundles, overlap


# ── API Routes ──

@skills_bp.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'skill-cockpit'})


@skills_bp.route('/api/skills')
def get_skills():
    skills = _scan_skills()
    total = len(skills)
    by_rank = {}
    for s in skills:
        r = s.get('rank', 'unknown')
        by_rank[r] = by_rank.get(r, 0) + 1
    return jsonify({
        'skills': skills,
        'total': total,
        'by_rank': by_rank,
    })


@skills_bp.route('/api/skills/<path:skill_id>/detail')
def get_skill_detail(skill_id):
    skill_path = os.path.join(HERMES_SKILLS_DIR, skill_id, 'SKILL.md')
    if not os.path.isfile(skill_path):
        return jsonify({'error': 'not found'}), 404
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@skills_bp.route('/api/references')
def get_references():
    refs = _scan_all_references()
    # Summary stats
    total = len(refs)
    by_light = {}
    for r in refs:
        tl = r['traffic_light']
        by_light[tl] = by_light.get(tl, 0) + 1
    orphaned = [r for r in refs if not r['has_cron']]
    return jsonify({
        'references': refs,
        'total': total,
        'by_traffic_light': by_light,
        'orphaned_count': len(orphaned),
        'total_skills_with_refs': len(set(r['skill_id'] for r in refs)),
    })


@skills_bp.route('/api/references/<path:ref_id>/refresh', methods=['POST'])
def refresh_reference(ref_id):
    """Trigger the cron job associated with a reference."""
    refs = _scan_all_references()
    target = None
    for r in refs:
        # Build a unique ref_id: skill_id/name
        if f"{r['skill_id']}/{r['name']}" == ref_id:
            target = r
            break
    if not target:
        return jsonify({'error': 'reference not found'}), 404
    cron = target.get('cron')
    if not cron:
        return jsonify({'error': 'no cron job associated'}), 400
    # Trigger the cron via hermes CLI
    job_id = cron['job_id']
    try:
        result = subprocess.run(
            ['hermes', 'cron', 'run', job_id],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, 'HOME': HOME},
        )
        if result.returncode != 0:
            return jsonify({'error': f'cron run failed: {result.stderr.strip()}'}), 500
        return jsonify({
            'status': 'triggered',
            'job_id': job_id,
            'job_name': cron['name'],
            'output': result.stdout.strip(),
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'cron run timed out'}), 504
    except FileNotFoundError:
        return jsonify({'error': 'hermes CLI not found'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@skills_bp.route('/api/bundles', methods=['GET'])
def get_bundles():
    all_skills = _scan_skills()
    bundles, overlap = _scan_bundles()
    return jsonify({
        'bundles': bundles,
        'overlap': overlap,
        'total_skills': len(all_skills),
    })


@skills_bp.route('/api/bundles/overlap')
def get_bundle_overlap():
    _, overlap = _scan_bundles()
    return jsonify({'overlap': overlap})


@skills_bp.route('/api/bundles', methods=['POST'])
def create_bundle():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'name erforderlich'}), 400
    slug = data['name'].strip().lower().replace(' ', '-')
    fname = f'{slug}.md'
    fpath = os.path.join(BUNDLES_DIR, fname)
    skills_list = data.get('skills', [])
    frontmatter = {
        'name': data['name'].strip(),
        'description': data.get('description', ''),
        'skills': ', '.join(skills_list),
        'created': datetime.now().isoformat(),
        'modified': datetime.now().isoformat(),
    }
    body = data.get('instruction', '')
    content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False).strip()}\n---\n\n{body}\n"
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    return jsonify({'slug': slug, 'file': fname}), 201


# ── Flask App Factory ──

def create_app():
    app = Flask(__name__)
    app.register_blueprint(skills_bp)

    # Statisches Frontend servieren
    if os.path.isdir(FRONTEND_DIST):
        @app.route('/')
        def index():
            return send_from_directory(FRONTEND_DIST, 'index.html')

        @app.route('/assets/<path:filename>')
        def assets(filename):
            return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)

        @app.errorhandler(404)
        def fallback(e):
            # SPA fallback — alle nicht-API Routen zeigen index.html
            if request.path.startswith('/api/'):
                return jsonify({'error': 'not found'}), 404
            return send_from_directory(FRONTEND_DIST, 'index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=9123, debug=False)