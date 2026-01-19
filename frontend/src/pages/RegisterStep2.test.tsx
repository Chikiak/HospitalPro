import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import RegisterStep2 from './RegisterStep2'

// Mock the API module
vi.mock('../lib/api', () => ({
  default: {
    patch: vi.fn(),
  },
}))

// Mock useNavigate from react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('RegisterStep2', () => {
  it('renders the medical history form', () => {
    render(
      <BrowserRouter>
        <RegisterStep2 />
      </BrowserRouter>
    )

    // Check for main heading
    expect(screen.getByText(/información médica/i)).toBeInTheDocument()

    // Check for form fields
    expect(screen.getByText(/antecedentes de enfermedades crónicas/i)).toBeInTheDocument()
    const allergyElements = screen.getAllByText(/alergias a medicamentos/i)
    expect(allergyElements.length).toBeGreaterThan(0)
    expect(screen.getByText(/otros datos de interés/i)).toBeInTheDocument()

    // Check for submit button
    expect(screen.getByRole('button', { name: /completar registro/i })).toBeInTheDocument()
  })

  it('displays step indicator', () => {
    render(
      <BrowserRouter>
        <RegisterStep2 />
      </BrowserRouter>
    )

    expect(screen.getByText(/paso 2: historial médico/i)).toBeInTheDocument()
  })

  it('has skip link', () => {
    render(
      <BrowserRouter>
        <RegisterStep2 />
      </BrowserRouter>
    )

    expect(screen.getByText(/omitir este paso por ahora/i)).toBeInTheDocument()
  })
})
