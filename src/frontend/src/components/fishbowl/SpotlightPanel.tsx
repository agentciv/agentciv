/**
 * SpotlightPanel — curated "what's happening now" view.
 *
 * Derives interesting live data from worldState + feedEvents:
 * population stats, active conversations, agents in need, recent milestones.
 */

import { useSimulation } from "../../hooks/useSimulation";
import { BusEventType } from "../../types";

const C = {
  ink: "#2D2A24",
  inkLight: "#5C5648",
  inkMuted: "#8C8578",
  gold: "#C5962B",
  goldPale: "#FDF6E3",
  sage: "#6B9B7B",
  sagePale: "#E8F2EC",
  sky: "#5B9BD5",
  skyPale: "#E3F0FA",
  rose: "#C88B93",
  rosePale: "#F5E8EB",
  border: "#E8E2D6",
  warmWhite: "#FFFAF0",
  cream: "#FEFCF6",
};

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div
      className="rounded-lg px-2 py-1.5 text-center"
      style={{ background: C.cream, border: `1px solid ${C.border}` }}
    >
      <div className="text-sm font-semibold" style={{ color: color ?? C.ink }}>
        {value}
      </div>
      <div
        className="text-[9px] uppercase tracking-wider"
        style={{ color: C.inkMuted }}
      >
        {label}
      </div>
    </div>
  );
}

