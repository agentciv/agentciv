/**
 * Simulation state context & hook.
 *
 * Provides the WorldStateResponse (current + previous for animation
 * interpolation), selected agent tracking, live/historical mode, and
 * WebSocket connection status to all Fishbowl components.
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
  BusEventSchema,
  AgentDetailResponse,
} from "../types";
import { BusEventType } from "../types";
import { fetchState, fetchHistoryState } from "../api/client";
import { useWebSocket, type ConnectionStatus } from "../api/websocket";

// ---------------------------------------------------------------------------
// Feed event (enriched BusEvent used by LiveFeed)
// ---------------------------------------------------------------------------

export interface FeedEvent extends BusEventSchema {
  /** Unique id for React keys. */
  feedId: string;
}

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

export interface SimulationContextValue {
  worldState: WorldStateResponse | null;
  prevWorldState: WorldStateResponse | null;
  selectedAgentId: number | null;
  selectAgent: (id: number | null) => void;
  isLive: boolean;
  currentTick: number;
  latestTick: number;
  seekToTick: (tick: number) => void;
  goLive: () => void;
  connectionStatus: ConnectionStatus;
  feedEvents: FeedEvent[];
  /** Milliseconds between ticks — used by animation system. */
  tickInterval: number;
  /** Optional provider for agent detail data (used in replay mode). */
  agentDetailProvider?: (id: number) => AgentDetailResponse | null;
  /** Whether the replay is currently playing (undefined in live mode). */
  playing?: boolean;
  /** Toggle play/pause (only available in replay mode). */
  togglePlayPause?: () => void;
}

export const SimulationContext = createContext<SimulationContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

const MAX_FEED = 200;
let feedCounter = 0;

export function SimulationProvider({ children }: { children: ReactNode }) {
  // ----- core state --------------------------------------------------------
  const [worldState, setWorldState] = useState<WorldStateResponse | null>(null);
  const [prevWorldState, setPrevWorldState] = useState<WorldStateResponse | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [isLive, setIsLive] = useState(true);
  const [feedEvents, setFeedEvents] = useState<FeedEvent[]>([]);
  const latestTickRef = useRef(0);
  const [latestTick, setLatestTick] = useState(0);
  const currentTick = worldState?.tick ?? 0;

  // Estimated tick interval (default 5s, refined from observation)
  const [tickInterval, setTickInterval] = useState(5000);
  const lastTickTimeRef = useRef<number>(0);

  // ----- initial fetch -----------------------------------------------------
  useEffect(() => {
    fetchState()
      .then((state) => {
        setWorldState(state);
        setPrevWorldState(state);
        latestTickRef.current = state.tick;
        setLatestTick(state.tick);
      })
      .catch(() => {
        // Backend not reachable yet — that's fine, WS will trigger refresh
      });
  }, []);

  // ----- WebSocket event handler -------------------------------------------
  const onEvent = useCallback(
    (event: BusEventSchema) => {
      // Always accumulate feed events (even in historical mode, for context)
      if (isLive) {
        const feedEvent: FeedEvent = {
          ...event,
          feedId: `fe-${++feedCounter}`,
        };
        setFeedEvents((prev) => {
          const next = [...prev, feedEvent];
          return next.length > MAX_FEED ? next.slice(next.length - MAX_FEED) : next;
        });
      }

      // On TICK_END, fetch fresh world state
      if (event.type === BusEventType.TICK_END) {
        const now = performance.now();
        if (lastTickTimeRef.current > 0) {
          const elapsed = now - lastTickTimeRef.current;
          // Smooth the estimate
          setTickInterval((prev) => prev * 0.7 + elapsed * 0.3);
        }
        lastTickTimeRef.current = now;

        latestTickRef.current = event.tick;
        setLatestTick(event.tick);

        if (isLive) {
          fetchState()
            .then((state) => {
              setPrevWorldState((prev) => prev ?? state);
              setWorldState((prev) => {
                setPrevWorldState(prev);
                return state;
              });
            })
            .catch(() => {
              // Transient failure — next tick will retry
            });
        }
      }
    },
    [isLive],
  );

  const { status: connectionStatus } = useWebSocket({ onEvent, enabled: true });

  // ----- public actions ----------------------------------------------------
  const selectAgent = useCallback((id: number | null) => {
    setSelectedAgentId(id);
  }, []);

  const seekToTick = useCallback(
    (tick: number) => {
      setIsLive(false);
      fetchHistoryState(tick)
        .then((state) => {
          setPrevWorldState(worldState);
          setWorldState(state);
        })
        .catch(() => {
          // ignore
        });
    },
    [worldState],
  );

  const goLive = useCallback(() => {
    setIsLive(true);
    fetchState()
      .then((state) => {
        setPrevWorldState(state);
        setWorldState(state);
      })
      .catch(() => {
        // ignore
      });
  }, []);

  // ----- context value -----------------------------------------------------
  const value: SimulationContextValue = {
    worldState,
    prevWorldState,
    selectedAgentId,
    selectAgent,
    isLive,
    currentTick,
    latestTick,
    seekToTick,
    goLive,
    connectionStatus,
    feedEvents,
    tickInterval,
  };

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Consumer hook
// ---------------------------------------------------------------------------

export function useSimulation(): SimulationContextValue {
  const ctx = useContext(SimulationContext);
  if (!ctx) {
    throw new Error("useSimulation must be used within <SimulationProvider>");
  }
  return ctx;
}
