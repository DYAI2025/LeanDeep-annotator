/** LeanDeep 6.0 API types — mirrors 2-design/data-model.md */

export interface VADScores {
  valence: number
  arousal: number
  dominance: number
}

export interface SemanticFrame {
  tone: string
  themes: string[]
  relational_dynamics: string
  intent: string
  emotional_tenor: number
  context_validity: number
  offline_context_risk: number
}

export interface PatternMatch {
  pattern: string
  span: [number, number]
  matched_text: string
}

export interface DetectedMarker {
  id: string
  layer: 'ATO' | 'SEM' | 'CLU' | 'MEMA'
  family: string
  confidence: number
  description: string
  matches: PatternMatch[]
  message_indices: number[]
  resonance_score: number
  adjusted_confidence: number
  tier: 'STRONG' | 'WEAK' | 'DISCARDED'
  meaning_in_context: string
  vad: VADScores
}

export interface SupportingMarker {
  id: string
  adjusted_confidence: number
  span: [number, number]
  meaning_in_context: string
}

export interface Narrative {
  narrative_id: number
  type: 'Primary' | 'Contrarian' | 'Novel' | 'High-Uncertainty' | 'Weak Cluster'
  text: string
  confidence: number
  supporting_markers: SupportingMarker[]
  uncertainty_warning: string | null
  score: number
}

export interface WeakMarkerCluster {
  markers: DetectedMarker[]
  coherence: number
  cluster_meaning: string
  confidence: number
}

export interface VADPoint {
  valence: number
  arousal: number
  dominance: number
  message_index: number
}

export interface AnalyzeMeta {
  processing_ms: number
  version: string
  text_length: number
  markers_detected: number
  layers_scanned: string[]
}

export interface ConversationResponse {
  frame: SemanticFrame | null
  markers: DetectedMarker[]
  narratives: Narrative[]
  weak_clusters: WeakMarkerCluster[]
  semantic_profile: Record<string, unknown>[]
  vad_trajectory: VADPoint[]
  degraded: boolean
  provider_used: string
  fallback_reason: string | null
  duration_ms: number
  meta: AnalyzeMeta
}

export interface Message {
  role: string
  text: string
}

export interface ConversationRequest {
  messages: Message[]
  language?: 'de' | 'en'
  layers?: ('ATO' | 'SEM' | 'CLU' | 'MEMA')[]
  threshold?: number
  semantic_mode?: 'auto' | 'llm' | 'embedding' | 'off'
}

export interface MarkerDetail {
  id: string
  layer: string
  lang: string
  description: string
  tags: string[]
  rating: number
  family: string | null
  resonance_tags: string[]
}

export interface MarkerListResponse {
  total: number
  offset: number
  limit: number
  markers: MarkerDetail[]
}

export interface HealthResponse {
  status: string
  version: string
  markers_loaded: number
  uptime_seconds: number
}

export interface ApiError {
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
}
