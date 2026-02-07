import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Profile from './Profile'
import { AuthProvider } from '../context/AuthContext'
import * as medicalRecordService from '../services/medicalRecordService'

// Mock the medical record service
vi.mock('../services/medicalRecordService', () => ({
  getMedicalRecord: vi.fn(),
  downloadMedicalRecordPdf: vi.fn(),
}))

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
})

// Create a test query client
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

describe('Profile', () => {
  const mockUser = {
    id: 1,
    dni: '12345678901',
    full_name: 'Juan Pérez',
    role: 'patient' as const,
    is_active: true,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Set up mock user in localStorage
    mockLocalStorage.getItem.mockImplementation((key: string) => {
      if (key === 'user') return JSON.stringify(mockUser)
      if (key === 'access_token') return 'mock-token'
      return null
    })
  })

  it('renders profile page with user information', async () => {
    vi.mocked(medicalRecordService.getMedicalRecord).mockResolvedValue({
      id: 1,
      patient_id: 1,
      registration_survey: {
        chronic_diseases: 'Diabetes',
        medication_allergies: ['Penicilina'],
        other_information: 'Ninguna',
      },
      entries: [],
      created_at: '2024-01-01T00:00:00Z',
      last_updated: '2024-01-01T00:00:00Z',
    })

    const queryClient = createTestQueryClient()

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Profile />
          </AuthProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )

    // Check for profile header
    expect(screen.getByText(/Mi/)).toBeInTheDocument()
    expect(screen.getByText(/Perfil/)).toBeInTheDocument()

    // Check for personal information
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('12345678901')).toBeInTheDocument()
    expect(screen.getByText('Paciente')).toBeInTheDocument()

    // Wait for medical record to load
    await waitFor(() => {
      expect(screen.getByText(/Diabetes/)).toBeInTheDocument()
    })
  })

  it('shows message when no medical record is available', async () => {
    vi.mocked(medicalRecordService.getMedicalRecord).mockRejectedValue(
      new Error('Not found')
    )

    const queryClient = createTestQueryClient()

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Profile />
          </AuthProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/No hay historia clínica disponible/)).toBeInTheDocument()
    })
  })

  it('has download PDF button', async () => {
    vi.mocked(medicalRecordService.getMedicalRecord).mockResolvedValue({
      id: 1,
      patient_id: 1,
      registration_survey: null,
      entries: null,
      created_at: '2024-01-01T00:00:00Z',
      last_updated: '2024-01-01T00:00:00Z',
    })

    const queryClient = createTestQueryClient()

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Profile />
          </AuthProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )

    await waitFor(() => {
      const downloadButton = screen.getByText(/Descargar PDF/)
      expect(downloadButton).toBeInTheDocument()
    })
  })

  it('calls download PDF function when button is clicked', async () => {
    const mockDownload = vi.fn().mockResolvedValue(undefined)
    vi.mocked(medicalRecordService.downloadMedicalRecordPdf).mockImplementation(mockDownload)
    
    vi.mocked(medicalRecordService.getMedicalRecord).mockResolvedValue({
      id: 1,
      patient_id: 1,
      registration_survey: null,
      entries: null,
      created_at: '2024-01-01T00:00:00Z',
      last_updated: '2024-01-01T00:00:00Z',
    })

    const queryClient = createTestQueryClient()
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Profile />
          </AuthProvider>
        </QueryClientProvider>
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Descargar PDF/)).toBeInTheDocument()
    })

    const downloadButton = screen.getByText(/Descargar PDF/)
    await user.click(downloadButton)

    await waitFor(() => {
      expect(mockDownload).toHaveBeenCalledWith(1)
    })
  })
})
