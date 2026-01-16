import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
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

describe('App Routing', () => {
  it('renders login page when navigating to /login', () => {
    window.history.pushState({}, '', '/login')
    render(<App />, { wrapper: createWrapper() })
    
    // The login page should have the heading "Iniciar Sesión"
    expect(screen.getByRole('heading', { name: /iniciar sesión/i })).toBeInTheDocument()
    // Should have DNI and Password fields
    expect(screen.getByPlaceholderText(/ingrese su dni/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/ingrese su contraseña/i)).toBeInTheDocument()
  })

  it('renders dashboard page when navigating to /', () => {
    window.history.pushState({}, '', '/')
    render(<App />, { wrapper: createWrapper() })
    
    // The dashboard page should have the main heading "Dashboard"
    expect(screen.getByRole('heading', { name: /^dashboard$/i, level: 1 })).toBeInTheDocument()
    // Should show some dashboard content
    expect(screen.getByText(/vista general del sistema/i)).toBeInTheDocument()
  })

  it('renders MainLayout components on dashboard route', () => {
    window.history.pushState({}, '', '/')
    render(<App />, { wrapper: createWrapper() })
    
    // MainLayout should contain the HospitalPro branding
    expect(screen.getByRole('heading', { name: /hospitalpro/i })).toBeInTheDocument()
    // MainLayout should contain navigation items
    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument()
    // Should have the logout button
    expect(screen.getByRole('button', { name: /cerrar sesión/i })).toBeInTheDocument()
  })

  it('renders AuthLayout components on login route', () => {
    window.history.pushState({}, '', '/login')
    render(<App />, { wrapper: createWrapper() })
    
    // AuthLayout should contain the HospitalPro branding
    expect(screen.getAllByText(/hospitalpro/i).length).toBeGreaterThan(0)
    // AuthLayout should show the branding text
    expect(screen.getByText(/gestión eficiente de turnos médicos/i)).toBeInTheDocument()
  })
})
