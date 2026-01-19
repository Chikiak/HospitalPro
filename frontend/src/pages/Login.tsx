import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { User, Briefcase } from 'lucide-react'
import AuthLayout from '../layouts/AuthLayout'
import { useAuth } from '../context/AuthContext'
import Tabs from '../components/ui/Tabs'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import Alert from '../components/ui/Alert'

// Schemas for validation
const patientLoginSchema = z.object({
  dni: z
    .string()
    .min(1, 'El DNI es requerido')
    .regex(/^\d{11}$/, 'El DNI debe tener exactamente 11 dígitos'),
  password: z.string().min(1, 'La contraseña es requerida'),
})

const staffLoginSchema = z.object({
  password: z.string().min(1, 'La contraseña es requerida'),
})

type PatientLoginData = z.infer<typeof patientLoginSchema>
type StaffLoginData = z.infer<typeof staffLoginSchema>

type LoginMode = 'patient' | 'staff'

export default function Login() {
  const { login, staffLogin } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<LoginMode>('patient')

  // Patient form
  const patientForm = useForm<PatientLoginData>({
    resolver: zodResolver(patientLoginSchema),
  })

  // Staff form
  const staffForm = useForm<StaffLoginData>({
    resolver: zodResolver(staffLoginSchema),
  })

  const handlePatientLogin = async (data: PatientLoginData) => {
    try {
      setError(null)
      await login(data.dni, data.password)
      navigate('/')
    } catch (err) {
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error.response?.status === 401) {
        setError('DNI o contraseña incorrectos. Por favor, intente nuevamente.')
      } else if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Error al iniciar sesión. Por favor, intente nuevamente.')
      }
      console.error('Login error:', err)
    }
  }

  const handleStaffLogin = async (data: StaffLoginData) => {
    try {
      setError(null)
      await staffLogin(data.password)
      navigate('/')
    } catch (err) {
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error.response?.status === 401) {
        setError('Contraseña incorrecta. Por favor, intente nuevamente.')
      } else if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Error al iniciar sesión. Por favor, intente nuevamente.')
      }
      console.error('Staff login error:', err)
    }
  }

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId as LoginMode)
    setError(null)
    // Reset both forms when switching tabs
    patientForm.reset()
    staffForm.reset()
  }

  const tabs = [
    { id: 'patient', label: 'Paciente', icon: <User className="h-4 w-4" /> },
    { id: 'staff', label: 'Personal', icon: <Briefcase className="h-4 w-4" /> },
  ]

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Iniciar Sesión</h2>
          <p className="text-slate-600">Ingrese sus credenciales para acceder al sistema</p>
        </div>

        <Tabs tabs={tabs} activeTab={activeTab} onTabChange={handleTabChange} />

        {error && (
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Patient Login Form */}
        {activeTab === 'patient' && (
          <div
            key="patient-form"
            className="animate-fade-in-right"
            role="tabpanel"
            id="tabpanel-patient"
          >
            <form onSubmit={patientForm.handleSubmit(handlePatientLogin)} className="space-y-4">
              <Input
                {...patientForm.register('dni')}
                label="DNI"
                type="text"
                placeholder="Ingrese su DNI"
                error={patientForm.formState.errors.dni?.message}
                autoComplete="username"
              />

              <Input
                {...patientForm.register('password')}
                label="Contraseña"
                type="password"
                placeholder="Ingrese su contraseña"
                error={patientForm.formState.errors.password?.message}
                autoComplete="current-password"
              />

              <Button
                type="submit"
                isLoading={patientForm.formState.isSubmitting}
                className="w-full"
              >
                Iniciar Sesión
              </Button>
            </form>
          </div>
        )}

        {/* Staff Login Form */}
        {activeTab === 'staff' && (
          <div
            key="staff-form"
            className="animate-fade-in-left"
            role="tabpanel"
            id="tabpanel-staff"
          >
            <form onSubmit={staffForm.handleSubmit(handleStaffLogin)} className="space-y-4">
              <Input
                {...staffForm.register('password')}
                label="Contraseña del Personal"
                type="password"
                placeholder="Ingrese la contraseña del personal"
                error={staffForm.formState.errors.password?.message}
                autoComplete="current-password"
              />

              <Button
                type="submit"
                isLoading={staffForm.formState.isSubmitting}
                className="w-full"
              >
                Acceder como Personal
              </Button>
            </form>
          </div>
        )}

        {activeTab === 'patient' && (
          <div className="text-center text-sm text-slate-600">
            ¿No tiene una cuenta?{' '}
            <Link to="/registro" className="font-medium text-teal-700 hover:text-teal-600">
              Registrarse ahora
            </Link>
          </div>
        )}
      </div>
    </AuthLayout>
  )
}
