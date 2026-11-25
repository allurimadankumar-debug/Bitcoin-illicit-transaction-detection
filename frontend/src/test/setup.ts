import '@testing-library/jest-dom/vitest'
import { beforeEach, vi } from 'vitest'

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal('ResizeObserver', ResizeObserverMock)

const transaction = {
  transaction_id: 'DEMO00000001',
  masked_transaction_id: 'DEMO00…0001',
  time_step: 7,
  ground_truth_label: 'illicit',
  predicted_class: 'illicit',
  risk_score: 0.91,
  status: 'high-risk',
  is_synthetic: true,
  in_degree: 2,
  out_degree: 3,
}

const summary = {
  total_transactions: 360,
  labeled_transactions: 250,
  illicit_transactions: 40,
  licit_transactions: 210,
  unknown_transactions: 110,
  high_risk_transactions: 38,
  dataset_source: 'demo',
  is_synthetic: true,
  model_trained: true,
  model_name: 'random_forest',
  best_pr_auc: 0.82,
  best_recall: 0.79,
  best_f1: 0.77,
  test_metrics: { pr_auc: 0.82, recall: 0.79, f1: 0.77, balanced_accuracy: 0.86, confusion_matrix: [[100, 12], [8, 30]] },
  prediction_history_count: 5,
  last_trained_at: '2026-01-01T00:00:00Z',
  note: 'DEMO MODE: synthetic data.',
}

const metrics = {
  available: true,
  best_model: 'random_forest',
  models: {
    logistic_regression: { precision: 0.6, recall: 0.62, f1: 0.61, roc_auc: 0.7, pr_auc: 0.55, balanced_accuracy: 0.68 },
    random_forest: { precision: 0.8, recall: 0.79, f1: 0.77, roc_auc: 0.9, pr_auc: 0.82, balanced_accuracy: 0.86 },
  },
  test_metrics: summary.test_metrics,
  split: { method: 'chronological', train_rows: 150, validation_rows: 40, test_rows: 60, calibration: 'sigmoid' },
  dataset: { is_synthetic: true },
  message: null,
}

function json(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } })
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost')
      const path = url.pathname

      if (path === '/api/health') return json({ status: 'ok', version: '1.0.0', dataset_source: 'demo', is_synthetic: true, model_trained: true, timestamp: '2026-01-01T00:00:00Z' })
      if (path === '/api/dashboard/summary') return json(summary)
      if (path === '/api/transactions') {
        return json({ items: [transaction], total: 360, page: 1, page_size: 12, total_pages: 30 })
      }
      if (path === '/api/models/metrics') return json(metrics)
      if (path === '/api/analytics/risk-distribution') {
        return json({ bins: 10, buckets: Array.from({ length: 10 }, (_, index) => ({ bucket: `${index / 10}-${(index + 1) / 10}`, count: index * 3 })), unrated: 0, is_synthetic: true })
      }
      if (path === '/api/analytics/temporal') {
        return json({ metric: 'illicit_count', is_synthetic: true, points: [{ time_step: 1, total: 10, illicit: 2, licit: 6, unknown: 2, illicit_rate: 0.2 }] })
      }
      if (path === '/api/settings') return json({ explorer_base_url: 'https://blockstream.info/tx', enable_live_lookup: false, mask_ids_by_default: false, dataset_source: 'demo', version: '1.0.0', keys_required: [], overrides: { table_page_size: 12, high_risk_threshold: 0.65 }, note: 'Preferences only.' })
      if (path === '/api/predict') return json({ ...transaction, predicted_class: 'illicit', risk_score: 0.91, confidence: 0.91, model_name: 'random_forest', explanation: [{ feature: 'feature_005', value: 2.1, impact: 0.3, direction: 'increases_risk' }], warning: 'Model prediction is not proof of criminal activity', ground_truth_label: 'illicit', explanation_method: 'shap_tree', explanation_note: null, model_source: 'demo_synthetic', calibration: 'sigmoid', note: null, is_synthetic_data: true, is_synthetic_model_data: true, related_count: 5 })
      if (path === '/api/predict/batch') return json({ results: [], total: 0, succeeded: 0, failed: 0, errors: [], warning: 'Model prediction is not proof of criminal activity' })
      if (path.endsWith('/graph')) return json({ center: 'DEMO00000001', nodes: [{ ...transaction, id: 'DEMO00000001', label: 'illicit', color: '#f43f5e', size: 12 }], edges: [], depth: 1, truncated: false, total_neighbors: 0, is_synthetic: true, note: null })
      if (path.endsWith('/explanation')) return json({ transaction_id: 'DEMO00000001', items: [{ feature: 'feature_005', value: 2.1, impact: 0.3, direction: 'increases_risk' }], method: 'shap_tree', note: 'SHAP values describe model behaviour.', warning: 'Explanations describe model behaviour, not proof of criminal intent.', is_synthetic: true })
      if (path.startsWith('/api/transactions/')) return json({ ...transaction, features: [{ name: 'feature_005', value: 2.1, category: 'base' }], graph_features: { graph_out_count: 3 }, related: [{ transaction_id: 'DEMO00000002', direction: 'outgoing', ground_truth_label: 'licit', risk_score: 0.2 }], related_count: 1, risk_indicators: ['High illicit risk score'], confidence: 0.91, model_name: 'random_forest', warning: 'Model prediction is not proof of criminal activity', note: null })
      if (path === '/api/blockchain/lookup/DEMO00000001') return json({ transaction_id: 'DEMO00000001', enabled: false, is_live_blockchain_data: false, found: false, data: null, message: 'Live lookup is disabled.', explorer_url: 'https://blockstream.info/tx/DEMO00000001' })
      if (path === '/api/blockchain/explorer-url') return json({ transaction_id: 'DEMO00000001', url: 'https://blockstream.info/tx/DEMO00000001' })

      return json({ error: 'NotFound', detail: `Unmocked route: ${path}`, status_code: 404 }, 404)
    }),
  )
})
