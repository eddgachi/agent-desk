<template>
  <div class="flex items-center justify-between gap-2 py-0.5">
    <span class="text-gray-500 flex-none">{{ label }}</span>
    <span
      class="text-right truncate"
      :class="[mono ? 'font-mono' : '', valueClass || 'text-gray-300']"
    >{{ value }}</span>
  </div>
</template>

<script setup>
defineProps({
  label:      String,
  value:      [String, Number],
  mono:       Boolean,
  valueClass: String,
})
</script>
