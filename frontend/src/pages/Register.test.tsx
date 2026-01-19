import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Register from './Register'
import { AuthProvider } from '../context/AuthContext'

// Mock the useNavigate hook
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('Register', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })

  it('renders registration form with all required fields', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    )

    expect(screen.getByLabelText(/dni/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/nombre completo/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^contraseña$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirmar contraseña/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /crear cuenta/i })).toBeInTheDocument()
  })

  it('shows error when passwords do not match', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    )

    const dniInput = screen.getByLabelText(/dni/i)
    const nameInput = screen.getByLabelText(/nombre completo/i)
    const passwordInput = screen.getByLabelText(/^contraseña$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirmar contraseña/i)

    await user.type(dniInput, '12345678901')
    await user.type(nameInput, 'Test User')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'differentpassword')

    const submitButton = screen.getByRole('button', { name: /crear cuenta/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/las contraseñas no coinciden/i)).toBeInTheDocument()
    })
  })

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    )

    const submitButton = screen.getByRole('button', { name: /crear cuenta/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/el dni debe tener exactamente 11 caracteres/i)).toBeInTheDocument()
      expect(screen.getByText(/el nombre completo debe tener al menos 3 caracteres/i)).toBeInTheDocument()
      expect(screen.getByText(/la contraseña debe tener al menos 6 caracteres/i)).toBeInTheDocument()
    })
  })

  it('validates DNI format', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    )

    const dniInput = screen.getByLabelText(/dni/i)
    await user.type(dniInput, 'abcdefghijk')

    const submitButton = screen.getByRole('button', { name: /crear cuenta/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/el dni debe contener solo números/i)).toBeInTheDocument()
    })
  })

  it('validates password length', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    )

    const passwordInput = screen.getByLabelText(/^contraseña$/i)
    await user.type(passwordInput, '12345')

    const submitButton = screen.getByRole('button', { name: /crear cuenta/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/la contraseña debe tener al menos 6 caracteres/i)).toBeInTheDocument()
    })
  })
})
