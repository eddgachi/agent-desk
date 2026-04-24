import { CANVAS_H, CANVAS_W, furniture, rooms } from './officeLayout.js'

// ── Role colours ───────────────────────────────────────────
const ROLE = {
  engineer: { body: '#3b82f6', ring: '#93c5fd', glow: '#1d4ed855' },
  designer: { body: '#a855f7', ring: '#d8b4fe', glow: '#7e22ce55' },
  manager:  { body: '#f59e0b', ring: '#fde68a', glow: '#b4530955' },
  analyst:  { body: '#10b981', ring: '#6ee7b7', glow: '#06503455' },
  default:  { body: '#64748b', ring: '#cbd5e1', glow: '#33415555' },
}

const STATUS_DOT = {
  idle:     '#94a3b8',
  working:  '#3b82f6',
  moving:   '#f59e0b',
  meeting:  '#a855f7',
  chatting: '#ec4899',
  break:    '#10b981',
}

const STATUS_LABEL = {
  idle:     '',
  working:  '⚙',
  moving:   '',
  meeting:  '⚑',
  chatting: '💬',
  break:    '☕',
}

const AGENT_R = 14

// ── Helpers ────────────────────────────────────────────────
function roundRect(ctx, x, y, w, h, r = 4) {
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

function hexAlpha(hex, a) {
  // append alpha byte to a 6-char hex colour
  return hex + Math.round(a * 255).toString(16).padStart(2, '0')
}

// ── Background grid ────────────────────────────────────────
function drawGrid(ctx) {
  const step = 40
  ctx.save()
  ctx.strokeStyle = '#13151f'
  ctx.lineWidth = 0.5
  for (let x = 0; x <= CANVAS_W; x += step) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, CANVAS_H); ctx.stroke()
  }
  for (let y = 0; y <= CANVAS_H; y += step) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CANVAS_W, y); ctx.stroke()
  }
  ctx.restore()
}

// ── Rooms ──────────────────────────────────────────────────
function drawRooms(ctx) {
  rooms.forEach(room => {
    // Room fill with subtle gradient
    ctx.save()
    const grad = ctx.createLinearGradient(room.x, room.y, room.x + room.w, room.y + room.h)
    grad.addColorStop(0, room.fill)
    grad.addColorStop(1, hexAlpha('#000000', 0.08) === room.fill ? room.fill : room.fill)
    ctx.fillStyle = room.fill
    roundRect(ctx, room.x, room.y, room.w, room.h, 6)
    ctx.fill()

    if (room.stroke && room.stroke !== 'transparent') {
      ctx.strokeStyle = room.stroke
      ctx.lineWidth = 1.5
      ctx.stroke()
    }

    if (room.label) {
      ctx.fillStyle = room.labelColor
      ctx.font = '600 10px "Inter", system-ui, sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(room.label.toUpperCase(), room.x + 10, room.y + 18)
    }
    ctx.restore()
  })
}

// ── Furniture ──────────────────────────────────────────────
function drawFurniture(ctx) {
  furniture.forEach(f => {
    ctx.save()
    if (f.type === 'desk') {
      // Desk body
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      roundRect(ctx, f.x, f.y, f.w, f.h, 5)
      ctx.fill(); ctx.stroke()

      // Monitor
      ctx.fillStyle = '#0d1a12'
      ctx.strokeStyle = '#1e4028'
      ctx.lineWidth = 1
      roundRect(ctx, f.x + 7, f.y + 6, 28, 20, 2)
      ctx.fill(); ctx.stroke()

      // Screen glow
      ctx.fillStyle = '#00ff7715'
      roundRect(ctx, f.x + 9, f.y + 8, 24, 16, 1)
      ctx.fill()

      // Desk label
      ctx.fillStyle = '#3d5040'
      ctx.font = '8px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(f.label, f.x + f.w / 2, f.y + f.h - 5)

    } else if (f.type === 'rect') {
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      roundRect(ctx, f.x, f.y, f.w, f.h, f.r || 4)
      ctx.fill(); ctx.stroke()

    } else if (f.type === 'circle') {
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2)
      ctx.fill(); ctx.stroke()
    }
    ctx.restore()
  })
}

// ── Movement paths ─────────────────────────────────────────
function drawPaths(ctx, agents) {
  agents.forEach(agent => {
    if (agent.status !== 'moving') return
    if (agent.target_x == null) return
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y
    ctx.save()
    ctx.setLineDash([5, 5])
    ctx.strokeStyle = '#f59e0b33'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(agent.target_x, agent.target_y)
    ctx.stroke()
    // Target dot
    ctx.setLineDash([])
    ctx.beginPath()
    ctx.arc(agent.target_x, agent.target_y, 3, 0, Math.PI * 2)
    ctx.fillStyle = '#f59e0b66'
    ctx.fill()
    ctx.restore()
  })
}

// ── Chat connection lines ──────────────────────────────────
function drawChatLinks(ctx, agents, ts) {
  const chatters = agents.filter(a => a.status === 'chatting' && a.conversation_partner_id)
  const drawn = new Set()
  chatters.forEach(a => {
    if (drawn.has(a.id)) return
    const partner = agents.find(p => p.id === a.conversation_partner_id)
    if (!partner) return
    drawn.add(a.id); drawn.add(partner.id)
    const ax = a._renderX ?? a.position_x
    const ay = a._renderY ?? a.position_y
    const px = partner._renderX ?? partner.position_x
    const py = partner._renderY ?? partner.position_y
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(ts / 400))
    ctx.save()
    ctx.strokeStyle = `rgba(236,72,153,${pulse * 0.5})`
    ctx.lineWidth = 1.5
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(ax, ay)
    ctx.lineTo(px, py)
    ctx.stroke()
    ctx.restore()
  })
}

