<template>
  <div class="flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-3 py-2.5 border-b border-gray-800">
      <span class="text-xs font-semibold text-gray-500 uppercase tracking-widest">Inspector</span>
      <button v-if="agent" class="text-gray-600 hover:text-gray-300 text-xs leading-none"
              @click="uiStore.selectAgent(null)">✕</button>
    </div>

    <!-- Empty state -->
    <div v-if="!agent" class="flex flex-col items-center justify-center py-8 text-center px-4">
      <div class="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center mb-3 text-lg">🖱</div>
      <p class="text-gray-500 text-xs">Click an agent on the map to inspect</p>
    </div>

    <!-- Agent details -->
    <div v-else class="px-3 py-3 space-y-3 text-xs overflow-y-auto scrollbar-thin">

      <!-- Identity row -->
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm text-white flex-none shadow-lg"
             :style="{ backgroundColor: roleColor, boxShadow: `0 0 12px ${roleColor}55` }">
          {{ initials }}
        </div>
        <div>
          <div class="font-semibold text-gray-100 text-sm">{{ agent.name }}</div>
          <div class="text-gray-400 capitalize">{{ agent.role }}</div>
        </div>
        <div class="ml-auto">
          <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="statusClass">
            {{ agent.status }}
          </span>
        </div>
      </div>

      <!-- Stats bars -->
      <div class="bg-gray-800/50 rounded-lg p-2.5 space-y-2">
        <StatBar label="Energy" :value="agent.energy"  color="bg-emerald-500" />
        <StatBar label="Focus"  :value="agent.focus"   color="bg-blue-500" />
        <StatBar label="Mood"   :value="agent.mood"    color="bg-pink-500" />
      </div>

      <!-- Position -->
      <div class="grid grid-cols-2 gap-1.5 text-xs">
        <InfoRow label="Position"
                 :value="`(${fmt(agent.position_x)}, ${fmt(agent.position_y)})`" mono />
        <InfoRow v-if="agent.target_x != null" label="Target"
                 :value="`(${fmt(agent.target_x)}, ${fmt(agent.target_y)})`"
                 mono valueClass="text-yellow-400" />
        <InfoRow v-if="agent.desk_id" label="Desk" :value="agent.desk_id" />
      </div>

      <!-- Current task -->
      <div v-if="currentTask" class="bg-gray-800 rounded-lg p-2.5 space-y-1.5">
        <div class="flex items-start justify-between gap-1">
          <span class="text-gray-100 font-medium leading-snug">{{ currentTask.title }}</span>
          <span class="flex-none px-1.5 py-0.5 rounded text-xs"
                :class="taskTypeClass(currentTask.type)">{{ currentTask.type }}</span>
        </div>
        <p class="text-gray-400 text-xs leading-relaxed">{{ currentTask.description }}</p>
        <div v-if="agent.remaining_task_ticks != null" class="flex items-center gap-2">
          <div class="flex-1 bg-gray-700 rounded-full h-1">
            <div class="h-1 rounded-full bg-blue-500 transition-all"
                 :style="{ width: taskProgress + '%' }" />
          </div>
          <span class="text-gray-400 tabular-nums">{{ agent.remaining_task_ticks }}t</span>
        </div>
      </div>
      <div v-else class="text-gray-600 text-xs italic pl-0.5">No current task</div>

      <!-- Conversation -->
      <div v-if="agent.conversation_partner_id" class="flex items-center gap-2 bg-pink-900/30 rounded-lg px-2.5 py-2">
        <span class="text-pink-400">💬</span>
        <span class="text-pink-300 text-xs">
          Chatting with <strong>{{ partnerName }}</strong>
        </span>
      </div>

      <!-- Memory -->
      <div v-if="agent.memory && agent.memory.length">
        <div class="text-gray-600 text-xs uppercase tracking-widest mb-1.5">Memory</div>
        <div class="space-y-1">
          <div v-for="(mem, i) in [...agent.memory].reverse().slice(0, 4)" :key="i"
               class="text-gray-400 text-xs bg-gray-800/40 rounded px-2 py-1 leading-relaxed truncate"
               :title="mem">
            {{ mem }}
          </div>
        </div>
      </div>

      <!-- Recent events for this agent -->
      <div v-if="agentEvents.length">
        <div class="text-gray-600 text-xs uppercase tracking-widest mb-1.5">Recent Activity</div>
        <div class="space-y-1">
          <div v-for="ev in agentEvents" :key="ev.event_id"
               class="flex items-center gap-1.5 text-xs text-gray-400 bg-gray-800/40 rounded px-2 py-1">
            <span class="text-gray-600 tabular-nums">[{{ ev.tick }}]</span>
            <span :class="evTypeColor(ev.type)">{{ ev.type }}</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useEventsStore } from '../stores/events.js'
