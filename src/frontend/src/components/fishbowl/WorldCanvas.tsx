/**
 * WorldCanvas — the core visual of the Fishbowl.
 *
 * Renders the world as an organic, beautiful canvas painting:
 *   1. Terrain base layer (blended gradients, no grid lines)
 *   2. Path network layer (warm earth connecting lines)
 *   3. Structure layer (icons growing from terrain)
 *   4. Agent layer (glowing dots that glide between positions)
 *   5. Interaction layer (fading communication arcs)
 *   6. Hover/selection overlay
 *
 * Uses raw HTML5 Canvas2D with requestAnimationFrame for ~60fps.
 */

import {
  useRef,
  useEffect,
  useCallback,
  useState,
  useMemo,
  type MouseEvent as ReactMouseEvent,
} from "react";
import { useSimulation } from "../../hooks/useSimulation";
import { useAnimation } from "../../hooks/useAnimation";
import type {
  WorldStateResponse,
  AgentSummary,
  TileSchema,
  StructureSchema,
  BusEventSchema,
} from "../../types";
import { BusEventType } from "../../types";

// ---------------------------------------------------------------------------
// Design system colours (from index.css)
// ---------------------------------------------------------------------------

const C = {
  cream: "#FEFCF6",
  plainBase: "#F5F0E3",
  rocky: "#D4C8B8",
  dense: "#C8D8C4",
  waterShift: "#A8CDE8",
  foodShift: "#D4C878",
  materialShift: "#BBA88D",
  pathLine: "#BBA88D",
  sage: "#6B9B7B",
  sagePale: "#E8F2EC",
  rose: "#C88B93",
  goldPale: "#FDF6E3",
  gold: "#C5962B",
  goldLight: "#E8D59A",
  sky: "#5B9BD5",
  skyLight: "#A8CDE8",
  earth: "#8B7355",
  earthLight: "#BBA88D",
  ember: "#D4785A",
  ink: "#2D2A24",
  inkMuted: "#8C8578",
  warmWhite: "#FFFAF0",
  border: "#E8E2D6",
} as const;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CommunicationLine {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  startTime: number;
  broadcast: boolean;
}

interface StructureBuildAnim {
  x: number;
  y: number;
  startTime: number;
  structureType: string;
  customName: string | null;
  composedFrom: string[] | null;
}

interface ThoughtBubble {
  agentId: number;
  text: string;
  startTime: number;
  isMessage: boolean;
}

