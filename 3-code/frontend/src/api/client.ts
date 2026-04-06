import type {
  ConversationRequest,
  ConversationResponse,
  HealthResponse,
  MarkerListResponse,
  MarkerDetail,
} from './types'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl = '') {
    this.baseUrl = baseUrl
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const { headers: extraHeaders, ...rest } = options ?? {}
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...rest,
      headers: {
        'Content-Type': 'application/json',
        ...(extraHeaders instanceof Headers
          ? Object.fromEntries(extraHeaders.entries())
          : extraHeaders),
      },
    })

    if (!response.ok) {
      const body = await response.json().catch(() => null)
      const code = body?.error?.code ?? `HTTP_${response.status}`
      const message = body?.error?.message ?? response.statusText
      throw new ApiRequestError(code, message, response.status)
    }

    return response.json()
  }

  async analyzeConversation(req: ConversationRequest): Promise<ConversationResponse> {
    return this.request<ConversationResponse>('/v1/analyze/conversation', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  }

  async getMarkers(params?: {
    layer?: string
    family?: string
    search?: string
    limit?: number
    offset?: number
  }): Promise<MarkerListResponse> {
    const query = new URLSearchParams()
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined) query.set(key, String(value))
      }
    }
    const qs = query.toString()
    return this.request<MarkerListResponse>(`/v1/markers${qs ? `?${qs}` : ''}`)
  }

  async getMarker(id: string): Promise<MarkerDetail> {
    return this.request<MarkerDetail>(`/v1/markers/${encodeURIComponent(id)}`)
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/v1/health')
  }
}

export class ApiRequestError extends Error {
  readonly code: string
  readonly status: number

  constructor(code: string, message: string, status: number) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
    this.status = status
  }
}

export const api = new ApiClient()
