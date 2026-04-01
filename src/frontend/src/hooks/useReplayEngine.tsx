/**
 * Replay engine — provides the same SimulationContextValue interface
 * as the live SimulationProvider, but powered by pre-recorded static
 * JSON data instead of a WebSocket + REST API.
 *
 * To a consumer component, there is zero difference between live and replay.
 * Agents glide, events appear in the feed, the inspector works, the
 * timeline scrubs. The only visible difference is the status indicator
 * shows "Replay · tick N/M" instead of "Connected".
 */

import {
  createContext,
  useContext,
  useState,
  useRef,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import type {
  WorldStateResponse,
  AgentSummary,
  AgentDetailResponse,
  ActionSchema,
  TileSchema,
  StatsResponse,
  BusEventSchema,
} from "../types";
import type { ConnectionStatus } from "../api/websocket";
import { SimulationContext, type SimulationContextValue, type FeedEvent } from "./useSimulation";

// ---------------------------------------------------------------------------
// Replay metadata (loaded from /replay_data/metadata.json)
// ---------------------------------------------------------------------------

interface ChunkIndex {
  name: string;
  start_tick: number;
  end_tick: number;
  file: string;
}

interface ReplayMetadata {
  name: string;
  min_tick: number;
  max_tick: number;
  total_ticks: number;
  agent_count: number;
  grid_width: number;
  grid_height: number;
  chunk_size: number;
  snapshot_chunks: ChunkIndex[];
  event_chunks: ChunkIndex[];
}

// ---------------------------------------------------------------------------
// Raw snapshot → WorldStateResponse transformer
// ---------------------------------------------------------------------------

const DEGRADATION_THRESHOLD = 0.3; // matches Capabilities.DEGRADATION_THRESHOLD

/** Transform a raw per-tick snapshot (backend format) into WorldStateResponse. */
function snapshotToWorldState(raw: Record<string, unknown>): WorldStateResponse {
  const tick = raw.tick as number;
  const gw = raw.grid_width as number;
  const gh = raw.grid_height as number;

  // Tiles: raw tiles[x][y] → frontend tiles[row][col] (same indexing)
  const rawTiles = raw.tiles as TileSchema[][];
  const tiles: TileSchema[][] = rawTiles; // format is compatible

  // Agents: dict keyed by string id → array of AgentSummary
  const rawAgents = raw.agents as Record<string, Record<string, unknown>>;
  const agents: AgentSummary[] = [];

  for (const agent of Object.values(rawAgents)) {
    const pos = agent.position as { x: number; y: number };
    const caps = agent.capabilities as {
      perception_range: number;
      base_perception_range: number;
      movement_speed: number;
      base_movement_speed: number;
      memory_capacity: number;
      base_memory_capacity: number;
    };
    const needs = agent.needs as { levels: Record<string, number> };
    const inventory = (agent.inventory as string[]) || [];
    const currentAction = agent.current_action as { type: string } | null;

    // Compute degradation_ratio
    const minPerc = 1;
    const basePerc = caps.base_perception_range || 5;
    const totalRange = basePerc - minPerc;
    const currentLoss = basePerc - caps.perception_range;
    const degradation = totalRange > 0
      ? Math.min(1, Math.max(0, currentLoss / totalRange))
      : 0;

    // needs_critical: any level below threshold
    const needsCritical = Object.values(needs.levels).some(
      (v) => v < DEGRADATION_THRESHOLD,
    );

    agents.push({
      id: agent.id as number,
      position: { x: pos.x, y: pos.y },
      wellbeing: (agent.wellbeing as number) ?? 0.5,
      curiosity: (agent.curiosity as number) ?? 0.5,
      degradation_ratio: degradation,
      specialisations: (agent.specialisations as string[]) || [],
      goals: (agent.goals as string[]) || [],
      age: (agent.age as number) ?? 0,
      current_action_type: currentAction?.type ?? null,
      inventory_count: inventory.length,
      needs_critical: needsCritical,
    });
  }

  // Compute stats
  let totalStructures = 0;
  let totalInnovations = 0;
  for (const col of rawTiles) {
    for (const tile of col) {
      totalStructures += tile.structures.length;
      for (const s of tile.structures) {
        if (s.custom_name) totalInnovations++;
      }
    }
  }

  const recipes = (raw.discovered_recipes as unknown[]) || [];
  const rules = (raw.collective_rules as Array<{ established?: boolean }>) || [];
  const establishedRules = rules.filter((r) => r.established).length;
  const specialisedAgents = agents.filter((a) => a.specialisations.length > 0).length;

  const stats: StatsResponse = {
    current_tick: tick,
    total_agents: agents.length,
    total_structures: totalStructures,
    total_innovations: totalInnovations,
    total_compositions: 0,
    total_recipes: recipes.length,
    total_rules: rules.length,
    established_rules: establishedRules,
    total_milestones: 0,
    total_specialised_agents: specialisedAgents,
    uptime_ticks: tick,
  };

  return { tick, grid_width: gw, grid_height: gh, tiles, agents, stats };
}

// ---------------------------------------------------------------------------
// Chunk cache
// ---------------------------------------------------------------------------

type SnapshotChunk = Record<string, Record<string, unknown>>; // tick → raw snapshot
type EventChunk = BusEventSchema[];

const snapshotCache = new Map<string, SnapshotChunk>();
const eventCache = new Map<string, EventChunk>();

async function loadSnapshotChunk(
  chunk: ChunkIndex,
): Promise<SnapshotChunk> {
  const cached = snapshotCache.get(chunk.name);
  if (cached) return cached;

  const res = await fetch(`/replay_data/${chunk.file}`);
  const data = (await res.json()) as SnapshotChunk;
  snapshotCache.set(chunk.name, data);
  return data;
}

async function loadEventChunk(chunk: ChunkIndex): Promise<EventChunk> {
  const cached = eventCache.get(chunk.name);
  if (cached) return cached;

  const res = await fetch(`/replay_data/${chunk.file}`);
  const data = (await res.json()) as EventChunk;
  eventCache.set(chunk.name, data);
  return data;
}

function findChunk(tick: number, chunks: ChunkIndex[]): ChunkIndex | null {
  return chunks.find((c) => tick >= c.start_tick && tick <= c.end_tick) ?? null;
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

const MAX_FEED = 200;
let replayFeedCounter = 0;

export function ReplayProvider({ children }: { children: ReactNode }) {
  const [metadata, setMetadata] = useState<ReplayMetadata | null>(null);
  const [worldState, setWorldState] = useState<WorldStateResponse | null>(null);
  const [prevWorldState, setPrevWorldState] = useState<WorldStateResponse | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [feedEvents, setFeedEvents] = useState<FeedEvent[]>([]);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1); // ticks per second
  const currentTickRef = useRef(0);
  const playIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const currentTick = worldState?.tick ?? 0;
  const latestTick = metadata?.max_tick ?? 0;

  // Converted snapshot cache (avoid re-transforming)
  const convertedCache = useRef(new Map<number, WorldStateResponse>());

  // Raw agents dict for the current tick (used by agentDetailProvider)
  const rawAgentsRef = useRef<Record<string, Record<string, unknown>>>({});

  // ----- Load metadata on mount -----------------------------------------------
  useEffect(() => {
    fetch("/replay_data/metadata.json")
      .then((r) => r.json())
      .then((m: ReplayMetadata) => {
        setMetadata(m);
        // Load the first tick
        loadTick(m.min_tick, m).then((ws) => {
          if (ws) {
            setWorldState(ws);
            setPrevWorldState(ws);
            currentTickRef.current = m.min_tick;
          }
        });
      })
      .catch((err) => {
        console.error("Failed to load replay metadata:", err);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ----- Load a specific tick's world state -----------------------------------
  const loadTick = useCallback(
    async (
      tick: number,
      meta: ReplayMetadata | null,
    ): Promise<WorldStateResponse | null> => {
      const m = meta ?? metadata;
      if (!m) return null;

      // Check converted cache
      const cached = convertedCache.current.get(tick);
      if (cached) return cached;

      const chunk = findChunk(tick, m.snapshot_chunks);
      if (!chunk) return null;

      const data = await loadSnapshotChunk(chunk);
      const raw = data[String(tick)];
      if (!raw) return null;

      // Store raw agents for agentDetailProvider
      const rawAgents = raw.agents as Record<string, Record<string, unknown>>;
      if (rawAgents) {
        rawAgentsRef.current = rawAgents;
      }

      const ws = snapshotToWorldState(raw);
      convertedCache.current.set(tick, ws);

      // Keep cache bounded (last 200 ticks)
      if (convertedCache.current.size > 200) {
        const oldest = convertedCache.current.keys().next().value;
        if (oldest !== undefined) convertedCache.current.delete(oldest);
      }

      return ws;
    },
    [metadata],
  );

  // ----- Load events for a tick -----------------------------------------------
  const loadEventsForTick = useCallback(
    async (tick: number): Promise<BusEventSchema[]> => {
      if (!metadata) return [];
      const chunk = findChunk(tick, metadata.event_chunks);
      if (!chunk) return [];
      const events = await loadEventChunk(chunk);
      return events.filter((e) => e.tick === tick);
    },
    [metadata],
  );

  // ----- Advance to next tick -------------------------------------------------
  const advanceTick = useCallback(async () => {
    if (!metadata) return;
    const nextTick = currentTickRef.current + 1;
    if (nextTick > metadata.max_tick) {
      // Reached the end — stop playing
      setPlaying(false);
      return;
    }

    const ws = await loadTick(nextTick, null);
    if (!ws) return;

    // Update world state with animation support
    setWorldState((prev) => {
      setPrevWorldState(prev);
      return ws;
    });
    currentTickRef.current = nextTick;

    // Add events for this tick to the feed
    const tickEvents = await loadEventsForTick(nextTick);
    if (tickEvents.length > 0) {
      const feedItems: FeedEvent[] = tickEvents.map((e) => ({
        ...e,
        feedId: `rf-${++replayFeedCounter}`,
      }));
      setFeedEvents((prev) => {
        const next = [...prev, ...feedItems];
        return next.length > MAX_FEED ? next.slice(next.length - MAX_FEED) : next;
      });
    }
  }, [metadata, loadTick, loadEventsForTick]);

  // ----- Auto-play timer ------------------------------------------------------
  useEffect(() => {
    if (playIntervalRef.current) {
      clearInterval(playIntervalRef.current);
      playIntervalRef.current = null;
    }

    if (playing && metadata) {
      const ms = Math.max(100, 1000 / speed);
      playIntervalRef.current = setInterval(() => {
        advanceTick();
      }, ms);
    }

    return () => {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    };
  }, [playing, speed, metadata, advanceTick]);

  // ----- Public actions -------------------------------------------------------
  const selectAgent = useCallback((id: number | null) => {
    setSelectedAgentId(id);
  }, []);

  const seekToTick = useCallback(
    async (tick: number) => {
      if (!metadata) return;
      const clamped = Math.max(metadata.min_tick, Math.min(metadata.max_tick, tick));
      const ws = await loadTick(clamped, null);
      if (!ws) return;

      setPrevWorldState(worldState);
      setWorldState(ws);
      currentTickRef.current = clamped;

      // Load events up to this tick (last ~50 events for context)
      const events: BusEventSchema[] = [];
      const startTick = Math.max(metadata.min_tick, clamped - 10);
      for (let t = startTick; t <= clamped; t++) {
        const tickEvents = await loadEventsForTick(t);
        events.push(...tickEvents);
      }
      const feedItems: FeedEvent[] = events.slice(-MAX_FEED).map((e) => ({
        ...e,
        feedId: `rf-${++replayFeedCounter}`,
      }));
      setFeedEvents(feedItems);
    },
    [metadata, worldState, loadTick, loadEventsForTick],
  );

  const goLive = useCallback(() => {
    // In replay mode, "go live" means jump to the end and start playing
    if (!metadata) return;
    seekToTick(metadata.max_tick);
    setPlaying(true);
  }, [metadata, seekToTick]);

  // ----- Agent detail provider (converts raw snapshot agent → AgentDetailResponse) --
  const agentDetailProvider = useCallback(
    (id: number): AgentDetailResponse | null => {
      const rawAgents = rawAgentsRef.current;
      const agent = rawAgents[String(id)];
      if (!agent) return null;

      const pos = agent.position as { x: number; y: number };
      const caps = agent.capabilities as {
        perception_range: number;
        base_perception_range: number;
        movement_speed: number;
        base_movement_speed: number;
        memory_capacity: number;
        base_memory_capacity: number;
      };
      const needs = agent.needs as { levels: Record<string, number> };
      const inventory = (agent.inventory as string[]) || [];
      const currentAction = agent.current_action as Record<string, unknown> | null;
      const memories = (agent.memories as Array<{
        tick: number;
        summary: string;
        importance: number;
        access_count: number;
      }>) || [];

      // Compute degradation_ratio (same logic as snapshotToWorldState)
      const minPerc = 1;
      const basePerc = caps.base_perception_range || 5;
      const totalRange = basePerc - minPerc;
      const currentLoss = basePerc - caps.perception_range;
      const degradation = totalRange > 0
        ? Math.min(1, Math.max(0, currentLoss / totalRange))
        : 0;

      const needsCritical = Object.values(needs.levels).some(
        (v) => v < DEGRADATION_THRESHOLD,
      );

      // Build ActionSchema from raw current_action
      let actionSchema: ActionSchema | null = null;
      if (currentAction) {
        actionSchema = {
          type: (currentAction.type as string) ?? "idle",
          direction: (currentAction.direction as [number, number]) ?? null,
          resource_type: (currentAction.resource_type as string) ?? null,
          message: (currentAction.message as string) ?? null,
          target_agent_id: (currentAction.target_agent_id as number) ?? null,
          goal: (currentAction.goal as string) ?? null,
          structure_type: (currentAction.structure_type as string) ?? null,
          reasoning: (currentAction.reasoning as string) ?? "",
        };
      }

      return {
        id: agent.id as number,
        position: { x: pos.x, y: pos.y },
        wellbeing: (agent.wellbeing as number) ?? 0.5,
        curiosity: (agent.curiosity as number) ?? 0.5,
        degradation_ratio: degradation,
        specialisations: (agent.specialisations as string[]) || [],
        goals: (agent.goals as string[]) || [],
        age: (agent.age as number) ?? 0,
        current_action_type: actionSchema?.type ?? null,
        inventory_count: inventory.length,
        needs_critical: needsCritical,
        needs: { levels: needs.levels },
        capabilities: {
          perception_range: caps.perception_range,
          movement_speed: caps.movement_speed,
          memory_capacity: caps.memory_capacity,
          base_perception_range: caps.base_perception_range,
          base_movement_speed: caps.base_movement_speed,
          base_memory_capacity: caps.base_memory_capacity,
          degradation_ratio: degradation,
        },
        memories,
        plan: (agent.plan as string[]) || [],
        inventory,
        activity_counts: (agent.activity_counts as Record<string, number>) || {},
        known_recipes: (agent.known_recipes as string[]) || [],
        relationships: (() => {
          const rawRels = agent.relationships as Record<string, {
            interaction_count: number;
            positive_count: number;
            negative_count: number;
            last_interaction_tick: number;
            is_bonded: boolean;
          }> | undefined;
          if (!rawRels) return [];
          return Object.entries(rawRels).map(([aid, rel]) => ({
            agent_id: Number(aid),
            interaction_count: rel.interaction_count ?? 0,
            positive_count: rel.positive_count ?? 0,
            negative_count: rel.negative_count ?? 0,
            last_interaction_tick: rel.last_interaction_tick ?? 0,
            is_bonded: rel.is_bonded ?? false,
          }));
        })(),
        current_action: actionSchema,
        alive_since_tick: (agent.alive_since_tick as number) ?? 0,
      };
    },
    [],
  );

  // ----- Play/pause toggle ----------------------------------------------------
  const togglePlayPause = useCallback(() => {
    setPlaying((p) => !p);
  }, []);

  // ----- Tick interval for animation system -----------------------------------
  const tickInterval = speed > 0 ? 1000 / speed : 1000;

  // ----- Context value (same interface as SimulationProvider) -----------------
  const value: SimulationContextValue = {
    worldState,
    prevWorldState,
    selectedAgentId,
    selectAgent,
    isLive: false, // replay is never "live"
    currentTick,
    latestTick,
    seekToTick,
    goLive,
    connectionStatus: "connected" as ConnectionStatus, // always "connected" in replay
    feedEvents,
    tickInterval,
    agentDetailProvider,
    playing,
    togglePlayPause,
  };

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  );
}

// Consumer components use useSimulation() — it reads from SimulationContext
// which this ReplayProvider populates. No separate hook needed.
