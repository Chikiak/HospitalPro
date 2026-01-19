import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Login from './Login'
import { AuthProvider } from '../context/AuthContext'

// Mock the navigate function
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Login Dual Mode', () => {
  it('renders with two tabs (Paciente and Personal)', () => {
    renderLogin()
    
    expect(screen.getByRole('button', { name: /paciente/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /personal/i })).toBeInTheDocument()
  })

  it('defaults to Patient tab', () => {
    renderLogin()
    
    // Should show DNI field by default (patient mode)
    expect(screen.getByLabelText(/dni/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
  })

  it('switches to Staff mode when clicking Personal tab', async () => {
    const user = userEvent.setup()
    renderLogin()
    
    // Click on Personal tab
    const staffTab = screen.getByRole('button', { name: /personal/i })
    await user.click(staffTab)
    
    // Should show only password field (staff mode)
    await waitFor(() => {
      expect(screen.queryByLabelText(/^dni$/i)).not.toBeInTheDocument()
      expect(screen.getByLabelText(/contraseña de personal/i)).toBeInTheDocument()
    })
  })

  it('switches back to Patient mode when clicking Paciente tab', async () => {
    const user = userEvent.setup()
    renderLogin()
    
    // First switch to Staff
    const staffTab = screen.getByRole('button', { name: /personal/i })
    await user.click(staffTab)
    
    await waitFor(() => {
      expect(screen.queryByLabelText(/^dni$/i)).not.toBeInTheDocument()
    })
    
    // Then switch back to Patient
    const patientTab = screen.getByRole('button', { name: /paciente/i })
    await user.click(patientTab)
    
    // Should show DNI field again
    await waitFor(() => {
      expect(screen.getByLabelText(/dni/i)).toBeInTheDocument()
    })
  })

  it('shows registration link only in Patient mode', async () => {
    const user = userEvent.setup()
    renderLogin()
    
    // Should show registration link in patient mode
    expect(screen.getByText(/registrarse ahora/i)).toBeInTheDocument()
    
    // Switch to Staff mode
    const staffTab = screen.getByRole('button', { name: /personal/i })
    await user.click(staffTab)
    
    // Registration link should not be visible in staff mode
    await waitFor(() => {
      expect(screen.queryByText(/registrarse ahora/i)).not.toBeInTheDocument()
    })
  })

  it('clears error when switching tabs', async () => {
    const user = userEvent.setup()
    renderLogin()
    
    // Submit patient form with invalid data to trigger error
    const submitButton = screen.getByRole('button', { name: /^iniciar sesión$/i })
    await user.click(submitButton)
    
    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/el dni es requerido/i)).toBeInTheDocument()
    })
    
    // Switch to Staff tab
    const staffTab = screen.getByRole('button', { name: /personal/i })
    await user.click(staffTab)
    
    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText(/el dni es requerido/i)).not.toBeInTheDocument()
    })
  })

  it('renders with glassmorphism styling', () => {
    renderLogin()
    
    // Check for glass effect class on tabs container
    const glassElements = document.querySelectorAll('.glass')
    expect(glassElements.length).toBeGreaterThan(0)
  })

  it('shows Patient submit button text in Patient mode', () => {
    renderLogin()
    
    // Check for patient-specific submit button
    expect(screen.getByRole('button', { name: /^iniciar sesión$/i })).toBeInTheDocument()
  })

  it('shows Staff submit button text in Staff mode', async () => {
    const user = userEvent.setup()
    renderLogin()
    
    // Switch to Staff mode
    const staffTab = screen.getByRole('button', { name: /personal/i })
    await user.click(staffTab)
    
    // Check for staff-specific submit button
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /iniciar sesión como personal/i })).toBeInTheDocument()
    })
  })
})
