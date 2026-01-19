import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { RoleGuard } from './RoleGuard'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext')

describe('RoleGuard', () => {
  it('redirects to /login when user is not authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: false,
      user: null,
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <RoleGuard allowedRoles={['patient']}>
          <div>Protected Content</div>
        </RoleGuard>
      </BrowserRouter>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when user has allowed role', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: {
        id: 1,
        dni: '12345678',
        full_name: 'Test Patient',
        role: 'patient',
        is_active: true,
      },
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <RoleGuard allowedRoles={['patient']}>
          <div>Protected Content</div>
        </RoleGuard>
      </BrowserRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('redirects to / when user does not have allowed role', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: {
        id: 1,
        dni: null,
        full_name: 'Test Staff',
        role: 'staff',
        is_active: true,
      },
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <RoleGuard allowedRoles={['patient']}>
          <div>Protected Content</div>
        </RoleGuard>
      </BrowserRouter>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when user role is in allowed roles list', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: {
        id: 1,
        dni: null,
        full_name: 'Test Admin',
        role: 'admin',
        is_active: true,
      },
      isLoading: false,
      login: vi.fn(),
      staffLogin: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <BrowserRouter>
        <RoleGuard allowedRoles={['admin', 'staff']}>
          <div>Protected Content</div>
        </RoleGuard>
      </BrowserRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})
