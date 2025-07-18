<template>
  <div class="flex flex-col h-full bg-white rounded-lg shadow-lg">
    <!-- Chat Header -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-800">
        {{ conversation?.title || 'New Conversation' }}
      </h2>
      <div class="flex items-center space-x-2">
        <span v-if="isConnected" class="flex items-center text-sm text-green-600">
          <div class="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
          Connected
        </span>
        <span v-else class="flex items-center text-sm text-red-600">
          <div class="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
          Disconnected
        </span>
      </div>
    </div>

    <!-- Messages Container -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-4 space-y-4"
      @scroll="handleScroll"
    >
      <div v-if="messages.length === 0" class="flex items-center justify-center h-full">
        <div class="text-center text-gray-500">
          <p class="text-lg mb-2">Start a conversation</p>
          <p class="text-sm">Ask a question or upload files to get started</p>
        </div>
      </div>

      <MessageBubble
        v-for="message in messages"
        :key="message.id"
        :message="message"
        :is-streaming="isStreaming && message.id === streamingMessageId"
        @citation-click="handleCitationClick"
      />

      <!-- Loading indicator for new messages -->
      <div v-if="isLoading" class="flex justify-start">
        <div class="bg-gray-100 rounded-lg p-3 max-w-xs">
          <div class="flex space-x-1">
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div
              class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style="animation-delay: 0.1s"
            ></div>
            <div
              class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style="animation-delay: 0.2s"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- File Upload Area -->
    <FileUploadArea
      v-if="showFileUpload"
      :files="uploadedFiles"
      :is-uploading="isUploading"
      :upload-progress="uploadProgress"
      @files-selected="handleFilesSelected"
      @file-remove="handleFileRemove"
      @upload-complete="handleUploadComplete"
      @upload-error="handleUploadError"
    />

    <!-- Message Input -->
    <div class="border-t border-gray-200 p-4">
      <MessageInput
        v-model="messageText"
        :is-sending="isSending"
        :has-files="uploadedFiles.length > 0"
        @send="handleSendMessage"
        @toggle-file-upload="toggleFileUpload"
        @clear-files="clearFiles"
      />
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 border-l-4 border-red-400 p-4 m-4">
      <div class="flex">
        <div class="ml-3">
          <p class="text-sm text-red-700">{{ error }}</p>
          <button
            @click="clearError"
            class="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import type { Message, Citation, Conversation, UploadedFile } from '@/types'
import MessageBubble from './MessageBubble.vue'
import MessageInput from './MessageInput.vue'
import FileUploadArea from './FileUploadArea.vue'

interface Props {
  conversation?: Conversation
  initialMessages?: Message[]
}

interface Emits {
  (e: 'message-sent', message: string, files: UploadedFile[]): void
  (e: 'citation-clicked', citation: Citation): void
  (e: 'conversation-updated', conversation: Conversation): void
}

const props = withDefaults(defineProps<Props>(), {
  initialMessages: () => [],
})

const emit = defineEmits<Emits>()

// Reactive state
const messages = ref<Message[]>([...props.initialMessages])
const messageText = ref('')
const messagesContainer = ref<HTMLElement>()
const showFileUpload = ref(false)
const uploadedFiles = ref<UploadedFile[]>([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const isSending = ref(false)
const isLoading = ref(false)
const isStreaming = ref(false)
const streamingMessageId = ref<string | null>(null)
const isConnected = ref(true)
const error = ref<string | null>(null)

// Auto-scroll to bottom when new messages arrive
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Handle scroll events
const handleScroll = () => {
  // Could implement "scroll to see new messages" indicator here
}

// Message handling
const handleSendMessage = async () => {
  if (!messageText.value.trim() && uploadedFiles.value.length === 0) return

  try {
    isSending.value = true
    error.value = null

    // Add user message immediately
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: messageText.value,
      timestamp: new Date(),
    }

    messages.value.push(userMessage)

    // Emit the message
    emit('message-sent', messageText.value, [...uploadedFiles.value])

    // Clear input
    messageText.value = ''
    clearFiles()

    // Start loading state for AI response
    isLoading.value = true

    await scrollToBottom()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to send message'
  } finally {
    isSending.value = false
  }
}

// File handling
const toggleFileUpload = () => {
  showFileUpload.value = !showFileUpload.value
}

const handleFilesSelected = (files: File[]) => {
  const newFiles: UploadedFile[] = files.map((file) => ({
    id: generateId(),
    name: file.name,
    size: file.size,
    type: file.type,
    status: 'pending',
  }))

  uploadedFiles.value.push(...newFiles)
  startFileUpload(newFiles)
}

const startFileUpload = async (files: UploadedFile[]) => {
  isUploading.value = true

  for (const file of files) {
    try {
      file.status = 'uploading'
      // Simulate upload progress
      for (let progress = 0; progress <= 100; progress += 10) {
        file.progress = progress
        uploadProgress.value = progress
        await new Promise((resolve) => setTimeout(resolve, 100))
      }
      file.status = 'completed'
    } catch (err) {
      file.status = 'error'
      file.error = err instanceof Error ? err.message : 'Upload failed'
    }
  }

  isUploading.value = false
}

const handleFileRemove = (fileId: string) => {
  uploadedFiles.value = uploadedFiles.value.filter((f) => f.id !== fileId)
}

const handleUploadComplete = () => {
  // Handle upload completion
}

const handleUploadError = (errorMessage: string) => {
  error.value = errorMessage
}

const clearFiles = () => {
  uploadedFiles.value = []
  showFileUpload.value = false
}

// Citation handling
const handleCitationClick = (citation: Citation) => {
  emit('citation-clicked', citation)
}

// Error handling
const clearError = () => {
  error.value = null
}

// Utility functions
const generateId = () => {
  return Math.random().toString(36).substring(2, 11)
}

// Public methods for parent components
const addMessage = (message: Message) => {
  messages.value.push(message)
  scrollToBottom()
}

const startStreaming = (messageId: string) => {
  isLoading.value = false
  isStreaming.value = true
  streamingMessageId.value = messageId
}

const stopStreaming = () => {
  isStreaming.value = false
  streamingMessageId.value = null
}

const updateStreamingMessage = (messageId: string, content: string) => {
  const message = messages.value.find((m) => m.id === messageId)
  if (message) {
    message.content = content
  }
}

// Expose methods to parent
defineExpose({
  addMessage,
  startStreaming,
  stopStreaming,
  updateStreamingMessage,
  scrollToBottom,
})

// Lifecycle
onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
/* Custom scrollbar for messages container */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
