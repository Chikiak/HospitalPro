import { Users, Calendar, Clock, TrendingUp } from 'lucide-react'

export default function Dashboard() {
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
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-slate-100">
              <div>
                <p className="font-medium text-slate-900">Juan Pérez</p>
                <p className="text-sm text-slate-600">Consulta General - Dr. García</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-900">10:30 AM</p>
                <span className="inline-block px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">
                  Confirmado
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-slate-100">
              <div>
                <p className="font-medium text-slate-900">María González</p>
                <p className="text-sm text-slate-600">Cardiología - Dra. Rodríguez</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-900">11:00 AM</p>
                <span className="inline-block px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700">
                  Pendiente
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-slate-900">Carlos Martínez</p>
                <p className="text-sm text-slate-600">Traumatología - Dr. López</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-900">11:30 AM</p>
                <span className="inline-block px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">
                  Confirmado
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
