import { Link, Route, Routes } from 'react-router-dom'
import { AppShell } from './layouts/AppShell'
import { Overview } from './pages/Overview'
import { Detection } from './pages/Detection'
import { Explorer } from './pages/Explorer'
import { GraphAnalytics } from './pages/GraphAnalytics'
import { ModelPerformance } from './pages/ModelPerformance'
import { TemporalAnalytics } from './pages/TemporalAnalytics'
import { PrivacyWeb3 } from './pages/PrivacyWeb3'
import { Settings } from './pages/Settings'
import { TransactionDetail } from './pages/TransactionDetail'

function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <p className="text-5xl font-semibold text-violet-300">404</p>
      <p className="text-slate-300">This page does not exist.</p>
      <Link to="/" className="text-sm text-cyan-300 hover:underline">Return to overview</Link>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Overview />} />
        <Route path="detect" element={<Detection />} />
        <Route path="explorer" element={<Explorer />} />
        <Route path="transactions/:id" element={<TransactionDetail />} />
        <Route path="graph" element={<GraphAnalytics />} />
        <Route path="models" element={<ModelPerformance />} />
        <Route path="temporal" element={<TemporalAnalytics />} />
        <Route path="privacy" element={<PrivacyWeb3 />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
