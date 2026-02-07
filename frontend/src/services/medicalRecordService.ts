import api from '../lib/api'

export interface MedicalRecord {
  id: number
  patient_id: number
  registration_survey: Record<string, unknown> | null
  entries: Array<{
    entry_type: string
    specialty?: string
    doctor_name?: string
    diagnosis?: string
    notes?: string
    results?: Record<string, unknown>
    timestamp: string
  }> | null
  created_at: string
  last_updated: string
}

export const getMedicalRecord = async (patientId: number): Promise<MedicalRecord> => {
  const response = await api.get(`/patients/${patientId}/medical-record`)
  return response.data
}

export const downloadMedicalRecordPdf = async (patientId: number): Promise<void> => {
  const response = await api.get(`/patients/${patientId}/medical-record/pdf`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = `historia_clinica_${patientId}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
