/**
 * WebSocket connection manager for the live event stream.
 *
 * Provides a hook that:
 *  - Connects to /api/ws/live (proxied by Vite in dev)
 *  - Automatically reconnects with exponential back-off
 *  - Exposes connection status for the UI indicator
 *  - Distributes incoming BusEventSchema messages via a callback
 */

import { useEffect, useRef, useCallback, useState } from "react";
import type { BusEventSchema } from "../types";

export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";

interface UseWebSocketOptions {
  /** Called for every incoming event. */
  onEvent: (event: BusEventSchema) => void;
  /** Whether the hook should maintain a connection. */
  enabled?: boolean;
}

const BASE_DELAY = 1000;
const MAX_DELAY = 30000;

function wsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/api/ws/live`;
}

export function useWebSocket({ onEvent, enabled = true }: UseWebSocketOptions) {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;

  const connect = useCallback(() => {
    if (!enabledRef.current) return;

    // Clean up previous socket if it exists
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.close();
    }

    const ws = new WebSocket(wsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0;
      setStatus("connected");
    };

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as BusEventSchema;
        onEventRef.current(data);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (!enabledRef.current) {
        setStatus("disconnected");
        return;
      }
      setStatus("reconnecting");
      const delay = Math.min(BASE_DELAY * 2 ** retriesRef.current, MAX_DELAY);
      retriesRef.current += 1;
      timerRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      // onclose will fire after onerror — reconnect happens there
    };
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
      setStatus("disconnected");
    };
  }, [enabled, connect]);

  return { status };
}
