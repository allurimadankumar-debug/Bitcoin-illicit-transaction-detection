import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface Props {
  models: Record<string, Record<string, unknown>>
}

const METRICS = [
  { key: 'precision', color: '#22d3ee' },
  { key: 'recall', color: '#a855f7' },
  { key: 'f1', color: '#f59e0b' },
  { key: 'pr_auc', color: '#f43f5e' },
]

export function ModelComparisonChart({ models }: Props) {
  const data = Object.entries(models).map(([name, metrics]) => {
    const row: Record<string, string | number> = { name: name.replace(/_/g, ' ') }
    METRICS.forEach(({ key }) => {
      const value = metrics[key]
      row[key] = typeof value === 'number' ? Number(value.toFixed(3)) : 0
    })
    return row
  })

  return (
    <div className="h-[320px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -18, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-18} textAnchor="end" />
          <YAxis domain={[0, 1]} tick={{ fill: '#64748b', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: '#0b1430', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: '#e2e8f0' }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {METRICS.map(({ key, color }) => (
            <Bar key={key} dataKey={key} fill={color} radius={[3, 3, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
