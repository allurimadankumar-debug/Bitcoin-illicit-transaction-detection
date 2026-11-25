import { useState } from 'react'
import { CalendarClock } from 'lucide-react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Label, Select } from '../components/ui/Field'
import { ErrorState, LoadingState } from '../components/ui/Feedback'
import { SyntheticBanner } from '../components/SyntheticBanner'
import { TemporalTrendChart } from '../components/charts/TemporalTrendChart'
import { formatPercent } from '../lib/utils'

export function TemporalAnalytics() {
  const [metric, setMetric] = useState('illicit_count')
  const { data, error, loading, refetch } = useApi(() => api.temporal(metric), [metric])

  return (
    <div className="space-y-6 animate-fade-in">
      {data?.is_synthetic && <SyntheticBanner compact />}
      <Card>
        <CardHeader>
          <CardTitle>Transaction activity over time</CardTitle>
          <CalendarClock className="h-4 w-4 text-cyan-300" />
        </CardHeader>
        <CardContent>
          <div className="mb-5 w-56">
            <Label htmlFor="metric">View</Label>
            <Select id="metric" value={metric} onChange={(event) => setMetric(event.target.value)}>
              <option value="illicit_count">Illicit counts & volume</option>
              <option value="illicit_rate">Illicit rate</option>
              <option value="volume">Transaction volume</option>
            </Select>
          </div>
          {loading && !data ? <LoadingState /> : error ? <ErrorState message={error} onRetry={() => void refetch()} /> : data && (
            <>
              <TemporalTrendChart points={data.points} />
              <div className="mt-6 max-h-[320px] overflow-auto rounded-lg border border-white/5">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-navy-800 text-[10px] uppercase text-slate-500">
                    <tr><th className="px-3 py-2">Time step</th><th>Total</th><th>Illicit</th><th>Licit</th><th>Unknown</th><th>Illicit rate</th></tr>
                  </thead>
                  <tbody>
                    {data.points.map((point) => (
                      <tr key={point.time_step} className="border-t border-white/5">
                        <td className="px-3 py-2 font-mono text-slate-300">{point.time_step}</td>
                        <td className="font-mono text-slate-400">{point.total}</td>
                        <td className="font-mono text-rose-300">{point.illicit}</td>
                        <td className="font-mono text-emerald-300">{point.licit}</td>
                        <td className="font-mono text-slate-500">{point.unknown}</td>
                        <td className="font-mono text-amber-300">{formatPercent(point.illicit_rate)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
