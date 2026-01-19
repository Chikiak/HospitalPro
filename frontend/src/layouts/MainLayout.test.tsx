import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import MainLayout from './MainLayout'
import * as AuthContext from '../context/AuthContext'

// Mock useAuth hook
const mockUseAuth = vi.spyOn(AuthContext, 'useAuth')

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('MainLayout', () => {
  it('renders patient navigation when user is a patient', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: '12345678',
        full_name: 'Juan Pérez',
        role: 'patient',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Patient navigation items should be visible
    expect(screen.getByRole('link', { name: /inicio/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /mis turnos/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /perfil/i })).toBeInTheDocument()

    // Staff navigation items should not be visible
    expect(screen.queryByRole('link', { name: /calendario/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /gestión de bloques/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /exportar/i })).not.toBeInTheDocument()
  })

  it('renders staff navigation when user is staff', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: null,
        full_name: 'Personal',
        role: 'staff',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Staff navigation items should be visible
    expect(screen.getByRole('link', { name: /calendario/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /gestión de bloques/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /exportar/i })).toBeInTheDocument()

    // Patient navigation items should not be visible (except those shared)
    expect(screen.queryByRole('link', { name: /mis turnos/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /perfil/i })).not.toBeInTheDocument()
  })

  it('shows search bar for patients', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: '12345678',
        full_name: 'Juan Pérez',
        role: 'patient',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Search bar should be visible for patients
    expect(screen.getByPlaceholderText(/buscar pacientes, citas/i)).toBeInTheDocument()
  })

  it('hides search bar for staff', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: null,
        full_name: 'Personal',
        role: 'staff',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Search bar should be hidden for staff
    expect(screen.queryByPlaceholderText(/buscar pacientes, citas/i)).not.toBeInTheDocument()
  })

  it('displays "Personal Administrativo" for staff users', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: null,
        full_name: 'Personal',
        role: 'staff',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Should display "Personal Administrativo" for staff
    expect(screen.getByText(/personal administrativo/i)).toBeInTheDocument()
    expect(screen.getByText(/staff/i)).toBeInTheDocument()
  })

  it('displays user name for patient users', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: '12345678',
        full_name: 'Juan Pérez',
        role: 'patient',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Should display user's full name for patients
    expect(screen.getByText(/juan pérez/i)).toBeInTheDocument()
    expect(screen.getByText(/paciente/i)).toBeInTheDocument()
  })

  it('displays PA avatar initials for staff', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: null,
        full_name: 'Personal',
        role: 'staff',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Should display "PA" for staff avatar
    expect(screen.getByText('PA')).toBeInTheDocument()
  })

  it('displays user first initial for patient avatar', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 1,
        dni: '12345678',
        full_name: 'Juan Pérez',
        role: 'patient',
        is_active: true,
      },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    renderWithRouter(<MainLayout>Test Content</MainLayout>)

    // Should display first letter of name for patient avatar
    expect(screen.getByText('J')).toBeInTheDocument()
  })
})
