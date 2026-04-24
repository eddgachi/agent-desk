<template>
  <div class="flex items-center gap-2">
    <span class="text-gray-400 w-12 flex-none text-xs">{{ label }}</span>
    <div class="flex-1 bg-gray-700 rounded-full h-1.5">
      <div
        class="h-1.5 rounded-full transition-all duration-500"
        :class="color"
        :style="{ width: clampedValue + '%' }"
      />
    </div>
    <span class="text-gray-400 w-6 text-right tabular-nums text-xs">{{ Math.round(value) }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: String,
  value: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  color: { type: String, default: 'bg-blue-500' },
})

const clampedValue = computed(() => Math.min(100, Math.max(0, (props.value / props.max) * 100)))
</script>
