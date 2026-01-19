import { describe, it, expect, beforeEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import api from './api'

describe('API Client', () => {
  let mock: MockAdapter
  let originalLocation: string

  beforeEach(() => {
    // Setup mock adapter
    mock = new MockAdapter(api)
    
    // Clear localStorage
    localStorage.clear()
    
    // Save original location and create a mock
    originalLocation = window.location.href
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (window as any).location
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    window.location = { href: '' } as any
  })

  afterEach(() => {
    mock.restore()
    // Restore window.location
    Object.defineProperty(window, 'location', {
      value: { href: originalLocation },
      writable: true,
    })
  })

  it('exports an axios instance', () => {
    expect(api).toBeDefined()
    expect(api.defaults).toBeDefined()
    expect(api.defaults.baseURL).toBeDefined()
  })

  it('has correct Content-Type header', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json')
  })

  describe('Request Interceptor', () => {
    it('adds authorization header when token exists', async () => {
      const token = 'test-token-123'
      localStorage.setItem('access_token', token)
      
      mock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBe(`Bearer ${token}`)
        return [200, { success: true }]
      })

      await api.get('/test')
    })

    it('does not add authorization header when token does not exist', async () => {
      mock.onGet('/test').reply((config) => {
        expect(config.headers?.Authorization).toBeUndefined()
        return [200, { success: true }]
      })

      await api.get('/test')
    })
  })

  describe('Response Interceptor - 401 Handling', () => {
    it('clears storage and redirects on 401 error', async () => {
      localStorage.setItem('access_token', 'test-token')
      localStorage.setItem('user', JSON.stringify({ id: 1, name: 'Test' }))

      mock.onGet('/protected').reply(401)

      try {
        await api.get('/protected')
        // Should not reach here
        expect(true).toBe(false)
      } catch {
        // Expected to throw
      }

      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
      expect(window.location.href).toBe('/login')
    })

    it('does not redirect on non-401 errors', async () => {
      localStorage.setItem('access_token', 'test-token')
      
      mock.onGet('/error').reply(500)

      try {
        await api.get('/error')
        // Should not reach here
        expect(true).toBe(false)
      } catch {
        // Expected to throw
      }

      expect(localStorage.getItem('access_token')).toBe('test-token')
      expect(window.location.href).toBe('')
    })

    it('returns response on successful request', async () => {
      mock.onGet('/success').reply(200, { data: 'test' })

      const response = await api.get('/success')

      expect(response.data).toEqual({ data: 'test' })
      expect(response.status).toBe(200)
    })
  })
})
