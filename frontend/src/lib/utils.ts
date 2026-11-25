import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPercent(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'N/A'
  return `${(value * 100).toFixed(digits)}%`
}

export function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return new Intl.NumberFormat('en-US').format(value)
}

export function classColor(value: string) {
  switch (value) {
    case 'illicit':
    case 'high-risk':
      return 'text-rose-400 bg-rose-500/10 border-rose-500/25'
    case 'licit':
    case 'low-risk':
      return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25'
    case 'elevated':
    case 'high-risk-prediction':
      return 'text-amber-300 bg-amber-500/10 border-amber-500/25'
    default:
      return 'text-slate-400 bg-slate-500/10 border-slate-500/25'
  }
}

export function riskTone(score: number | null) {
  if (score === null) return 'text-slate-400'
  if (score >= 0.65) return 'text-rose-400'
  if (score >= 0.4) return 'text-amber-300'
  return 'text-emerald-400'
}
