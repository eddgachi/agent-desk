/**
 * Renderer — blueprint / game-map aesthetic with LEGO-like agents.
 *
 * Draws the office layout as a clean, top-down simulation map.
 * Agents are rendered as LEGO-style blocky figures with role-based colours.
 */
import { C, CANVAS_H, CANVAS_W, furniture, rooms } from './officeLayout.js'

// ── Role colours (vibrant LEGO-like) ──────────────────────
const ROLE = {
  engineer: { body: '#2563eb', belt: '#1d4ed8', ring: '#60a5fa' },
  designer: { body: '#9333ea', belt: '#7e22ce', ring: '#c084fc' },
  manager: { body: '#d97706', belt: '#b45309', ring: '#fcd34d' },
  analyst: { body: '#059669', belt: '#047857', ring: '#34d399' },
  default: { body: '#64748b', belt: '#475569', ring: '#cbd5e1' },
}

const STATUS_DOT = {
  idle: '#94a3b8',
  working: '#3b82f6',
  moving: '#f59e0b',
  meeting: '#a855f7',
  chatting: '#ec4899',
  break: '#10b981',
}

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
  return (
    hex +
    Math.round(a * 255)
      .toString(16)
      .padStart(2, '0')
  )
}

// ── Outer border / frame ───────────────────────────────────
function drawBorder(ctx) {
  ctx.save()
  // Outer shadow (border only, no fill over the whole canvas!)
  ctx.shadowColor = 'rgba(0,0,0,0.10)'
  ctx.shadowBlur = 8
  ctx.shadowOffsetX = 1
  ctx.shadowOffsetY = 1
  ctx.strokeStyle = '#3a3a4e'
  ctx.lineWidth = 4
  roundRect(ctx, 2, 2, CANVAS_W - 4, CANVAS_H - 4, 10)
  ctx.stroke()
  ctx.shadowColor = 'transparent'

  // Double-stroke for blueprint border effect
  ctx.strokeStyle = '#3a3a4e'
  ctx.lineWidth = 3
  roundRect(ctx, 3, 3, CANVAS_W - 6, CANVAS_H - 6, 9)
  ctx.stroke()
  ctx.restore()
}

// ── Background grid (like blueprint paper) ─────────────────
function drawGrid(ctx) {
  const step = 50
  ctx.save()
  ctx.strokeStyle = '#b8b4a8'
  ctx.lineWidth = 0.6
  for (let x = 0; x <= CANVAS_W; x += step) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, CANVAS_H)
    ctx.stroke()
  }
  for (let y = 0; y <= CANVAS_H; y += step) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(CANVAS_W, y)
    ctx.stroke()
  }
  ctx.restore()
}

// ── Rooms with walls ───────────────────────────────────────
function drawRooms(ctx) {
  rooms.forEach((room) => {
    ctx.save()

    // Floor fill
    ctx.fillStyle = room.fill
    roundRect(ctx, room.x, room.y, room.w, room.h, 6)
    ctx.fill()

    // Inner subtle floor pattern (tiles)
    ctx.globalAlpha = 0.15
    ctx.strokeStyle = '#4a4a5a'
    ctx.lineWidth = 0.3
    const tileSize = 20
    for (let tx = room.x + tileSize; tx < room.x + room.w - tileSize; tx += tileSize) {
      ctx.beginPath()
      ctx.moveTo(tx, room.y + 4)
      ctx.lineTo(tx, room.y + room.h - 4)
      ctx.stroke()
    }
    for (let ty = room.y + tileSize; ty < room.y + room.h - tileSize; ty += tileSize) {
      ctx.beginPath()
      ctx.moveTo(room.x + 4, ty)
      ctx.lineTo(room.x + room.w - 4, ty)
      ctx.stroke()
    }
    ctx.globalAlpha = 1.0

    // Wall shadow (gives 3D depth)
    if (room.stroke && room.stroke !== 'transparent') {
      ctx.shadowColor = 'rgba(0,0,0,0.08)'
      ctx.shadowBlur = 8
      ctx.shadowOffsetX = 2
      ctx.shadowOffsetY = 2
      ctx.strokeStyle = C.wallShadow
      ctx.lineWidth = 6
      roundRect(ctx, room.x + 1, room.y + 1, room.w - 2, room.h - 2, 5)
      ctx.stroke()
      ctx.shadowColor = 'transparent'

      // Wall stroke (thick, like blueprint walls)
      ctx.strokeStyle = room.stroke
      ctx.lineWidth = 3.5
      roundRect(ctx, room.x, room.y, room.w, room.h, 6)
      ctx.stroke()

      // Room label
      if (room.label) {
        ctx.fillStyle = room.labelColor
        ctx.font = '700 11px "Inter", system-ui, sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText(room.label.toUpperCase(), room.x + 12, room.y + 20)
      }
    }
    ctx.restore()
  })
}

