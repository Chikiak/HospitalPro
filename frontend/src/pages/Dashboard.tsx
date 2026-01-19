import { Users, Calendar, Clock, TrendingUp, Activity, ArrowRight, UserPlus } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import api from '../lib/axios'
import Button from '../components/ui/Button'
// @ts-ignore
import dashboardIll from '../assets/dashboard_ill.png'

// Types
interface Appointment {
  id: string
  patient_name: string
  specialty: string
  doctor_name: string
  date: string
  status: 'confirmed' | 'pending' | 'completed'
}

// Mock data remains the same
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
  const { data: appointments = MOCK_APPOINTMENTS, isLoading } = useQuery<Appointment[]>({
    queryKey: ['appointments', 'me'],
    queryFn: async () => {
      try {
        const response = await api.get('/appointments/me')
        return Array.isArray(response.data) ? response.data : MOCK_APPOINTMENTS
      } catch (error) {
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
      case 'confirmed': return 'bg-emerald-100 text-emerald-700'
      case 'pending': return 'bg-amber-100 text-amber-700'
      case 'completed': return 'bg-indigo-100 text-indigo-700'
      default: return 'bg-slate-100 text-slate-700'
    }
  }

  return (
    <div className="space-y-10 pb-12">
      {/* Header Section with Welcome */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <h1 className="text-4xl font-black tracking-tight text-slate-900">
            Panel de <span className="text-primary">Control</span>
          </h1>
          <p className="text-slate-500 font-medium">Bienvenido de nuevo al sistema HospitalPro.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="hidden sm:flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Reportes
          </Button>
          <Button className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Nuevo Turno
          </Button>
        </div>
      </div>

      {/* Hero-like Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-slate-900 p-8 md:p-12 text-white shadow-2xl">
        <div className="relative z-10 max-w-lg space-y-6">
          <span className="inline-block px-3 py-1 rounded-full bg-primary/20 text-primary text-xs font-bold uppercase tracking-widest border border-primary/30">
            Actualización del Sistema
          </span>
          <h2 className="text-3xl md:text-4xl font-bold leading-tight">
            Optimiza la atención de tus pacientes hoy mismo.
          </h2>
          <p className="text-slate-300 text-lg">
            Hemos integrado nuevas herramientas de triaje y seguimiento post-consulta.
          </p>
          <Button className="bg-white text-slate-900 border-none hover:bg-slate-100">
            Ver Novedades <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
        <img
          src={dashboardIll}
          alt="Dashboard Illustration"
          className="absolute right-[-10%] top-[-20%] w-[60%] opacity-40 mix-blend-screen pointer-events-none hidden lg:block"
        />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Pacientes Totales', value: '1,234', icon: Users, color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { label: 'Turnos de Hoy', value: '42', icon: Calendar, color: 'text-indigo-600', bg: 'bg-indigo-50' },
          { label: 'Tiempo Promedio', value: '24min', icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
          { label: 'Nuevos Registros', value: '+12', icon: UserPlus, color: 'text-rose-600', bg: 'bg-rose-50' },
        ].map((stat, i) => (
          <div key={i} className="premium-card group">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-1">{stat.label}</p>
                <p className="text-3xl font-black text-slate-900">{stat.value}</p>
              </div>
              <div className={`${stat.bg} ${stat.color} p-4 rounded-2xl transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <span className="flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">
                <TrendingUp className="h-3 w-3 mr-1" /> +12%
              </span>
              <span className="text-xs text-slate-400 font-medium tracking-tight">vs el mes pasado</span>
            </div>
          </div>
        ))}
      </div>

      {/* Activity Table */}
      <div className="premium-card !p-0 overflow-hidden border-none shadow-xl bg-white">
        <div className="p-8 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">Próximos Turnos</h2>
            <p className="text-sm font-medium text-slate-500">Listado actualizado en tiempo real</p>
          </div>
          <Button variant="ghost" className="text-xs font-bold uppercase tracking-widest">
            Ver Todos
          </Button>
        </div>
        <div className="p-4">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
              <p className="text-slate-400 font-medium animate-pulse">Sincronizando datos...</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-50">
              {appointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-2xl transition-colors hover:bg-slate-50/80 cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 font-bold group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                      {appointment.patient_name[0]}
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
                      <p className="text-sm font-black text-slate-900">{formatTime(appointment.date)}</p>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Hoy</p>
                    </div>
                    <span
                      className={`px-3 py-1 text-[10px] font-black uppercase tracking-widest rounded-lg shadow-sm ${getStatusBadgeClass(
                        appointment.status
                      )}`}
                    >
                      {appointment.status === 'confirmed' ? 'Confirmado' :
                        appointment.status === 'pending' ? 'Pendiente' :
                          appointment.status === 'completed' ? 'Completado' : appointment.status}
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
