/**
 * TimelineScrubber — thin horizontal bar at the bottom of the fishbowl.
 *
 * Shows: tick range, draggable handle, milestone markers, LIVE indicator.
 * Dragging to a historical tick fetches that state. "LIVE" returns to real-time.
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { useSimulation } from "../../hooks/useSimulation";
import { fetchMilestones } from "../../api/client";
import type { MilestoneSchema } from "../../types";

// ---------------------------------------------------------------------------
// Colours
// ---------------------------------------------------------------------------

const C = {
  ink: "#2D2A24",
  inkMuted: "#8C8578",
  gold: "#C5962B",
  goldLight: "#E8D59A",
  sage: "#6B9B7B",
  sky: "#5B9BD5",
  border: "#E8E2D6",
  warmWhite: "#FFFAF0",
  cream: "#FEFCF6",
};

export default function TimelineScrubber() {
  const { currentTick, latestTick, isLive, seekToTick, goLive, playing, togglePlayPause } = useSimulation();
  const trackRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const [hoverTick, setHoverTick] = useState<number | null>(null);
  const [milestones, setMilestones] = useState<MilestoneSchema[]>([]);

  // Fetch milestones for markers
  useEffect(() => {
    fetchMilestones()
      .then((res) => setMilestones(res.milestones))
      .catch(() => {});
  }, [latestTick]);

  const maxTick = Math.max(latestTick, 1);
  const progress = maxTick > 0 ? currentTick / maxTick : 0;

  // Convert pixel position to tick
  const posToTick = useCallback(
    (clientX: number) => {
      const track = trackRef.current;
      if (!track) return 0;
      const rect = track.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      return Math.round(ratio * maxTick);
    },
    [maxTick],
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      setDragging(true);
      const tick = posToTick(e.clientX);
      if (tick !== currentTick) {
        seekToTick(tick);
      }
    },
    [posToTick, currentTick, seekToTick],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const tick = posToTick(e.clientX);
      setHoverTick(tick);
      if (dragging) {
        seekToTick(tick);
      }
    },
    [dragging, posToTick, seekToTick],
  );

  const handleMouseUp = useCallback(() => {
    setDragging(false);
  }, []);

  // Global mouse up to stop dragging
  useEffect(() => {
    if (!dragging) return;
    const onUp = () => setDragging(false);
    window.addEventListener("mouseup", onUp);
    return () => window.removeEventListener("mouseup", onUp);
  }, [dragging]);

  return (
    <div
      className="flex h-10 items-center gap-3 border-t px-4"
      style={{ background: C.warmWhite, borderColor: C.border }}
    >
      {/* Play/Pause (replay mode only) */}
      {togglePlayPause && (
        <button
          onClick={togglePlayPause}
          className="flex shrink-0 items-center justify-center rounded-md transition-colors hover:bg-[#F3EDE0]"
          style={{ width: 28, height: 28, color: C.ink }}
          aria-label={playing ? "Pause" : "Play"}
          title={playing ? "Pause" : "Play"}
        >
          {playing ? (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
              <rect x="2" y="1" width="4" height="12" rx="1" />
              <rect x="8" y="1" width="4" height="12" rx="1" />
            </svg>
          ) : (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
              <path d="M3 1.5v11l9-5.5L3 1.5z" />
            </svg>
          )}
        </button>
      )}

      {/* Tick 1 label */}
      <span className="shrink-0 text-[10px] font-medium tabular-nums" style={{ color: C.inkMuted }}>
        Tick 1
      </span>

      {/* Track */}
      <div
        ref={trackRef}
        className="relative flex-1 select-none"
        style={{ height: 20 }}
      >
        {/* Track background */}
        <div
          className="absolute top-1/2 left-0 right-0 -translate-y-1/2 rounded-full"
          style={{ height: 4, background: C.border }}
        />

        {/* Filled portion */}
        <div
          className="absolute top-1/2 left-0 -translate-y-1/2 rounded-full transition-[width] duration-200"
          style={{
            height: 4,
            width: `${progress * 100}%`,
            background: isLive ? C.sage : C.sky,
          }}
        />

        {/* Milestone markers */}
        {milestones.map((m, i) => {
          const mPos = maxTick > 0 ? (m.tick / maxTick) * 100 : 0;
          return (
            <div
              key={i}
              className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full"
              style={{
                left: `${mPos}%`,
                width: 6,
                height: 6,
                background: C.gold,
                border: `1px solid ${C.goldLight}`,
              }}
              title={`${m.name} (tick ${m.tick})`}
            />
          );
        })}

        {/* Handle */}
        <div
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-sm transition-[left] duration-200"
          style={{
            left: `${progress * 100}%`,
            width: 14,
            height: 14,
            background: isLive ? C.sage : C.sky,
            border: `2px solid ${C.warmWhite}`,
          }}
        />

        {/* Hover tooltip */}
        {hoverTick != null && !dragging && (
          <div
            className="absolute -top-6 -translate-x-1/2 rounded px-1.5 py-0.5 text-[10px] font-medium shadow-sm"
            style={{
              left: `${(hoverTick / maxTick) * 100}%`,
              background: C.warmWhite,
              color: C.inkMuted,
              border: `1px solid ${C.border}`,
            }}
          >
            tick {hoverTick}
          </div>
        )}
      </div>

      {/* Current tick label */}
      <span className="shrink-0 text-[10px] font-medium tabular-nums" style={{ color: C.inkMuted }}>
        Tick {latestTick}
      </span>

      {/* LIVE button */}
      <button
        onClick={goLive}
        className={`flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all ${
          isLive
            ? "shadow-sm"
            : "opacity-70 hover:opacity-100"
        }`}
        style={{
          background: isLive ? C.sage : "transparent",
          color: isLive ? "#fff" : C.sage,
          border: isLive ? "none" : `1px solid ${C.sage}`,
        }}
      >
        {/* Pulsing green dot */}
        <span
          className={`inline-block h-2 w-2 rounded-full ${isLive ? "animate-pulse" : ""}`}
          style={{
            background: isLive ? "#86EFAC" : C.inkMuted,
          }}
        />
        {isLive ? "LIVE" : "LATEST"}
      </button>
    </div>
  );
}
