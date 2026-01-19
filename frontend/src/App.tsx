import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { AuthGuard } from './components/AuthGuard'
import { RoleGuard } from './components/RoleGuard'
import Login from './pages/Login'
import Register from './pages/Register'
import RegisterStep2 from './pages/RegisterStep2'
import Dashboard from './pages/Dashboard'
import NewAppointment from './pages/appointments/NewAppointment'
import AdminSettings from './pages/AdminSettings'
import MainLayout from './layouts/MainLayout'
import AppointmentSearch from './features/appointments/AppointmentSearch'

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
          <Route
            path="/appointments/search"
            element={
              <RoleGuard allowedRoles={['patient']}>
                <MainLayout>
                  <AppointmentSearch />
                </MainLayout>
              </RoleGuard>
            }
          />

          {/* Private routes - Staff only (admin, doctor, staff roles) */}
          <Route
            path="/admin/settings"
            element={
              <RoleGuard allowedRoles={['admin', 'doctor', 'staff']}>
                <MainLayout>
                  <AdminSettings />
                </MainLayout>
              </RoleGuard>
            }
          />
          <Route
            path="/admin/*"
            element={
              <RoleGuard allowedRoles={['admin', 'doctor', 'staff']}>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </RoleGuard>
            }
          />
          <Route
            path="/staff/*"
            element={
              <RoleGuard allowedRoles={['admin', 'doctor', 'staff']}>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </RoleGuard>
            }
          />

          {/* Private route - Any authenticated user can access profile */}
          <Route
            path="/profile"
            element={
              <AuthGuard>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </AuthGuard>
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
