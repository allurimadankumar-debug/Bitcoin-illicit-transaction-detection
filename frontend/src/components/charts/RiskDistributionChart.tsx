import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { RiskDistribution } from '../../types'

export function RiskDistributionChart({ data }: { data: RiskDistribution }) {
  const chartData = data.buckets.map((bucket) => ({
    range: bucket.bucket,
    count: bucket.count,
  }))
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: -18, bottom: 4 }}>
          <defs>
            <linearGradient id="riskBar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#22d3ee" stopOpacity={0.55} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 10 }} interval={1} />
          <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
            contentStyle={{ background: '#0b1430', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: '#e2e8f0' }}
          />
          <Bar dataKey="count" fill="url(#riskBar)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      {data.unrated > 0 && (
        <p className="mt-2 text-center text-[11px] text-slate-500">
          {data.unrated.toLocaleString()} unrated transactions (no model predictions)
        </p>
      )}
    </div>
  )
}
