import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

describe('application navigation', () => {
  it('renders all primary navigation items', async () => {
    render(<MemoryRouter><App /></MemoryRouter>)
    expect(await screen.findByRole('link', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Transaction Detection' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Transaction Explorer' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Graph Analytics' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'ML Model Performance' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Temporal Analytics' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Privacy & Web3' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument()
  })

  it('navigates to the detection page', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter><App /></MemoryRouter>)
    await user.click(await screen.findByRole('link', { name: 'Transaction Detection' }))
    expect(await screen.findByText('Single transaction analysis')).toBeInTheDocument()
    expect(screen.getByText('Batch CSV analysis')).toBeInTheDocument()
  })

  it('shows a not-found page for unknown routes', async () => {
    render(<MemoryRouter initialEntries={['/does-not-exist']}><App /></MemoryRouter>)
    expect(await screen.findByText('404')).toBeInTheDocument()
    expect(screen.getByText('Return to overview')).toBeInTheDocument()
  })
})
