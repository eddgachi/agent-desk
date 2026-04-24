<template>
  <div class="panel">
    <div class="panel-header">Simulation Controls</div>
    <div class="panel-body space-y-3">

      <!-- Primary actions -->
      <div class="flex flex-wrap gap-1.5">
        <button class="btn-success" :disabled="simStore.loading || simStore.isRunning" @click="handlePlay">
          ▶ Play
        </button>
        <button class="btn-danger" :disabled="simStore.loading || !simStore.isRunning" @click="handlePause">
          ⏸ Pause
        </button>
        <button class="btn-ghost" :disabled="simStore.loading" @click="handleTick">
          ⏭ Step
        </button>
        <button class="btn-ghost" :disabled="simStore.loading" @click="handleReset">
          ↺ Reset
        </button>
      </div>

      <!-- Speed slider -->
      <div class="space-y-1">
        <div class="flex justify-between text-xs text-gray-400">
          <span>Speed</span>
          <span class="tabular-nums text-gray-200">{{ speedLabel }}</span>
        </div>
        <input
          type="range"
          min="0" max="4" step="1"
          :value="speedIndex"
          @input="handleSpeedChange"
          class="w-full accent-blue-500"
        />
        <div class="flex justify-between text-gray-600" style="font-size:9px">
          <span>0.25×</span><span>0.5×</span><span>1×</span><span>2×</span><span>4×</span>
        </div>
      </div>

      <!-- Status row -->
      <div class="flex items-center justify-between text-xs border-t border-gray-700 pt-2">
        <span class="text-gray-400">
          Tick <strong class="text-gray-200 tabular-nums">{{ simStore.currentTick }}</strong>
        </span>
        <span
          class="px-2 py-0.5 rounded-full text-xs font-medium"
          :class="simStore.isRunning ? 'bg-emerald-900 text-emerald-300' : 'bg-gray-700 text-gray-400'"
        >
          {{ simStore.isRunning ? 'Running' : 'Paused' }}
        </span>
      </div>

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
const speedIndex = ref(2)   // default 1×

const speedLabel = computed(() => `${SPEEDS[speedIndex.value]}×`)

async function handlePlay() {
  const interval = 1 / SPEEDS[speedIndex.value]
  await simStore.start(interval)
}

async function handlePause() {
  await simStore.stop()
}

async function handleTick() {
  await simStore.tick()
}

async function handleReset() {
  await simStore.reset()
}

function handleSpeedChange(e) {
  speedIndex.value = Number(e.target.value)
  uiStore.setSpeed(SPEEDS[speedIndex.value])
  // If already running, restart at new speed
  if (simStore.isRunning) {
    simStore.stop().then(() => {
      simStore.start(1 / SPEEDS[speedIndex.value])
    })
  }
}
</script>
