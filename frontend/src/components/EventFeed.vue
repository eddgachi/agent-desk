<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex-none flex items-center justify-between px-3 py-1.5 border-b border-gray-800">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Activity Feed</span>
        <span class="bg-gray-800 text-gray-400 text-xs px-1.5 py-0.5 rounded-full tabular-nums font-mono">
          {{ eventsStore.items.length }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <!-- Filter buttons -->
        <button
          v-for="opt in filterOptions"
          :key="opt.key"
          class="text-[10px] px-1.5 py-0.5 rounded transition-colors"
          :class="filter === opt.key ? 'bg-gray-700 text-gray-200' : 'text-gray-600 hover:text-gray-400'"
          @click="filter = opt.key"
        >
          {{ opt.label }}
        </button>
        <span class="text-gray-700 mx-0.5">|</span>
        <button class="text-[10px] text-gray-600 hover:text-gray-400 transition-colors" @click="eventsStore.clear()">
          Clear
        </button>
      </div>
    </div>

    <!-- Events list (horizontal scrolling for compactness) -->
    <div ref="listRef" class="flex-1 overflow-y-auto scrollbar-thin text-xs">
      <div v-if="!filteredEvents.length" class="flex items-center justify-center h-full text-gray-600 italic text-xs">
        {{ eventsStore.items.length ? 'No matching events' : 'Waiting for events…' }}
      </div>
      <TransitionGroup name="feed" tag="div" class="divide-y divide-gray-800/40">
        <div
          v-for="ev in filteredEvents"
          :key="ev.event_id ?? `${ev.tick}-${ev.type}`"
          class="flex items-start gap-2 px-3 py-1.5 hover:bg-gray-800/40 transition-colors cursor-pointer group"
          @click="maybeSelectAgent(ev)"
        >
          <!-- Icon -->
          <span class="flex-none mt-0.5 text-xs leading-none">{{ eventIcon(ev.type) }}</span>

          <!-- Main content -->
          <div class="flex-1 min-w-0 flex items-baseline gap-2">
            <!-- Tick -->
            <span class="text-gray-700 tabular-nums w-8 text-right flex-none font-mono text-[10px]">{{ ev.tick }}</span>
            <!-- Type badge -->
            <span
              class="flex-none px-1 py-0.5 rounded font-medium text-[10px] leading-none"
              :class="typeBadge(ev.type)"
            >
              {{ ev.type.replace('_', ' ') }}
            </span>
            <!-- Summary -->
            <span class="text-gray-300 truncate flex-1 text-xs">{{ summarise(ev) }}</span>
          </div>

          <!-- Agent name tag -->
          <span
            v-if="ev.payload?.agent_name"
            class="flex-none text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 truncate max-w-[80px]"
          >
            {{ ev.payload.agent_name.split(' ')[0] }}
          </span>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useEventsStore } from '../stores/events.js'
import { useSimulationStore } from '../stores/simulation.js'
import { useUiStore } from '../stores/ui.js'

const eventsStore = useEventsStore()
const uiStore = useUiStore()
const simStore = useSimulationStore()
const listRef = ref(null)
const filter = ref('all')

const filterOptions = [
  { key: 'all', label: 'All' },
  { key: 'tasks', label: 'Tasks' },
  { key: 'chats', label: 'Chats' },
  { key: 'movement', label: 'Move' },
]

const EVENT_ICONS = {
  task_started: '📋',
  task_completed: '✅',
  task_assigned: '📎',
  task_failed: '❌',
  agent_spawned: '🟢',
  agent_wandering: '🚶',
  agent_arrived: '📍',
  chat_started: '💬',
  chat_ended: '💤',
  break_started: '☕',
  break_ended: '🔋',
  meeting_started: '📊',
  meeting_ended: '📁',
  simulation_created: '🏗️',
}

const TYPE_BADGE = {
  task_started: 'bg-blue-900/60 text-blue-300',
  task_completed: 'bg-emerald-900/60 text-emerald-300',
  task_assigned: 'bg-sky-900/60 text-sky-300',
  task_failed: 'bg-red-900/60 text-red-300',
  agent_spawned: 'bg-gray-700 text-gray-300',
  agent_wandering: 'bg-amber-900/60 text-amber-300',
  agent_arrived: 'bg-gray-700 text-gray-300',
  chat_started: 'bg-pink-900/60 text-pink-300',
  chat_ended: 'bg-pink-900/30 text-pink-400',
  break_started: 'bg-emerald-900/60 text-emerald-300',
  break_ended: 'bg-emerald-900/30 text-emerald-400',
  meeting_started: 'bg-purple-900/60 text-purple-300',
  meeting_ended: 'bg-purple-900/30 text-purple-400',
  simulation_created: 'bg-indigo-900/60 text-indigo-300',
}

const FILTER_GROUPS = {
  all: () => true,
  tasks: (t) => t.startsWith('task_'),
  chats: (t) => t.startsWith('chat_'),
  movement: (t) => t === 'agent_wandering' || t === 'agent_arrived' || t === 'agent_spawned',
}

const filteredEvents = computed(() => {
  const f = FILTER_GROUPS[filter.value] || FILTER_GROUPS.all
  return eventsStore.items.slice(0, 150).filter((e) => f(e.type))
})

function eventIcon(type) {
  return EVENT_ICONS[type] || '📌'
}

function typeBadge(type) {
  return TYPE_BADGE[type] || 'bg-gray-700 text-gray-400'
}

function summarise(ev) {
  const p = ev.payload ?? {}
  if (p.agent_name && p.task_title) return `${p.agent_name} → ${p.task_title}`
  if (p.agent_name && p.target) {
    const tx = Math.round(p.target.x ?? 0)
    const ty = Math.round(p.target.y ?? 0)
    // Try to name the location
    const loc = locationName(tx, ty)
    return `${p.agent_name} heading to ${loc || `(${tx}, ${ty})`}`
  }
  if (p.agent_name) return p.agent_name
  if (p.task_title) return p.task_title
  if (p.agents) return p.agents.join(', ')
  const first = Object.values(p).find((v) => typeof v === 'string')
  return first || JSON.stringify(p).slice(0, 60)
}

function locationName(x, y) {
  // Match against known waypoints from the office layout
  const locations = {
    '92,155': 'Desk A1',
    '210,155': 'Desk A2',
    '328,155': 'Desk A3',
    '446,155': 'Desk A4',
    '92,275': 'Desk B1',
    '210,275': 'Desk B2',
    '328,275': 'Desk B3',
    '446,275': 'Desk B4',
    '726,110': 'Meeting A',
    '726,309': 'Meeting B',
    '200,530': 'Break Room',
    '556,310': 'Corridor',
    '556,390': 'Printer',
    '455,530': 'Server Room',
  }
  return locations[`${x},${y}`] || null
}

function maybeSelectAgent(ev) {
  const id = ev.payload?.agent_id ?? ev.payload?.agent_ids?.[0]
  if (id && simStore.agents[id]) uiStore.selectAgent(id)
}

// Auto-scroll to top (newest item) when new events arrive
watch(
  () => eventsStore.items.length,
  () => {
    if (listRef.value) listRef.value.scrollTop = 0
  },
)
</script>

<style scoped>
.feed-enter-active {
  transition: all 0.18s ease;
}
.feed-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
