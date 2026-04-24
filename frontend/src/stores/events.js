import { defineStore } from 'pinia'
import { ref } from 'vue'

const MAX_EVENTS = 200

export const useEventsStore = defineStore('events', () => {
  const items = ref([])   // newest first

  function push(event) {
    items.value.unshift(event)
    if (items.value.length > MAX_EVENTS) {
      items.value.length = MAX_EVENTS
    }
  }

  function pushMany(events) {
    // events from backend are oldest-first; reverse so newest is at index 0
    const reversed = [...events].reverse()
    items.value.unshift(...reversed)
    if (items.value.length > MAX_EVENTS) {
      items.value.length = MAX_EVENTS
    }
  }

  function clear() {
    items.value = []
  }

  return { items, push, pushMany, clear }
})
