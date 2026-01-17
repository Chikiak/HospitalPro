import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import NewAppointment from './NewAppointment'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(() => Promise.reject(new Error('API not available'))),
    post: vi.fn(() => Promise.resolve({ data: { success: true } })),
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('NewAppointment', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the first step (specialty selection) by default', () => {
    render(<NewAppointment />, { wrapper: createWrapper() })

    expect(screen.getByText('Nuevo Turno')).toBeInTheDocument()
    expect(screen.getByText('Seleccione una Especialidad')).toBeInTheDocument()
    expect(screen.getByText('Cardiología')).toBeInTheDocument()
    expect(screen.getByText('Traumatología')).toBeInTheDocument()
    expect(screen.getByText('Pediatría')).toBeInTheDocument()
  })

  it('shows progress indicator with step 1 active', () => {
    render(<NewAppointment />, { wrapper: createWrapper() })

    const step1Text = screen.getByText('Especialidad')
    const step1Container = step1Text.closest('div')
    expect(step1Container).toHaveClass('text-teal-700')
  })

  it('moves to step 2 when a specialty is selected', async () => {
    const user = userEvent.setup()
    render(<NewAppointment />, { wrapper: createWrapper() })

    const cardiologyButton = screen.getByText('Cardiología')
    await user.click(cardiologyButton)

    await waitFor(() => {
      expect(screen.getByText(/Turnos Disponibles - Cardiología/i)).toBeInTheDocument()
    })
  })

  it('displays mock turns in step 2', async () => {
    const user = userEvent.setup()
    render(<NewAppointment />, { wrapper: createWrapper() })

    const cardiologyButton = screen.getByText('Cardiología')
    await user.click(cardiologyButton)

    await waitFor(() => {
      expect(screen.getByText(/Dr\. García/i)).toBeInTheDocument()
      expect(screen.getByText(/Dra\. Rodríguez/i)).toBeInTheDocument()
      expect(screen.getByText(/Dr\. López/i)).toBeInTheDocument()
    })
  })

  it('allows navigation back to step 1 from step 2', async () => {
    const user = userEvent.setup()
    render(<NewAppointment />, { wrapper: createWrapper() })

    // Go to step 2
    const cardiologyButton = screen.getByText('Cardiología')
    await user.click(cardiologyButton)

    await waitFor(() => {
      expect(screen.getByText(/Turnos Disponibles/i)).toBeInTheDocument()
    })

    // Click back button
    const backButtons = screen.getAllByRole('button', { name: /volver/i })
    await user.click(backButtons[0])

    expect(screen.getByText('Seleccione una Especialidad')).toBeInTheDocument()
  })

  it('moves to step 3 when a turn is selected', async () => {
    const user = userEvent.setup()
    render(<NewAppointment />, { wrapper: createWrapper() })

    // Go to step 2
    const cardiologyButton = screen.getByText('Cardiología')
    await user.click(cardiologyButton)

    await waitFor(() => {
      expect(screen.getByText(/Dr\. García/i)).toBeInTheDocument()
    })

    // Select a turn
    const turns = screen.getAllByRole('button')
    const firstTurn = turns.find((btn) => btn.textContent?.includes('Dr. García'))
    if (firstTurn) {
      await user.click(firstTurn)
    }

    await waitFor(() => {
      expect(screen.getByText('Confirmar Reserva')).toBeInTheDocument()
    })
  })

  it('displays selected appointment details in step 3', async () => {
    const user = userEvent.setup()
    render(<NewAppointment />, { wrapper: createWrapper() })

    // Go to step 2
    const cardiologyButton = screen.getByText('Cardiología')
    await user.click(cardiologyButton)

    await waitFor(() => {
      expect(screen.getByText(/Dr\. García/i)).toBeInTheDocument()
    })

    // Select a turn
    const turns = screen.getAllByRole('button')
    const firstTurn = turns.find((btn) => btn.textContent?.includes('Dr. García'))
    if (firstTurn) {
      await user.click(firstTurn)
    }

    await waitFor(() => {
      expect(screen.getByText('Confirmar Reserva')).toBeInTheDocument()
      expect(screen.getAllByText('Cardiología').length).toBeGreaterThan(0)
    })
  })

  it('shows confirm button in step 3', async () => {
    const user = userEvent.setup()
    render(<NewAppointment />, { wrapper: createWrapper() })

    // Navigate to step 3
    const cardiologyButton = screen.getByText('Cardiología')
    await user.click(cardiologyButton)

    await waitFor(() => {
      expect(screen.getByText(/Dr\. García/i)).toBeInTheDocument()
    })

    const turns = screen.getAllByRole('button')
    const firstTurn = turns.find((btn) => btn.textContent?.includes('Dr. García'))
    if (firstTurn) {
      await user.click(firstTurn)
    }

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /confirmar turno/i })).toBeInTheDocument()
    })
  })
})
