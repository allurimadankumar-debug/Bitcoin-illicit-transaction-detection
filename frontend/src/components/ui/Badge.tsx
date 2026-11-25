import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider',
  {
    variants: {
      variant: {
        default: 'border-violet-400/25 bg-violet-500/10 text-violet-300',
        illicit: 'border-rose-400/25 bg-rose-500/10 text-rose-300',
        licit: 'border-emerald-400/25 bg-emerald-500/10 text-emerald-300',
        unknown: 'border-slate-500/25 bg-slate-500/10 text-slate-400',
        warning: 'border-amber-400/25 bg-amber-500/10 text-amber-300',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}
