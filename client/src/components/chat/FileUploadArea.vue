<template>
  <div class="border-t border-gray-200 p-4 bg-gray-50">
    <!-- Upload Area -->
    <div
      ref="dropZoneRef"
      :class="dropZoneClass"
      @click="triggerFileInput"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <input
        ref="fileInputRef"
        type="file"
        multiple
        accept=".txt,.log,.json,.png,.jpg,.jpeg,.gif,.pdf,.doc,.docx"
        class="hidden"
        @change="handleFileSelect"
      />

      <div class="text-center">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <div class="mt-4">
          <p class="text-sm text-gray-600">
            <span class="font-medium text-blue-600 hover:text-blue-500 cursor-pointer">
              Click to upload
            </span>
            or drag and drop
          </p>
          <p class="text-xs text-gray-500 mt-1">Images, logs, documents (max 10MB each)</p>
        </div>
      </div>
    </div>

    <!-- File List -->
    <div v-if="files.length > 0" class="mt-4 space-y-2">
      <div class="text-sm font-medium text-gray-700 mb-2">Attached Files ({{ files.length }})</div>

      <div v-for="file in files" :key="file.id" class="file-item">
        <div class="flex items-center space-x-3">
          <!-- File Icon -->
          <div class="flex-shrink-0">
            <FileIcon :file-type="file.type" class="w-6 h-6 text-gray-500" />
          </div>

          <!-- File Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-gray-900 truncate">
                {{ file.name }}
              </p>
              <p class="text-xs text-gray-500 ml-2">
                {{ formatFileSize(file.size) }}
              </p>
            </div>

            <!-- Progress Bar -->
            <div v-if="file.status === 'uploading'" class="mt-1">
              <div class="bg-gray-200 rounded-full h-1.5">
                <div
                  class="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                  :style="{ width: `${file.progress || 0}%` }"
                />
              </div>
              <p class="text-xs text-gray-500 mt-1">Uploading... {{ file.progress || 0 }}%</p>
            </div>

            <!-- Status Messages -->
            <div v-else-if="file.status === 'completed'" class="mt-1">
              <p class="text-xs text-green-600 flex items-center">
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                Upload complete
              </p>
            </div>

            <div v-else-if="file.status === 'error'" class="mt-1">
              <p class="text-xs text-red-600 flex items-center">
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clip-rule="evenodd"
                  />
                </svg>
                {{ file.error || 'Upload failed' }}
              </p>
            </div>

            <div v-else-if="file.status === 'pending'" class="mt-1">
              <p class="text-xs text-gray-500">Ready to upload</p>
            </div>
          </div>

          <!-- Remove Button -->
          <button
            @click="removeFile(file.id)"
            :disabled="file.status === 'uploading'"
            class="remove-button"
            title="Remove file"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Progress Summary -->
    <div v-if="isUploading && uploadProgress > 0" class="mt-4">
      <div class="flex items-center justify-between text-sm text-gray-600 mb-1">
        <span>Overall Progress</span>
        <span>{{ uploadProgress }}%</span>
      </div>
      <div class="bg-gray-200 rounded-full h-2">
        <div
          class="bg-blue-500 h-2 rounded-full transition-all duration-300"
          :style="{ width: `${uploadProgress}%` }"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, defineComponent, h } from 'vue'
import type { UploadedFile } from '@/types'

interface Props {
  files: UploadedFile[]
  isUploading?: boolean
  uploadProgress?: number
  maxFileSize?: number // in bytes
  maxFiles?: number
}

interface Emits {
  (e: 'files-selected', files: File[]): void
  (e: 'file-remove', fileId: string): void
  (e: 'upload-complete'): void
  (e: 'upload-error', error: string): void
}

const props = withDefaults(defineProps<Props>(), {
  isUploading: false,
  uploadProgress: 0,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFiles: 5,
})

const emit = defineEmits<Emits>()

const dropZoneRef = ref<HTMLElement>()
const fileInputRef = ref<HTMLInputElement>()
const isDragOver = ref(false)

const dropZoneClass = computed(() => {
  const baseClasses =
    'border-2 border-dashed rounded-lg p-6 cursor-pointer transition-colors duration-200'

  if (isDragOver.value) {
    return `${baseClasses} border-blue-400 bg-blue-50`
  } else {
    return `${baseClasses} border-gray-300 hover:border-gray-400`
  }
})

// File handling
const triggerFileInput = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    processFiles(Array.from(target.files))
    target.value = '' // Reset input
  }
}

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false

  if (event.dataTransfer?.files) {
    processFiles(Array.from(event.dataTransfer.files))
  }
}

const handleDragOver = () => {
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const processFiles = (files: File[]) => {
  // Validate file count
  if (props.files.length + files.length > props.maxFiles) {
    emit('upload-error', `Maximum ${props.maxFiles} files allowed`)
    return
  }

  // Validate file sizes and types
  const validFiles: File[] = []
  const errors: string[] = []

  for (const file of files) {
    if (file.size > props.maxFileSize) {
      errors.push(`${file.name} is too large (max ${formatFileSize(props.maxFileSize)})`)
      continue
    }

    if (!isValidFileType(file)) {
      errors.push(`${file.name} is not a supported file type`)
      continue
    }

    validFiles.push(file)
  }

  if (errors.length > 0) {
    emit('upload-error', errors.join(', '))
  }

  if (validFiles.length > 0) {
    emit('files-selected', validFiles)
  }
}

const removeFile = (fileId: string) => {
  emit('file-remove', fileId)
}

// File validation
const isValidFileType = (file: File) => {
  const allowedTypes = [
    'text/plain',
    'text/log',
    'application/json',
    'image/png',
    'image/jpeg',
    'image/gif',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ]

  const allowedExtensions = [
    '.txt',
    '.log',
    '.json',
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.pdf',
    '.doc',
    '.docx',
  ]

  return (
    allowedTypes.includes(file.type) ||
    allowedExtensions.some((ext) => file.name.toLowerCase().endsWith(ext))
  )
}

// Utility functions
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// File icon component
const FileIcon = defineComponent({
  props: {
    fileType: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const getIconPath = () => {
      if (props.fileType.startsWith('image/')) {
        return 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z'
      } else if (
        props.fileType.includes('json') ||
        props.fileType.includes('text') ||
        props.fileType.includes('log')
      ) {
        return 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
      } else if (props.fileType.includes('pdf')) {
        return 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z'
      } else {
        return 'M9 2a1 1 0 000 2h2a1 1 0 100-2H9z M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6h-2V9a1 1 0 10-2 0v2H8V9a1 1 0 10-2 0v2H4V5z'
      }
    }

    return () =>
      h(
        'svg',
        {
          fill: 'none',
          stroke: 'currentColor',
          viewBox: '0 0 24 24',
          class: 'w-6 h-6',
        },
        [
          h('path', {
            'stroke-linecap': 'round',
            'stroke-linejoin': 'round',
            'stroke-width': '2',
            d: getIconPath(),
          }),
        ],
      )
  },
})
</script>

<style scoped>
.file-item {
  @apply bg-white border border-gray-200 rounded-lg p-3;
}

.remove-button {
  @apply p-1 text-gray-400 hover:text-red-500 rounded transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed;
}

.remove-button:hover:not(:disabled) {
  @apply bg-red-50;
}
</style>
