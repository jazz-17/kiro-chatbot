import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  persistent?: boolean
  actions?: Array<{
    label: string
    action: () => void
    style?: 'primary' | 'secondary'
  }>
  createdAt: Date
}

export const useNotificationsStore = defineStore('notifications', () => {
  // State
  const notifications = ref<Notification[]>([])
  const maxNotifications = ref(5)
  const defaultDuration = ref(5000) // 5 seconds

  // Getters
  const activeNotifications = computed(() => notifications.value)
  const hasNotifications = computed(() => notifications.value.length > 0)
  const errorNotifications = computed(() => 
    notifications.value.filter(n => n.type === 'error')
  )
  const successNotifications = computed(() => 
    notifications.value.filter(n => n.type === 'success')
  )

  // Private functions
  function generateId(): string {
    return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  function scheduleRemoval(id: string, duration: number) {
    setTimeout(() => {
      removeNotification(id)
    }, duration)
  }

  function enforceMaxNotifications() {
    if (notifications.value.length > maxNotifications.value) {
      const excess = notifications.value.length - maxNotifications.value
      notifications.value.splice(0, excess)
    }
  }

  // Actions
  function addNotification(notification: Omit<Notification, 'id' | 'createdAt'>): string {
    const id = generateId()
    const newNotification: Notification = {
      ...notification,
      id,
      createdAt: new Date(),
      duration: notification.duration ?? defaultDuration.value,
    }

    notifications.value.push(newNotification)
    enforceMaxNotifications()

    // Schedule automatic removal if not persistent
    if (!newNotification.persistent && newNotification.duration > 0) {
      scheduleRemoval(id, newNotification.duration)
    }

    return id
  }

  function removeNotification(id: string) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  function clearAll() {
    notifications.value = []
  }

  function clearByType(type: Notification['type']) {
    notifications.value = notifications.value.filter(n => n.type !== type)
  }

  // Convenience methods for different notification types
  function success(title: string, message?: string, options?: Partial<Notification>): string {
    return addNotification({
      type: 'success',
      title,
      message,
      ...options,
    })
  }

  function error(title: string, message?: string, options?: Partial<Notification>): string {
    return addNotification({
      type: 'error',
      title,
      message,
      persistent: true, // Errors are persistent by default
      ...options,
    })
  }

  function warning(title: string, message?: string, options?: Partial<Notification>): string {
    return addNotification({
      type: 'warning',
      title,
      message,
      duration: 7000, // Warnings last longer
      ...options,
    })
  }

  function info(title: string, message?: string, options?: Partial<Notification>): string {
    return addNotification({
      type: 'info',
      title,
      message,
      ...options,
    })
  }

  // Error handling helpers
  function handleApiError(error: unknown, context?: string) {
    let title = 'An error occurred'
    let message = 'Please try again later'

    if (error instanceof Error) {
      title = context ? `${context} failed` : 'Operation failed'
      message = error.message
    } else if (typeof error === 'string') {
      message = error
    }

    return this.error(title, message)
  }

  function handleNetworkError(context?: string) {
    return error(
      'Network Error',
      context ? `Failed to ${context}. Please check your connection.` : 'Please check your internet connection.',
      {
        actions: [
          {
            label: 'Retry',
            action: () => window.location.reload(),
            style: 'primary',
          },
        ],
      }
    )
  }

  function handleValidationError(errors: Record<string, string[]>) {
    const errorMessages = Object.entries(errors)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('\n')

    return error('Validation Error', errorMessages)
  }

  // Batch operations
  function showUploadProgress(fileName: string): string {
    return info('Uploading', `Uploading ${fileName}...`, {
      persistent: true,
    })
  }

  function showUploadSuccess(fileName: string): string {
    return success('Upload Complete', `${fileName} uploaded successfully`)
  }

  function showUploadError(fileName: string, errorMessage?: string): string {
    return error(
      'Upload Failed',
      `Failed to upload ${fileName}${errorMessage ? `: ${errorMessage}` : ''}`,
      {
        actions: [
          {
            label: 'Retry',
            action: () => {
              // This would trigger a retry mechanism
              console.log('Retry upload for', fileName)
            },
            style: 'primary',
          },
        ],
      }
    )
  }

  function showConnectionStatus(isOnline: boolean) {
    if (isOnline) {
      success('Connection Restored', 'You are back online')
    } else {
      warning(
        'Connection Lost',
        'You are currently offline. Some features may not work.',
        {
          persistent: true,
        }
      )
    }
  }

  // Authentication notifications
  function showLoginSuccess(userName?: string) {
    return success(
      'Welcome back!',
      userName ? `Hello, ${userName}` : 'You have successfully logged in'
    )
  }

  function showLogoutSuccess() {
    return info('Logged out', 'You have been logged out successfully')
  }

  function showAuthError(message?: string) {
    return error(
      'Authentication Error',
      message || 'Please log in to continue',
      {
        actions: [
          {
            label: 'Login',
            action: () => {
              // This would navigate to login page
              console.log('Navigate to login')
            },
            style: 'primary',
          },
        ],
      }
    )
  }

  return {
    // State
    notifications: readonly(notifications),
    maxNotifications: readonly(maxNotifications),
    defaultDuration: readonly(defaultDuration),
    
    // Getters
    activeNotifications,
    hasNotifications,
    errorNotifications,
    successNotifications,
    
    // Core actions
    addNotification,
    removeNotification,
    clearAll,
    clearByType,
    
    // Convenience methods
    success,
    error,
    warning,
    info,
    
    // Error handling
    handleApiError,
    handleNetworkError,
    handleValidationError,
    
    // Specialized notifications
    showUploadProgress,
    showUploadSuccess,
    showUploadError,
    showConnectionStatus,
    showLoginSuccess,
    showLogoutSuccess,
    showAuthError,
  }
})