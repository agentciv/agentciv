/**
 * FishbowlLayout — three-area panel layout for the fishbowl page.
 *
 * ┌──────────────────────────┬──────────────────┐
 * │                          │   Live Feed      │
 * │   World Canvas           │   (~55% height)  │
 * │   (~65% width)           │                  │
 * │                          ├──────────────────┤
 * │                          │Insp|Spot |Chron  │
 * │                          │   (~45% height)  │
 * └──────────────────────────┴──────────────────┘
 *          Timeline Scrubber (full width bar)
 *
 * On mobile, the right panel collapses and is toggled via a button.
 * Milestone celebrations overlay the canvas when triggered.
 */

import { useState, useEffect, useRef } from "react";
import WorldCanvas from "./WorldCanvas";
import LiveFeed from "./LiveFeed";
import AgentInspector from "./AgentInspector";
import Chronicle from "./Chronicle";
import SpotlightPanel from "./SpotlightPanel";
import TimelineScrubber from "./TimelineScrubber";
import { useSimulation } from "../../hooks/useSimulation";
import { BusEventType } from "../../types";

// ---------------------------------------------------------------------------
// Colours
// ---------------------------------------------------------------------------

const C = {
  warmWhite: "#FFFAF0",
  border: "#E8E2D6",
  ink: "#2D2A24",
  inkMuted: "#8C8578",
  sky: "#5B9BD5",
  gold: "#C5962B",
};

type BottomTab = "inspector" | "spotlight" | "chronicle";

