import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import api from '../lib/axios'

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
  
  const login = async (dni: string, password: string) => {
    try {
      const response = await api.post('/auth/login/access-token', {
        dni,
        password,
      })

      const { access_token } = response.data

      // Store token
      localStorage.setItem('access_token', access_token)

      // Fetch user profile (we need to decode token or fetch user info)
      // For now, we'll create a basic user object from the login response
      // In a real scenario, you might want to fetch the user profile from a separate endpoint
      const userProfile: User = {
        id: 0, // This should come from backend
        dni,
        full_name: 'User', // This should come from backend
        role: 'patient',
        is_active: true,
      }

      localStorage.setItem('user', JSON.stringify(userProfile))
      setUser(userProfile)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const register = async (data: RegisterData) => {
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
    isLoading: false,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
