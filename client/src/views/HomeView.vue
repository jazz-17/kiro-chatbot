<script setup lang="ts">
import { ref } from 'vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'
import type { Message, Citation, Conversation, UploadedFile } from '@/types'

// Demo data
const conversation = ref<Conversation>({
  id: 'demo-conversation',
  title: 'Demo Chat Session',
  createdAt: new Date(),
  updatedAt: new Date()
})

const initialMessages = ref<Message[]>([
  {
    id: 'msg-1',
    role: 'assistant',
    content: `# Welcome to the AI Chat Assistant! 

I'm here to help you with technical questions and support. You can:

- Ask me questions about **programming**, **troubleshooting**, or **technical concepts**
- Upload **log files** or **screenshots** for analysis
- Get responses with **citations** and **source references**

Try asking me something or uploading a file to see how it works!`,
    timestamp: new Date(Date.now() - 60000),
    citations: [
      {
        id: 'cite-1',
        title: 'Getting Started Guide',
        source: 'Documentation',
        excerpt: 'Learn how to use the AI assistant effectively for technical support.'
      }
    ]
  }
])

// Event handlers
const handleMessageSent = (message: string, files: UploadedFile[]) => {
  console.log('Message sent:', message, JSON.stringify(files, null, 2))
  
  // Simulate AI response after a delay
  setTimeout(() => {
    const response: Message = {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: `Thanks for your message: "${message}"

This is a **demo response** showing how the chat interface works. In a real implementation, this would be connected to:

- A backend API for processing messages
- AI providers for generating responses  
- Vector databases for RAG functionality
- File processing services

\`\`\`javascript
// Example code formatting
function processMessage(input) {
  return aiProvider.generateResponse(input);
}
\`\`\`

The interface supports:
1. **Markdown rendering** with syntax highlighting
2. **Real-time streaming** responses
3. **File uploads** with drag & drop
4. **Citation references** for sources`,
      timestamp: new Date(),
      citations: files.length > 0 ? [
        {
          id: 'cite-file',
          title: `Analysis of ${files[0].name}`,
          source: 'File Processing Service',
          excerpt: 'Automated analysis of uploaded file content.'
        }
      ] : []
    }
    
    chatWindowRef.value?.addMessage(response)
  }, 1000)
}

const handleCitationClicked = (citation: Citation) => {
  console.log('Citation clicked:', JSON.stringify(citation, null, 2))
  alert(`Citation clicked: ${citation.title}\n\nSource: ${citation.source}\n\nExcerpt: ${citation.excerpt}`)
}

const chatWindowRef = ref<InstanceType<typeof ChatWindow>>()
</script>

<template>
  <div class="h-[calc(100vh-200px)] bg-red-50023">
    <div class="bg-white rounded-lg shadow-lg h-full">
      <ChatWindow
        ref="chatWindowRef"
        :conversation="conversation"
        :initial-messages="initialMessages"
        @message-sent="handleMessageSent"
        @citation-clicked="handleCitationClicked"
      />
    </div>
  </div>
</template>
