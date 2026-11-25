export type RiskClass = 'licit' | 'illicit' | 'unknown'
export type GroundTruth = 'licit' | 'illicit' | 'unknown'

export interface Health {
  status: string
  version: string
  dataset_source: string
  is_synthetic: boolean
  model_trained: boolean
  timestamp: string
}

export interface DashboardSummary {
  total_transactions: number
  labeled_transactions: number
  illicit_transactions: number
  licit_transactions: number
  unknown_transactions: number
  high_risk_transactions: number
  dataset_source: string
  is_synthetic: boolean
  model_trained: boolean
  model_name: string | null
  best_pr_auc: number | null
  best_recall: number | null
  best_f1: number | null
  test_metrics: Record<string, unknown> | null
  prediction_history_count: number
  last_trained_at: string | null
  note: string | null
}

export interface TransactionSummary {
  transaction_id: string
  masked_transaction_id: string
  time_step: number
  ground_truth_label: GroundTruth
  predicted_class: RiskClass
  risk_score: number | null
  status: string
  is_synthetic: boolean
  in_degree: number
  out_degree: number
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface FeatureValue {
  name: string
  value: number
  category: 'base' | 'graph'
}

export interface RelatedTransaction {
  transaction_id: string
  direction: 'incoming' | 'outgoing'
  ground_truth_label: GroundTruth
  risk_score: number | null
}

export interface TransactionDetail {
  transaction_id: string
  masked_transaction_id: string
  dataset_source: string
  is_synthetic: boolean
  time_step: number
  ground_truth_label: GroundTruth
  predicted_class: RiskClass
  risk_score: number | null
  confidence: number
  model_name: string
  warning: string
  features: FeatureValue[]
  graph_features: Record<string, number>
  related: RelatedTransaction[]
  related_count: number
  risk_indicators: string[]
  note: string | null
}

export interface ExplanationItem {
  feature: string
  value: number
  impact: number
  direction: string
}

export interface PredictionResult {
  transaction_id: string
  predicted_class: RiskClass
  risk_score: number | null
  confidence: number
  model_name: string
  explanation: ExplanationItem[]
  warning: string
  ground_truth_label: GroundTruth
  explanation_method: string | null
  explanation_note: string | null
  model_source: string | null
  calibration: string | null
  note: string | null
  is_synthetic_data: boolean
  is_synthetic_model_data: boolean
  related_count: number
}

export interface BatchResult {
  results: PredictionResult[]
  total: number
  succeeded: number
  failed: number
  errors: Array<{ transaction_id: string; error: string }>
  warning: string
}

export interface GraphNode {
  id: string
  label: string
  color: string
  risk_score: number | null
  time_step: number
  size: number
}

export interface GraphEdge {
  source: string
  target: string
}

export interface GraphData {
  center: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  depth: number
  truncated: boolean
  total_neighbors: number
  is_synthetic: boolean
  note: string | null
}

export interface MetricsResponse {
  available: boolean
  best_model: string | null
  models: Record<string, Record<string, unknown>>
  test_metrics: Record<string, unknown> | null
  split: Record<string, unknown>
  dataset: Record<string, unknown>
  message: string | null
}

export interface TemporalPoint {
  time_step: number
  total: number
  illicit: number
  licit: number
  unknown: number
  illicit_rate: number
}

export interface TemporalResponse {
  points: TemporalPoint[]
  metric: string
  is_synthetic: boolean
}

export interface RiskDistribution {
  bins: number
  buckets: Array<{ bucket: string; count: number }>
  unrated: number
  is_synthetic: boolean
}

export interface AppSettings {
  explorer_base_url: string
  enable_live_lookup: boolean
  mask_ids_by_default: boolean
  dataset_source: string
  version: string
  keys_required: string[]
  overrides: Record<string, unknown>
  note: string
}

export interface LiveLookup {
  transaction_id: string
  enabled: boolean
  is_live_blockchain_data: boolean
  found: boolean
  data: Record<string, unknown> | null
  message: string | null
  explorer_url: string
}

export interface ApiError {
  error: string
  detail: string | unknown
  status_code: number
}
