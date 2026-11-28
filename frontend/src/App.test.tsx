import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'

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

const renderApp = (path: string) => {
  window.history.pushState({}, '', path)
  return render(<App />, { wrapper: createWrapper() })
}

describe('App Routing', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('redirects / to /login when there is no session', async () => {
    renderApp('/')
    await waitFor(() => expect(window.location.pathname).toBe('/login'))
    expect(window.location.pathname).toBe('/login')
  })

  it('redirects /dashboard to /login when there is no session', async () => {
    renderApp('/dashboard')
    await waitFor(() => expect(window.location.pathname).toBe('/login'))
    // AuthGuard must not render Dashboard: assert via location, not absence of Dashboard
    expect(window.location.pathname).toBe('/login')
  })

  it('renders login page at /login without session', () => {
    renderApp('/login')

    expect(screen.getByRole('heading', { name: /iniciar sesión/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/ingrese su dni/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/ingrese su contraseña/i)).toBeInTheDocument()
  })

  it('renders AuthLayout branding on login route', () => {
    renderApp('/login')

    expect(screen.getAllByText(/hospitalpro/i).length).toBeGreaterThan(0)
  })
})

describe('Admission route', () => {
  const setSession = (role: 'patient' | 'doctor' | 'admin' | 'staff', id = 1) => {
    localStorage.setItem('access_token', 'test-token')
    localStorage.setItem(
      'user',
      JSON.stringify({ id, dni: '12345678', full_name: 'Usuario Test', role, is_active: true }),
    )
  }

  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('redirects /admission to /login when there is no session', async () => {
    renderApp('/admission')

    await waitFor(() => expect(window.location.pathname).toBe('/login'))
    expect(window.location.pathname).toBe('/login')
  })

  it('redirects /admission to / for non-patient roles (doctor)', async () => {
    setSession('doctor')
    renderApp('/admission')

    await waitFor(() => expect(window.location.pathname).toBe('/'))
    expect(window.location.pathname).toBe('/')
  })

  it('redirects /admission to / for non-patient roles (admin)', async () => {
    setSession('admin')
    renderApp('/admission')

    await waitFor(() => expect(window.location.pathname).toBe('/'))
    expect(window.location.pathname).toBe('/')
  })

  it('renders the admission form at /admission for an authenticated patient', async () => {
    setSession('patient')
    renderApp('/admission')

    await waitFor(() => expect(screen.getByText('Triaje Digital')).toBeInTheDocument())
    expect(screen.getByText('Identificación del Paciente')).toBeInTheDocument()
    expect(screen.getByLabelText(/DNI/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Teléfono de Contacto/i)).toBeInTheDocument()
  })

  it('navigates to the admission form from the patient dashboard sidebar', async () => {
    const user = userEvent.setup()
    setSession('patient')
    renderApp('/')

    await waitFor(() => expect(screen.getByText('Inicio')).toBeInTheDocument())

    await user.click(screen.getByRole('link', { name: /Admisión/i }))

    await waitFor(() => expect(window.location.pathname).toBe('/admission'))
    await waitFor(() => expect(screen.getByText('Triaje Digital')).toBeInTheDocument())
  })
})
