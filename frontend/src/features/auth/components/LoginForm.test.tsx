import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginForm from './LoginForm'

describe('LoginForm', () => {
  it('renders form fields correctly', () => {
    render(<LoginForm />)
    
    expect(screen.getByLabelText(/dni/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('shows validation errors when submitting empty form', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)
    
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/el dni es requerido/i)).toBeInTheDocument()
      expect(screen.getByText(/la contraseña es requerida/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid DNI format', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)
    
    const dniInput = screen.getByLabelText(/dni/i)
    await user.type(dniInput, 'abc123')
    
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/el dni debe ser numérico y tener 7-8 dígitos/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for DNI with less than 7 digits', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)
    
    const dniInput = screen.getByLabelText(/dni/i)
    await user.type(dniInput, '123456')
    
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/el dni debe ser numérico y tener 7-8 dígitos/i)).toBeInTheDocument()
    })
  })

  it('accepts valid DNI with 7 digits', async () => {
    const handleSubmit = vi.fn()
    const user = userEvent.setup()
    render(<LoginForm onSubmit={handleSubmit} />)
    
    const dniInput = screen.getByLabelText(/dni/i)
    const passwordInput = screen.getByLabelText(/contraseña/i)
    
    await user.type(dniInput, '1234567')
    await user.type(passwordInput, 'password123')
    
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith({
        dni: '1234567',
        password: 'password123',
      })
    })
  })

  it('accepts valid DNI with 8 digits', async () => {
    const handleSubmit = vi.fn()
    const user = userEvent.setup()
    render(<LoginForm onSubmit={handleSubmit} />)
    
    const dniInput = screen.getByLabelText(/dni/i)
    const passwordInput = screen.getByLabelText(/contraseña/i)
    
    await user.type(dniInput, '12345678')
    await user.type(passwordInput, 'password123')
    
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith({
        dni: '12345678',
        password: 'password123',
      })
    })
  })

  it('shows loading state when submitting', async () => {
    const handleSubmit = vi.fn(async () => {
      await new Promise(resolve => setTimeout(resolve, 100))
    })
    const user = userEvent.setup()
    render(<LoginForm onSubmit={handleSubmit} />)
    
    const dniInput = screen.getByLabelText(/dni/i)
    const passwordInput = screen.getByLabelText(/contraseña/i)
    
    await user.type(dniInput, '12345678')
    await user.type(passwordInput, 'password123')
    
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitButton)
    
    // Check for loading state
    await waitFor(() => {
      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })
  })

  it('disables submit button when loading', async () => {
    const handleSubmit = vi.fn(async () => {
      await new Promise(resolve => setTimeout(resolve, 100))
    })
    const user = userEvent.setup()
    render(<LoginForm onSubmit={handleSubmit} />)
    
    const dniInput = screen.getByLabelText(/dni/i)
    const passwordInput = screen.getByLabelText(/contraseña/i)
    
    await user.type(dniInput, '12345678')
    await user.type(passwordInput, 'password123')
    
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeDisabled()
    })
  })
})
