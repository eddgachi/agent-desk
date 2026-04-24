import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const selectedAgentId  = ref(null)
  const inspectorVisible = ref(true)
  const feedVisible      = ref(true)
  const simSpeed         = ref(1.0)   // ticks/sec when running

  function selectAgent(id) {
    selectedAgentId.value = id === selectedAgentId.value ? null : id
  }

  function setSpeed(s) {
    simSpeed.value = s
  }

  return {
    selectedAgentId,
    inspectorVisible,
    feedVisible,
    simSpeed,
    selectAgent,
    setSpeed,
  }
})