import { useSimulationStore } from '../stores/simulation'
import { useUiStore } from '../stores/ui'
import InfoRow from './InfoRow.vue'
import StatBar from './StatBar.vue'

const simStore    = useSimulationStore()
const uiStore     = useUiStore()
const eventsStore = useEventsStore()

const ROLE_COLORS = {
  engineer: '#3b82f6', designer: '#a855f7',
  manager: '#f59e0b', analyst: '#10b981',
}

const STATUS_CLASSES = {
  idle:     'bg-gray-700 text-gray-300',
  working:  'bg-blue-900 text-blue-300',
  moving:   'bg-yellow-900 text-yellow-300',
  meeting:  'bg-purple-900 text-purple-300',
  chatting: 'bg-pink-900 text-pink-300',
  break:    'bg-emerald-900 text-emerald-300',
}

const EV_COLORS = {
  task_started:   'text-blue-400',
  task_completed: 'text-emerald-400',
  task_assigned:  'text-sky-400',
  task_failed:    'text-red-400',
  chat_started:   'text-pink-400',
  break_started:  'text-green-400',
  meeting_started:'text-purple-400',
}

const agent = computed(() =>
  uiStore.selectedAgentId ? simStore.agents[uiStore.selectedAgentId] ?? null : null
)

const currentTask = computed(() =>
  agent.value?.current_task_id ? simStore.tasks[agent.value.current_task_id] ?? null : null
)

const initials = computed(() =>
  agent.value?.name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase() ?? ''
)

const roleColor = computed(() => ROLE_COLORS[agent.value?.role] ?? '#64748b')

const statusClass = computed(() =>
  STATUS_CLASSES[agent.value?.status] ?? 'bg-gray-700 text-gray-300'
)

const taskProgress = computed(() => {
  if (!currentTask.value || agent.value?.remaining_task_ticks == null) return 0
  const total = currentTask.value.duration_ticks || 1
  const done  = total - agent.value.remaining_task_ticks
  return Math.round((done / total) * 100)
})

const partnerName = computed(() => {
  const pid = agent.value?.conversation_partner_id
  return pid ? (simStore.agents[pid]?.name ?? pid) : ''
})

const agentEvents = computed(() => {
  if (!agent.value) return []
  const id = agent.value.id
  return eventsStore.items
    .filter(e => e.payload?.agent_id === id || e.payload?.agent_ids?.includes(id))
    .slice(0, 5)
})

const fmt = n => (n == null ? '—' : Math.round(n))

const taskTypeClass = type => ({
  work:     'bg-blue-900/50 text-blue-300',
  meeting:  'bg-purple-900/50 text-purple-300',
  research: 'bg-amber-900/50 text-amber-300',
  review:   'bg-sky-900/50 text-sky-300',
  break:    'bg-emerald-900/50 text-emerald-300',
}[type] ?? 'bg-gray-700 text-gray-300')

const evTypeColor = t => EV_COLORS[t] ?? 'text-gray-400'
</script>
