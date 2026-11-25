import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  Activity,
  BarChart3,
  Blocks,
  Fingerprint,
  GitBranch,
  LayoutDashboard,
  Menu,
  Radar,
  Settings,
  ShieldCheck,
  X,
} from 'lucide-react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { cn } from '../lib/utils'

const navigation = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/detect', label: 'Transaction Detection', icon: Radar },
  { to: '/explorer', label: 'Transaction Explorer', icon: Blocks },
  { to: '/graph', label: 'Graph Analytics', icon: GitBranch },
  { to: '/models', label: 'ML Model Performance', icon: BarChart3 },
  { to: '/temporal', label: 'Temporal Analytics', icon: Activity },
  { to: '/privacy', label: 'Privacy & Web3', icon: Fingerprint },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { data: health, error: healthError, loading: healthLoading } = useApi(() => api.health(), [])
  const current = navigation.find((item) => item.to === location.pathname)
  const title = current?.label ?? (location.pathname.startsWith('/transactions/') ? 'Transaction Details' : 'Sentinel Chain')
  const statusLabel = healthError
    ? 'API unavailable'
    : healthLoading || !health
      ? 'Checking API…'
      : health.model_trained
        ? 'Model ready'
        : 'Model not trained'
  const datasetLabel = !health ? 'Unknown' : health.is_synthetic ? 'Synthetic demo' : 'Elliptic historical'

  return (
    <div className="min-h-screen bg-navy-950 text-slate-200">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_15%_-10%,rgba(139,92,246,0.14),transparent_45%),radial-gradient(circle_at_90%_0%,rgba(34,211,238,0.09),transparent_40%)]" />
      <div className="relative flex">
        {mobileOpen && (
          <button
            className="fixed inset-0 z-30 bg-black/60 lg:hidden"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          />
        )}
        <aside
          className={cn(
            'fixed inset-y-0 left-0 z-40 flex w-[258px] flex-col border-r border-white/[0.06] bg-navy-900/95 backdrop-blur-xl transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0',
            mobileOpen ? 'translate-x-0' : '-translate-x-full',
          )}
        >
          <div className="flex h-16 items-center gap-3 border-b border-white/[0.06] px-5">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-violet-500 to-cyan-400">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-tight text-white">Sentinel Chain</p>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Transaction Intelligence</p>
            </div>
            <button className="ml-auto text-slate-400 lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu">
              <X className="h-5 w-5" />
            </button>
          </div>

          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5" aria-label="Main navigation">
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-600">Workspace</p>
            {navigation.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
                    isActive
                      ? 'bg-gradient-to-r from-violet-500/20 to-cyan-500/5 text-white ring-1 ring-inset ring-violet-400/20'
                      : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-100',
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="border-t border-white/[0.06] p-4">
            <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
              <div className="flex items-center gap-2 text-xs">
                <span
                  className={cn(
                    'h-2 w-2 rounded-full',
                    healthError || !health?.model_trained ? 'bg-amber-400' : 'bg-emerald-400',
                  )}
                />
                <span className="text-slate-300">{statusLabel}</span>
              </div>
              <p className="mt-2 text-[10px] text-slate-500">Dataset: {datasetLabel}</p>
              <p className="text-[10px] text-slate-500">API v{health?.version ?? '…'}</p>
            </div>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-white/[0.06] bg-navy-950/80 px-4 backdrop-blur-xl sm:px-7">
            <button className="text-slate-300 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-base font-semibold text-white">{title}</h1>
              <p className="hidden text-[11px] text-slate-500 sm:block">
                Academic research & decision support · predictions are not proof of criminal activity
              </p>
            </div>
          </header>
          <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-7">{<Outlet />}</main>
        </div>
      </div>
    </div>
  )
}
