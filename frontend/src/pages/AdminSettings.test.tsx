import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import MockAdapter from 'axios-mock-adapter'
import api from '../lib/api'
import AdminSettings from './AdminSettings'

const renderAdminSettings = () =>
  render(
    <BrowserRouter>
      <AdminSettings />
    </BrowserRouter>
  )

let mock: MockAdapter

beforeEach(() => {
  mock = new MockAdapter(api)
  mock.onGet('/admin/schedules').reply(200, [])
})

afterEach(() => {
  mock.restore()
  localStorage.clear()
})

describe('AdminSettings', () => {
  it('renders the current page title and subtitle', () => {
    renderAdminSettings()

    expect(screen.getByRole('heading', { name: /^configuración$/i })).toBeInTheDocument()
    expect(screen.getByText(/sistema de gestión hospitalaria/i)).toBeInTheDocument()
  })

  it('renders the current tabs', () => {
    renderAdminSettings()

    expect(screen.getByRole('button', { name: /horarios y especialidades/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /gestión de dnis/i })).toBeInTheDocument()
  })

  it('does not render deleted texts', () => {
    renderAdminSettings()

    expect(screen.queryByText(/configuración administrativa/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /guardar cambios/i })).not.toBeInTheDocument()
    expect(screen.queryByText(/lunes/i)).not.toBeInTheDocument()
  })

  it('opens the admin authorization overlay when a password-protected action is triggered', async () => {
    const user = userEvent.setup()
    renderAdminSettings()

    expect(screen.queryByText(/autorización admin/i)).not.toBeInTheDocument()

    const nameInput = screen.getByPlaceholderText(/ej\. cardiología/i)
    await user.clear(nameInput)
    await user.type(nameInput, 'Cardiología')
    await user.click(screen.getByRole('button', { name: /crear/i }))

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /autorización admin/i })).toBeInTheDocument()
    )
    expect(screen.getByPlaceholderText(/contraseña de administrador/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument()
  })
})
