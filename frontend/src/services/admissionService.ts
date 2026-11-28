import api from '../lib/api'

/**
 * Payload de admisión tal como lo emite el formulario (camelCase, zod-validado).
 * Es independiente del PR #74: este servicio solo se encarga de mapear y enviar
 * al endpoint de historial médico; no redefine las claves que #74 ya envía
 * (chronic_diseases, medication_allergies, other_information, allergies), las
 * reutiliza tal cual para no colisionar con ese contrato.
 */
export interface AdmissionVitals {
  temperature: number
  heartRate: number
  bloodPressureSystolic: number
  bloodPressureDiastolic: number
  oxygenSaturation: number
  weight: number
}

export interface AdmissionIdentification {
  dni: string
  firstName: string
  lastName: string
  dateOfBirth: string
  phone: string
}

export interface AdmissionMedicalHistory {
  chronicDiseases: string[]
  allergies: string[]
  currentMedications: string
  symptoms: string
  emergencyContact: string
}

export interface AdmissionPayload {
  identification: AdmissionIdentification
  vitals: AdmissionVitals
  medicalHistory: AdmissionMedicalHistory
}

/** Respuesta del endpoint PATCH /patients/{id}/medical-history (reutilizada). */
export interface AdmissionSubmitResponse {
  ok: boolean
  patient_id: number
  medical_history?: Record<string, unknown>
  allergies?: string
}

/** Error tipado del servicio de admisión. Nunca expone el cuerpo del request. */
export class AdmissionServiceError extends Error {
  readonly status: number
  readonly detail?: string

  constructor(status: number, message: string, detail?: string) {
    super(message)
    this.name = 'AdmissionServiceError'
    this.status = status
    this.detail = detail
  }
}

/**
 * Convierte el payload de admisión (camelCase) al cuerpo que espera el backend
 * en `PATCH /patients/{patient_id}/medical-history`:
 *  - `medical_history` dict en snake_case con las claves whitelisteadas
 *    (`phone`, `date_of_birth`, `emergency_contact`, `vitals`, `symptoms`,
 *    `current_medications`, `chronic_diseases`, `allergies`).
 *  - `allergies` a nivel superior, tal como ya lo envía el flujo #74.
 *
 * Los campos sensibles (`phone`, `emergency_contact`) viajan solo en el cuerpo
 * de la petición HTTPS; este servicio nunca los escribe en logs.
 */
const mapToBackendBody = (payload: AdmissionPayload) => {
  const { identification, vitals, medicalHistory } = payload
  return {
    medical_history: {
      phone: identification.phone,
      date_of_birth: identification.dateOfBirth,
      emergency_contact: medicalHistory.emergencyContact,
      symptoms: medicalHistory.symptoms,
      current_medications: medicalHistory.currentMedications,
      chronic_diseases: medicalHistory.chronicDiseases,
      allergies: medicalHistory.allergies,
      vitals: {
        temperature: vitals.temperature,
        heart_rate: vitals.heartRate,
        blood_pressure_systolic: vitals.bloodPressureSystolic,
        blood_pressure_diastolic: vitals.bloodPressureDiastolic,
        oxygen_saturation: vitals.oxygenSaturation,
        weight: vitals.weight,
      },
    },
    allergies: medicalHistory.allergies.join(', '),
  }
}

/**
 * Envía una admisión al backend.
 *
 * @param patientId - id del paciente autenticado (sobre su propio id)
 * @param payload - datos de admisión validados por el formulario
 * @returns la respuesta parseada del endpoint
 * @throws {AdmissionServiceError} con status 401/422/500 (u otro) y detail cuando aplica
 */
export const submitAdmission = async (
  patientId: number,
  payload: AdmissionPayload,
): Promise<AdmissionSubmitResponse> => {
  const body = mapToBackendBody(payload)

  try {
    const response = await api.patch(`/patients/${patientId}/medical-history`, body)
    return {
      ok: true,
      patient_id: patientId,
      ...(response.data as Record<string, unknown>),
    }
  } catch (error) {
    const status = (error as { response?: { status?: number } })?.response?.status
    const detail =
      (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail

    // 401 ya es gestionado por el interceptor de api (limpia sesión y redirige),
    // pero lo tipamos igual para que el llamante pueda mostrar UI coherente.
    if (status === 401) {
      throw new AdmissionServiceError(401, 'Sesión expirada. Inicie sesión nuevamente.', detail)
    }
    if (status === 422) {
      throw new AdmissionServiceError(
        422,
        'El servidor rechazó los datos de admisión. Revise los campos e intente nuevamente.',
        detail,
      )
    }
    if (status === 500) {
      throw new AdmissionServiceError(
        500,
        'Error interno del servidor al guardar la admisión. Intente nuevamente más tarde.',
        detail,
      )
    }
    throw new AdmissionServiceError(
      status ?? 0,
      'No se pudo enviar la admisión. Verifique su conexión e intente nuevamente.',
      detail,
    )
  }
}
