/// <reference types="vite/client" />
import axios from 'axios'

// Get base URL from environment variable or use default
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
