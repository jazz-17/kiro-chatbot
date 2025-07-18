import { ref, computed, readonly } from 'vue'
import { defineStore } from 'pinia'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value && !!token.value)
  const userEmail = computed(() => user.value?.email || '')
  const userName = computed(() => user.value?.name || user.value?.email || '')

  // Actions
  function setUser(userData: User) {
    user.value = userData
    error.value = null
  }

  function setToken(authToken: string) {
    token.value = authToken
    localStorage.setItem('auth_token', authToken)
  }

  function setError(errorMessage: string) {
    error.value = errorMessage
  }

  function clearError() {
    error.value = null
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  async function login(email: string, password: string) {
    setLoading(true)
    clearError()
    
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Login failed')
      }

      const data = await response.json()
      setToken(data.token)
      setUser(data.user)
      
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  async function register(email: string, password: string, name?: string) {
    setLoading(true)
    clearError()
    
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Registration failed')
      }

      const data = await response.json()
      setToken(data.token)
      setUser(data.user)
      
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  async function logout() {
    setLoading(true)
    
    try {
      if (token.value) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token.value}`,
          },
        })
      }
    } catch (err) {
      console.warn('Logout request failed:', err)
    } finally {
      // Clear local state regardless of API call success
      user.value = null
      token.value = null
      localStorage.removeItem('auth_token')
      clearError()
      setLoading(false)
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return null

    setLoading(true)
    clearError()
    
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token.value}`,
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          // Token is invalid, clear it
          await logout()
          return null
        }
        throw new Error('Failed to fetch user data')
      }

      const userData = await response.json()
      setUser(userData)
      return userData
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch user'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  // Initialize auth state on store creation
  if (token.value) {
    fetchCurrentUser()
  }

  return {
    // State
    user: readonly(user),
    token: readonly(token),
    isLoading: readonly(isLoading),
    error: readonly(error),
    
    // Getters
    isAuthenticated,
    userEmail,
    userName,
    
    // Actions
    login,
    register,
    logout,
    fetchCurrentUser,
    setUser,
    setToken,
    setError,
    clearError,
    setLoading,
  }
})