import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'
import { Calendar, Clock, Search } from 'lucide-react'

// Types
interface Category {
  id: number
  category_type: 'specialty' | 'laboratory'
  name: string
  day_of_week: number
  start_time: string
  turn_duration: number
  max_turns_per_block: number
  rotation_type: 'fixed' | 'alternated'
  rotation_weeks: number
}

interface TimeSlot {
  slot_datetime: string
  category_name: string
  category_id: number
}

// Constants
const MAX_SLOTS_TO_DISPLAY = 3

// Mock data for fallback
const MOCK_CATEGORIES: Category[] = [
  {
    id: 1,
    category_type: 'specialty',
    name: 'Cardiología',
    day_of_week: 1,
    start_time: '09:00:00',
    turn_duration: 30,
    max_turns_per_block: 10,
    rotation_type: 'fixed',
    rotation_weeks: 1,
  },
  {
    id: 2,
    category_type: 'specialty',
    name: 'Traumatología',
    day_of_week: 2,
    start_time: '10:00:00',
    turn_duration: 30,
    max_turns_per_block: 10,
    rotation_type: 'fixed',
    rotation_weeks: 1,
  },
  {
    id: 3,
    category_type: 'laboratory',
    name: 'Análisis Clínicos',
    day_of_week: 3,
    start_time: '08:00:00',
    turn_duration: 15,
    max_turns_per_block: 20,
    rotation_type: 'fixed',
    rotation_weeks: 1,
  },
]

const MOCK_SLOTS: TimeSlot[] = [
  {
    slot_datetime: '2026-01-22T10:00:00',
    category_name: 'Cardiología',
    category_id: 1,
  },
  {
    slot_datetime: '2026-01-23T14:30:00',
    category_name: 'Cardiología',
    category_id: 1,
  },
  {
    slot_datetime: '2026-01-24T09:00:00',
    category_name: 'Cardiología',
    category_id: 1,
  },
]