export default function SpotlightPanel() {
  const { worldState, feedEvents, selectAgent } = useSimulation();

  if (!worldState) {
    return (
      <div
        className="flex h-full items-center justify-center"
        style={{ background: C.warmWhite }}
      >
        <span className="text-sm" style={{ color: C.inkMuted }}>
          Waiting for world data...
        </span>
      </div>
    );
  }

  const agents = worldState.agents;
  const totalAgents = agents.length;
  const avgHealth =
    totalAgents > 0
      ? agents.reduce((s, a) => s + (1 - a.degradation_ratio), 0) /
        totalAgents
      : 0;
  const avgWellbeing =
    totalAgents > 0
      ? agents.reduce((s, a) => s + a.wellbeing, 0) / totalAgents
      : 0;
  const criticalAgents = agents.filter((a) => a.needs_critical);
  const communicating = agents.filter(
    (a) => a.current_action_type === "communicate",
  );
  const building = agents.filter((a) => a.current_action_type === "build");
  const specialized = agents.filter((a) => a.specialisations.length > 0);

  // Count structures
  let structureCount = 0;
  for (const row of worldState.tiles) {
    for (const tile of row) {
      structureCount += tile.structures.length;
    }
  }

  // Recent conversations from feed
  const recentConversations = feedEvents
    .filter((ev) => ev.type === BusEventType.MESSAGE_SENT)
    .slice(-5)
    .reverse();

  // Recent milestones from feed
  const recentMilestones = feedEvents
    .filter((ev) => ev.type === BusEventType.WATCHER_MILESTONE)
    .slice(-3)
    .reverse();

  return (
    <div
      className="flex h-full flex-col overflow-y-auto"
      style={{ background: C.warmWhite }}
    >
      <div className="space-y-3 px-3 py-2">
        {/* Population Overview */}
        <div>
          <h4
            className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
            style={{ color: C.inkMuted }}
          >
            Population
          </h4>
          <div className="grid grid-cols-3 gap-2">
            <StatCard label="Agents" value={totalAgents} />
            <StatCard
              label="Health"
              value={`${(avgHealth * 100).toFixed(0)}%`}
              color={avgHealth > 0.6 ? C.sage : C.rose}
            />
            <StatCard
              label="Social"
              value={`${(avgWellbeing * 100).toFixed(0)}%`}
              color={avgWellbeing > 0.5 ? C.sage : C.rose}
            />
          </div>
          <div className="mt-1.5 grid grid-cols-3 gap-2">
            <StatCard label="Structures" value={structureCount} />
            <StatCard label="Specialists" value={specialized.length} />
            <StatCard
              label="Critical"
              value={criticalAgents.length}
              color={criticalAgents.length > 0 ? C.rose : C.sage}
            />
          </div>
        </div>

        {/* Right Now */}
        {(communicating.length > 0 || building.length > 0) && (
          <div>
            <h4
              className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: C.inkMuted }}
            >
              Right Now
            </h4>
            {communicating.length > 0 && (
              <div
                className="mb-1 rounded-lg px-2.5 py-1.5"
                style={{ background: C.skyPale }}
              >
                <span className="text-xs" style={{ color: C.sky }}>
                  {"\uD83D\uDCAC"} {communicating.length} agent
                  {communicating.length > 1 ? "s" : ""} talking
                </span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {communicating.slice(0, 6).map((a) => (
                    <button
                      key={a.id}
                      onClick={() => selectAgent(a.id)}
                      className="rounded px-1.5 py-0.5 text-[10px] font-medium hover:underline"
                      style={{
                        color: C.sky,
                        background: "rgba(91, 155, 213, 0.1)",
                      }}
                    >
                      #{a.id}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {building.length > 0 && (
              <div
                className="rounded-lg px-2.5 py-1.5"
                style={{ background: C.goldPale }}
              >
                <span className="text-xs" style={{ color: C.gold }}>
                  {"\uD83D\uDD28"} {building.length} agent
                  {building.length > 1 ? "s" : ""} building
                </span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {building.slice(0, 6).map((a) => (
                    <button
                      key={a.id}
                      onClick={() => selectAgent(a.id)}
                      className="rounded px-1.5 py-0.5 text-[10px] font-medium hover:underline"
                      style={{
                        color: C.gold,
                        background: "rgba(197, 150, 43, 0.1)",
                      }}
                    >
                      #{a.id}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Needs Attention */}
        {criticalAgents.length > 0 && (
          <div>
            <h4
              className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: C.rose }}
            >
              Needs Attention
            </h4>
            {criticalAgents.slice(0, 4).map((a) => (
              <button
                key={a.id}
                onClick={() => selectAgent(a.id)}
                className="mb-1 w-full rounded-lg px-2.5 py-1.5 text-left transition-colors hover:shadow-sm"
                style={{ background: C.rosePale }}
              >
                <div className="flex items-center justify-between">
                  <span
                    className="text-xs font-medium"
                    style={{ color: C.rose }}
                  >
                    Agent {a.id}
                  </span>
                  <span className="text-[10px]" style={{ color: C.inkMuted }}>
                    Health{" "}
                    {((1 - a.degradation_ratio) * 100).toFixed(0)}%
                  </span>
                </div>
                {a.goals.length > 0 && (
                  <div
                    className="mt-0.5 truncate text-[10px]"
                    style={{ color: C.inkMuted }}
                  >
                    Goal: {a.goals[0]}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Recent Milestones */}
        {recentMilestones.length > 0 && (
          <div>
            <h4
              className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: C.gold }}
            >
              Milestones
            </h4>
            {recentMilestones.map((ev, i) => (
              <div
                key={i}
                className="mb-1 rounded-lg px-2.5 py-1.5"
                style={{
                  background: C.goldPale,
                  borderLeft: `2px solid ${C.gold}`,
                }}
              >
                <span
                  className="text-xs font-medium"
                  style={{ color: C.gold }}
                >
                  {(ev.data.name as string) ?? "Milestone"}
                </span>
                {typeof ev.data.commentary === "string" && (
                  <div
                    className="mt-0.5 text-[10px]"
                    style={{ color: C.inkMuted }}
                  >
                    {ev.data.commentary}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Recent Conversations */}
        {recentConversations.length > 0 && (
          <div>
            <h4
              className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: C.sky }}
            >
              Recent Messages
            </h4>
            {recentConversations.map((ev, i) => {
              const sender = ev.agent_id;
              const receiver = ev.data.receiver_id as number | undefined;
              const content =
                (ev.data.content as string) ??
                (ev.data.message as string) ??
                "";
              const truncated =
                content.length > 80 ? content.slice(0, 77) + "..." : content;
              return (
                <div
                  key={i}
                  className="mb-1 rounded-lg px-2.5 py-1.5"
                  style={{ background: C.skyPale }}
                >
                  <div
                    className="text-[10px] font-medium"
                    style={{ color: C.sky }}
                  >
                    <button
                      onClick={() => sender != null && selectAgent(sender)}
                      className="hover:underline"
                    >
                      Agent {sender}
                    </button>
                    {receiver != null && (
                      <>
                        {" \u2192 "}
                        <button
                          onClick={() => selectAgent(receiver)}
                          className="hover:underline"
                        >
                          Agent {receiver}
                        </button>
                      </>
                    )}
                  </div>
                  <div
                    className="mt-0.5 text-[10px] leading-relaxed"
                    style={{ color: C.inkLight }}
                  >
                    &ldquo;{truncated}&rdquo;
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Empty state */}
        {totalAgents === 0 && (
          <div
            className="py-8 text-center text-sm"
            style={{ color: C.inkMuted }}
          >
            Waiting for agents to appear...
          </div>
        )}
      </div>
    </div>
  );
}
