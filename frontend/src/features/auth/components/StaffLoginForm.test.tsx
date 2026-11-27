import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import StaffLoginForm from './StaffLoginForm'

describe('StaffLoginForm', () => {
  it('renders DNI and password fields', () => {
    render(<StaffLoginForm />)

    expect(screen.getByLabelText(/dni/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña de personal/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión como personal/i })).toBeInTheDocument()
  })

  it('shows validation errors when submitting empty form', async () => {
    const user = userEvent.setup()
    render(<StaffLoginForm />)

    const submitButton = screen.getByRole('button', { name: /iniciar sesión como personal/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/el dni es requerido/i)).toBeInTheDocument()
      expect(screen.getByText(/la contraseña es requerida/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid DNI format', async () => {
    const user = userEvent.setup()
    render(<StaffLoginForm />)

    const dniInput = screen.getByLabelText(/dni/i)
    await user.type(dniInput, 'abc123')

    const submitButton = screen.getByRole('button', { name: /iniciar sesión como personal/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/el dni debe tener exactamente 11 dígitos/i)).toBeInTheDocument()
    })
  })

  it('accepts valid DNI with 11 digits and password', async () => {
    const handleSubmit = vi.fn()
    const user = userEvent.setup()
    render(<StaffLoginForm onSubmit={handleSubmit} />)

    const dniInput = screen.getByLabelText(/dni/i)
    const passwordInput = screen.getByLabelText(/contraseña de personal/i)

    await user.type(dniInput, '12345678901')
    await user.type(passwordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /iniciar sesión como personal/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith({
        dni: '12345678901',
        password: 'password123',
      })
    })
  })

  it('rejects DNI with more than 11 digits', async () => {
    const user = userEvent.setup()
    render(<StaffLoginForm />)

    const dniInput = screen.getByLabelText(/dni/i)
    await user.type(dniInput, '123456789012')

    const submitButton = screen.getByRole('button', { name: /iniciar sesión como personal/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/el dni debe tener exactamente 11 dígitos/i)).toBeInTheDocument()
    })
  })

  it('disables submit button when loading', async () => {
    const handleSubmit = vi.fn(async () => {
      await new Promise(resolve => setTimeout(resolve, 100))
    })
    const user = userEvent.setup()
    render(<StaffLoginForm onSubmit={handleSubmit} />)

    const dniInput = screen.getByLabelText(/dni/i)
    const passwordInput = screen.getByLabelText(/contraseña de personal/i)

    await user.type(dniInput, '12345678901')
    await user.type(passwordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /iniciar sesión como personal/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeDisabled()
    })
  })
})
