import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AnalysisPage } from './AnalysisPage'
import * as client from '../api/client'
import type { ConversationResponse } from '../api/types'

// Mock the API client
vi.mock('../api/client', async () => {
  const actual = await vi.importActual('../api/client')
  return {
    ...actual,
    api: {
      analyzeConversation: vi.fn(),
    },
  }
})

const mockResponse: ConversationResponse = {
  frame: {
    tone: 'uncertain',
    themes: ['doubt'],
    relational_dynamics: 'seeking-support',
    intent: 'exploratory',
    emotional_tenor: -0.3,
    context_validity: 0.6,
    offline_context_risk: 0.5,
  },
  markers: [
    {
      id: 'ATO_HESITATION',
      layer: 'ATO' as const,
      family: 'MODAL_DOUBT',
      confidence: 0.85,
      description: 'Hesitation',
      matches: [{ pattern: 'weiss nicht', span: [4, 14] as [number, number], matched_text: 'weiss nicht' }],
      message_indices: [0],
      resonance_score: 0.9,
      adjusted_confidence: 0.76,
      tier: 'STRONG' as const,
      meaning_in_context: 'Indicates uncertainty',
      vad: { valence: -0.5, arousal: 0.6, dominance: 0.2 },
    },
  ],
  narratives: [
    {
      narrative_id: 1,
      type: 'Primary' as const,
      text: 'The dialogue suggests uncertainty.',
      confidence: 0.8,
      supporting_markers: [
        { id: 'ATO_HESITATION', adjusted_confidence: 0.76, span: [4, 14] as [number, number], meaning_in_context: 'uncertainty' },
      ],
      uncertainty_warning: null,
      score: 0.82,
    },
  ],
  weak_clusters: [],
  semantic_profile: [],
  vad_trajectory: [],
  degraded: false,
  provider_used: 'gemini',
  fallback_reason: null,
  duration_ms: 420,
  meta: {
    processing_ms: 420,
    version: '6.0',
    text_length: 45,
    markers_detected: 1,
    layers_scanned: ['ATO', 'SEM', 'CLU', 'MEMA'],
  },
}

describe('AnalysisPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dialogue input in idle state', () => {
    render(<AnalysisPage />)
    expect(screen.getByText('Dialogue Input')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Paste dialogue here/)).toBeInTheDocument()
    expect(screen.getByText('Analyze')).toBeInTheDocument()
  })

  it('shows error when submitting empty input', () => {
    render(<AnalysisPage />)
    const btn = screen.getByText('Analyze')
    // Button should be disabled when text is empty
    expect(btn).toBeDisabled()
  })

  it('shows loading state during analysis', async () => {
    const mockFn = vi.mocked(client.api.analyzeConversation)
    mockFn.mockImplementation(() => new Promise(() => {})) // never resolves

    render(<AnalysisPage />)
    const textarea = screen.getByPlaceholderText(/Paste dialogue here/)
    fireEvent.change(textarea, { target: { value: 'A: Ich weiss nicht.\nB: Was?' } })
    fireEvent.click(screen.getByText('Analyze'))

    await waitFor(() => {
      expect(screen.getByText('Analyzing...')).toBeInTheDocument()
      expect(screen.getByText('Analyzing dialogue...')).toBeInTheDocument()
    })
  })

  it('displays analysis results after successful submit', async () => {
    const mockFn = vi.mocked(client.api.analyzeConversation)
    mockFn.mockResolvedValueOnce(mockResponse)

    render(<AnalysisPage />)
    const textarea = screen.getByPlaceholderText(/Paste dialogue here/)
    fireEvent.change(textarea, { target: { value: 'A: Ich weiss nicht.\nB: Was meinst du?' } })
    fireEvent.click(screen.getByText('Analyze'))

    await waitFor(() => {
      expect(screen.getByText('Analysis Results')).toBeInTheDocument()
    })

    // Markers detected count
    expect(screen.getByText('1 markers')).toBeInTheDocument()

    // Semantic frame card rendered
    expect(screen.getByText('Semantic Frame')).toBeInTheDocument()

    // Narrative panel rendered
    expect(screen.getByText('Interpretations')).toBeInTheDocument()
  })

  it('shows error state on API failure', async () => {
    const mockFn = vi.mocked(client.api.analyzeConversation)
    mockFn.mockRejectedValueOnce(new client.ApiRequestError('VALIDATION_ERROR', 'Bad input', 400))

    render(<AnalysisPage />)
    const textarea = screen.getByPlaceholderText(/Paste dialogue here/)
    fireEvent.change(textarea, { target: { value: 'A: test' } })
    fireEvent.click(screen.getByText('Analyze'))

    await waitFor(() => {
      expect(screen.getByText('Analysis failed')).toBeInTheDocument()
      expect(screen.getByText('Bad input')).toBeInTheDocument()
      expect(screen.getByText('VALIDATION_ERROR')).toBeInTheDocument()
    })
  })

  it('dismisses error on button click', async () => {
    const mockFn = vi.mocked(client.api.analyzeConversation)
    mockFn.mockRejectedValueOnce(new client.ApiRequestError('ERR', 'fail', 500))

    render(<AnalysisPage />)
    const textarea = screen.getByPlaceholderText(/Paste dialogue here/)
    fireEvent.change(textarea, { target: { value: 'A: test' } })
    fireEvent.click(screen.getByText('Analyze'))

    await waitFor(() => {
      expect(screen.getByText('Analysis failed')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Dismiss'))

    await waitFor(() => {
      expect(screen.queryByText('Analysis failed')).not.toBeInTheDocument()
    })
  })

  it('shows degraded badge when response is degraded', async () => {
    const mockFn = vi.mocked(client.api.analyzeConversation)
    mockFn.mockResolvedValueOnce({
      ...mockResponse,
      frame: null,
      degraded: true,
      provider_used: 'none',
      fallback_reason: 'all_providers_unavailable',
    })

    render(<AnalysisPage />)
    const textarea = screen.getByPlaceholderText(/Paste dialogue here/)
    fireEvent.change(textarea, { target: { value: 'A: test' } })
    fireEvent.click(screen.getByText('Analyze'))

    await waitFor(() => {
      expect(screen.getByText('Degraded')).toBeInTheDocument()
    })
  })

  it('shows export menu with options', async () => {
    const mockFn = vi.mocked(client.api.analyzeConversation)
    mockFn.mockResolvedValueOnce(mockResponse)

    render(<AnalysisPage />)
    const textarea = screen.getByPlaceholderText(/Paste dialogue here/)
    fireEvent.change(textarea, { target: { value: 'A: test' } })
    fireEvent.click(screen.getByText('Analyze'))

    await waitFor(() => {
      expect(screen.getByText('Export')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Export'))
    expect(screen.getByText('JSON (raw data)')).toBeInTheDocument()
    expect(screen.getByText('HTML (report)')).toBeInTheDocument()
  })
})
