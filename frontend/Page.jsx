import { useState, useEffect, useCallback } from 'react'
import styles from './Page.module.css'

const SOURCE_LABELS = {
  own: 'Eigene Skills',
  installed: 'Installiert',
  anthropic: 'Anthropic',
  n8n: 'n8n-Workflows',
}

const SOURCE_ORDER = ['own', 'installed', 'anthropic', 'n8n']

function SourceBadge({ source }) {
  return <span className={`${styles.badge} ${styles[`badge_${source}`] || ''}`}>{SOURCE_LABELS[source] || source}</span>
}

function RatingStars({ value, max = 5, onChange }) {
  return (
    <span className={styles.stars}>
      {Array.from({ length: max }, (_, i) => (
        <span
          key={i}
          className={`${styles.star} ${i < value ? styles.starActive : ''}`}
          onClick={() => onChange?.(i + 1)}
          style={{ cursor: onChange ? 'pointer' : 'default' }}
        >
          {i < value ? '\u2605' : '\u2606'}
        </span>
      ))}
    </span>
  )
}

export default function SkillsPage() {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [ratings, setRatings] = useState({})

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

  const openDetail = useCallback((id) => {
    setSelectedId(id)
    setDetailLoading(true)
    setDetail(null)
    Promise.all([
      fetch(`/api/skills/${id}/detail`).then(r => r.json()),
      fetch(`/api/skills/${id}/ratings`).then(r => r.json()).catch(() => ({})),
    ]).then(([d, r]) => {
      setDetail(d)
      setRatings(r)
      setDetailLoading(false)
    }).catch(e => { setError(e.message); setDetailLoading(false) })
  }, [])

  const updateRating = useCallback((key, value) => {
    const updated = { ...ratings, [key]: value }
    setRatings(updated)
    fetch(`/api/skills/${selectedId}/ratings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated),
    }).catch(() => {})
  }, [ratings, selectedId])

  if (loading) return <div className={styles.loading}>Lade Skills...</div>
  if (error) return <div className={styles.error}>Fehler: {error}</div>

  // Detail view
  if (selectedId) {
    return (
      <div className={styles.page}>
        <button className={styles.backBtn} onClick={() => { setSelectedId(null); setDetail(null) }}>
          &larr; Zurueck
        </button>
        {detailLoading ? (
          <div className={styles.loading}>Lade Detail...</div>
        ) : detail ? (
          <div className={styles.detailView}>
            <h1 className={styles.detailTitle}>{detail.name || detail.display_name || selectedId}</h1>
            {detail.source && <SourceBadge source={detail.source} />}
            {detail.description && <p className={styles.detailDesc}>{detail.description}</p>}

            <div className={styles.ratingsSection}>
              <h3 className={styles.sectionTitle}>Bewertung</h3>
              <div className={styles.ratingRow}>
                <span className={styles.ratingLabel}>Verstehe:</span>
                <RatingStars value={ratings.verstehe || 0} onChange={v => updateRating('verstehe', v)} />
              </div>
              <div className={styles.ratingRow}>
                <span className={styles.ratingLabel}>Nutze:</span>
                <RatingStars value={ratings.nutze || 0} onChange={v => updateRating('nutze', v)} />
              </div>
            </div>

            {detail.secrets && detail.secrets.length > 0 && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Secrets</h3>
                <ul className={styles.secretsList}>
                  {detail.secrets.map((s, i) => <li key={i}><code>{s}</code></li>)}
                </ul>
              </div>
            )}

            {detail.content && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>SKILL.md</h3>
                <pre className={styles.codeBlock}>{detail.content.slice(0, 2000)}{detail.content.length > 2000 ? '\n...(gekuerzt)' : ''}</pre>
              </div>
            )}

            {detail.dataflow && detail.dataflow.length > 0 && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Dataflow</h3>
                <div className={styles.dataflow}>
                  {detail.dataflow.map((node, i) => (
                    <div key={i} className={styles.dataflowNode}>
                      <span className={styles.dataflowType}>{node.type}</span>
                      <span>{node.label || node.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className={styles.error}>Detail konnte nicht geladen werden.</div>
        )}
      </div>
    )
  }

  // List view grouped by source
  const grouped = {}
  skills.forEach(s => {
    const src = s.source || 'own'
    if (!grouped[src]) grouped[src] = []
    grouped[src].push(s)
  })

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Skills</h1>
        <span className={styles.count}>{skills.length} Skills</span>
      </div>

      {SOURCE_ORDER.map(src => {
        const items = grouped[src]
        if (!items || items.length === 0) return null
        return (
          <div key={src} className={styles.group}>
            <h2 className={styles.groupTitle}>{SOURCE_LABELS[src]} ({items.length})</h2>
            <div className={styles.grid}>
              {items.map(skill => (
                <div key={skill.id} className={styles.card} onClick={() => openDetail(skill.id)}>
                  <div className={styles.cardHeader}>
                    <span className={styles.cardName}>{skill.display_name || skill.name || skill.id}</span>
                    <SourceBadge source={src} />
                  </div>
                  <p className={styles.cardDesc}>{skill.description || '–'}</p>
                </div>
              ))}
            </div>
          </div>
        )
      })}

      {/* Ungrouped */}
      {Object.keys(grouped).filter(k => !SOURCE_ORDER.includes(k)).map(src => {
        const items = grouped[src]
        return (
          <div key={src} className={styles.group}>
            <h2 className={styles.groupTitle}>{src} ({items.length})</h2>
            <div className={styles.grid}>
              {items.map(skill => (
                <div key={skill.id} className={styles.card} onClick={() => openDetail(skill.id)}>
                  <span className={styles.cardName}>{skill.display_name || skill.id}</span>
                  <p className={styles.cardDesc}>{skill.description || '–'}</p>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
