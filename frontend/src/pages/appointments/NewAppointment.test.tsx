import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import MockAdapter from 'axios-mock-adapter'
import api from '../../lib/api'
import NewAppointment from './NewAppointment'

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

let mock: MockAdapter

beforeEach(() => {
  mock = new MockAdapter(api)
  mock.onGet('/appointments/categories').reply(200, [
    { id: 1, name: 'Cardiología', category_type: 'specialty' },
    { id: 2, name: 'Laboratorio Clínico', category_type: 'laboratory' },
  ])
  mock.onGet('/appointments/slots').reply(200, [
    {
      slot_datetime: '2026-11-21T10:30:00',
      category_name: 'Cardiología',
      category_id: 1,
    },
  ])
  mock.onPost('/appointments/book').reply(200, { success: true })
})

afterEach(() => {
  mock.restore()
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('NewAppointment', () => {
  it('renders step 1: servicio selection', async () => {
    render(<NewAppointment />, { wrapper: createWrapper() })

    expect(screen.getByRole('heading', { name: /agenda tu turno/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /seleccione el servicio/i })).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /cardiología/i })).toBeInTheDocument()
    )
  })

  it('completes the flow: servicio → turnos disponibles → verificar datos → confirmar', async () => {
    const user = userEvent.setup()
    const alertSpy = vi.spyOn(window, 'alert')

    render(<NewAppointment />, { wrapper: createWrapper() })

    expect(screen.getByRole('heading', { name: /agenda tu turno/i })).toBeInTheDocument()

    // Paso 1: seleccionar servicio
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /cardiología/i })).toBeInTheDocument()
    )
    await user.click(screen.getByRole('button', { name: /cardiología/i }))

    // Paso 2: turnos disponibles y seleccionar turno
    await waitFor(() => expect(screen.getByText(/turnos disponibles/i)).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /10:30/ })).toBeInTheDocument()
    )
    await user.click(screen.getByRole('button', { name: /10:30/ }))

    // Paso 3: verificar datos
    await waitFor(() => expect(screen.getByText(/verifica los datos/i)).toBeInTheDocument())
    await waitFor(() => expect(screen.getByText(/cardiología/i)).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /confirmar y finalizar/i })).toBeInTheDocument()

    // Confirmar
    await user.click(screen.getByRole('button', { name: /confirmar y finalizar/i }))
    await waitFor(() =>
      expect(alertSpy).toHaveBeenCalledWith('¡Turno reservado exitosamente!')
    )
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /cardiología/i })).toBeInTheDocument()
    )
  })
})
