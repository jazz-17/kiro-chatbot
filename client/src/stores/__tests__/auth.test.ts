import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should initialize with null user and token', () => {
      const authStore = useAuthStore()
      
      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.isLoading).toBe(false)
      expect(authStore.error).toBeNull()
    })

    it('should load token from localStorage on initialization', () => {
      mockLocalStorage.getItem.mockReturnValue('stored-token')
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          createdAt: new Date(),
        }),
      })

      const authStore = useAuthStore()
      
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('auth_token')
      expect(authStore.token).toBe('stored-token')
    })
  })

  describe('Computed Properties', () => {
    it('should compute isAuthenticated correctly', () => {
      const authStore = useAuthStore()
      
      expect(authStore.isAuthenticated).toBe(false)
      
      // Set user and token
      authStore.setUser({
        id: '1',
        email: 'test@example.com',
        createdAt: new Date(),
      })
      authStore.setToken('test-token')
      
      expect(authStore.isAuthenticated).toBe(true)
    })

    it('should compute user display properties', () => {
      const authStore = useAuthStore()
      const user = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        createdAt: new Date(),
      }
      
      authStore.setUser(user)
      
      expect(authStore.userEmail).toBe('test@example.com')
      expect(authStore.userName).toBe('Test User')
    })

    it('should fallback to email for userName when name is not provided', () => {
      const authStore = useAuthStore()
      const user = {
        id: '1',
        email: 'test@example.com',
        createdAt: new Date(),
      }
      
      authStore.setUser(user)
      
      expect(authStore.userName).toBe('test@example.com')
    })
  })

  describe('Login', () => {
    it('should login successfully', async () => {
      const authStore = useAuthStore()
      const mockResponse = {
        token: 'auth-token',
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          createdAt: new Date(),
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await authStore.login('test@example.com', 'password')

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password',
        }),
      })

      expect(result).toEqual(mockResponse)
      expect(authStore.token).toBe('auth-token')
      expect(authStore.user).toEqual(mockResponse.user)
      expect(authStore.isAuthenticated).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'auth-token')
    })

    it('should handle login failure', async () => {
      const authStore = useAuthStore()

      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ message: 'Invalid credentials' }),
      })

      await expect(authStore.login('test@example.com', 'wrong-password'))
        .rejects.toThrow('Invalid credentials')

      expect(authStore.error).toBe('Invalid credentials')
      expect(authStore.isAuthenticated).toBe(false)
    })

    it('should set loading state during login', async () => {
      const authStore = useAuthStore()

      mockFetch.mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ token: 'token', user: {} }),
        }), 100))
      )

      const loginPromise = authStore.login('test@example.com', 'password')
      
      expect(authStore.isLoading).toBe(true)
      
      await loginPromise
      
      expect(authStore.isLoading).toBe(false)
    })
  })

  describe('Register', () => {
    it('should register successfully', async () => {
      const authStore = useAuthStore()
      const mockResponse = {
        token: 'auth-token',
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          createdAt: new Date(),
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await authStore.register('test@example.com', 'password', 'Test User')

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password',
          name: 'Test User',
        }),
      })

      expect(result).toEqual(mockResponse)
      expect(authStore.isAuthenticated).toBe(true)
    })
  })

  describe('Logout', () => {
    it('should logout successfully', async () => {
      const authStore = useAuthStore()
      
      // Set initial authenticated state
      authStore.setToken('auth-token')
      authStore.setUser({
        id: '1',
        email: 'test@example.com',
        createdAt: new Date(),
      })

      mockFetch.mockResolvedValueOnce({
        ok: true,
      })

      await authStore.logout()

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer auth-token',
        },
      })

      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token')
    })

    it('should clear local state even if API call fails', async () => {
      const authStore = useAuthStore()
      
      authStore.setToken('auth-token')
      authStore.setUser({
        id: '1',
        email: 'test@example.com',
        createdAt: new Date(),
      })

      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await authStore.logout()

      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
    })
  })

  describe('Fetch Current User', () => {
    it('should fetch current user successfully', async () => {
      const authStore = useAuthStore()
      const mockUser = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        createdAt: new Date(),
      }

      authStore.setToken('auth-token')
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser),
      })

      const result = await authStore.fetchCurrentUser()

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/me', {
        headers: {
          'Authorization': 'Bearer auth-token',
        },
      })

      expect(result).toEqual(mockUser)
      expect(authStore.user).toEqual(mockUser)
    })

    it('should handle 401 unauthorized by logging out', async () => {
      const authStore = useAuthStore()
      
      authStore.setToken('invalid-token')
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      })

      const result = await authStore.fetchCurrentUser()

      expect(result).toBeNull()
      expect(authStore.token).toBeNull()
      expect(authStore.user).toBeNull()
    })

    it('should return null if no token is present', async () => {
      const authStore = useAuthStore()

      const result = await authStore.fetchCurrentUser()

      expect(result).toBeNull()
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should set and clear errors', () => {
      const authStore = useAuthStore()

      authStore.setError('Test error')
      expect(authStore.error).toBe('Test error')

      authStore.clearError()
      expect(authStore.error).toBeNull()
    })
  })
})