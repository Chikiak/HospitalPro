import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdmissionForm from './AdmissionForm';
import { submitAdmission } from '../../../services/admissionService';
import type { AdmissionData } from '../schemas';

vi.mock('../../../services/admissionService', () => ({
  submitAdmission: vi.fn(),
}))

const mockSubmitAdmission = vi.mocked(submitAdmission)

const fullDraft: AdmissionData = {
  identification: {
    dni: '12345678901',
    firstName: 'Juan',
    lastName: 'Pérez',
    dateOfBirth: '1990-01-01',
    phone: '3001234567',
  },
  vitals: {
    temperature: 36.5,
    heartRate: 70,
    bloodPressureSystolic: 120,
    bloodPressureDiastolic: 80,
    oxygenSaturation: 98,
    weight: 70,
  },
  medicalHistory: {
    chronicDiseases: [],
    allergies: [],
    currentMedications: 'Metformina 500',
    symptoms: 'Dolor abdominal leve y persistente',
    emergencyContact: '3009876543',
  },
}

const setAuthenticatedUser = (patientId: number) => {
  localStorage.setItem('user', JSON.stringify({ id: patientId, role: 'patient' }))
}

const prefillDraftAndRender = async () => {
  localStorage.setItem('admission_form_draft', JSON.stringify(fullDraft))
  render(<AdmissionForm />)
  await waitFor(() => {
    expect((screen.getByLabelText(/DNI/i) as HTMLInputElement).value).toBe('12345678901')
  })
}

const goToLastStepAndSubmit = async (user: ReturnType<typeof userEvent.setup>) => {
  // Paso 1 → 2 (el borrador ya se restauró con valores válidos)
  await waitFor(() => expect(screen.getByRole('button', { name: /Siguiente/i })).not.toBeDisabled(), { timeout: 3000 })
  await user.click(screen.getByRole('button', { name: /Siguiente/i }))
  await waitFor(() => expect(screen.getByText('Signos Vitales')).toBeInTheDocument())
  await user.clear(screen.getByLabelText(/Temperatura/i))
  await user.type(screen.getByLabelText(/Temperatura/i), '36.5')
  await waitFor(() => expect(screen.getByRole('button', { name: /Siguiente/i })).not.toBeDisabled())
  await user.click(screen.getByRole('button', { name: /Siguiente/i }))
  // Paso 2 → 3 y envío
  await waitFor(() => expect(screen.getByText('Historia Médica')).toBeInTheDocument())
  await user.clear(screen.getByLabelText(/Síntomas Actuales/i))
  await user.type(screen.getByLabelText(/Síntomas Actuales/i), fullDraft.medicalHistory.symptoms)
  await waitFor(() => expect(screen.getByRole('button', { name: /Enviar/i })).not.toBeDisabled())
  await user.click(screen.getByRole('button', { name: /Enviar/i }))
}

