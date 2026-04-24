<template>
  <div class="panel">
    <div class="panel-header flex items-center justify-between">
      <span>Inspector</span>
      <button
        v-if="agent"
        class="text-gray-500 hover:text-gray-300 text-xs"
        @click="uiStore.selectAgent(null)"
      >✕</button>
    </div>

    <!-- Empty state -->
    <div v-if="!agent" class="panel-body text-center text-gray-500 text-xs py-6">
      <div class="text-2xl mb-2">🖱</div>
      Click an agent on the map
    </div>

    <!-- Agent details -->
    <div v-else class="panel-body space-y-3 text-xs">
      <!-- Identity -->
      <div class="flex items-center gap-3">
        <div
          class="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-sm flex-none"
          :style="{ backgroundColor: roleColor }"
        >
          {{ initials }}
        </div>
        <div>
          <div class="font-semibold text-gray-100 text-sm">{{ agent.name }}</div>
          <div class="text-gray-400 capitalize">{{ agent.role }}</div>
        </div>
      </div>

      <div class="border-t border-gray-700" />

      <!-- Status -->
      <div class="flex items-center justify-between">
        <span class="text-gray-400">Status</span>
        <span :class="`status-${agent.status}`">
          {{ STATUS_ICON[agent.status] || '·' }} {{ agent.status }}
        </span>
      </div>

      <!-- Position -->
      <div class="flex items-center justify-between">
        <span class="text-gray-400">Position</span>
        <span class="tabular-nums text-gray-300 font-mono">
          {{ fmtN(agent.position_x) }}, {{ fmtN(agent.position_y) }}
        </span>
      </div>

      <!-- Target (if moving) -->
      <div v-if="agent.target_x != null" class="flex items-center justify-between">
        <span class="text-gray-400">Target</span>
        <span class="tabular-nums text-yellow-400 font-mono">
          {{ fmtN(agent.target_x) }}, {{ fmtN(agent.target_y) }}
        </span>
      </div>

      <!-- Energy / Focus bars -->
      <div class="space-y-1.5">
        <StatBar label="Energy" :value="agent.energy ?? 100" color="bg-emerald-500" />
        <StatBar label="Focus"  :value="agent.focus  ?? 100" color="bg-blue-500" />
      </div>

      <div class="border-t border-gray-700" />

      <!-- Current task -->
      <div>
        <div class="text-gray-400 mb-1">Current Task</div>
        <div v-if="currentTask" class="bg-gray-800 rounded p-2 space-y-1">
          <div class="text-gray-200 font-medium">{{ currentTask.title }}</div>
          <div class="flex items-center justify-between text-gray-400">
            <span class="capitalize">{{ currentTask.type }}</span>
            <span class="text-yellow-400">P{{ currentTask.priority }}</span>
          </div>
          <div v-if="agent.remaining_task_ticks != null" class="text-gray-400">
            {{ agent.remaining_task_ticks }} ticks remaining
          </div>
        </div>
        <div v-else class="text-gray-500 italic">Unassigned</div>
      </div>

      <!-- Recent actions -->
      <div v-if="recentActions.length">
        <div class="text-gray-400 mb-1">Recent Events</div>
        <div class="space-y-1">
          <div
            v-for="ev in recentActions"
            :key="ev.event_id"
            class="bg-gray-800 rounded px-2 py-1 text-gray-300"
          >
            <span class="text-gray-500 font-mono mr-1">[{{ ev.tick }}]</span>
            {{ ev.type }}
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
import StatBar from './StatBar.vue'

const simStore    = useSimulationStore()
const uiStore     = useUiStore()
const eventsStore = useEventsStore()

const STATUS_ICON = {
  idle: '💤', working: '⚙', moving: '→',
  meeting: '💬', chatting: '💬', break: '☕',
}

const ROLE_COLORS = {
  engineer: '#3b82f6',
  designer: '#a855f7',
  manager:  '#f59e0b',
  analyst:  '#10b981',
}

const agent = computed(() =>
  uiStore.selectedAgentId ? simStore.agents[uiStore.selectedAgentId] ?? null : null
)

const currentTask = computed(() => {
  if (!agent.value?.current_task_id) return null
  return simStore.tasks[agent.value.current_task_id] ?? null
})

const initials = computed(() => {
  if (!agent.value) return ''
  return agent.value.name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase()
})

const roleColor = computed(() =>
  ROLE_COLORS[agent.value?.role] ?? '#64748b'
)

const recentActions = computed(() => {
  if (!agent.value) return []
  return eventsStore.items
    .filter(e => e.payload?.agent_id === agent.value.id || e.payload?.actor_id === agent.value.id)
    .slice(0, 5)
})

const fmtN = (n) => (n == null ? '—' : Math.round(n))
</script>
