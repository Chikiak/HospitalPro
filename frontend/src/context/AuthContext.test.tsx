import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { useState, useEffect } from 'react'
import MockAdapter from 'axios-mock-adapter'
import api from '../lib/api'
import { AuthProvider, useAuth } from './AuthContext'

let mock: MockAdapter

let originalLocation: string

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
function TriggerUnauthorized() {
  const [status, setStatus] = useState<string>('idle')

  useEffect(() => {
    api.get('/appointments/categories').catch((err) => {
      setStatus(String(err.response?.status ?? 'unknown'))
    })
  }, [])

  return <div data-testid="trigger-status">{status}</div>
}

beforeEach(() => {
  mock = new MockAdapter(api)
  localStorage.clear()

  // Se anula la navegación real del interceptor (como en lib/api.test.ts)
  originalLocation = window.location.href
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete (window as any).location
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  window.location = { href: '', pathname: '/dashboard' } as any
})

afterEach(() => {
  mock.restore()
  localStorage.clear()
  Object.defineProperty(window, 'location', {
    value: { href: originalLocation },
    writable: true,
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

    // La petición disparada efectivamente recibe 401
    await waitFor(() => expect(screen.getByTestId('trigger-status')).toHaveTextContent('401'))

    // El estado de React se vació junto con localStorage
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false'))
    expect(screen.getByTestId('user-dni')).toHaveTextContent('null')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()

    // El interceptor mantiene su redirección a login (no estaba en /login)
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

    await waitFor(() => expect(screen.getByTestId('trigger-status')).toHaveTextContent('401'))
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false'))
    expect(screen.getByTestId('user-dni')).toHaveTextContent('null')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })
})
