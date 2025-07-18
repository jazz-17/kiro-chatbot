import { mount, VueWrapper } from '@vue/test-utils'
import { vi } from 'vitest'
import type { Message, Citation, UploadedFile } from '@/types'

// Mock highlight.js
vi.mock('highlight.js', () => ({
  default: {
    highlight: vi.fn().mockReturnValue({ value: 'highlighted code' }),
    highlightAuto: vi.fn().mockReturnValue({ value: 'highlighted code' }),
    getLanguage: vi.fn().mockReturnValue(true)
  }
}))

// Mock @vueuse/core
vi.mock('@vueuse/core', () => ({
  useEventSource: vi.fn().mockReturnValue({
    status: 'CONNECTING',
    data: null,
    error: null,
    close: vi.fn(),
    open: vi.fn()
  })
}))

// Test utilities
export const createMockMessage = (overrides: Partial<Message> = {}): Message => ({
  id: 'test-message-1',
  role: 'user',
  content: 'Test message',
  timestamp: new Date(),
  ...overrides
})

export const createMockCitation = (overrides: Partial<Citation> = {}): Citation => ({
  id: 'test-citation-1',
  title: 'Test Document',
  source: 'Test Source',
  excerpt: 'This is a test excerpt from the document.',
  ...overrides
})

export const createMockFile = (overrides: Partial<UploadedFile> = {}): UploadedFile => ({
  id: 'test-file-1',
  name: 'test.txt',
  size: 1024,
  type: 'text/plain',
  status: 'pending' as const,
  ...overrides
})

// Helper to wait for next tick
export const nextTick = () => new Promise(resolve => setTimeout(resolve, 0))

// Helper to trigger file drop event
export const createFileDropEvent = (files: File[]) => {
  const dataTransfer = {
    files: files,
    items: files.map(file => ({ kind: 'file', type: file.type, getAsFile: () => file })),
    types: ['Files']
  }
  
  // Create a mock event object since DragEvent might not be available in test environment
  return {
    type: 'drop',
    dataTransfer,
    preventDefault: vi.fn(),
    stopPropagation: vi.fn()
  }
}

// Helper to create mock File objects
export const createMockFileObject = (name: string, size: number = 1024, type: string = 'text/plain') => {
  const file = new File(['test content'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}