<template>
  <div>
    <h1>Office Simulation – Phase 1</h1>
    <button @click="checkHealth">Check Backend Health</button>
    <pre>{{ healthStatus }}</pre>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import apiClient from '../api/client'

const healthStatus = ref('Not yet checked')

async function checkHealth() {
  try {
    const res = await apiClient.get('/health/')
    healthStatus.value = JSON.stringify(res.data, null, 2)
  } catch (err) {
    healthStatus.value = 'Error: ' + err.message
  }
}
</script>
