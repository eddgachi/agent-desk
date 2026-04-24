<template>
  <div>
    <h2>Simulation Control</h2>
    <button @click="createSim">Create New Simulation</button>
    <div v-if="simId">
      <p>Simulation ID: {{ simId }}</p>
      <p>Current Tick: {{ currentTick }}</p>
      <button @click="tick">Advance Tick</button>
      <button @click="reset">Reset Simulation</button>
      <h3>Agents</h3>
      <pre>{{ agents }}</pre>
      <h3>Tasks</h3>
      <pre>{{ tasks }}</pre>
      <h3>Events</h3>
      <pre>{{ events }}</pre>
    </div>
    <button @click="startAuto">Start Auto Tick (0.5s)</button>
    <button @click="stopAuto">Stop Auto Tick</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import apiClient from '../api/client'

const simId = ref(null)
const currentTick = ref(0)
const agents = ref({})
const tasks = ref({})
const events = ref([])

async function startAuto() {
  await apiClient.post(`/api/v1/simulations/${simId.value}/start`, null, { params: { interval: 0.5 } })
}
async function stopAuto() {
  await apiClient.post(`/api/v1/simulations/${simId.value}/stop`)
}

async function createSim() {
  const res = await apiClient.post('/api/v1/simulations', { seed: 42 })
  simId.value = res.data.sim_id
  currentTick.value = res.data.current_tick
  agents.value = res.data.agents
  tasks.value = res.data.tasks
  events.value = res.data.event_log
}

async function tick() {
  if (!simId.value) return
  const res = await apiClient.post(`/api/v1/simulations/${simId.value}/tick`)
  currentTick.value = res.data.new_tick
  // refresh state
  const stateRes = await apiClient.get(`/api/v1/simulations/${simId.value}`)
  agents.value = stateRes.data.agents
  tasks.value = stateRes.data.tasks
  events.value = stateRes.data.event_log
}

async function reset() {
  if (!simId.value) return
  const res = await apiClient.post(`/api/v1/simulations/${simId.value}/reset`)
  currentTick.value = res.data.current_tick
  agents.value = res.data.agents
  tasks.value = res.data.tasks
  events.value = res.data.event_log
}
</script>
