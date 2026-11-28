import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { useState } from 'react'
import MockAdapter from 'axios-mock-adapter'
import api from '../lib/api'
import { AuthProvider, useAuth } from './AuthContext'

let mock: MockAdapter

// Referencia completa del objeto window.location original (no solo su href).
const originalLocation = window.location

function AuthStatus() {
  const { user, isAuthenticated } = useAuth()
  return (
    <div>
      <span data-testid="is-authenticated">{String(isAuthenticated)}</span>
      <span data-testid="user-dni">{user?.dni ?? 'null'}</span>
    </div>
  )
}

// Dispara una petición que termina en 401 y expone el estado recibido.
// El disparo lo provoca el usuario mediante un botón (no un useEffect al montar),
// así el test comprueba primero el estado autenticado y luego la transición.
function TriggerUnauthorized() {
  const [status, setStatus] = useState<string>('idle')

  const trigger = () => {
    api.get('/appointments/categories').catch((err) => {
      setStatus(String(err.response?.status ?? 'unknown'))
    })
  }

  return (
    <div>
      <button type="button" onClick={trigger} data-testid="trigger-btn">
        Disparar 401
      </button>
      <div data-testid="trigger-status">{status}</div>
    </div>
  )
}

beforeEach(() => {
  mock = new MockAdapter(api)
  localStorage.clear()

  // Se anula la navegación real del interceptor (como en lib/api.test.ts)
  Object.defineProperty(window, 'location', {
    value: { href: '', pathname: '/dashboard' },
    writable: true,
    configurable: true,
  })
})

afterEach(() => {
  mock.restore()
  localStorage.clear()
  Object.defineProperty(window, 'location', {
    value: originalLocation,
    writable: true,
    configurable: true,
  })
})

describe('AuthContext - sincronización de estado ante 401', () => {
  it('vacía el estado de React (user/isAuthenticated) cuando una petición recibe 401', async () => {
    localStorage.setItem('access_token', 'test-token')
    localStorage.setItem(
      'user',
      JSON.stringify({ id: 1, dni: '12345678', full_name: 'Test User', role: 'patient', is_active: true }),
    )

    mock.onGet('/appointments/categories').reply(401)

    render(
      <AuthProvider>
        <AuthStatus />
        <TriggerUnauthorized />
      </AuthProvider>,
    )

    // Estado inicial: autenticado antes de disparar nada
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
    expect(screen.getByTestId('user-dni')).toHaveTextContent('12345678')

    // Disparar el 401 y esperar la transición determinista
    fireEvent.click(screen.getByTestId('trigger-btn'))
    await waitFor(() => expect(screen.getByTestId('trigger-status')).toHaveTextContent('401'))

    // El estado de React se vació junto con localStorage
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false'))
    expect(screen.getByTestId('user-dni')).toHaveTextContent('null')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()

    // El interceptor redirige a login (no estaba en /login)
    expect(window.location.href).toBe('/login')
  })

  it('no redirige cuando ya se está en /login, pero sí vacía el estado de auth', async () => {
    localStorage.setItem('access_token', 'test-token')
    localStorage.setItem('user', JSON.stringify({ id: 1, dni: '12345678', full_name: 'Test User', role: 'patient', is_active: true }))

    // pathname '/login' evita el window.location.href del interceptor
    window.location.pathname = '/login'

    mock.onGet('/appointments/categories').reply(401)

    render(
      <AuthProvider>
        <AuthStatus />
        <TriggerUnauthorized />
      </AuthProvider>,
    )

    // Estado inicial: autenticado antes de disparar nada
    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
    expect(screen.getByTestId('user-dni')).toHaveTextContent('12345678')

    // Disparar el 401 y esperar la transición determinista
    fireEvent.click(screen.getByTestId('trigger-btn'))
    await waitFor(() => expect(screen.getByTestId('trigger-status')).toHaveTextContent('401'))
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false'))
    expect(screen.getByTestId('user-dni')).toHaveTextContent('null')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()

    // El interceptor no cambió window.location.href al estar en /login
    expect(window.location.href).toBe('')
  })
})
