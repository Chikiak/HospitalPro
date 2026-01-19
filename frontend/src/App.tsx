import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { AuthGuard } from './components/AuthGuard'
import { RoleGuard } from './components/RoleGuard'
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
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Register />} />
          <Route path="/registro/paso2" element={<RegisterStep2 />} />

          {/* Private routes - Any authenticated user */}
          <Route
            path="/"
            element={
              <AuthGuard>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </AuthGuard>
            }
          />
          <Route
            path="/dashboard"
            element={
              <AuthGuard>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </AuthGuard>
            }
          />

          {/* Private routes - Patient only */}
          <Route
            path="/appointments/new"
            element={
              <RoleGuard allowedRoles={['patient']}>
                <MainLayout>
                  <NewAppointment />
                </MainLayout>
              </RoleGuard>
            }
          />

          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
