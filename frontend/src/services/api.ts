import type {
  AppSettings,
  BatchResult,
  DashboardSummary,
  GraphData,
  Health,
  LiveLookup,
  MetricsResponse,
  Paginated,
  PredictionResult,
  RiskDistribution,
  TemporalResponse,
  TransactionDetail,
  TransactionSummary,
} from '../types'

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? ''

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly payload?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError('Cannot reach the backend API. Is it running on port 8000?', 0)
  }
  const text = await response.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = text
    }
  }
  if (!response.ok) {
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`
    throw new ApiError(detail, response.status, payload)
  }
  return payload as T
}

const query = (params: Record<string, string | number | boolean | undefined>) => {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.set(key, String(value))
  })
  const serialized = search.toString()
  return serialized ? `?${serialized}` : ''
}

export const api = {
  health: () => request<Health>('/api/health'),
  summary: () => request<DashboardSummary>('/api/dashboard/summary'),
  transactions: (params: {
    search?: string
    label?: string
    risk?: string
    sort_by?: string
    order?: string
    page?: number
    page_size?: number
    mask?: boolean
  }) => request<Paginated<TransactionSummary>>(`/api/transactions${query(params)}`),
  transaction: (id: string) =>
    request<TransactionDetail>(`/api/transactions/${encodeURIComponent(id)}`),
  graph: (id: string, depth = 1, limit = 30) =>
    request<GraphData>(
      `/api/transactions/${encodeURIComponent(id)}/graph${query({ depth, limit })}`,
    ),
  explanation: (id: string) =>
    request<{
      items: unknown[]
      method: string | null
      note: string | null
      warning?: string
      message?: string
    }>(`/api/transactions/${encodeURIComponent(id)}/explanation`),
  predict: (id: string, threshold = 0.5) =>
    request<PredictionResult>('/api/predict', {
      method: 'POST',
      body: JSON.stringify({ transaction_id: id, threshold }),
    }),
  predictBatch: (transactionIds: string[], csvContent?: string, threshold = 0.5) =>
    request<BatchResult>('/api/predict/batch', {
      method: 'POST',
      body: JSON.stringify({
        transaction_ids: transactionIds,
        csv_content: csvContent,
        threshold,
      }),
    }),
  metrics: () => request<MetricsResponse>('/api/models/metrics'),
  train: (
    source: 'demo' | 'elliptic',
    model?: 'auto' | 'random_forest' | 'logistic_regression' | 'hist_gradient_boosting' | 'xgboost',
  ) =>
    request<{ status: string; model_name: string; selection_rule?: string }>(
      `/api/models/train${query({ source, model })}`,
      { method: 'POST' },
    ),
  temporal: (metric = 'illicit_count') =>
    request<TemporalResponse>(`/api/analytics/temporal${query({ metric })}`),
  riskDistribution: (bins = 10) =>
    request<RiskDistribution>(`/api/analytics/risk-distribution${query({ bins })}`),
  settings: () => request<AppSettings>('/api/settings'),
  updateSettings: (payload: Partial<AppSettings>) =>
    request<AppSettings>('/api/settings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  explorerUrl: (id: string) =>
    request<{ transaction_id: string; url: string }>(
      `/api/blockchain/explorer-url${query({ tx_id: id })}`,
    ),
  lookup: (id: string) =>
    request<LiveLookup>(`/api/blockchain/lookup/${encodeURIComponent(id)}`),
}

export default api
