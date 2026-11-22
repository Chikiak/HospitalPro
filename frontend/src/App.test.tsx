import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
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
