import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Activity, HeartPulse } from 'lucide-react'

function App() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/health')
      return response.data
    }
  })

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg overflow-hidden md:max-w-2xl">
        <div className="p-8">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-blue-100 p-3 rounded-full">
              <HeartPulse className="h-10 w-10 text-blue-600" />
            </div>
          </div>
          <div className="uppercase tracking-wide text-sm text-blue-500 font-semibold text-center mb-1">
            Sistema de Gestión de Turnos
          </div>
          <h1 className="block mt-1 text-3xl leading-tight font-bold text-gray-900 text-center">
            HospitalPro
          </h1>
          <p className="mt-4 text-gray-500 text-center">
            Inicialización del proyecto completada.
          </p>

          <div className="mt-8 border-t pt-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center justify-center gap-2">
              <Activity className="h-5 w-5" />
              Estado del Sistema
            </h2>

            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center bg-gray-50 p-3 rounded-lg">
                <span className="text-gray-600">Frontend (React + Vite)</span>
                <span className="px-2 py-1 text-xs font-semibold text-green-700 bg-green-100 rounded-full">Active</span>
              </div>

              <div className="flex justify-between items-center bg-gray-50 p-3 rounded-lg">
                <span className="text-gray-600">Backend API</span>
                {isLoading ? (
                  <span className="px-2 py-1 text-xs font-semibold text-yellow-700 bg-yellow-100 rounded-full">Connecting...</span>
                ) : error ? (
                  <span className="px-2 py-1 text-xs font-semibold text-red-700 bg-red-100 rounded-full">Error</span>
                ) : (
                  <span className="px-2 py-1 text-xs font-semibold text-green-700 bg-green-100 rounded-full">
                    {data?.status === 'ok' ? 'Online' : 'Unexpected Response'}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
