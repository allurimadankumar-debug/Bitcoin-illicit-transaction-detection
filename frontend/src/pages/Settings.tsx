import { useEffect, useState } from 'react'
import { Save, Shield } from 'lucide-react'
import { api, ApiError } from '../services/api'
import { useApi } from '../hooks/useApi'
import type { AppSettings } from '../types'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input, Label, Select } from '../components/ui/Field'
import { ErrorState, LoadingState } from '../components/ui/Feedback'

export function Settings() {
  const { data, error, loading, refetch } = useApi(() => api.settings(), [])
  const [form, setForm] = useState({
    mask_ids_by_default: false,
    explorer_base_url: '',
    enable_live_lookup: false,
    table_page_size: 12,
    high_risk_threshold: 0.65,
  })
  const [message, setMessage] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!data) return
    setForm({
      mask_ids_by_default: data.mask_ids_by_default,
      explorer_base_url: data.explorer_base_url,
      enable_live_lookup: data.enable_live_lookup,
      table_page_size: Number(data.overrides.table_page_size ?? 12),
      high_risk_threshold: Number(data.overrides.high_risk_threshold ?? 0.65),
    })
  }, [data])

  async function save() {
    setSaving(true)
    setMessage(null)
    try {
      await api.updateSettings(form as Partial<AppSettings>)
      setMessage('Preferences saved.')
      await refetch()
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : 'Could not save preferences')
    } finally {
      setSaving(false)
    }
  }

  if (loading && !data) return <LoadingState label="Loading preferences…" />
  if (error) return <ErrorState message={error} onRetry={() => void refetch()} />

  return (
    <div className="space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <CardTitle>Application preferences</CardTitle>
          <Shield className="h-4 w-4 text-violet-300" />
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="mask">Transaction ID masking</Label>
              <Select id="mask" value={form.mask_ids_by_default ? 'yes' : 'no'} onChange={(event) => setForm({ ...form, mask_ids_by_default: event.target.value === 'yes' })}>
                <option value="no">Show full IDs</option>
                <option value="yes">Mask IDs by default</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="page-size">Table page size</Label>
              <Select id="page-size" value={form.table_page_size} onChange={(event) => setForm({ ...form, table_page_size: Number(event.target.value) })}>
                {[5, 10, 12, 20, 50].map((size) => <option key={size} value={size}>{size} rows</option>)}
              </Select>
            </div>
            <div>
              <Label htmlFor="threshold">High-risk threshold</Label>
              <Input id="threshold" type="number" min={0} max={1} step={0.05} value={form.high_risk_threshold} onChange={(event) => setForm({ ...form, high_risk_threshold: Number(event.target.value) })} />
            </div>
            <div>
              <Label htmlFor="live">Live blockchain lookup</Label>
              <Select id="live" value={form.enable_live_lookup ? 'yes' : 'no'} onChange={(event) => setForm({ ...form, enable_live_lookup: event.target.value === 'yes' })}>
                <option value="no">Disabled (recommended)</option>
                <option value="yes">Enabled for real Bitcoin txids</option>
              </Select>
            </div>
          </div>
          <div>
            <Label htmlFor="explorer">Public explorer base URL</Label>
            <Input id="explorer" value={form.explorer_base_url} onChange={(event) => setForm({ ...form, explorer_base_url: event.target.value })} placeholder="https://blockstream.info/tx" />
            <p className="mt-2 text-[11px] text-slate-500">HTTPS only on non-local hosts. API keys and credentials are never accepted here.</p>
          </div>
          {message && <p role="status" className={`text-xs ${message.startsWith('Preferences') ? 'text-emerald-300' : 'text-rose-300'}`}>{message}</p>}
          <Button onClick={() => void save()} disabled={saving}>
            <Save className="h-4 w-4" /> {saving ? 'Saving…' : 'Save preferences'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Environment configuration</CardTitle></CardHeader>
        <CardContent>
          <p className="mb-3 text-xs text-slate-400">
            Server-side settings are read from <code className="font-mono text-slate-300">.env</code>. Copy{' '}
            <code className="font-mono text-slate-300">.env.example</code> to get started.
          </p>
          <pre className="overflow-x-auto rounded-lg border border-white/5 bg-navy-950/70 p-4 text-[11px] leading-relaxed text-slate-400">{`DATASET_SOURCE=auto          # auto | elliptic | demo
AUTO_TRAIN_DEMO=true         # train a synthetic model on first start
CALIBRATE_MODEL=true         # sigmoid probability calibration
ENABLE_LIVE_LOOKUP=false     # opt-in public explorer API
EXPLORER_BASE_URL=https://blockstream.info/tx
CORS_ORIGINS=http://localhost:5173`}</pre>
          <p className="mt-4 text-[11px] text-slate-500">
            Kaggle credentials are intentionally not stored in the application. See docs/KAGGLE_SETUP.md.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
