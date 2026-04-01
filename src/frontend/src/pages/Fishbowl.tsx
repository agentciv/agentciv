/**
 * Fishbowl — full-screen visualization of the AI civilisation.
 *
 * Automatically detects whether replay data is available:
 * - If /replay_data/metadata.json exists → replay mode (recorded simulation)
 * - Otherwise → live mode (connects to running backend via WebSocket)
 *
 * All child components use useSimulation() and see the same interface
 * regardless of which mode is active.
 */

import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { SimulationProvider, useSimulation } from "../hooks/useSimulation";
import { ReplayProvider } from "../hooks/useReplayEngine";
import FishbowlLayout from "../components/fishbowl/FishbowlLayout";
import { FishbowlGuideButton, FishbowlGuideOverlay } from "../components/fishbowl/FishbowlGuide";

// ---------------------------------------------------------------------------
// Colours
// ---------------------------------------------------------------------------

const C = {
  cream: "#FEFCF6",
  warmWhite: "#FFFAF0",
  ink: "#2D2A24",
  inkMuted: "#8C8578",
  border: "#E8E2D6",
  sky: "#5B9BD5",
  sage: "#6B9B7B",
  gold: "#C5962B",
  rose: "#C88B93",
};

// ---------------------------------------------------------------------------
// Top bar (internal to Fishbowl)
// ---------------------------------------------------------------------------

function FishbowlTopBar({
  onToggleGuide,
  isReplay,
}: {
  onToggleGuide: () => void;
  isReplay: boolean;
}) {
  const { currentTick, latestTick, worldState, connectionStatus, isLive } = useSimulation();
  const agentCount = worldState?.agents.length ?? 0;

  // Replay mode: show tick progress. Live mode: show connection status.
  let statusColor: string;
  let statusLabel: string;

  if (isReplay) {
    statusColor = C.gold;
    statusLabel = `Simulation · tick ${currentTick} / ${latestTick}`;
  } else if (isLive) {
    statusColor = connectionStatus === "connected" ? C.sage
      : connectionStatus === "reconnecting" ? C.gold : C.rose;
    statusLabel = connectionStatus === "connected" ? "Live"
      : connectionStatus === "reconnecting" ? "Reconnecting..." : "Disconnected";
  } else {
    statusColor = C.sky;
    statusLabel = `Tick ${currentTick}`;
  }

  return (
    <header
      className="flex h-10 items-center justify-between border-b px-4"
      style={{ background: C.warmWhite, borderColor: C.border }}
    >
      {/* Left: Logo */}
      <Link
        to="/"
        className="text-sm font-semibold"
        style={{ fontFamily: "Lora, Georgia, serif", color: C.ink }}
      >
        AgentCiv
      </Link>

      {/* Centre: Stats */}
      <div className="flex items-center gap-4">
        <Stat label="Tick" value={String(currentTick)} />
        <Stat label="Agents" value={String(agentCount)} />
        <div className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ background: statusColor }}
            title={statusLabel}
          />
          <span className="text-[10px]" style={{ color: C.inkMuted }}>
            {statusLabel}
          </span>
        </div>
      </div>

      {/* Right: Guide + Back link */}
      <div className="flex items-center gap-3">
        <FishbowlGuideButton onClick={onToggleGuide} />
        <Link
          to="/"
          className="text-xs font-medium transition-colors hover:underline"
          style={{ color: C.sky }}
        >
          Back to site
        </Link>
      </div>
    </header>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[10px] font-medium uppercase tracking-wider" style={{ color: C.inkMuted }}>
        {label}
      </span>
      <span className="text-xs font-semibold tabular-nums" style={{ color: C.ink }}>
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page wrapper
// ---------------------------------------------------------------------------

function FishbowlInner({ isReplay }: { isReplay: boolean }) {
  const [showGuide, setShowGuide] = useState(() => {
    try {
      return !localStorage.getItem("fishbowl-guide-seen");
    } catch {
      return false;
    }
  });

  const closeGuide = () => {
    setShowGuide(false);
    try {
      localStorage.setItem("fishbowl-guide-seen", "1");
    } catch {
      // localStorage unavailable
    }
  };

  return (
    <div className="flex h-screen flex-col" style={{ background: C.cream }}>
      <FishbowlTopBar
        onToggleGuide={() => setShowGuide((v) => !v)}
        isReplay={isReplay}
      />
      <div className="relative flex-1 min-h-0">
        <FishbowlLayout />
        {showGuide && <FishbowlGuideOverlay onClose={closeGuide} />}
      </div>
    </div>
  );
}

export default function Fishbowl() {
  const [mode, setMode] = useState<"loading" | "replay" | "live">("loading");

  // Detect replay data on mount
  useEffect(() => {
    fetch("/replay_data/metadata.json", { method: "HEAD" })
      .then((r) => {
        setMode(r.ok ? "replay" : "live");
      })
      .catch(() => {
        setMode("live");
      });
  }, []);

  if (mode === "loading") {
    return (
      <div
        className="flex h-screen items-center justify-center"
        style={{ background: C.cream, color: C.inkMuted }}
      >
        <p className="text-sm">Loading fishbowl...</p>
      </div>
    );
  }

  if (mode === "replay") {
    return (
      <ReplayProvider>
        <FishbowlInner isReplay />
      </ReplayProvider>
    );
  }

  return (
    <SimulationProvider>
      <FishbowlInner isReplay={false} />
    </SimulationProvider>
  );
}
