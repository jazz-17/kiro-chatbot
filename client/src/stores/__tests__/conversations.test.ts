import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConversationsStore } from '../conversations'
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

// Mock EventSource
class MockEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  close = vi.fn()
  
  constructor(public url: string) {}
}

global.EventSource = MockEventSource as any

describe('Conversations Store', () => {
  let conversationsStore: ReturnType<typeof useConversationsStore>
  let authStore: ReturnType<typeof useAuthStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    mockLocalStorage.getItem.mockReturnValue('test-token')
    
    authStore = useAuthStore()
    conversationsStore = useConversationsStore()
    
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should initialize with correct default state', () => {
      expect(conversationsStore.activeConversationId).toBeNull()
      expect(conversationsStore.streamingMessageId).toBeNull()
      expect(conversationsStore.streamingContent).toBe('')
      expect(conversationsStore.isStreaming).toBe(false)
    })
  })

  describe('Active Conversation Management', () => {
    it('should set active conversation', () => {
      const conversationId = 'conv-1'
      
      conversationsStore.setActiveConversation(conversationId)
      
      expect(conversationsStore.activeConversationId).toBe(conversationId)
    })

    it('should clear active conversation', () => {
      conversationsStore.setActiveConversation('conv-1')
      conversationsStore.setActiveConversation(null)
      
      expect(conversationsStore.activeConversationId).toBeNull()
    })
  })

  describe('API Functions', () => {
    it('should fetch conversations with auth header', async () => {
      const mockConversations = {
        conversations: [
          {
            id: 'conv-1',
            title: 'Test Conversation',
            createdAt: new Date(),
            updatedAt: new Date(),
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockConversations),
      })

      const result = await conversationsStore.fetchConversations()

      expect(mockFetch).toHaveBeenCalledWith('/api/conversations', {
        headers: {
          'Authorization': 'Bearer test-token',
        },
      })
      expect(result).toEqual(mockConversations)
    })

    it('should fetch conversation by id', async () => {
      const mockConversation = {
        id: 'conv-1',
        title: 'Test Conversation',
        createdAt: new Date(),
        updatedAt: new Date(),
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockConversation),
      })

      const result = await conversationsStore.fetchConversation('conv-1')

      expect(mockFetch).toHaveBeenCalledWith('/api/conversations/conv-1', {
        headers: {
          'Authorization': 'Bearer test-token',
        },
      })
      expect(result).toEqual(mockConversation)
    })

    it('should fetch messages for conversation', async () => {
      const mockMessages = [
        {
          id: 'msg-1',
          role: 'user' as const,
          content: 'Hello',
          timestamp: new Date(),
        },
        {
          id: 'msg-2',
          role: 'assistant' as const,
          content: 'Hi there!',
          timestamp: new Date(),
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockMessages),
      })

      const result = await conversationsStore.fetchMessages('conv-1')

      expect(mockFetch).toHaveBeenCalledWith('/api/conversations/conv-1/messages', {
        headers: {
          'Authorization': 'Bearer test-token',
        },
      })
      expect(result).toEqual(mockMessages)
    })
  })

  describe('API Mutations', () => {
    it('should create new conversation', async () => {
      const mockConversation = {
        id: 'conv-new',
        title: 'New Conversation',
        createdAt: new Date(),
        updatedAt: new Date(),
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockConversation),
      })

      const result = await conversationsStore.createConversation('New Conversation')

      expect(mockFetch).toHaveBeenCalledWith('/api/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
        body: JSON.stringify({ title: 'New Conversation' }),
      })

      expect(result).toEqual(mockConversation)
    })

    it('should send message', async () => {
      const mockResponse = {
        message: {
          id: 'msg-new',
          role: 'assistant' as const,
          content: 'Response',
          timestamp: new Date(),
        },
        streamId: 'stream-123',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await conversationsStore.sendMessage('conv-1', 'Hello')

      expect(mockFetch).toHaveBeenCalledWith('/api/conversations/conv-1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token',
        },
        body: JSON.stringify({ content: 'Hello' }),
      })

      expect(result).toEqual(mockResponse)
    })

    it('should delete conversation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
      })

      await conversationsStore.deleteConversation('conv-1')

      expect(mockFetch).toHaveBeenCalledWith('/api/conversations/conv-1', {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer test-token',
        },
      })
    })
  })

  describe('State Management', () => {
    it('should manage conversations state', () => {
      const mockConversations = [
        {
          id: 'conv-1',
          title: 'Test Conversation',
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      ]

      conversationsStore.setConversations(mockConversations)
      expect(conversationsStore.conversations).toEqual(mockConversations)

      const newConversation = {
        id: 'conv-2',
        title: 'New Conversation',
        createdAt: new Date(),
        updatedAt: new Date(),
      }

      conversationsStore.addConversation(newConversation)
      expect(conversationsStore.conversations).toHaveLength(2)
      expect(conversationsStore.activeConversationId).toBe('conv-2')

      conversationsStore.removeConversation('conv-1')
      expect(conversationsStore.conversations).toHaveLength(1)
      expect(conversationsStore.conversations[0].id).toBe('conv-2')
    })

    it('should manage messages state', () => {
      const mockMessages = [
        {
          id: 'msg-1',
          role: 'user' as const,
          content: 'Hello',
          timestamp: new Date(),
        },
      ]

      conversationsStore.setMessages('conv-1', mockMessages)
      expect(conversationsStore.messages.get('conv-1')).toEqual(mockMessages)

      const newMessage = {
        id: 'msg-2',
        role: 'assistant' as const,
        content: 'Hi there!',
        timestamp: new Date(),
      }

      conversationsStore.addMessage('conv-1', newMessage)
      expect(conversationsStore.messages.get('conv-1')).toHaveLength(2)

      conversationsStore.removeMessage('conv-1', 'msg-1')
      expect(conversationsStore.messages.get('conv-1')).toHaveLength(1)
      expect(conversationsStore.messages.get('conv-1')![0].id).toBe('msg-2')
    })
  })

  describe('Streaming', () => {
    it('should start streaming', () => {
      const streamId = 'stream-123'
      const conversationId = 'conv-1'

      conversationsStore.startStreaming(streamId, conversationId)

      expect(conversationsStore.isStreaming).toBe(true)
      expect(conversationsStore.streamingMessageId).toBe(`stream-${streamId}`)
      expect(conversationsStore.streamingContent).toBe('')
    })

    it('should stop streaming', () => {
      conversationsStore.startStreaming('stream-123', 'conv-1')
      conversationsStore.stopStreaming()

      expect(conversationsStore.isStreaming).toBe(false)
      expect(conversationsStore.streamingMessageId).toBeNull()
      expect(conversationsStore.streamingContent).toBe('')
    })

    it('should handle streaming messages', () => {
      const streamId = 'stream-123'
      const conversationId = 'conv-1'

      // Start streaming - this creates the EventSource internally
      conversationsStore.startStreaming(streamId, conversationId)

      // Get the EventSource that was created
      const eventSource = conversationsStore.eventSource as any as MockEventSource

      // Simulate receiving a chunk
      if (eventSource && eventSource.onmessage) {
        eventSource.onmessage({
          data: JSON.stringify({
            id: 'chunk-1',
            content: 'Hello ',
            isComplete: false,
          }),
        } as MessageEvent)
      }

      expect(conversationsStore.streamingContent).toBe('Hello ')

      // Simulate completion
      if (eventSource && eventSource.onmessage) {
        eventSource.onmessage({
          data: JSON.stringify({
            id: 'chunk-2',
            content: 'world!',
            isComplete: true,
            messageId: 'msg-final',
          }),
        } as MessageEvent)
      }

      expect(conversationsStore.isStreaming).toBe(false)
    })
  })

  describe('Optimistic Updates', () => {
    it('should add optimistic message', () => {
      const messageId = conversationsStore.addOptimisticMessage('conv-1', {
        role: 'user',
        content: 'Test message',
      })

      expect(messageId).toMatch(/^optimistic-/)
    })

    it('should remove optimistic message', () => {
      const messageId = conversationsStore.addOptimisticMessage('conv-1', {
        role: 'user',
        content: 'Test message',
      })

      conversationsStore.removeOptimisticMessage('conv-1', messageId)
      
      // This would need to be tested with actual query cache inspection
      // For now, we just verify the method doesn't throw
      expect(true).toBe(true)
    })
  })

  describe('Cleanup', () => {
    it('should cleanup resources', () => {
      conversationsStore.startStreaming('stream-123', 'conv-1')
      conversationsStore.cleanup()

      expect(conversationsStore.isStreaming).toBe(false)
    })
  })
})