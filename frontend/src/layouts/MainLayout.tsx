import { type ReactNode } from 'react'
import { HeartPulse, LayoutDashboard, Users, Calendar, Settings, LogOut, Bell, Search } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '../lib/utils'

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation()

  const navItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/' },
    { label: 'Pacientes', icon: Users, path: '/patients' },
    { label: 'Turnos', icon: Calendar, path: '/appointments/new' },
    { label: 'Configuración', icon: Settings, path: '/settings' },
  ]

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-72 bg-slate-900 flex-col shadow-2xl z-20">
        {/* Logo Section */}
        <div className="p-8">
          <div className="flex items-center gap-4 group cursor-pointer">
            <div className="bg-primary p-3 rounded-2xl shadow-lg shadow-primary/20 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3">
              <HeartPulse className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-black text-white uppercase tracking-tighter">HospitalPro</h1>
              <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest leading-none">Management v2.0</span>
            </div>
          </div>
        </div>

        {/* Navigation Section */}
        <nav className="flex-1 px-4 py-6">
          <div className="space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 font-bold text-sm",
                    isActive
                      ? "bg-primary text-white shadow-xl shadow-primary/20 translate-x-1"
                      : "text-slate-400 hover:text-white hover:bg-white/5"
                  )}
                >
                  <item.icon className={cn("h-5 w-5", isActive ? "text-white" : "text-slate-500")} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Bottom Section */}
        <div className="p-4 border-t border-white/5 space-y-4">
          <div className="bg-white/5 rounded-2xl p-4 space-y-3">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest text-center">Espacio de Almacenamiento</p>
            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full w-[65%] bg-primary rounded-full shadow-[0_0_10px_rgba(20,184,166,0.5)]"></div>
            </div>
          </div>
          <button className="flex items-center gap-4 px-5 py-4 rounded-2xl text-slate-400 font-bold text-sm hover:text-rose-400 hover:bg-rose-400/10 transition-all w-full">
            <LogOut className="h-5 w-5" />
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Modern Header */}
        <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 h-20 flex items-center px-8 z-10 shrink-0">
          <div className="flex-1 flex items-center justify-between">
            {/* Search Bar */}
            <div className="hidden md:flex items-center bg-slate-100 rounded-2xl px-4 py-2 w-96 group transition-all focus-within:ring-2 focus-within:ring-primary/20 focus-within:bg-white">
              <Search className="h-5 w-5 text-slate-400 mr-2 group-focus-within:text-primary transition-colors" />
              <input
                type="text"
                placeholder="Buscar pacientes, citas..."
                className="bg-transparent border-none outline-none text-sm font-medium w-full placeholder:text-slate-400"
              />
            </div>

            {/* Profile & Notifications */}
            <div className="flex items-center gap-6">
              <button className="relative p-2 text-slate-400 hover:text-primary hover:bg-slate-100 rounded-xl transition-all">
                <Bell className="h-6 w-6" />
                <span className="absolute top-2 right-2 h-2.5 w-2.5 bg-rose-500 border-2 border-white rounded-full animate-bounce"></span>
              </button>

              <div className="flex items-center gap-4 pl-6 border-l border-slate-200">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-black text-slate-900 leading-none">Dr. Adrian G.</p>
                  <p className="text-[10px] font-bold text-primary uppercase tracking-widest mt-1">Admin Principal</p>
                </div>
                <div className="h-12 w-12 rounded-2xl bg-primary text-white flex items-center justify-center font-black shadow-lg shadow-primary/20 cursor-pointer transition-transform hover:scale-110 active:scale-95">
                  AG
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content with custom scrollbar */}
        <main className="flex-1 overflow-y-auto p-8 scrollbar-hide">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
