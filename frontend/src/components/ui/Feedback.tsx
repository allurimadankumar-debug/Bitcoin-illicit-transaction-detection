import { AlertTriangle, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('h-5 w-5 animate-spin text-violet-400', className)} aria-label="Loading" />
}

export function LoadingState({ label = 'Loading data…' }: { label?: string }) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center gap-3 text-slate-400">
      <Spinner />
      <p className="text-sm">{label}</p>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex min-h-[180px] flex-col items-center justify-center gap-3 text-center">
      <AlertTriangle className="h-8 w-8 text-amber-400" />
      <p className="max-w-md text-sm text-slate-300">{message}</p>
      {onRetry && (
        <button className="text-sm font-medium text-cyan-300 hover:underline" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex min-h-[180px] flex-col items-center justify-center gap-2 text-center">
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {description && <p className="max-w-md text-xs text-slate-500">{description}</p>}
    </div>
  )
}
