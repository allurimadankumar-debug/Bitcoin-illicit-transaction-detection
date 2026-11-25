import { FlaskConical } from 'lucide-react'

export function SyntheticBanner({ compact = false }: { compact?: boolean }) {
  return (
    <div
      role="status"
      className="flex items-start gap-3 rounded-lg border border-amber-400/25 bg-amber-500/[0.07] px-4 py-3 text-amber-200"
    >
      <FlaskConical className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div className={compact ? 'text-xs' : 'text-sm'}>
        <p className="font-semibold">Synthetic demo data — not real blockchain data</p>
        {!compact && (
          <p className="mt-1 text-amber-200/70">
            Transaction IDs start with DEMO and all labels/predictions come from a seeded simulator.
            Add the Kaggle Elliptic CSVs to <code className="font-mono">data/raw/</code> to use real
            historical data.
          </p>
        )}
      </div>
    </div>
  )
}
