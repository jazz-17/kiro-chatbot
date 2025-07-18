import { ref, computed, readonly } from 'vue'
import { defineStore } from 'pinia'
import type { 
  Conversation, 
  Message, 
  ChatSession, 
  ConversationListResponse,
  MessageResponse,
  StreamChunk 
} from '@/types'
import { useAuthStore } from './auth'

export const useConversationsStore = defineStore('conversations', () => {
  const authStore = useAuthStore()
  
  // State
  const activeConversationId = ref<string | null>(null)
  const streamingMessageId = ref<string | null>(null)
  const streamingContent = ref<string>('')
  const isStreaming = ref(false)
  const eventSource = ref<EventSource | null>(null)
  const conversations = ref<Conversation[]>([])
  const messages = ref<Map<string, Message[]>>(new Map())

  // Getters
  const activeConversation = computed(() => {
    if (!activeConversationId.value) return null
    return conversations.value.find(conv => conv.id === activeConversationId.value) || null
  })

  const activeMessages = computed(() => {
    if (!activeConversationId.value) return []
    return messages.value.get(activeConversationId.value) || []
  })

  // API functions
  async function fetchConversations(): Promise<ConversationListResponse> {
    const response = await fetch('/api/conversations', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch conversations')
    }
    
    return response.json()
  }

  async function fetchConversation(id: string): Promise<Conversation> {
    const response = await fetch(`/api/conversations/${id}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch conversation')
    }
    
    return response.json()
  }

  async function fetchMessages(conversationId: string): Promise<Message[]> {
    const response = await fetch(`/api/conversations/${conversationId}/messages`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch messages')
    }
    
    return response.json()
  }

  async function createConversation(title?: string): Promise<Conversation> {
    const response = await fetch('/api/conversations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({ title }),
    })
    
    if (!response.ok) {
      throw new Error('Failed to create conversation')
    }
    
    return response.json()
  }

  async function sendMessage(conversationId: string, content: string): Promise<MessageResponse> {
    const response = await fetch(`/api/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({ content }),
    })
    
    if (!response.ok) {
      throw new Error('Failed to send message')
    }
    
    return response.json()
  }

  async function deleteConversation(id: string): Promise<void> {
    const response = await fetch(`/api/conversations/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to delete conversation')
    }
  }

  // State management functions
  function setConversations(newConversations: Conversation[]) {
    conversations.value = newConversations
  }

  function addConversation(conversation: Conversation) {
    conversations.value.unshift(conversation)
    setActiveConversation(conversation.id)
  }

  function updateConversation(id: string, updates: Partial<Conversation>) {
    const index = conversations.value.findIndex(conv => conv.id === id)
    if (index > -1) {
      conversations.value[index] = { ...conversations.value[index], ...updates }
    }
  }

  function removeConversation(id: string) {
    conversations.value = conversations.value.filter(conv => conv.id !== id)
    messages.value.delete(id)
    
    if (activeConversationId.value === id) {
      activeConversationId.value = null
    }
  }

  function setMessages(conversationId: string, newMessages: Message[]) {
    messages.value.set(conversationId, newMessages)
  }

  function addMessage(conversationId: string, message: Message) {
    const currentMessages = messages.value.get(conversationId) || []
    messages.value.set(conversationId, [...currentMessages, message])
  }

  function updateMessage(conversationId: string, messageId: string, updates: Partial<Message>) {
    const currentMessages = messages.value.get(conversationId) || []
    const index = currentMessages.findIndex(msg => msg.id === messageId)
    if (index > -1) {
      currentMessages[index] = { ...currentMessages[index], ...updates }
      messages.value.set(conversationId, [...currentMessages])
    }
  }

  function removeMessage(conversationId: string, messageId: string) {
    const currentMessages = messages.value.get(conversationId) || []
    messages.value.set(conversationId, currentMessages.filter(msg => msg.id !== messageId))
  }

  // Streaming functions
  function startStreaming(streamId: string, conversationId: string) {
    if (eventSource.value) {
      eventSource.value.close()
    }

    isStreaming.value = true
    streamingContent.value = ''
    streamingMessageId.value = `stream-${streamId}`

    eventSource.value = new EventSource(
      `/api/conversations/${conversationId}/stream/${streamId}?token=${authStore.token}`
    )

    eventSource.value.onmessage = (event) => {
      try {
        const chunk: StreamChunk = JSON.parse(event.data)
        
        if (chunk.isComplete) {
          // Streaming complete, add final message to store
          const assistantMessage: Message = {
            id: chunk.messageId || streamingMessageId.value!,
            role: 'assistant',
            content: streamingContent.value,
            timestamp: new Date(),
            citations: [], // Will be populated by the API response
          }
          
          addMessage(conversationId, assistantMessage)
          stopStreaming()
        } else {
          // Append chunk content
          streamingContent.value += chunk.content
        }
      } catch (error) {
        console.error('Error parsing stream chunk:', error)
        stopStreaming()
      }
    }

    eventSource.value.onerror = (error) => {
      console.error('Streaming error:', error)
      stopStreaming()
    }
  }

  function stopStreaming() {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    
    isStreaming.value = false
    streamingContent.value = ''
    streamingMessageId.value = null
  }

  // Actions
  function setActiveConversation(id: string | null) {
    activeConversationId.value = id
  }

  function addOptimisticMessage(conversationId: string, message: Partial<Message>) {
    const optimisticMessage: Message = {
      id: `optimistic-${Date.now()}`,
      role: 'user',
      content: '',
      timestamp: new Date(),
      ...message,
    }
    
    addMessage(conversationId, optimisticMessage)
    return optimisticMessage.id
  }

  function removeOptimisticMessage(conversationId: string, messageId: string) {
    removeMessage(conversationId, messageId)
  }

  // Cleanup on unmount
  function cleanup() {
    stopStreaming()
  }

  return {
    // State
    activeConversationId: readonly(activeConversationId),
    streamingMessageId: readonly(streamingMessageId),
    streamingContent: readonly(streamingContent),
    isStreaming: readonly(isStreaming),
    conversations: readonly(conversations),
    messages: readonly(messages),
    eventSource: readonly(eventSource),
    
    // Getters
    activeConversation,
    activeMessages,
    
    // API functions
    fetchConversations,
    fetchConversation,
    fetchMessages,
    createConversation,
    sendMessage,
    deleteConversation,
    
    // State management
    setConversations,
    addConversation,
    updateConversation,
    removeConversation,
    setMessages,
    addMessage,
    updateMessage,
    removeMessage,
    
    // Actions
    setActiveConversation,
    addOptimisticMessage,
    removeOptimisticMessage,
    startStreaming,
    stopStreaming,
    cleanup,
  }
})