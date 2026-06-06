import { useState, useEffect, useCallback, useMemo } from 'react'
import styles from './Page.module.css'

const TABS = [
  { id: 'skills', label: 'Skills' },
  { id: 'bundles', label: 'Bundles' },
  { id: 'references', label: 'References' },
]

const SORT_OPTIONS = [
  { id: 'alpha', label: 'Alphabetisch' },
  { id: 'rank', label: 'Rang' },
  { id: 'usage', label: 'Nutzung' },
  { id: 'age', label: 'Alter' },
]

const RANK_CONFIG = {
  gold: { label: 'Gold', cls: styles.rankGold },
  silver: { label: 'Silber', cls: styles.rankSilver },
  bronze: { label: 'Bronze', cls: styles.rankBronze },
}

function RankCircle({ rank }) {
  const config = RANK_CONFIG[rank]
  if (!config || rank === 'archived') return null
  return <span className={`${styles.rankCircle} ${config.cls}`} title={config.label} />
}

function MiniChart({ data }) {
  if (!data || data.length === 0) return <div className={styles.noData}>Keine Daten</div>
  const max = Math.max(...data, 1)
  return (
    <div className={styles.miniChart}>
      {data.map((v, i) => (
        <div
          key={i}
          className={styles.miniBar}
          style={{ height: `${(v / max) * 100}%` }}
          title={`Tag ${i + 1}: ${v}`}
        />
      ))}
    </div>
  )
}

function RefTrafficLight({ count }) {
  let color, label
  if (count >= 10) { color = styles.refGreen; label = 'Aktuell' }
  else if (count >= 3) { color = styles.refYellow; label = 'Veraltet' }
  else { color = styles.refRed; label = 'Minimal' }
  return <span className={`${styles.refStatusDot} ${color}`} title={`${count} references – ${label}`} />
}

function renderMarkdown(md) {
  if (!md) return ''
  let html = md
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold/italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    // Links
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>')
    // Line breaks
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>')
  return `<p>${html}</p>`
}

