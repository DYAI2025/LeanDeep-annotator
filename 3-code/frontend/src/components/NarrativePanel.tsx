import { useState } from 'react'
import type { Narrative, WeakMarkerCluster } from '../api/types'
import './NarrativePanel.css'

interface Props {
  narratives: Narrative[]
  weakClusters: WeakMarkerCluster[]
  offlineContextRisk: number
  activeNarrativeId: number | null
  onSelectNarrative: (narrativeId: number | null) => void
}

const TYPE_LABELS: Record<string, string> = {
  Primary: 'Primary Reading',
  Contrarian: 'Contrarian Reading',
  Novel: 'Novel Pattern',
  'High-Uncertainty': 'High-Uncertainty Variant',
  'Weak Cluster': 'Weak Cluster Perspective',
}

export function NarrativePanel({
  narratives,
  weakClusters,
  offlineContextRisk,
  activeNarrativeId,
  onSelectNarrative,
}: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const handleSelect = (id: number) => {
    if (activeNarrativeId === id) {
      onSelectNarrative(null)
    } else {
      onSelectNarrative(id)
    }
  }

  const handleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="narrative-panel" role="region" aria-label="Narrative Interpretations">
      <div className="narrative-header">
        <h3 className="narrative-title">
          Interpretations
          <span className="narrative-count">{narratives.length}</span>
        </h3>
        {offlineContextRisk >= 0.6 && (
          <span className="uncertainty-badge" role="status">
            High Uncertainty
          </span>
        )}
      </div>

      <div className="narrative-list">
        {narratives.map((narrative) => (
          <NarrativeCard
            key={narrative.narrative_id}
            narrative={narrative}
            isActive={activeNarrativeId === narrative.narrative_id}
            isExpanded={expandedId === narrative.narrative_id}
            onSelect={() => handleSelect(narrative.narrative_id)}
            onExpand={() => handleExpand(narrative.narrative_id)}
          />
        ))}

        {weakClusters.map((cluster, idx) => (
          <WeakClusterCard key={`cluster-${idx}`} cluster={cluster} index={idx} />
        ))}
      </div>
    </div>
  )
}

interface NarrativeCardProps {
  narrative: Narrative
  isActive: boolean
  isExpanded: boolean
  onSelect: () => void
  onExpand: () => void
}

function NarrativeCard({ narrative, isActive, isExpanded, onSelect, onExpand }: NarrativeCardProps) {
  const typeLabel = TYPE_LABELS[narrative.type] ?? narrative.type
  const isWeakCluster = narrative.type === 'Weak Cluster'
  const isHighUncertainty = narrative.type === 'High-Uncertainty'

  return (
    <div
      className={[
        'narrative-card',
        isActive ? 'narrative-card--active' : '',
        isWeakCluster ? 'narrative-card--cluster' : '',
        isHighUncertainty ? 'narrative-card--uncertainty' : '',
      ].join(' ')}
      role="button"
      tabIndex={0}
      aria-pressed={isActive}
      aria-label={`${typeLabel}: click to ${isActive ? 'deselect' : 'highlight supporting markers'}`}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect()
        }
      }}
    >
      <div className="narrative-card-header">
        <span className="narrative-type-badge">{typeLabel}</span>
        <span className="narrative-confidence">
          {Math.round(narrative.confidence * 100)}%
        </span>
      </div>

      <p className="narrative-text">
        {isExpanded ? narrative.text : truncate(narrative.text, 150)}
      </p>

      {narrative.text.length > 150 && (
        <button
          className="narrative-expand"
          onClick={(e) => { e.stopPropagation(); onExpand() }}
          aria-label={isExpanded ? 'Collapse narrative' : 'Expand narrative'}
        >
          {isExpanded ? 'Show less' : 'Show more'}
        </button>
      )}

      {narrative.uncertainty_warning && (
        <div className="narrative-warning" role="alert">
          {narrative.uncertainty_warning}
        </div>
      )}

      <div className="narrative-markers">
        <span className="narrative-markers-label">Supporting markers:</span>
        {narrative.supporting_markers.map((sm) => (
          <span key={sm.id} className="narrative-marker-tag">
            {sm.id}
          </span>
        ))}
      </div>

      <div className="narrative-score-bar">
        <div
          className="narrative-score-fill"
          style={{ width: `${narrative.score * 100}%` }}
        />
      </div>
    </div>
  )
}

interface WeakClusterCardProps {
  cluster: WeakMarkerCluster
  index: number
}

function WeakClusterCard({ cluster, index }: WeakClusterCardProps) {
  return (
    <div className="narrative-card narrative-card--cluster">
      <div className="narrative-card-header">
        <span className="narrative-type-badge">Weak Cluster #{index + 1}</span>
        <span className="narrative-confidence">
          coherence: {Math.round(cluster.coherence * 100)}%
        </span>
      </div>
      <p className="narrative-text">{cluster.cluster_meaning}</p>
      <div className="narrative-markers">
        <span className="narrative-markers-label">Clustered markers:</span>
        {cluster.markers.map((m) => (
          <span key={m.id} className="narrative-marker-tag">
            {m.id}
          </span>
        ))}
      </div>
    </div>
  )
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trimEnd() + '...'
}
