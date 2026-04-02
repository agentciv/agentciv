import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";
import TableOfContents from "../components/common/TableOfContents";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AgentProfile {
  id: number;
  final_position: [number, number];
  final_wellbeing: number;
  final_maslow: number;
  specialisations: string[];
  structures_built: number;
  innovation_proposed: string | null;
  known_recipes: string[];
  relationship_count: number;
  bonded_count: number;
  total_interactions: number;
}

interface WbCurve {
  tick: number;
  mean: number;
  min: number;
  max: number;
}

interface PerAgentWb {
  tick: number;
  wellbeing: number;
}

interface SpecEntry {
  tick: number;
  specialisations: string[];
  spec_count: number;
  top_activity: string | null;
  top_count: number;
}

interface GovEvent {
  type: string;
  tick: number;
  agent: number;
  data: Record<string, unknown>;
}

interface RelEntry {
  interactions: number;
  positive: number;
  negative: number;
  bonded: boolean;
  last_tick: number;
}

interface RelData {
  [agentId: string]: RelEntry;
}

// ---------------------------------------------------------------------------
// Data hook
// ---------------------------------------------------------------------------

function useSimData() {
  const [profiles, setProfiles] = useState<Record<string, AgentProfile>>({});
  const [wellbeingAvg, setWellbeingAvg] = useState<WbCurve[]>([]);
  const [wellbeingPerAgent, setWellbeingPerAgent] = useState<Record<string, PerAgentWb[]>>({});
  const [specPerAgent, setSpecPerAgent] = useState<Record<string, SpecEntry[]>>({});
  const [governance, setGovernance] = useState<GovEvent[]>([]);
  const [relationships, setRelationships] = useState<Record<string, RelData>>({});
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/stats/agent_profiles.json").then((r) => r.json()),
      fetch("/stats/wellbeing_curves.json").then((r) => r.json()),
      fetch("/stats/specialisation_progression.json").then((r) => r.json()),
      fetch("/stats/governance_timeline.json").then((r) => r.json()),
      fetch("/stats/relationship_network.json").then((r) => r.json()),
    ]).then(([ap, wb, sp, gov, rel]) => {
      setProfiles(ap);
      setWellbeingAvg(wb.average);
      setWellbeingPerAgent(wb.per_agent);
      setSpecPerAgent(sp.per_agent);
      setGovernance(gov);
      setRelationships(rel);
      setLoaded(true);
    });
  }, []);

  return { profiles, wellbeingAvg, wellbeingPerAgent, specPerAgent, governance, relationships, loaded };
}

// ---------------------------------------------------------------------------
// Agent colours (consistent across charts)
// ---------------------------------------------------------------------------

const AGENT_COLORS = [
  "#5B9BD5", "#C5962B", "#6B9B7B", "#D4785A", "#C88B93", "#8B7355",
  "#7B68AE", "#5CAD8B", "#D4A05A", "#6A8CAD", "#B57E6E", "#7BAD7B",
];

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