function SkillModal({ skill, onClose }) {
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(true)
  const detailUrl = `/api/skills/${skill.id}/detail`

  useEffect(() => {
    setDetailLoading(true)
    fetch(detailUrl)
      .then(r => r.json())
      .then(d => { setDetail(d); setDetailLoading(false) })
      .catch(() => setDetailLoading(false))
  }, [detailUrl])

  // Simulated 30-day usage data (placeholder until real data is available)
  const usageData = useMemo(() => {
    const base = skill.load_count || 0
    return Array.from({ length: 30 }, (_, i) => {
      // Decay from most recent
      const decay = Math.max(0, Math.round(base * (1 - i / 35)))
      return Math.min(decay + Math.round(Math.random() * 2), 15)
    })
  }, [skill.load_count])

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <button className={styles.modalCloseBtn} onClick={onClose}>&times;</button>

        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.modalHeaderTop}>
            <RankCircle rank={skill.rank} />
            <h2 className={styles.modalTitle}>{skill.name}</h2>
            {skill.version && <span className={styles.cardVersion}>v{skill.version}</span>}
            <span className={styles.cardCategory}>{skill.category}</span>
          </div>
          {skill.description && (
            <div className={styles.modalDetailRow}>
              <span>{skill.description}</span>
            </div>
          )}
          {skill.installed && (
            <div className={styles.modalDetailRow}>
              <span>Installiert: {skill.installed}</span>
              <span>Quelle: {skill.source}</span>
            </div>
          )}
        </div>

        {/* Body */}
        {detailLoading ? (
          <div className={styles.detailLoading}>Lade Detail...</div>
        ) : (
          <>
            <div className={styles.modalBody}>
              {/* Left column: metadata */}
              <div className={styles.modalLeft}>
                <div className={styles.metaSection}>
                  <h4 className={styles.metaSectionTitle}>Metadaten</h4>
                  <div className={styles.metaRow}>
                    <span className={styles.metaLabel}>Rang</span>
                    <span className={styles.metaValue}>
                      {RANK_CONFIG[skill.rank]?.label || skill.rank}
                    </span>
                  </div>
                  <div className={styles.metaRow}>
                    <span className={styles.metaLabel}>Version</span>
                    <span className={styles.metaValue}>{skill.version || '–'}</span>
                  </div>
                  <div className={styles.metaRow}>
                    <span className={styles.metaLabel}>Nutzung</span>
                    <span className={styles.metaValue}>{skill.load_count}x geladen</span>
                  </div>
                  <div className={styles.metaRow}>
                    <span className={styles.metaLabel}>Letzter Ladevorgang</span>
                    <span className={styles.metaValue}>{skill.last_load || '–'}</span>
                  </div>
                  <div className={styles.metaRow}>
                    <span className={styles.metaLabel}>Kategorie</span>
                    <span className={styles.metaValue}>{skill.category || '–'}</span>
                  </div>
                </div>

                {/* Usage chart */}
                <div className={styles.chartSection}>
                  <h4 className={styles.chartTitle}>Nutzung (letzte 30 Tage)</h4>
                  <MiniChart data={usageData} />
                </div>
              </div>

              {/* Right column: SKILL.md content */}
              <div className={styles.modalRight}>
                <h4 className={styles.metaSectionTitle}>SKILL.md</h4>
                {detail?.content ? (
                  <div
                    className={styles.markdownContent}
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(detail.content) }}
                  />
                ) : (
                  <div className={styles.noData}>Kein Inhalt</div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className={styles.modalFooter}>
              <div className={styles.footerLeft}>
                {/* References with traffic light */}
                <div className={styles.referencesSection}>
                  <span className={styles.metaLabel}>References</span>
                  <RefTrafficLight count={skill.references_count || 0} />
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {skill.references_count || 0} Dateien
                  </span>
                </div>

                {/* Bundle dropdown */}
                <select className={styles.bundleDropdown} value={skill.category} disabled>
                  <option value={skill.category}>
                    Bundle: {skill.category || 'keins'}
                  </option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button className={styles.actionBtn}>Bearbeiten</button>
                <button className={styles.actionBtn}>Review</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function SkillCard({ skill, onClick }) {
  const isArchived = skill.rank === 'archived' || skill.category === '.archive'
  return (
    <div
      className={`${styles.card} ${isArchived ? styles.cardArchived : ''}`}
      onClick={() => onClick(skill)}
    >
      <div className={styles.cardTop}>
        <RankCircle rank={skill.rank} />
        <span className={styles.cardName}>{skill.name}</span>
      </div>
      <div className={styles.cardMeta}>
        {skill.version && <span className={styles.cardVersion}>v{skill.version}</span>}
        <span className={styles.cardMetaItem}>
          {skill.load_count}x
        </span>
        {skill.last_load && (
          <span className={styles.cardMetaItem}>{skill.last_load}</span>
        )}
        <span className={styles.cardMetaItem}>
          📦{skill.bundle_count || 0}
        </span>
        <span className={styles.cardMetaItem}>
          📄{skill.references_count || 0}
        </span>
        <span className={styles.cardCategory}>{skill.category}</span>
      </div>
      {skill.description && (
        <p className={styles.cardDesc}>{skill.description}</p>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════
   Bundles-Tab Components
   ═══════════════════════════════════════════════════════════════ */

const RANK_COLORS = [
  '#6c8cff', '#34d399', '#fbbf24', '#f87171',
  '#a78bfa', '#fb923c', '#60a5fa', '#f472b6',
  '#22d3ee', '#a3e635', '#e879f9', '#facc15',
]

function rankColor(index) {
  return RANK_COLORS[index % RANK_COLORS.length]
}

function formatDate(s) {
  return s ? new Date(s).toLocaleDateString('de-DE') : '—'
}

function formatTokens(n) {
  if (!n) return '—'
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return `${n}`
}

function BundleCard({ bundle, overlap, onOverlapClick }) {
  const [expanded, setExpanded] = useState(false)
  const w = bundle.weight

  return (
    <div className={styles.bundleCard}>
      <div className={styles.bundleHeader}>
        <div>
          <div className={styles.bundleNameRow}>
            <strong className={styles.bundleSlug}>/{bundle.slug}</strong>
            {bundle.has_overlap && (
              <span className={styles.overlapBadge}>◈ Überschneidung</span>
            )}
          </div>
          {bundle.description && (
            <p className={styles.bundleDesc}>{bundle.description}</p>
          )}
        </div>
        <button className={styles.actionBtn} onClick={() => setExpanded(!expanded)}>
          {expanded ? '▲' : '▼'}
        </button>
      </div>

      {/* Weight bar */}
      <div className={styles.bundleWeight}>
        <span className={styles.weightTokens}>~{formatTokens(w?.total_estimated_tokens)} Tokens</span>
        <span className={styles.weightCount}>{w?.skill_count || bundle.skills.length} Skills</span>
        <span className={styles.weightOverlap}>{bundle.skills.filter(s => overlap[s]).length} Überschneidungen</span>
      </div>
      {w && (
        <div className={styles.weightBarBg}>
          <div
            className={styles.weightBarFill}
            style={{
              width: `${Math.min(100, (w.total_estimated_tokens / 5000) * 100)}%`,
              background: w.total_estimated_tokens > 3000
                ? 'var(--orange)' : w.total_estimated_tokens > 1500
                  ? 'var(--yellow)' : 'var(--green)',
            }}
          />
        </div>
      )}

      <div className={styles.bundleMeta}>
        <span>Erstellt: {formatDate(bundle.created)}</span>
        <span>Geändert: {formatDate(bundle.last_modified)}</span>
        <span>Datei: <code>{bundle.file_path?.split('/').slice(-2).join('/')}</code></span>
      </div>

      {/* Skill list */}
      <div className={styles.bundleSkills}>
        <span className={styles.skillListLabel}>Skills ({bundle.skills.length})</span>
        <div className={styles.skillTags}>
          {bundle.skills.map((slug, idx) => {
            const inOverlap = overlap[slug]
            return (
              <span
                key={slug}
                onClick={() => inOverlap && onOverlapClick(slug)}
                className={inOverlap ? styles.skillTagOverlap : styles.skillTag}
                title={inOverlap ? `${slug} ist auch in ${overlap[slug].join(', ')}` : slug}
              >
                <span className={styles.skillDot} style={{ background: rankColor(idx) }} />
                {slug}
                {inOverlap && <span className={styles.overlapMarker}>◈ in {overlap[slug].length} Bundles</span>}
              </span>
            )
          })}
        </div>
      </div>

      {/* Expanded: instruction & missing skills */}
      {expanded && (
        <div className={styles.bundleExpanded}>
          {bundle.instruction && (
            <div>
              <strong className={styles.expandedLabel}>Instruction:</strong>
              <pre className={styles.expandedPre}>{bundle.instruction}</pre>
            </div>
          )}
          {w?.missing_skills?.length > 0 && (
            <div>
              <strong className={styles.expandedMissingLabel}>⚠ Fehlende Skills:</strong>
              <p className={styles.expandedMissingText}>{w.missing_skills.join(', ')}</p>
            </div>
          )}
          {w && (
            <div className={styles.expandedTokenDetail}>
              Token-Detail: {formatTokens(w.total_estimated_tokens - w.overhead_tokens)} (Skills) + {formatTokens(w.overhead_tokens)} (Overhead) = {formatTokens(w.total_estimated_tokens)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function OverlapPopup({ skillSlug, overlapData, onClose }) {
  const bundles = overlapData[skillSlug]
  if (!bundles) return null

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()} style={{ minWidth: 320 }}>
        <button className={styles.modalCloseBtn} onClick={onClose}>&times;</button>
        <h2 style={{ marginBottom: '0.75rem' }}>◈ {skillSlug}</h2>
        <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          Dieser Skill ist in {bundles.length} Bundles enthalten:
        </p>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {bundles.map(b => (
            <li key={b} style={{
              padding: '0.4rem 0.6rem', marginBottom: '0.25rem',
              background: 'var(--surface2)', borderRadius: 6,
              fontSize: '0.85rem',
            }}>
              📦 {b}
            </li>
          ))}
        </ul>
        <div className={styles.modalFooter} style={{ justifyContent: 'flex-end' }}>
          <button className={styles.actionBtn} onClick={onClose}>Schließen</button>
        </div>
      </div>
    </div>
  )
}

function NewBundleModal({ skills, onClose, onCreated }) {
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [selected, setSelected] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const cats = {}
  skills.forEach(s => {
    if (!cats[s.category]) cats[s.category] = []
    cats[s.category].push(s)
  })

  const toggleSkill = (slug) => {
    setSelected(prev => ({ ...prev, [slug]: !prev[slug] }))
  }

  const selectAllInCat = (cat, checked) => {
    const updates = {}
    cats[cat].forEach(s => { updates[s.slug || s.id || s.name] = checked })
    setSelected(prev => ({ ...prev, ...updates }))
  }

  const handleCreate = async () => {
    if (!name.trim()) { setError('Bitte einen Namen eingeben'); return }
    const skillSlugs = Object.entries(selected).filter(([, v]) => v).map(([k]) => k)
    if (skillSlugs.length === 0) { setError('Mindestens einen Skill auswählen'); return }

    setSaving(true)
    setError(null)
    try {
      const res = await fetch('/api/bundles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), description: desc.trim(), skills: skillSlugs }),
      })
      if (!res.ok) throw new Error(await res.text())
      const result = await res.json()
      onCreated(result)
    } catch (e) {
      setError(e.message)
    }
    setSaving(false)
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()} style={{ minWidth: 500, maxWidth: '85vw', maxHeight: '85vh', overflow: 'auto' }}>
        <button className={styles.modalCloseBtn} onClick={onClose}>&times;</button>
        <h2 style={{ marginBottom: '1rem' }}>Neues Bundle erstellen</h2>

        {error && <div className={styles.error} style={{ marginBottom: '0.75rem', fontSize: '0.85rem' }}>{error}</div>}

        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>Bundle-Name *</label>
          <input value={name} onChange={e => setName(e.target.value)} placeholder="z.B. backend-dev" style={{ width: '100%' }} />
        </div>

        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>Beschreibung</label>
          <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Kurzbeschreibung des Bundles" style={{ width: '100%' }} />
        </div>

        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>
            Skills auswählen ({Object.values(selected).filter(Boolean).length} von {skills.length} ausgewählt)
          </label>
          <div style={{ maxHeight: 300, overflow: 'auto', border: '1px solid var(--border)', borderRadius: 8, padding: '0.5rem' }}>
            {Object.entries(cats).sort().map(([cat, catSkills]) => (
              <div key={cat} style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem', padding: '0.25rem 0' }}>
                  <strong style={{ fontSize: '0.8rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>{cat}</strong>
                  <div style={{ display: 'flex', gap: '0.35rem' }}>
                    <button className={styles.actionBtn} onClick={() => selectAllInCat(cat, true)} style={{ fontSize: '0.7rem' }}>Alle</button>
                    <button className={styles.actionBtn} onClick={() => selectAllInCat(cat, false)} style={{ fontSize: '0.7rem' }}>Keine</button>
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                  {catSkills.sort((a, b) => (a.slug || a.id || a.name || '').localeCompare(b.slug || b.id || b.name || '')).map(s => {
                    const key = s.slug || s.id || s.name
                    return (
                      <label
                        key={key}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '0.3rem',
                          padding: '0.2rem 0.5rem', borderRadius: 4, cursor: 'pointer',
                          background: selected[key] ? 'var(--primary)' : 'var(--surface2)',
                          color: selected[key] ? '#fff' : 'var(--text)',
                          fontSize: '0.78rem', transition: 'all 0.1s',
                          border: selected[key] ? '1px solid var(--primary)' : '1px solid var(--border)',
                        }}
                      >
                        <input type="checkbox" checked={!!selected[key]} onChange={() => toggleSkill(key)} style={{ display: 'none' }} />
                        {key}
                      </label>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.modalFooter} style={{ justifyContent: 'flex-end' }}>
          <button className={styles.actionBtn} onClick={onClose} disabled={saving}>Abbrechen</button>
          <button className={styles.actionBtn} onClick={handleCreate} disabled={saving} style={{ background: 'var(--primary)', color: '#fff' }}>
            {saving ? 'Erstelle...' : 'Bundle erstellen'}
          </button>
        </div>
      </div>
    </div>
  )
}

function BundlesTab({ skills }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showNewModal, setShowNewModal] = useState(false)
  const [overlapSkill, setOverlapSkill] = useState(null)

  const load = () => {
    setLoading(true)
    setError(null)
    Promise.all([
      fetch('/api/bundles').then(r => r.json()),
    ])
      .then(([bundleData]) => setData(bundleData))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleCreated = () => {
    setShowNewModal(false)
    load()
  }

  if (loading) return <div className={styles.loading}>Lade Bundles...</div>
  if (error) return <div className={styles.error}>{error}</div>

  const bundles = data?.bundles || []
  const overlap = data?.overlap || {}
  const totalSkills = data?.total_skills || skills.length

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            {bundles.length} Bundles · {totalSkills} Skills
          </span>
        </div>
        <button className={styles.actionBtn} onClick={() => setShowNewModal(true)}
          style={{ background: 'var(--primary)', color: '#fff' }}>
          + Neues Bundle
        </button>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
        <div className={styles.card} style={{ cursor: 'default' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)' }}>{bundles.length}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Bundles</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Definitionen</div>
        </div>
        <div className={styles.card} style={{ cursor: 'default' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)' }}>{totalSkills}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Skills</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Installiert</div>
        </div>
        <div className={styles.card} style={{ cursor: 'default' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)' }}>
            {formatTokens(bundles.reduce((sum, b) => sum + (b.weight?.total_estimated_tokens || 0), 0))}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Gesamt-Token</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Alle Bundles</div>
        </div>
        <div className={styles.card} style={{ cursor: 'default' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)' }}>{Object.keys(overlap).length}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Überschneidungen</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Skills in 2+ Bundles</div>
        </div>
      </div>

      {/* Bundle cards */}
      {bundles.length === 0 ? (
        <div className={styles.card} style={{ textAlign: 'center', padding: '3rem', cursor: 'default' }}>
          <p style={{ color: 'var(--text-dim)', marginBottom: '0.75rem' }}>Noch keine Bundles angelegt.</p>
          <button className={styles.actionBtn} onClick={() => setShowNewModal(true)}
            style={{ background: 'var(--primary)', color: '#fff' }}>
            + Erstes Bundle erstellen
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(520px, 1fr))', gap: '1rem' }}>
          {bundles.map(bundle => (
            <BundleCard
              key={bundle.slug}
              bundle={bundle}
              overlap={overlap}
              onOverlapClick={setOverlapSkill}
            />
          ))}
        </div>
      )}

      {overlapSkill && (
        <OverlapPopup
          skillSlug={overlapSkill}
          overlapData={overlap}
          onClose={() => setOverlapSkill(null)}
        />
      )}

      {showNewModal && (
        <NewBundleModal
          skills={skills}
          onClose={() => setShowNewModal(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  )
}

function ReferencesTab() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [skillFilter, setSkillFilter] = useState('all')
  const [sortBy, setSortBy] = useState('freshness')
  const [refreshing, setRefreshing] = useState({})

  const load = () => {
    setLoading(true)
    setError(null)
    fetch('/api/references')
      .then(r => r.json())
      .then(d => setData(d))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  // Unique skills list for filter
  const skillOptions = useMemo(() => {
    if (!data) return []
    const skills = new Set()
    data.references.forEach(r => skills.add(r.skill_name))
    return Array.from(skills).sort()
  }, [data])

  // Filtered + sorted references
  const filteredSorted = useMemo(() => {
    if (!data) return []
    let refs = data.references
    if (skillFilter !== 'all') {
      refs = refs.filter(r => r.skill_name === skillFilter)
    }
    const sorted = [...refs]
    switch (sortBy) {
      case 'freshness':
        sorted.sort((a, b) => {
          const order = { green: 0, yellow: 1, red: 2, gray: 3 }
          return (order[a.traffic_light] || 3) - (order[b.traffic_light] || 3)
        })
        break
      case 'skill':
        sorted.sort((a, b) => (a.skill_name || '').localeCompare(b.skill_name || ''))
        break
      case 'cron':
        sorted.sort((a, b) => {
          const aCron = a.has_cron ? 0 : 1
          const bCron = b.has_cron ? 0 : 1
          return aCron - bCron
        })
        break
      case 'name':
        sorted.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
        break
      case 'size':
        sorted.sort((a, b) => (b.size || 0) - (a.size || 0))
        break
    }
    return sorted
  }, [data, skillFilter, sortBy])

  const handleRefresh = async (ref) => {
    const refId = `${ref.skill_id}/${ref.name}`
    setRefreshing(prev => ({ ...prev, [refId]: true }))
    try {
      const res = await fetch(`/api/references/${encodeURIComponent(refId)}/refresh`, { method: 'POST' })
      const result = await res.json()
      if (!res.ok) {
        alert(`Fehler: ${result.error}`)
      } else {
        setTimeout(() => load(), 2000)
      }
    } catch (e) {
      alert(`Fehler: ${e.message}`)
    }
    setRefreshing(prev => ({ ...prev, [refId]: false }))
  }

  const trafficLightClass = (color) => {
    switch (color) {
      case 'green': return styles.refDotGreen
      case 'yellow': return styles.refDotYellow
      case 'red': return styles.refDotRed
      default: return styles.refDotGray
    }
  }

  if (loading) return <div className={styles.loading}>Lade References...</div>
  if (error) return <div className={styles.error}>Fehler: {error}</div>
  if (!data) return null

  const byLight = data.by_traffic_light || {}

  return (
    <div>
      {/* Stats overview */}
      <div className={styles.refStatCards}>
        <div className={styles.refStatCard}>
          <div className={styles.refStatValue}>{data.total}</div>
          <div className={styles.refStatLabel}>References</div>
          <div className={styles.refStatSub}>Gesamt</div>
        </div>
        <div className={styles.refStatCard}>
          <div className={styles.refStatValue} style={{ color: '#22c55e' }}>{byLight.green || 0}</div>
          <div className={styles.refStatLabel}>Grün</div>
          <div className={styles.refStatSub}>Heute aktualisiert</div>
        </div>
        <div className={styles.refStatCard}>
          <div className={styles.refStatValue} style={{ color: '#f59e0b' }}>{byLight.yellow || 0}</div>
          <div className={styles.refStatLabel}>Gelb</div>
          <div className={styles.refStatSub}>1–3 Tage alt</div>
        </div>
        <div className={styles.refStatCard}>
          <div className={styles.refStatValue} style={{ color: '#ef4444' }}>{byLight.red || 0}</div>
          <div className={styles.refStatLabel}>Rot</div>
          <div className={styles.refStatSub}>{'>'}3 Tage alt</div>
        </div>
        <div className={styles.refStatCard}>
          <div className={styles.refStatValue} style={{ color: data.orphaned_count > 0 ? '#f59e0b' : 'var(--text)' }}>{data.orphaned_count}</div>
          <div className={styles.refStatLabel}>Verwaist</div>
          <div className={styles.refStatSub}>Kein Cron zugeordnet</div>
        </div>
      </div>

      {/* Controls bar */}
      <div className={styles.refControls}>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className={styles.refControlLabel}>Skill:</span>
          <select
            className={styles.refSelect}
            value={skillFilter}
            onChange={e => setSkillFilter(e.target.value)}
          >
            <option value="all">Alle Skills ({data.total_skills_with_refs})</option>
            {skillOptions.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className={styles.refControlLabel}>Sortieren:</span>
          {['freshness', 'skill', 'cron', 'name', 'size'].map(opt => (
            <button
              key={opt}
              className={`${styles.refSortBtn} ${sortBy === opt ? styles.refSortBtnActive : ''}`}
              onClick={() => setSortBy(opt)}
            >
              {opt === 'freshness' ? 'Aktualität' :
               opt === 'skill' ? 'Skill' :
               opt === 'cron' ? 'Cron' :
               opt === 'name' ? 'Dateiname' : 'Größe'}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <div className={styles.refCount}>{filteredSorted.length} von {data.total} Einträgen</div>

      {/* References table */}
      <div className={styles.refTable}>
        <div className={styles.refTableHeader}>
          <span className={styles.refColAmpel}></span>
          <span className={styles.refColName}>Dateiname</span>
          <span className={styles.refColSkill}>Skill</span>
          <span className={styles.refColTime}>Letztes Update</span>
          <span className={styles.refColSize}>Größe</span>
          <span className={styles.refColCron}>Cron</span>
          <span className={styles.refColAction}></span>
        </div>
        {filteredSorted.length === 0 && (
          <div className={styles.refEmpty}>Keine Einträge gefunden</div>
        )}
        {filteredSorted.map((ref, idx) => (
          <div key={`${ref.skill_id}/${ref.name}`} className={`${styles.refRow} ${!ref.has_cron ? styles.refRowOrphaned : ''}`}>
            <span className={styles.refColAmpel}>
              <span className={`${styles.refDot} ${trafficLightClass(ref.traffic_light)}`} title={ref.traffic_light_label} />
            </span>
            <span className={styles.refColName}>
              <span className={styles.refFileName}>{ref.name}</span>
            </span>
            <span className={styles.refColSkill}>
              <span className={styles.refSkillBadge}>{ref.skill_name}</span>
            </span>
            <span className={styles.refColTime}>
              <span className={styles.refTime}>{ref.last_update}</span>
            </span>
            <span className={styles.refColSize}>
              <span className={styles.refSize}>{ref.size_formatted}</span>
            </span>
            <span className={styles.refColCron}>
              {ref.has_cron ? (
                <div className={styles.refCronInfo}>
                  <span className={styles.refCronName} title={`Job: ${ref.cron.name}`}>{ref.cron.name}</span>
                  <span className={styles.refCronSchedule}>{ref.cron.schedule}</span>
                </div>
              ) : (
                <span className={styles.refOrphanedTag}>⛔ Verwaist</span>
              )}
            </span>
            <span className={styles.refColAction}>
              <button
                className={styles.refRefreshBtn}
                disabled={!ref.has_cron || refreshing[`${ref.skill_id}/${ref.name}`]}
                onClick={() => handleRefresh(ref)}
                title={ref.has_cron ? 'Jetzt aktualisieren' : 'Kein Cron zugeordnet'}
              >
                {refreshing[`${ref.skill_id}/${ref.name}`] ? '…' : '🔄'}
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function SkillCockpitPage() {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('alpha')
  const [activeTab, setActiveTab] = useState('skills')
  const [selectedSkill, setSelectedSkill] = useState(null)

  const fetchSkills = useCallback(() => {
    setLoading(true)
    fetch('/api/skills')
      .then(r => r.json())
      .then(data => {
        setSkills(data.skills || [])
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  useEffect(() => { fetchSkills() }, [fetchSkills])

  // Filter by search
  const filtered = useMemo(() => {
    if (!search.trim()) return skills
    const q = search.toLowerCase()
    return skills.filter(s =>
      (s.name || '').toLowerCase().includes(q) ||
      (s.description || '').toLowerCase().includes(q) ||
      (s.category || '').toLowerCase().includes(q)
    )
  }, [skills, search])

  // Split into active and archived
  const { active, archived } = useMemo(() => {
    const a = [], ar = []
    for (const s of filtered) {
      if (s.rank === 'archived' || s.category === '.archive') {
        ar.push(s)
      } else {
        a.push(s)
      }
    }
    return { active: a, archived: ar }
  }, [filtered])

  // Sort active skills
  const sortedActive = useMemo(() => {
    const s = [...active]
    switch (sortBy) {
      case 'rank': {
        const rankOrder = { gold: 0, silver: 1, bronze: 2 }
        s.sort((a, b) => (rankOrder[a.rank] || 3) - (rankOrder[b.rank] || 3))
        break
      }
      case 'usage':
        s.sort((a, b) => (b.load_count || 0) - (a.load_count || 0))
        break
      case 'age':
        s.sort((a, b) => (b.last_load || '').localeCompare(a.last_load || ''))
        break
      case 'alpha':
      default:
        s.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
        break
    }
    return s
  }, [active, sortBy])

  if (loading) return <div className={styles.loading}>Lade Skills...</div>
  if (error) return <div className={styles.error}>Fehler: {error}</div>

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.headerBar}>
        <div>
          <h1 className={styles.headerTitle}>Skill-Cockpit</h1>
          <span className={styles.headerCount}>
            {active.length} aktiv · {archived.length} archiviert
          </span>
        </div>
        <div className={styles.controls}>
          <input
            className={styles.searchInput}
            type="text"
            placeholder="Skills durchsuchen..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <select
            className={styles.sortSelect}
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
          >
            {SORT_OPTIONS.map(opt => (
              <option key={opt.id} value={opt.id}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        {TABS.map(t => (
          <button
            key={t.id}
            className={`${styles.tab} ${activeTab === t.id ? styles.tabActive : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Skills Tab */}
      {activeTab === 'skills' && (
        <>
          {/* Active skills grid */}
          <div className={styles.grid}>
            {sortedActive.map(skill => (
              <SkillCard
                key={skill.id}
                skill={skill}
                onClick={setSelectedSkill}
              />
            ))}
          </div>

          {/* Archive section */}
          {archived.length > 0 && (
            <div className={styles.archiveSection}>
              <h3 className={styles.archiveTitle}>
                Archiv ({archived.length})
              </h3>
              <div className={styles.grid}>
                {archived.map(skill => (
                  <SkillCard
                    key={skill.id}
                    skill={skill}
                    onClick={setSelectedSkill}
                  />
                ))}
              </div>
            </div>
          )}

          {sortedActive.length === 0 && archived.length === 0 && (
            <div className={styles.noData} style={{ textAlign: 'center', padding: '24px' }}>
              Keine Skills gefunden
            </div>
          )}
        </>
      )}

      {/* Bundles Tab */}
      {activeTab === 'bundles' && (
        <BundlesTab skills={skills} />
      )}

      {/* References Tab */}
      {activeTab === 'references' && (
        <ReferencesTab />
      )}

      {/* Detail Modal */}
      {selectedSkill && (
        <SkillModal
          skill={selectedSkill}
          onClose={() => setSelectedSkill(null)}
        />
      )}
    </div>
  )
}