// ── Door indicators ────────────────────────────────────────
function drawDoors(ctx) {
  ctx.save()
  const doorEntries = [
    // [roomX, roomY, roomW, side, label]
    // Meeting A door (bottom side)
    { x: 726, y: 200, w: 28, h: 4, fill: C.doorFill, stroke: C.doorStroke },
    // Meeting B door (top side)
    { x: 726, y: 218, w: 28, h: 4, fill: C.doorFill, stroke: C.doorStroke },
    // Break room door (top side)
    { x: 168, y: 432, w: 28, h: 4, fill: C.doorFill, stroke: C.doorStroke },
    // Server room door (top side)
    { x: 455, y: 432, w: 28, h: 4, fill: C.doorFill, stroke: C.doorStroke },
  ]
  doorEntries.forEach((d) => {
    ctx.fillStyle = d.fill
    ctx.strokeStyle = d.stroke
    ctx.lineWidth = 1.5
    roundRect(ctx, d.x, d.y, d.w, d.h, 2)
    ctx.fill()
    ctx.stroke()
  })
  ctx.restore()
}

// ── Furniture ──────────────────────────────────────────────
function drawFurniture(ctx, ts, agents) {
  furniture.forEach((f) => {
    ctx.save()

    if (f.type === 'desk') {
      // Desk shadow
      ctx.shadowColor = 'rgba(0,0,0,0.06)'
      ctx.shadowBlur = 4
      ctx.shadowOffsetX = 1
      ctx.shadowOffsetY = 1

      // Desk body
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      roundRect(ctx, f.x, f.y, f.w, f.h, 4)
      ctx.fill()
      ctx.stroke()
      ctx.shadowColor = 'transparent'

      // Desk top surface line (gives 3D bevel look)
      ctx.strokeStyle = '#f0e8d0'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(f.x + 6, f.y + 4)
      ctx.lineTo(f.x + f.w - 6, f.y + 4)
      ctx.stroke()

      // Monitor
      const monW = 24,
        monH = 14
      const mX = f.x + (f.w - monW) / 2
      const mY = f.y + 6
      ctx.fillStyle = C.monitorFill
      ctx.strokeStyle = '#3a3a4a'
      ctx.lineWidth = 1.5
      roundRect(ctx, mX, mY, monW, monH, 2)
      ctx.fill()
      ctx.stroke()

      // Screen glow (subtle pulse)
      const pulse = 0.3 + 0.15 * Math.sin(ts / 800)
      ctx.fillStyle = `rgba(60, 130, 255, ${pulse})`
      roundRect(ctx, mX + 2, mY + 2, monW - 4, monH - 4, 1)
      ctx.fill()

      // Desk Clutter if an agent is nearby
      const assignedAgent = agents.find((a) => {
        const dx = (a._renderX ?? a.position_x) - (f.x + f.w / 2)
        const dy = (a._renderY ?? a.position_y) - (f.y + f.h / 2)
        return Math.sqrt(dx * dx + dy * dy) < 60
      })

      if (assignedAgent) {
        // Keyboard/Laptop
        ctx.fillStyle = '#2a2a3a'
        ctx.fillRect(f.x + (f.w - 20) / 2, f.y + 24, 20, 10)
        ctx.strokeStyle = '#4a4a5a'
        ctx.lineWidth = 0.5
        ctx.strokeRect(f.x + (f.w - 20) / 2, f.y + 24, 20, 10)

        // Coffee mug
        ctx.fillStyle = assignedAgent.role === 'designer' ? '#fca5a5' : '#fff'
        ctx.beginPath()
        ctx.arc(f.x + 15, f.y + 35, 3.5, 0, Math.PI * 2)
        ctx.fill()
        ctx.strokeStyle = '#d1d5db'
        ctx.lineWidth = 1
        ctx.stroke()
        // Coffee in mug
        ctx.fillStyle = '#4b2c20'
        ctx.beginPath()
        ctx.arc(f.x + 15, f.y + 35, 2, 0, Math.PI * 2)
        ctx.fill()

        // Steam (very subtle)
        if (Math.sin(ts / 1000) > 0.5) {
          ctx.strokeStyle = 'rgba(255,255,255,0.3)'
          ctx.beginPath()
          ctx.moveTo(f.x + 15, f.y + 30)
          ctx.lineTo(f.x + 15 + Math.sin(ts / 300) * 2, f.y + 25)
          ctx.stroke()
        }
      }

      // Desk label
      ctx.fillStyle = C.labelDesk
      ctx.font = '7px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(f.label, f.x + f.w / 2, f.y + f.h - 4)
    } else if (f.type === 'chair') {
      // Chair shadow
      ctx.shadowColor = 'rgba(0,0,0,0.06)'
      ctx.shadowBlur = 3
      ctx.shadowOffsetX = 1
      ctx.shadowOffsetY = 1
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
      ctx.shadowColor = 'transparent'

      // Chair back highlight
      ctx.fillStyle = hexAlpha(f.fill, 0.3)
      ctx.beginPath()
      ctx.arc(f.x, f.y - 2, f.r * 0.5, 0, Math.PI * 2)
      ctx.fill()
    } else if (f.type === 'rect') {
      // Shadow
      if (f.id !== 'printer_tray') {
        ctx.shadowColor = 'rgba(0,0,0,0.05)'
        ctx.shadowBlur = 3
        ctx.shadowOffsetX = 1
        ctx.shadowOffsetY = 1
      }
      ctx.fillStyle = f.fill
      ctx.strokeStyle = f.stroke
      ctx.lineWidth = 1.5
      roundRect(ctx, f.x, f.y, f.w, f.h, f.r || 3)
      ctx.fill()
      ctx.stroke()
      ctx.shadowColor = 'transparent'

      // Coffee machine detail
      if (f.id === 'coffee_machine') {
        ctx.fillStyle = '#6a7a3a'
        ctx.beginPath()
        ctx.arc(f.x + f.w / 2, f.y + 8, 4, 0, Math.PI * 2)
        ctx.fill()
        ctx.fillStyle = '#2a2a2a'
        ctx.fillRect(f.x + 9, f.y + 14, 14, 2)
      }
      // Microwave detail
      if (f.id === 'microwave') {
        ctx.fillStyle = '#2a3a2a'
        ctx.fillRect(f.x + 4, f.y + 6, 14, 10)
      }
    } else if (f.type === 'circle') {
      if (f.id && f.id.startsWith('server_led')) {
        // Blinking server LEDs
        const blink = Math.sin(ts / 300 + parseInt(f.id.split('_')[2] || '0') * 1.5) > 0
        ctx.fillStyle = blink ? f.fill : '#1a2a1a'
        ctx.beginPath()
        ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2)
        ctx.fill()
      } else {
        ctx.shadowColor = 'rgba(0,0,0,0.06)'
        ctx.shadowBlur = 4
        ctx.shadowOffsetX = 1
        ctx.shadowOffsetY = 1
        ctx.fillStyle = f.fill
        ctx.strokeStyle = f.stroke
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2)
        ctx.fill()
        ctx.stroke()
        ctx.shadowColor = 'transparent'

        // Meeting table cross lines
        if (f.id === 'table_meeting_a') {
          ctx.strokeStyle = hexAlpha(f.stroke, 0.3)
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.moveTo(f.x - f.r + 8, f.y)
          ctx.lineTo(f.x + f.r - 8, f.y)
          ctx.moveTo(f.x, f.y - f.r + 8)
          ctx.lineTo(f.x, f.y + f.r - 8)
          ctx.stroke()
        }
      }
    }
    ctx.restore()
  })
}

