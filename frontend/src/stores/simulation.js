import { defineStore } from 'pinia'
import { ref } from 'vue'
import { simulationApi } from '../api/simulationApi.js'

export const useSimulationStore = defineStore('simulation', () => {
  const currentSimId = ref(null)
  const agents       = ref({})
  const tasks        = ref({})
  const currentTick  = ref(0)
  const loading      = ref(false)
  const isRunning    = ref(false)

  // ── Lifecycle ──────────────────────────────────────────
  async function createSimulation(seed = null) {
    loading.value = true
    try {
      const res = await simulationApi.create(seed)
      _applyState(res.data)
    } finally {
      loading.value = false
    }
    return currentSimId.value
  }

  async function fetchState() {
    if (!currentSimId.value) return
    const res = await simulationApi.get(currentSimId.value)
    _applyState(res.data)
  }

  async function tick() {
    if (!currentSimId.value) return
    loading.value = true
    try {
      await simulationApi.tick(currentSimId.value)
      await fetchState()
    } finally {
      loading.value = false
    }
  }

  async function reset() {
    if (!currentSimId.value) return
    loading.value = true
    try {
      const res = await simulationApi.reset(currentSimId.value)
      _applyState(res.data)
    } finally {
      loading.value = false
    }
  }

  async function start(interval = 1.0) {
    if (!currentSimId.value) return
    await simulationApi.startAuto(currentSimId.value, interval)
    isRunning.value = true
  }

  async function stop() {
    if (!currentSimId.value) return
    await simulationApi.stopAuto(currentSimId.value)
    isRunning.value = false
  }

  // ── State patch (called by WS store too) ───────────────
  function applyTickUpdate(data) {
    if (data.agents)       agents.value = data.agents
    if (data.tasks)        tasks.value  = data.tasks
    if (data.current_tick != null) currentTick.value = data.current_tick
    if (data.running      != null) isRunning.value   = data.running
  }

  function _applyState(data) {
    if (data.sim_id)            currentSimId.value = data.sim_id
    if (data.agents)            agents.value       = data.agents
    if (data.tasks)             tasks.value        = data.tasks
    if (data.current_tick != null) currentTick.value = data.current_tick
    if (data.running      != null) isRunning.value   = data.running
    // event_log is delegated to events store via ws.js on state_snapshot
  }

  return {
    currentSimId,
    agents,
    tasks,
    currentTick,
    loading,
    isRunning,
    createSimulation,
    fetchState,
    tick,
    reset,
    start,
    stop,
    applyTickUpdate,
  }
})
