import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { 
  Heart, 
  Pill, 
  FileText, 
  CheckCircle, 
  ArrowRight, 
  AlertCircle,
  Plus,
  X
} from 'lucide-react'
import AuthLayout from '../layouts/AuthLayout'
import Button from '../components/ui/Button'
import api from '../lib/api'

// Validation schema for medical history form
const medicalHistorySchema = z.object({
  chronicDiseases: z.string().optional(),
  otherInformation: z.string().optional(),
})

type MedicalHistoryFormData = z.infer<typeof medicalHistorySchema>

// Component to manage medication allergies as a dynamic list
function AllergyList({ allergies, onUpdate }: { allergies: string[]; onUpdate: (allergies: string[]) => void }) {
  const [newAllergy, setNewAllergy] = useState('')

  const addAllergy = () => {
    if (newAllergy.trim()) {
      onUpdate([...allergies, newAllergy.trim()])
      setNewAllergy('')
    }
  }

  const removeAllergy = (index: number) => {
    onUpdate(allergies.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-3">
      <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 ml-1">
        <Pill className="inline w-4 h-4 mr-2" />
        Alergias a Medicamentos
      </label>
      
      <div className="flex gap-2">
        <input
          type="text"
          value={newAllergy}
          onChange={(e) => setNewAllergy(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAllergy())}
          placeholder="Nombre del medicamento"
          className="flex h-12 flex-1 rounded-xl border border-slate-200 bg-white/50 px-4 py-3 text-sm transition-all duration-200 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary focus:bg-white"
        />
        <Button
          type="button"
          onClick={addAllergy}
          variant="outline"
          className="px-4"
        >
          <Plus className="w-5 h-5" />
        </Button>
      </div>

      {allergies.length > 0 && (
        <div className="space-y-2">
          {allergies.map((allergy, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-teal-50 border border-teal-200 rounded-lg px-4 py-2"
            >
              <span className="text-sm text-slate-700">{allergy}</span>
              <button
                type="button"
                onClick={() => removeAllergy(index)}
                className="text-red-500 hover:text-red-700 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {allergies.length === 0 && (
        <p className="text-xs text-slate-500 ml-1">
          No ha registrado alergias a medicamentos
        </p>
      )}
    </div>
  )
}

export default function RegisterStep2() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [allergies, setAllergies] = useState<string[]>([])

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<MedicalHistoryFormData>({
    resolver: zodResolver(medicalHistorySchema),
  })

  const onSubmit = async (data: MedicalHistoryFormData) => {
    try {
      setError(null)
      
      // Prepare medical history data in JSON format
      const medicalHistoryData = {
        chronic_diseases: data.chronicDiseases || '',
        medication_allergies: allergies,
        other_information: data.otherInformation || '',
      }

      // Get the current user ID from localStorage
      const userStr = localStorage.getItem('user')
      if (!userStr) {
        setError('No se encontró información del usuario. Por favor, inicie sesión.')
        return
      }

      let user
      try {
        user = JSON.parse(userStr)
      } catch (e) {
        setError('Error al leer información del usuario. Por favor, inicie sesión nuevamente.')
        return
      }

      const userId = user?.id
      if (!userId) {
        setError('No se encontró el ID del usuario. Por favor, inicie sesión nuevamente.')
        return
      }

      // Send PUT/PATCH request to update medical history
      // Note: This endpoint needs to be created in the backend
      await api.patch(`/patients/${userId}/medical-history`, {
        medical_history: medicalHistoryData,
      })

      setSuccess(true)
      
      // Redirect to dashboard after successful submission
      setTimeout(() => {
        navigate('/')
      }, 1500)
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Error al guardar la información médica. Por favor, intente nuevamente.')
      }
      console.error('Medical history update error:', err)
    }
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">
            Información Médica
          </h2>
          <p className="text-slate-600">
            Complete su historial médico (Paso 2 de 2)
          </p>
        </div>

        {/* Success message */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            <span>¡Información guardada correctamente! Redirigiendo...</span>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Step indicator */}
          <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-teal-700">
              <FileText className="w-5 h-5" />
              <span className="text-sm font-semibold">Paso 2: Historial Médico</span>
            </div>
          </div>

          {/* Chronic diseases field */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 ml-1">
              <Heart className="inline w-4 h-4 mr-2" />
              ¿Tiene antecedentes de enfermedades crónicas?
            </label>
            <textarea
              {...register('chronicDiseases')}
              rows={4}
              placeholder="Ejemplo: Diabetes tipo 2, Hipertensión arterial, etc."
              className="flex w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3 text-sm transition-all duration-200 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary focus:bg-white resize-none"
            />
            {errors.chronicDiseases && (
              <p className="mt-1.5 text-xs font-medium text-red-500 ml-1">
                {errors.chronicDiseases.message}
              </p>
            )}
          </div>

          {/* Medication allergies list */}
          <AllergyList allergies={allergies} onUpdate={setAllergies} />

          {/* Other medical information */}
          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 ml-1">
              <FileText className="inline w-4 h-4 mr-2" />
              Otros Datos de Interés
            </label>
            <textarea
              {...register('otherInformation')}
              rows={3}
              placeholder="Cirugías previas, condiciones especiales, etc."
              className="flex w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3 text-sm transition-all duration-200 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary focus:bg-white resize-none"
            />
            {errors.otherInformation && (
              <p className="mt-1.5 text-xs font-medium text-red-500 ml-1">
                {errors.otherInformation.message}
              </p>
            )}
          </div>

          {/* Submit button */}
          <Button
            type="submit"
            isLoading={isSubmitting}
            className="w-full"
          >
            {isSubmitting ? (
              'Guardando...'
            ) : (
              <>
                Completar Registro
                <ArrowRight className="ml-2 w-5 h-5" />
              </>
            )}
          </Button>
        </form>

        {/* Optional skip link */}
        <div className="text-center">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
          >
            Omitir este paso por ahora
          </button>
        </div>
      </div>
    </AuthLayout>
  )
}
