import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDown, ArrowUp, ArrowUpRight, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input, Label, Select } from '../components/ui/Field'
import { Badge } from '../components/ui/Badge'
import { ErrorState, LoadingState } from '../components/ui/Feedback'
import { SyntheticBanner } from '../components/SyntheticBanner'
import { cn, formatPercent, riskTone } from '../lib/utils'

export function Explorer() {
  const [search, setSearch] = useState('')
  const [label, setLabel] = useState('all')
  const [risk, setRisk] = useState('all')
  const [sortBy, setSortBy] = useState('time_step')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [mask, setMask] = useState(false)

  const { data, error, loading, refetch } = useApi(
    () => api.transactions({ search, label, risk, sort_by: sortBy, order, page, page_size: 12, mask }),
    [search, label, risk, sortBy, order, page, mask],
  )

  function toggleSort(column: string) {
    if (sortBy === column) setOrder(order === 'asc' ? 'desc' : 'asc')
    else { setSortBy(column); setOrder('desc') }
    setPage(1)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {data?.items[0]?.is_synthetic && <SyntheticBanner compact />}
      <Card>
        <CardHeader>
          <CardTitle>Transaction explorer</CardTitle>
          <span className="text-xs text-slate-500">{data?.total.toLocaleString() ?? 0} matching transactions</span>
        </CardHeader>
        <CardContent>
          <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                <Input id="search" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="ID, time step or status" className="pl-9" />
              </div>
            </div>
            <div>
              <Label htmlFor="label-filter">Ground truth</Label>
              <Select id="label-filter" value={label} onChange={(event) => { setLabel(event.target.value); setPage(1) }}>
                <option value="all">All labels</option>
                <option value="illicit">Illicit</option>
                <option value="licit">Licit</option>
                <option value="unknown">Unknown</option>
                <option value="predicted_illicit">Predicted illicit</option>
                <option value="predicted_licit">Predicted licit</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="risk-filter">Risk status</Label>
              <Select id="risk-filter" value={risk} onChange={(event) => { setRisk(event.target.value); setPage(1) }}>
                <option value="all">All risk levels</option>
                <option value="high-risk">High risk</option>
                <option value="elevated">Elevated</option>
                <option value="low-risk">Low risk</option>
                <option value="unrated">Unrated</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="mask-toggle">Privacy</Label>
              <Select id="mask-toggle" value={mask ? 'masked' : 'full'} onChange={(event) => setMask(event.target.value === 'masked')}>
                <option value="full">Full IDs</option>
                <option value="masked">Masked IDs</option>
              </Select>
            </div>
          </div>

          {loading && !data ? <LoadingState /> : error ? <ErrorState message={error} onRetry={() => void refetch()} /> : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[820px] text-left text-sm">
                  <thead className="text-[10px] uppercase tracking-widest text-slate-500">
                    <tr className="border-b border-white/5">
                      <SortableHeader label="Transaction ID" column="transaction_id" current={sortBy} order={order} onClick={toggleSort} />
                      <th className="px-3 py-3">Ground truth</th>
                      <th className="px-3 py-3">Predicted</th>
                      <SortableHeader label="Risk score" column="risk_score" current={sortBy} order={order} onClick={toggleSort} />
                      <SortableHeader label="Time step" column="time_step" current={sortBy} order={order} onClick={toggleSort} />
                      <th className="px-3 py-3">In / Out</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-5 py-3 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.items.map((item) => (
                      <tr key={item.transaction_id} className="border-b border-white/[0.03] transition-colors hover:bg-white/[0.02]">
                        <td className="px-5 py-3 font-mono text-xs text-slate-200">{item.transaction_id}</td>
                        <td className="px-3 py-3"><Badge variant={item.ground_truth_label as 'illicit' | 'licit' | 'unknown'}>{item.ground_truth_label}</Badge></td>
                        <td className="px-3 py-3"><Badge variant={item.predicted_class === 'illicit' ? 'illicit' : item.predicted_class === 'licit' ? 'licit' : 'unknown'}>{item.predicted_class}</Badge></td>
                        <td className={cn('px-3 py-3 font-mono text-xs', riskTone(item.risk_score))}>{formatPercent(item.risk_score, 2)}</td>
                        <td className="px-3 py-3 text-xs text-slate-400">{item.time_step}</td>
                        <td className="px-3 py-3 font-mono text-xs text-slate-400">{item.in_degree} / {item.out_degree}</td>
                        <td className="px-3 py-3 text-xs text-slate-400">{item.status}</td>
                        <td className="px-5 py-3 text-right">
                          <Link to={`/transactions/${item.transaction_id}`} className="inline-flex text-cyan-300 hover:text-cyan-200" aria-label={`View details for ${item.transaction_id}`}>
                            <ArrowUpRight className="h-4 w-4" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-5 flex items-center justify-between text-xs text-slate-500">
                <span>Page {data?.page ?? 1} of {data?.total_pages ?? 1}</span>
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" disabled={(data?.page ?? 1) <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
                    <ChevronLeft className="h-4 w-4" /> Previous
                  </Button>
                  <Button size="sm" variant="secondary" disabled={(data?.page ?? 1) >= (data?.total_pages ?? 1)} onClick={() => setPage((value) => value + 1)}>
                    Next <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function SortableHeader({
  label, column, current, order, onClick,
}: { label: string; column: string; current: string; order: string; onClick: (column: string) => void }) {
  return (
    <th className="px-3 py-3">
      <button className="inline-flex items-center gap-1 hover:text-slate-200" onClick={() => onClick(column)}>
        {label}
        {current === column && (order === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
      </button>
    </th>
  )
}
