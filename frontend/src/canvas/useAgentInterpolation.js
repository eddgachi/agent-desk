/**
 * Manages per-agent render positions (_renderX, _renderY).
 * Call `tickInterpolation(agents, dt)` each frame.
 *
 * Agents smoothly lerp toward their actual position_x / position_y.
 * Speed is tunable via LERP_SPEED (0–1 per frame at 60fps).
 */

const LERP_SPEED = 0.12   // per-frame lerp factor (at 60fps ≈ 12% per frame)
const SNAP_DIST  = 0.5    // snap to target when this close (px)

// Track per-agent render state outside Vue reactivity for performance
const renderState = new Map()

export function tickInterpolation(agents, _dt) {
  agents.forEach(agent => {
    const id = agent.id
    const targetX = agent.position_x
    const targetY = agent.position_y

    if (!renderState.has(id)) {
      // First time we see this agent — place exactly at its position
      renderState.set(id, { x: targetX, y: targetY })
    }

    const state = renderState.get(id)

    const dx = targetX - state.x
    const dy = targetY - state.y

    if (Math.abs(dx) < SNAP_DIST && Math.abs(dy) < SNAP_DIST) {
      state.x = targetX
      state.y = targetY
    } else {
      state.x += dx * LERP_SPEED
      state.y += dy * LERP_SPEED
    }

    // Write back to the agent object so the renderer picks it up
    agent._renderX = state.x
    agent._renderY = state.y
  })
}

export function removeAgent(id) {
  renderState.delete(id)
}

export function clearAll() {
  renderState.clear()
}
