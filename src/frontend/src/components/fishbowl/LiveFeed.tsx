/**
 * LiveFeed — scrolling real-time event stream.
 *
 * Events arrive via the SimulationContext (populated by WebSocket).
 * Four visual categories: Reasoning, Conversations, Building, Chronicler.
 * Clicking an agent ID selects it on the canvas + opens Inspector.
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { useSimulation, type FeedEvent } from "../../hooks/useSimulation";
import { BusEventType } from "../../types";

// ---------------------------------------------------------------------------
// Event categorisation
// ---------------------------------------------------------------------------

type EventCategory = "reasoning" | "conversation" | "building" | "watcher";

function categorise(type: string): EventCategory {
  switch (type) {
    case BusEventType.REASONING_STEP:
    case BusEventType.GOAL_SET:
    case BusEventType.GOAL_COMPLETED:
    case BusEventType.PLAN_UPDATED:
    case BusEventType.ACTION_TAKEN:
    case BusEventType.OBSERVATION:
      return "reasoning";

    case BusEventType.MESSAGE_SENT:
    case BusEventType.MESSAGE_RECEIVED:
      return "conversation";

    case BusEventType.STRUCTURE_BUILT:
    case BusEventType.STRUCTURE_DISCOVERED:
    case BusEventType.COMPOSITION_DISCOVERED:
    case BusEventType.COMPOSITION_FAILED:
    case BusEventType.INNOVATION_SUCCEEDED:
    case BusEventType.INNOVATION_FAILED:
    case BusEventType.SPECIALISATION_GAINED:
    case BusEventType.RESOURCE_STORED:
    case BusEventType.RESOURCE_CONSUMED:
      return "building";

    case BusEventType.WATCHER_NARRATIVE:
    case BusEventType.WATCHER_MILESTONE:
    case BusEventType.WATCHER_TICK_REPORT:
      return "watcher";

    default:
      return "reasoning";
  }
}

const CATEGORY_STYLES: Record<
  EventCategory,
  { bg: string; icon: string; accent: string }
> = {
  reasoning: {
    bg: "bg-[#FEFCF6]",
    icon: "\uD83D\uDCAD", // thought bubble
    accent: "text-[#8C8578]",
  },
  conversation: {
    bg: "bg-[#E3F0FA]",
    icon: "\uD83D\uDCAC", // speech
    accent: "text-[#5B9BD5]",
  },
  building: {
    bg: "bg-[#FDF6E3]",
    icon: "\uD83D\uDD28", // hammer
    accent: "text-[#C5962B]",
  },
  watcher: {
    bg: "bg-[#E8F2EC]",
    icon: "\uD83D\uDCDC", // scroll
    accent: "text-[#6B9B7B]",
  },
};

// ---------------------------------------------------------------------------
// Format event into display text
// ---------------------------------------------------------------------------

function formatEvent(ev: FeedEvent): { primary: string; secondary?: string } {
  const d = ev.data;
  const agentPrefix = ev.agent_id != null ? `Agent ${ev.agent_id}` : "";

  switch (ev.type) {
    case BusEventType.REASONING_STEP: {
      // The agentic loop emits the agent's full inner monologue in data.response
      const thought = (d.response as string) ?? (d.summary as string) ?? (d.reasoning as string) ?? "thinking...";
      const truncatedThought = thought.length > 200 ? thought.slice(0, 197) + "..." : thought;
      return {
        primary: `${agentPrefix}: ${truncatedThought}`,
      };
    }
    case BusEventType.GOAL_SET:
      return { primary: `${agentPrefix} set goal: ${d.goal as string ?? ""}` };
    case BusEventType.GOAL_COMPLETED:
      return { primary: `${agentPrefix} completed goal: ${d.goal as string ?? ""}` };
    case BusEventType.PLAN_UPDATED:
      return { primary: `${agentPrefix} updated plan` };
    case BusEventType.ACTION_TAKEN:
      return {
        primary: `${agentPrefix}: ${(d.action as string) ?? (d.action_type as string) ?? "acted"}`,
        secondary: d.reasoning as string | undefined,
      };
    case BusEventType.OBSERVATION:
      return { primary: `${agentPrefix} observed: ${(d.observation as string) ?? (d.summary as string) ?? ""}` };

    case BusEventType.MESSAGE_SENT: {
      const receiver = d.receiver_id != null ? `Agent ${d.receiver_id}` : "all";
      const content = (d.content as string) ?? (d.message as string) ?? "";
      const truncated = content.length > 120 ? content.slice(0, 117) + "..." : content;
      return { primary: `${agentPrefix} \u2192 ${receiver}: ${truncated}` };
    }
    case BusEventType.MESSAGE_RECEIVED:
      return { primary: `${agentPrefix} received message` };

    case BusEventType.STRUCTURE_BUILT: {
      const stype = (d.structure_type as string) ?? "structure";
      const cname = d.custom_name as string | undefined;
      return {
        primary: `${agentPrefix} built ${cname ?? stype}`,
        secondary: d.custom_description as string | undefined,
      };
    }
    case BusEventType.COMPOSITION_DISCOVERED:
      return {
        primary: `${agentPrefix} discovered composition: ${(d.output_name as string) ?? "new recipe"}`,
      };
    case BusEventType.INNOVATION_SUCCEEDED:
      return {
        primary: `${agentPrefix} innovated: ${(d.name as string) ?? (d.custom_name as string) ?? "something new"}`,
        secondary: d.description as string | undefined,
      };
    case BusEventType.INNOVATION_FAILED:
      return { primary: `${agentPrefix} innovation attempt failed` };
    case BusEventType.SPECIALISATION_GAINED:
      return {
        primary: `${agentPrefix} specialised in ${(d.activity as string) ?? "an activity"}`,
      };

    case BusEventType.WATCHER_NARRATIVE:
      return { primary: (d.text as string) ?? (d.narrative as string) ?? "" };
    case BusEventType.WATCHER_MILESTONE:
      return {
        primary: `Milestone: ${(d.name as string) ?? ""}`,
        secondary: d.commentary as string | undefined,
      };

    default:
      return { primary: `${agentPrefix}: ${ev.type}` };
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LiveFeed() {
  const { feedEvents, selectAgent } = useSimulation();

  // Filter state
  const [filters, setFilters] = useState<Record<EventCategory, boolean>>({
    reasoning: true,
    conversation: true,
    building: true,
    watcher: true,
  });

  // Auto-scroll
  const scrollRef = useRef<HTMLDivElement>(null);
  const [userScrolledUp, setUserScrolledUp] = useState(false);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    setUserScrolledUp(!isAtBottom);
  }, []);

  // Auto-scroll to bottom when new events arrive (if not scrolled up)
  useEffect(() => {
    if (!userScrolledUp && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [feedEvents, userScrolledUp]);

  const scrollToLatest = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      setUserScrolledUp(false);
    }
  }, []);

  const toggleFilter = (cat: EventCategory) => {
    setFilters((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  // Filter events (hide tick_start/tick_end — they're infrastructure, not interesting)
  const filtered = feedEvents.filter((ev) => {
    if (ev.type === BusEventType.TICK_START || ev.type === BusEventType.TICK_END ||
        ev.type === "TICK_START" || ev.type === "TICK_END") return false;
    const cat = categorise(ev.type);
    return filters[cat];
  });

  const handleAgentClick = (agentId: number) => {
    selectAgent(agentId);
  };

  return (
    <div className="flex h-full flex-col" style={{ background: "#FFFAF0" }}>
      {/* Header + Filter toggles */}
      <div className="flex items-center gap-1.5 border-b px-3 py-2" style={{ borderColor: "#E8E2D6" }}>
        <span
          className="mr-2 text-xs font-semibold"
          style={{ color: "#2D2A24", fontFamily: "Lora, Georgia, serif" }}
        >
          Event Feed
        </span>
        <span className="mr-1 text-[10px] font-medium" style={{ color: "#8C8578" }}>
          Filter:
        </span>
        {(
          [
            ["reasoning", "Reasoning"],
            ["conversation", "Conversations"],
            ["building", "Building"],
            ["watcher", "Chronicler"],
          ] as [EventCategory, string][]
        ).map(([cat, label]) => (
          <button
            key={cat}
            onClick={() => toggleFilter(cat)}
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-all ${
              filters[cat]
                ? `${CATEGORY_STYLES[cat].bg} ${CATEGORY_STYLES[cat].accent} ring-1 ring-current/20`
                : "bg-transparent text-[#8C8578] opacity-50"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Event list */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-3 py-2"
      >
        {filtered.length === 0 && (
          <div className="py-8 text-center text-sm" style={{ color: "#8C8578" }}>
            Waiting for events...
          </div>
        )}
        {filtered.map((ev) => {
          const cat = categorise(ev.type);
          const style = CATEGORY_STYLES[cat];
          const { primary, secondary } = formatEvent(ev);
          const isMilestone = ev.type === BusEventType.WATCHER_MILESTONE;
          const isConversation = cat === "conversation";
          const isNotableBuilding =
            ev.type === BusEventType.STRUCTURE_BUILT ||
            ev.type === BusEventType.INNOVATION_SUCCEEDED ||
            ev.type === BusEventType.COMPOSITION_DISCOVERED;

          // --- Milestone: big prominent card ---
          if (isMilestone) {
            return (
              <div
                key={ev.feedId}
                className="mb-2 rounded-lg px-3 py-2.5 animate-[fadeIn_0.3s_ease]"
                style={{
                  background: "#FDF6E3",
                  borderLeft: "3px solid #C5962B",
                  boxShadow: "0 1px 3px rgba(197, 150, 43, 0.15)",
                }}
              >
                <div className="flex items-start gap-2">
                  <span className="mt-0.5 shrink-0 text-sm">{"\uD83C\uDFC6"}</span>
                  <div className="min-w-0 flex-1">
                    <span className="text-sm font-semibold" style={{ color: "#C5962B" }}>
                      <AgentIdLinks text={primary} onAgentClick={handleAgentClick} />
                    </span>
                    {secondary && (
                      <div className="mt-1 text-xs leading-relaxed" style={{ color: "#5C5648" }}>
                        {secondary}
                      </div>
                    )}
                  </div>
                  <span className="shrink-0 text-[10px] font-medium" style={{ color: "#C5962B" }}>
                    t{ev.tick}
                  </span>
                </div>
              </div>
            );
          }

          // --- Conversation: more prominent ---
          if (isConversation) {
            return (
              <div
                key={ev.feedId}
                className="mb-1.5 rounded-lg px-3 py-2 animate-[fadeIn_0.3s_ease]"
                style={{ background: "#E3F0FA" }}
              >
                <div className="flex items-start gap-1.5">
                  <span className="mt-0.5 shrink-0 text-xs">{"\uD83D\uDCAC"}</span>
                  <div className="min-w-0 flex-1">
                    <span className="text-xs font-medium" style={{ color: "#5B9BD5" }}>
                      <AgentIdLinks text={primary} onAgentClick={handleAgentClick} />
                    </span>
                    {secondary && (
                      <div className="mt-0.5 text-[11px]" style={{ color: "#8C8578" }}>
                        {secondary}
                      </div>
                    )}
                  </div>
                  <span className="shrink-0 text-[10px]" style={{ color: "#BBA88D" }}>
                    t{ev.tick}
                  </span>
                </div>
              </div>
            );
          }

          // --- Building / Innovation: medium prominence ---
          if (isNotableBuilding) {
            return (
              <div
                key={ev.feedId}
                className="mb-1.5 rounded-lg px-3 py-2 animate-[fadeIn_0.3s_ease]"
                style={{ background: "#FDF6E3", borderLeft: "2px solid #E8D59A" }}
              >
                <div className="flex items-start gap-1.5">
                  <span className="mt-0.5 shrink-0 text-xs">{style.icon}</span>
                  <div className="min-w-0 flex-1">
                    <span className="text-xs font-medium" style={{ color: "#C5962B" }}>
                      <AgentIdLinks text={primary} onAgentClick={handleAgentClick} />
                    </span>
                    {secondary && (
                      <div className="mt-0.5 text-[11px]" style={{ color: "#8C8578" }}>
                        {secondary}
                      </div>
                    )}
                  </div>
                  <span className="shrink-0 text-[10px]" style={{ color: "#BBA88D" }}>
                    t{ev.tick}
                  </span>
                </div>
              </div>
            );
          }

          // --- Default: reasoning / other (compact) ---
          return (
            <div
              key={ev.feedId}
              className={`mb-1 rounded-lg px-2.5 py-1 text-xs leading-relaxed animate-[fadeIn_0.3s_ease] ${style.bg}`}
            >
              <div className="flex items-start gap-1.5">
                <span className="mt-0.5 shrink-0 text-[10px]">{style.icon}</span>
                <div className="min-w-0 flex-1">
                  <span className="italic" style={{ color: "#8C8578" }}>
                    <AgentIdLinks text={primary} onAgentClick={handleAgentClick} />
                  </span>
                </div>
                <span className="shrink-0 text-[10px]" style={{ color: "#BBA88D" }}>
                  t{ev.tick}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Scroll-to-latest button */}
      {userScrolledUp && (
        <button
          onClick={scrollToLatest}
          className="absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full px-3 py-1 text-xs font-medium shadow-md transition-all hover:shadow-lg"
          style={{
            background: "#5B9BD5",
            color: "#fff",
          }}
        >
          Scroll to latest
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AgentIdLinks: makes "Agent 5" clickable
// ---------------------------------------------------------------------------

function AgentIdLinks({
  text,
  onAgentClick,
}: {
  text: string;
  onAgentClick: (id: number) => void;
}) {
  // Match "Agent N" patterns
  const parts = text.split(/(Agent \d+)/g);
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^Agent (\d+)$/);
        if (match) {
          const id = parseInt(match[1], 10);
          return (
            <button
              key={i}
              onClick={(e) => {
                e.stopPropagation();
                onAgentClick(id);
              }}
              className="font-semibold underline decoration-dotted underline-offset-2 hover:decoration-solid"
              style={{ color: "#5B9BD5" }}
            >
              Agent {id}
            </button>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
