import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import api from '../lib/api'

interface User {
  id: number
  dni: string
  full_name: string
  role: 'patient' | 'doctor' | 'admin'
  is_active: boolean
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (dni: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
}

interface RegisterData {
  dni: string
  password: string
  full_name: string
  role?: 'patient' | 'doctor' | 'admin'
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    // Load user from localStorage on mount
    const storedUser = localStorage.getItem('user')
    const token = localStorage.getItem('access_token')

    if (storedUser && token) {
      try {
        return JSON.parse(storedUser)
      } catch (error) {
        console.error('Failed to parse stored user:', error)
        localStorage.removeItem('user')
        localStorage.removeItem('access_token')
      }
    }
    return null
  })
  const [isLoading, setIsLoading] = useState(false)

  const login = async (dni: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await api.post('/auth/login/access-token', {
        dni,
        password,
      })

      const { access_token } = response.data

      // Store token
      localStorage.setItem('access_token', access_token)

      // TODO: Ideally, the backend should return user profile in login response
      // or provide a /me endpoint to fetch user info after login.
      // For now, we create a minimal user object with available data.
      const userProfile: User = {
        id: 0,
        dni,
        full_name: 'Usuario',
        role: 'patient',
        is_active: true,
      }

      localStorage.setItem('user', JSON.stringify(userProfile))
      setUser(userProfile)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (data: RegisterData) => {
    setIsLoading(true)
    try {
      await api.post('/auth/users/register', {
        dni: data.dni,
        password: data.password,
        full_name: data.full_name,
        role: data.role || 'patient',
      })

      // After successful registration, automatically log in
      await login(data.dni, data.password)
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
