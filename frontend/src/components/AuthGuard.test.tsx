import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthGuard } from './AuthGuard'
import { useAuth } from '../context/AuthContext'

vi.mock('../context/AuthContext')

describe('AuthGuard', () => {
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
        <AuthGuard>
          <div>Protected Content</div>
        </AuthGuard>
      </BrowserRouter>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when user is authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: {
        id: 1,
        dni: '12345678',
        full_name: 'Test User',
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
        <AuthGuard>
          <div>Protected Content</div>
        </AuthGuard>
      </BrowserRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})
