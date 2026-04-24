<template>
  <div class="relative">
    <canvas
      ref="canvasRef"
      :width="CANVAS_W"
      :height="CANVAS_H"
      class="rounded-lg cursor-pointer block"
      :style="{ width: displayW + 'px', height: displayH + 'px' }"
      @click="handleClick"
      @mousemove="handleMouseMove"
    />
    <!-- Tooltip -->
    <Transition name="fade">
      <div
        v-if="tooltip"
        class="absolute pointer-events-none bg-gray-800 border border-gray-600 text-xs text-gray-200 rounded px-2 py-1 shadow-lg"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      >
        <span class="font-semibold">{{ tooltip.name }}</span>
        <span class="text-gray-400 ml-1">· {{ tooltip.role }}</span>
        <br />
        <span :class="`status-${tooltip.status}`">{{ tooltip.status }}</span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CANVAS_H, CANVAS_W } from '../canvas/officeLayout.js'
import { AGENT_RADIUS, renderFrame } from '../canvas/renderer.js'
import { tickInterpolation } from '../canvas/useAgentInterpolation.js'
import { useAnimationLoop } from '../canvas/useAnimationLoop.js'
import { useSimulationStore } from '../stores/simulation'
import { useUiStore } from '../stores/ui'

const simStore = useSimulationStore()
const uiStore = useUiStore()

const canvasRef = ref(null)
const tooltip = ref(null)

// Responsive: scale canvas to fit window while keeping aspect ratio
const MAX_W = 1100
const aspect = CANVAS_H / CANVAS_W
const displayW = computed(() => Math.min(MAX_W, window.innerWidth - 260))
const displayH = computed(() => Math.round(displayW.value * aspect))

// Scale factor from CSS display size → canvas pixel coords
function getScale() {
  return CANVAS_W / displayW.value
}

// ── Animation loop ────────────────────────────────────────
let lastTs = 0
useAnimationLoop((ts) => {
  const dt = ts - lastTs
  lastTs = ts

  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const agents = Object.values(simStore.agents)

  tickInterpolation(agents, dt)
  renderFrame(ctx, agents, uiStore.selectedAgentId, ts)
})

// ── Hit testing ───────────────────────────────────────────
function getAgentAt(canvasX, canvasY) {
  const agents = Object.values(simStore.agents)
  for (const agent of agents) {
    const rx = agent._renderX ?? agent.position_x
    const ry = agent._renderY ?? agent.position_y
    const dx = canvasX - rx
    const dy = canvasY - ry
    if (Math.sqrt(dx * dx + dy * dy) <= AGENT_RADIUS + 2) return agent
  }
  return null
}

function canvasCoordsFromEvent(e) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scale = getScale()
  return {
    x: (e.clientX - rect.left) * scale,
    y: (e.clientY - rect.top) * scale,
  }
}

function handleClick(e) {
  const { x, y } = canvasCoordsFromEvent(e)
  const agent = getAgentAt(x, y)
  uiStore.selectAgent(agent ? agent.id : null)
}

function handleMouseMove(e) {
  const { x, y } = canvasCoordsFromEvent(e)
  const agent = getAgentAt(x, y)
  if (agent) {
    const scale = getScale()
    tooltip.value = {
      name: agent.name,
      role: agent.role,
      status: agent.status,
      // position in div coords (not canvas coords)
      x: (agent._renderX ?? agent.position_x) / scale + 16,
      y: (agent._renderY ?? agent.position_y) / scale - 20,
    }
  } else {
    tooltip.value = null
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
