<template>
  <div class="flex flex-col h-screen overflow-hidden bg-gray-900 text-gray-200 select-none">
    <!-- ── Header (dark navbar) ────────────────────────── -->
    <header
      class="flex-none flex items-center justify-between px-4 h-11 bg-gray-900 border-b border-gray-800 z-10 shadow-md"
    >
      <div class="flex items-center gap-4">
        <span class="text-indigo-400 font-bold text-sm tracking-widest uppercase">AgentDesk</span>
        <span class="text-gray-700">│</span>
        <span class="text-gray-500 text-xs">Office Simulation</span>
      </div>

      <div class="flex items-center gap-5 text-xs">
        <!-- Tick counter -->
        <div class="flex items-center gap-1.5 text-gray-400">
          <span class="text-gray-500">TICK</span>
          <span class="font-mono font-bold text-gray-100 tabular-nums w-10 text-right">
            {{ simStore.currentTick }}
          </span>
        </div>

        <!-- Agent count -->
        <div class="flex items-center gap-1.5 text-gray-400">
          <span class="text-gray-500">AGENTS</span>
          <span class="font-bold text-gray-100">{{ agentCount }}</span>
        </div>

        <!-- Running state -->
        <div class="flex items-center gap-1.5">
          <span
            class="w-2 h-2 rounded-full"
            :class="simStore.isRunning ? 'bg-emerald-400 animate-pulse' : 'bg-gray-600'"
          />
          <span :class="simStore.isRunning ? 'text-emerald-400' : 'text-gray-500'">
            {{ simStore.isRunning ? 'Running' : 'Paused' }}
          </span>
        </div>

        <!-- WS connection -->
        <div
          class="flex items-center gap-1.5"
          :class="wsStore.connected ? 'text-emerald-400' : wsStore.reconnecting ? 'text-amber-400' : 'text-red-400'"
        >
          <span
            class="w-1.5 h-1.5 rounded-full"
            :class="
              wsStore.connected ? 'bg-emerald-400' : wsStore.reconnecting ? 'bg-amber-400 animate-pulse' : 'bg-red-400'
            "
          />
          <span>{{ wsStore.connected ? 'Live' : wsStore.reconnecting ? 'Reconnecting…' : 'Offline' }}</span>
        </div>

        <!-- Nav links -->
        <router-link
          to="/about"
          class="ml-2 px-2.5 py-1 rounded text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
        >
          About
        </router-link>
      </div>
    </header>

    <!-- ── Body ─────────────────────────────────────────── -->
    <div class="flex flex-1 min-h-0 overflow-hidden">
      <!-- Canvas area (takes all remaining space) -->
      <main class="flex-1 flex items-center justify-center bg-gray-800 p-2 overflow-hidden">
        <OfficeMap />
      </main>

      <!-- Right sidebar (dark) -->
      <aside
        class="flex-none w-64 flex flex-col gap-0 bg-gray-900 border-l border-gray-800 overflow-y-auto scrollbar-thin"
      >
        <ControlPanel />
        <div class="border-t border-gray-800" />
        <AgentInspector />
        <div class="border-t border-gray-800" />
        <TaskList />
      </aside>
    </div>

    <!-- ── Activity feed (dark) ─────────────────────────── -->
    <footer class="flex-none h-36 border-t border-gray-800 bg-gray-900">
      <EventFeed />
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import AgentInspector from '../components/AgentInspector.vue'
import ControlPanel from '../components/ControlPanel.vue'
import EventFeed from '../components/EventFeed.vue'
import OfficeMap from '../components/OfficeMap.vue'
import TaskList from '../components/TaskList.vue'
import { useSimulationStore } from '../stores/simulation'
import { useWsStore } from '../stores/ws'

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
