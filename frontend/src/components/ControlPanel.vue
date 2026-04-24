<template>
  <div class="px-3 py-3 space-y-3">
    <div class="text-xs font-semibold text-gray-500 uppercase tracking-widest">Controls</div>

    <!-- Action buttons -->
    <div class="grid grid-cols-2 gap-1.5">
      <button class="btn-success col-span-1"
              :disabled="simStore.loading || simStore.isRunning"
              @click="handlePlay">▶ Play</button>

      <button class="btn-danger col-span-1"
              :disabled="simStore.loading || !simStore.isRunning"
              @click="handlePause">⏸ Pause</button>

      <button class="btn-ghost col-span-1"
              :disabled="simStore.loading || simStore.isRunning"
              @click="handleTick">⏭ Step</button>

      <button class="btn-ghost col-span-1"
              :disabled="simStore.loading"
              @click="handleReset">↺ Reset</button>
    </div>

    <!-- Speed control -->
    <div class="space-y-1.5">
      <div class="flex justify-between text-xs">
        <span class="text-gray-500">Speed</span>
        <span class="text-gray-300 font-mono">{{ SPEEDS[speedIdx] }}× / tick</span>
      </div>
      <input
        type="range" min="0" max="4" step="1"
        class="w-full accent-blue-500 cursor-pointer"
        :value="speedIdx"
        @input="onSpeedChange"
      />
      <div class="flex justify-between text-gray-700" style="font-size:9px; letter-spacing:0.02em">
        <span v-for="s in SPEEDS" :key="s">{{ s }}×</span>
      </div>
    </div>

    <!-- Status strip -->
    <div class="flex items-center justify-between text-xs text-gray-500 pt-1 border-t border-gray-800">
      <span>Tick <strong class="text-gray-300 tabular-nums">{{ simStore.currentTick }}</strong></span>
      <span>Tasks <strong class="text-gray-300">{{ taskCounts.total }}</strong>
            <span class="text-emerald-500 ml-1">✓{{ taskCounts.done }}</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { useUiStore } from '../stores/ui'

const simStore = useSimulationStore()
const uiStore  = useUiStore()

const SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0]
const speedIdx = ref(2)

const taskCounts = computed(() => {
  const tasks = Object.values(simStore.tasks)
  return {
    total: tasks.length,
    done:  tasks.filter(t => t.status === 'completed').length,
  }
})

async function handlePlay() {
  const interval = 1 / SPEEDS[speedIdx.value]
  await simStore.start(interval)
}

async function handlePause() {
  await simStore.stop()
}

async function handleTick() {
  await simStore.tick()
}

async function handleReset() {
  uiStore.selectAgent(null)
  await simStore.reset()
}

function onSpeedChange(e) {
  speedIdx.value = Number(e.target.value)
  uiStore.setSpeed(SPEEDS[speedIdx.value])
  if (simStore.isRunning) {
    simStore.stop().then(() => simStore.start(1 / SPEEDS[speedIdx.value]))
  }
}
</script>
