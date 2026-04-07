import { useCallback, useMemo, useState } from 'react'
import type { ConversationResponse, DetectedMarker, Message } from '../api/types'
import { api, ApiRequestError } from '../api/client'
import { DialogueInput } from './DialogueInput'
import { SemanticFrameCard } from './SemanticFrameCard'
import { HighlightedText } from './HighlightedText'
import { NarrativePanel } from './NarrativePanel'
import { ExportMenu } from './ExportMenu'
import './AnalysisPage.css'

type AnalysisState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string; code?: string }
  | { status: 'done'; data: ConversationResponse; messages: Message[] }

export function AnalysisPage() {
  const [state, setState] = useState<AnalysisState>({ status: 'idle' })
  const [activeNarrativeId, setActiveNarrativeId] = useState<number | null>(null)
  const [activeMarkerId, setActiveMarkerId] = useState<string | null>(null)

  const handleSubmit = useCallback(async (messages: Message[]) => {
    setState({ status: 'loading' })
    setActiveNarrativeId(null)
    setActiveMarkerId(null)

    try {
      const data = await api.analyzeConversation({ messages })
      setState({ status: 'done', data, messages })
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setState({ status: 'error', message: err.message, code: err.code })
      } else {
        setState({ status: 'error', message: 'An unexpected error occurred.' })
      }
    }
  }, [])

  const handleSelectNarrative = useCallback((id: number | null) => {
    setActiveNarrativeId(id)
    setActiveMarkerId(null)
  }, [])

  const handleMarkerClick = useCallback((marker: DetectedMarker) => {
    setActiveMarkerId((prev) => prev === marker.id ? null : marker.id)
    setActiveNarrativeId(null)
  }, [])

  // Build the set of active marker IDs from narrative or direct selection
  const activeMarkerIds = useMemo(() => {
    const ids = new Set<string>()
    if (state.status === 'done' && activeNarrativeId !== null) {
      const narrative = state.data.narratives.find((n) => n.narrative_id === activeNarrativeId)
      if (narrative) {
        for (const sm of narrative.supporting_markers) {
          ids.add(sm.id)
        }
      }
    }
    if (activeMarkerId) {
      ids.add(activeMarkerId)
    }
    return ids
  }, [state, activeNarrativeId, activeMarkerId])

  return (
    <div className="analysis-page">
      <DialogueInput
        onSubmit={handleSubmit}
        isLoading={state.status === 'loading'}
      />

      {state.status === 'loading' && (
        <div className="analysis-loading" role="status" aria-live="polite">
          <div className="loading-spinner" />
          <span>Analyzing dialogue...</span>
        </div>
      )}

      {state.status === 'error' && (
        <div className="analysis-error" role="alert">
          <strong>Analysis failed</strong>
          {state.code && <span className="error-code">{state.code}</span>}
          <p>{state.message}</p>
          <button className="btn btn--secondary" onClick={() => setState({ status: 'idle' })}>
            Dismiss
          </button>
        </div>
      )}

      {state.status === 'done' && (
        <div className="analysis-results">
          <div className="results-header">
            <h2 className="results-title">Analysis Results</h2>
            <div className="results-meta">
              <span>{state.data.meta.markers_detected} markers</span>
              <span>{state.data.meta.processing_ms.toFixed(0)}ms</span>
              {state.data.degraded && (
                <span className="degraded-badge" title={state.data.fallback_reason ?? undefined}>
                  Degraded
                </span>
              )}
              <ExportMenu data={state.data} messages={state.messages} />
            </div>
          </div>

          {state.data.frame && (
            <SemanticFrameCard frame={state.data.frame} />
          )}

          <HighlightedText
            messages={state.messages}
            markers={state.data.markers}
            activeMarkerIds={activeMarkerIds}
            onMarkerClick={handleMarkerClick}
          />

          <NarrativePanel
            narratives={state.data.narratives.map((n) => ({
              ...n,
              supporting_markers: n.supporting_markers.map((sm) => ({
                ...sm,
                span: sm.span ?? ([0, 0] as [number, number]),
              })),
            }))}
            weakClusters={state.data.weak_clusters.map((wc) => ({
              markers: state.data.markers.filter(
                (m) => wc.marker_ids.includes(m.id),
              ),
              coherence: wc.coherence,
              cluster_meaning: wc.cluster_label,
              confidence: wc.avg_confidence,
            }))}
            offlineContextRisk={state.data.frame?.offline_context_risk ?? 0}
            activeNarrativeId={activeNarrativeId}
            onSelectNarrative={handleSelectNarrative}
          />
        </div>
      )}
    </div>
  )
}
