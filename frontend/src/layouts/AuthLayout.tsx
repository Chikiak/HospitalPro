import { type ReactNode } from 'react'
import { HeartPulse } from 'lucide-react'
// @ts-ignore
import loginBg from '../assets/login_bg.png'

interface AuthLayoutProps {
  children: ReactNode
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen relative flex items-center justify-center overflow-hidden font-sans">
      {/* Background Image with Overlay */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center transition-transform duration-1000 md:animate-slow-zoom"
        style={{ backgroundImage: `url(${loginBg})` }}
      >
        <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-5xl px-4 flex flex-col md:flex-row items-stretch gap-8">

        {/* Left Aspect - Branding & Value Prop */}
        <div className="hidden lg:flex flex-1 flex-col justify-between p-8 text-white lg:animate-fade-in-left">
          <div className="flex items-center gap-4">
            <div className="glass p-4 rounded-2xl bg-white/20">
              <HeartPulse className="h-10 w-10 text-white fill-white/10" />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tighter uppercase">HospitalPro</h1>
              <p className="text-sm font-medium text-emerald-300">Gestión de Atención Avanzada</p>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-5xl font-bold leading-tight tracking-tight">
              Reinventando la <br /> Gestión de <br />
              <span className="text-emerald-400">Salud.</span>
            </h2>
            <p className="text-slate-200 text-lg max-w-sm">
              Experimente la próxima generación de organización médica profesional. Simplificada, intuitiva y notablemente eficiente.
            </p>
          </div>

          <div className="text-slate-300 text-xs font-medium uppercase tracking-widest">
            Establecido 2026 • Experiencia Premium
          </div>
        </div>

        {/* Right Aspect - Form Container */}
        <div className="flex-1 flex items-center justify-center lg:animate-fade-in-right">
          <div className="premium-card w-full max-w-md backdrop-blur-2xl bg-white/80 border-white/40 shadow-2xl">
            {/* Mobile Logo Visibility */}
            <div className="lg:hidden flex flex-col items-center gap-2 mb-8">
              <div className="bg-primary p-3 rounded-2xl shadow-lg">
                <HeartPulse className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-2xl font-black uppercase tracking-tight text-slate-900">HospitalPro</h1>
            </div>

            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