// ── Agents ─────────────────────────────────────────────────
function drawAgents(ctx, agents, selectedId, ts) {
  // Draw shadows first
  agents.forEach(agent => {
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y
    ctx.save()
    ctx.beginPath()
    ctx.ellipse(x, y + AGENT_R + 2, AGENT_R * 0.9, 5, 0, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,0,0,0.35)'
    ctx.fill()
    ctx.restore()
  })

  agents.forEach(agent => {
    const colors = ROLE[agent.role] || ROLE.default
    const isSelected = agent.id === selectedId
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y

    ctx.save()

    // Glow for active states
    if (agent.status === 'working' || agent.status === 'meeting') {
      const pulse = 0.5 + 0.5 * Math.sin(ts / 500)
      ctx.beginPath()
      ctx.arc(x, y, AGENT_R + 8 + pulse * 4, 0, Math.PI * 2)
      ctx.fillStyle = colors.glow
      ctx.fill()
    }

    // Selection ring (animated dashes)
    if (isSelected) {
      ctx.save()
      ctx.translate(x, y)
      ctx.rotate(ts / 1200)
      ctx.beginPath()
      ctx.arc(0, 0, AGENT_R + 7, 0, Math.PI * 2)
      ctx.strokeStyle = colors.ring
      ctx.lineWidth = 2
      ctx.setLineDash([5, 4])
      ctx.stroke()
      ctx.restore()
    }

    // Agent body
    const bodyGrad = ctx.createRadialGradient(x - 4, y - 4, 2, x, y, AGENT_R)
    bodyGrad.addColorStop(0, lighten(colors.body, 0.3))
    bodyGrad.addColorStop(1, colors.body)
    ctx.beginPath()
    ctx.arc(x, y, AGENT_R, 0, Math.PI * 2)
    ctx.fillStyle = bodyGrad
    ctx.fill()
    ctx.strokeStyle = colors.ring
    ctx.lineWidth = 2
    ctx.stroke()

    // Initials
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 9px "Inter", system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const initials = agent.name.split(' ').map(p => p[0]).join('').slice(0, 2)
    ctx.fillText(initials, x, y)
    ctx.textBaseline = 'alphabetic'

    // Status dot (bottom-right corner)
    const dotColor = STATUS_DOT[agent.status] || '#94a3b8'
    ctx.beginPath()
    ctx.arc(x + 9, y + 9, 5, 0, Math.PI * 2)
    ctx.fillStyle = dotColor
    ctx.fill()
    ctx.strokeStyle = '#0f1117'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // Status icon inside dot
    const icon = STATUS_LABEL[agent.status]
    if (icon) {
      ctx.font = '7px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#fff'
      ctx.fillText(icon, x + 9, y + 9)
      ctx.textBaseline = 'alphabetic'
    }

    // Name tag (above agent)
    const nameTag = agent.name.split(' ')[0]
    const tagW = ctx.measureText(nameTag).width + 10
    const tagH = 14
    const tagX = x - tagW / 2
    const tagY = y - AGENT_R - tagH - 4

    ctx.fillStyle = 'rgba(15,17,23,0.8)'
    roundRect(ctx, tagX, tagY, tagW, tagH, 3)
    ctx.fill()

    ctx.fillStyle = isSelected ? colors.ring : '#e2e8f0'
    ctx.font = `${isSelected ? 'bold' : 'normal'} 9px "Inter", system-ui, sans-serif`
    ctx.textAlign = 'center'
    ctx.fillText(nameTag, x, tagY + tagH - 3)

    ctx.restore()
  })
}

// ── Energy bars under agents ───────────────────────────────
function drawEnergyBars(ctx, agents, selectedId) {
  agents.forEach(agent => {
    if (agent.id !== selectedId && agent.status === 'idle') return  // only show on selected or active
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y
    const barW = 28
    const barH = 3
    const bx = x - barW / 2
    const by = y + AGENT_R + 6

    ctx.save()
    ctx.fillStyle = '#1e2030'
    roundRect(ctx, bx, by, barW, barH, 1)
    ctx.fill()

    const energy = (agent.energy ?? 100) / 100
    const color = energy > 0.6 ? '#10b981' : energy > 0.3 ? '#f59e0b' : '#ef4444'
    ctx.fillStyle = color
    roundRect(ctx, bx, by, Math.max(2, barW * energy), barH, 1)
    ctx.fill()
    ctx.restore()
  })
}

// ── Outer border ───────────────────────────────────────────
function drawBorder(ctx) {
  ctx.save()
  ctx.strokeStyle = '#3d4166'
  ctx.lineWidth = 3
  roundRect(ctx, 1, 1, CANVAS_W - 2, CANVAS_H - 2, 8)
  ctx.stroke()
  ctx.restore()
}

// ── Main render ────────────────────────────────────────────
export function renderFrame(ctx, agents, selectedId, ts) {
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H)
  ctx.fillStyle = '#11131e'
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)

  drawGrid(ctx)
  drawRooms(ctx)
  drawFurniture(ctx)
  drawPaths(ctx, agents)
  drawChatLinks(ctx, agents, ts)
  drawAgents(ctx, agents, selectedId, ts)
  drawEnergyBars(ctx, agents, selectedId)
  drawBorder(ctx)
}

// ── Colour utility ─────────────────────────────────────────
function lighten(hex, amount) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.min(255, (num >> 16) + Math.round(255 * amount))
  const g = Math.min(255, ((num >> 8) & 0xff) + Math.round(255 * amount))
  const b = Math.min(255, (num & 0xff) + Math.round(255 * amount))
  return `rgb(${r},${g},${b})`
}

export { AGENT_R as AGENT_RADIUS }
