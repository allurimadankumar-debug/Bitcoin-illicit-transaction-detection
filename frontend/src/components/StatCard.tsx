import type { LucideIcon } from 'lucide-react'
import { Card } from './ui/Card'
import { cn } from '../lib/utils'

interface StatCardProps {
  label: string
  value: string | number
  hint?: string
  icon: LucideIcon
  tone?: 'purple' | 'cyan' | 'rose' | 'emerald' | 'amber'
}

const tones = {
  purple: 'from-violet-500/20 text-violet-300',
  cyan: 'from-cyan-500/20 text-cyan-300',
  rose: 'from-rose-500/20 text-rose-300',
  emerald: 'from-emerald-500/20 text-emerald-300',
  amber: 'from-amber-500/20 text-amber-300',
}

export function StatCard({ label, value, hint, icon: Icon, tone = 'purple' }: StatCardProps) {
  return (
    <Card className="group p-4 transition-transform hover:-translate-y-0.5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight text-white">{value}</p>
          {hint && <p className="mt-1 text-[11px] text-slate-500">{hint}</p>}
        </div>
        <div className={cn('rounded-lg bg-gradient-to-br to-transparent p-2.5', tones[tone])}>
          <Icon className="h-5 w-5" aria-hidden />
        </div>
      </div>
    </Card>
  )
}
