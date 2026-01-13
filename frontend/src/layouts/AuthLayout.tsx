import { type ReactNode } from 'react'
import { HeartPulse } from 'lucide-react'

interface AuthLayoutProps {
  children: ReactNode
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Left side - Image/Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-teal-700 p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 text-white">
            <div className="bg-white/10 p-3 rounded-lg">
              <HeartPulse className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">HospitalPro</h1>
              <p className="text-sm text-teal-100">Sistema de Gestión de Turnos</p>
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          <h2 className="text-3xl font-bold text-white leading-tight">
            Gestión eficiente de turnos médicos
          </h2>
          <p className="text-teal-100 text-lg">
            Simplifica la administración de consultas y mejora la experiencia de tus pacientes.
          </p>
        </div>

        <div className="text-teal-200 text-sm">
          © 2026 HospitalPro. Todos los derechos reservados.
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 mb-8">
            <div className="bg-teal-700 p-3 rounded-lg">
              <HeartPulse className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">HospitalPro</h1>
          </div>

          {children}
        </div>
      </div>
    </div>
  )
}
