import { onMounted, onUnmounted, ref } from 'vue'

/**
 * Drives a requestAnimationFrame loop.
 * Calls `onFrame(timestamp)` each frame.
 * Returns `pause()` / `resume()` controls.
 */
export function useAnimationLoop(onFrame) {
  const running = ref(true)
  let rafId = null

  function loop(ts) {
    if (running.value) onFrame(ts)
    rafId = requestAnimationFrame(loop)
  }

  onMounted(() => {
    rafId = requestAnimationFrame(loop)
  })

  onUnmounted(() => {
    if (rafId) cancelAnimationFrame(rafId)
  })

  return {
    running,
    pause() { running.value = false },
    resume() { running.value = true },
  }
}
