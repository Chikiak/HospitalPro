import { useState } from 'react'
import { Plus, UserCheck, Search, ShieldAlert } from 'lucide-react'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import api from '../../lib/api'

interface AdminDniManagerProps {
    adminPasswordProvider: () => Promise<string>
}

export default function AdminDniManager({ adminPasswordProvider }: AdminDniManagerProps) {
    const [dni, setDni] = useState('')
    const [fullName, setFullName] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null)

    const handleAddDni = async () => {
        if (!dni) return
        
        try {
            setIsLoading(true)
            setMessage(null)
            
            const pass = await adminPasswordProvider()
            
            await api.post('/admin/allowed-persons', {
                admin_password: pass,
                dni: dni,
                full_name: fullName || null
            })
            
            setMessage({ text: `DNI ${dni} agregado correctamente.`, type: 'success' })
            setDni('')
            setFullName('')
        } catch (error) {
            console.error("Error adding DNI", error)
            const err = error as { response?: { data?: { detail?: string } } }
            const detail = err.response?.data?.detail || "Error al agregar DNI"
            setMessage({ text: detail, type: 'error' })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="premium-card p-6 space-y-6">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 bg-primary/10 text-primary rounded-xl flex items-center justify-center">
                        <UserCheck size={20} />
                    </div>
                    <div>
                        <h3 className="text-xl font-black text-slate-800">Autorizar Nuevo Registro</h3>
                        <p className="text-slate-500 text-sm font-medium">Agregue un DNI a la lista blanca para permitir su registro como paciente.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-1">
                        <label className="text-xs font-bold uppercase text-slate-500 ml-1">DNI (Obligatorio)</label>
                        <Input
                            placeholder="Ej. 12345678"
                            value={dni}
                            onChange={(e) => setDni(e.target.value)}
                            className="h-12 text-lg font-bold"
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs font-bold uppercase text-slate-500 ml-1">Nombre Completo (Opcional)</label>
                        <Input
                            placeholder="Ej. Juan Pérez"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            className="h-12"
                        />
                    </div>
                </div>

                {message && (
                    <div className={`p-4 rounded-2xl flex items-center gap-3 text-sm font-bold border-2 ${
                        message.type === 'success' 
                        ? 'bg-emerald-50 border-emerald-100 text-emerald-700' 
                        : 'bg-rose-50 border-rose-100 text-rose-700'
                    }`}>
                        {message.type === 'error' && <ShieldAlert size={18} />}
                        {message.text}
                    </div>
                )}

                <div className="flex justify-end pt-2">
                    <Button 
                        onClick={handleAddDni} 
                        isLoading={isLoading}
                        disabled={!dni}
                        className="px-8 h-12 shadow-lg shadow-primary/30"
                    >
                        <Plus size={20} className="mr-2" />
                        AGREGAR DNI
                    </Button>
                </div>
            </div>

            {/* Hint Card */}
            <div className="bg-slate-900 text-slate-400 rounded-3xl p-6 flex gap-4 items-start border-4 border-slate-800">
                <div className="h-10 w-10 bg-white/5 rounded-xl flex items-center justify-center text-white flex-shrink-0">
                    <Search size={20} />
                </div>
                <div className="space-y-1">
                    <p className="text-white font-bold">Nota de Seguridad</p>
                    <p className="text-sm">Esta operación requiere confirmación con contraseña de administrador debido a que otorga acceso al sistema de registro de pacientes.</p>
                </div>
            </div>
        </div>
    )
}
