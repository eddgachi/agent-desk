<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex-none flex items-center justify-between px-3 py-2 border-b border-gray-800">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-widest">Activity</span>
        <span class="bg-gray-800 text-gray-400 text-xs px-1.5 py-0.5 rounded-full tabular-nums">
          {{ eventsStore.items.length }}
        </span>
      </div>
      <button class="text-xs text-gray-600 hover:text-gray-400" @click="eventsStore.clear()">
        Clear
      </button>
    </div>

    <!-- Events list -->
    <div ref="listRef" class="flex-1 overflow-y-auto scrollbar-thin font-mono text-xs px-1">
      <div v-if="!eventsStore.items.length"
           class="flex items-center justify-center h-full text-gray-600 italic">
        Waiting for events…
      </div>
      <TransitionGroup name="feed" tag="div">
        <div
          v-for="ev in eventsStore.items.slice(0, 100)"
          :key="ev.event_id ?? `${ev.tick}-${ev.type}`"
          class="flex items-baseline gap-2 py-0.5 px-1.5 rounded hover:bg-gray-800/50 transition-colors group cursor-default"
          @click="maybeSelectAgent(ev)"
        >
          <span class="text-gray-700 tabular-nums w-8 text-right flex-none">{{ ev.tick }}</span>
          <span class="flex-none w-32 truncate" :class="typeColor(ev.type)">{{ ev.type }}</span>
          <span class="text-gray-400 truncate flex-1">{{ summarise(ev) }}</span>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useEventsStore } from '../stores/events.js'
import { useUiStore } from '../stores/ui.js'
import { useSimulationStore } from '../stores/simulation.js'

const eventsStore = useEventsStore()
const uiStore     = useUiStore()
const simStore    = useSimulationStore()
const listRef     = ref(null)

const TYPE_COLOR = {
  task_started:         'text-blue-400',
  task_completed:       'text-emerald-400',
  task_assigned:        'text-sky-400',
  task_failed:          'text-red-400',
  agent_wandering:      'text-gray-500',
  chat_started:         'text-pink-400',
  chat_ended:           'text-pink-300',
  break_started:        'text-green-400',
  break_ended:          'text-green-300',
  meeting_started:      'text-purple-400',
  meeting_ended:        'text-purple-300',
  simulation_created:   'text-blue-300',
}

function typeColor(type) {
  return TYPE_COLOR[type] ?? 'text-gray-400'
}

function summarise(ev) {
  const p = ev.payload ?? {}
  if (p.agent_name && p.task_title) return `${p.agent_name} → ${p.task_title}`
  if (p.agent_name && p.target)     return `${p.agent_name} → (${Math.round(p.target.x ?? 0)}, ${Math.round(p.target.y ?? 0)})`
  if (p.agent_name)                 return p.agent_name
  if (p.task_title)                 return p.task_title
  if (p.agents)                     return p.agents.join(', ')
  // Fallback: first string value found
  const first = Object.values(p).find(v => typeof v === 'string')
  return first ?? ''
}

function maybeSelectAgent(ev) {
  const id = ev.payload?.agent_id ?? ev.payload?.agent_ids?.[0]
  if (id && simStore.agents[id]) uiStore.selectAgent(id)
}

// Auto-scroll to top (newest item) when new events arrive
watch(() => eventsStore.items.length, () => {
  if (listRef.value) listRef.value.scrollTop = 0
})
</script>

<style scoped>
.feed-enter-active { transition: all 0.18s ease; }
.feed-enter-from   { opacity: 0; transform: translateY(-4px); }
</style>
