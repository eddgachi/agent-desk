import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useEventsStore } from './events.js'
import { useSimulationStore } from './simulation.js'

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const RECONNECT_DELAY = 3000

export const useWsStore = defineStore('ws', () => {
  const connected    = ref(false)
  const reconnecting = ref(false)
  const error        = ref(null)

  let socket      = null
  let simId       = null
  let retryTimer  = null
  let intentional = false  // true when we close on purpose

  // ── Public API ─────────────────────────────────────────
  function connect(id) {
    if (!id) return
    simId = id
    intentional = false
    _open()
  }

  function disconnect() {
    intentional = true
    clearTimeout(retryTimer)
    if (socket) {
      socket.close()
      socket = null
    }
    connected.value    = false
    reconnecting.value = false
  }

  // ── Internal ───────────────────────────────────────────
  function _open() {
    if (socket) {
      socket.onclose = null
      socket.close()
    }

    const url = `${WS_BASE}/api/v1/simulations/${simId}/ws`
    socket = new WebSocket(url)

    socket.onopen = () => {
      connected.value    = true
      reconnecting.value = false
      error.value        = null
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        _dispatch(msg)
      } catch (e) {
        console.warn('[WS] parse error', e)
      }
    }

    socket.onerror = (e) => {
      error.value = 'WebSocket error'
      console.warn('[WS] error', e)
    }

    socket.onclose = () => {
      connected.value = false
      if (!intentional) {
        reconnecting.value = true
        retryTimer = setTimeout(_open, RECONNECT_DELAY)
      }
    }
  }

  /**
   * Route incoming messages to the correct stores.
   *
   * Expected message shapes from backend:
   *   { type: 'tick_update',   data: { current_tick, agents, tasks, running } }
   *   { type: 'agent_update',  data: { agent } }
   *   { type: 'event',         data: { event_id, tick, type, payload } }
   *   { type: 'state_snapshot',data: { current_tick, agents, tasks, event_log } }
   */
  function _dispatch(msg) {
    const simStore    = useSimulationStore()
    const eventsStore = useEventsStore()

    switch (msg.type) {
      case 'tick_update':
        simStore.applyTickUpdate(msg.data)
        break

      case 'agent_update': {
        const agent = msg.data?.agent
        if (agent?.id) {
          simStore.agents[agent.id] = agent
        }
        break
      }

      case 'event':
        eventsStore.push(msg.data)
        break

      case 'state_snapshot':
        simStore.applyTickUpdate(msg.data)
        if (msg.data.event_log?.length) {
          eventsStore.pushMany(msg.data.event_log)
        }
        break

      default:
        console.debug('[WS] unknown message type:', msg.type)
    }
  }

  return {
    connected,
    reconnecting,
    error,
    connect,
    disconnect,
  }
})
