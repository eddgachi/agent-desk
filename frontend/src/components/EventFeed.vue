<template>
  <div class="h-full flex flex-col">
    <div class="panel-header flex items-center justify-between flex-none">
      <span>Activity Feed</span>
      <button class="text-gray-600 hover:text-gray-400 text-xs" @click="eventsStore.clear()">
        Clear
      </button>
    </div>
    <div
      ref="listRef"
      class="flex-1 overflow-y-auto scrollbar-thin px-2 py-1 font-mono text-xs"
    >
      <TransitionGroup name="feed" tag="div">
        <div
          v-for="ev in eventsStore.items.slice(0, 80)"
          :key="ev.event_id ?? ev.tick + ev.type"
          class="flex items-start gap-2 py-0.5 border-b border-gray-800 hover:bg-gray-800/40"
        >
          <span class="text-gray-600 flex-none tabular-nums w-10 text-right">{{ ev.tick }}</span>
          <span class="flex-none" :class="typeColor(ev.type)">{{ ev.type }}</span>
          <span class="text-gray-400 truncate">{{ summarise(ev) }}</span>
        </div>
      </TransitionGroup>
      <div v-if="!eventsStore.items.length" class="text-gray-600 italic p-2">
        Waiting for events…
      </div>
    </div>
  </div>
</template>

<script setup>
import { useEventsStore } from '../stores/events.js'

const eventsStore = useEventsStore()

const TYPE_COLORS = {
  task_started:    'text-blue-400',
  task_completed:  'text-emerald-400',
  task_failed:     'text-red-400',
  agent_moved:     'text-yellow-400',
  meeting_started: 'text-purple-400',
  meeting_ended:   'text-purple-300',
  chat_started:    'text-pink-400',
  break_started:   'text-green-400',
  break_ended:     'text-green-300',
  idle:            'text-gray-500',
}

function typeColor(type) {
  return TYPE_COLORS[type] ?? 'text-gray-400'
}

function summarise(ev) {
  const p = ev.payload ?? {}
  if (p.agent_name && p.task_title)  return `${p.agent_name} → ${p.task_title}`
  if (p.agent_name && p.target)      return `${p.agent_name} → (${Math.round(p.target.x)}, ${Math.round(p.target.y)})`
  if (p.agent_name)                  return p.agent_name
  if (p.task_title)                  return p.task_title
  const keys = Object.keys(p)
  if (keys.length)                   return keys.map(k => `${k}: ${p[k]}`).join(' · ')
  return ''
}
</script>

<style scoped>
.feed-enter-active {
  transition: all 0.2s ease;
}
.feed-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
