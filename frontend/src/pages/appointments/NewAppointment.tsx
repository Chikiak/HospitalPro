import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import Button from '../../components/ui/Button'
import { Calendar, Check, ChevronLeft, Clock, User } from 'lucide-react'

// Types
interface Turn {
  id: string
  date: string
  doctor_name: string
}

interface Specialty {
  id: string
  name: string
}

// Mock data for fallback
const MOCK_TURNS: Turn[] = [
  { id: '1', date: '2026-01-20T10:00:00', doctor_name: 'Dr. García' },
  { id: '2', date: '2026-01-21T14:30:00', doctor_name: 'Dra. Rodríguez' },
  { id: '3', date: '2026-01-22T09:00:00', doctor_name: 'Dr. López' },
]

const MOCK_SPECIALTIES: Specialty[] = [
  { id: '1', name: 'Cardiología' },
  { id: '2', name: 'Traumatología' },
  { id: '3', name: 'Pediatría' },
  { id: '4', name: 'Dermatología' },
  { id: '5', name: 'Oftalmología' },
]

export default function NewAppointment() {
  const [step, setStep] = useState(1)
  const [selectedSpecialty, setSelectedSpecialty] = useState<Specialty | null>(null)
  const [selectedTurn, setSelectedTurn] = useState<Turn | null>(null)

  // Fetch available turns based on specialty
  const { data: turns = MOCK_TURNS, isLoading: turnsLoading } = useQuery<Turn[]>({
    queryKey: ['turns', selectedSpecialty?.id],
    queryFn: async () => {
      try {
        const response = await axios.get(`/api/appointments/available?specialty=${selectedSpecialty?.id}`)
        // Ensure we always return an array
        if (Array.isArray(response.data)) {
          return response.data
        }
        console.warn('API returned non-array data, using mock data')
        return MOCK_TURNS
      } catch (error) {
        // Fallback to mock data if API fails
        console.warn('API not available, using mock data:', error)
        return MOCK_TURNS
      }
    },
    enabled: !!selectedSpecialty && step === 2,
  })

  const handleSpecialtySelect = (specialty: Specialty) => {
    setSelectedSpecialty(specialty)
    setStep(2)
  }

  const handleTurnSelect = (turn: Turn) => {
    setSelectedTurn(turn)
    setStep(3)
  }

  const handleConfirmBooking = async () => {
    try {
      await axios.post('/api/appointments', {
        specialty_id: selectedSpecialty?.id,
        turn_id: selectedTurn?.id,
      })
      alert('¡Turno reservado exitosamente!')
      // Reset form
      setStep(1)
      setSelectedSpecialty(null)
      setSelectedTurn(null)
    } catch (error) {
      console.error('Error booking appointment:', error)
      alert('Error al reservar el turno. Por favor, intente nuevamente.')
    }
  }

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1)
      if (step === 2) setSelectedSpecialty(null)
      if (step === 3) setSelectedTurn(null)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('es-AR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Nuevo Turno</h1>
        <p className="text-slate-600 mt-2">Reserve su cita médica en 3 simples pasos</p>
      </div>

      {/* Progress Indicator */}
      <div className="bg-white rounded-lg p-6 border border-slate-200">
        <div className="flex items-center justify-between">
          <div className={`flex items-center gap-3 ${step >= 1 ? 'text-teal-700' : 'text-slate-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-teal-700 text-white' : 'bg-slate-200'}`}>
              {step > 1 ? <Check className="h-5 w-5" /> : '1'}
            </div>
            <span className="font-medium">Especialidad</span>
          </div>
          <div className="flex-1 h-1 mx-4 bg-slate-200">
            <div className={`h-full ${step >= 2 ? 'bg-teal-700' : 'bg-slate-200'}`} style={{ width: step >= 2 ? '100%' : '0%' }} />
          </div>
          <div className={`flex items-center gap-3 ${step >= 2 ? 'text-teal-700' : 'text-slate-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-teal-700 text-white' : 'bg-slate-200'}`}>
              {step > 2 ? <Check className="h-5 w-5" /> : '2'}
            </div>
            <span className="font-medium">Turnos</span>
          </div>
          <div className="flex-1 h-1 mx-4 bg-slate-200">
            <div className={`h-full ${step >= 3 ? 'bg-teal-700' : 'bg-slate-200'}`} style={{ width: step >= 3 ? '100%' : '0%' }} />
          </div>
          <div className={`flex items-center gap-3 ${step >= 3 ? 'text-teal-700' : 'text-slate-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-teal-700 text-white' : 'bg-slate-200'}`}>
              3
            </div>
            <span className="font-medium">Confirmar</span>
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-lg p-6 border border-slate-200">
        {/* Step 1: Select Specialty */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-slate-900">Seleccione una Especialidad</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {MOCK_SPECIALTIES.map((specialty) => (
                <button
                  key={specialty.id}
                  onClick={() => handleSpecialtySelect(specialty)}
                  className="p-4 border-2 border-slate-200 rounded-lg hover:border-teal-700 hover:bg-teal-50 transition-all text-left"
                >
                  <p className="font-medium text-slate-900">{specialty.name}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Show 3 Closest Turns */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-slate-900">
                Turnos Disponibles - {selectedSpecialty?.name}
              </h2>
              <Button variant="ghost" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Volver
              </Button>
            </div>
            {turnsLoading ? (
              <div className="text-center py-8">
                <p className="text-slate-600">Cargando turnos disponibles...</p>
              </div>
            ) : !Array.isArray(turns) || turns.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-slate-600">No hay turnos disponibles</p>
              </div>
            ) : (
              <div className="space-y-3">
                {turns.slice(0, 3).map((turn) => (
                  <button
                    key={turn.id}
                    onClick={() => handleTurnSelect(turn)}
                    className="w-full p-4 border-2 border-slate-200 rounded-lg hover:border-teal-700 hover:bg-teal-50 transition-all text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-5 w-5 text-teal-700" />
                          <p className="font-medium text-slate-900">{formatDate(turn.date)}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <User className="h-5 w-5 text-slate-600" />
                          <p className="text-sm text-slate-600">{turn.doctor_name}</p>
                        </div>
                      </div>
                      <Clock className="h-5 w-5 text-slate-400" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Confirm Booking */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-slate-900">Confirmar Reserva</h2>
              <Button variant="ghost" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Volver
              </Button>
            </div>
            <div className="bg-slate-50 rounded-lg p-6 space-y-4">
              <div>
                <p className="text-sm text-slate-600">Especialidad</p>
                <p className="text-lg font-semibold text-slate-900">{selectedSpecialty?.name}</p>
              </div>
              <div className="border-t border-slate-200 pt-4">
                <p className="text-sm text-slate-600">Fecha y Hora</p>
                <p className="text-lg font-semibold text-slate-900">
                  {selectedTurn && formatDate(selectedTurn.date)}
                </p>
              </div>
              <div className="border-t border-slate-200 pt-4">
                <p className="text-sm text-slate-600">Profesional</p>
                <p className="text-lg font-semibold text-slate-900">{selectedTurn?.doctor_name}</p>
              </div>
            </div>
            <div className="flex gap-4">
              <Button variant="outline" onClick={handleBack} className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleConfirmBooking} className="flex-1">
                <Check className="h-5 w-5 mr-2" />
                Confirmar Turno
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
