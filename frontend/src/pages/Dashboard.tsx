import { Calendar } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useMemo } from 'react'
import api from '../lib/api'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'

// Types
interface Appointment {
  id: string
  patient_name: string
  specialty: string
  doctor_name: string
  date: string
  status: 'confirmed' | 'pending' | 'completed'
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const { data: appointments = [], isLoading } = useQuery<Appointment[]>({
    queryKey: ['appointments', 'me'],
    queryFn: async () => {
      try {
        const response = await api.get('/appointments/me')
        return Array.isArray(response.data) ? response.data : []
      } catch (error) {
        console.warn('API not available:', error)
        return []
      }
    },
  })

  // Filter to show only future appointments
  const futureAppointments = useMemo(() => {
    return appointments.filter(appointment => {
      const appointmentDate = new Date(appointment.date)
      return appointmentDate > new Date()
    })
  }, [appointments])

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('es-AR', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    }).format(date)
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'confirmed': return 'bg-emerald-100 text-emerald-700'
      case 'pending': return 'bg-amber-100 text-amber-700'
      case 'completed': return 'bg-indigo-100 text-indigo-700'
      default: return 'bg-slate-100 text-slate-700'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'confirmed': return 'Confirmado'
      case 'pending': return 'Pendiente'
      case 'completed': return 'Completado'
      default: return status
    }
  }

  // If user is a patient, show appointment booking as primary action
  if (user?.role === 'patient') {
    return (
      <div className="space-y-10 pb-12">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <h1 className="text-4xl font-black tracking-tight text-slate-900">
              Mis <span className="text-primary">Turnos</span>
            </h1>
            <p className="text-slate-500 font-medium">Gestiona tus citas médicas.</p>
          </div>
          <Button 
            onClick={() => navigate('/appointments/new')}
            className="flex items-center gap-2"
          >
            <Calendar className="h-4 w-4" />
            Nuevo Turno
          </Button>
        </div>

        {/* Future Appointments Table */}
        <div className="premium-card !p-0 overflow-hidden border-none shadow-xl bg-white">
          <div className="p-8 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight">Próximos Turnos</h2>
              <p className="text-sm font-medium text-slate-500">Tus citas programadas</p>
            </div>
          </div>
          <div className="p-4">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                <p className="text-slate-400 font-medium animate-pulse">Cargando turnos...</p>
              </div>
            ) : futureAppointments.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <Calendar className="h-16 w-16 text-slate-300" />
                <p className="text-slate-500 font-medium">No tienes turnos programados</p>
                <Button 
                  onClick={() => navigate('/appointments/new')}
                  variant="outline"
                  className="mt-4"
                >
                  Agendar Turno
                </Button>
              </div>
            ) : (
              <div className="divide-y divide-slate-50">
                {futureAppointments.map((appointment) => (
                  <div
                    key={appointment.id}
                    className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-2xl transition-colors hover:bg-slate-50/80"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 font-bold group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                        <Calendar className="h-6 w-6" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-900 group-hover:text-primary transition-colors">{appointment.specialty}</p>
                        <p className="text-xs font-medium text-slate-500">
                          {appointment.doctor_name}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between sm:justify-end gap-6 mt-4 sm:mt-0">
                      <div className="text-right">
                        <p className="text-sm font-black text-slate-900">{formatDate(appointment.date)}</p>
                        <p className="text-xs font-medium text-slate-500">{formatTime(appointment.date)}</p>
                      </div>
                      <span
                        className={`px-3 py-1 text-[10px] font-black uppercase tracking-widest rounded-lg shadow-sm ${getStatusBadgeClass(
                          appointment.status
                        )}`}
                      >
                        {getStatusLabel(appointment.status)}
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

  // For non-patient users (admin, doctor, staff), show a different view
  return (
    <div className="space-y-10 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <h1 className="text-4xl font-black tracking-tight text-slate-900">
            Panel de <span className="text-primary">Control</span>
          </h1>
          <p className="text-slate-500 font-medium">Bienvenido de nuevo al sistema HospitalPro.</p>
        </div>
      </div>

      {/* Appointments Table */}
      <div className="premium-card !p-0 overflow-hidden border-none shadow-xl bg-white">
        <div className="p-8 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">Próximos Turnos</h2>
            <p className="text-sm font-medium text-slate-500">Listado de citas programadas</p>
          </div>
        </div>
        <div className="p-4">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
              <p className="text-slate-400 font-medium animate-pulse">Cargando datos...</p>
            </div>
          ) : futureAppointments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <Calendar className="h-16 w-16 text-slate-300" />
              <p className="text-slate-500 font-medium">No hay turnos programados</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-50">
              {futureAppointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-2xl transition-colors hover:bg-slate-50/80"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 font-bold group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                      {appointment.patient_name?.[0] || '?'}
                    </div>
                    <div>
                      <p className="font-bold text-slate-900 group-hover:text-primary transition-colors">{appointment.patient_name}</p>
                      <p className="text-xs font-medium text-slate-500">
                        {appointment.specialty} • {appointment.doctor_name}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between sm:justify-end gap-6 mt-4 sm:mt-0">
                    <div className="text-right">
                      <p className="text-sm font-black text-slate-900">{formatDate(appointment.date)}</p>
                      <p className="text-xs font-medium text-slate-500">{formatTime(appointment.date)}</p>
                    </div>
                    <span
                      className={`px-3 py-1 text-[10px] font-black uppercase tracking-widest rounded-lg shadow-sm ${getStatusBadgeClass(
                        appointment.status
                      )}`}
                    >
                      {getStatusLabel(appointment.status)}
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
