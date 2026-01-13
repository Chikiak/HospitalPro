import AuthLayout from '../layouts/AuthLayout'
import LoginForm from '../features/auth/components/LoginForm'

export default function Login() {
  const handleLogin = async (data: { dni: string; password: string }) => {
    // TODO: Implement actual authentication logic
    console.log('Login attempt:', data)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // TODO: Handle success/error
    alert(`Login successful for DNI: ${data.dni}`)
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Iniciar Sesión</h2>
          <p className="text-slate-600">Ingrese sus credenciales para acceder al sistema</p>
        </div>
        
        <LoginForm onSubmit={handleLogin} />
        
        <div className="text-center text-sm text-slate-600">
          ¿Olvidó su contraseña?{' '}
          <a href="#" className="font-medium text-teal-700 hover:text-teal-600">
            Recuperar acceso
          </a>
        </div>
      </div>
    </AuthLayout>
  )
}
