/**
 * AgentInspector — detail panel for a selected agent.
 *
 * Shows: identity, needs bars, goals, plan, action, inventory,
 *        specialisations, and tabbed Memory / Interactions views.
 * Fetches full agent detail on selection and refreshes each tick.
 */

import { useState, useEffect, useCallback } from "react";
import { useSimulation } from "../../hooks/useSimulation";
import { fetchAgent, fetchAgentInteractions } from "../../api/client";
import type { AgentDetailResponse, InteractionListResponse } from "../../types";

// ---------------------------------------------------------------------------
// Colour helpers from design system
// ---------------------------------------------------------------------------

const C = {
  sage: "#6B9B7B",
  sageLight: "#A8CBB5",
  sagePale: "#E8F2EC",
  rose: "#C88B93",
  roseLight: "#E8C5CA",
  gold: "#C5962B",
  goldLight: "#E8D59A",
  goldPale: "#FDF6E3",
  sky: "#5B9BD5",
  skyLight: "#A8CDE8",
  skyPale: "#E3F0FA",
  earth: "#8B7355",
  earthLight: "#BBA88D",
  ink: "#2D2A24",
  inkLight: "#5C5648",
  inkMuted: "#8C8578",
  border: "#E8E2D6",
  warmWhite: "#FFFAF0",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AgentInspector() {
  const { selectedAgentId, currentTick, worldState, agentDetailProvider } = useSimulation();
  const [detail, setDetail] = useState<AgentDetailResponse | null>(null);
  const [interactions, setInteractions] = useState<InteractionListResponse | null>(null);
  const [tab, setTab] = useState<"memory" | "relationships" | "interactions">("memory");
  const [partnerFilter, setPartnerFilter] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);

  // Fetch agent detail when selected or tick changes
  useEffect(() => {
    if (selectedAgentId == null) {
      setDetail(null);
      setInteractions(null);
      return;
    }

    // In replay mode, use agentDetailProvider (no REST API available)
    if (agentDetailProvider) {
      const replayDetail = agentDetailProvider(selectedAgentId);
      if (replayDetail) {
        setDetail(replayDetail);
        setLoading(false);
        // No interaction data available in replay — clear it
        setInteractions(null);
        return;
      }
    }

    // Fallback: live mode — fetch from REST API
    setLoading(true);
    fetchAgent(selectedAgentId)
      .then((d) => {
        setDetail(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    fetchAgentInteractions(selectedAgentId, partnerFilter)
      .then(setInteractions)
      .catch(() => {});
  }, [selectedAgentId, currentTick, partnerFilter, agentDetailProvider]);

  if (selectedAgentId == null) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-6 text-center">
        <p
          className="mb-2 text-sm font-semibold"
          style={{ color: C.ink, fontFamily: "Lora, Georgia, serif" }}
        >
          Agent Inspector
        </p>
        <p className="text-xs leading-relaxed" style={{ color: C.inkMuted }}>
          Click any agent on the map to see their needs, goals, plan, memories, and conversations.
        </p>
      </div>
    );
  }

  if (loading && !detail) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm" style={{ color: C.inkMuted }}>Loading...</p>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm" style={{ color: C.inkMuted }}>Agent not found.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden" style={{ background: C.warmWhite }}>
      {/* Header */}
      <div className="border-b px-4 py-2.5" style={{ borderColor: C.border }}>
        <div className="flex items-center justify-between">
          <h4
            className="text-sm font-semibold"
            style={{ color: C.ink, fontFamily: "Lora, Georgia, serif" }}
          >
            Agent {detail.id}
          </h4>
          <div className="flex items-center gap-3 text-xs" style={{ color: C.inkMuted }}>
            <span>Age: {detail.age} ticks</span>
            <span>
              ({detail.position.x}, {detail.position.y})
            </span>
          </div>
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {/* Needs bars */}
        <Section title="Needs">
          {Object.entries(detail.needs.levels).map(([need, level]) => (
            <NeedBar key={need} label={need} value={level} />
          ))}
          <NeedBar label="Social Wellbeing" value={detail.wellbeing} />
          <NeedBar label="Curiosity" value={detail.curiosity} />
          <NeedBar
            label="Capability"
            value={1 - detail.degradation_ratio}
          />
        </Section>

        {/* Goals */}
        {detail.goals.length > 0 && (
          <Section title="Goals">
            <ul className="ml-3 list-disc text-xs leading-relaxed" style={{ color: C.inkLight }}>
              {detail.goals.map((g, i) => (
                <li key={i}>{g}</li>
              ))}
            </ul>
          </Section>
        )}

        {/* Plan */}
        {detail.plan.length > 0 && (
          <Section title="Plan">
            <ol className="ml-3 list-decimal text-xs leading-relaxed" style={{ color: C.inkLight }}>
              {detail.plan.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ol>
          </Section>
        )}

        {/* Current action */}
        {detail.current_action && (
          <Section title="Current Action">
            <div className="text-xs" style={{ color: C.inkLight }}>
              <span className="font-medium" style={{ color: C.ink }}>
                {detail.current_action.type}
              </span>
              {detail.current_action.reasoning && (
                <span className="ml-1">— {detail.current_action.reasoning}</span>
              )}
            </div>
          </Section>
        )}

        {/* Inventory */}
        {detail.inventory.length > 0 && (
          <Section title="Inventory">
            <div className="flex flex-wrap gap-1.5">
              {detail.inventory.map((item, i) => (
                <span
                  key={i}
                  className="rounded-full px-2 py-0.5 text-xs font-medium"
                  style={{
                    background: inventoryColor(item).bg,
                    color: inventoryColor(item).text,
                  }}
                >
                  {item}
                </span>
              ))}
            </div>
          </Section>
        )}

        {/* Specialisations */}
        <Section title="Specialisations">
          {detail.specialisations.length === 0 ? (
            <p className="text-xs" style={{ color: C.inkMuted }}>
              None yet
            </p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {detail.specialisations.map((spec) => {
                const count = detail.activity_counts[spec] ?? 0;
                return (
                  <div
                    key={spec}
                    className="flex items-center gap-1.5 rounded-full px-2 py-0.5"
                    style={{ background: C.sagePale }}
                  >
                    <span className="text-[10px]" style={{ color: C.gold }}>
                      ★
                    </span>
                    <span className="text-xs font-medium" style={{ color: C.sage }}>
                      {spec}
                    </span>
                    <span className="text-[10px]" style={{ color: C.inkMuted }}>
                      ({count})
                    </span>
                  </div>
                );
              })}
            </div>
          )}
          {/* Activity progress */}
          {Object.entries(detail.activity_counts).length > 0 && (
            <div className="mt-2 space-y-1">
              {Object.entries(detail.activity_counts)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 6)
                .map(([activity, count]) => {
                  const threshold = 10; // Default spec threshold
                  const pct = Math.min(count / threshold, 1);
                  const isAchieved = detail.specialisations.includes(activity);
                  return (
                    <div key={activity} className="flex items-center gap-2">
                      <span
                        className="w-20 truncate text-[10px]"
                        style={{ color: C.inkMuted }}
                      >
                        {activity}
                      </span>
                      <div
                        className="h-1.5 flex-1 overflow-hidden rounded-full"
                        style={{ background: C.border }}
                      >
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${pct * 100}%`,
                            background: isAchieved ? C.sage : C.earthLight,
                          }}
                        />
                      </div>
                      <span className="text-[10px]" style={{ color: C.inkMuted }}>
                        {count}
                      </span>
                    </div>
                  );
                })}
            </div>
          )}
        </Section>

        {/* Tabs: Memory / Interactions */}
        <div className="mt-3 border-t pt-2" style={{ borderColor: C.border }}>
          <div className="flex gap-1 mb-2">
            <TabButton active={tab === "memory"} onClick={() => setTab("memory")}>
              Memory
            </TabButton>
            <TabButton
              active={tab === "relationships"}
              onClick={() => setTab("relationships")}
            >
              Bonds
            </TabButton>
            <TabButton
              active={tab === "interactions"}
              onClick={() => setTab("interactions")}
            >
              Messages
            </TabButton>
          </div>

          {tab === "memory" && (
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {detail.memories.length === 0 ? (
                <p className="text-xs" style={{ color: C.inkMuted }}>
                  No memories yet.
                </p>
              ) : (
                [...detail.memories]
                  .sort((a, b) => b.tick - a.tick)
                  .map((m, i) => (
                    <div
                      key={i}
                      className="rounded px-2 py-1.5 text-xs"
                      style={{
                        background: C.warmWhite,
                        borderLeft: `${Math.max(2, Math.min(5, m.importance * 5))}px solid ${C.goldLight}`,
                        color: C.inkLight,
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <span>{m.summary}</span>
                        <span className="ml-2 shrink-0 text-[10px]" style={{ color: C.inkMuted }}>
                          t{m.tick}
                        </span>
                      </div>
                    </div>
                  ))
              )}
            </div>
          )}

          {tab === "relationships" && (
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {!detail.relationships || detail.relationships.length === 0 ? (
                <p className="text-xs" style={{ color: C.inkMuted }}>
                  No relationships formed yet.
                </p>
              ) : (
                [...detail.relationships]
                  .sort((a, b) => b.interaction_count - a.interaction_count)
                  .map((rel) => {
                    const sentiment =
                      rel.positive_count > rel.negative_count
                        ? "positive"
                        : rel.negative_count > 0
                          ? "strained"
                          : "neutral";
                    const sentimentColor =
                      sentiment === "positive"
                        ? C.sage
                        : sentiment === "strained"
                          ? C.rose
                          : C.inkMuted;
                    return (
                      <div
                        key={rel.agent_id}
                        className="rounded px-2 py-1.5 text-xs"
                        style={{
                          background: rel.is_bonded ? C.sagePale : C.warmWhite,
                          borderLeft: `3px solid ${rel.is_bonded ? C.sage : C.border}`,
                          color: C.inkLight,
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium" style={{ color: C.ink }}>
                            Agent {rel.agent_id}
                            {rel.is_bonded && (
                              <span
                                className="ml-1.5 text-[10px] font-semibold"
                                style={{ color: C.sage }}
                              >
                                BONDED
                              </span>
                            )}
                          </span>
                          <span className="text-[10px]" style={{ color: C.inkMuted }}>
                            last t{rel.last_interaction_tick}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-[10px]">
                          <span style={{ color: C.inkMuted }}>
                            {rel.interaction_count} interaction{rel.interaction_count !== 1 ? "s" : ""}
                          </span>
                          <span style={{ color: sentimentColor }}>
                            {sentiment}
                          </span>
                          <span style={{ color: C.inkMuted }}>
                            +{rel.positive_count} / -{rel.negative_count}
                          </span>
                        </div>
                      </div>
                    );
                  })
              )}
            </div>
          )}

          {tab === "interactions" && (
            <div>
              {/* Partner filter */}
              <div className="mb-2">
                <select
                  value={partnerFilter ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    setPartnerFilter(val ? parseInt(val, 10) : undefined);
                  }}
                  className="rounded border px-2 py-0.5 text-xs"
                  style={{
                    borderColor: C.border,
                    background: C.warmWhite,
                    color: C.inkLight,
                  }}
                >
                  <option value="">All agents</option>
                  {worldState?.agents
                    .filter((a) => a.id !== selectedAgentId)
                    .map((a) => (
                      <option key={a.id} value={a.id}>
                        Agent {a.id}
                      </option>
                    ))}
                </select>
              </div>

              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {!interactions || interactions.messages.length === 0 ? (
                  <p className="text-xs" style={{ color: C.inkMuted }}>
                    No interactions yet.
                  </p>
                ) : (
                  [...interactions.messages]
                    .sort((a, b) => b.tick - a.tick)
                    .map((msg, i) => {
                      const isSent = msg.sender_id === selectedAgentId;
                      return (
                        <div
                          key={i}
                          className="rounded px-2 py-1.5 text-xs"
                          style={{
                            background: isSent ? C.skyPale : C.warmWhite,
                            color: C.inkLight,
                          }}
                        >
                          <div className="flex items-center gap-1 text-[10px] font-medium" style={{ color: C.inkMuted }}>
                            <span>
                              {isSent
                                ? `\u2192 Agent ${msg.receiver_id}`
                                : `\u2190 Agent ${msg.sender_id}`}
                            </span>
                            <span className="ml-auto">t{msg.tick}</span>
                          </div>
                          <div className="mt-0.5">{msg.content}</div>
                        </div>
                      );
                    })
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-3">
      <h5
        className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
        style={{ color: C.inkMuted }}
      >
        {title}
      </h5>
      {children}
    </div>
  );
}

function NeedBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const pct = Math.max(0, Math.min(1, value)) * 100;

  // Smooth gradient: red (0) → amber (0.35) → gold (0.55) → green (1.0)
  let barColor: string;
  if (value >= 0.55) {
    // Green zone: sage green
    const t = (value - 0.55) / 0.45; // 0..1
    barColor = `rgb(${Math.round(180 - t * 73)}, ${Math.round(160 + t * (155 - 160))}, ${Math.round(60 + t * 63)})`;
  } else if (value >= 0.35) {
    // Amber zone: gold → amber
    const t = (value - 0.35) / 0.2;
    barColor = `rgb(${Math.round(210 - t * 30)}, ${Math.round(140 + t * 20)}, ${Math.round(40 + t * 20)})`;
  } else {
    // Red zone: rose → red
    const t = value / 0.35;
    barColor = `rgb(${Math.round(200 + (1 - t) * 20)}, ${Math.round(80 + t * 60)}, ${Math.round(70 + t * (40 - 70))})`;
  }

  return (
    <div className="mb-1 flex items-center gap-2">
      <span
        className="w-24 truncate text-right text-[10px] font-medium capitalize"
        style={{ color: "#8C8578" }}
      >
        {label}
      </span>
      <div
        className="h-2 flex-1 overflow-hidden rounded-full"
        style={{ background: "#E8E2D6" }}
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: barColor,
          }}
        />
      </div>
      <span className="w-8 text-right text-[10px]" style={{ color: "#8C8578" }}>
        {Math.round(pct)}%
      </span>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
        active
          ? "shadow-sm"
          : "hover:bg-[#F3EDE0]"
      }`}
      style={{
        background: active ? C.warmWhite : "transparent",
        color: active ? C.ink : C.inkMuted,
        border: active ? `1px solid ${C.border}` : "1px solid transparent",
      }}
    >
      {children}
    </button>
  );
}

function inventoryColor(item: string): { bg: string; text: string } {
  const s = item.toLowerCase();
  if (s.includes("water")) return { bg: C.skyPale, text: C.sky };
  if (s.includes("food")) return { bg: C.goldPale, text: C.gold };
  return { bg: "#F3EDE0", text: C.earth };
}
