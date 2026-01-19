import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdmissionForm from './AdmissionForm';

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
});
