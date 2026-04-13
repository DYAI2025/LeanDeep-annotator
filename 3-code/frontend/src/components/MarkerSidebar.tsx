import { useMemo, useState } from 'react'
import type { DetectedMarker } from '../api/types'
import './MarkerSidebar.css'

interface Props {
  markers: DetectedMarker[]
  activeMarkerId: string | null
  onSelectMarker: (markerId: string | null) => void
}

type LayerFilter = 'ALL' | 'ATO' | 'SEM' | 'CLU' | 'MEMA'
type TierFilter = 'ALL' | 'STRONG' | 'WEAK'
type SortMode = 'layer' | 'confidence' | 'family'

const LAYER_ORDER: Record<string, number> = { MEMA: 0, CLU: 1, SEM: 2, ATO: 3 }

export function MarkerSidebar({ markers, activeMarkerId, onSelectMarker }: Props) {
  const [search, setSearch] = useState('')
  const [layerFilter, setLayerFilter] = useState<LayerFilter>('ALL')
  const [tierFilter, setTierFilter] = useState<TierFilter>('ALL')
  const [familyFilter, setFamilyFilter] = useState<string>('ALL')
  const [sortMode, setSortMode] = useState<SortMode>('layer')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const families = useMemo(() => {
    const set = new Set<string>()
    for (const m of markers) {
      if (m.family) set.add(m.family)
    }
    const sorted = Array.from(set).sort()
    if (familyFilter !== 'ALL' && !set.has(familyFilter)) {
      setFamilyFilter('ALL')
    }
    return sorted
  }, [markers, familyFilter])

  const filtered = useMemo(() => {
    let result = markers.filter((m) => m.tier !== 'DISCARDED')

    if (search) {
      const q = search.toLowerCase()
      result = result.filter(
        (m) =>
          m.id.toLowerCase().includes(q) ||
          m.description.toLowerCase().includes(q) ||
          m.meaning_in_context.toLowerCase().includes(q),
      )
    }

    if (layerFilter !== 'ALL') {
      result = result.filter((m) => m.layer === layerFilter)
    }

    if (tierFilter !== 'ALL') {
      result = result.filter((m) => m.tier === tierFilter)
    }

    if (familyFilter !== 'ALL') {
      result = result.filter((m) => m.family === familyFilter)
    }

    const sorted = [...result]
    if (sortMode === 'layer') {
      sorted.sort((a, b) => (LAYER_ORDER[a.layer] ?? 9) - (LAYER_ORDER[b.layer] ?? 9))
    } else if (sortMode === 'confidence') {
      sorted.sort((a, b) => b.adjusted_confidence - a.adjusted_confidence)
    } else if (sortMode === 'family') {
      sorted.sort((a, b) => (a.family ?? '').localeCompare(b.family ?? ''))
    }

    return sorted
  }, [markers, search, layerFilter, tierFilter, familyFilter, sortMode])

  const handleToggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="marker-sidebar" role="region" aria-label="Marker Library">
      <div className="sidebar-search">
        <input
          type="search"
          className="sidebar-search-input"
          placeholder="Search markers..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search markers by ID or description"
        />
      </div>

      <div className="sidebar-filters">
        <div className="filter-row">
          <label className="filter-label" htmlFor="layer-filter">Layer</label>
          <select
            id="layer-filter"
            className="filter-select"
            value={layerFilter}
            onChange={(e) => setLayerFilter(e.target.value as LayerFilter)}
          >
            <option value="ALL">All</option>
            <option value="ATO">ATO</option>
            <option value="SEM">SEM</option>
            <option value="CLU">CLU</option>
            <option value="MEMA">MEMA</option>
          </select>
        </div>

        <div className="filter-row">
          <label className="filter-label" htmlFor="tier-filter">Tier</label>
          <select
            id="tier-filter"
            className="filter-select"
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value as TierFilter)}
          >
            <option value="ALL">All</option>
            <option value="STRONG">Strong</option>
            <option value="WEAK">Weak</option>
          </select>
        </div>

        {families.length > 0 && (
          <div className="filter-row">
            <label className="filter-label" htmlFor="family-filter">Family</label>
            <select
              id="family-filter"
              className="filter-select"
              value={familyFilter}
              onChange={(e) => setFamilyFilter(e.target.value)}
            >
              <option value="ALL">All</option>
              {families.map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
          </div>
        )}

        <div className="filter-row">
          <label className="filter-label" htmlFor="sort-mode">Sort</label>
          <select
            id="sort-mode"
            className="filter-select"
            value={sortMode}
            onChange={(e) => setSortMode(e.target.value as SortMode)}
          >
            <option value="layer">Layer (importance)</option>
            <option value="confidence">Confidence</option>
            <option value="family">Family</option>
          </select>
        </div>
      </div>

      <div className="sidebar-count">
        {filtered.length} of {markers.filter((m) => m.tier !== 'DISCARDED').length} markers
      </div>

      <ul className="sidebar-marker-list" role="list">
        {filtered.map((marker, idx) => (
          <MarkerItem
            key={`${marker.id}-${idx}`}
            marker={marker}
            isActive={activeMarkerId === marker.id}
            isExpanded={expandedId === marker.id}
            onSelect={() => onSelectMarker(activeMarkerId === marker.id ? null : marker.id)}
            onToggleExpand={() => handleToggleExpand(marker.id)}
          />
        ))}
        {filtered.length === 0 && (
          <li className="sidebar-empty">No markers match filters.</li>
        )}
      </ul>
    </div>
  )
}

