import * as React from 'react'
import { cn } from '../../lib/utils'

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'h-10 w-full rounded-lg border border-white/10 bg-navy-900/70 px-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20',
        className,
      )}
      {...props}
    />
  ),
)
Input.displayName = 'Input'

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      'h-10 w-full rounded-lg border border-white/10 bg-navy-900/70 px-3 text-sm text-slate-100 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20',
      className,
    )}
    {...props}
  />
))
Select.displayName = 'Select'

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      'min-h-[120px] w-full rounded-lg border border-white/10 bg-navy-900/70 p-3 font-mono text-xs text-slate-100 placeholder:text-slate-500 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20',
      className,
    )}
    {...props}
  />
))
Textarea.displayName = 'Textarea'

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn('mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-400', className)}
      {...props}
    />
  )
}
