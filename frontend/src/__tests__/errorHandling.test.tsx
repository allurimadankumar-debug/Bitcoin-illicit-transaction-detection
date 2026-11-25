import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { api, ApiError } from '../services/api'
import { Overview } from '../pages/Overview'

describe('error handling', () => {
  beforeEach(() => {
    vi.mocked(fetch).mockImplementation(async () =>
      new Response(JSON.stringify({ error: 'HTTPException', detail: 'Transaction not found', status_code: 404 }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
  })

  it('turns API error responses into typed ApiError instances', async () => {
    await expect(api.transaction('DEMO99999999')).rejects.toBeInstanceOf(ApiError)
    await expect(api.transaction('DEMO99999999')).rejects.toMatchObject({ status: 404 })
  })

  it('surfaces backend failures in the UI instead of crashing', async () => {
    vi.mocked(fetch).mockImplementation(async (input) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname === '/api/dashboard/summary') {
        return new Response(JSON.stringify({ detail: 'Backend offline' }), { status: 503 })
      }
      return new Response(JSON.stringify({}), { status: 200 })
    })
    render(<MemoryRouter><Overview /></MemoryRouter>)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Try again')).toBeInTheDocument()
  })
})
