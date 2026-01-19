import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import AuthLayout from '../layouts/AuthLayout'
import RegisterForm from '../features/auth/components/RegisterForm'
import { useAuth } from '../context/AuthContext'

export default function Register() {
    const { register } = useAuth()
    const navigate = useNavigate()
    const [error, setError] = useState<string | null>(null)

    const handleRegister = async (data: { dni: string; password: string; full_name: string }) => {
        try {
            setError(null)
            await register(data)
            // Redirect to step 2 (medical history) after successful registration
            navigate('/registro/paso2')
        } catch (err) {
            const error = err as { response?: { data?: { detail?: string } } }
            if (error.response?.data?.detail) {
                setError(error.response.data.detail)
            } else {
                setError('Error al registrarse. Por favor, intente nuevamente.')
            }
            console.error('Registration error:', err)
        }
    }

    return (
        <AuthLayout>
            <div className="space-y-6">
                <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-slate-900">Crear Cuenta</h2>
                    <p className="text-slate-600">Complete sus datos para registrarse en el sistema</p>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                        {error}
                    </div>
                )}

                <RegisterForm onSubmit={handleRegister} />

                <div className="text-center text-sm text-slate-600">
                    ¿Ya tiene una cuenta?{' '}
                    <Link to="/login" className="font-medium text-teal-700 hover:text-teal-600">
                        Iniciar sesión
                    </Link>
                </div>
            </div>
        </AuthLayout>
    )
}