export default function AppointmentSearch() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Fetch categories
  const { data: categories = MOCK_CATEGORIES } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: async () => {
      try {
        const response = await api.get('/admin/schedules')
        return Array.isArray(response.data) ? response.data : MOCK_CATEGORIES
      } catch (error) {
        console.warn('API not available, using mock data:', error)
        return MOCK_CATEGORIES
      }
    },
  })

  // Fetch available slots for selected category
  const { data: slots = [], isLoading: slotsLoading } = useQuery<TimeSlot[]>({
    queryKey: ['available-slots', selectedCategory?.id],
    queryFn: async () => {
      if (!selectedCategory) return []

      try {
        // Calculate today's date for the API call (not needed for next-slots but kept for reference if needed)
        // const today = new Date()
        // const dateStr = today.toISOString().split('T')[0]

        const response = await api.get(`/appointments/slots`, {
          params: {
            category_name: selectedCategory.name,
            category_type: selectedCategory.category_type,
          },
        })

        // The API should return TimeSlot objects
        return Array.isArray(response.data) ? response.data.slice(0, MAX_SLOTS_TO_DISPLAY) : MOCK_SLOTS
      } catch (error) {
        console.warn('API not available, using mock data:', error)
        return MOCK_SLOTS
      }
    },
    enabled: !!selectedCategory,
  })

  // Filter categories based on search query
  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) return []

    const query = searchQuery.toLowerCase()
    return categories.filter((cat) =>
      cat.name.toLowerCase().includes(query)
    ).slice(0, 5) // Show max 5 suggestions
  }, [categories, searchQuery])

  const handleCategorySelect = (category: Category) => {
    setSelectedCategory(category)
    setSearchQuery(category.name)
    setShowSuggestions(false)
  }

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
    setShowSuggestions(true)
    if (!value.trim()) {
      setSelectedCategory(null)
    }
  }

  const handleSlotClick = async (slot: TimeSlot) => {
    try {
      const response = await api.post('/appointments/book', {
        category_id: slot.category_id,
        appointment_date: slot.slot_datetime,
        category_name: slot.category_name,
        notes: 'Reserva desde el buscador inteligente'
      })

      if (response.status === 201) {
        alert(`¡Turno reservado con éxito para el ${formatDateTime(slot.slot_datetime)}!`)
        // Optionally refresh slots
      }
    } catch (err) {
      console.error('Error booking appointment:', err)
      alert('Error al reservar el turno. Por favor, intente nuevamente.')
    }
  }

  const formatDateTime = (dateString: string) => {
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
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      {/* Header */}
      <div className="space-y-2">
        <span className="text-xs font-black uppercase tracking-[0.2em] text-primary">
          Búsqueda Inteligente
        </span>
        <h1 className="text-4xl font-black tracking-tight text-slate-900">
          Buscar <span className="text-primary">Turnos</span>
        </h1>
        <p className="text-slate-500 font-medium">
          Busque por especialidad o laboratorio para ver turnos disponibles
        </p>
      </div>

      {/* Search Input with Autosuggest */}
      <div className="premium-card">
        <div className="relative">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-slate-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() => searchQuery && setShowSuggestions(true)}
              placeholder="Buscar especialidad o laboratorio..."
              className="flex h-14 w-full rounded-xl border-2 border-slate-200 bg-white pl-12 pr-4 py-3 text-base transition-all duration-200 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>

          {/* Suggestions Dropdown */}
          {showSuggestions && filteredCategories.length > 0 && (
            <div className="absolute z-10 w-full mt-2 bg-white rounded-xl shadow-xl border-2 border-slate-100 overflow-hidden">
              {filteredCategories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategorySelect(category)}
                  className="w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors flex items-center justify-between group"
                >
                  <div>
                    <p className="font-bold text-slate-900 group-hover:text-primary transition-colors">
                      {category.name}
                    </p>
                    <p className="text-xs text-slate-500 uppercase tracking-wider">
                      {category.category_type === 'specialty' ? 'Especialidad' : 'Laboratorio'}
                    </p>
                  </div>
                  <div className="h-8 w-8 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-primary transition-colors">
                    <Search className="h-4 w-4 text-slate-400 group-hover:text-white" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Available Slots */}
      {selectedCategory && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">
                Turnos Disponibles
              </h2>
              <p className="text-sm font-bold text-primary uppercase tracking-widest">
                {selectedCategory.name}
              </p>
            </div>
          </div>

          {slotsLoading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
              <p className="text-slate-400 font-bold tracking-widest animate-pulse">
                BUSCANDO DISPONIBILIDAD...
              </p>
            </div>
          ) : slots.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {slots.slice(0, MAX_SLOTS_TO_DISPLAY).map((slot) => (
                <button
                  key={`${slot.category_id}-${slot.slot_datetime}`}
                  onClick={() => handleSlotClick(slot)}
                  className="premium-card group hover:bg-slate-900 hover:text-white !p-0 overflow-hidden border-transparent transition-all duration-300"
                >
                  <div className="p-6 space-y-4">
                    <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-all">
                      <Calendar className="h-6 w-6 text-primary group-hover:text-white" />
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs font-black uppercase tracking-widest text-slate-400 group-hover:text-primary transition-colors">
                        Turno Disponible
                      </p>
                      <p className="text-base font-bold text-slate-900 group-hover:text-white transition-colors leading-tight">
                        {formatDateTime(slot.slot_datetime)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 py-2 px-3 bg-slate-50 rounded-lg group-hover:bg-white/10 transition-colors">
                      <Clock className="h-4 w-4 text-slate-500 group-hover:text-white" />
                      <span className="text-sm font-bold text-slate-700 group-hover:text-white">
                        {selectedCategory.turn_duration} minutos
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="premium-card text-center py-12">
              <div className="h-16 w-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
                <Calendar className="h-8 w-8 text-slate-400" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">
                No hay turnos disponibles
              </h3>
              <p className="text-slate-500">
                Por favor, intente con otra especialidad o laboratorio
              </p>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!selectedCategory && !searchQuery && (
        <div className="premium-card text-center py-16">
          <div className="h-20 w-20 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
            <Search className="h-10 w-10 text-primary" />
          </div>
          <h3 className="text-2xl font-black text-slate-900 mb-2">
            Comience su Búsqueda
          </h3>
          <p className="text-slate-500 font-medium max-w-md mx-auto">
            Escriba el nombre de una especialidad o laboratorio en el campo de búsqueda para ver los turnos disponibles
          </p>
        </div>
      )}
    </div>
  )
}
