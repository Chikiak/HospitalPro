/// <reference types="vite/client" />
import axios from 'axios'

// Get base URL from environment variable or use default
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Handler notified when a request fails with 401 so the auth layer (AuthContext)
// can sync its React state with localStorage. Registered by AuthProvider on mount.
let onUnauthorized: (() => void) | null = null

/**
 * Registra el handler invocado ante respuestas 401. Está pensado para que
 * AuthProvider lo llame una vez al montarse y así mantener sincronizado el
 * estado de autenticación de React con lo que queda en localStorage.
 */
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler
}

// Create axios instance with base configuration
const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add access token to headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('Unauthorized request (401). clearing session...');
      // Clear authentication data
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')

      // Notificar a la capa de auth para que el estado de React (user /
      // isAuthenticated) se vacíe junto con localStorage. Sin esto, la app
      // sigue actuando como autenticada sin token y entra en bucle de 401.
      onUnauthorized?.()

      // Redirect to login page ONLY if not already there to avoid redirect loops
      if (window.location.pathname !== '/login') {
        console.warn('Redirecting to login...');
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
