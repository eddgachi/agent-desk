<template>
  <div class="flex flex-col h-screen overflow-hidden bg-gray-950 text-gray-200 select-none">

    <!-- ── Header ───────────────────────────────────────── -->
    <header class="flex-none flex items-center justify-between px-4 h-11
                   bg-gray-900 border-b border-gray-800 z-10 shadow-md">
      <div class="flex items-center gap-3">
        <span class="text-blue-400 font-bold text-sm tracking-widest uppercase">AgentDesk</span>
        <span class="text-gray-700">│</span>
        <span class="text-gray-500 text-xs">Office Simulation</span>
      </div>

      <div class="flex items-center gap-5 text-xs">
        <!-- Tick counter -->
        <div class="flex items-center gap-1.5 text-gray-400">
          <span class="text-gray-600">TICK</span>
          <span class="font-mono font-bold text-gray-200 tabular-nums w-10 text-right">
            {{ simStore.currentTick }}
          </span>
        </div>

        <!-- Agent count -->
        <div class="flex items-center gap-1.5 text-gray-400">
          <span class="text-gray-600">AGENTS</span>
          <span class="font-bold text-gray-200">{{ agentCount }}</span>
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
        <div class="flex items-center gap-1.5"
             :class="wsStore.connected ? 'text-emerald-400' : wsStore.reconnecting ? 'text-yellow-400' : 'text-red-400'">
          <span class="w-1.5 h-1.5 rounded-full"
                :class="wsStore.connected ? 'bg-emerald-400'
                        : wsStore.reconnecting ? 'bg-yellow-400 animate-pulse'
                        : 'bg-red-400'" />
          <span>{{ wsStore.connected ? 'Live' : wsStore.reconnecting ? 'Reconnecting…' : 'Offline' }}</span>
        </div>
      </div>
    </header>

    <!-- ── Body ─────────────────────────────────────────── -->
    <div class="flex flex-1 min-h-0 overflow-hidden">

      <!-- Canvas area -->
      <main class="flex-1 flex items-center justify-center bg-gray-950 p-3 overflow-hidden">
        <OfficeMap />
      </main>

      <!-- Right sidebar -->
      <aside class="flex-none w-72 flex flex-col gap-0 bg-gray-900 border-l border-gray-800 overflow-y-auto scrollbar-thin">
        <ControlPanel />
        <div class="border-t border-gray-800" />
        <AgentInspector />
        <div class="border-t border-gray-800" />
        <TaskList />
      </aside>
    </div>

    <!-- ── Activity feed ─────────────────────────────────── -->
    <footer class="flex-none h-32 border-t border-gray-800 bg-gray-900">
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
const wsStore  = useWsStore()

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
