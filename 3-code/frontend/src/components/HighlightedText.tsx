import { useCallback, useEffect, useRef, useState } from 'react'
import type { DetectedMarker, Message } from '../api/types'
import { MarkerTooltip } from './MarkerTooltip'
import './HighlightedText.css'

interface Props {
  messages: Message[]
  markers: DetectedMarker[]
  activeMarkerIds?: Set<string>
  onMarkerClick?: (marker: DetectedMarker) => void
  onMarkerIdClick?: (id: string) => void
}

const LAYER_COLORS: Record<string, string> = {
  ATO: 'var(--color-ato)',
  SEM: 'var(--color-sem)',
  CLU: 'var(--color-clu)',
  MEMA: 'var(--color-mema)',
}

interface MarkerSpan {
  start: number
  end: number
  marker: DetectedMarker
}

function buildSpans(markers: DetectedMarker[]): MarkerSpan[] {
  const spans: MarkerSpan[] = []
  for (const marker of markers) {
    if (marker.tier === 'DISCARDED') continue
    for (const match of marker.matches) {
      spans.push({ start: match.span[0], end: match.span[1], marker })
    }
  }
  spans.sort((a, b) => a.start - b.start || b.end - a.end)
  return spans
}

function renderSegments(
  text: string,
  spans: MarkerSpan[],
  activeMarkerIds: Set<string>,
  onMouseEnter: (marker: DetectedMarker, rect: DOMRect) => void,
  onMouseLeave: () => void,
  onMarkerClick?: (marker: DetectedMarker) => void,
  markerRefs?: React.MutableRefObject<HTMLElement[]>,
) {
  const segments: React.ReactNode[] = []
  let pos = 0

  for (const span of spans) {
    if (span.start < pos) continue
    if (span.start > pos) {
      segments.push(<span key={`t-${pos}`}>{text.slice(pos, span.start)}</span>)
    }

    const color = LAYER_COLORS[span.marker.layer] ?? 'var(--color-accent)'
    const opacity = 0.15 + span.marker.adjusted_confidence * 0.45
    const isActive = activeMarkerIds.has(span.marker.id)

    segments.push(
      <mark
        key={`m-${span.start}-${span.marker.id}`}
        className={`marker-highlight ${isActive ? 'marker-highlight--active' : ''}`}
        style={{
          backgroundColor: color,
          opacity: isActive ? 1 : undefined,
          '--marker-opacity': opacity,
        } as React.CSSProperties}
        tabIndex={0}
        role="button"
        aria-label={`Marker: ${span.marker.id}, ${span.marker.meaning_in_context}`}
        ref={(el) => { if (el && markerRefs) markerRefs.current.push(el) }}
        onMouseEnter={(e) => onMouseEnter(span.marker, e.currentTarget.getBoundingClientRect())}
        onMouseLeave={onMouseLeave}
        onFocus={(e) => onMouseEnter(span.marker, e.currentTarget.getBoundingClientRect())}
        onBlur={onMouseLeave}
        onClick={() => onMarkerClick?.(span.marker)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onMarkerClick?.(span.marker)
          }
        }}
      >
        {text.slice(span.start, span.end)}
      </mark>,
    )
    pos = span.end
  }

  if (pos < text.length) {
    segments.push(<span key={`t-${pos}`}>{text.slice(pos)}</span>)
  }

  return segments
}

export function HighlightedText({
  messages,
  markers,
  activeMarkerIds = new Set(),
  onMarkerClick,
  onMarkerIdClick,
}: Props) {
  const [tooltip, setTooltip] = useState<{
    marker: DetectedMarker
    position: { x: number; y: number }
  } | null>(null)
  const hoverTimerRef = useRef<number | null>(null)
  const markerRefs = useRef<HTMLElement[]>([])

  useEffect(() => {
    markerRefs.current = []
  }, [messages, markers])

  const handleMouseEnter = useCallback((marker: DetectedMarker, rect: DOMRect) => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
    hoverTimerRef.current = window.setTimeout(() => {
      setTooltip({
        marker,
        position: {
          x: Math.min(rect.left, window.innerWidth - 340),
          y: rect.bottom + 8 > window.innerHeight - 150
            ? rect.top - 8
            : rect.bottom + 8,
        },
      })
    }, 100)
  }, [])

  const handleMouseLeave = useCallback(() => {
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current)
      hoverTimerRef.current = null
    }
    setTooltip(null)
  }, [])

  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
    }
  }, [])

  return (
    <div className="highlighted-text" role="region" aria-label="Analyzed text with markers">
      {messages.map((message, idx) => {
        const offsetBefore = messages.slice(0, idx).reduce((sum, m) => sum + m.text.length + 1, 0)
        const msgMarkers = markers.filter((m) =>
          m.message_indices.includes(idx) ||
          m.matches.some((match) =>
            match.span[0] >= offsetBefore && match.span[1] <= offsetBefore + message.text.length,
          ),
        )
        const msgSpans = buildSpans(msgMarkers.map((m) => ({
          ...m,
          matches: m.matches.map((match) => ({
            ...match,
            span: [match.span[0] - offsetBefore, match.span[1] - offsetBefore] as [number, number],
          })).filter((match) => match.span[0] >= 0 && match.span[1] <= message.text.length),
        })))

        return (
          <div key={idx} className="message-block">
            <span className="message-role">{message.role}:</span>
            <span className="message-text">
              {renderSegments(
                message.text,
                msgSpans,
                activeMarkerIds,
                handleMouseEnter,
                handleMouseLeave,
                onMarkerClick,
                markerRefs,
              )}
            </span>
          </div>
        )
      })}

      {tooltip && (
        <MarkerTooltip
          marker={tooltip.marker}
          position={tooltip.position}
          onClickMarkerId={onMarkerIdClick}
        />
      )}
    </div>
  )
}
