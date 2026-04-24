/**
 * Office layout definition — blueprint / game-map style.
 * All coordinates are in "world units" on a 900×650 canvas.
 *
 * zones       – background floor sections
 * rooms       – enclosed rooms with walls
 * furniture   – desks, tables, chairs drawn as shapes
 * waypoints   – named positions agents can target
 */

export const CANVAS_W = 900
export const CANVAS_H = 650

export const OFFICE_PADDING = 20

// ── Colour palette (blueprint / game-map) ─────────────────
export const C = {
  // Background & floors
  bg: '#e2dcc9',
  floorWork: '#cdc5ae',
  floorCorridor: '#dad4c2',
  floorMeeting: '#bcc0ca',
  floorBreak: '#c2cab8',
  floorServer: '#c0bcc6',

  // Walls
  wallFill: '#a8a498',
  wallStroke: '#3a3a4e',
  wallShadow: '#989488',

  // Doors
  doorFill: '#c4c0b4',
  doorStroke: '#5a5a6a',

  // Furniture – desks
  deskFill: '#b8a888',
  deskStroke: '#6a5e40',
  deskTop: '#a89878',
  monitorFill: '#1a1a2a',
  monitorGlow: '#3a7aff33',
  chairFill: '#3a5a7a',
  chairStroke: '#2a4a6a',

  // Furniture – meeting tables
  tableFill: '#a89c84',
  tableStroke: '#6a6250',
  meetingChair: '#5a4a7a',

  // Furniture – break room
  counterFill: '#b0a890',
  counterStroke: '#6a6250',
  applianceFill: '#2a2a3a',

  // Labels
  labelRoom: '#4a4a5a',
  labelDesk: '#6a5e40',

  // Characters
  skinTone: '#e8c898',
  skinShadow: '#c8a878',
}

// ── Room / zone definitions ────────────────────────────────
export const rooms = [
  // ── Main work floor (open plan) ──
  {
    id: 'workfloor',
    label: 'Work Floor',
    x: OFFICE_PADDING,
    y: OFFICE_PADDING,
    w: 520,
    h: 380,
    fill: C.floorWork,
    stroke: C.wallStroke,
    labelColor: C.labelRoom,
  },
  // ── Meeting A (top-right) ──
  {
    id: 'meeting_a',
    label: 'Meeting A',
    x: 572,
    y: OFFICE_PADDING,
    w: 308,
    h: 180,
    fill: C.floorMeeting,
    stroke: C.wallStroke,
    labelColor: C.labelRoom,
  },
  // ── Meeting B (mid-right) ──
  {
    id: 'meeting_b',
    label: 'Meeting B',
    x: 572,
    y: 218,
    w: 308,
    h: 182,
    fill: C.floorMeeting,
    stroke: C.wallStroke,
    labelColor: C.labelRoom,
  },
  // ── Break room (bottom-left) ──
  {
    id: 'breakroom',
    label: 'Break Room',
    x: OFFICE_PADDING,
    y: 432,
    w: 308,
    h: 198,
    fill: C.floorBreak,
    stroke: C.wallStroke,
    labelColor: C.labelRoom,
  },
  // ── Server / storage (bottom-center) ──
  {
    id: 'server',
    label: 'Server Room',
    x: 352,
    y: 432,
    w: 206,
    h: 198,
    fill: C.floorServer,
    stroke: C.wallStroke,
    labelColor: C.labelRoom,
  },
  // ── Corridor (vertical, between work floor and meeting rooms) ──
  {
    id: 'corridor_v',
    label: '',
    x: 540,
    y: OFFICE_PADDING,
    w: 32,
    h: 380,
    fill: C.floorCorridor,
    stroke: 'transparent',
    labelColor: 'transparent',
  },
  // ── Corridor (horizontal, between work floor and bottom rooms) ──
  {
    id: 'corridor_h',
    label: '',
    x: OFFICE_PADDING,
    y: 400,
    w: 308,
    h: 32,
    fill: C.floorCorridor,
    stroke: 'transparent',
    labelColor: 'transparent',
  },
]

// ── Furniture ──────────────────────────────────────────────
// Helper: generate a row of desks
function makeDeskRow(startX, y, count, rowLabel) {
  const items = []
  for (let i = 0; i < count; i++) {
    const dx = startX + i * 118
    items.push({
      type: 'desk',
      id: `desk_${rowLabel}${i + 1}`,
      label: `${rowLabel}${i + 1}`,
      x: dx,
      y,
      w: 80,
      h: 50,
      fill: C.deskFill,
      stroke: C.deskStroke,
    })
    // Chair behind desk
    items.push({
      type: 'chair',
      parentDesk: `desk_${rowLabel}${i + 1}`,
      x: dx + 40,
      y: y - 20,
      r: 10,
      fill: C.chairFill,
      stroke: C.chairStroke,
    })
  }
  return items
}

