// Core chat types for the application

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  citations?: Citation[]
}

export interface Citation {
  id: string
  title: string
  source: string
  excerpt?: string
  url?: string
  page?: number
}

export interface Conversation {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  userId?: string
  lastMessageAt?: Date
}

export interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: 'pending' | 'uploading' | 'completed' | 'error'
  url?: string
  uploadProgress?: number
  progress?: number
  error?: string
  errorMessage?: string
}

// Additional helper types
export interface User {
  id: string
  email: string
  name?: string
  avatar?: string
  createdAt: Date
}

export interface ChatSession {
  conversation: Conversation
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  error?: string
}

// API response types
export interface MessageResponse {
  message: Message
  conversation?: Conversation
  streamId?: string
}

export interface ConversationListResponse {
  conversations: Conversation[]
  total: number
  page: number
  limit: number
}

// File upload types
export interface FileUploadResponse {
  file: UploadedFile
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
  extractedText?: string
  metadata?: Record<string, any>
}

// Streaming types
export interface StreamChunk {
  id: string
  content: string
  isComplete: boolean
  messageId?: string
}

// Error types
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, any>
}
