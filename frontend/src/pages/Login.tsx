import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { UserCircle, Briefcase } from 'lucide-react'
import AuthLayout from '../layouts/AuthLayout'
import LoginForm from '../features/auth/components/LoginForm'
import StaffLoginForm from '../features/auth/components/StaffLoginForm'
import Tabs from '../components/ui/Tabs'
import Alert from '../components/ui/Alert'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, staffLogin } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const handlePatientLogin = async (data: { dni: string; password: string }) => {
    try {
      setError(null)
      await login(data.dni, data.password)
      // Redirect to dashboard on successful login
      navigate('/')
    } catch (err) {
      // Handle 401 and other errors gracefully
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error.response?.status === 401) {
        setError('DNI o contraseña incorrectos. Por favor, intente nuevamente.')
      } else if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Error al iniciar sesión. Por favor, intente nuevamente.')
      }
      console.error('Patient login error:', err)
    }
  }

  const handleStaffLogin = async (data: { password: string }) => {
    try {
      setError(null)
      await staffLogin(data.password)
      // Redirect to dashboard on successful login
      navigate('/')
    } catch (err) {
      // Handle 401 and other errors gracefully
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

  const handleTabChange = () => {
    setError(null) // Clear errors when switching tabs
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Iniciar Sesión</h2>
          <p className="text-slate-600">Seleccione su tipo de usuario e ingrese sus credenciales</p>
        </div>

        {error && (
          <Alert variant="error">
            {error}
          </Alert>
        )}

        <Tabs
          tabs={[
            { id: 'patient', label: 'Paciente', icon: <UserCircle size={18} /> },
            { id: 'staff', label: 'Personal', icon: <Briefcase size={18} /> },
          ]}
          defaultTab="patient"
          onTabChange={handleTabChange}
        >
          {(activeTab) => (
            <>
              {activeTab === 'patient' && (
                <>
                  <LoginForm onSubmit={handlePatientLogin} />
                  <div className="text-center text-sm text-slate-600 mt-4">
                    ¿No tiene una cuenta?{' '}
                    <Link to="/registro" className="font-medium text-teal-700 hover:text-teal-600">
                      Registrarse ahora
                    </Link>
                  </div>
                </>
              )}
              {activeTab === 'staff' && (
                <StaffLoginForm onSubmit={handleStaffLogin} />
              )}
            </>
          )}
        </Tabs>
      </div>
    </AuthLayout>
  )
}
