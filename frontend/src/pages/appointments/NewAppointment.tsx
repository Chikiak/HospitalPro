import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/axios'
import Button from '../../components/ui/Button'
import { Calendar, Check, ChevronLeft, Clock, User, Stethoscope, ArrowRight, ShieldCheck } from 'lucide-react'
import { cn } from '../../lib/utils'

// Types remain the same
interface Turn {
  id: string
  date: string
  doctor_name: string
}

interface Specialty {
  id: string
  name: string
}

// Mock data remains the same
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

  const { data: turns = MOCK_TURNS, isLoading: turnsLoading } = useQuery<Turn[]>({
    queryKey: ['turns', selectedSpecialty?.id],
    queryFn: async () => {
      try {
        const response = await api.get(`/appointments/available?specialty=${selectedSpecialty?.id}`)
        return Array.isArray(response.data) ? response.data : MOCK_TURNS
      } catch (error) {
        console.warn('API not available, using mock data:', error)
        return MOCK_TURNS
      }
    },
    enabled: !!selectedSpecialty?.id && step === 2,
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
      await api.post('/appointments/book', {
        specialty_id: selectedSpecialty?.id,
        turn_id: selectedTurn?.id,
      })
      alert('¡Turno reservado exitosamente!')
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
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  return (
    <div className="max-w-5xl mx-auto space-y-10 pb-20">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <span className="text-xs font-black uppercase tracking-[0.2em] text-primary">Proceso de Reserva</span>
          <h1 className="text-4xl font-black tracking-tight text-slate-900">
            Agenda tu <span className="text-primary">Turno</span>
          </h1>
          <p className="text-slate-500 font-medium">Gestiona tu salud de forma rápida y profesional.</p>
        </div>
        <div className="hidden md:flex items-center gap-2 text-slate-400 font-bold text-xs">
          <ShieldCheck className="h-4 w-4" />
          SISTEMA SEGURO Y CIFRADO
        </div>
      </div>

      {/* Modern Progress Indicator */}
      <div className="premium-card bg-slate-900 text-white !py-8">
        <div className="flex items-center justify-center max-w-2xl mx-auto">
          {[
            { s: 1, label: 'Especialidad', icon: Stethoscope },
            { s: 2, label: 'Disponibilidad', icon: Clock },
            { s: 3, label: 'Finalizar', icon: Check },
          ].map((item, i) => (
            <div key={item.s} className="flex items-center flex-1 last:flex-none group">
              <div className="flex flex-col items-center gap-3 relative z-10">
                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500 shadow-lg",
                  step >= item.s
                    ? "bg-primary text-white shadow-primary/40 scale-110"
                    : "bg-slate-800 text-slate-500"
                )}>
                  {step > item.s ? <Check className="h-6 w-6" /> : <item.icon className="h-6 w-6" />}
                </div>
                <span className={cn(
                  "text-[10px] font-black uppercase tracking-widest whitespace-nowrap transition-colors duration-500",
                  step >= item.s ? "text-primary" : "text-slate-600"
                )}>
                  {item.label}
                </span>
              </div>
              {i < 2 && (
                <div className="flex-1 h-0.5 mx-[-10px] mt-[-20px] bg-slate-800 overflow-hidden relative">
                  <div className={cn(
                    "h-full bg-primary transition-all duration-700 ease-in-out",
                    step > item.s ? "w-full" : "w-0"
                  )}></div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Wizard Content */}
      <div className="min-h-[400px]">
        {/* Step 1: Specialty Selection */}
        {step === 1 && (
          <div className="space-y-6 lg:animate-fade-in-up">
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">Seleccione la Especialidad</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {MOCK_SPECIALTIES.map((specialty) => (
                <button
                  key={specialty.id}
                  onClick={() => handleSpecialtySelect(specialty)}
                  className="premium-card group hover:bg-slate-900 hover:text-white border-transparent"
                >
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-xs font-bold uppercase tracking-widest text-slate-500 group-hover:text-primary transition-colors">Departamento</p>
                      <p className="text-xl font-bold">{specialty.name}</p>
                    </div>
                    <div className="h-10 w-10 rounded-xl bg-slate-100 flex items-center justify-center group-hover:bg-primary transition-colors">
                      <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-white" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Available Turns */}
        {step === 2 && (
          <div className="space-y-8 lg:animate-fade-in-right">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">Turnos Disponibles</h2>
                <p className="text-sm font-bold text-primary uppercase tracking-widest">{selectedSpecialty?.name}</p>
              </div>
              <Button variant="outline" onClick={handleBack} className="text-xs">
                <ChevronLeft className="h-4 w-4 mr-1" /> VOLVER
              </Button>
            </div>
            {turnsLoading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                <p className="text-slate-400 font-bold tracking-widest animate-pulse">BUSCANDO DISPONIBILIDAD...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {turns.slice(0, 4).map((turn) => (
                  <button
                    key={turn.id}
                    onClick={() => handleTurnSelect(turn)}
                    className="premium-card group text-left !p-0 overflow-hidden"
                  >
                    <div className="p-6 flex items-start gap-5">
                      <div className="h-14 w-14 rounded-2xl bg-primary/10 flex flex-col items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-all">
                        <Calendar className="h-5 w-5" />
                      </div>
                      <div className="flex-1 space-y-3">
                        <div>
                          <p className="text-xs font-black uppercase tracking-widest text-slate-400 group-hover:text-emerald-500 transition-colors">Horario Disponible</p>
                          <p className="text-xl font-bold text-slate-900 group-hover:text-primary transition-colors leading-tight mt-1">{formatDate(turn.date)}</p>
                        </div>
                        <div className="flex items-center gap-2 py-1 px-3 bg-slate-50 rounded-lg w-fit group-hover:bg-white/10 transition-colors">
                          <User className="h-4 w-4 text-slate-500" />
                          <span className="text-sm font-bold text-slate-700 group-hover:text-white">{turn.doctor_name}</span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Final Confirmation */}
        {step === 3 && (
          <div className="max-w-2xl mx-auto lg:animate-fade-in-scale">
            <div className="premium-card !p-0 overflow-hidden relative border-none shadow-2xl">
              <div className="bg-primary p-8 text-white text-center space-y-2">
                <div className="h-16 w-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-white/40">
                  <Check className="h-8 w-8 text-white" />
                </div>
                <h2 className="text-2xl font-black uppercase tracking-tight">Verifica los Datos</h2>
                <p className="text-emerald-100 font-medium">Confirma tu asistencia al siguiente turno</p>
              </div>

              <div className="p-10 space-y-8 bg-white">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-1">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Especialidad Médica</p>
                    <p className="text-lg font-bold text-slate-900">{selectedSpecialty?.name}</p>
                  </div>
                  <div className="space-y-1 text-right">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Profesional Asignado</p>
                    <p className="text-lg font-bold text-slate-900">{selectedTurn?.doctor_name}</p>
                  </div>
                </div>

                <div className="py-6 border-y border-slate-50 text-center space-y-1">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Cita Programada para</p>
                  <p className="text-2xl font-black text-primary uppercase">{selectedTurn && formatDate(selectedTurn.date)}</p>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 pt-4">
                  <Button variant="outline" onClick={handleBack} className="flex-1 !py-4 font-black tracking-widest text-xs uppercase">
                    MODIFICAR
                  </Button>
                  <Button onClick={handleConfirmBooking} className="flex-1 !py-4 font-black tracking-widest text-xs uppercase shadow-xl shadow-primary/30">
                    CONFIRMAR Y FINALIZAR
                  </Button>
                </div>
              </div>
            </div>
            <p className="text-center mt-6 text-slate-400 text-xs font-bold uppercase tracking-widest">Al confirmar, el turno quedará reservado automáticamente</p>
          </div>
        )}
      </div>
    </div>
  )
}
