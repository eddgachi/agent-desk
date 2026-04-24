<template>
  <div class="panel flex flex-col min-h-0">
    <div class="panel-header flex items-center justify-between">
      <span>Tasks</span>
      <span class="text-gray-500">{{ taskList.length }}</span>
    </div>
    <div class="overflow-y-auto scrollbar-thin flex-1 max-h-48">
      <div v-if="!taskList.length" class="panel-body text-gray-500 text-xs italic">No tasks</div>
      <div
        v-for="task in taskList"
        :key="task.id"
        class="px-3 py-2 border-b border-gray-800 text-xs hover:bg-gray-800 transition-colors"
      >
        <div class="flex items-start justify-between gap-1">
          <span class="text-gray-200 font-medium leading-snug">{{ task.title }}</span>
          <span
            class="flex-none px-1.5 py-0.5 rounded text-xs font-medium"
            :class="statusClass(task.status)"
          >{{ task.status }}</span>
        </div>
        <div class="flex items-center gap-2 mt-0.5 text-gray-500">
          <span class="capitalize">{{ task.type }}</span>
          <span>·</span>
          <span>P{{ task.priority }}</span>
          <span v-if="task.assigned_agent_id">
            · <span class="text-blue-400">{{ agentName(task.assigned_agent_id) }}</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'

const simStore = useSimulationStore()

const taskList = computed(() =>
  Object.values(simStore.tasks).sort((a, b) => b.priority - a.priority)
)

function agentName(id) {
  return simStore.agents[id]?.name?.split(' ')[0] ?? id
}

function statusClass(status) {
  return {
    pending:     'bg-gray-700 text-gray-300',
    assigned:    'bg-blue-900 text-blue-300',
    in_progress: 'bg-emerald-900 text-emerald-300',
    completed:   'bg-gray-800 text-gray-500',
    failed:      'bg-red-900 text-red-300',
  }[status] ?? 'bg-gray-700 text-gray-300'
}
</script>
