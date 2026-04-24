import { CANVAS_H, CANVAS_W, furniture, rooms } from './officeLayout.js'

/**
 * Agent colour palette keyed by role.
 */
const ROLE_COLOR = {
  engineer:   { fill: '#3b82f6', stroke: '#60a5fa', ring: '#1d4ed8' },
  designer:   { fill: '#a855f7', stroke: '#c084fc', ring: '#7e22ce' },
  manager:    { fill: '#f59e0b', stroke: '#fbbf24', ring: '#b45309' },
  analyst:    { fill: '#10b981', stroke: '#34d399', ring: '#065f46' },
  default:    { fill: '#64748b', stroke: '#94a3b8', ring: '#334155' },
}

const STATUS_COLOR = {
  idle:     '#94a3b8',
  working:  '#3b82f6',
  moving:   '#f59e0b',
  meeting:  '#a855f7',
  chatting: '#ec4899',
  break:    '#10b981',
}

const STATUS_ICON = {
  idle:     '💤',
  working:  '⚙',
  moving:   '→',
  meeting:  '💬',
  chatting: '💬',
  break:    '☕',
}

const AGENT_RADIUS = 14

// ── Grid ──────────────────────────────────────────────────
function drawGrid(ctx) {
  ctx.save()
  ctx.strokeStyle = '#151722'
  ctx.lineWidth = 0.5
  const step = 40
  for (let x = 0; x <= CANVAS_W; x += step) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, CANVAS_H); ctx.stroke()
  }
  for (let y = 0; y <= CANVAS_H; y += step) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CANVAS_W, y); ctx.stroke()
  }
  ctx.restore()
}

// ── Rooms ─────────────────────────────────────────────────
function drawRooms(ctx) {
  rooms.forEach(room => {
    if (room.fill === 'transparent') return
    ctx.fillStyle = room.fill
    ctx.fillRect(room.x, room.y, room.w, room.h)

    if (room.stroke !== 'transparent') {
      ctx.strokeStyle = room.stroke
      ctx.lineWidth = 2
      ctx.strokeRect(room.x, room.y, room.w, room.h)
    }

    if (room.label) {
      ctx.fillStyle = room.labelColor
      ctx.font = '11px "Inter", system-ui, sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(room.label.toUpperCase(), room.x + 8, room.y + 16)
    }
  })
}

// ── Furniture ─────────────────────────────────────────────
function drawFurniture(ctx) {
  furniture.forEach(f => {
    ctx.save()
    if (f.type === 'desk') {
      // Desk body
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      roundRect(ctx, f.x, f.y, f.w, f.h, 4)
      ctx.fill()
      ctx.stroke()

      // Monitor screen hint
      ctx.fillStyle = '#1a3020'
      ctx.strokeStyle = '#305040'
      ctx.lineWidth = 1
      roundRect(ctx, f.x + 8, f.y + 6, 30, 22, 2)
      ctx.fill()
      ctx.stroke()

      // Screen glow
      ctx.fillStyle = '#00ff8820'
      roundRect(ctx, f.x + 10, f.y + 8, 26, 18, 1)
      ctx.fill()

      // Label
      ctx.fillStyle = '#4a6050'
      ctx.font = '9px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(f.label, f.x + f.w / 2, f.y + f.h - 6)

    } else if (f.type === 'rect') {
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      roundRect(ctx, f.x, f.y, f.w, f.h, f.r || 0)
      ctx.fill()
      ctx.stroke()

    } else if (f.type === 'circle') {
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
    }
    ctx.restore()
  })
}

// ── Outer office border ───────────────────────────────────
function drawBorder(ctx) {
  ctx.save()
  ctx.strokeStyle = '#4a4f70'
  ctx.lineWidth = 3
  ctx.strokeRect(2, 2, CANVAS_W - 4, CANVAS_H - 4)
  ctx.restore()
}

// ── Agents ────────────────────────────────────────────────
function drawAgents(ctx, agents, selectedId, timestamp) {
  agents.forEach(agent => {
    const colors = ROLE_COLOR[agent.role] || ROLE_COLOR.default
    const isSelected = agent.id === selectedId
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y

    ctx.save()

    // Selection ring
    if (isSelected) {
      ctx.beginPath()
      ctx.arc(x, y, AGENT_RADIUS + 6, 0, Math.PI * 2)
      ctx.strokeStyle = colors.stroke
      ctx.lineWidth = 2
      ctx.setLineDash([4, 3])
      ctx.stroke()
      ctx.setLineDash([])
    }

    // Status pulse ring (working / meeting)
    if (agent.status === 'working' || agent.status === 'meeting') {
      const pulse = 0.5 + 0.5 * Math.sin(timestamp / 600)
      ctx.beginPath()
      ctx.arc(x, y, AGENT_RADIUS + 4 + pulse * 3, 0, Math.PI * 2)
      ctx.strokeStyle = STATUS_COLOR[agent.status] + '66'
      ctx.lineWidth = 1.5
      ctx.stroke()
    }

    // Agent body
    ctx.beginPath()
    ctx.arc(x, y, AGENT_RADIUS, 0, Math.PI * 2)
    ctx.fillStyle = colors.fill
    ctx.fill()
    ctx.strokeStyle = colors.stroke
    ctx.lineWidth = 2
    ctx.stroke()

    // Status dot (bottom-right)
    ctx.beginPath()
    ctx.arc(x + 9, y + 9, 5, 0, Math.PI * 2)
    ctx.fillStyle = STATUS_COLOR[agent.status] || '#94a3b8'
    ctx.fill()
    ctx.strokeStyle = '#0f1117'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // Name label
    ctx.fillStyle = '#e2e8f0'
    ctx.font = 'bold 10px "Inter", sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(agent.name.split(' ')[0], x, y - AGENT_RADIUS - 5)

    ctx.restore()
  })
}

// ── Movement path lines ───────────────────────────────────
function drawPaths(ctx, agents) {
  agents.forEach(agent => {
    if (agent.status !== 'moving') return
    if (agent.target_x == null || agent.target_y == null) return
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y
    ctx.save()
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(agent.target_x, agent.target_y)
    ctx.strokeStyle = '#f59e0b44'
    ctx.lineWidth = 1
    ctx.setLineDash([4, 4])
    ctx.stroke()
    ctx.setLineDash([])

    // Target dot
    ctx.beginPath()
    ctx.arc(agent.target_x, agent.target_y, 3, 0, Math.PI * 2)
    ctx.fillStyle = '#f59e0b88'
    ctx.fill()
    ctx.restore()
  })
}

// ── Main render call ──────────────────────────────────────
export function renderFrame(ctx, agents, selectedId, timestamp) {
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H)

  // Background
  ctx.fillStyle = '#12141f'
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)

  drawGrid(ctx)
  drawRooms(ctx)
  drawFurniture(ctx)
  drawPaths(ctx, agents)
  drawAgents(ctx, agents, selectedId, timestamp)
  drawBorder(ctx)
}

// ── Helpers ───────────────────────────────────────────────
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

export { AGENT_RADIUS }