describe('AdmissionForm', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => { });
    vi.spyOn(console, 'error').mockImplementation(() => { });
  });

  it('renders the form with initial step', () => {
    render(<AdmissionForm />);

    expect(screen.getByText('Triaje Digital')).toBeInTheDocument();
    expect(screen.getByText('Identificación del Paciente')).toBeInTheDocument();
    expect(screen.getByLabelText(/DNI/i)).toBeInTheDocument();
  });

  it('shows progress bar with correct initial state', () => {
    render(<AdmissionForm />);

    expect(screen.getByText('Paso 1 de 3')).toBeInTheDocument();
  });

  describe('Step Navigation', () => {
    it('has "Next" button disabled when identification step is invalid', async () => {
      render(<AdmissionForm />);

      const nextButton = screen.getByRole('button', { name: /Siguiente/i });

      // Initially, the button should be disabled (empty form)
      expect(nextButton).toBeDisabled();
    });

    it('enables "Next" button when identification step is valid', async () => {
      const user = userEvent.setup();
      render(<AdmissionForm />);

      const nextButton = screen.getByRole('button', { name: /Siguiente/i });

      // Fill in all required fields
      await user.type(screen.getByLabelText(/DNI/i), '12345678901');
      await user.type(screen.getByLabelText(/Nombre/i), 'Juan');
      await user.type(screen.getByLabelText(/Apellido/i), 'Pérez');
      await user.type(screen.getByLabelText(/Fecha de Nacimiento/i), '1990-01-01');
      await user.type(screen.getByLabelText(/Teléfono de Contacto/i), '1234567890');

      // Wait for validation to complete
      await waitFor(() => {
        expect(nextButton).not.toBeDisabled();
      }, { timeout: 2000 });
    });

    it('navigates to second step when "Next" is clicked', async () => {
      const user = userEvent.setup();
      render(<AdmissionForm />);

      // Fill in identification step
      await user.type(screen.getByLabelText(/DNI/i), '12345678901');
      await user.type(screen.getByLabelText(/Nombre/i), 'Juan');
      await user.type(screen.getByLabelText(/Apellido/i), 'Pérez');
      await user.type(screen.getByLabelText(/Fecha de Nacimiento/i), '1990-01-01');
      await user.type(screen.getByLabelText(/Teléfono de Contacto/i), '1234567890');

      // Wait for "Next" button to be enabled
      const nextButton = screen.getByRole('button', { name: /Siguiente/i });
      await waitFor(() => {
        expect(nextButton).not.toBeDisabled();
      });

      // Click next
      await user.click(nextButton);

      // Should now be on step 2
      await waitFor(() => {
        expect(screen.getByText('Signos Vitales')).toBeInTheDocument();
      });
      expect(screen.getByText('Paso 2 de 3')).toBeInTheDocument();
    });

    it('can navigate back to previous step', async () => {
      const user = userEvent.setup();
      render(<AdmissionForm />);

      // Navigate to step 2
      await user.type(screen.getByLabelText(/DNI/i), '12345678901');
      await user.type(screen.getByLabelText(/Nombre/i), 'Juan');
      await user.type(screen.getByLabelText(/Apellido/i), 'Pérez');
      await user.type(screen.getByLabelText(/Fecha de Nacimiento/i), '1990-01-01');
      await user.type(screen.getByLabelText(/Teléfono de Contacto/i), '1234567890');

      const nextButton = screen.getByRole('button', { name: /Siguiente/i });
      await waitFor(() => expect(nextButton).not.toBeDisabled());
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Signos Vitales')).toBeInTheDocument();
      });

      // Click previous
      const previousButton = screen.getByRole('button', { name: /Anterior/i });
      await user.click(previousButton);

      // Should be back on step 1
      await waitFor(() => {
        expect(screen.getByText('Identificación del Paciente')).toBeInTheDocument();
      });
    });
  });

  describe('LocalStorage functionality', () => {
    it('saves form data to localStorage when fields change', async () => {
      const user = userEvent.setup();
      render(<AdmissionForm />);

      // Fill in a field
      await user.type(screen.getByLabelText(/DNI/i), '12345678901');

      // Wait for auto-save
      await waitFor(() => {
        const savedData = localStorage.getItem('admission_form_draft');
        expect(savedData).toBeTruthy();

        if (savedData) {
          const parsed = JSON.parse(savedData);
          expect(parsed.identification.dni).toBe('12345678901');
        }
      }, { timeout: 1000 });
    });

    it('restores form data from localStorage on mount', async () => {
      // Pre-populate localStorage
      const mockData = {
        identification: {
          dni: '12345678901',
          firstName: 'Maria',
          lastName: 'Garcia',
          dateOfBirth: '1985-05-15',
          phone: '9876543210',
        },
        vitals: {
          temperature: 37.2,
          heartRate: 75,
          bloodPressureSystolic: 125,
          bloodPressureDiastolic: 82,
          oxygenSaturation: 97,
          weight: 65,
        },
        medicalHistory: {
          chronicDiseases: [],
          allergies: [],
          currentMedications: '',
          symptoms: '',
          emergencyContact: '',
        },
      };

      localStorage.setItem('admission_form_draft', JSON.stringify(mockData));

      // Render the form
      render(<AdmissionForm />);

      // Wait for restoration
      await waitFor(() => {
        const dniInput = screen.getByLabelText(/DNI/i) as HTMLInputElement;
        expect(dniInput.value).toBe('12345678901');
      });

      const firstNameInput = screen.getByLabelText(/Nombre/i) as HTMLInputElement;
      expect(firstNameInput.value).toBe('Maria');

      const lastNameInput = screen.getByLabelText(/Apellido/i) as HTMLInputElement;
      expect(lastNameInput.value).toBe('Garcia');
    });
  });

  describe('Envío al servicio de admisión', () => {
    beforeEach(() => {
      mockSubmitAdmission.mockReset()
      mockSubmitAdmission.mockResolvedValue({ ok: true, patient_id: 7 })
    })

    it('envía los datos al servicio con el patientId del usuario autenticado', async () => {
      setAuthenticatedUser(7)
      await prefillDraftAndRender()
      const user = userEvent.setup()

      await goToLastStepAndSubmit(user)

      await waitFor(() => expect(mockSubmitAdmission).toHaveBeenCalledTimes(1))
      expect(mockSubmitAdmission).toHaveBeenCalledWith(7, expect.objectContaining({
        identification: expect.objectContaining({
          dni: '12345678901',
          phone: '3001234567',
        }),
        vitals: expect.objectContaining({
          temperature: 36.5,
          heartRate: 70,
        }),
        medicalHistory: expect.objectContaining({
          emergencyContact: '3009876543',
          symptoms: 'Dolor abdominal leve y persistente',
          chronicDiseases: [],
          allergies: [],
        }),
      }))
    })

    it('muestra mensaje de éxito y borra el borrador de localStorage solo tras éxito 200', async () => {
      setAuthenticatedUser(7)
      await prefillDraftAndRender()
      const user = userEvent.setup()

      await goToLastStepAndSubmit(user)

      await waitFor(() => expect(screen.getByText(/admisión enviada correctamente/i)).toBeInTheDocument())
      await waitFor(() => expect(localStorage.getItem('admission_form_draft')).toBeNull())
    })

    it('muestra el error del servidor y no borra el borrador cuando falla el envío (422)', async () => {
      mockSubmitAdmission.mockRejectedValueOnce(
        new Error('El servidor rechazó los datos de admisión. Revise los campos e intente nuevamente.'),
      )
      setAuthenticatedUser(7)
      await prefillDraftAndRender()
      const user = userEvent.setup()

      await goToLastStepAndSubmit(user)

      await waitFor(() => expect(screen.getByText(/servidor rechazó los datos de admisión/i)).toBeInTheDocument())
      expect(localStorage.getItem('admission_form_draft')).not.toBeNull()
      expect(mockSubmitAdmission).toHaveBeenCalledTimes(1)
    })

    it('previene el doble submit aunque se dispare el envío dos veces seguidas', async () => {
      let resolveAdmission: ((value: unknown) => void) | undefined
      mockSubmitAdmission.mockImplementation(() => new Promise((resolve) => {
        resolveAdmission = resolve as (value: unknown) => void
      }))
      setAuthenticatedUser(7)
      await prefillDraftAndRender()
      const user = userEvent.setup()

      await goToLastStepAndSubmit(user)
      // Segundo envío inmediato mientras el primero está en curso
      await user.click(screen.getByRole('button', { name: /Enviar/i }))

      expect(mockSubmitAdmission).toHaveBeenCalledTimes(1)

      resolveAdmission!({ ok: true, patient_id: 7 })
      await waitFor(() => expect(screen.getByText(/admisión enviada correctamente/i)).toBeInTheDocument())
    })

    it('reporta error cuando no hay usuario autenticado en localStorage', async () => {
      // Sin 'user' en localStorage
      await prefillDraftAndRender()
      const user = userEvent.setup()

      await goToLastStepAndSubmit(user)

      await waitFor(() => expect(screen.getByText(/no se encontró información del usuario/i)).toBeInTheDocument())
      expect(mockSubmitAdmission).not.toHaveBeenCalled()
      expect(localStorage.getItem('admission_form_draft')).not.toBeNull()
    })
  });
});