export const furniture = [
  // ── Work floor desks — 2 rows of 4 ──
  ...makeDeskRow(52, 130, 4, 'A'),
  ...makeDeskRow(52, 250, 4, 'B'),

  // ── Meeting A – round table + chairs ──
  {
    type: 'circle',
    id: 'table_meeting_a',
    x: 726,
    y: 110,
    r: 48,
    fill: C.tableFill,
    stroke: C.tableStroke,
  },
  ...makeChairsAround(726, 110, 64, 6, C.meetingChair),

  // ── Meeting B – rectangular table + chairs ──
  {
    type: 'rect',
    id: 'table_meeting_b',
    x: 612,
    y: 262,
    w: 228,
    h: 94,
    r: 6,
    fill: C.tableFill,
    stroke: C.tableStroke,
  },
  ...makeChairsAround(726, 309, 72, 6, C.meetingChair),

  // ── Break room furniture ──
  // Kitchen counter (L-shaped)
  {
    type: 'rect',
    id: 'counter_top',
    x: 40,
    y: 452,
    w: 100,
    h: 36,
    r: 4,
    fill: C.counterFill,
    stroke: C.counterStroke,
  },
  {
    type: 'rect',
    id: 'counter_left',
    x: 40,
    y: 488,
    w: 36,
    h: 70,
    r: 4,
    fill: C.counterFill,
    stroke: C.counterStroke,
  },
  // Sink
  {
    type: 'rect',
    id: 'sink',
    x: 52,
    y: 458,
    w: 28,
    h: 24,
    r: 2,
    fill: '#d8dad8',
    stroke: '#9a9a9a',
  },
  // Coffee machine
  {
    type: 'rect',
    id: 'coffee_machine',
    x: 148,
    y: 510,
    w: 32,
    h: 28,
    r: 3,
    fill: C.applianceFill,
    stroke: '#5a5a6a',
  },
  // Microwave
  {
    type: 'rect',
    id: 'microwave',
    x: 148,
    y: 478,
    w: 32,
    h: 24,
    r: 2,
    fill: C.applianceFill,
    stroke: '#5a5a6a',
  },
  // Break table (small round)
  {
    type: 'circle',
    id: 'break_table',
    x: 250,
    y: 518,
    r: 22,
    fill: C.tableFill,
    stroke: C.tableStroke,
  },
  // Chairs around break table
  ...makeChairsAround(250, 518, 34, 4, '#5a7a5a'),

  // Couch / lounge area
  {
    type: 'rect',
    id: 'couch',
    x: 200,
    y: 452,
    w: 70,
    h: 36,
    r: 6,
    fill: '#6a8a7a',
    stroke: '#4a6a5a',
  },

  // ── Server room ──
  {
    type: 'rect',
    id: 'server_rack',
    x: 372,
    y: 452,
    w: 48,
    h: 80,
    r: 3,
    fill: '#3a3a4a',
    stroke: '#5a5a6a',
  },
  {
    type: 'rect',
    id: 'server_rack2',
    x: 430,
    y: 452,
    w: 48,
    h: 80,
    r: 3,
    fill: '#3a3a4a',
    stroke: '#5a5a6a',
  },
  // Blinking server lights
  ...(() => {
    const lights = []
    for (let rack = 0; rack < 2; rack++) {
      for (let row = 0; row < 6; row++) {
        lights.push({
          type: 'circle',
          id: `server_led_${rack}_${row}`,
          x: 380 + rack * 58 + (row % 2) * 10,
          y: 462 + row * 12,
          r: 2,
          fill: '#00ff66',
          stroke: 'transparent',
          blink: true,
        })
      }
    }
    return lights
  })(),

  // ── Printer station (in corridor) ──
  {
    type: 'rect',
    id: 'printer',
    x: 546,
    y: 370,
    w: 20,
    h: 30,
    r: 2,
    fill: '#4a4a5a',
    stroke: '#6a6a7a',
  },
  // Printer output tray
  {
    type: 'rect',
    id: 'printer_tray',
    x: 544,
    y: 402,
    w: 24,
    h: 6,
    r: 1,
    fill: '#c8c4bc',
    stroke: '#8a8a9a',
  },
  // Water cooler
  {
    type: 'circle',
    id: 'water_cooler',
    x: 556,
    y: 414,
    r: 10,
    fill: '#6a9ac8',
    stroke: '#4a7aaa',
  },
  {
    type: 'rect',
    id: 'water_cooler_base',
    x: 548,
    y: 420,
    w: 16,
    h: 8,
    r: 2,
    fill: '#3a5a7a',
    stroke: '#2a4a6a',
  },
]

function makeChairsAround(cx, cy, radius, count, fillColor) {
  const chairs = []
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2 - Math.PI / 2
    chairs.push({
      type: 'circle',
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
      r: 9,
      fill: fillColor,
      stroke: darken(fillColor, 0.2),
    })
  }
  return chairs
}

function darken(hex, amt) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.max(0, (num >> 16) - Math.round(255 * amt))
  const g = Math.max(0, ((num >> 8) & 0xff) - Math.round(255 * amt))
  const b = Math.max(0, (num & 0xff) - Math.round(255 * amt))
  return `rgb(${r},${g},${b})`
}

// ── Desk lookup: id → center position ────────────────────
export const deskPositions = {}
furniture.forEach((f) => {
  if (f.type === 'desk') {
    deskPositions[f.id] = { x: f.x + f.w / 2, y: f.y + f.h / 2 }
  }
})

// ── Named waypoints agents can target ─────────────────────
export const waypoints = {
  desk_A1: { x: 92, y: 110 },
  desk_A2: { x: 210, y: 110 },
  desk_A3: { x: 328, y: 110 },
  desk_A4: { x: 446, y: 110 },
  desk_B1: { x: 92, y: 230 },
  desk_B2: { x: 210, y: 230 },
  desk_B3: { x: 328, y: 230 },
  desk_B4: { x: 446, y: 230 },
  meeting_a: { x: 726, y: 110 },
  meeting_b: { x: 726, y: 309 },
  breakroom: { x: 200, y: 530 },
  break_couch: { x: 235, y: 470 },
  corridor: { x: 556, y: 310 },
  printer: { x: 556, y: 390 },
  server: { x: 455, y: 530 },
}
