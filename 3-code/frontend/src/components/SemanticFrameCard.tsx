import type { SemanticFrame } from '../api/types'
import './SemanticFrameCard.css'

interface Props {
  frame: SemanticFrame
}

function formatTenor(value: number): string {
  if (value <= -0.5) return 'very negative'
  if (value <= -0.1) return 'negative'
  if (value <= 0.1) return 'neutral'
  if (value <= 0.5) return 'positive'
  return 'very positive'
}

export function SemanticFrameCard({ frame }: Props) {
  return (
    <div className="frame-card" role="region" aria-label="Semantic Frame">
      <h3 className="frame-title">Semantic Frame</h3>
      <div className="frame-grid">
        <div className="frame-item">
          <span className="frame-label">Tone</span>
          <span className="frame-value">{frame.tone}</span>
        </div>
        <div className="frame-item">
          <span className="frame-label">Themes</span>
          <span className="frame-value">{frame.themes.join(', ')}</span>
        </div>
        <div className="frame-item">
          <span className="frame-label">Dynamics</span>
          <span className="frame-value">{frame.relational_dynamics}</span>
        </div>
        <div className="frame-item">
          <span className="frame-label">Intent</span>
          <span className="frame-value">{frame.intent}</span>
        </div>
        <div className="frame-item">
          <span className="frame-label">Emotional Tenor</span>
          <div className="frame-bar-container">
            <div
              className="frame-bar"
              style={{
                width: `${((frame.emotional_tenor + 1) / 2) * 100}%`,
                backgroundColor: frame.emotional_tenor < 0 ? 'var(--color-error)' : 'var(--color-success)',
              }}
            />
            <span className="frame-bar-label">{formatTenor(frame.emotional_tenor)}</span>
          </div>
        </div>
        <div className="frame-item">
          <span className="frame-label">Context Validity</span>
          <div className="frame-bar-container">
            <div
              className="frame-bar"
              style={{
                width: `${frame.context_validity * 100}%`,
                backgroundColor: 'var(--color-accent)',
              }}
            />
            <span className="frame-bar-label">{Math.round(frame.context_validity * 100)}%</span>
          </div>
        </div>
        <div className="frame-item">
          <span className="frame-label">Offline Context Risk</span>
          <div className="frame-bar-container">
            <div
              className="frame-bar"
              style={{
                width: `${frame.offline_context_risk * 100}%`,
                backgroundColor: frame.offline_context_risk >= 0.6 ? 'var(--color-warning)' : 'var(--color-accent)',
              }}
            />
            <span className="frame-bar-label">{Math.round(frame.offline_context_risk * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}
