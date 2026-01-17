import { Users, Calendar, Clock, TrendingUp } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/axios'

// Types
interface Appointment {
  id: string
  patient_name: string
  specialty: string
  doctor_name: string
  date: string
  status: 'confirmed' | 'pending' | 'completed'
}

// Mock data for fallback
const MOCK_APPOINTMENTS: Appointment[] = [
  {
    id: '1',
    patient_name: 'Juan Pérez',
    specialty: 'Consulta General',
    doctor_name: 'Dr. García',
    date: '2026-01-16T10:30:00',
    status: 'confirmed',
  },
  {
    id: '2',
    patient_name: 'María González',
    specialty: 'Cardiología',
    doctor_name: 'Dra. Rodríguez',
    date: '2026-01-16T11:00:00',
    status: 'pending',
  },
  {
    id: '3',
    patient_name: 'Carlos Martínez',
    specialty: 'Traumatología',
    doctor_name: 'Dr. López',
    date: '2026-01-16T11:30:00',
    status: 'confirmed',
  },
]

export default function Dashboard() {
  // Fetch user's appointments
  const { data: appointments = MOCK_APPOINTMENTS, isLoading, error } = useQuery<Appointment[]>({
    queryKey: ['appointments', 'me'],
    queryFn: async () => {
      try {
        const response = await api.get('/appointments/me')
        // Ensure we always return an array
        if (Array.isArray(response.data)) {
          return response.data
        }
        console.warn('API returned non-array data, using mock data')
        return MOCK_APPOINTMENTS
      } catch (error) {
        // Fallback to mock data if API fails
        console.warn('API not available, using mock data:', error)
        return MOCK_APPOINTMENTS
      }
    },
  })

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-700'
      case 'pending':
        return 'bg-yellow-100 text-yellow-700'
      case 'completed':
        return 'bg-blue-100 text-blue-700'
      default:
        return 'bg-slate-100 text-slate-700'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'Confirmado'
      case 'pending':
        return 'Pendiente'
      case 'completed':
        return 'Completado'
      default:
        return status
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-2">Vista general del sistema de gestión de turnos</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Pacientes Totales</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">1,234</p>
            </div>
            <div className="bg-teal-100 p-3 rounded-lg">
              <Users className="h-6 w-6 text-teal-700" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1 text-sm">
            <TrendingUp className="h-4 w-4 text-green-600" />
            <span className="text-green-600">+12%</span>
            <span className="text-slate-600">desde el mes pasado</span>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Turnos de Hoy</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">42</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <Calendar className="h-6 w-6 text-blue-700" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1 text-sm">
            <span className="text-slate-600">18 completados, 24 pendientes</span>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Tiempo Promedio</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">24min</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <Clock className="h-6 w-6 text-purple-700" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1 text-sm">
            <span className="text-slate-600">por consulta</span>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Tasa de Ocupación</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">87%</p>
            </div>
            <div className="bg-orange-100 p-3 rounded-lg">
              <TrendingUp className="h-6 w-6 text-orange-700" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-1 text-sm">
            <span className="text-slate-600">capacidad utilizada</span>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900">Próximos Turnos</h2>
        </div>
        <div className="p-6">
          {isLoading ? (
            <div className="text-center py-8">
              <p className="text-slate-600">Cargando turnos...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-600">Error al cargar los turnos</p>
            </div>
          ) : !Array.isArray(appointments) || appointments.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-600">No hay turnos programados</p>
            </div>
          ) : (
            <div className="space-y-4">
              {appointments.map((appointment, index) => (
                <div
                  key={appointment.id}
                  className={`flex items-center justify-between py-3 ${index < appointments.length - 1 ? 'border-b border-slate-100' : ''
                    }`}
                >
                  <div>
                    <p className="font-medium text-slate-900">{appointment.patient_name}</p>
                    <p className="text-sm text-slate-600">
                      {appointment.specialty} - {appointment.doctor_name}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-slate-900">{formatTime(appointment.date)}</p>
                    <span
                      className={`inline-block px-2 py-1 text-xs rounded-full ${getStatusBadgeClass(
                        appointment.status
                      )}`}
                    >
                      {getStatusText(appointment.status)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