export default function FishbowlLayout() {
  const { selectedAgentId, feedEvents } = useSimulation();
  const [bottomTab, setBottomTab] = useState<BottomTab>("spotlight");
  const [mobilePanel, setMobilePanel] = useState(false);

  // ----- Milestone celebration overlay ------------------------------------
  const [activeMilestone, setActiveMilestone] = useState<{
    name: string;
    commentary: string;
    tick: number;
  } | null>(null);
  const lastMilestoneLenRef = useRef(0);
  const milestoneTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (feedEvents.length <= lastMilestoneLenRef.current) {
      lastMilestoneLenRef.current = feedEvents.length;
      return;
    }
    const newEvents = feedEvents.slice(lastMilestoneLenRef.current);
    lastMilestoneLenRef.current = feedEvents.length;

    for (const ev of newEvents) {
      if (ev.type === BusEventType.WATCHER_MILESTONE) {
        setActiveMilestone({
          name: (ev.data.name as string) ?? "Milestone",
          commentary: (ev.data.commentary as string) ?? "",
          tick: ev.tick,
        });
        // Clear any existing timer
        if (milestoneTimerRef.current) clearTimeout(milestoneTimerRef.current);
        milestoneTimerRef.current = setTimeout(
          () => setActiveMilestone(null),
          8000,
        );
      }
    }
  }, [feedEvents]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (milestoneTimerRef.current) clearTimeout(milestoneTimerRef.current);
    };
  }, []);

  // Auto-switch to inspector when agent is first selected
  const prevSelectedRef = useRef<number | null>(null);
  useEffect(() => {
    if (selectedAgentId != null && prevSelectedRef.current !== selectedAgentId) {
      setBottomTab("inspector");
    }
    prevSelectedRef.current = selectedAgentId;
  }, [selectedAgentId]);

  const effectiveTab = bottomTab;

  const tabs: { key: BottomTab; label: string }[] = [
    { key: "inspector", label: "Inspector" },
    { key: "spotlight", label: "Spotlight" },
    { key: "chronicle", label: "Chronicle" },
  ];

  return (
    <div className="flex h-full flex-col">
      {/* Main area */}
      <div className="flex min-h-0 flex-1">
        {/* Left: World Canvas */}
        <div
          className="relative min-w-0 flex-[65]"
          style={{ minHeight: 0 }}
        >
          <WorldCanvas />

          {/* Milestone celebration overlay */}
          {activeMilestone && (
            <div
              className="pointer-events-auto absolute inset-0 z-20 flex items-center justify-center"
              style={{ background: "rgba(45, 42, 36, 0.25)" }}
            >
              <div
                className="rounded-xl px-8 py-6 text-center shadow-xl"
                style={{
                  background: "linear-gradient(135deg, #FDF6E3, #FFFAF0)",
                  border: `2px solid ${C.gold}`,
                  maxWidth: "420px",
                  animation: "milestoneIn 0.4s ease",
                }}
              >
                <div className="mb-2 text-3xl">{"\uD83C\uDFC6"}</div>
                <h3
                  className="mb-2 text-lg font-bold"
                  style={{
                    color: C.gold,
                    fontFamily: "Lora, Georgia, serif",
                  }}
                >
                  {activeMilestone.name}
                </h3>
                {activeMilestone.commentary && (
                  <p
                    className="mb-3 text-sm leading-relaxed"
                    style={{ color: "#5C5648" }}
                  >
                    {activeMilestone.commentary}
                  </p>
                )}
                <div className="text-xs" style={{ color: C.inkMuted }}>
                  Tick {activeMilestone.tick}
                </div>
                <button
                  onClick={() => setActiveMilestone(null)}
                  className="mt-3 rounded-full px-4 py-1 text-xs font-medium transition-colors hover:bg-[#E8E2D6]"
                  style={{ color: C.inkMuted }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Mobile toggle button */}
          <button
            onClick={() => setMobilePanel((p) => !p)}
            className="absolute bottom-3 right-3 z-10 rounded-full px-3 py-1.5 text-xs font-semibold shadow-lg md:hidden"
            style={{
              background: C.sky,
              color: "#fff",
            }}
          >
            {mobilePanel ? "Map" : "Panels"}
          </button>
        </div>

        {/* Right: Feed + Inspector/Spotlight/Chronicle */}
        <div
          className={`flex flex-col border-l ${
            mobilePanel
              ? "absolute inset-0 z-20 md:relative md:inset-auto md:z-auto"
              : "hidden md:flex"
          }`}
          style={{
            borderColor: C.border,
            background: C.warmWhite,
            flex: "0 0 35%",
            maxWidth: "480px",
            minWidth: "280px",
          }}
        >
          {/* Mobile close button */}
          {mobilePanel && (
            <button
              onClick={() => setMobilePanel(false)}
              className="absolute right-2 top-2 z-30 rounded-full p-1 md:hidden"
              style={{ background: C.warmWhite, color: C.inkMuted }}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M6 6l8 8M14 6l-8 8" />
              </svg>
            </button>
          )}

          {/* Live Feed (top ~55%) */}
          <div className="relative min-h-0 flex-[55] overflow-hidden">
            <LiveFeed />
          </div>

          {/* Tab bar */}
          <div
            className="flex border-y"
            style={{ borderColor: C.border }}
          >
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setBottomTab(tab.key)}
                className={`flex-1 px-3 py-1.5 text-xs font-medium transition-all ${
                  effectiveTab === tab.key
                    ? "font-semibold"
                    : "opacity-60 hover:opacity-90"
                }`}
                style={{
                  color:
                    effectiveTab === tab.key ? C.ink : C.inkMuted,
                  background:
                    effectiveTab === tab.key ? C.warmWhite : "transparent",
                  borderBottom:
                    effectiveTab === tab.key
                      ? `2px solid ${C.sky}`
                      : "2px solid transparent",
                }}
              >
                {tab.label}
                {tab.key === "inspector" && selectedAgentId != null && (
                  <span className="ml-1 text-[10px] opacity-60">
                    #{selectedAgentId}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Bottom panel (~45%) */}
          <div className="min-h-0 flex-[45] overflow-hidden">
            {effectiveTab === "inspector" ? (
              <AgentInspector />
            ) : effectiveTab === "spotlight" ? (
              <SpotlightPanel />
            ) : (
              <Chronicle />
            )}
          </div>
        </div>
      </div>

      {/* Timeline Scrubber (full width) */}
      <TimelineScrubber />

      {/* Milestone keyframes */}
      <style>{`
        @keyframes milestoneIn {
          0% { transform: scale(0.85); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
