import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MarkerSidebar } from './MarkerSidebar'
import type { DetectedMarker } from '../api/types'

function makeMarker(overrides: Partial<DetectedMarker> = {}): DetectedMarker {
  return {
    id: 'ATO_HESITATION',
    layer: 'ATO',
    family: 'MODAL_DOUBT',
    confidence: 0.85,
    description: 'Hesitation in self-disclosure',
    matches: [{ pattern: '\\bnot\\s+sure\\b', span: [22, 30], matched_text: 'not sure' }],
    message_indices: [0],
    resonance_score: 0.92,
    adjusted_confidence: 0.78,
    tier: 'STRONG',
    meaning_in_context: 'This could indicate uncertainty',
    vad: { valence: -0.5, arousal: 0.6, dominance: 0.2 },
    ...overrides,
  }
}

const MARKERS: DetectedMarker[] = [
  makeMarker(),
  makeMarker({
    id: 'ATO_EVASION',
    layer: 'ATO',
    family: 'AVOIDANCE',
    confidence: 0.72,
    adjusted_confidence: 0.61,
    tier: 'STRONG',
    description: 'Evasion of direct answer',
    meaning_in_context: 'Deliberate information withholding',
  }),
  makeMarker({
    id: 'SEM_DOUBT_COMPLEX',
    layer: 'SEM',
    family: 'MODAL_DOUBT',
    confidence: 0.65,
    adjusted_confidence: 0.45,
    tier: 'WEAK',
    description: 'Complex doubt pattern',
    meaning_in_context: 'Multi-layered uncertainty',
  }),
  makeMarker({
    id: 'ATO_DISCARDED',
    layer: 'ATO',
    tier: 'DISCARDED',
    adjusted_confidence: 0.1,
    description: 'Should not appear',
  }),
]

describe('MarkerSidebar', () => {
  it('renders marker list excluding DISCARDED', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    expect(screen.getByText('ATO_HESITATION')).toBeInTheDocument()
    expect(screen.getByText('ATO_EVASION')).toBeInTheDocument()
    expect(screen.getByText('SEM_DOUBT_COMPLEX')).toBeInTheDocument()
    expect(screen.queryByText('ATO_DISCARDED')).not.toBeInTheDocument()
    expect(screen.getByText('3 of 3 markers')).toBeInTheDocument()
  })

  it('filters by search query', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    const input = screen.getByPlaceholderText('Search markers...')
    fireEvent.change(input, { target: { value: 'evasion' } })
    expect(screen.getByText('ATO_EVASION')).toBeInTheDocument()
    expect(screen.queryByText('ATO_HESITATION')).not.toBeInTheDocument()
  })

  it('filters by layer', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    const select = screen.getByLabelText('Layer')
    fireEvent.change(select, { target: { value: 'SEM' } })
    expect(screen.getByText('SEM_DOUBT_COMPLEX')).toBeInTheDocument()
    expect(screen.queryByText('ATO_HESITATION')).not.toBeInTheDocument()
  })

  it('filters by tier', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    const select = screen.getByLabelText('Tier')
    fireEvent.change(select, { target: { value: 'WEAK' } })
    expect(screen.getByText('SEM_DOUBT_COMPLEX')).toBeInTheDocument()
    expect(screen.queryByText('ATO_HESITATION')).not.toBeInTheDocument()
  })

  it('calls onSelectMarker when item header is clicked', () => {
    const onSelect = vi.fn()
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={onSelect} />,
    )
    const header = screen.getByLabelText(/ATO_HESITATION: click to highlight/)
    fireEvent.click(header)
    expect(onSelect).toHaveBeenCalledWith('ATO_HESITATION')
  })

  it('deselects active marker on second click', () => {
    const onSelect = vi.fn()
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId="ATO_HESITATION" onSelectMarker={onSelect} />,
    )
    const header = screen.getByLabelText(/ATO_HESITATION: click to deselect/)
    fireEvent.click(header)
    expect(onSelect).toHaveBeenCalledWith(null)
  })

  it('expands marker details on Details click', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    // Default sort: SEM first (index 0), then ATO (index 1, 2)
    const detailsBtns = screen.getAllByText('Details')
    fireEvent.click(detailsBtns[0]) // SEM_DOUBT_COMPLEX
    expect(screen.getByText('Multi-layered uncertainty')).toBeInTheDocument()
  })

  it('shows VAD bars in expanded details', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    const detailsBtns = screen.getAllByText('Details')
    fireEvent.click(detailsBtns[0])
    expect(screen.getByText('-0.50')).toBeInTheDocument()
    expect(screen.getByText('0.60')).toBeInTheDocument()
    expect(screen.getByText('0.20')).toBeInTheDocument()
  })

  it('shows empty state when no markers match filters', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    const input = screen.getByPlaceholderText('Search markers...')
    fireEvent.change(input, { target: { value: 'zzzznonexistent' } })
    expect(screen.getByText('No markers match filters.')).toBeInTheDocument()
  })

  it('supports keyboard navigation on marker header', () => {
    const onSelect = vi.fn()
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={onSelect} />,
    )
    const header = screen.getByLabelText(/ATO_HESITATION: click to highlight/)
    fireEvent.keyDown(header, { key: 'Enter' })
    expect(onSelect).toHaveBeenCalledWith('ATO_HESITATION')
  })

  it('filters by family', () => {
    render(
      <MarkerSidebar markers={MARKERS} activeMarkerId={null} onSelectMarker={vi.fn()} />,
    )
    const select = screen.getByLabelText('Family')
    fireEvent.change(select, { target: { value: 'AVOIDANCE' } })
    expect(screen.getByText('ATO_EVASION')).toBeInTheDocument()
    expect(screen.queryByText('ATO_HESITATION')).not.toBeInTheDocument()
  })
})
