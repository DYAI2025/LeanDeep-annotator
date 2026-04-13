import type { DetectedMarker } from '../api/types'
import './MarkerTooltip.css'

interface Props {
  marker: DetectedMarker
  position: { x: number; y: number }
  onClickMarkerId?: (id: string) => void
}

const LAYER_LABELS: Record<string, string> = {
  ATO: 'Atomic Signal',
  SEM: 'Semantic Blend',
  CLU: 'Cluster Intuition',
  MEMA: 'Meta-Diagnosis',
}

export function MarkerTooltip({ marker, position, onClickMarkerId }: Props) {
  return (
    <div
      className="marker-tooltip"
      role="tooltip"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className="tooltip-header">
        <button
          className="tooltip-marker-id"
          onClick={() => onClickMarkerId?.(marker.id)}
          title="View in marker library"
        >
          {marker.id}
        </button>
        <span className={`tooltip-tier tooltip-tier--${marker.tier.toLowerCase()}`}>
          {marker.tier}
        </span>
      </div>
      <div className="tooltip-type">
        {LAYER_LABELS[marker.layer] ?? marker.layer}
      </div>
      <div className="tooltip-meaning">
        {marker.meaning_in_context}
      </div>
      <div className="tooltip-confidence">
        Confidence: {Math.round(marker.adjusted_confidence * 100)}%
        {marker.resonance_score > 0 && (
          <span className="tooltip-resonance">
            {' '}(resonance: {Math.round(marker.resonance_score * 100)}%)
          </span>
        )}
      </div>
    </div>
  )
}
