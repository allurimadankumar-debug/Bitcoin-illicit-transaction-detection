import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ExternalLink, GitBranch, ShieldAlert } from 'lucide-react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { ErrorState, LoadingState } from '../components/ui/Feedback'
import { SyntheticBanner } from '../components/SyntheticBanner'
import { TransactionGraph } from '../components/charts/TransactionGraph'
import { formatNumber, formatPercent, riskTone } from '../lib/utils'

export function TransactionDetail() {
  const { id = '' } = useParams()
  const detail = useApi(() => api.transaction(decodeURIComponent(id)), [id])
  const graph = useApi(() => api.graph(decodeURIComponent(id), 1, 20), [id])
  const explanation = useApi(() => api.explanation(decodeURIComponent(id)), [id])

  if (detail.loading) return <LoadingState label="Loading transaction analysis…" />
  if (detail.error || !detail.data) {
    return (
      <Card>
        <CardHeader><CardTitle>Transaction not available</CardTitle></CardHeader>
        <CardContent>
          <ErrorState message={detail.error ?? 'Transaction not found'} onRetry={() => void detail.refetch()} />
          <Link to="/explorer" className="mt-4 inline-block text-sm text-cyan-300 hover:underline">← Back to explorer</Link>
        </CardContent>
      </Card>
    )
  }

  const tx = detail.data
  return (
    <div className="space-y-6 animate-fade-in">
      <Link to="/explorer" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-cyan-300">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to explorer
      </Link>
      {tx.is_synthetic && <SyntheticBanner compact />}

      <Card className="overflow-hidden">
        <div className="bg-gradient-to-r from-violet-600/20 via-transparent to-cyan-500/10 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-widest text-slate-400">Transaction ID</p>
              <h2 className="mt-1 break-all font-mono text-lg text-white sm:text-xl">{tx.transaction_id}</h2>
              <p className="mt-2 text-xs text-slate-400">
                Time step {tx.time_step} · dataset {tx.dataset_source}
              </p>
            </div>
            <div className="flex gap-2">
              <Badge variant={tx.ground_truth_label === 'illicit' ? 'illicit' : tx.ground_truth_label === 'licit' ? 'licit' : 'unknown'}>
                Truth: {tx.ground_truth_label}
              </Badge>
              <Badge variant={tx.predicted_class === 'illicit' ? 'illicit' : tx.predicted_class === 'licit' ? 'licit' : 'unknown'}>
                Model: {tx.predicted_class}
              </Badge>
            </div>
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-slate-500">Illicit risk probability</p>
              <p className={`mt-1 font-mono text-3xl ${riskTone(tx.risk_score)}`}>{formatPercent(tx.risk_score, 2)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-slate-500">Model confidence</p>
              <p className="mt-1 font-mono text-3xl text-cyan-300">{formatPercent(tx.confidence)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-slate-500">Model</p>
              <p className="mt-2 font-mono text-sm text-violet-300">{tx.model_name}</p>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Graph neighborhood</CardTitle>
              <GitBranch className="h-4 w-4 text-cyan-300" />
            </CardHeader>
            <CardContent>
              {graph.loading && !graph.data ? <LoadingState /> : graph.error ? <ErrorState message={graph.error} /> : graph.data && graph.data.nodes.length > 0 ? (
                <TransactionGraph data={graph.data} />
              ) : <p className="py-10 text-center text-xs text-slate-500">No graph relationships available for this transaction.</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Feature values</CardTitle>
              <span className="text-[11px] text-slate-500">{tx.features.length} finite values shown</span>
            </CardHeader>
            <CardContent className="max-h-[420px] overflow-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-navy-800 text-[10px] uppercase text-slate-500">
                  <tr><th className="px-2 py-2">Feature</th><th>Type</th><th className="text-right">Value</th></tr>
                </thead>
                <tbody>
                  {tx.features.map((feature) => (
                    <tr key={feature.name} className="border-t border-white/5">
                      <td className="px-2 py-1.5 font-mono text-slate-300">{feature.name}</td>
                      <td className="text-slate-500">{feature.category}</td>
                      <td className="text-right font-mono text-slate-400">{feature.value.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Risk indicators</CardTitle><ShieldAlert className="h-4 w-4 text-amber-300" /></CardHeader>
            <CardContent className="space-y-2">
              {tx.risk_indicators.length ? tx.risk_indicators.map((indicator) => (
                <p key={indicator} className="rounded-lg bg-amber-500/[0.07] px-3 py-2 text-xs text-amber-200">{indicator}</p>
              )) : <p className="text-xs text-slate-500">No heuristic indicators triggered.</p>}
              <p className="pt-2 text-[11px] leading-relaxed text-slate-500">{tx.warning}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Model explanation</CardTitle>
              <span className="text-[10px] text-slate-500">{explanation.data?.method ?? '—'}</span>
            </CardHeader>
            <CardContent className="space-y-2">
              {explanation.loading ? <LoadingState /> : explanation.error ? <ErrorState message={explanation.error} /> : explanation.data?.items?.length ? (
                (explanation.data.items as Array<{ feature: string; value: number; impact: number; direction: string }>).map((item) => (
                  <div key={item.feature} className="flex items-center justify-between gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
                    <div className="min-w-0">
                      <p className="truncate font-mono text-[11px] text-slate-300">{item.feature}</p>
                      <p className="text-[10px] text-slate-500">value {formatNumber(item.value)}</p>
                    </div>
                    <span className={`font-mono text-xs ${item.impact > 0 ? 'text-rose-300' : 'text-emerald-300'}`}>
                      {item.impact > 0 ? '+' : ''}{item.impact.toFixed(4)}
                    </span>
                  </div>
                ))
              ) : <p className="text-xs text-slate-500">No explanation available. {explanation.data?.message ?? ''}</p>}
              {(explanation.data?.note || explanation.data?.warning) && (
                <p className="pt-2 text-[11px] leading-relaxed text-slate-500">
                  {explanation.data?.note}
                  {explanation.data?.note && explanation.data?.warning ? ' · ' : ''}
                  {explanation.data?.warning}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Relationships</CardTitle>
              <span className="text-[11px] text-slate-500">{tx.related_count} neighbors</span>
            </CardHeader>
            <CardContent className="max-h-[340px] space-y-2 overflow-auto">
              {tx.related.map((item) => (
                <div key={`${item.direction}-${item.transaction_id}`} className="flex items-center justify-between gap-2 border-b border-white/5 pb-2">
                  <div className="min-w-0">
                    <p className="truncate font-mono text-[11px] text-slate-300">{item.transaction_id}</p>
                    <p className="text-[10px] text-slate-500">{item.direction} · truth: {item.ground_truth_label}</p>
                  </div>
                  <span className={`font-mono text-xs ${riskTone(item.risk_score)}`}>{formatPercent(item.risk_score, 1)}</span>
                </div>
              ))}
              {!tx.related.length && <p className="text-xs text-slate-500">No incoming or outgoing relationships.</p>}
              <Button variant="ghost" size="sm" className="mt-2 w-full" onClick={() => void graph.refetch()}>
                <ExternalLink className="h-3.5 w-3.5" /> Refresh neighborhood
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
