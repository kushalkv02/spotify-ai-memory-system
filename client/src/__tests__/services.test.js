import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock localStorage in Node environment
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString() },
    clear: () => { store = {} },
    removeItem: (key) => { delete store[key] }
  }
})()

globalThis.localStorage = localStorageMock

import apiClient from '../services/apiClient.js'

describe('Client API Services', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('attaches authorization bearer token if token is present in localStorage', async () => {
    localStorage.setItem('reverie:token', 'test-jwt-token')
    
    const config = { headers: {} }
    const requestInterceptor = apiClient.interceptors.request.handlers[0].fulfilled
    const resultConfig = requestInterceptor(config)
    
    expect(resultConfig.headers.Authorization).toBe('Bearer test-jwt-token')
  })

  it('normalizes error messages from API response', async () => {
    const errorResponse = {
      response: {
        data: {
          detail: 'Unauthorized access'
        }
      }
    }
    
    const responseInterceptorError = apiClient.interceptors.response.handlers[0].rejected
    await expect(responseInterceptorError(errorResponse)).rejects.toThrow('Unauthorized access')
  })
})
