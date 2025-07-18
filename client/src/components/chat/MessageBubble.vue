<template>
  <div class="flex" :class="alignmentClass">
    <!-- Avatar -->
    <div v-if="message.role === 'assistant'" class="flex-shrink-0 mr-3">
      <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
        <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      </div>
    </div>
    
    <!-- Message Content -->
    <div class="flex flex-col max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-xl">
      <!-- Message Bubble -->
      <div :class="bubbleClass">
        <!-- Markdown Content -->
        <div 
          v-if="message.role === 'assistant'"
          class="prose prose-sm max-w-none"
          v-html="renderedContent"
        ></div>
        
        <!-- Plain Text for User Messages -->
        <div v-else class="whitespace-pre-wrap">
          {{ message.content }}
        </div>
        
        <!-- Streaming Indicator -->
        <div v-if="isStreaming" class="flex items-center mt-2">
          <div class="flex space-x-1">
            <div class="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
            <div class="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
            <div class="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
          </div>
          <span class="ml-2 text-xs text-gray-500">AI is typing...</span>
        </div>
      </div>
      
      <!-- Citations -->
      <CitationList
        v-if="message.citations && message.citations.length > 0"
        :citations="message.citations"
        :align="message.role === 'user' ? 'right' : 'left'"
        @citation-click="handleCitationClick"
      />
      
      <!-- Timestamp -->
      <div :class="timestampClass">
        {{ formatTimestamp(message.timestamp) }}
      </div>
    </div>
    
    <!-- User Avatar -->
    <div v-if="message.role === 'user'" class="flex-shrink-0 ml-3">
      <div class="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
        <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import CitationList from './CitationList.vue'
import type { Message, Citation } from '@/types'

interface Props {
  message: Message
  isStreaming?: boolean
}

interface Emits {
  (e: 'citation-click', citation: Citation): void
}

const props = withDefaults(defineProps<Props>(), {
  isStreaming: false
})

const emit = defineEmits<Emits>()

// Configure marked for better rendering
marked.setOptions({
  breaks: true,
  gfm: true
})

// Computed properties for styling
const alignmentClass = computed(() => {
  return props.message.role === 'user' ? 'justify-end' : 'justify-start'
})

const bubbleClass = computed(() => {
  const baseClasses = 'px-4 py-2 rounded-lg shadow-sm'
  
  if (props.message.role === 'user') {
    return `${baseClasses} bg-blue-500 text-white`
  } else {
    return `${baseClasses} bg-gray-100 text-gray-800`
  }
})

const timestampClass = computed(() => {
  const baseClasses = 'text-xs text-gray-500 mt-1'
  return props.message.role === 'user' 
    ? `${baseClasses} text-right` 
    : `${baseClasses} text-left`
})

// Render markdown content
const renderedContent = computed(() => {
  if (props.message.role !== 'assistant') {
    return props.message.content
  }
  
  try {
    return marked.parse(props.message.content)
  } catch (error) {
    console.error('Markdown parsing error:', error)
    return `<p>${props.message.content}</p>`
  }
})

// Format timestamp
const formatTimestamp = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) {
    return 'Just now'
  } else if (minutes < 60) {
    return `${minutes}m ago`
  } else if (minutes < 1440) {
    const hours = Math.floor(minutes / 60)
    return `${hours}h ago`
  } else {
    return timestamp.toLocaleDateString()
  }
}

// Handle citation clicks
const handleCitationClick = (citation: Citation) => {
  emit('citation-click', citation)
}
</script>

<style scoped>
/* Prose styling for markdown content */
.prose {
  color: inherit;
}

.prose h1,
.prose h2,
.prose h3,
.prose h4,
.prose h5,
.prose h6 {
  color: inherit;
  margin-top: 1em;
  margin-bottom: 0.5em;
}

.prose h1:first-child,
.prose h2:first-child,
.prose h3:first-child,
.prose h4:first-child,
.prose h5:first-child,
.prose h6:first-child {
  margin-top: 0;
}

.prose p {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose p:first-child {
  margin-top: 0;
}

.prose p:last-child {
  margin-bottom: 0;
}

.prose ul,
.prose ol {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
  padding-left: 1.5em;
}

.prose li {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

.prose code {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
}

.prose pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 0.5em;
  overflow-x: auto;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose pre code {
  background-color: transparent;
  padding: 0;
}

.prose blockquote {
  border-left: 4px solid rgba(0, 0, 0, 0.2);
  padding-left: 1em;
  margin-left: 0;
  font-style: italic;
  color: rgba(0, 0, 0, 0.7);
}

.prose a {
  color: #3b82f6;
  text-decoration: underline;
}

.prose a:hover {
  color: #1d4ed8;
}

.prose table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose th,
.prose td {
  border: 1px solid rgba(0, 0, 0, 0.2);
  padding: 0.5em;
  text-align: left;
}

.prose th {
  background-color: rgba(0, 0, 0, 0.05);
  font-weight: 600;
}
</style>