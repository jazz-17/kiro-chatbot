<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-900">AI Chat Assistant</h1>
          </div>
          <nav class="flex space-x-4">
            <RouterLink 
              to="/" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Chat
            </RouterLink>
            <RouterLink 
              to="/about" 
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              About
            </RouterLink>
          </nav>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.router-link-active {
  @apply text-blue-600 bg-blue-50;
}
</style>
