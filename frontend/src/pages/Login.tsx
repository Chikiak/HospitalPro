import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import AuthLayout from '../layouts/AuthLayout'
import LoginForm from '../features/auth/components/LoginForm'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const handleLogin = async (data: { dni: string; password: string }) => {
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
      console.error('Login error:', err)
    }
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Iniciar Sesión</h2>
          <p className="text-slate-600">Ingrese sus credenciales para acceder al sistema</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        <LoginForm onSubmit={handleLogin} />

        <div className="text-center text-sm text-slate-600">
          ¿No tiene una cuenta?{' '}
          <Link to="/registro" className="font-medium text-teal-700 hover:text-teal-600">
            Registrarse ahora
          </Link>
        </div>
      </div>
    </AuthLayout>
  )
}
