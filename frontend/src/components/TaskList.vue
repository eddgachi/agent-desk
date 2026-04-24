<template>
  <div class="flex flex-col min-h-0">
    <div class="flex items-center justify-between px-3 py-2.5 border-b border-gray-800">
      <span class="text-xs font-semibold text-gray-500 uppercase tracking-widest">Tasks</span>
      <div class="flex gap-1 text-xs">
        <span class="bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded-full">{{ taskList.length }}</span>
      </div>
    </div>

    <div class="overflow-y-auto scrollbar-thin flex-1 max-h-64">
      <div v-if="!taskList.length" class="p-3 text-gray-600 text-xs italic">No tasks</div>

      <div
        v-for="task in taskList"
        :key="task.id"
        class="px-3 py-2 border-b border-gray-800/60 hover:bg-gray-800/30 transition-colors cursor-default"
        :class="{ 'opacity-50': task.status === 'completed' || task.status === 'failed' }"
      >
        <!-- Title + status -->
        <div class="flex items-start justify-between gap-1 mb-1">
          <span class="text-gray-200 text-xs font-medium leading-snug flex-1">{{ task.title }}</span>
          <span class="flex-none text-xs px-1.5 py-0.5 rounded font-medium"
                :class="statusClass(task.status)">
            {{ task.status }}
          </span>
        </div>

        <!-- Meta -->
        <div class="flex items-center gap-2 text-gray-500 text-xs">
          <span class="text-gray-600 capitalize">{{ task.type }}</span>
          <span class="text-gray-700">·</span>
          <span class="font-mono">P{{ task.priority }}</span>
          <span v-if="task.assigned_agent_id" class="text-gray-700">·</span>
          <span v-if="task.assigned_agent_id" class="text-blue-400">
            {{ agentName(task.assigned_agent_id) }}
          </span>
        </div>

        <!-- Progress bar for in-progress tasks -->
        <div v-if="task.status === 'in_progress' && task.remaining_ticks != null"
             class="mt-1.5 flex items-center gap-2">
          <div class="flex-1 bg-gray-700 rounded-full h-1">
            <div class="h-1 rounded-full bg-blue-500 transition-all"
                 :style="{ width: taskPct(task) + '%' }" />
          </div>
          <span class="text-gray-500 tabular-nums text-xs">{{ task.remaining_ticks }}t</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'

const simStore = useSimulationStore()

const STATUS_ORDER = { in_progress: 0, assigned: 1, pending: 2, completed: 3, failed: 4 }

const taskList = computed(() =>
  Object.values(simStore.tasks)
    .sort((a, b) => {
      const so = (STATUS_ORDER[a.status] ?? 5) - (STATUS_ORDER[b.status] ?? 5)
      return so !== 0 ? so : b.priority - a.priority
    })
)

function agentName(id) {
  return simStore.agents[id]?.name?.split(' ')[0] ?? id
}

function taskPct(task) {
  const dur = task.duration_ticks || 1
  const rem = task.remaining_ticks ?? 0
  return Math.round(((dur - rem) / dur) * 100)
}

function statusClass(status) {
  return {
    pending:     'bg-gray-800 text-gray-400',
    assigned:    'bg-sky-900/60 text-sky-300',
    in_progress: 'bg-blue-900/60 text-blue-300',
    completed:   'bg-emerald-900/40 text-emerald-500',
    failed:      'bg-red-900/60 text-red-400',
  }[status] ?? 'bg-gray-800 text-gray-400'
}
</script>
