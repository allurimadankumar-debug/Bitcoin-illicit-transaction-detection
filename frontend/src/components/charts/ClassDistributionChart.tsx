import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

interface Props {
  licit: number
  illicit: number
  unknown: number
}

export function ClassDistributionChart({ licit, illicit, unknown }: Props) {
  const data = [
    { name: 'Licit', value: licit, color: '#22c55e' },
    { name: 'Illicit', value: illicit, color: '#f43f5e' },
    { name: 'Unknown', value: unknown, color: '#64748b' },
  ].filter((item) => item.value > 0)

  return (
    <div className="h-[220px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={86} paddingAngle={3} stroke="none">
            {data.map((item) => (
              <Cell key={item.name} fill={item.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#0b1430', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: '#e2e8f0' }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="mt-1 flex flex-wrap justify-center gap-4 text-xs text-slate-400">
        {data.map((item) => (
          <span key={item.name} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: item.color }} />
            {item.name}: <strong className="text-slate-200">{item.value.toLocaleString()}</strong>
          </span>
        ))}
      </div>
    </div>
  )
}
