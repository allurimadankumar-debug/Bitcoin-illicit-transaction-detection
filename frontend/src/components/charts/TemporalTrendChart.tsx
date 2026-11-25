import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { TemporalPoint } from '../../types'

export function TemporalTrendChart({ points }: { points: TemporalPoint[] }) {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 8, right: 10, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="illicitArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.55} />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="volumeArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#22d3ee" stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="time_step" tick={{ fill: '#64748b', fontSize: 10 }} />
          <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: '#0b1430', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: '#e2e8f0' }}
          />
          <Area type="monotone" dataKey="total" name="All transactions" stroke="#22d3ee" fill="url(#volumeArea)" strokeWidth={2} />
          <Area type="monotone" dataKey="illicit" name="Illicit" stroke="#f43f5e" fill="url(#illicitArea)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
