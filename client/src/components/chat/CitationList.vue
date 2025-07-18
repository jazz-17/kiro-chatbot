<template>
  <div :class="containerClass">
    <div class="text-xs text-gray-600 mb-2 font-medium">Sources:</div>
    <div class="space-y-1">
      <button
        v-for="(citation, index) in citations"
        :key="citation.id"
        @click="handleCitationClick(citation)"
        class="citation-button"
        :title="citation.excerpt || citation.title"
      >
        <div class="flex items-start space-x-2">
          <span class="citation-number">{{ index + 1 }}</span>
          <div class="flex-1 text-left">
            <div class="citation-title">{{ citation.title }}</div>
            <div class="citation-source">{{ citation.source }}</div>
            <div v-if="citation.excerpt" class="citation-excerpt">
              {{ truncateText(citation.excerpt, 100) }}
            </div>
          </div>
          <svg 
            class="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              stroke-width="2" 
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Citation } from '@/types'

interface Props {
  citations: Citation[]
  align?: 'left' | 'right'
}

interface Emits {
  (e: 'citation-click', citation: Citation): void
}

const props = withDefaults(defineProps<Props>(), {
  align: 'left'
})

const emit = defineEmits<Emits>()

const containerClass = computed(() => {
  const baseClasses = 'mt-2 max-w-sm'
  return props.align === 'right' 
    ? `${baseClasses} ml-auto` 
    : baseClasses
})

const handleCitationClick = (citation: Citation) => {
  emit('citation-click', citation)
}

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trim() + '...'
}
</script>

<style scoped>
.citation-button {
  @apply w-full p-2 bg-gray-50 hover:bg-gray-100 rounded-md border border-gray-200 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50;
}

.citation-number {
  @apply inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-white bg-blue-500 rounded-full flex-shrink-0;
}

.citation-title {
  @apply text-sm font-medium text-gray-900 line-clamp-1;
}

.citation-source {
  @apply text-xs text-gray-600 mt-0.5;
}

.citation-excerpt {
  @apply text-xs text-gray-500 mt-1 line-clamp-2;
}

/* Line clamp utilities */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>