function ChartTip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: number;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-warm-white px-3 py-2 shadow-sm text-xs">
      <p className="font-medium text-ink-muted">Tick {label}</p>
      {payload.slice(0, 4).map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(3) : p.value}
        </p>
      ))}
      {payload.length > 4 && (
        <p className="text-ink-muted">+{payload.length - 4} more</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Expandable
// ---------------------------------------------------------------------------

function Expandable({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-t border-border-light pt-4 mt-4">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-left text-sm font-semibold text-ink-light hover:text-ink transition-colors"
      >
        <span>{title}</span>
        <span className="ml-2 text-ink-muted transition-transform" style={{ transform: open ? "rotate(180deg)" : "rotate(0)" }}>
          &#9660;
        </span>
      </button>
      {open && <div className="mt-4">{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// TOC
// ---------------------------------------------------------------------------

const tocItems = [
  { id: "run-overview", label: "Run Overview" },
  { id: "agent-profiles", label: "Agent Profiles" },
  { id: "wellbeing-by-agent", label: "Wellbeing by Agent" },
  { id: "specialisation", label: "Specialisation" },
  { id: "governance", label: "Governance" },
  { id: "relationships", label: "Relationships" },
  { id: "raw-data", label: "Raw Data" },
];

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export default function Simulations() {
  const { profiles, wellbeingAvg, wellbeingPerAgent, specPerAgent, governance, relationships, loaded } =
    useSimData();

  // Build per-agent wellbeing chart data
  const agentWbChartData = useMemo(() => {
    if (!wellbeingPerAgent || Object.keys(wellbeingPerAgent).length === 0) return [];
    const agentKeys = Object.keys(wellbeingPerAgent).sort((a, b) => Number(a) - Number(b));
    const firstAgent = wellbeingPerAgent[agentKeys[0]];
    if (!firstAgent) return [];
    return firstAgent.map((_, i) => {
      const point: Record<string, number> = { tick: firstAgent[i].tick };
      for (const key of agentKeys) {
        const d = wellbeingPerAgent[key]?.[i];
        if (d) point[`a${key}`] = d.wellbeing ?? (d as unknown as Record<string, number>).mean ?? 0;
      }
      return point;
    });
  }, [wellbeingPerAgent]);

  // Relationship matrix for the final tick
  const relMatrix = useMemo(() => {
    const tick70 = relationships["70"];
    if (!tick70) return [];
    const agents = Object.keys(tick70).sort((a, b) => Number(a) - Number(b));
    const rows: Array<{ from: number; to: number; interactions: number; bonded: boolean }> = [];
    for (const from of agents) {
      for (const [to, data] of Object.entries(tick70[from]) as [string, RelEntry][]) {
        if (Number(from) < Number(to)) {
          rows.push({ from: Number(from), to: Number(to), interactions: data.interactions, bonded: data.bonded });
        }
      }
    }
    rows.sort((a, b) => b.interactions - a.interactions);
    return rows;
  }, [relationships]);

  const agentKeys = Object.keys(profiles).sort((a, b) => Number(a) - Number(b));

  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-4">Simulation Data</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            Complete data from the Civilisation Alpha run. 12 agents (Claude
            Sonnet), 70 ticks, 15x15 grid. Every metric, every agent profile,
            every relationship — all from real simulation data.
          </p>
        </Container>
      </Section>

      {/* Content */}
      <Section bg="cream" className="pt-0">
        <div className="mx-auto max-w-7xl px-6">
          <div className="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">
            <TableOfContents items={tocItems} />

            <div className="max-w-4xl pb-24">
              {/* ── Run overview ── */}
              <article id="run-overview" className="scroll-mt-24 pb-12">
                <h2 className="mb-6">Run Overview</h2>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                  {[
                    { v: "Civilisation Alpha", l: "Run Name" },
                    { v: "Claude Sonnet", l: "Model" },
                    { v: "12", l: "Agents" },
                    { v: "70", l: "Ticks" },
                    { v: "15 x 15", l: "Grid" },
                    { v: "60", l: "Structures" },
                    { v: "12", l: "Innovations" },
                    { v: "1,604", l: "Messages" },
                  ].map(({ v, l }) => (
                    <div key={l} className="rounded-lg border border-border bg-warm-white p-3 text-center">
                      <p className="text-lg font-bold text-ink">{v}</p>
                      <p className="text-xs text-ink-muted">{l}</p>
                    </div>
                  ))}
                </div>

                <Callout variant="sage">
                  <p className="text-sm text-ink">
                    <strong>Configuration:</strong> Maslow-inspired drives
                    (food, water, material needs), perception range 5, movement
                    speed 1.0, ReAct reasoning loop. Wellbeing ceiling removed
                    at tick 50 (the only intervention). No instructions given to
                    any agent.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* ── Agent profiles ── */}
              <article id="agent-profiles" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Agent Profiles</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Final state of each agent at tick 70. Every agent reached
                  Maslow level 8 (self-actualisation) and near-perfect
                  wellbeing, but each took a different path.
                </p>

                {loaded && (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {agentKeys.map((k) => {
                      const a = profiles[k];
                      return (
                        <div
                          key={k}
                          className="rounded-xl border border-border bg-warm-white p-4"
                        >
                          <div className="flex items-center gap-3 mb-3">
                            <div
                              className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold text-white"
                              style={{ backgroundColor: AGENT_COLORS[a.id % AGENT_COLORS.length] }}
                            >
                              {a.id}
                            </div>
                            <div>
                              <p className="font-semibold text-ink">Agent {a.id}</p>
                              <p className="text-xs text-ink-muted">
                                Wellbeing {a.final_wellbeing.toFixed(2)} · Maslow {a.final_maslow}
                              </p>
                            </div>
                          </div>
                          <div className="space-y-1.5 text-sm text-ink-light">
                            <p>
                              <span className="text-ink-muted">Structures:</span>{" "}
                              <span className="font-medium">{a.structures_built}</span>
                            </p>
                            {a.innovation_proposed && (
                              <p>
                                <span className="text-ink-muted">Innovation:</span>{" "}
                                <span className="font-medium">{a.innovation_proposed}</span>
                              </p>
                            )}
                            <p>
                              <span className="text-ink-muted">Specialisations:</span>{" "}
                              <span className="font-medium">
                                {a.specialisations.length > 0 ? a.specialisations.join(", ") : "none"}
                              </span>
                            </p>
                            <p>
                              <span className="text-ink-muted">Bonds:</span>{" "}
                              <span className="font-medium">
                                {a.bonded_count} bonded · {a.total_interactions} interactions
                              </span>
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Wellbeing by agent ── */}
              <article id="wellbeing-by-agent" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Wellbeing by Agent</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Each coloured line is one agent's wellbeing over 70 ticks.
                  Note the convergence in Era III — individual trajectories
                  merge as the civilisation stabilises.
                </p>

                {loaded && agentWbChartData.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4">
                    <ResponsiveContainer width="100%" height={360}>
                      <LineChart data={agentWbChartData} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Tick", position: "bottom", offset: 5, fontSize: 12, fill: "#8C8578" }}
                        />
                        <YAxis
                          domain={[0, 1.05]}
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                        />
                        <Tooltip content={<ChartTip />} />
                        <ReferenceLine x={50} stroke="#C5962B" strokeDasharray="4 4" strokeWidth={1.5} />
                        <ReferenceLine x={60} stroke="#6B9B7B" strokeDasharray="4 4" strokeWidth={1.5} />
                        {agentKeys.map((k) => (
                          <Line
                            key={k}
                            dataKey={`a${k}`}
                            stroke={AGENT_COLORS[Number(k) % AGENT_COLORS.length]}
                            strokeWidth={1.5}
                            dot={false}
                            name={`Agent ${k}`}
                            type="monotone"
                            strokeOpacity={0.7}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                    <div className="mt-3 flex flex-wrap justify-center gap-3">
                      {agentKeys.map((k) => (
                        <span key={k} className="flex items-center gap-1 text-xs text-ink-muted">
                          <span
                            className="inline-block h-2 w-2 rounded-full"
                            style={{ backgroundColor: AGENT_COLORS[Number(k) % AGENT_COLORS.length] }}
                          />
                          {k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Specialisation ── */}
              <article id="specialisation" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Specialisation</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Agents weren't assigned roles. Through repeated activity, they
                  developed specialisations — becoming experts in gathering,
                  building, communication, or movement. By tick 70, 11 of 12
                  agents had specialised in building.
                </p>

                {loaded && Object.keys(specPerAgent).length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-left text-ink-muted">
                          <th className="py-2 pr-3">Agent</th>
                          <th className="py-2 pr-3">Top Activity</th>
                          <th className="py-2 pr-3">Count</th>
                          <th className="py-2">All Specialisations</th>
                        </tr>
                      </thead>
                      <tbody>
                        {agentKeys.map((k) => {
                          const entries = specPerAgent[k];
                          const final = entries?.[entries.length - 1];
                          if (!final) return null;
                          return (
                            <tr key={k} className="border-b border-border-light">
                              <td className="py-2 pr-3">
                                <span className="flex items-center gap-2">
                                  <span
                                    className="inline-block h-2.5 w-2.5 rounded-full"
                                    style={{ backgroundColor: AGENT_COLORS[Number(k) % AGENT_COLORS.length] }}
                                  />
                                  <span className="font-medium text-ink">Agent {k}</span>
                                </span>
                              </td>
                              <td className="py-2 pr-3 text-ink-light">
                                {final.top_activity ?? "—"}
                              </td>
                              <td className="py-2 pr-3 font-mono text-xs text-ink-muted">
                                {final.top_count}
                              </td>
                              <td className="py-2 text-ink-light">
                                {final.specialisations.length > 0
                                  ? final.specialisations.join(", ")
                                  : "—"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Governance ── */}
              <article id="governance" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Governance</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  One collective rule was proposed, debated, and eventually
                  established — without any agent being told that governance was
                  possible. The rule emerged from Agent 0 at tick 21, 29 ticks
                  before it was formally established.
                </p>

                {loaded && governance.length > 0 && (
                  <div className="space-y-3">
                    {governance.map((ev, i) => (
                      <div
                        key={i}
                        className="flex gap-4 rounded-lg border border-border bg-warm-white p-4"
                      >
                        <div className="flex h-8 w-12 shrink-0 items-center justify-center rounded bg-parchment font-mono text-sm font-semibold text-ink-muted">
                          t{ev.tick}
                        </div>
                        <div>
                          <p className="font-semibold text-ink">
                            {ev.type === "rule_proposed" && "Rule Proposed"}
                            {ev.type === "rule_accepted" && "Rule Accepted"}
                            {ev.type === "rule_established" && "Rule Established"}
                            {!["rule_proposed", "rule_accepted", "rule_established"].includes(ev.type) && ev.type}
                            <span className="ml-2 text-sm font-normal text-ink-muted">
                              by Agent {ev.agent}
                            </span>
                          </p>
                          {ev.data.text != null && (
                            <p className="mt-1 text-sm italic text-ink-light">
                              &ldquo;{String(ev.data.text)}&rdquo;
                            </p>
                          )}
                          {ev.data.adoption_rate !== undefined && (
                            <p className="mt-1 text-sm text-ink-muted">
                              Adoption rate: {(Number(ev.data.adoption_rate) * 100).toFixed(0)}%
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Relationships ── */}
              <article id="relationships" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Relationships</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  By tick 70, agents had formed complex social networks through
                  unprompted interaction. Below are the strongest relationships
                  (by interaction count) at the end of the simulation. Zero
                  negative interactions were recorded across the entire run.
                </p>

                {loaded && relMatrix.length > 0 && (
                  <>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-border text-left text-ink-muted">
                            <th className="py-2 pr-3">Pair</th>
                            <th className="py-2 pr-3">Interactions</th>
                            <th className="py-2">Bonded</th>
                          </tr>
                        </thead>
                        <tbody>
                          {relMatrix.slice(0, 15).map((r, i) => (
                            <tr key={i} className="border-b border-border-light">
                              <td className="py-2 pr-3 font-medium text-ink">
                                <span className="flex items-center gap-1.5">
                                  <span
                                    className="inline-block h-2 w-2 rounded-full"
                                    style={{ backgroundColor: AGENT_COLORS[r.from] }}
                                  />
                                  {r.from}
                                  <span className="text-ink-muted">↔</span>
                                  <span
                                    className="inline-block h-2 w-2 rounded-full"
                                    style={{ backgroundColor: AGENT_COLORS[r.to] }}
                                  />
                                  {r.to}
                                </span>
                              </td>
                              <td className="py-2 pr-3 font-mono text-xs text-ink-light">
                                {r.interactions}
                              </td>
                              <td className="py-2">
                                {r.bonded ? (
                                  <span className="text-sage font-medium">Yes</span>
                                ) : (
                                  <span className="text-ink-muted">No</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <Expandable title={`View all ${relMatrix.length} relationships`}>
                      <div className="max-h-80 overflow-y-auto">
                        <table className="w-full text-sm">
                          <tbody>
                            {relMatrix.map((r, i) => (
                              <tr key={i} className="border-b border-border-light">
                                <td className="py-1.5 pr-3 text-ink">
                                  Agent {r.from} ↔ Agent {r.to}
                                </td>
                                <td className="py-1.5 pr-3 font-mono text-xs text-ink-muted">
                                  {r.interactions}
                                </td>
                                <td className="py-1.5 text-xs">
                                  {r.bonded ? "bonded" : ""}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Expandable>
                  </>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Raw data downloads ── */}
              <article id="raw-data" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Raw Data</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Full transparency — download any data file used to generate
                  this page and the Discovery charts. All JSON, all real.
                </p>

                <div className="grid gap-2 sm:grid-cols-2">
                  {[
                    { file: "wellbeing_curves.json", desc: "Per-agent wellbeing over 70 ticks" },
                    { file: "maslow_progression.json", desc: "Per-agent Maslow level trajectory" },
                    { file: "structure_growth.json", desc: "Cumulative structures per tick" },
                    { file: "communication_volume.json", desc: "Messages per tick + cumulative" },
                    { file: "innovation_timeline.json", desc: "All 12 innovations with details" },
                    { file: "agent_profiles.json", desc: "Final state of all 12 agents" },
                    { file: "specialisation_progression.json", desc: "Per-agent skill development" },
                    { file: "relationship_network.json", desc: "Social network at 8 timepoints" },
                    { file: "era_comparison.json", desc: "Metrics by era" },
                    { file: "governance_timeline.json", desc: "Rule proposals and adoption" },
                    { file: "milestones.json", desc: "58 recorded milestones" },
                    { file: "build_events.json", desc: "Every structure built" },
                    { file: "need_curves.json", desc: "Per-agent resource needs" },
                    { file: "action_distribution.json", desc: "Action type counts" },
                  ].map(({ file, desc }) => (
                    <a
                      key={file}
                      href={`/stats/${file}`}
                      download
                      className="flex items-center gap-3 rounded-lg border border-border bg-warm-white p-3 text-sm transition-colors hover:bg-parchment"
                    >
                      <span className="shrink-0 text-sky">&#x2B73;</span>
                      <div className="min-w-0">
                        <p className="font-mono text-xs font-medium text-ink truncate">{file}</p>
                        <p className="text-xs text-ink-muted">{desc}</p>
                      </div>
                    </a>
                  ))}
                </div>

                <div className="mt-6 rounded-lg border border-border bg-parchment p-4 text-sm text-ink-light">
                  <p className="font-medium text-ink mb-1">Want everything?</p>
                  <p>
                    The complete dataset — 71 snapshots, 22,648 bus events, 1,604
                    messages, 172 chronicle entries, 72 interview transcripts —
                    is available in the{" "}
                    <a
                      href="https://github.com/agentciv/agentciv"
                      className="font-medium text-sky underline"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      GitHub repository
                    </a>.
                  </p>
                </div>
              </article>

              {/* ── Navigation ── */}
              <div className="mt-4 flex flex-wrap gap-4 border-t border-border pt-8 text-sm">
                <Link
                  to="/fishbowl"
                  className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
                >
                  Watch the Replay
                </Link>
                <Link
                  to="/discovery"
                  className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
                >
                  Key Findings
                </Link>
                <Link
                  to="/interviews"
                  className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
                >
                  Interviews
                </Link>
              </div>
            </div>
          </div>
        </div>
      </Section>
    </>
  );
}
