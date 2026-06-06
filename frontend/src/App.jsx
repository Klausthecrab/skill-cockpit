import SkillCockpitPage from './Page'

const theme = {
  '--bg-primary': '#0f0f13',
  '--bg-secondary': '#16161e',
  '--bg-tertiary': '#1e1e2a',
  '--surface-primary': '#1a1a24',
  '--surface-secondary': '#22222e',
  '--border-primary': '#2a2a3a',
  '--text-primary': '#e8e8f0',
  '--text-secondary': '#b0b0c0',
  '--text-muted': '#787890',
  '--text-dim': '#585870',
  '--color-accent': '#6c8cff',
  '--color-accent-hover': '#8aa4ff',
  '--primary': '#6c8cff',
  '--orange': '#f59e0b',
  '--yellow': '#eab308',
  '--green': '#22c55e',
  '--red': '#ef4444',
  '--radius-sm': '4px',
  '--radius-md': '8px',
  '--radius-lg': '12px',
  '--spacing-xs': '4px',
  '--spacing-sm': '8px',
  '--spacing-md': '12px',
  '--spacing-lg': '20px',
  '--spacing-xl': '32px',
  '--font-size-xs': '0.75rem',
  '--font-size-sm': '0.85rem',
  '--font-size-md': '1rem',
}

function applyTheme() {
  const root = document.documentElement
  Object.entries(theme).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
  // Global body styles
  document.body.style.margin = '0'
  document.body.style.padding = '0'
  document.body.style.background = 'var(--bg-primary)'
  document.body.style.color = 'var(--text-primary)'
  document.body.style.fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
  document.body.style.fontSize = '14px'
  document.body.style.lineHeight = '1.5'
}

applyTheme()

export default function App() {
  return <SkillCockpitPage />
}