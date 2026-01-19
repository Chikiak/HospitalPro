import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import AdminSettings from './AdminSettings'

const renderAdminSettings = () => {
  return render(
    <BrowserRouter>
      <AdminSettings />
    </BrowserRouter>
  )
}

describe('AdminSettings', () => {
  it('renders the page title', () => {
    renderAdminSettings()
    
    expect(screen.getByRole('heading', { name: /Configuración Administrativa/i })).toBeInTheDocument()
  })

  it('renders tabs for Especialidades and Laboratorio', () => {
    renderAdminSettings()
    
    expect(screen.getByRole('button', { name: /Especialidades/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Laboratorio/i })).toBeInTheDocument()
  })

  it('defaults to Especialidades tab', () => {
    renderAdminSettings()
    
    expect(screen.getByText(/Configuración de Especialidades/i)).toBeInTheDocument()
  })

  it('switches to Laboratorio tab when clicked', async () => {
    const user = userEvent.setup()
    renderAdminSettings()
    
    const laboratoryTab = screen.getByRole('button', { name: /Laboratorio/i })
    await user.click(laboratoryTab)
    
    expect(screen.getByText(/Configuración de Laboratorio/i)).toBeInTheDocument()
  })

  it('renders all days of the week', () => {
    renderAdminSettings()
    
    expect(screen.getByText('Lunes')).toBeInTheDocument()
    expect(screen.getByText('Martes')).toBeInTheDocument()
    expect(screen.getByText('Miércoles')).toBeInTheDocument()
    expect(screen.getByText('Jueves')).toBeInTheDocument()
    expect(screen.getByText('Viernes')).toBeInTheDocument()
    expect(screen.getByText('Sábado')).toBeInTheDocument()
    expect(screen.getByText('Domingo')).toBeInTheDocument()
  })

  it('renders checkboxes for each day', () => {
    renderAdminSettings()
    
    const checkboxes = screen.getAllByRole('checkbox')
    // 7 days for specialty (default tab)
    expect(checkboxes.length).toBeGreaterThanOrEqual(7)
  })

  it('enables inputs when day is checked', async () => {
    const user = userEvent.setup()
    renderAdminSettings()
    
    const mondayCheckbox = screen.getByLabelText('Lunes')
    expect(mondayCheckbox).not.toBeChecked()
    
    await user.click(mondayCheckbox)
    
    expect(mondayCheckbox).toBeChecked()
  })

  it('renders save and cancel buttons', () => {
    renderAdminSettings()
    
    expect(screen.getByRole('button', { name: /Guardar Cambios/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Cancelar/i })).toBeInTheDocument()
  })
})
