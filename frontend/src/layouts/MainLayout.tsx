import { type ReactNode } from 'react'
import { HeartPulse, LayoutDashboard, Users, Calendar, Settings, LogOut } from 'lucide-react'
import { Link } from 'react-router-dom'

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="bg-teal-700 p-2 rounded-lg">
              <HeartPulse className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">HospitalPro</h1>
              <p className="text-xs text-slate-500">Gestión de Turnos</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            <li>
              <Link
                to="/"
                className="flex items-center gap-3 px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <LayoutDashboard className="h-5 w-5" />
                <span>Dashboard</span>
              </Link>
            </li>
            <li>
              <Link
                to="#"
                className="flex items-center gap-3 px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <Users className="h-5 w-5" />
                <span>Pacientes</span>
              </Link>
            </li>
            <li>
              <Link
                to="#"
                className="flex items-center gap-3 px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <Calendar className="h-5 w-5" />
                <span>Turnos</span>
              </Link>
            </li>
            <li>
              <Link
                to="#"
                className="flex items-center gap-3 px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <Settings className="h-5 w-5" />
                <span>Configuración</span>
              </Link>
            </li>
          </ul>
        </nav>

        {/* User section */}
        <div className="p-4 border-t border-slate-200">
          <button className="flex items-center gap-3 px-4 py-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors w-full">
            <LogOut className="h-5 w-5" />
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Top navbar */}
        <header className="bg-white border-b border-slate-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900">Bienvenido</h2>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-slate-900">Usuario</p>
                <p className="text-xs text-slate-500">Administrador</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-teal-700 flex items-center justify-center text-white font-semibold">
                U
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
