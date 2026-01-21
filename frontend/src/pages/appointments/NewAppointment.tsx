import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'
import Button from '../../components/ui/Button'
import { Check, ChevronLeft, Clock, Stethoscope, ArrowRight, ShieldCheck, FlaskConical, AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/utils'
import Tabs from '../../components/ui/Tabs'

// Types
interface TimeSlot {
  slot_datetime: string
  category_name: string
  category_id: number
  warning_message?: string
  deadline_time?: string
}

interface Category {
  id: number
  name: string
  category_type: 'specialty' | 'laboratory'
}

export default function NewAppointment() {
  const [step, setStep] = useState(1)
  const [activeType, setActiveType] = useState<'specialty' | 'laboratory'>('specialty')
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null)
  const [selectedTurn, setSelectedTurn] = useState<TimeSlot | null>(null)

  // Fetch all categories (schedules) to get the list of unique specialties/labs
  const { data: allCategories = [], isLoading: catsLoading } = useQuery<Category[]>({
    queryKey: ['admin-schedules'],
    queryFn: async () => {
      const response = await api.get('/admin/schedules')
      const data = response.data as any[]

      // Deduplicate by name
      const uniqueMap = new Map<string, Category>()
      data.forEach(item => {
        if (!uniqueMap.has(item.name)) {
          uniqueMap.set(item.name, {
            id: item.id,
            name: item.name,
            category_type: item.category_type
          })
        }
      })
      return Array.from(uniqueMap.values())
    }
  })

  const filteredCategories = useMemo(() => {
    return allCategories.filter(cat => cat.category_type === activeType)
  }, [allCategories, activeType])

  const { data: turns = [], isLoading: turnsLoading } = useQuery<TimeSlot[]>({
    queryKey: ['turns', selectedCategory?.name],
    queryFn: async () => {
      if (!selectedCategory) return []
      const today = new Date()
      // We look for slots from tomorrow onwards for safety or today
      const dateStr = today.toISOString().split('T')[0]
      const response = await api.get(`/appointments/slots`, {
        params: {
          category_name: selectedCategory.name,
          category_type: selectedCategory.category_type,
          date: dateStr,
        }
      })
      return Array.isArray(response.data) ? response.data : []
    },
    enabled: !!selectedCategory && step === 2,
  })

  const groupedTurns = useMemo(() => {
    const groups: Record<string, TimeSlot[]> = {}
    turns.forEach(turn => {
      const dateKey = turn.slot_datetime.split('T')[0]
      if (!groups[dateKey]) groups[dateKey] = []
      groups[dateKey].push(turn)
    })
    return groups
  }, [turns])

  const handleCategorySelect = (category: Category) => {
    setSelectedCategory(category)
    setStep(2)
  }

  const handleTurnSelect = (turn: TimeSlot) => {
    setSelectedTurn(turn)
    setStep(3)
  }

  const handleConfirmBooking = async () => {
    if (!selectedTurn || !selectedCategory) return
    try {
      await api.post('/appointments/book', {
        category_id: selectedCategory.id, // Link to the specific schedule
        appointment_date: selectedTurn.slot_datetime,
        category_name: selectedCategory.name,
        notes: `Reserva de ${activeType === 'specialty' ? 'Especialidad' : 'Laboratorio'}`
      })
      alert('¡Turno reservado exitosamente!')
      setStep(1)
      setSelectedCategory(null)
      setSelectedTurn(null)
    } catch (error) {
      console.error('Error booking appointment:', error)
      alert('Error al reservar el turno. Por favor, intente nuevamente.')
    }
  }

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1)
      if (step === 2) setSelectedCategory(null)
      if (step === 3) setSelectedTurn(null)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('es-AR', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    }).format(date)
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('es-AR', {
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
        <div className="hidden md:flex items-center gap-2 text-slate-400 font-bold text-xs text-right">
          <ShieldCheck className="h-4 w-4" />
          <div className="flex flex-col leading-tight">
            <span>SISTEMA SEGURO Y CIFRADO</span>
            <span>HOSPITAL PRO V1.0</span>
          </div>
        </div>
      </div>

      {/* Modern Progress Indicator */}
      <div className="premium-card bg-slate-900 text-white !py-8">
        <div className="flex items-center justify-center max-w-2xl mx-auto">
          {[
            { s: 1, label: 'Servicio', icon: Stethoscope },
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
        {/* Step 1: Specialty/Lab Selection */}
        {step === 1 && (
          <div className="space-y-8 lg:animate-fade-in-up">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">Seleccione el Servicio</h2>
              <div className="w-full md:w-auto">
                <Tabs
                  onTabChange={(id) => setActiveType(id as any)}
                  tabs={[
                    { id: 'specialty', label: 'Especialidades', icon: <Stethoscope size={16} /> },
                    { id: 'laboratory', label: 'Laboratorio', icon: <FlaskConical size={16} /> },
                  ]}
                  defaultTab="specialty"
                >
                  {() => null}
                </Tabs>
              </div>
            </div>

            {catsLoading ? (
              <div className="flex flex-col items-center justify-center py-20 animate-pulse text-slate-400">
                <div className="h-10 w-10 border-4 border-t-primary rounded-full animate-spin mb-4"></div>
                CARGANDO SERVICIOS...
              </div>
            ) : filteredCategories.length === 0 ? (
              <div className="text-center py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                <p className="text-slate-400 font-bold uppercase tracking-widest text-sm">No hay servicios disponibles en esta categoría</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredCategories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => handleCategorySelect(cat)}
                    className="premium-card group hover:bg-slate-900 hover:text-white border-transparent text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-500 group-hover:text-primary transition-colors">Departamento</p>
                        <p className="text-xl font-bold">{cat.name}</p>
                      </div>
                      <div className="h-10 w-10 rounded-xl bg-slate-100 flex items-center justify-center group-hover:bg-primary transition-colors">
                        <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-white" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 2: Available Turns */}
        {step === 2 && (
          <div className="space-y-8 lg:animate-fade-in-right">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">Turnos Disponibles</h2>
                <p className="text-sm font-bold text-primary uppercase tracking-widest">{selectedCategory?.name}</p>
              </div>
              <Button variant="outline" onClick={handleBack} className="text-xs">
                <ChevronLeft className="h-4 w-4 mr-1" /> VOLVER
              </Button>
            </div>
            
            {/* Warning message for laboratories */}
            {turns.length > 0 && turns[0].warning_message && (
              <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-4 flex items-start gap-3 shadow-sm">
                <AlertTriangle className="h-6 w-6 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-amber-800 text-sm uppercase tracking-wide">Aviso Importante</p>
                  <p className="text-amber-700 font-medium mt-1">{turns[0].warning_message}</p>
                  {turns[0].deadline_time && (
                    <p className="text-amber-600 text-sm mt-2 font-bold">
                      ⏰ Hora límite de recepción: {turns[0].deadline_time}
                    </p>
                  )}
                </div>
              </div>
            )}
            
            {turnsLoading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                <p className="text-slate-400 font-bold tracking-widest animate-pulse">BUSCANDO DISPONIBILIDAD...</p>
              </div>
            ) : turns.length === 0 ? (
              <div className="text-center py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                <p className="text-slate-400 font-bold uppercase tracking-widest text-sm">No hay turnos próximos para esta especialidad</p>
              </div>
            ) : (
              <div className="space-y-12">
                {Object.entries(groupedTurns).map(([dateKey, slots]) => (
                  <div key={dateKey} className="space-y-6">
                    <div className="flex items-center gap-4">
                      <div className="h-px flex-1 bg-slate-100"></div>
                      <h3 className="text-sm font-black text-slate-400 uppercase tracking-[0.2em] whitespace-nowrap">
                        {formatDate(dateKey)}
                      </h3>
                      <div className="h-px flex-1 bg-slate-100"></div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                      {slots.map((turn) => (
                        <button
                          key={`${turn.category_id}-${turn.slot_datetime}`}
                          onClick={() => handleTurnSelect(turn)}
                          className="premium-card group text-center !p-4 hover:border-primary transition-all hover:bg-primary/5"
                        >
                          <p className="text-lg font-bold text-slate-900 group-hover:text-primary transition-colors">
                            {formatTime(turn.slot_datetime)}
                          </p>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">Disponible</p>
                        </button>
                      ))}
                    </div>
                  </div>
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
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Servicio Seleccionado</p>
                    <p className="text-lg font-bold text-slate-900">{selectedCategory?.name}</p>
                  </div>
                  <div className="space-y-1 text-right">
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Tipo de Turno</p>
                    <p className="text-lg font-bold text-slate-900 capitalize">{activeType === 'specialty' ? 'Especialidad' : 'Laboratorio'}</p>
                  </div>
                </div>

                <div className="py-6 border-y border-slate-50 text-center space-y-1">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Cita Programada para</p>
                  <p className="text-2xl font-black text-primary uppercase">
                    {selectedTurn && formatDate(selectedTurn.slot_datetime)} - {selectedTurn && formatTime(selectedTurn.slot_datetime)}
                  </p>
                </div>
                
                {/* Warning message for laboratory appointments in confirmation step */}
                {selectedTurn?.warning_message && (
                  <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold text-amber-800 text-sm">Recordatorio Importante</p>
                      <p className="text-amber-700 text-sm mt-1">{selectedTurn.warning_message}</p>
                    </div>
                  </div>
                )}

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
