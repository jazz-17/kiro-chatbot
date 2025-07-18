<template>
  <div class="flex flex-col space-y-2">
    <!-- File indicators -->
    <div v-if="hasFiles" class="flex items-center space-x-2 text-sm text-gray-600">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
      </svg>
      <span>Files attached</span>
      <button 
        @click="$emit('clear-files')"
        class="text-red-500 hover:text-red-700 text-xs underline"
      >
        Clear
      </button>
    </div>
    
    <!-- Input area -->
    <div class="flex items-end space-x-2">
      <!-- Text input -->
      <div class="flex-1 relative">
        <textarea
          ref="textareaRef"
          v-model="localValue"
          :placeholder="placeholder"
          :disabled="isSending"
          class="input-textarea"
          rows="1"
          @keydown="handleKeydown"
          @input="handleInput"
        />
        
        <!-- Character count -->
        <div 
          v-if="showCharCount && localValue.length > 0" 
          class="absolute bottom-2 right-2 text-xs text-gray-400"
        >
          {{ localValue.length }}
        </div>
      </div>
      
      <!-- Action buttons -->
      <div class="flex items-center space-x-1">
        <!-- File upload button -->
        <button
          @click="$emit('toggle-file-upload')"
          :disabled="isSending"
          class="action-button"
          title="Attach files"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
          </svg>
        </button>
        
        <!-- Send button -->
        <button
          @click="handleSend"
          :disabled="!canSend"
          class="send-button"
          title="Send message (Ctrl+Enter)"
        >
          <svg 
            v-if="!isSending"
            class="w-5 h-5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
          
          <!-- Loading spinner -->
          <svg 
            v-else
            class="w-5 h-5 animate-spin" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Keyboard shortcuts hint -->
    <div class="text-xs text-gray-500">
      Press <kbd class="kbd">Ctrl</kbd> + <kbd class="kbd">Enter</kbd> to send
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'

interface Props {
  modelValue: string
  isSending?: boolean
  hasFiles?: boolean
  placeholder?: string
  maxLength?: number
  showCharCount?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'send'): void
  (e: 'toggle-file-upload'): void
  (e: 'clear-files'): void
}

const props = withDefaults(defineProps<Props>(), {
  isSending: false,
  hasFiles: false,
  placeholder: 'Type your message...',
  maxLength: 4000,
  showCharCount: false
})

const emit = defineEmits<Emits>()

const textareaRef = ref<HTMLTextAreaElement>()
const localValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const canSend = computed(() => {
  return !props.isSending && (localValue.value.trim().length > 0 || props.hasFiles)
})

// Auto-resize textarea
const adjustTextareaHeight = async () => {
  await nextTick()
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    const scrollHeight = textareaRef.value.scrollHeight
    const maxHeight = 120 // Max height in pixels (about 5 lines)
    textareaRef.value.style.height = Math.min(scrollHeight, maxHeight) + 'px'
  }
}

const handleInput = () => {
  adjustTextareaHeight()
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    if (event.ctrlKey || event.metaKey) {
      // Ctrl+Enter or Cmd+Enter to send
      event.preventDefault()
      handleSend()
    } else if (!event.shiftKey) {
      // Enter without Shift to send (prevent default line break)
      event.preventDefault()
      handleSend()
    }
    // Shift+Enter allows line break (default behavior)
  }
}

const handleSend = () => {
  if (canSend.value) {
    emit('send')
  }
}

// Watch for value changes to adjust height
watch(() => props.modelValue, () => {
  adjustTextareaHeight()
})

// Focus the textarea when component mounts
const focusInput = () => {
  if (textareaRef.value) {
    textareaRef.value.focus()
  }
}

// Expose focus method
defineExpose({
  focus: focusInput
})
</script>

<style scoped>
.input-textarea {
  @apply w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed;
  min-height: 40px;
  max-height: 120px;
}

.action-button {
  @apply p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed;
}

.send-button {
  @apply p-2 bg-blue-500 text-white hover:bg-blue-600 rounded-lg transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-500;
}

.kbd {
  @apply inline-block px-1 py-0.5 text-xs font-mono bg-gray-100 border border-gray-300 rounded;
}
</style>