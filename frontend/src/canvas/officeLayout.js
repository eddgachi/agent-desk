/**
 * Office layout definition.
 * All coordinates are in "world units" on an 800×600 canvas.
 *
 * zones  – background areas (floor sections)
 * rooms  – enclosed rooms with a label
 * furniture – desks, tables, chairs drawn as shapes
 */

export const CANVAS_W = 900
export const CANVAS_H = 620

export const OFFICE_PADDING = 24

// ── Zone colours ──────────────────────────────────────────
const C = {
  floorMain:    '#1e2030',
  floorCorridor:'#191b28',
  wallFill:     '#2a2d3e',
  wallStroke:   '#3d4166',
  roomMeeting:  '#1a2540',
  roomBreak:    '#1a2d1f',
  deskFill:     '#2c3a1e',
  deskStroke:   '#4a6030',
  tableRound:   '#252040',
  tableStroke:  '#4040a0',
  chairFill:    '#2a2030',
  labelColor:   '#6b7280',
  labelRoom:    '#94a3b8',
  grid:         '#1a1d2e',
}

// ── Rooms ──────────────────────────────────────────────────
export const rooms = [
  // Open-plan work area
  {
    id: 'workfloor',
    label: 'Work Floor',
    x: OFFICE_PADDING, y: OFFICE_PADDING,
    w: 560, h: 380,
    fill: C.floorMain, stroke: C.wallStroke,
    labelColor: C.labelRoom,
  },
  // Meeting room top-right
  {
    id: 'meeting_a',
    label: 'Meeting A',
    x: 612, y: OFFICE_PADDING,
    w: 264, h: 180,
    fill: C.roomMeeting, stroke: '#3d5a8a',
    labelColor: '#7090c0',
  },
  // Meeting room bottom-right
  {
    id: 'meeting_b',
    label: 'Meeting B',
    x: 612, y: 228,
    w: 264, h: 176,
    fill: C.roomMeeting, stroke: '#3d5a8a',
    labelColor: '#7090c0',
  },
  // Break room bottom-left
  {
    id: 'breakroom',
    label: 'Break Room',
    x: OFFICE_PADDING, y: 432,
    w: 280, h: 164,
    fill: C.roomBreak, stroke: '#305030',
    labelColor: '#60a070',
  },
  // Server / storage bottom-right
  {
    id: 'server',
    label: 'Server Room',
    x: 330, y: 432,
    w: 254, h: 164,
    fill: '#1e1e2a', stroke: '#3a3a5a',
    labelColor: '#606080',
  },
  // Corridor (right strip)
  {
    id: 'corridor',
    label: '',
    x: 588, y: OFFICE_PADDING,
    w: 24, h: 572,
    fill: C.floorCorridor, stroke: 'transparent',
    labelColor: 'transparent',
  },
  // Corridor (bottom strip)
  {
    id: 'corridor_h',
    label: '',
    x: OFFICE_PADDING, y: 408,
    w: 560, h: 24,
    fill: C.floorCorridor, stroke: 'transparent',
    labelColor: 'transparent',
  },
]

// ── Furniture ──────────────────────────────────────────────
export const furniture = [
  // ── Work floor desks (2 rows × 4) ──
  ...makeDeskRow(60,  70, 4, 'A'),
  ...makeDeskRow(60, 170, 4, 'B'),
  ...makeDeskRow(60, 270, 4, 'C'),

  // ── Meeting A – round table + chairs ──
  { type: 'circle', x: 744, y: 120, r: 48, fill: C.tableRound, stroke: C.tableStroke },
  ...makeChairsAround(744, 120, 68, 6),

  // ── Meeting B – rectangular table ──
  { type: 'rect', x: 638, y: 268, w: 212, h: 90, fill: C.tableRound, stroke: C.tableStroke, r: 6 },
  ...makeChairsAround(744, 313, 72, 6),

  // ── Break room furniture ──
  { type: 'rect', x: 50, y: 460, w: 80, h: 50, fill: '#243020', stroke: '#406030', r: 4 }, // couch
  { type: 'circle', x: 200, y: 500, r: 28, fill: '#243020', stroke: '#406030' },            // coffee table
  { type: 'rect', x: 250, y: 455, w: 44, h: 28, fill: '#1e2820', stroke: '#305028', r: 3 }, // microwave
  { type: 'rect', x: 250, y: 490, w: 44, h: 28, fill: '#1e2820', stroke: '#305028', r: 3 }, // coffee machine
]

function makeDeskRow(startX, y, count, row) {
  const desks = []
  for (let i = 0; i < count; i++) {
    desks.push({
      type: 'desk',
      id: `desk_${row}${i + 1}`,
      label: `${row}${i + 1}`,
      x: startX + i * 128,
      y,
      w: 80,
      h: 52,
      fill: C.deskFill,
      stroke: C.deskStroke,
    })
  }
  return desks
}

function makeChairsAround(cx, cy, radius, count) {
  const chairs = []
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 2 - Math.PI / 2
    chairs.push({
      type: 'circle',
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
      r: 10,
      fill: C.chairFill,
      stroke: '#504060',
    })
  }
  return chairs
}

// ── Desk lookup: id → center position ──────────────────────
export const deskPositions = {}
furniture.forEach(f => {
  if (f.type === 'desk') {
    deskPositions[f.id] = { x: f.x + f.w / 2, y: f.y + f.h / 2 }
  }
})

// ── Named waypoints agents can target ─────────────────────
export const waypoints = {
  desk_A1: { x: 100,  y: 96  },
  desk_A2: { x: 228,  y: 96  },
  desk_A3: { x: 356,  y: 96  },
  desk_A4: { x: 484,  y: 96  },
  desk_B1: { x: 100,  y: 196 },
  desk_B2: { x: 228,  y: 196 },
  desk_B3: { x: 356,  y: 196 },
  desk_B4: { x: 484,  y: 196 },
  desk_C1: { x: 100,  y: 296 },
  desk_C2: { x: 228,  y: 296 },
  desk_C3: { x: 356,  y: 296 },
  desk_C4: { x: 484,  y: 296 },
  meeting_a: { x: 744, y: 120 },
  meeting_b: { x: 744, y: 313 },
  breakroom:  { x: 160, y: 510 },
  corridor:   { x: 600, y: 300 },
}
