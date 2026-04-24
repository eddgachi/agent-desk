import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useEventsStore } from './events.js'
import { useSimulationStore } from './simulation.js'

const WS_BASE         = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const RECONNECT_DELAY = 3000
const PING_INTERVAL   = 25000

export const useWsStore = defineStore('ws', () => {
  const connected    = ref(false)
  const reconnecting = ref(false)
  const error        = ref(null)

  let socket       = null
  let simId        = null
  let retryTimer   = null
  let pingTimer    = null
  let intentional  = false

  // ── Public ─────────────────────────────────────────────
  function connect(id) {
    if (!id) return
    simId       = id
    intentional = false
    _open()
  }

  function disconnect() {
    intentional = true
    _clearTimers()
    if (socket) { socket.onclose = null; socket.close(); socket = null }
    connected.value    = false
    reconnecting.value = false
  }

  function sendCmd(cmd, extra = {}) {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ cmd, ...extra }))
    }
  }

  // ── Internal ────────────────────────────────────────────
  function _open() {
    if (socket) { socket.onclose = null; socket.close() }

    const url = `${WS_BASE}/api/v1/simulations/${simId}/ws`
    socket = new WebSocket(url)

    socket.onopen = () => {
      connected.value    = true
      reconnecting.value = false
      error.value        = null
      _startPing()
    }

    socket.onmessage = e => {
      try { _dispatch(JSON.parse(e.data)) } catch (ex) {
        console.warn('[WS] parse error', ex)
      }
    }

    socket.onerror = () => { error.value = 'WebSocket error' }

    socket.onclose = () => {
      connected.value = false
      _clearTimers()
      if (!intentional) {
        reconnecting.value = true
        retryTimer = setTimeout(_open, RECONNECT_DELAY)
      }
    }
  }

  function _startPing() {
    _clearPing()
    pingTimer = setInterval(() => sendCmd('ping'), PING_INTERVAL)
  }

  function _clearPing() {
    if (pingTimer) { clearInterval(pingTimer); pingTimer = null }
  }

  function _clearTimers() {
    _clearPing()
    if (retryTimer) { clearTimeout(retryTimer); retryTimer = null }
  }

  function _dispatch(msg) {
    const simStore    = useSimulationStore()
    const eventsStore = useEventsStore()

    switch (msg.type) {
      case 'tick_update':
        simStore.applyTickUpdate(msg.data)
        break

      case 'agent_update': {
        const a = msg.data?.agent
        if (a?.id) simStore.agents[a.id] = a
        break
      }

      case 'event':
        eventsStore.push(msg.data)
        break

      case 'state_snapshot': {
        const d = msg.data
        simStore.applyTickUpdate(d)
        if (d.event_log?.length) eventsStore.pushMany(d.event_log)
        break
      }

      case 'pong':
        break   // keep-alive acknowledged

      default:
        console.debug('[WS] unknown type:', msg.type)
    }
  }

  return { connected, reconnecting, error, connect, disconnect, sendCmd }
})
