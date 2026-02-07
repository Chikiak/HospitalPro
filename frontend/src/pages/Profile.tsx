import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { User, FileText, Download, Calendar, HeartPulse, Pill, AlertCircle, Stethoscope, ClipboardList } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { getMedicalRecord, downloadMedicalRecordPdf } from '../services/medicalRecordService'
import Button from '../components/ui/Button'

export default function Profile() {
  const { user } = useAuth()
  const [isDownloading, setIsDownloading] = useState(false)

  // Fetch medical record
  const { data: medicalRecord, isLoading, error } = useQuery({
    queryKey: ['medicalRecord', user?.id],
    queryFn: () => {
      if (!user?.id) throw new Error('User ID not found')
      return getMedicalRecord(user.id)
    },
    enabled: !!user?.id,
  })

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('es-AR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  const handleDownloadPdf = async () => {
    if (!user?.id) return
    
    try {
      setIsDownloading(true)
      await downloadMedicalRecordPdf(user.id)
    } catch (err) {
      console.error('Error downloading PDF:', err)
      alert('Error al descargar el PDF. Por favor, intente nuevamente.')
    } finally {
      setIsDownloading(false)
    }
  }

  const getEntryTypeLabel = (type: string) => {
    switch (type) {
      case 'consultation':
        return 'Consulta'
      case 'laboratory':
        return 'Laboratorio'
      default:
        return type
    }
  }

  return (
    <div className="space-y-10 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <h1 className="text-4xl font-black tracking-tight text-slate-900">
            Mi <span className="text-primary">Perfil</span>
          </h1>
          <p className="text-slate-500 font-medium">Información personal y historia clínica</p>
        </div>
      </div>

      {/* Personal Information Section */}
      <div className="premium-card !p-0 overflow-hidden border-none shadow-xl bg-white">
        <div className="p-8 border-b border-slate-50 flex items-center gap-3 bg-slate-50/50">
          <User className="h-6 w-6 text-primary" />
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">Información Personal</h2>
            <p className="text-sm font-medium text-slate-500">Datos del paciente</p>
          </div>
        </div>
        <div className="p-8 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center gap-2">
            <span className="text-sm font-bold text-slate-500 uppercase tracking-widest md:w-48">Nombre Completo:</span>
            <span className="text-slate-900 font-medium">{user?.full_name || 'N/A'}</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center gap-2">
            <span className="text-sm font-bold text-slate-500 uppercase tracking-widest md:w-48">DNI:</span>
            <span className="text-slate-900 font-medium">{user?.dni || 'N/A'}</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-center gap-2">
            <span className="text-sm font-bold text-slate-500 uppercase tracking-widest md:w-48">Rol:</span>
            <span className="text-slate-900 font-medium">Paciente</span>
          </div>
        </div>
      </div>

      {/* Medical Record Section */}
      <div className="premium-card !p-0 overflow-hidden border-none shadow-xl bg-white">
        <div className="p-8 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-3">
            <FileText className="h-6 w-6 text-primary" />
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight">Historia Clínica</h2>
              <p className="text-sm font-medium text-slate-500">Registro médico completo</p>
            </div>
          </div>
          <Button
            onClick={handleDownloadPdf}
            isLoading={isDownloading}
            variant="outline"
            className="flex items-center gap-2"
            disabled={!medicalRecord || isLoading}
          >
            <Download className="h-4 w-4" />
            Descargar PDF
          </Button>
        </div>

        <div className="p-8">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
              <p className="text-slate-400 font-medium animate-pulse">Cargando historia clínica...</p>
            </div>
          ) : error || !medicalRecord ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <AlertCircle className="h-16 w-16 text-slate-300" />
              <p className="text-slate-500 font-medium">No hay historia clínica disponible</p>
              <p className="text-sm text-slate-400">
                Complete su registro médico para ver su historia clínica
              </p>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Last Updated */}
              {medicalRecord.last_updated && (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Calendar className="h-4 w-4" />
                  <span>Última actualización: {formatDate(medicalRecord.last_updated)}</span>
                </div>
              )}

              {/* Registration Survey */}
              {medicalRecord.registration_survey && (
                <div className="space-y-4">
                  <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                    <HeartPulse className="h-5 w-5 text-primary" />
                    Datos de Registro
                  </h3>
                  <div className="space-y-4 bg-slate-50/50 rounded-xl p-6">
                    {typeof medicalRecord.registration_survey.chronic_diseases === 'string' && medicalRecord.registration_survey.chronic_diseases && (
                      <div className="space-y-2">
                        <span className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                          <HeartPulse className="h-4 w-4" />
                          Enfermedades Crónicas:
                        </span>
                        <p className="text-slate-700 ml-6">
                          {String(medicalRecord.registration_survey.chronic_diseases) || 'No registrado'}
                        </p>
                      </div>
                    )}

                    {(typeof medicalRecord.registration_survey.medication_allergies === 'string' || Array.isArray(medicalRecord.registration_survey.medication_allergies)) && medicalRecord.registration_survey.medication_allergies && (
                      <div className="space-y-2">
                        <span className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                          <Pill className="h-4 w-4" />
                          Alergias a Medicamentos:
                        </span>
                        <div className="ml-6">
                          {Array.isArray(medicalRecord.registration_survey.medication_allergies) ? (
                            medicalRecord.registration_survey.medication_allergies.length > 0 ? (
                              <div className="flex flex-wrap gap-2">
                                {medicalRecord.registration_survey.medication_allergies.map((allergy, index) => (
                                  <span
                                    key={index}
                                    className="px-3 py-1 bg-teal-100 text-teal-700 text-sm rounded-lg font-medium"
                                  >
                                    {String(allergy)}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <p className="text-slate-700">No registrado</p>
                            )
                          ) : (
                            <p className="text-slate-700">
                              {String(medicalRecord.registration_survey.medication_allergies)}
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {typeof medicalRecord.registration_survey.other_information === 'string' && medicalRecord.registration_survey.other_information && (
                      <div className="space-y-2">
                        <span className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                          <ClipboardList className="h-4 w-4" />
                          Otros Datos de Interés:
                        </span>
                        <p className="text-slate-700 ml-6">
                          {String(medicalRecord.registration_survey.other_information) || 'No registrado'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Medical Entries */}
              {medicalRecord.entries && medicalRecord.entries.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                    <Stethoscope className="h-5 w-5 text-primary" />
                    Historial de Atenciones
                  </h3>
                  <div className="divide-y divide-slate-100">
                    {medicalRecord.entries.map((entry, index) => (
                      <div key={index} className="py-4 first:pt-0 last:pb-0">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-3">
                              <span className="px-3 py-1 bg-primary/10 text-primary text-xs font-black uppercase tracking-widest rounded-lg">
                                {getEntryTypeLabel(entry.entry_type)}
                              </span>
                              <span className="text-sm text-slate-500 flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                {formatDate(entry.timestamp)}
                              </span>
                            </div>
                            
                            {entry.specialty && (
                              <p className="text-sm font-medium text-slate-700">
                                <span className="font-bold text-slate-500">Especialidad:</span> {entry.specialty}
                              </p>
                            )}
                            
                            {entry.doctor_name && (
                              <p className="text-sm font-medium text-slate-700">
                                <span className="font-bold text-slate-500">Médico:</span> {entry.doctor_name}
                              </p>
                            )}
                            
                            {entry.diagnosis && (
                              <p className="text-sm font-medium text-slate-700">
                                <span className="font-bold text-slate-500">Diagnóstico:</span> {entry.diagnosis}
                              </p>
                            )}
                            
                            {entry.notes && (
                              <p className="text-sm font-medium text-slate-700">
                                <span className="font-bold text-slate-500">Notas:</span> {entry.notes}
                              </p>
                            )}
                            
                            {entry.results && (
                              <div className="text-sm font-medium text-slate-700">
                                <span className="font-bold text-slate-500">Resultados:</span>
                                <pre className="mt-1 text-xs bg-slate-50 p-3 rounded-lg overflow-auto">
                                  {JSON.stringify(entry.results, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
