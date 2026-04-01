/**
 * Chronicle — historical record of milestones, narratives, and ethical flags.
 *
 * Sits in the bottom-right panel alongside AgentInspector (tabbed).
 * Fetches from /api/chronicle/milestones and /api/chronicle/narratives.
 */

import { useState, useEffect } from "react";
import { fetchMilestones, fetchNarratives } from "../../api/client";
import { useSimulation } from "../../hooks/useSimulation";
import type { MilestoneSchema, NarrativeSchema } from "../../types";
import { BusEventType } from "../../types";

// ---------------------------------------------------------------------------
// Colours
// ---------------------------------------------------------------------------

const C = {
  ink: "#2D2A24",
  inkLight: "#5C5648",
  inkMuted: "#8C8578",
  gold: "#C5962B",
  goldLight: "#E8D59A",
  goldPale: "#FDF6E3",
  sage: "#6B9B7B",
  sagePale: "#E8F2EC",
  rose: "#C88B93",
  rosePale: "#F5E8EB",
  sky: "#5B9BD5",
  border: "#E8E2D6",
  warmWhite: "#FFFAF0",
};

type FilterType = "all" | "milestones" | "narratives" | "flags";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Chronicle() {
  const { currentTick, feedEvents } = useSimulation();
  const [milestones, setMilestones] = useState<MilestoneSchema[]>([]);
  const [narratives, setNarratives] = useState<NarrativeSchema[]>([]);
  const [filter, setFilter] = useState<FilterType>("all");
  const [expandedNarrative, setExpandedNarrative] = useState<number | null>(null);

  // Fetch from REST API (works in live mode, silently fails in replay)
  useEffect(() => {
    fetchMilestones()
      .then((res) => setMilestones(res.milestones))
      .catch(() => {});
    fetchNarratives()
      .then((res) => setNarratives(res.narratives))
      .catch(() => {});
  }, [currentTick]);

  // Extract milestones from feed events (works in replay mode)
  const feedMilestones = feedEvents
    .filter((ev) => ev.type === BusEventType.WATCHER_MILESTONE)
    .map((ev) => ({
      tick: ev.tick,
      name: (ev.data.name as string) ?? "Milestone",
      commentary: (ev.data.commentary as string) ?? "",
    }));

  // Merge: REST milestones + feed milestones (deduplicate by tick+name)
  const allMilestones = (() => {
    const seen = new Set<string>();
    const result: MilestoneSchema[] = [];
    for (const m of [...milestones, ...feedMilestones]) {
      const key = `${m.tick}:${m.name}`;
      if (!seen.has(key)) {
        seen.add(key);
        result.push(m);
      }
    }
    return result;
  })();

  // Extract tick reports from feed
  const tickReports = feedEvents
    .filter((ev) => ev.type === BusEventType.WATCHER_TICK_REPORT)
    .map((ev) => ({
      tick: ev.tick,
      data: ev.data as Record<string, unknown>,
    }));

  // Detect ethical flags
  const ethicalFlags = [
    ...allMilestones
      .filter(
        (m) =>
          m.name.toLowerCase().includes("ethic") ||
          m.commentary.toLowerCase().includes("ethic") ||
          m.name.toLowerCase().includes("conflict") ||
          m.name.toLowerCase().includes("violation"),
      )
      .map((m) => ({ type: "milestone" as const, tick: m.tick, text: `${m.name}: ${m.commentary}` })),
    ...narratives
      .filter(
        (n) =>
          n.text.toLowerCase().includes("ethic") ||
          n.text.toLowerCase().includes("conflict") ||
          n.text.toLowerCase().includes("harm"),
      )
      .map((n) => ({ type: "narrative" as const, tick: n.tick, text: n.text })),
  ];

  const showMilestones = filter === "all" || filter === "milestones";
  const showNarratives = filter === "all" || filter === "narratives";
  const showFlags = filter === "all" || filter === "flags";

  return (
    <div className="flex h-full flex-col" style={{ background: C.warmWhite }}>
      {/* Filter bar */}
      <div
        className="flex items-center gap-1.5 border-b px-3 py-2"
        style={{ borderColor: C.border }}
      >
        {(
          [
            ["all", "All"],
            ["milestones", "Milestones"],
            ["narratives", "Narratives"],
            ["flags", "Flags"],
          ] as [FilterType, string][]
        ).map(([f, label]) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-all ${
              filter === f
                ? "shadow-sm ring-1 ring-current/20"
                : "opacity-50 hover:opacity-80"
            }`}
            style={{
              background:
                filter === f
                  ? f === "flags"
                    ? C.rosePale
                    : f === "milestones"
                      ? C.goldPale
                      : f === "narratives"
                        ? C.sagePale
                        : C.warmWhite
                  : "transparent",
              color:
                f === "flags"
                  ? C.rose
                  : f === "milestones"
                    ? C.gold
                    : f === "narratives"
                      ? C.sage
                      : C.inkMuted,
            }}
          >
            {label}
            {f === "flags" && ethicalFlags.length > 0 && (
              <span className="ml-1 text-[10px]">({ethicalFlags.length})</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        {/* Milestones */}
        {showMilestones &&
          allMilestones.length > 0 &&
          [...allMilestones]
            .sort((a, b) => a.tick - b.tick)
            .map((m, i) => (
              <div
                key={`m-${i}`}
                className="rounded-lg px-3 py-2"
                style={{
                  background: C.goldPale,
                  borderLeft: `3px solid ${C.gold}`,
                }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs" style={{ color: C.gold }}>
                    &#9670;
                  </span>
                  <span
                    className="text-xs font-semibold"
                    style={{ color: C.ink }}
                  >
                    {m.name}
                  </span>
                  <span
                    className="ml-auto text-[10px]"
                    style={{ color: C.inkMuted }}
                  >
                    tick {m.tick}
                  </span>
                </div>
                {m.commentary && (
                  <p className="mt-1 text-xs leading-relaxed" style={{ color: C.inkLight }}>
                    {m.commentary}
                  </p>
                )}
              </div>
            ))}

        {/* Narratives */}
        {showNarratives &&
          narratives.length > 0 &&
          [...narratives]
            .sort((a, b) => b.tick - a.tick)
            .map((n, i) => {
              const isExpanded = expandedNarrative === i;
              const isLong = n.text.length > 200;
              const displayText =
                isLong && !isExpanded ? n.text.slice(0, 197) + "..." : n.text;

              return (
                <div
                  key={`n-${i}`}
                  className="rounded-lg px-3 py-2 cursor-pointer transition-all hover:shadow-sm"
                  style={{
                    background: C.sagePale,
                    borderLeft: `3px solid ${C.sage}`,
                  }}
                  onClick={() =>
                    setExpandedNarrative(isExpanded ? null : i)
                  }
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-medium uppercase tracking-wider" style={{ color: C.sage }}>
                      Narrative
                    </span>
                    <span className="text-[10px]" style={{ color: C.inkMuted }}>
                      tick {n.tick}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: C.inkLight }}>
                    {displayText}
                  </p>
                  {isLong && (
                    <button
                      className="mt-1 text-[10px] font-medium"
                      style={{ color: C.sage }}
                    >
                      {isExpanded ? "Show less" : "Read more"}
                    </button>
                  )}
                </div>
              );
            })}

        {/* Ethical flags */}
        {showFlags &&
          ethicalFlags.length > 0 &&
          ethicalFlags.map((flag, i) => (
            <div
              key={`f-${i}`}
              className="rounded-lg px-3 py-2"
              style={{
                background: C.rosePale,
                borderLeft: `3px solid ${C.rose}`,
              }}
            >
              <div className="flex items-center justify-between mb-1">
                <span
                  className="text-[10px] font-medium uppercase tracking-wider"
                  style={{ color: C.rose }}
                >
                  Ethical Flag
                </span>
                <span className="text-[10px]" style={{ color: C.inkMuted }}>
                  tick {flag.tick}
                </span>
              </div>
              <p className="text-xs leading-relaxed" style={{ color: C.inkLight }}>
                {flag.text}
              </p>
            </div>
          ))}

        {/* Tick Reports (compact per-tick summaries) */}
        {(filter === "all" || filter === "narratives") &&
          tickReports.length > 0 &&
          [...tickReports]
            .sort((a, b) => b.tick - a.tick)
            .slice(0, 20)
            .map((tr, i) => {
              const d = tr.data;
              const pop = (d.population as Record<string, number>) ?? {};
              const comm = (d.communication as Record<string, number>) ?? {};
              const struct = (d.structures as Record<string, number>) ?? {};
              return (
                <div
                  key={`tr-${i}`}
                  className="rounded-lg px-3 py-1.5 text-xs"
                  style={{
                    background: C.warmWhite,
                    borderLeft: `2px solid ${C.border}`,
                    color: C.inkLight,
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span>
                      {pop.total ?? "?"} agents
                      {(comm.messages_sent ?? 0) > 0 && ` · ${comm.messages_sent} messages`}
                      {(struct.total ?? 0) > 0 && ` · ${struct.total} structures`}
                    </span>
                    <span className="text-[10px]" style={{ color: C.inkMuted }}>
                      tick {tr.tick}
                    </span>
                  </div>
                </div>
              );
            })}

        {/* Empty states */}
        {allMilestones.length === 0 && narratives.length === 0 && tickReports.length === 0 && (
          <div className="py-8 text-center text-sm" style={{ color: C.inkMuted }}>
            The Chronicler is observing. Entries will appear as the civilisation develops.
          </div>
        )}
      </div>
    </div>
  );
}
