import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitBranch, Network } from 'lucide-react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import type { GraphData } from '../types'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Label, Select } from '../components/ui/Field'
import { Badge } from '../components/ui/Badge'
import { EmptyState, ErrorState, LoadingState } from '../components/ui/Feedback'
import { SyntheticBanner } from '../components/SyntheticBanner'
import { TransactionGraph } from '../components/charts/TransactionGraph'
import { formatPercent, riskTone } from '../lib/utils'

export function GraphAnalytics() {
  const transactions = useApi(() => api.transactions({ page: 1, page_size: 100, sort_by: 'illicit_count', order: 'desc' }), [])
  const [selected, setSelected] = useState('')
  const [depth, setDepth] = useState(1)
  const [limit, setLimit] = useState(30)
  const [active, setActive] = useState<GraphData | null>(null)

  useEffect(() => {
    if (!selected && transactions.data?.items.length) {
      setSelected(transactions.data.items[0].transaction_id)
    }
  }, [transactions.data, selected])

  const graph = useApi(
    () => (selected ? api.graph(selected, depth, limit) : Promise.resolve(null)),
    [selected, depth, limit],
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {transactions.data?.items[0]?.is_synthetic && <SyntheticBanner compact />}
      <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
        <Card>
          <CardHeader>
            <CardTitle>Transaction neighborhood</CardTitle>
            <Network className="h-4 w-4 text-cyan-300" />
          </CardHeader>
          <CardContent>
            <div className="mb-4 grid gap-3 sm:grid-cols-3">
              <div className="sm:col-span-1">
                <Label htmlFor="graph-tx">Center transaction</Label>
                <Select id="graph-tx" value={selected} onChange={(event) => { setSelected(event.target.value); setActive(null) }}>
                  <option value="">Choose…</option>
                  {transactions.data?.items.map((item) => (
                    <option key={item.transaction_id} value={item.transaction_id}>{item.transaction_id}</option>
                  ))}
                </Select>
              </div>
              <div>
                <Label htmlFor="graph-depth">Neighborhood depth</Label>
                <Select id="graph-depth" value={depth} onChange={(event) => setDepth(Number(event.target.value))}>
                  <option value={1}>1 hop</option>
                  <option value={2}>2 hops</option>
                  <option value={3}>3 hops</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="graph-limit">Node limit</Label>
                <Select id="graph-limit" value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
                  <option value={15}>15 nodes</option>
                  <option value={30}>30 nodes</option>
                  <option value={50}>50 nodes</option>
                  <option value={80}>80 nodes</option>
                </Select>
              </div>
            </div>
            {graph.loading && !graph.data ? <LoadingState label="Building subgraph…" /> : graph.error ? (
              <ErrorState message={graph.error} onRetry={() => void graph.refetch()} />
            ) : graph.data ? (
              <TransactionGraph data={graph.data} onSelect={() => setActive(graph.data)} />
            ) : <EmptyState title="Select a transaction" description="Choose a transaction ID to explore its connected neighborhood." />}
            {graph.data?.truncated && (
              <p className="mt-2 text-center text-[11px] text-amber-300">Subgraph truncated at {limit} nodes — the full graph is never rendered at once.</p>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Graph summary</CardTitle>
              <GitBranch className="h-4 w-4 text-violet-300" />
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {graph.data ? (
                <>
                  <Row label="Center" value={graph.data.center} mono />
                  <Row label="Nodes shown" value={graph.data.nodes.length} />
                  <Row label="Edges shown" value={graph.data.edges.length} />
                  <Row label="Neighbors" value={graph.data.total_neighbors} />
                  <Row label="Depth" value={graph.data.depth} />
                </>
              ) : <p className="text-xs text-slate-500">No graph loaded.</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Connected nodes</CardTitle>
              <span className="text-[11px] text-slate-500">{graph.data?.nodes.length ?? 0} total</span>
            </CardHeader>
            <CardContent className="max-h-[420px] space-y-2 overflow-y-auto">
              {graph.data?.nodes.map((node) => (
                <button
                  key={node.id}
                  onClick={() => setActive(graph.data)}
                  className="flex w-full items-center justify-between gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 text-left hover:bg-white/[0.05]"
                >
                  <div className="min-w-0">
                    <p className="truncate font-mono text-[11px] text-slate-300">{node.id}</p>
                    <p className="text-[10px] text-slate-500">t={node.time_step}</p>
                  </div>
                  <div className="text-right">
                    <Badge variant={node.label === 'illicit' ? 'illicit' : node.label === 'licit' ? 'licit' : node.label === 'high-risk-prediction' ? 'warning' : 'unknown'}>{node.label}</Badge>
                    <p className={`mt-1 font-mono text-[10px] ${riskTone(node.risk_score)}`}>{formatPercent(node.risk_score, 1)}</p>
                  </div>
                </button>
              ))}
              {active && (
                <Link to={`/transactions/${active.center}`} className="block pt-2 text-xs text-cyan-300 hover:underline">
                  Open center transaction details →
                </Link>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, mono = false }: { label: string; value: string | number; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-white/[0.04] pb-2 last:border-0">
      <span className="text-xs text-slate-500">{label}</span>
      <span className={`truncate text-xs text-slate-200 ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}
