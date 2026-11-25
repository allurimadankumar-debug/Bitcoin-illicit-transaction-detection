import { useState } from 'react'
import { ExternalLink, Fingerprint, KeyRound, Link2, ShieldCheck } from 'lucide-react'
import { api, ApiError } from '../services/api'
import { useApi } from '../hooks/useApi'
import type { LiveLookup } from '../types'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input, Label } from '../components/ui/Field'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Feedback'
import { ErrorState } from '../components/ui/Feedback'

const principles = [
  {
    icon: Fingerprint,
    title: 'Pseudonymous, not anonymous',
    body: 'Bitcoin addresses and transaction hashes are public pseudonyms. They can sometimes be linked to real identities through external data.',
  },
  {
    icon: KeyRound,
    title: 'No keys or personal data',
    body: 'This app never asks for a wallet connection, seed phrase, private key, name, email or IP-based profile.',
  },
  {
    icon: Link2,
    title: 'Opaque identifiers',
    body: 'Historical Elliptic IDs are kept as opaque strings. Dashboard tables can mask them; logs redact long identifiers.',
  },
  {
    icon: ShieldCheck,
    title: 'Local-first storage',
    body: 'Only analysis metadata is stored in SQLite. No raw personal information is saved.',
  },
]

export function PrivacyWeb3() {
  const settings = useApi(() => api.settings(), [])
  const [txId, setTxId] = useState('')
  const [explorer, setExplorer] = useState<{ url: string } | null>(null)
  const [lookup, setLookup] = useState<LiveLookup | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function check() {
    if (!txId.trim()) return
    setBusy(true)
    setError(null)
    setExplorer(null)
    setLookup(null)
    try {
      setExplorer(await api.explorerUrl(txId.trim()))
      setLookup(await api.lookup(txId.trim()))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Lookup failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {principles.map(({ icon: Icon, title, body }) => (
          <Card key={title} className="p-4">
            <Icon className="h-5 w-5 text-violet-300" />
            <p className="mt-3 text-sm font-semibold text-white">{title}</p>
            <p className="mt-2 text-xs leading-relaxed text-slate-400">{body}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Blockchain explorer lookup</CardTitle>
            <Link2 className="h-4 w-4 text-cyan-300" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="web3-tx">Bitcoin transaction hash or dataset ID</Label>
              <div className="flex gap-2">
                <Input id="web3-tx" value={txId} onChange={(event) => setTxId(event.target.value)} placeholder="64-hex Bitcoin txid or DEMO00000001" className="font-mono" />
                <Button onClick={() => void check()} disabled={busy || !txId.trim()}>
                  {busy ? <Spinner className="h-4 w-4" /> : 'Check'}
                </Button>
              </div>
            </div>
            {error && <ErrorState message={error} />}
            {explorer && (
              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4 text-sm">
                <p className="text-xs text-slate-400">Configured explorer link</p>
                <a href={explorer.url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 break-all text-cyan-300 hover:underline">
                  {explorer.url} <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                </a>
              </div>
            )}
            {lookup && (
              <div className="space-y-3 rounded-lg border border-white/10 bg-white/[0.02] p-4">
                <div className="flex items-center gap-2">
                  <Badge variant={lookup.is_live_blockchain_data ? 'licit' : 'unknown'}>
                    {lookup.is_live_blockchain_data ? 'Live blockchain data' : 'Not live data'}
                  </Badge>
                  {lookup.found && <Badge variant="licit">Found</Badge>}
                </div>
                {lookup.data ? (
                  <dl className="grid grid-cols-2 gap-2 text-xs">
                    {Object.entries(lookup.data).map(([key, value]) => (
                      <div key={key}>
                        <dt className="text-slate-500">{key.replaceAll('_', ' ')}</dt>
                        <dd className="font-mono text-slate-200">{String(value ?? '—')}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p className="text-xs leading-relaxed text-slate-400">{lookup.message}</p>
                )}
                <p className="border-t border-white/5 pt-3 text-[11px] text-slate-500">
                  Live explorer results are unrelated to the historical, anonymized Elliptic dataset.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration & handling</CardTitle>
            <ShieldCheck className="h-4 w-4 text-emerald-300" />
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="grid gap-2 text-xs">
              <Row label="Explorer base URL" value={settings.data?.explorer_base_url ?? '—'} />
              <Row label="Live lookup" value={settings.data?.enable_live_lookup ? 'Enabled' : 'Disabled'} />
              <Row label="Secret keys required" value={settings.data?.keys_required.length ? settings.data.keys_required.join(', ') : 'None'} />
              <Row label="Dataset source" value={settings.data?.dataset_source ?? '—'} />
            </div>
            <p className="rounded-lg bg-violet-500/10 p-3 text-xs leading-relaxed text-violet-200">
              {settings.data?.note}
            </p>
            <p className="text-xs leading-relaxed text-slate-400">
              The Elliptic dataset is historical and anonymized. Its identifiers are not live Bitcoin
              transaction hashes, so on-chain lookups are intentionally separated and disabled by
              default.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-white/5 pb-2">
      <span className="text-slate-500">{label}</span>
      <span className="truncate font-mono text-slate-200">{value}</span>
    </div>
  )
}