interface MarkerItemProps {
  marker: DetectedMarker
  isActive: boolean
  isExpanded: boolean
  onSelect: () => void
  onToggleExpand: () => void
}

function MarkerItem({ marker, isActive, isExpanded, onSelect, onToggleExpand }: MarkerItemProps) {
  const layerClass = `marker-layer--${marker.layer.toLowerCase()}`
  const tierClass = `marker-tier--${marker.tier.toLowerCase()}`

  return (
    <li
      className={`sidebar-marker-item ${isActive ? 'sidebar-marker-item--active' : ''}`}
      role="listitem"
    >
      <div
        className="marker-item-header"
        role="button"
        tabIndex={0}
        aria-pressed={isActive}
        aria-label={`${marker.id}: click to ${isActive ? 'deselect' : 'highlight in text'}`}
        onClick={onSelect}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onSelect()
          }
        }}
      >
        <div className="marker-item-badges">
          <span className={`marker-layer-badge ${layerClass}`}>{marker.layer}</span>
          <span className={`marker-tier-badge ${tierClass}`}>{marker.tier}</span>
        </div>
        <span className="marker-item-id">{marker.id}</span>
        <span className="marker-item-conf">
          {Math.round(marker.adjusted_confidence * 100)}%
        </span>
      </div>

      <p className="marker-item-desc">{marker.description}</p>

      <button
        className="marker-item-expand"
        onClick={(e) => { e.stopPropagation(); onToggleExpand() }}
        aria-expanded={isExpanded}
        aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
      >
        {isExpanded ? 'Hide details' : 'Details'}
      </button>

      {isExpanded && (
        <div className="marker-item-details">
          {marker.family && (
            <div className="detail-row">
              <span className="detail-label">Family</span>
              <span className="detail-value">{marker.family}</span>
            </div>
          )}

          <div className="detail-row">
            <span className="detail-label">Raw confidence</span>
            <span className="detail-value">{Math.round(marker.confidence * 100)}%</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Resonance</span>
            <span className="detail-value">{Math.round(marker.resonance_score * 100)}%</span>
          </div>

          <div className="detail-row">
            <span className="detail-label">Meaning</span>
            <span className="detail-value detail-value--italic">{marker.meaning_in_context}</span>
          </div>

          {marker.vad && (
            <div className="detail-vad">
              <span className="detail-label">VAD</span>
              <div className="vad-bars">
                <VadBar label="V" value={marker.vad.valence} />
                <VadBar label="A" value={marker.vad.arousal} />
                <VadBar label="D" value={marker.vad.dominance} />
              </div>
            </div>
          )}

          {marker.matches.length > 0 && (
            <div className="detail-matches">
              <span className="detail-label">Patterns matched</span>
              {marker.matches.map((m, i) => (
                <code key={i} className="detail-match-text">
                  {m.matched_text}
                </code>
              ))}
            </div>
          )}
        </div>
      )}
    </li>
  )
}

function VadBar({ label, value }: { label: string; value: number }) {
  const isNegative = value < 0
  const fillLeft = isNegative ? `${((value + 1) / 2) * 100}%` : '50%'

  return (
    <div className="vad-bar-row">
      <span className="vad-label">{label}</span>
      <div className="vad-bar-track">
        <div className="vad-bar-center" />
        <div
          className={`vad-bar-fill ${isNegative ? 'vad-bar-fill--negative' : ''}`}
          style={{
            left: fillLeft,
            width: `${Math.abs(value) * 50}%`,
          }}
        />
      </div>
      <span className="vad-value">{value.toFixed(2)}</span>
    </div>
  )
}
