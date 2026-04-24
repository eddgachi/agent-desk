<template>
  <div class="flex flex-col h-screen overflow-hidden">
    <!-- ── Header ── -->
    <header class="flex-none flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700 z-10">
      <div class="flex items-center gap-3">
        <span class="text-blue-400 font-bold text-sm tracking-wider uppercase">AgentDesk</span>
        <span class="text-gray-600">|</span>
        <span class="text-gray-400 text-xs">Office Simulation</span>
      </div>

      <div class="flex items-center gap-4 text-xs text-gray-400">
        <span>
          Tick:
          <strong class="text-gray-200 tabular-nums">{{ simStore.currentTick }}</strong>
        </span>
        <span>
          Agents:
          <strong class="text-gray-200">{{ agentCount }}</strong>
        </span>
        <span
          class="flex items-center gap-1"
          :class="wsStore.connected ? 'text-emerald-400' : 'text-red-400'"
        >
          <span class="w-1.5 h-1.5 rounded-full"
            :class="wsStore.connected ? 'bg-emerald-400' : 'bg-red-400'"
          ></span>
          {{ wsStore.connected ? 'Live' : 'Disconnected' }}
        </span>
      </div>
    </header>

    <!-- ── Body: canvas + sidebar ── -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Canvas area -->
      <main class="flex-1 flex items-center justify-center bg-gray-950 overflow-hidden p-3">
        <OfficeMap />
      </main>

      <!-- Right sidebar -->
      <aside class="flex-none w-72 flex flex-col gap-2 p-2 bg-gray-900 border-l border-gray-700 overflow-y-auto scrollbar-thin">
        <ControlPanel />
        <AgentInspector />
        <TaskList />
      </aside>
    </div>

    <!-- ── Bottom: event feed ── -->
    <footer class="flex-none h-36 border-t border-gray-700 bg-gray-900">
      <EventFeed />
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { useWsStore } from '../stores/ws'
import AgentInspector from '../components/AgentInspector.vue'
import ControlPanel from '../components/ControlPanel.vue'
import EventFeed from '../components/EventFeed.vue'
import OfficeMap from '../components/OfficeMap.vue'
import TaskList from '../components/TaskList.vue'

const simStore = useSimulationStore()
const wsStore = useWsStore()

const agentCount = computed(() => Object.keys(simStore.agents).length)

onMounted(async () => {
  if (!simStore.currentSimId) {
    await simStore.createSimulation()
  }
  wsStore.connect(simStore.currentSimId)
})

onUnmounted(() => {
  wsStore.disconnect()
})
</script>
