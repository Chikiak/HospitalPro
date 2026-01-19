import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import RegisterStep2 from './pages/RegisterStep2'
import Dashboard from './pages/Dashboard'
import NewAppointment from './pages/appointments/NewAppointment'
import MainLayout from './layouts/MainLayout'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Register />} />
          <Route path="/registro/paso2" element={<RegisterStep2 />} />
          <Route
            path="/"
            element={
              <MainLayout>
                <Dashboard />
              </MainLayout>
            }
          />
          <Route
            path="/appointments/new"
            element={
              <MainLayout>
                <NewAppointment />
              </MainLayout>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
