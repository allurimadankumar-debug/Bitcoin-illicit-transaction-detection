import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileUp, ScanSearch, ShieldAlert, Sparkles } from 'lucide-react'
import { api, ApiError } from '../services/api'
import { useApi } from '../hooks/useApi'
import type { BatchResult, PredictionResult } from '../types'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input, Label, Select } from '../components/ui/Field'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Feedback'
import { SyntheticBanner } from '../components/SyntheticBanner'
import { classColor, formatPercent, riskTone } from '../lib/utils'

export function Detection() {
  const [txId, setTxId] = useState('')
  const [csv, setCsv] = useState('')
  const [csvName, setCsvName] = useState('')
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [batch, setBatch] = useState<BatchResult | null>(null)
  const [busy, setBusy] = useState<'single' | 'batch' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const transactions = useApi(() => api.transactions({ page: 1, page_size: 100, sort_by: 'time_step', order: 'desc' }), [])

  const options = useMemo(
    () => transactions.data?.items.map((item) => item.transaction_id) ?? [],
    [transactions.data],
  )

  async function runSingle() {
    if (!txId.trim()) return
    setBusy('single')
    setError(null)
    setPrediction(null)
    try {
      setPrediction(await api.predict(txId.trim()))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Prediction failed')
    } finally {
      setBusy(null)
    }
  }

  async function runBatch() {
    setBusy('batch')
    setError(null)
    setBatch(null)
    try {
      const ids = csv.split(/[\r\n,]+/).map((value) => value.trim()).filter(Boolean)
      setBatch(await api.predictBatch(ids, csv))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Batch prediction failed')
    } finally {
      setBusy(null)
    }
  }

  function loadFile(file: File | undefined) {
    if (!file) return
    setCsvName(file.name)
    const reader = new FileReader()
    reader.onload = () => setCsv(String(reader.result ?? ''))
    reader.readAsText(file)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {prediction?.is_synthetic_data && <SyntheticBanner compact />}
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Single transaction analysis</CardTitle>
            <ScanSearch className="h-4 w-4 text-cyan-300" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="tx-input">Transaction ID</Label>
              <div className="flex gap-2">
                <Input
                  id="tx-input"
                  value={txId}
                  onChange={(event) => setTxId(event.target.value)}
                  placeholder="DEMO00000001 or a 64-char Bitcoin hash"
                  className="font-mono"
                  onKeyDown={(event) => event.key === 'Enter' && void runSingle()}
                />
                <Button onClick={() => void runSingle()} disabled={busy === 'single' || !txId.trim()}>
                  {busy === 'single' ? <Spinner className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                  Analyze
                </Button>
              </div>
            </div>
            <div>
              <Label htmlFor="tx-select">Or select from the loaded dataset</Label>
              <Select
                id="tx-select"
                defaultValue=""
                onChange={(event) => event.target.value && setTxId(event.target.value)}
                disabled={!options.length}
              >
                <option value="">Choose a transaction…</option>
                {options.map((id) => (
                  <option key={id} value={id}>{id}</option>
                ))}
              </Select>
              {transactions.error && <p className="mt-2 text-xs text-rose-300">{transactions.error}</p>}
            </div>
            {error && <p role="alert" className="rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{error}</p>}
            {prediction && <PredictionCard result={prediction} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Batch CSV analysis</CardTitle>
            <FileUp className="h-4 w-4 text-violet-300" />
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs leading-relaxed text-slate-400">
              Upload a CSV with transaction IDs in the first column (a header such as{' '}
              <code className="font-mono text-slate-300">tx_id</code> is detected automatically), or paste
              IDs directly. Maximum 5,000 rows.
            </p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(event) => loadFile(event.target.files?.[0])}
            />
            <Button variant="secondary" onClick={() => fileRef.current?.click()}>
              <FileUp className="h-4 w-4" /> {csvName || 'Choose CSV file'}
            </Button>
            <textarea
              value={csv}
              onChange={(event) => setCsv(event.target.value)}
              placeholder={'tx_id\nDEMO00000001\nDEMO00000002'}
              rows={6}
              className="w-full rounded-lg border border-white/10 bg-navy-900/70 p-3 font-mono text-xs text-slate-200 placeholder:text-slate-600 focus:border-violet-400/50 focus:outline-none"
            />
            <Button onClick={() => void runBatch()} disabled={busy === 'batch' || !csv.trim()}>
              {busy === 'batch' ? <Spinner className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
              Analyze batch
            </Button>
            {batch && (
              <div className="space-y-3">
                <div className="flex gap-4 text-xs text-slate-400">
                  <span>Total: <strong className="text-white">{batch.total}</strong></span>
                  <span>Succeeded: <strong className="text-emerald-300">{batch.succeeded}</strong></span>
                  <span>Failed: <strong className="text-rose-300">{batch.failed}</strong></span>
                </div>
                <div className="max-h-72 overflow-auto rounded-lg border border-white/5">
                  <table className="w-full text-left text-xs">
                    <thead className="sticky top-0 bg-navy-800 text-[10px] uppercase text-slate-500">
                      <tr><th className="px-3 py-2">ID</th><th className="px-3 py-2">Class</th><th className="px-3 py-2">Risk</th></tr>
                    </thead>
                    <tbody>
                      {batch.results.map((item) => (
                        <tr key={item.transaction_id} className="border-t border-white/5">
                          <td className="px-3 py-2 font-mono">{item.transaction_id}</td>
                          <td className="px-3 py-2"><Badge variant={item.predicted_class === 'illicit' ? 'illicit' : 'licit'}>{item.predicted_class}</Badge></td>
                          <td className={`px-3 py-2 font-mono ${riskTone(item.risk_score)}`}>{formatPercent(item.risk_score)}</td>
                        </tr>
                      ))}
                      {batch.errors.map((item) => (
                        <tr key={`err-${item.transaction_id}`} className="border-t border-white/5 text-rose-300">
                          <td className="px-3 py-2 font-mono">{item.transaction_id}</td>
                          <td colSpan={2} className="px-3 py-2">{item.error}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function PredictionCard({ result }: { result: PredictionResult }) {
  return (
    <div className="rounded-xl border border-white/10 bg-gradient-to-br from-violet-500/10 to-cyan-500/[0.03] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-widest text-slate-500">Model prediction</p>
          <p className={`mt-1 text-2xl font-semibold ${result.predicted_class === 'illicit' ? 'text-rose-300' : result.predicted_class === 'licit' ? 'text-emerald-300' : 'text-slate-400'}`}>
            {result.predicted_class}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] uppercase tracking-widest text-slate-500">Illicit risk</p>
          <p className={`font-mono text-2xl ${riskTone(result.risk_score)}`}>{formatPercent(result.risk_score, 2)}</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-400 sm:grid-cols-3">
        <div>Confidence: <span className="text-slate-200">{formatPercent(result.confidence)}</span></div>
        <div>Model: <span className="text-slate-200">{result.model_name}</span></div>
        <div>Ground truth: <span className={classColor(result.ground_truth_label)}>{result.ground_truth_label}</span></div>
      </div>
      {result.explanation.length > 0 && (
        <div className="mt-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500">Top influential features ({result.explanation_method})</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {result.explanation.slice(0, 4).map((item) => (
              <span key={item.feature} className="rounded-md border border-white/5 bg-white/[0.03] px-2 py-1 font-mono text-[10px] text-slate-300">
                {item.feature} · {item.impact.toFixed(3)}
              </span>
            ))}
          </div>
        </div>
      )}
      {result.note && <p className="mt-3 text-xs text-amber-300">{result.note}</p>}
      <p className="mt-3 flex items-start gap-2 text-[11px] text-slate-500">
        <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {result.warning}
      </p>
      <Link to={`/transactions/${result.transaction_id}`} className="mt-3 inline-block text-xs text-cyan-300 hover:underline">
        Open full transaction details →
      </Link>
    </div>
  )
}