// ── Movement paths ─────────────────────────────────────────
function drawPaths(ctx, agents) {
  agents.forEach((agent) => {
    if (agent.status !== 'moving') return
    if (agent.target_x == null) return
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y

    ctx.save()
    // Dashed path with arrowheads
    ctx.setLineDash([4, 6])
    ctx.strokeStyle = '#c8a03055'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineTo(agent.target_x, agent.target_y)
    ctx.stroke()

    // Target marker (diamond)
    ctx.setLineDash([])
    ctx.fillStyle = '#c8a03088'
    ctx.strokeStyle = '#c8a030bb'
    ctx.lineWidth = 1
    const s = 5
    ctx.beginPath()
    ctx.moveTo(agent.target_x, agent.target_y - s)
    ctx.lineTo(agent.target_x + s, agent.target_y)
    ctx.lineTo(agent.target_x, agent.target_y + s)
    ctx.lineTo(agent.target_x - s, agent.target_y)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
    ctx.restore()
  })
}

// ── Chat connection lines ──────────────────────────────────
function drawChatLinks(ctx, agents, ts) {
  const chatters = agents.filter((a) => a.status === 'chatting' && a.conversation_partner_id)
  const drawn = new Set()
  chatters.forEach((a) => {
    if (drawn.has(a.id)) return
    const partner = agents.find((p) => p.id === a.conversation_partner_id)
    if (!partner) return
    drawn.add(a.id)
    drawn.add(partner.id)
    const ax = a._renderX ?? a.position_x
    const ay = a._renderY ?? a.position_y
    const px = partner._renderX ?? partner.position_x
    const py = partner._renderY ?? partner.position_y
    const pulse = 0.4 + 0.6 * Math.abs(Math.sin(ts / 400))
    ctx.save()
    ctx.strokeStyle = `rgba(236,72,153,${pulse * 0.4})`
    ctx.lineWidth = 1.5
    ctx.setLineDash([4, 6])
    ctx.beginPath()
    ctx.moveTo(ax, ay)
    ctx.lineTo(px, py)
    ctx.stroke()
    ctx.restore()
  })
}

