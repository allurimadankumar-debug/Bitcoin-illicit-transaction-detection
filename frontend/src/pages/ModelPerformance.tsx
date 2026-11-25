import { useState } from 'react'
import { BrainCircuit, RefreshCw } from 'lucide-react'
import { api, ApiError } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { ErrorState, LoadingState, Spinner } from '../components/ui/Feedback'
import { SyntheticBanner } from '../components/SyntheticBanner'
import { ModelComparisonChart } from '../components/charts/ModelComparisonChart'
import { ConfusionMatrix } from '../components/charts/ConfusionMatrix'
import { formatPercent } from '../lib/utils'

export function ModelPerformance() {
  const metrics = useApi(() => api.metrics(), [])
  const [training, setTraining] = useState(false)
  const [trainError, setTrainError] = useState<string | null>(null)

  async function train() {
    setTraining(true)
    setTrainError(null)
    try {
      await api.train('demo', 'random_forest')
      await metrics.refetch()
    } catch (error) {
      setTrainError(error instanceof ApiError ? error.message : 'Training failed')
    } finally {
      setTraining(false)
    }
  }

  if (metrics.loading) return <LoadingState label="Loading model metrics…" />
  if (metrics.error) return <ErrorState message={metrics.error} onRetry={() => void metrics.refetch()} />

  const data = metrics.data
  if (!data?.available) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Card>
          <CardHeader><CardTitle>ML model performance</CardTitle><BrainCircuit className="h-4 w-4 text-violet-300" /></CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-300">{data?.message ?? 'Metrics are unavailable until training completes.'}</p>
            <p className="text-xs text-slate-500">Run <code className="font-mono">python backend/ml/train.py --source demo</code> from the project root, or train a synthetic demo model below.</p>
            {trainError && <p className="text-xs text-rose-300">{trainError}</p>}
            <Button onClick={() => void train()} disabled={training}>
              {training ? <Spinner className="h-4 w-4" /> : <RefreshCw className="h-4 w-4" />} Train Random Forest demo
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {data.dataset?.is_synthetic === true && <SyntheticBanner compact />}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Best model" value={String(data.best_model ?? '—').replaceAll('_', ' ')} />
        <MetricCard label="PR-AUC (illicit)" value={formatPercent(number(data.test_metrics?.pr_auc))} tone="text-rose-300" />
        <MetricCard label="Recall (illicit)" value={formatPercent(number(data.test_metrics?.recall))} tone="text-amber-300" />
        <MetricCard label="Balanced accuracy" value={formatPercent(number(data.test_metrics?.balanced_accuracy))} tone="text-cyan-300" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Model comparison</CardTitle>
            <span className="text-[11px] text-slate-500">Validation split selection · illicit class metrics</span>
          </CardHeader>
          <CardContent><ModelComparisonChart models={data.models} /></CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Confusion matrix</CardTitle>
            <span className="text-[11px] text-slate-500">Chronological test split</span>
          </CardHeader>
          <CardContent>
            <ConfusionMatrix matrix={data.test_metrics?.confusion_matrix} />
            <p className="mt-4 text-[11px] leading-relaxed text-slate-500">
              Accuracy alone is not used for model selection. PR-AUC and illicit-class recall are
              prioritised because illicit transactions are rare.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Detailed metrics</CardTitle>
          <div className="flex items-center gap-2">
            {trainError && <span className="text-xs text-rose-300">{trainError}</span>}
            <Button size="sm" variant="secondary" onClick={() => void train()} disabled={training}>
              {training ? <Spinner className="h-3.5 w-3.5" /> : <RefreshCw className="h-3.5 w-3.5" />} Retrain Random Forest
            </Button>
          </div>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="text-[10px] uppercase tracking-widest text-slate-500">
              <tr className="border-b border-white/5">
                <th className="py-2">Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th><th>Bal. accuracy</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.models).map(([name, model]) => (
                <tr key={name} className="border-b border-white/[0.03]">
                  <td className="py-2.5">
                    <span className="flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-200">{name.replaceAll('_', ' ')}</span>
                      {name === data.best_model && <Badge variant="licit">selected</Badge>}
                    </span>
                  </td>
                  <td className="font-mono text-xs text-slate-300">{formatPercent(number(model.precision))}</td>
                  <td className="font-mono text-xs text-slate-300">{formatPercent(number(model.recall))}</td>
                  <td className="font-mono text-xs text-slate-300">{formatPercent(number(model.f1))}</td>
                  <td className="font-mono text-xs text-slate-300">{formatPercent(number(model.roc_auc))}</td>
                  <td className="font-mono text-xs text-slate-300">{formatPercent(number(model.pr_auc))}</td>
                  <td className="font-mono text-xs text-slate-300">{formatPercent(number(model.balanced_accuracy))}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-[11px] text-slate-500">
            Split: {String(data.split?.method ?? '—')} · train {String(data.split?.train_rows ?? '—')} / validation{' '}
            {String(data.split?.validation_rows ?? '—')} / test {String(data.split?.test_rows ?? '—')} · calibration:{' '}
            {String(data.split?.calibration ?? 'none')}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

function number(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function MetricCard({ label, value, tone = 'text-white' }: { label: string; value: string; tone?: string }) {
  return (
    <Card className="p-4">
      <p className="text-[10px] uppercase tracking-widest text-slate-500">{label}</p>
      <p className={`mt-2 truncate text-xl font-semibold ${tone}`}>{value}</p>
    </Card>
  )
}
