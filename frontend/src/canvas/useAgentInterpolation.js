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
  agents.forEach((agent) => {
    const id = agent.id
    const targetX = agent.position_x
    const targetY = agent.position_y

    // Determine target rotation
    let targetRot = agent._targetRot ?? 0
    if (agent.status === 'moving' && agent.target_x !== null) {
      targetRot = Math.atan2(agent.target_y - agent.position_y, agent.target_x - agent.position_x)
    } else if (agent.status === 'working') {
      targetRot = Math.PI / 2 // Face "down" towards desk
    } else if (agent.status === 'chatting' && agent.conversation_partner_id) {
      const partner = agents.find((p) => p.id === agent.conversation_partner_id)
      if (partner) {
        targetRot = Math.atan2(
          (partner._renderY ?? partner.position_y) - (agent._renderY ?? agent.position_y),
          (partner._renderX ?? partner.position_x) - (agent._renderX ?? agent.position_x),
        )
      }
    }

    if (!renderState.has(id)) {
      renderState.set(id, { x: targetX, y: targetY, rot: targetRot })
    }

    const state = renderState.get(id)

    // Position lerp
    const dx = targetX - state.x
    const dy = targetY - state.y

    if (Math.abs(dx) < SNAP_DIST && Math.abs(dy) < SNAP_DIST) {
      state.x = targetX
      state.y = targetY
    } else {
      state.x += dx * LERP_SPEED
      state.y += dy * LERP_SPEED
    }

    // Rotation lerp (shortest path)
    let dr = targetRot - state.rot
    while (dr > Math.PI) dr -= Math.PI * 2
    while (dr < -Math.PI) dr += Math.PI * 2
    state.rot += dr * 0.1

    // Write back to the agent object
    agent._renderX = state.x
    agent._renderY = state.y
    agent._renderRot = state.rot
  })
}

export function removeAgent(id) {
  renderState.delete(id)
}

export function clearAll() {
  renderState.clear()
}
