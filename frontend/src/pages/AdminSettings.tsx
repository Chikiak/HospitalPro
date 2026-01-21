import { useState } from 'react'
import { Settings, ShieldCheck } from 'lucide-react'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import AdminScheduleManager from '../features/admin/AdminScheduleManager'




export default function AdminSettings() {
  const [adminPassword, setAdminPassword] = useState('')
  const [showAdminPrompt, setShowAdminPrompt] = useState(false)
  const [pendingAuthResolve, setPendingAuthResolve] = useState<((pass: string) => void) | null>(null)
  const [pendingAuthReject, setPendingAuthReject] = useState<((reason?: any) => void) | null>(null)

  // Auth provider pattern for child components
  const requestAdminPassword = (): Promise<string> => {
    return new Promise((resolve, reject) => {
      setPendingAuthResolve(() => resolve)
      setPendingAuthReject(() => reject)
      setShowAdminPrompt(true)
    })
  }

  const handleAdminAuth = () => {
    if (!adminPassword || !pendingAuthResolve) return
    pendingAuthResolve(adminPassword)
    setShowAdminPrompt(false)
    setAdminPassword('')
    setPendingAuthResolve(null)
    setPendingAuthReject(null)
  }

  const handleCancelAuth = () => {
    if (pendingAuthReject) pendingAuthReject("User cancelled")
    setShowAdminPrompt(false)
    setAdminPassword('')
    setPendingAuthResolve(null)
    setPendingAuthReject(null)
  }

  return (
    <div className="space-y-8 pb-20">
      {/* Admin Password Overlay */}
      {showAdminPrompt && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl p-8 shadow-2xl w-full max-w-md space-y-6 animate-fade-in-scale">
            <div className="text-center space-y-2">
              <div className="h-16 w-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mx-auto">
                <ShieldCheck size={32} />
              </div>
              <h3 className="text-2xl font-black text-slate-900">Autorización Admin</h3>
              <p className="text-slate-500 text-sm font-medium">Ingrese la contraseña de administrador para confirmar.</p>
            </div>

            <Input
              type="password"
              placeholder="Contraseña de Administrador"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              className="py-4 text-center text-xl tracking-widest"
              autoFocus
            />

            <div className="flex gap-4">
              <Button
                variant="outline"
                className="flex-1"
                onClick={handleCancelAuth}
              >
                CANCELAR
              </Button>
              <Button
                className="flex-1 shadow-lg shadow-primary/30"
                onClick={handleAdminAuth}
              >
                CONFIRMAR
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <h1 className="text-4xl font-black tracking-tight text-slate-900 flex items-center gap-3">
            <Settings className="h-10 w-10 text-primary" />
            Configuración
          </h1>
          <p className="text-slate-500 font-medium">Sistema de Gestión Hospitalaria</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <div className="space-y-6 lg:col-span-1">
          <div className="premium-card bg-slate-900 text-white p-6 space-y-4">
            <h3 className="font-bold uppercase tracking-widest text-xs opacity-70">Opciones</h3>
            <p className="text-sm font-medium">Gestione aquí las especialidades, horarios y configuraciones avanzadas del sistema.</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          <AdminScheduleManager adminPasswordProvider={requestAdminPassword} />
        </div>
      </div>
    </div>
  )
}
