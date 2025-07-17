<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Button from '@/components/ui/button/Button.vue'
import HelloWorld from './components/HelloWorld.vue'
</script>

<template>
  <header>
    <Button>Click me</Button>
  </header>

  <RouterView />
</template>