interface AgentPrevPos {
  x: number;
  y: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpColor(c1: [number, number, number], c2: [number, number, number], t: number): string {
  const r = Math.round(lerp(c1[0], c2[0], t));
  const g = Math.round(lerp(c1[1], c2[1], t));
  const b = Math.round(lerp(c1[2], c2[2], t));
  return `rgb(${r},${g},${b})`;
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

const RGB_PLAIN = hexToRgb(C.plainBase);
const RGB_ROCKY = hexToRgb(C.rocky);
const RGB_DENSE = hexToRgb(C.dense);
const RGB_WATER = hexToRgb(C.waterShift);
const RGB_FOOD = hexToRgb(C.foodShift);
const RGB_MATERIAL = hexToRgb(C.materialShift);
const RGB_SAGE = hexToRgb(C.sage);
const RGB_ROSE = hexToRgb(C.rose);

function terrainBaseRgb(terrain: string): [number, number, number] {
  switch (terrain) {
    case "rocky":
      return RGB_ROCKY;
    case "dense":
      return RGB_DENSE;
    default:
      return RGB_PLAIN;
  }
}

/** Compute a tile colour that blends terrain + resource presence. */
function tileColor(tile: TileSchema): [number, number, number] {
  const base = terrainBaseRgb(tile.terrain);
  let r = base[0],
    g = base[1],
    b = base[2];

  // Shift toward resource colours proportional to amount/max
  for (const res of Object.values(tile.resources)) {
    const ratio = res.max_amount > 0 ? res.amount / res.max_amount : 0;
    const strength = ratio * 0.35; // max 35% shift
    let target: [number, number, number];
    switch (res.resource_type) {
      case "water":
        target = RGB_WATER;
        break;
      case "food":
        target = RGB_FOOD;
        break;
      default:
        target = RGB_MATERIAL;
    }
    r = lerp(r, target[0], strength);
    g = lerp(g, target[1], strength);
    b = lerp(b, target[2], strength);
  }

  return [Math.round(r), Math.round(g), Math.round(b)];
}

/** Get the blended colour for a tile by averaging with neighbors. */
function blendedTileColor(
  tiles: TileSchema[][],
  x: number,
  y: number,
  gw: number,
  gh: number,
): [number, number, number] {
  const center = tileColor(tiles[y][x]);
  const neighbors: [number, number, number][] = [center];

  // Cardinal neighbors
  if (x > 0) neighbors.push(tileColor(tiles[y][x - 1]));
  if (x < gw - 1) neighbors.push(tileColor(tiles[y][x + 1]));
  if (y > 0) neighbors.push(tileColor(tiles[y - 1][x]));
  if (y < gh - 1) neighbors.push(tileColor(tiles[y + 1][x]));

  // Weight center 2x vs each neighbor 1x
  const totalWeight = 2 + (neighbors.length - 1);
  let r = center[0] * 2,
    g = center[1] * 2,
    b = center[2] * 2;
  for (let i = 1; i < neighbors.length; i++) {
    r += neighbors[i][0];
    g += neighbors[i][1];
    b += neighbors[i][2];
  }

  return [Math.round(r / totalWeight), Math.round(g / totalWeight), Math.round(b / totalWeight)];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function WorldCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const {
    worldState,
    prevWorldState,
    selectedAgentId,
    selectAgent,
    feedEvents,
    tickInterval,
  } = useSimulation();

  // ----- Camera state (zoom + pan) -----------------------------------------
  const cameraRef = useRef({
    offsetX: 0,
    offsetY: 0,
    zoom: 1,
    // Interaction state
    dragging: false,
    dragStartX: 0,
    dragStartY: 0,
    dragStartOffX: 0,
    dragStartOffY: 0,
  });

  // ----- Animation ephemeral state -----------------------------------------
  const commLinesRef = useRef<CommunicationLine[]>([]);
  const buildAnimsRef = useRef<StructureBuildAnim[]>([]);
  const thoughtBubblesRef = useRef<ThoughtBubble[]>([]);
  const prevPositionsRef = useRef<Map<number, AgentPrevPos>>(new Map());
  const newAgentsRef = useRef<Map<number, number>>(new Map()); // agentId -> arrivalTime
  const animProgressRef = useRef(0);
  const [hoveredAgent, setHoveredAgent] = useState<AgentSummary | null>(null);
  const hoverPosRef = useRef<{ cx: number; cy: number } | null>(null);

  // ----- Track prev agent positions when world state changes ---------------
  const lastTickRef = useRef(-1);
  useEffect(() => {
    if (!worldState) return;
    if (worldState.tick === lastTickRef.current) return;

    // Store previous positions from prevWorldState
    if (prevWorldState && prevWorldState.tick !== worldState.tick) {
      const map = new Map<number, AgentPrevPos>();
      for (const a of prevWorldState.agents) {
        map.set(a.id, { x: a.position.x, y: a.position.y });
      }
      prevPositionsRef.current = map;

      // Detect new agents
      const prevIds = new Set(prevWorldState.agents.map((a) => a.id));
      const now = performance.now();
      for (const a of worldState.agents) {
        if (!prevIds.has(a.id)) {
          newAgentsRef.current.set(a.id, now);
        }
      }
    }

    lastTickRef.current = worldState.tick;
  }, [worldState, prevWorldState]);

  // ----- Precomputed tile colour cache (avoids ~150K RGB ops/frame) ---------
  const tileColorCache = useMemo(() => {
    if (!worldState) return null;
    const tiles = worldState.tiles;
    const gw = worldState.grid_width;
    const gh = worldState.grid_height;
    const buf = new Uint8Array(gw * gh * 3);
    for (let y = 0; y < gh; y++) {
      for (let x = 0; x < gw; x++) {
        const rgb = blendedTileColor(tiles, x, y, gw, gh);
        const idx = (y * gw + x) * 3;
        buf[idx] = rgb[0];
        buf[idx + 1] = rgb[1];
        buf[idx + 2] = rgb[2];
      }
    }
    return buf;
  }, [worldState]);

  // ----- Process feed events for communication lines & build anims ---------
  const lastFeedLenRef = useRef(0);
  useEffect(() => {
    if (feedEvents.length <= lastFeedLenRef.current) {
      lastFeedLenRef.current = feedEvents.length;
      return;
    }

    const newEvents = feedEvents.slice(lastFeedLenRef.current);
    lastFeedLenRef.current = feedEvents.length;
    const now = performance.now();

    for (const ev of newEvents) {
      if (ev.type === BusEventType.MESSAGE_SENT && worldState) {
        const senderId = ev.agent_id;
        const receiverId = ev.data.receiver_id as number | undefined;
        if (senderId != null) {
          const sender = worldState.agents.find((a) => a.id === senderId);
          const receiver = receiverId != null
            ? worldState.agents.find((a) => a.id === receiverId)
            : null;

          if (sender) {
            const line: CommunicationLine = {
              fromX: sender.position.x,
              fromY: sender.position.y,
              toX: receiver ? receiver.position.x : sender.position.x,
              toY: receiver ? receiver.position.y : sender.position.y,
              startTime: now,
              broadcast: receiver == null,
            };
            commLinesRef.current.push(line);
          }
        }
      }

      if (ev.type === BusEventType.STRUCTURE_BUILT && ev.data.position) {
        const pos = ev.data.position as { x: number; y: number };
        buildAnimsRef.current.push({
          x: pos.x,
          y: pos.y,
          startTime: now,
          structureType: (ev.data.structure_type as string) ?? "shelter",
          customName: (ev.data.custom_name as string) ?? null,
          composedFrom: (ev.data.composed_from as string[]) ?? null,
        });
      }

      // Thought bubbles from reasoning and messages
      if (ev.type === BusEventType.REASONING_STEP && ev.agent_id != null) {
        const thought =
          (ev.data.response as string) ??
          (ev.data.summary as string) ??
          "";
        if (thought) {
          const truncated =
            thought.length > 50
              ? thought.slice(0, 47) + "\u2026"
              : thought;
          thoughtBubblesRef.current.push({
            agentId: ev.agent_id,
            text: truncated,
            startTime: now,
            isMessage: false,
          });
        }
      }
      if (ev.type === BusEventType.MESSAGE_SENT && ev.agent_id != null) {
        const content =
          (ev.data.content as string) ??
          (ev.data.message as string) ??
          "";
        if (content) {
          const truncated =
            content.length > 60
              ? content.slice(0, 57) + "\u2026"
              : content;
          thoughtBubblesRef.current.push({
            agentId: ev.agent_id,
            text: truncated,
            startTime: now,
            isMessage: true,
          });
        }
      }

      // Cap thought bubble buffer
      if (thoughtBubblesRef.current.length > 30) {
        thoughtBubblesRef.current = thoughtBubblesRef.current.slice(-30);
      }
    }
  }, [feedEvents, worldState]);

  // ----- Resize canvas to fill container -----------------------------------
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ro = new ResizeObserver(() => {
      const dpr = window.devicePixelRatio || 1;
      const w = container.clientWidth;
      const h = container.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
    });
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  // ----- Fit camera when first world state arrives -------------------------
  const fittedRef = useRef(false);
  useEffect(() => {
    if (!worldState || fittedRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    const cw = canvas.width / dpr;
    const ch = canvas.height / dpr;
    if (cw === 0 || ch === 0) return;

    const gw = worldState.grid_width;
    const gh = worldState.grid_height;

    // Calculate zoom to fit grid with some padding
    const padding = 40;
    const zoomX = (cw - padding * 2) / (gw * 24);
    const zoomY = (ch - padding * 2) / (gh * 24);
    const zoom = Math.min(zoomX, zoomY, 3);

    const cam = cameraRef.current;
    cam.zoom = zoom;
    cam.offsetX = (cw - gw * 24 * zoom) / 2;
    cam.offsetY = (ch - gh * 24 * zoom) / 2;
    fittedRef.current = true;
  }, [worldState]);

  // ----- Main render callback ----------------------------------------------
  const render = useCallback(
    (progress: number) => {
      animProgressRef.current = progress;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const cw = canvas.width / dpr;
      const ch = canvas.height / dpr;

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Clear background
      ctx.fillStyle = C.cream;
      ctx.fillRect(0, 0, cw, ch);

      if (!worldState) {
        // Draw loading state
        ctx.fillStyle = C.inkMuted;
        ctx.font = '16px Inter, system-ui, sans-serif';
        ctx.textAlign = "center";
        ctx.fillText("Connecting to simulation...", cw / 2, ch / 2);
        return;
      }

      const cam = cameraRef.current;
      const { zoom, offsetX, offsetY } = cam;
      const gw = worldState.grid_width;
      const gh = worldState.grid_height;
      const tiles = worldState.tiles;
      const TILE = 24; // base tile size in pixels
      const ts = TILE * zoom; // actual tile size on screen

      // Apply camera transform
      ctx.save();
      ctx.translate(offsetX, offsetY);
      ctx.scale(zoom, zoom);

      const now = performance.now();

      // ===== Layer 1: Terrain ==============================================
      // Precompute blended colours for visible tiles
      // Determine visible tile range
      const visMinX = Math.max(0, Math.floor(-offsetX / ts));
      const visMaxX = Math.min(gw - 1, Math.ceil((-offsetX + cw) / ts));
      const visMinY = Math.max(0, Math.floor(-offsetY / ts));
      const visMaxY = Math.min(gh - 1, Math.ceil((-offsetY + ch) / ts));

      for (let y = visMinY; y <= visMaxY; y++) {
        for (let x = visMinX; x <= visMaxX; x++) {
          if (tileColorCache) {
            const idx = (y * gw + x) * 3;
            ctx.fillStyle = `rgb(${tileColorCache[idx]},${tileColorCache[idx + 1]},${tileColorCache[idx + 2]})`;
          } else {
            const rgb = blendedTileColor(tiles, x, y, gw, gh);
            ctx.fillStyle = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
          }
          // Slight overlap (0.5px) to prevent sub-pixel seams
          ctx.fillRect(x * TILE - 0.25, y * TILE - 0.25, TILE + 0.5, TILE + 0.5);
        }
      }

      // Subtle "glow" for tiles with many structures (civilisation warmth)
      for (let y = visMinY; y <= visMaxY; y++) {
        for (let x = visMinX; x <= visMaxX; x++) {
          const tile = tiles[y][x];
          if (tile.structures.length > 0) {
            const intensity = Math.min(tile.structures.length / 5, 1.0) * 0.15;
            ctx.fillStyle = `rgba(197, 150, 43, ${intensity})`; // gold tint
            ctx.fillRect(x * TILE, y * TILE, TILE, TILE);
          }
        }
      }

      // ===== Layer 2: Path Network =========================================
      ctx.strokeStyle = `rgba(187, 168, 141, 0.5)`; // C.pathLine
      ctx.lineWidth = 2.5 / zoom; // Consistent visual width
      ctx.lineCap = "round";

      // Collect path tiles and draw connections
      const pathTiles: { x: number; y: number }[] = [];
      for (let y = visMinY; y <= visMaxY; y++) {
        for (let x = visMinX; x <= visMaxX; x++) {
          const tile = tiles[y][x];
          const hasPath = tile.structures.some(
            (s) => s.structure_type === "path",
          );
          if (hasPath) pathTiles.push({ x, y });
        }
      }

      // Draw connections between adjacent path tiles
      const pathSet = new Set<string>();
      for (const p of pathTiles) pathSet.add(`${p.x},${p.y}`);

      ctx.beginPath();
      for (const p of pathTiles) {
        const cx = p.x * TILE + TILE / 2;
        const cy = p.y * TILE + TILE / 2;
        // Check cardinal neighbors
        for (const [dx, dy] of [
          [1, 0],
          [0, 1],
        ] as const) {
          const nx = p.x + dx;
          const ny = p.y + dy;
          if (pathSet.has(`${nx},${ny}`)) {
            const ncx = nx * TILE + TILE / 2;
            const ncy = ny * TILE + TILE / 2;
            ctx.moveTo(cx, cy);
            ctx.lineTo(ncx, ncy);
          }
        }
      }
      ctx.stroke();

      // ===== Layer 3: Structures ===========================================
      for (let y = visMinY; y <= visMaxY; y++) {
        for (let x = visMinX; x <= visMaxX; x++) {
          const tile = tiles[y][x];
          for (const s of tile.structures) {
            if (s.structure_type === "path") continue; // drawn above
            drawStructure(ctx, x, y, TILE, s, now, zoom);
          }
        }
      }

      // Build animations (scale from 0)
      const activeBuilds: StructureBuildAnim[] = [];
      for (const ba of buildAnimsRef.current) {
        const elapsed = now - ba.startTime;
        if (elapsed < 500) {
          activeBuilds.push(ba);
          const scale = easeOutBack(elapsed / 500);
          ctx.save();
          const cx = ba.x * TILE + TILE / 2;
          const cy = ba.y * TILE + TILE / 2;
          ctx.translate(cx, cy);
          ctx.scale(scale, scale);
          ctx.translate(-cx, -cy);
          drawStructure(
            ctx,
            ba.x,
            ba.y,
            TILE,
            {
              structure_type: ba.structureType,
              builder_id: 0,
              built_tick: 0,
              health: 1,
              message: null,
              stored_resources: {},
              capacity: 0,
              custom_name: ba.customName,
              custom_description: null,
              composed_from: ba.composedFrom,
            },
            now,
            zoom,
          );
          ctx.restore();
        }
      }
      buildAnimsRef.current = activeBuilds;

      // ===== Layer 4: Agents ===============================================
      const agents = worldState.agents;
      const prevPosMap = prevPositionsRef.current;
      const t = Math.min(progress, 1.0); // animation interpolation

      for (const agent of agents) {
        const prev = prevPosMap.get(agent.id);
        const currX = agent.position.x * TILE + TILE / 2;
        const currY = agent.position.y * TILE + TILE / 2;
        let ax: number, ay: number;

        if (prev) {
          const prevX = prev.x * TILE + TILE / 2;
          const prevY = prev.y * TILE + TILE / 2;
          ax = lerp(prevX, currX, t);
          ay = lerp(prevY, currY, t);
        } else {
          ax = currX;
          ay = currY;
        }

        // Check if within visible area (with generous margin)
        const screenX = ax * zoom + offsetX;
        const screenY = ay * zoom + offsetY;
        if (screenX < -40 || screenX > cw + 40 || screenY < -40 || screenY > ch + 40) continue;

        // Fade-in for new agents
        let alpha = 1.0;
        const arrivalTime = newAgentsRef.current.get(agent.id);
        if (arrivalTime != null) {
          const fadeProgress = (now - arrivalTime) / 1000;
          if (fadeProgress < 1) {
            alpha = fadeProgress;
          } else {
            newAgentsRef.current.delete(agent.id);
          }
        }

        // Size: 9px healthy, 5px degraded
        const baseR = lerp(5, 9, 1 - agent.degradation_ratio);
        const r = baseR;

        // Colour: sage (healthy) to rose (degraded)
        const deg = agent.degradation_ratio;
        const fillRgb = lerpColor(RGB_SAGE, RGB_ROSE, deg);

        // Wellbeing glow
        if (agent.wellbeing > 0.5) {
          const glowStrength = (agent.wellbeing - 0.5) * 2; // 0..1
          const breathe = 0.6 + 0.4 * Math.sin(now / 1500 + agent.id * 0.7);
          const glowR = r + 4 + glowStrength * 6;
          const glowAlpha = glowStrength * 0.25 * breathe * alpha;
          ctx.beginPath();
          ctx.arc(ax, ay, glowR, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(253, 246, 227, ${glowAlpha})`; // goldPale
          ctx.fill();
        }

        // Curiosity sparkle (high curiosity = exploring/creating drive)
        if ((agent.curiosity ?? 0) > 0.7) {
          const sparkleStrength = (agent.curiosity - 0.7) * 3.33; // 0..1
          const sparkle = 0.5 + 0.5 * Math.sin(now / 800 + agent.id * 1.3);
          const sparkleR = r + 5 + sparkleStrength * 4;
          const sparkleAlpha = sparkleStrength * 0.2 * sparkle * alpha;
          ctx.beginPath();
          ctx.arc(ax, ay, sparkleR, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(147, 112, 219, ${sparkleAlpha})`; // soft violet
          ctx.fill();
        }

        // Specialisation ring
        if (agent.specialisations.length > 0) {
          const specColor = getSpecColor(agent.specialisations[0]);
          ctx.beginPath();
          ctx.arc(ax, ay, r + 1.5, 0, Math.PI * 2);
          ctx.strokeStyle = specColor;
          ctx.lineWidth = 1.2;
          ctx.globalAlpha = alpha;
          ctx.stroke();
          ctx.globalAlpha = 1;
        }

        // Main agent circle with outline
        ctx.beginPath();
        ctx.arc(ax, ay, r, 0, Math.PI * 2);
        ctx.fillStyle = fillRgb;
        ctx.globalAlpha = alpha;
        ctx.fill();
        // Dark outline for visibility
        ctx.strokeStyle = `rgba(45, 42, 36, ${0.4 * alpha})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.globalAlpha = 1;

        // Selection highlight
        if (agent.id === selectedAgentId) {
          ctx.beginPath();
          ctx.arc(ax, ay, r + 4, 0, Math.PI * 2);
          ctx.strokeStyle = C.sky;
          ctx.lineWidth = 2.5;
          ctx.stroke();
        }

        // Agent ID + descriptive label when zoomed in enough
        if (zoom >= 1.5) {
          ctx.save();
          const label = getAgentLabel(agent);
          const labelText = label ? `${agent.id} \u00B7 ${label}` : `${agent.id}`;
          ctx.font = `bold ${Math.round(9 / zoom)}px Inter, system-ui, sans-serif`;
          ctx.textAlign = "center";
          ctx.fillStyle = C.ink;
          ctx.globalAlpha = Math.min(1, (zoom - 1.5) * 2.5) * alpha;
          ctx.fillText(labelText, ax, ay + r + 10 / zoom);
          ctx.restore();
        }
      }

      // ===== Layer 5: Communication Lines ==================================
      const activeLines: CommunicationLine[] = [];
      for (const line of commLinesRef.current) {
        const elapsed = now - line.startTime;
        const totalDuration = 2000; // 2 seconds total
        if (elapsed > totalDuration) continue;

        activeLines.push(line);

        // Fade stages: in 0-300ms, hold 300-1500ms, out 1500-2000ms
        let lineAlpha: number;
        if (elapsed < 300) {
          lineAlpha = elapsed / 300;
        } else if (elapsed < 1500) {
          lineAlpha = 0.6 + 0.4 * Math.sin(elapsed / 200); // pulse
          lineAlpha = Math.max(0.4, Math.min(0.8, lineAlpha));
        } else {
          lineAlpha = 1 - (elapsed - 1500) / 500;
        }
        lineAlpha = Math.max(0, Math.min(1, lineAlpha)) * 0.6;

        const fx = line.fromX * TILE + TILE / 2;
        const fy = line.fromY * TILE + TILE / 2;
        const tx = line.toX * TILE + TILE / 2;
        const ty = line.toY * TILE + TILE / 2;

        ctx.beginPath();
        ctx.strokeStyle = `rgba(168, 205, 232, ${lineAlpha})`; // skyLight
        ctx.lineWidth = 1.5;
        if (line.broadcast) {
          ctx.setLineDash([4, 4]);
        }
        ctx.moveTo(fx, fy);
        ctx.lineTo(tx, ty);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      commLinesRef.current = activeLines;

      // ===== Layer 5.5: Thought Bubbles ================================
      const BUBBLE_DURATION = 4500;
      // GC expired bubbles
      thoughtBubblesRef.current = thoughtBubblesRef.current.filter(
        (b) => now - b.startTime <= BUBBLE_DURATION,
      );

      if (zoom >= 0.7) {
        const shownAgents = new Set<number>();
        // Iterate reverse so most recent bubble per agent is drawn
        for (let i = thoughtBubblesRef.current.length - 1; i >= 0; i--) {
          const bubble = thoughtBubblesRef.current[i];
          if (shownAgents.has(bubble.agentId)) continue;
          shownAgents.add(bubble.agentId);

          const bAgent = agents.find((a) => a.id === bubble.agentId);
          if (!bAgent) continue;

          // Interpolated position
          const bPrev = prevPosMap.get(bAgent.id);
          const bCurrX = bAgent.position.x * TILE + TILE / 2;
          const bCurrY = bAgent.position.y * TILE + TILE / 2;
          let bax: number, bay: number;
          if (bPrev) {
            bax = lerp(bPrev.x * TILE + TILE / 2, bCurrX, t);
            bay = lerp(bPrev.y * TILE + TILE / 2, bCurrY, t);
          } else {
            bax = bCurrX;
            bay = bCurrY;
          }

          // Cull off-screen
          const bScreenX = bax * zoom + offsetX;
          const bScreenY = bay * zoom + offsetY;
          if (
            bScreenX < -80 ||
            bScreenX > cw + 80 ||
            bScreenY < -40 ||
            bScreenY > ch + 40
          )
            continue;

          // Fade: in 0-200ms, hold 200-3500ms, out 3500-4500ms
          const elapsed = now - bubble.startTime;
          let bAlpha: number;
          if (elapsed < 200) bAlpha = elapsed / 200;
          else if (elapsed < 3500) bAlpha = 1;
          else bAlpha = 1 - (elapsed - 3500) / 1000;
          bAlpha = Math.max(0, Math.min(0.92, bAlpha));

          // Draw bubble — sizes in world units, scaled by 1/zoom for constant screen size
          const bFontSize = 10 / zoom;
          const isMsg = bubble.isMessage;
          ctx.save();
          ctx.font = `${isMsg ? "" : "italic "}${bFontSize}px Inter, system-ui, sans-serif`;
          const bTextW = ctx.measureText(bubble.text).width;
          const bPad = 4 / zoom;
          const bBoxW = bTextW + bPad * 2;
          const bBoxH = bFontSize + bPad * 2;
          const bAgentR = lerp(5, 9, 1 - bAgent.degradation_ratio);
          const bGap = 3 / zoom;
          const bBoxX = bax - bBoxW / 2;
          const bBoxY = bay - bAgentR - bGap - bBoxH;

          ctx.globalAlpha = bAlpha;

          // Background
          ctx.fillStyle = isMsg
            ? "rgba(227, 240, 250, 0.93)"
            : "rgba(254, 252, 246, 0.90)";
          ctx.strokeStyle = isMsg
            ? "rgba(91, 155, 213, 0.5)"
            : "rgba(140, 133, 120, 0.35)";
          ctx.lineWidth = 0.8 / zoom;
          roundRect(ctx, bBoxX, bBoxY, bBoxW, bBoxH, 3 / zoom);
          ctx.fill();
          ctx.stroke();

          // Small pointer triangle
          const triSize = 2.5 / zoom;
          ctx.beginPath();
          ctx.moveTo(bax - triSize, bBoxY + bBoxH);
          ctx.lineTo(bax, bBoxY + bBoxH + triSize);
          ctx.lineTo(bax + triSize, bBoxY + bBoxH);
          ctx.closePath();
          ctx.fillStyle = isMsg
            ? "rgba(227, 240, 250, 0.93)"
            : "rgba(254, 252, 246, 0.90)";
          ctx.fill();

          // Text
          ctx.fillStyle = isMsg ? "#5B9BD5" : "#8C8578";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(bubble.text, bax, bBoxY + bBoxH / 2);

          ctx.globalAlpha = 1;
          ctx.restore();
        }
      }

      ctx.restore(); // end camera transform

      // ===== Layer 6: Hover Tooltip ========================================
      if (hoveredAgent && hoverPosRef.current) {
        const { cx, cy } = hoverPosRef.current;
        drawTooltip(ctx, hoveredAgent, cx, cy, cw, ch);
      }
    },
    [worldState, selectedAgentId, hoveredAgent, tickInterval],
  );

  // ----- Drive animation loop ----------------------------------------------
  const { resetProgress } = useAnimation(render, tickInterval);

  // Reset on new tick
  const tickRef = useRef(0);
  useEffect(() => {
    if (worldState && worldState.tick !== tickRef.current) {
      tickRef.current = worldState.tick;
      resetProgress();
    }
  }, [worldState, resetProgress]);

  // ----- Mouse interaction -------------------------------------------------
  const getWorldPos = useCallback(
    (clientX: number, clientY: number) => {
      const canvas = canvasRef.current;
      if (!canvas || !worldState) return null;
      const rect = canvas.getBoundingClientRect();
      const cam = cameraRef.current;
      const mx = clientX - rect.left;
      const my = clientY - rect.top;
      const TILE = 24;
      const worldX = (mx - cam.offsetX) / cam.zoom;
      const worldY = (my - cam.offsetY) / cam.zoom;
      const tileX = Math.floor(worldX / TILE);
      const tileY = Math.floor(worldY / TILE);
      return { worldX, worldY, tileX, tileY, screenX: mx, screenY: my };
    },
    [worldState],
  );

  const findAgentAt = useCallback(
    (worldX: number, worldY: number): AgentSummary | null => {
      if (!worldState) return null;
      const TILE = 24;
      let closest: AgentSummary | null = null;
      let closestDist = Infinity;

      for (const a of worldState.agents) {
        const ax = a.position.x * TILE + TILE / 2;
        const ay = a.position.y * TILE + TILE / 2;
        const dx = worldX - ax;
        const dy = worldY - ay;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const hitRadius = 8; // generous click target
        if (dist < hitRadius && dist < closestDist) {
          closest = a;
          closestDist = dist;
        }
      }
      return closest;
    },
    [worldState],
  );

  const handleMouseDown = useCallback((e: ReactMouseEvent) => {
    const cam = cameraRef.current;
    cam.dragging = true;
    cam.dragStartX = e.clientX;
    cam.dragStartY = e.clientY;
    cam.dragStartOffX = cam.offsetX;
    cam.dragStartOffY = cam.offsetY;
  }, []);

  const handleMouseMove = useCallback(
    (e: ReactMouseEvent) => {
      const cam = cameraRef.current;
      if (cam.dragging) {
        cam.offsetX = cam.dragStartOffX + (e.clientX - cam.dragStartX);
        cam.offsetY = cam.dragStartOffY + (e.clientY - cam.dragStartY);
        setHoveredAgent(null);
        return;
      }

      // Hover detection
      const pos = getWorldPos(e.clientX, e.clientY);
      if (!pos) return;
      const agent = findAgentAt(pos.worldX, pos.worldY);
      setHoveredAgent(agent);
      if (agent) {
        hoverPosRef.current = { cx: pos.screenX, cy: pos.screenY };
      } else {
        hoverPosRef.current = null;
      }
    },
    [getWorldPos, findAgentAt],
  );

  const handleMouseUp = useCallback(
    (e: ReactMouseEvent) => {
      const cam = cameraRef.current;
      const wasDrag =
        Math.abs(e.clientX - cam.dragStartX) > 3 ||
        Math.abs(e.clientY - cam.dragStartY) > 3;
      cam.dragging = false;

      if (!wasDrag) {
        // Click — select agent
        const pos = getWorldPos(e.clientX, e.clientY);
        if (pos) {
          const agent = findAgentAt(pos.worldX, pos.worldY);
          selectAgent(agent ? agent.id : null);
        }
      }
    },
    [getWorldPos, findAgentAt, selectAgent],
  );

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const cam = cameraRef.current;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    const newZoom = Math.max(0.3, Math.min(10, cam.zoom * zoomFactor));

    // Zoom toward mouse position
    cam.offsetX = mx - (mx - cam.offsetX) * (newZoom / cam.zoom);
    cam.offsetY = my - (my - cam.offsetY) * (newZoom / cam.zoom);
    cam.zoom = newZoom;
  }, []);

  const handleDoubleClick = useCallback(
    (e: ReactMouseEvent) => {
      const cam = cameraRef.current;
      const canvas = canvasRef.current;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      const newZoom = Math.min(cam.zoom * 2, 10);
      cam.offsetX = mx - (mx - cam.offsetX) * (newZoom / cam.zoom);
      cam.offsetY = my - (my - cam.offsetY) * (newZoom / cam.zoom);
      cam.zoom = newZoom;
    },
    [],
  );

  // Welcome hint — auto-dismiss after 8s or on any interaction
  const [hintDismissed, setHintDismissed] = useState(false);
  const showHint = !hintDismissed && worldState && worldState.agents.length > 0;
  useEffect(() => {
    if (hintDismissed) return;
    const timer = setTimeout(() => setHintDismissed(true), 8000);
    return () => clearTimeout(timer);
  }, [hintDismissed]);

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden" style={{ cursor: hoveredAgent ? "pointer" : "grab" }}>
      <canvas
        ref={canvasRef}
        onMouseDown={(e) => { setHintDismissed(true); handleMouseDown(e); }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          cameraRef.current.dragging = false;
          setHoveredAgent(null);
        }}
        onWheel={(e) => { setHintDismissed(true); handleWheel(e); }}
        onDoubleClick={handleDoubleClick}
        className="block h-full w-full"
      />

      {/* Compact inline legend (bottom-left) */}
      <div
        className="pointer-events-none absolute bottom-3 left-3 flex flex-col gap-1 rounded-lg px-3 py-2"
        style={{
          background: "rgba(255, 250, 240, 0.92)",
          border: `1px solid ${C.border}`,
          backdropFilter: "blur(4px)",
        }}
      >
        <div className="flex items-center gap-4">
          {/* Agents */}
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{ background: C.sage, border: "1px solid rgba(45,42,36,0.3)" }}
            />
            <span className="text-[10px]" style={{ color: C.inkMuted }}>Healthy agent</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: C.rose, border: "1px solid rgba(45,42,36,0.3)" }}
            />
            <span className="text-[10px]" style={{ color: C.inkMuted }}>Degraded</span>
          </div>
          {/* Structures */}
          <div className="flex items-center gap-1.5">
            <svg width="10" height="10" viewBox="0 0 10 10">
              <polygon points="5,1 1,9 9,9" fill={C.earthLight} stroke="rgba(45,42,36,0.3)" strokeWidth="0.5" />
            </svg>
            <span className="text-[10px]" style={{ color: C.inkMuted }}>Shelter</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg width="10" height="10" viewBox="0 0 10 10">
              <rect x="1" y="2" width="8" height="6" fill={C.goldLight} stroke="rgba(45,42,36,0.3)" strokeWidth="0.5" />
            </svg>
            <span className="text-[10px]" style={{ color: C.inkMuted }}>Storage</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{
                background: "transparent",
                boxShadow: `0 0 4px 2px rgba(197,150,43,0.4)`,
                border: `1px solid rgba(197,150,43,0.3)`,
              }}
            />
            <span className="text-[10px]" style={{ color: C.inkMuted }}>High social wellbeing</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg width="14" height="6" viewBox="0 0 14 6">
              <line x1="0" y1="3" x2="14" y2="3" stroke={C.skyLight} strokeWidth="1.5" />
            </svg>
            <span className="text-[10px]" style={{ color: C.inkMuted }}>Talking</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg width="14" height="6" viewBox="0 0 14 6">
              <line x1="0" y1="3" x2="14" y2="3" stroke={C.skyLight} strokeWidth="1.5" strokeDasharray="3 3" />
            </svg>
            <span className="text-[10px]" style={{ color: C.inkMuted }}>Broadcast</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{
                background: "transparent",
                boxShadow: `0 0 3px 1px rgba(197,150,43,0.6)`,
                border: `1px solid ${C.gold}`,
              }}
            />
            <span className="text-[10px]" style={{ color: C.inkMuted }}>Innovation</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{
                background: "transparent",
                boxShadow: `0 0 4px 2px rgba(147, 112, 219, 0.4)`,
                border: `1px solid rgba(147, 112, 219, 0.5)`,
              }}
            />
            <span className="text-[10px]" style={{ color: C.inkMuted }}>High curiosity</span>
          </div>
        </div>
      </div>

      {/* First-time welcome hint (top-center) */}
      {showHint && (
        <div
          className="pointer-events-auto absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-3 rounded-lg px-4 py-2 shadow-md"
          style={{
            background: "rgba(255, 250, 240, 0.95)",
            border: `1px solid ${C.border}`,
            backdropFilter: "blur(4px)",
          }}
        >
          <span className="text-xs" style={{ color: C.ink }}>
            Scroll to zoom, drag to pan, click an agent to inspect it
          </span>
          <button
            onClick={() => setHintDismissed(true)}
            className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium transition-colors hover:bg-[#E8E2D6]"
            style={{ color: C.inkMuted }}
          >
            Got it
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Drawing helpers
// ---------------------------------------------------------------------------

function drawStructure(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  TILE: number,
  s: StructureSchema,
  now: number,
  zoom: number,
) {
  const cx = x * TILE + TILE / 2;
  const cy = y * TILE + TILE / 2;

  // Determine tier & size
  const isComposition = s.composed_from != null && s.composed_from.length > 0;
  const isInnovation = s.custom_name != null && !isComposition;
  let size = 3; // base
  if (isComposition) size = 5;
  if (isInnovation) size = 5;

  // Health fading
  const healthAlpha = 0.4 + s.health * 0.6;

  // Innovation shimmer
  if (isInnovation) {
    const shimmer = 0.3 + 0.3 * Math.sin(now / 600 + x * 3.7 + y * 2.3);
    ctx.beginPath();
    ctx.arc(cx, cy, size + 3, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(197, 150, 43, ${shimmer * healthAlpha})`; // gold shimmer
    ctx.fill();
  }

  ctx.globalAlpha = healthAlpha;

  switch (s.structure_type) {
    case "shelter": {
      // Warm triangle
      ctx.beginPath();
      ctx.moveTo(cx, cy - size);
      ctx.lineTo(cx - size, cy + size * 0.7);
      ctx.lineTo(cx + size, cy + size * 0.7);
      ctx.closePath();
      ctx.fillStyle = isComposition ? C.earth : C.earthLight;
      ctx.fill();
      break;
    }
    case "storage": {
      // Warm rectangle
      const half = size * 0.8;
      ctx.fillStyle = isComposition ? C.gold : C.goldLight;
      ctx.fillRect(cx - half, cy - half * 0.7, half * 2, half * 1.4);
      break;
    }
    case "marker": {
      // Circle with dot
      ctx.beginPath();
      ctx.arc(cx, cy, size * 0.8, 0, Math.PI * 2);
      ctx.strokeStyle = C.inkMuted;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(cx, cy, 1.5, 0, Math.PI * 2);
      ctx.fillStyle = C.inkMuted;
      ctx.fill();
      break;
    }
    default: {
      // Generic: filled circle
      ctx.beginPath();
      ctx.arc(cx, cy, size * 0.7, 0, Math.PI * 2);
      ctx.fillStyle = isComposition ? C.ember : C.earthLight;
      ctx.fill();
    }
  }

  ctx.globalAlpha = 1;
}

function drawTooltip(
  ctx: CanvasRenderingContext2D,
  agent: AgentSummary,
  sx: number,
  sy: number,
  canvasW: number,
  canvasH: number,
) {
  const label = getAgentLabel(agent);
  const lines = [
    label ? `Agent ${agent.id} \u2014 ${label}` : `Agent ${agent.id}`,
  ];
  if (agent.current_action_type) {
    lines.push(`Doing: ${agent.current_action_type}`);
  }
  if (agent.goals.length > 0) {
    const goal = agent.goals[0].length > 40 ? agent.goals[0].slice(0, 37) + "..." : agent.goals[0];
    lines.push(`Goal: ${goal}`);
  }
  if (agent.specialisations.length > 0) {
    lines.push(`Skills: ${agent.specialisations.join(", ")}`);
  }
  const health = (1 - agent.degradation_ratio) * 100;
  const wb = agent.wellbeing * 100;
  lines.push(`Health ${health.toFixed(0)}% | Social ${wb.toFixed(0)}%`);

  ctx.font = '12px Inter, system-ui, sans-serif';
  const lineHeight = 18;
  const padding = 8;
  const maxWidth = Math.max(...lines.map((l) => ctx.measureText(l).width));
  const boxW = maxWidth + padding * 2;
  const boxH = lines.length * lineHeight + padding * 2;

  // Position tooltip (avoid going off-screen)
  let tx = sx + 12;
  let ty = sy - boxH / 2;
  if (tx + boxW > canvasW - 4) tx = sx - boxW - 12;
  if (ty < 4) ty = 4;
  if (ty + boxH > canvasH - 4) ty = canvasH - boxH - 4;

  // Background
  ctx.fillStyle = "rgba(255, 250, 240, 0.95)"; // warmWhite
  ctx.strokeStyle = C.border;
  ctx.lineWidth = 1;
  roundRect(ctx, tx, ty, boxW, boxH, 6);
  ctx.fill();
  ctx.stroke();

  // Text
  ctx.fillStyle = C.ink;
  ctx.textAlign = "left";
  for (let i = 0; i < lines.length; i++) {
    const isHeader = i === 0;
    ctx.font = isHeader
      ? 'bold 12px Inter, system-ui, sans-serif'
      : '12px Inter, system-ui, sans-serif';
    ctx.fillText(lines[i], tx + padding, ty + padding + 12 + i * lineHeight);
  }
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}

function easeOutBack(t: number): number {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

function getSpecColor(spec: string): string {
  const s = spec.toLowerCase();
  if (s.includes("gather")) return C.sage;
  if (s.includes("build")) return C.earth;
  if (s.includes("communicat") || s.includes("social")) return C.sky;
  return C.goldLight;
}

function getAgentLabel(agent: AgentSummary): string | null {
  if (agent.specialisations.length > 0) {
    const s = agent.specialisations[0].toLowerCase();
    if (s.includes("gather")) return "Gatherer";
    if (s.includes("build")) return "Builder";
    if (s.includes("communicat") || s.includes("social")) return "Diplomat";
    if (s.includes("compos")) return "Alchemist";
    if (s.includes("innovat")) return "Inventor";
    if (s.includes("explor") || s.includes("move")) return "Scout";
    return "Specialist";
  }
  if (agent.needs_critical) return "Struggling";
  if ((agent.curiosity ?? 0) > 0.8) return "Curious";
  if (agent.wellbeing > 0.8 && agent.degradation_ratio < 0.2) return "Thriving";
  if (agent.degradation_ratio > 0.6) return "Fading";
  return null;
}
