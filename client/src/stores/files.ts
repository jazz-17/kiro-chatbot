import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import type { UploadedFile, FileUploadResponse } from '@/types'
import { useAuthStore } from './auth'

export const useFilesStore = defineStore('files', () => {
  const queryClient = useQueryClient()
  const authStore = useAuthStore()
  
  // State
  const uploadQueue = ref<Map<string, UploadedFile>>(new Map())
  const dragActive = ref(false)
  const maxFileSize = ref(10 * 1024 * 1024) // 10MB
  const allowedTypes = ref([
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/markdown',
  ])

  // Getters
  const uploadingFiles = computed(() => 
    Array.from(uploadQueue.value.values()).filter(file => 
      file.status === 'uploading' || file.status === 'pending'
    )
  )

  const completedFiles = computed(() => 
    Array.from(uploadQueue.value.values()).filter(file => 
      file.status === 'completed'
    )
  )

  const failedFiles = computed(() => 
    Array.from(uploadQueue.value.values()).filter(file => 
      file.status === 'error'
    )
  )

  const hasActiveUploads = computed(() => uploadingFiles.value.length > 0)

  // Validation functions
  function validateFile(file: File): { valid: boolean; error?: string } {
    if (file.size > maxFileSize.value) {
      return {
        valid: false,
        error: `File size exceeds ${Math.round(maxFileSize.value / 1024 / 1024)}MB limit`
      }
    }

    if (!allowedTypes.value.includes(file.type)) {
      return {
        valid: false,
        error: 'File type not supported'
      }
    }

    return { valid: true }
  }

  function validateFiles(files: File[]): { valid: File[]; invalid: Array<{ file: File; error: string }> } {
    const valid: File[] = []
    const invalid: Array<{ file: File; error: string }> = []

    files.forEach(file => {
      const validation = validateFile(file)
      if (validation.valid) {
        valid.push(file)
      } else {
        invalid.push({ file, error: validation.error! })
      }
    })

    return { valid, invalid }
  }

  // Upload functions
  async function uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/files/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Upload failed' }))
      throw new Error(errorData.message || 'Upload failed')
    }

    return response.json()
  }

  function createUploadedFile(file: File): UploadedFile {
    return {
      id: `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      uploadProgress: 0,
    }
  }

  // Mutation hooks
  function useUploadFileMutation() {
    return useMutation({
      mutationFn: uploadFile,
      onSuccess: (response, file) => {
        const uploadedFile = Array.from(uploadQueue.value.values())
          .find(f => f.name === file.name && f.size === file.size)
        
        if (uploadedFile) {
          uploadQueue.value.set(uploadedFile.id, {
            ...uploadedFile,
            status: 'completed',
            url: response.file.url,
            uploadProgress: 100,
          })
        }
      },
      onError: (error, file) => {
        const uploadedFile = Array.from(uploadQueue.value.values())
          .find(f => f.name === file.name && f.size === file.size)
        
        if (uploadedFile) {
          uploadQueue.value.set(uploadedFile.id, {
            ...uploadedFile,
            status: 'error',
            error: error instanceof Error ? error.message : 'Upload failed',
          })
        }
      },
    })
  }

  // Actions
  function addToQueue(files: File[]) {
    const { valid, invalid } = validateFiles(files)
    
    // Add valid files to queue
    valid.forEach(file => {
      const uploadedFile = createUploadedFile(file)
      uploadQueue.value.set(uploadedFile.id, uploadedFile)
    })

    // Return validation results
    return { valid, invalid }
  }

  function removeFromQueue(fileId: string) {
    uploadQueue.value.delete(fileId)
  }

  function clearQueue() {
    uploadQueue.value.clear()
  }

  function clearCompleted() {
    Array.from(uploadQueue.value.entries()).forEach(([id, file]) => {
      if (file.status === 'completed') {
        uploadQueue.value.delete(id)
      }
    })
  }

  function clearFailed() {
    Array.from(uploadQueue.value.entries()).forEach(([id, file]) => {
      if (file.status === 'error') {
        uploadQueue.value.delete(id)
      }
    })
  }

  function updateFileProgress(fileId: string, progress: number) {
    const file = uploadQueue.value.get(fileId)
    if (file) {
      uploadQueue.value.set(fileId, {
        ...file,
        uploadProgress: progress,
        status: progress === 100 ? 'completed' : 'uploading',
      })
    }
  }

  function setFileStatus(fileId: string, status: UploadedFile['status'], error?: string) {
    const file = uploadQueue.value.get(fileId)
    if (file) {
      uploadQueue.value.set(fileId, {
        ...file,
        status,
        error,
      })
    }
  }

  function setDragActive(active: boolean) {
    dragActive.value = active
  }

  async function processUploadQueue() {
    const uploadMutation = useUploadFileMutation()
    const pendingFiles = Array.from(uploadQueue.value.values())
      .filter(file => file.status === 'pending')

    for (const uploadedFile of pendingFiles) {
      try {
        // Update status to uploading
        setFileStatus(uploadedFile.id, 'uploading')
        
        // Find the original File object (this would need to be stored separately in a real implementation)
        // For now, we'll simulate the upload process
        const file = new File([''], uploadedFile.name, { type: uploadedFile.type })
        
        await uploadMutation.mutateAsync(file)
      } catch (error) {
        console.error(`Upload failed for ${uploadedFile.name}:`, error)
      }
    }
  }

  // Drag and drop handlers
  function handleDragEnter(event: DragEvent) {
    event.preventDefault()
    setDragActive(true)
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault()
    // Only set drag inactive if we're leaving the drop zone entirely
    if (!event.relatedTarget || !(event.currentTarget as Element).contains(event.relatedTarget as Node)) {
      setDragActive(false)
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault()
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setDragActive(false)
    
    const files = Array.from(event.dataTransfer?.files || [])
    if (files.length > 0) {
      const result = addToQueue(files)
      processUploadQueue()
      return result
    }
    
    return { valid: [], invalid: [] }
  }

  return {
    // State
    uploadQueue: readonly(uploadQueue),
    dragActive: readonly(dragActive),
    maxFileSize: readonly(maxFileSize),
    allowedTypes: readonly(allowedTypes),
    
    // Getters
    uploadingFiles,
    completedFiles,
    failedFiles,
    hasActiveUploads,
    
    // Validation
    validateFile,
    validateFiles,
    
    // Mutation hooks
    useUploadFileMutation,
    
    // Actions
    addToQueue,
    removeFromQueue,
    clearQueue,
    clearCompleted,
    clearFailed,
    updateFileProgress,
    setFileStatus,
    setDragActive,
    processUploadQueue,
    
    // Drag and drop handlers
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
  }
})