import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import api from '../lib/api'
import {
  submitAdmission,
  AdmissionServiceError,
  type AdmissionPayload,
} from './admissionService'

const PATIENT_ID = 42

const basePayload: AdmissionPayload = {
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
    chronicDiseases: ['Diabetes'],
    allergies: ['Penicilina'],
    currentMedications: 'Metformina 500',
    symptoms: 'Dolor abdominal leve',
    emergencyContact: '3009876543',
  },
}

describe('admissionService', () => {
  let mock: MockAdapter

  beforeEach(() => {
    mock = new MockAdapter(api)
    localStorage.clear()
    localStorage.setItem('access_token', 'test-token-123')
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'log').mockImplementation(() => {})
  })

  afterEach(() => {
    mock.restore()
    vi.restoreAllMocks()
  })

  it('envía payload válido a PATCH /patients/{id}/medical-history con cuerpo snake_case y token Bearer', async () => {
    const expectedBody = {
      medical_history: {
        phone: '3001234567',
        date_of_birth: '1990-01-01',
        emergency_contact: '3009876543',
        symptoms: 'Dolor abdominal leve',
        current_medications: 'Metformina 500',
        chronic_diseases: ['Diabetes'],
        allergies: ['Penicilina'],
        vitals: {
          temperature: 36.5,
          heart_rate: 70,
          blood_pressure_systolic: 120,
          blood_pressure_diastolic: 80,
          oxygen_saturation: 98,
          weight: 70,
        },
      },
      allergies: 'Penicilina',
    }

    mock.onPatch(`/patients/${PATIENT_ID}/medical-history`).reply((config) => {
      expect(config.headers?.Authorization).toBe('Bearer test-token-123')
      expect(JSON.parse(config.data as string)).toEqual(expectedBody)
      return [200, { ok: true, patient_id: PATIENT_ID }]
    })

    const result = await submitAdmission(PATIENT_ID, basePayload)

    expect(result.ok).toBe(true)
    expect(result.patient_id).toBe(PATIENT_ID)
  })

  it('maneja error 401 con AdmissionServiceError', async () => {
    mock.onPatch(`/patients/${PATIENT_ID}/medical-history`).reply(401, {
      detail: 'Token expirado',
    })

    await expect(submitAdmission(PATIENT_ID, basePayload)).rejects.toMatchObject({
      status: 401,
      name: 'AdmissionServiceError',
    })
  })

  it('maneja error 422 con detail del servidor', async () => {
    mock.onPatch(`/patients/${PATIENT_ID}/medical-history`).reply(422, {
      detail: 'Clave desconocida en medical_history',
    })

    try {
      await submitAdmission(PATIENT_ID, basePayload)
      expect(true).toBe(false) // no debería llegar
    } catch (error) {
      expect(error).toBeInstanceOf(AdmissionServiceError)
      expect((error as AdmissionServiceError).status).toBe(422)
      expect((error as AdmissionServiceError).detail).toBe('Clave desconocida en medical_history')
    }
  })

  it('maneja error 500 con mensaje genérico', async () => {
    mock.onPatch(`/patients/${PATIENT_ID}/medical-history`).reply(500)

    try {
      await submitAdmission(PATIENT_ID, basePayload)
      expect(true).toBe(false)
    } catch (error) {
      expect(error).toBeInstanceOf(AdmissionServiceError)
      expect((error as AdmissionServiceError).status).toBe(500)
    }
  })

  it('no escribe secretos (phone, emergency_contact) en logs', async () => {
    const errorSpy = vi.spyOn(console, 'error')
    const logSpy = vi.spyOn(console, 'log')

    mock.onPatch(`/patients/${PATIENT_ID}/medical-history`).reply(500)

    try {
      await submitAdmission(PATIENT_ID, basePayload)
    } catch {
      // esperado
    }

    const loggedText = [...errorSpy.mock.calls, ...logSpy.mock.calls]
      .map((args) => args.join(' '))
      .join(' ')

    expect(loggedText).not.toContain('3001234567')
    expect(loggedText).not.toContain('3009876543')
    expect(loggedText).not.toContain(basePayload.identification.phone)
    expect(loggedText).not.toContain(basePayload.medicalHistory.emergencyContact)
  })
})
