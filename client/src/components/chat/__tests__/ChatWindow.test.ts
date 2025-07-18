import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatWindow from '../ChatWindow.vue'
import MessageBubble from '../MessageBubble.vue'
import MessageInput from '../MessageInput.vue'
import FileUploadArea from '../FileUploadArea.vue'
import { createMockMessage, createMockCitation, nextTick } from '../../../test-utils'

describe('ChatWindow', () => {
  it('renders empty state correctly', () => {
    const wrapper = mount(ChatWindow, {
      props: {
        initialMessages: []
      }
    })

    expect(wrapper.text()).toContain('Start a conversation')
    expect(wrapper.text()).toContain('Ask a question or upload files')
  })

  it('renders initial messages', () => {
    const messages = [
      createMockMessage({
        id: '1',
        content: 'Hello',
        role: 'user'
      }),
      createMockMessage({
        id: '2',
        content: 'Hi there!',
        role: 'assistant'
      })
    ]

    const wrapper = mount(ChatWindow, {
      props: {
        initialMessages: messages
      },
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const messageBubbles = wrapper.findAllComponents(MessageBubble)
    expect(messageBubbles).toHaveLength(2)
    expect(messageBubbles[0].props('message')).toEqual(messages[0])
    expect(messageBubbles[1].props('message')).toEqual(messages[1])
  })

  it('shows conversation title', () => {
    const conversation = {
      id: 'conv-1',
      title: 'Test Conversation',
      createdAt: new Date(),
      updatedAt: new Date()
    }

    const wrapper = mount(ChatWindow, {
      props: { conversation }
    })

    expect(wrapper.text()).toContain('Test Conversation')
  })

  it('shows default title for new conversation', () => {
    const wrapper = mount(ChatWindow)

    expect(wrapper.text()).toContain('New Conversation')
  })

  it('shows connection status', () => {
    const wrapper = mount(ChatWindow)

    expect(wrapper.text()).toContain('Connected')
    expect(wrapper.find('.bg-green-500').exists()).toBe(true)
  })

  it('handles message sending', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const messageInput = wrapper.findComponent(MessageInput)
    
    // Simulate typing a message
    await messageInput.vm.$emit('update:modelValue', 'Hello world')
    await messageInput.vm.$emit('send')

    expect(wrapper.emitted('message-sent')).toBeTruthy()
    expect(wrapper.emitted('message-sent')?.[0]).toEqual(['Hello world', []])
  })

  it('shows loading state when sending', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const messageInput = wrapper.findComponent(MessageInput)
    
    // Set a message value first so the send can proceed
    await messageInput.vm.$emit('update:modelValue', 'Test message')
    await messageInput.vm.$emit('send')
    await nextTick()

    expect(wrapper.find('.animate-bounce').exists()).toBe(true)
  })

  it('toggles file upload area', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const messageInput = wrapper.findComponent(MessageInput)
    
    // Initially hidden
    expect(wrapper.findComponent(FileUploadArea).exists()).toBe(false)
    
    // Toggle to show
    await messageInput.vm.$emit('toggle-file-upload')
    await nextTick()
    
    expect(wrapper.findComponent(FileUploadArea).exists()).toBe(true)
  })

  it('handles file selection', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    // Show file upload area
    const messageInput = wrapper.findComponent(MessageInput)
    await messageInput.vm.$emit('toggle-file-upload')
    await nextTick()

    const fileUploadArea = wrapper.findComponent(FileUploadArea)
    const mockFiles = [
      new File(['content'], 'test.txt', { type: 'text/plain' })
    ]

    await fileUploadArea.vm.$emit('files-selected', mockFiles)

    // Should start upload process
    expect(wrapper.vm.uploadedFiles).toHaveLength(1)
  })

  it('handles file removal', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    // Add a file first
    wrapper.vm.uploadedFiles = [{
      id: 'file-1',
      name: 'test.txt',
      size: 1024,
      type: 'text/plain',
      status: 'completed'
    }]

    await nextTick()

    // Show file upload area
    const messageInput = wrapper.findComponent(MessageInput)
    await messageInput.vm.$emit('toggle-file-upload')
    await nextTick()

    const fileUploadArea = wrapper.findComponent(FileUploadArea)
    await fileUploadArea.vm.$emit('file-remove', 'file-1')

    expect(wrapper.vm.uploadedFiles).toHaveLength(0)
  })

  it('handles citation clicks', async () => {
    const citation = createMockCitation()
    const messages = [
      createMockMessage({
        role: 'assistant',
        citations: [citation]
      })
    ]

    const wrapper = mount(ChatWindow, {
      props: { initialMessages: messages },
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const messageBubble = wrapper.findComponent(MessageBubble)
    await messageBubble.vm.$emit('citation-click', citation)

    expect(wrapper.emitted('citation-clicked')).toBeTruthy()
    expect(wrapper.emitted('citation-clicked')?.[0]).toEqual([citation])
  })

  it('displays and clears errors', async () => {
    const wrapper = mount(ChatWindow)

    // Set an error
    wrapper.vm.error = 'Something went wrong'
    await nextTick()

    expect(wrapper.text()).toContain('Something went wrong')
    expect(wrapper.find('.bg-red-50').exists()).toBe(true)

    // Clear the error
    const buttons = wrapper.findAll('button')
    const dismissButton = buttons.find(btn => btn.text().includes('Dismiss'))
    
    if (dismissButton) {
      await dismissButton.trigger('click')
      expect(wrapper.vm.error).toBeNull()
    }
  })

  it('exposes public methods', () => {
    const wrapper = mount(ChatWindow)

    expect(typeof wrapper.vm.addMessage).toBe('function')
    expect(typeof wrapper.vm.startStreaming).toBe('function')
    expect(typeof wrapper.vm.stopStreaming).toBe('function')
    expect(typeof wrapper.vm.updateStreamingMessage).toBe('function')
    expect(typeof wrapper.vm.scrollToBottom).toBe('function')
  })

  it('adds messages via public method', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const newMessage = createMockMessage({
      content: 'New message'
    })

    wrapper.vm.addMessage(newMessage)
    await nextTick()

    const messageBubbles = wrapper.findAllComponents(MessageBubble)
    expect(messageBubbles).toHaveLength(1)
    expect(messageBubbles[0].props('message')).toEqual(newMessage)
  })

  it('handles streaming state', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const messageId = 'streaming-msg'
    
    wrapper.vm.startStreaming(messageId)
    expect(wrapper.vm.isStreaming).toBe(true)
    expect(wrapper.vm.streamingMessageId).toBe(messageId)

    wrapper.vm.stopStreaming()
    expect(wrapper.vm.isStreaming).toBe(false)
    expect(wrapper.vm.streamingMessageId).toBeNull()
  })

  it('updates streaming message content', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    const message = createMockMessage({
      id: 'streaming-msg',
      content: 'Initial'
    })

    wrapper.vm.addMessage(message)
    wrapper.vm.updateStreamingMessage('streaming-msg', 'Updated content')

    expect(wrapper.vm.messages[0].content).toBe('Updated content')
  })

  it('clears files when requested', async () => {
    const wrapper = mount(ChatWindow, {
      global: {
        components: {
          MessageBubble,
          MessageInput,
          FileUploadArea
        }
      }
    })

    // Add files
    wrapper.vm.uploadedFiles = [{
      id: 'file-1',
      name: 'test.txt',
      size: 1024,
      type: 'text/plain',
      status: 'completed'
    }]

    const messageInput = wrapper.findComponent(MessageInput)
    await messageInput.vm.$emit('clear-files')

    expect(wrapper.vm.uploadedFiles).toHaveLength(0)
    expect(wrapper.vm.showFileUpload).toBe(false)
  })
})