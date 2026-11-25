import { Link } from 'react-router-dom'
import {
  ArrowUpRight,
  Coins,
  Gauge,
  Layers3,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  Users,
} from 'lucide-react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { StatCard } from '../components/StatCard'
import { SyntheticBanner } from '../components/SyntheticBanner'
import { ClassDistributionChart } from '../components/charts/ClassDistributionChart'
import { RiskDistributionChart } from '../components/charts/RiskDistributionChart'
import { Badge } from '../components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { ErrorState, LoadingState } from '../components/ui/Feedback'
import { formatNumber, formatPercent, riskTone } from '../lib/utils'

export function Overview() {
  const summary = useApi(() => api.summary(), [])
  const transactions = useApi(() => api.transactions({ page: 1, page_size: 7, mask: false }), [])
  const risk = useApi(() => api.riskDistribution(10), [])

  if (summary.loading) return <LoadingState label="Loading dashboard…" />
  if (summary.error || !summary.data) return <ErrorState message={summary.error ?? 'No data'} onRetry={() => void summary.refetch()} />

  const data = summary.data
  return (
    <div className="space-y-6 animate-fade-in">
      {data.is_synthetic && <SyntheticBanner />}
      {!data.model_trained && (
        <div className="rounded-lg border border-violet-400/25 bg-violet-500/10 px-4 py-3 text-sm text-violet-200">
          No trained model yet. Run <code className="font-mono">python backend/ml/train.py --source demo</code>{' '}
          or use the Train button on the Model Performance page.
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total transactions" value={formatNumber(data.total_transactions)} hint={`${formatNumber(data.labeled_transactions)} labeled`} icon={Layers3} />
        <StatCard label="Illicit (known)" value={formatNumber(data.illicit_transactions)} hint="Ground-truth class 1" icon={ShieldAlert} tone="rose" />
        <StatCard label="Licit (known)" value={formatNumber(data.licit_transactions)} hint="Ground-truth class 2" icon={ShieldCheck} tone="emerald" />
        <StatCard label="High-risk predictions" value={formatNumber(data.high_risk_transactions)} hint="Score ≥ configured threshold" icon={Gauge} tone="amber" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Class distribution</CardTitle>
            <span className="text-[11px] text-slate-500">{formatNumber(data.unknown_transactions)} unlabeled</span>
          </CardHeader>
          <CardContent>
            <ClassDistributionChart
              licit={data.licit_transactions}
              illicit={data.illicit_transactions}
              unknown={data.unknown_transactions}
            />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Illicit risk distribution</CardTitle>
            <span className="text-[11px] text-slate-500">Model-generated scores · {data.model_name ?? 'no model'}</span>
          </CardHeader>
          <CardContent>
            {risk.data ? <RiskDistributionChart data={risk.data} /> : <LoadingState label="Loading distribution…" />}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent transactions</CardTitle>
            <Link to="/explorer" className="flex items-center gap-1 text-xs text-cyan-300 hover:underline">
              View all <ArrowUpRight className="h-3 w-3" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {transactions.loading ? (
              <LoadingState />
            ) : transactions.error ? (
              <ErrorState message={transactions.error} />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-[10px] uppercase tracking-widest text-slate-500">
                    <tr className="border-b border-white/5">
                      <th className="px-5 py-3">Transaction ID</th>
                      <th className="px-3 py-3">Predicted</th>
                      <th className="px-3 py-3">Risk</th>
                      <th className="px-3 py-3">Step</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-5 py-3 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.data?.items.map((item) => (
                      <tr key={item.transaction_id} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                        <td className="px-5 py-3 font-mono text-xs text-slate-300">{item.transaction_id}</td>
                        <td className="px-3 py-3">
                          <Badge variant={item.predicted_class === 'illicit' ? 'illicit' : item.predicted_class === 'licit' ? 'licit' : 'unknown'}>
                            {item.predicted_class}
                          </Badge>
                        </td>
                        <td className={`px-3 py-3 font-mono text-xs ${riskTone(item.risk_score)}`}>{formatPercent(item.risk_score)}</td>
                        <td className="px-3 py-3 text-xs text-slate-400">{item.time_step}</td>
                        <td className="px-3 py-3 text-xs text-slate-400">{item.status}</td>
                        <td className="px-5 py-3 text-right">
                          <Link to={`/transactions/${item.transaction_id}`} className="text-cyan-300 hover:text-cyan-200" aria-label={`View ${item.transaction_id}`}>
                            <ArrowUpRight className="ml-auto h-4 w-4" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Model indicators</CardTitle>
            <Gauge className="h-4 w-4 text-violet-300" />
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { label: 'PR-AUC (illicit)', value: formatPercent(data.best_pr_auc), icon: TrendingUp, tone: 'text-rose-300' },
              { label: 'Recall (illicit)', value: formatPercent(data.best_recall), icon: ShieldAlert, tone: 'text-amber-300' },
              { label: 'F1 (illicit)', value: formatPercent(data.best_f1), icon: Coins, tone: 'text-cyan-300' },
              { label: 'Prediction history', value: formatNumber(data.prediction_history_count), icon: Users, tone: 'text-violet-300' },
            ].map(({ label, value, icon: Icon, tone }) => (
              <div key={label} className="flex items-center justify-between border-b border-white/[0.04] pb-3 last:border-0 last:pb-0">
                <span className="flex items-center gap-2 text-xs text-slate-400"><Icon className={`h-3.5 w-3.5 ${tone}`} />{label}</span>
                <span className="font-mono text-sm text-white">{value}</span>
              </div>
            ))}
            {data.last_trained_at && (
              <p className="text-[10px] text-slate-500">Last trained {new Date(data.last_trained_at).toLocaleString()}</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
