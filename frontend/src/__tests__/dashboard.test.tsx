import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Overview } from '../pages/Overview'
import { ModelPerformance } from '../pages/ModelPerformance'
import { TransactionDetail } from '../pages/TransactionDetail'
import { Routes, Route } from 'react-router-dom'

describe('dashboard rendering', () => {
  it('renders overview statistics and a synthetic-data notice', async () => {
    render(<MemoryRouter><Overview /></MemoryRouter>)
    expect(await screen.findByText('Total transactions')).toBeInTheDocument()
    expect(screen.getByText('360')).toBeInTheDocument()
    expect(screen.getByText('Illicit risk distribution')).toBeInTheDocument()
    expect(screen.getByText(/Synthetic demo data/i)).toBeInTheDocument()
  })

  it('renders model metrics with computed values', async () => {
    render(<MemoryRouter><ModelPerformance /></MemoryRouter>)
    expect(await screen.findByText('Model comparison')).toBeInTheDocument()
    expect(screen.getAllByText('82.0%').length).toBeGreaterThan(0)
    expect(screen.getByText('Confusion matrix')).toBeInTheDocument()
  })

  it('renders transaction details with explanation warning', async () => {
    render(
      <MemoryRouter initialEntries={['/transactions/DEMO00000001']}>
        <Routes>
          <Route path="/transactions/:id" element={<TransactionDetail />} />
        </Routes>
      </MemoryRouter>,
    )
    expect(await screen.findByText('Graph neighborhood')).toBeInTheDocument()
    expect(screen.getByText('Risk indicators')).toBeInTheDocument()
    expect(screen.getAllByText(/not proof of criminal/i).length).toBeGreaterThan(0)
  })
})