// ── LEGO-style agents (top-down view) ─────────────────────
function drawAgents(ctx, agents, selectedId, ts) {
  // ── Draw shadows first ──
  agents.forEach((agent) => {
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y
    ctx.save()
    ctx.beginPath()
    ctx.ellipse(x, y + 2, 12, 6, 0, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,0,0,0.12)'
    ctx.fill()
    ctx.restore()
  })

  // ── Draw agents ──
  agents.forEach((agent) => {
    const colors = ROLE[agent.role] || ROLE.default
    const isSelected = agent.id === selectedId
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y
    const rot = agent._renderRot ?? 0
    const isWorking = agent.status === 'working'

    ctx.save()
    ctx.translate(x, y)

    // ── Selection glow ──
    if (isSelected) {
      const pulse = 0.3 + 0.2 * Math.sin(ts / 400)
      ctx.beginPath()
      ctx.arc(0, 0, 22 + pulse * 3, 0, Math.PI * 2)
      ctx.fillStyle = hexAlpha(colors.ring, 0.15 + pulse * 0.1)
      ctx.fill()

      // Rotation ring
      ctx.save()
      ctx.rotate(ts / 1000)
      ctx.beginPath()
      ctx.arc(0, 0, 20, 0, Math.PI * 2)
      ctx.strokeStyle = hexAlpha(colors.ring, 0.4)
      ctx.lineWidth = 2
      ctx.setLineDash([4, 6])
      ctx.stroke()
      ctx.restore()
    }

    // ── Activity glow ──
    if (isWorking || agent.status === 'meeting') {
      const pulse = 0.3 + 0.3 * Math.sin(ts / 500)
      ctx.beginPath()
      ctx.arc(0, 0, 18, 0, Math.PI * 2)
      ctx.fillStyle = hexAlpha(colors.body, 0.08 + pulse * 0.08)
      ctx.fill()
    }

    // ★ LEGO FIGURE WITH ROTATION ★
    ctx.rotate(rot)

    const bodyW = 16
    const bodyH = 22
    const headR = 8
    const typingOffset = isWorking ? Math.sin(ts / 150) * 2 : 0

    // ── Legs ──
    const legW = 6
    const legH = 8
    ctx.fillStyle = darken(colors.body, 0.3)
    ctx.strokeStyle = darken(colors.body, 0.4)
    ctx.lineWidth = 1
    // Left leg
    roundRect(ctx, -legW - 1, bodyH / 2 - 4, legW, legH, 2)
    ctx.fill()
    ctx.stroke()
    // Right leg
    roundRect(ctx, 1, bodyH / 2 - 4, legW, legH, 2)
    ctx.fill()
    ctx.stroke()

    // ── Body ──
    ctx.fillStyle = colors.body
    ctx.strokeStyle = darken(colors.body, 0.2)
    ctx.lineWidth = 1.5
    roundRect(ctx, -bodyW / 2, -bodyH / 2 + 2, bodyW, bodyH, 3)
    ctx.fill()
    ctx.stroke()

    // Belt
    ctx.fillStyle = colors.belt
    ctx.fillRect(-bodyW / 2 + 2, bodyH / 2 - 5, bodyW - 4, 3)

    // ── Arms (Animated if working) ──
    const armW = 4
    const armH = 10
    ctx.fillStyle = C.skinTone
    ctx.strokeStyle = C.skinShadow
    ctx.lineWidth = 1
    // Left arm
    ctx.save()
    if (isWorking) ctx.translate(0, -typingOffset)
    roundRect(ctx, -bodyW / 2 - armW + 1, -2, armW, armH, 2)
    ctx.fill()
    ctx.stroke()
    ctx.restore()
    // Right arm
    ctx.save()
    if (isWorking) ctx.translate(0, typingOffset)
    roundRect(ctx, bodyW / 2 - 1, -2, armW, armH, 2)
    ctx.fill()
    ctx.stroke()
    ctx.restore()

    // ── Head (Subtle bob) ──
    const headY = -bodyH / 2 - headR + 6 + (isWorking ? Math.sin(ts / 400) * 0.5 : 0)
    ctx.fillStyle = C.skinTone
    ctx.strokeStyle = C.skinShadow
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.arc(0, headY, headR, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()

    // Hair
    ctx.fillStyle = darken(colors.body, 0.4)
    ctx.beginPath()
    ctx.arc(0, headY - 2, headR - 1, Math.PI * 1.2, Math.PI * 1.8)
    ctx.fill()

    // Eyes
    ctx.fillStyle = '#1a1a2a'
    ctx.beginPath()
    ctx.arc(-2.5, headY + 1, 1.2, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(2.5, headY + 1, 1.2, 0, Math.PI * 2)
    ctx.fill()

    ctx.restore() // End rotation/translation

    // ── Status dot (Relative to center, no rotation so it's always readable) ──
    const dotColor = STATUS_DOT[agent.status] || '#94a3b8'
    ctx.save()
    ctx.translate(x + 11, y + 10)
    ctx.beginPath()
    ctx.arc(0, 0, 4.5, 0, Math.PI * 2)
    ctx.fillStyle = '#fff'
    ctx.fill()
    ctx.strokeStyle = dotColor
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.beginPath()
    ctx.arc(0, 0, 3, 0, Math.PI * 2)
    ctx.fillStyle = dotColor
    ctx.fill()
    ctx.restore()

    // ── Name tag ──
    const nameTag = agent.name.split(' ')[0]
    ctx.font = 'bold 9px "Inter", system-ui, sans-serif'
    const tagW = ctx.measureText(nameTag).width + 12
    const tagH = 16
    const tagX = x - tagW / 2
    const tagY = y - 30

    ctx.save()
    ctx.fillStyle = isSelected ? hexAlpha(colors.body, 0.85) : 'rgba(255,255,255,0.85)'
    ctx.strokeStyle = isSelected ? colors.body : '#c8c4bc'
    ctx.lineWidth = 1
    roundRect(ctx, tagX, tagY, tagW, tagH, 4)
    ctx.fill()
    ctx.stroke()

    ctx.fillStyle = isSelected ? '#fff' : '#4a4a5a'
    ctx.textAlign = 'center'
    ctx.fillText(nameTag, x, tagY + tagH - 4)
    ctx.restore()
  })
}

// ── Energy bars (compact, below agent) ─────────────────────
function drawEnergyBars(ctx, agents, selectedId) {
  agents.forEach((agent) => {
    if (agent.id !== selectedId && agent.status === 'idle') return
    const x = agent._renderX ?? agent.position_x
    const y = agent._renderY ?? agent.position_y
    const barW = 24
    const barH = 3
    const bx = x - barW / 2
    const by = y + 16

    ctx.save()
    ctx.fillStyle = 'rgba(200,200,200,0.4)'
    roundRect(ctx, bx, by, barW, barH, 1.5)
    ctx.fill()

    const energy = (agent.energy ?? 100) / 100
    const color = energy > 0.6 ? '#10b981' : energy > 0.3 ? '#f59e0b' : '#ef4444'
    ctx.fillStyle = color
    roundRect(ctx, bx, by, Math.max(2, barW * energy), barH, 1.5)
    ctx.fill()
    ctx.restore()
  })
}

// ── Main render ────────────────────────────────────────────
export function renderFrame(ctx, agents, selectedId, ts) {
  // Background
  ctx.fillStyle = C.bg
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)

  drawGrid(ctx)
  drawRooms(ctx)
  drawDoors(ctx)
  drawFurniture(ctx, ts, agents)
  drawPaths(ctx, agents)
  drawChatLinks(ctx, agents, ts)
  drawAgents(ctx, agents, selectedId, ts)
  drawEnergyBars(ctx, agents, selectedId)
  drawBorder(ctx)
}

// ── Colour utilities ───────────────────────────────────────
function darken(hex, amt) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.max(0, (num >> 16) - Math.round(255 * amt))
  const g = Math.max(0, ((num >> 8) & 0xff) - Math.round(255 * amt))
  const b = Math.max(0, (num & 0xff) - Math.round(255 * amt))
  return `rgb(${r},${g},${b})`
}

export { darken as darkenColor }

export const AGENT_RADIUS = 16 // approximate bounding size for hit testing
