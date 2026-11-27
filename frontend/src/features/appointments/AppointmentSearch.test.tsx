import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AppointmentSearch from './AppointmentSearch'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(() => Promise.reject(new Error('API not available'))),
    create: vi.fn(() => ({
      get: vi.fn(() => Promise.reject(new Error('API not available'))),
      interceptors: {
        request: { use: vi.fn(), eject: vi.fn() },
        response: { use: vi.fn(), eject: vi.fn() },
      },
    })),
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

// waitFor con timeout extendido para evitar fallos espúreos por timing
// bajo carga de CPU al ejecutar el suite completo en paralelo.
const longWaitFor = (cb: Parameters<typeof waitFor>[0]) => waitFor(cb, { timeout: 5000 })

describe('AppointmentSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the search component', () => {
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    expect(screen.getByText('Buscar')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)).toBeInTheDocument()
  })

  it('shows empty state when no search query', () => {
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    expect(screen.getByText(/comience su búsqueda/i)).toBeInTheDocument()
  })

  it('displays suggestions when typing in search field', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Cardio')

    await longWaitFor(() => {
      expect(screen.getByText('Cardiología')).toBeInTheDocument()
    })
  })

  it('filters categories based on search query', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Trauma')

    await longWaitFor(() => {
      expect(screen.getByText('Traumatología')).toBeInTheDocument()
      expect(screen.queryByText('Cardiología')).not.toBeInTheDocument()
    })
  })

  it('selects category when clicking on suggestion', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Cardio')

    await longWaitFor(() => {
      expect(screen.getByText('Cardiología')).toBeInTheDocument()
    })

    const suggestion = screen.getByRole('button', { name: /Cardiología/i })
    act(() => {
      fireEvent.click(suggestion)
    })

    await longWaitFor(() => {
      expect(screen.getByRole('heading', { name: /turnos disponibles/i })).toBeInTheDocument()
    })
  })

  it('shows loading state when fetching slots', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Cardio')

    await longWaitFor(() => {
      expect(screen.getByText('Cardiología')).toBeInTheDocument()
    })

    const suggestion = screen.getByRole('button', { name: /Cardiología/i })
    act(() => {
      fireEvent.click(suggestion)
    })

    // Should show loading state (appears asynchronously after click)
    await longWaitFor(() => {
      expect(screen.getByText(/buscando disponibilidad/i)).toBeInTheDocument()
    })
  })

  it('displays only 3 available slots maximum', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Cardio')

    await longWaitFor(() => {
      expect(screen.getByText('Cardiología')).toBeInTheDocument()
    })

    const suggestion = screen.getByRole('button', { name: /Cardiología/i })
    act(() => {
      fireEvent.click(suggestion)
    })

    await longWaitFor(() => {
      const slots = screen.getAllByText(/turno disponible/i)
      expect(slots.length).toBeLessThanOrEqual(3)
    })
  })

  it('shows category type label in suggestions', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Clínicos')

    await longWaitFor(() => {
      expect(screen.getByText('Laboratorio')).toBeInTheDocument()
    })
  })

  it('hides suggestions when category is selected', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Cardio')

    await longWaitFor(() => {
      expect(screen.getByText('Cardiología')).toBeInTheDocument()
    })

    const suggestion = screen.getByRole('button', { name: /Cardiología/i })
    act(() => {
      fireEvent.click(suggestion)
    })

    await longWaitFor(() => {
      // Suggestion dropdown should be hidden
      const allCardiologyElements = screen.getAllByText('Cardiología')
      // One in the search input value, one in the "Turnos Disponibles" section
      expect(allCardiologyElements.length).toBe(1)
    })
  })

  it('shows slots as clickable cards', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Cardio')

    await longWaitFor(() => {
      expect(screen.getByText('Cardiología')).toBeInTheDocument()
    })

    const suggestion = screen.getByRole('button', { name: /Cardiología/i })
    act(() => {
      fireEvent.click(suggestion)
    })

    await longWaitFor(() => {
      const slots = screen.getAllByText(/turno disponible/i)
      expect(slots.length).toBeGreaterThan(0)
    })
  })

  it('clears selected category when search is cleared', async () => {
    const user = userEvent.setup()
    render(<AppointmentSearch />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText(/buscar especialidad o laboratorio/i)
    await user.type(searchInput, 'Cardio')

    await longWaitFor(() => {
      expect(screen.getByText('Cardiología')).toBeInTheDocument()
    })

    const suggestion = screen.getByRole('button', { name: /Cardiología/i })
    act(() => {
      fireEvent.click(suggestion)
    })

    await longWaitFor(() => {
      expect(screen.getByRole('heading', { name: /turnos disponibles/i })).toBeInTheDocument()
    })

    // Clear the search
    await user.clear(searchInput)

    await longWaitFor(() => {
      expect(screen.queryByRole('heading', { name: /turnos disponibles/i })).not.toBeInTheDocument()
    })
  })
})
