import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";
import TableOfContents from "../components/common/TableOfContents";

// ---------------------------------------------------------------------------
// Types for our stats data
// ---------------------------------------------------------------------------

interface WellbeingPoint {
  tick: number;
  mean: number;
  min: number;
  max: number;
}

interface StructurePoint {
  tick: number;
  total: number;
  new: number;
}

interface CommPoint {
  tick: number;
  count: number;
  cumulative: number;
  unique_pairs: number;
}

interface MaslowPoint {
  tick: number;
  mean: number;
  min: number;
  max: number;
}

interface Innovation {
  name: string;
  description: string;
  discovered_by: number;
  discovered_tick: number;
  times_built: number;
  effect_type: string;
  inputs: string[];
}

interface EraData {
  ticks: string;
  duration: number;
  structures_start: number;
  structures_end: number;
  structures_delta: number;
  recipes_start: number;
  recipes_end: number;
  recipes_delta: number;
  wellbeing_start_mean: number;
  wellbeing_end_mean: number;
  maslow_start_mean: number;
  maslow_end_mean: number;
}

interface Milestone {
  tick: number;
  name: string;
  commentary: string;
}

// ---------------------------------------------------------------------------
// Data loading hook
// ---------------------------------------------------------------------------

function useStatsData() {
  const [wellbeing, setWellbeing] = useState<WellbeingPoint[]>([]);
  const [structures, setStructures] = useState<StructurePoint[]>([]);
  const [communication, setCommunication] = useState<CommPoint[]>([]);
  const [maslow, setMaslow] = useState<MaslowPoint[]>([]);
  const [innovations, setInnovations] = useState<Innovation[]>([]);
  const [eras, setEras] = useState<Record<string, EraData>>({});
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/stats/wellbeing_curves.json").then((r) => r.json()),
      fetch("/stats/structure_growth.json").then((r) => r.json()),
      fetch("/stats/communication_volume.json").then((r) => r.json()),
      fetch("/stats/maslow_progression.json").then((r) => r.json()),
      fetch("/stats/innovation_timeline.json").then((r) => r.json()),
      fetch("/stats/era_comparison.json").then((r) => r.json()),
      fetch("/stats/milestones.json").then((r) => r.json()),
    ]).then(([wb, sg, cv, mp, it, ec, ms]) => {
      setWellbeing(wb.average);
      setStructures(sg);
      setCommunication(cv);
      setMaslow(mp.average);
      setInnovations(it.innovations);
      setEras(ec);
      setMilestones(ms);
      setLoaded(true);
    });
  }, []);

  return { wellbeing, structures, communication, maslow, innovations, eras, milestones, loaded };
}

// ---------------------------------------------------------------------------
// Custom tooltip
// ---------------------------------------------------------------------------

function ChartTooltip({
  active,
  payload,
  label,
  formatter,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
  label?: number;
  formatter?: (v: number) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-warm-white px-3 py-2 shadow-sm">
      <p className="text-xs font-medium text-ink-muted">Tick {label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-sm font-semibold" style={{ color: p.color }}>
          {p.name}: {formatter ? formatter(p.value) : p.value}
        </p>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Era shading component (reusable across charts)
// ---------------------------------------------------------------------------

function EraShading() {
  return (
    <>
      <ReferenceArea x1={0} x2={50} fill="#C5962B" fillOpacity={0.06} />
      <ReferenceArea x1={50} x2={60} fill="#5B9BD5" fillOpacity={0.08} />
      <ReferenceArea x1={60} x2={70} fill="#6B9B7B" fillOpacity={0.08} />
      <ReferenceLine x={50} stroke="#C5962B" strokeDasharray="4 4" strokeWidth={1.5} />
      <ReferenceLine x={60} stroke="#6B9B7B" strokeDasharray="4 4" strokeWidth={1.5} />
    </>
  );
}

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

function StatCard({ value, label, sub }: { value: string; label: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-border bg-warm-white p-5 text-center">
      <p className="text-3xl font-bold text-ink">{value}</p>
      <p className="mt-1 text-sm font-medium text-ink-light">{label}</p>
      {sub && <p className="mt-0.5 text-xs text-ink-muted">{sub}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Expandable section
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
// Table of contents items
// ---------------------------------------------------------------------------

const tocItems = [
  { id: "overview", label: "Overview" },
  { id: "three-eras", label: "Three Eras" },
  { id: "wellbeing", label: "Wellbeing Journey" },
  { id: "innovation", label: "Innovation" },
  { id: "maslow", label: "Maslow Emergence" },
  { id: "communication", label: "Communication" },
  { id: "structures", label: "Building" },
  { id: "key-moments", label: "Key Moments" },
  { id: "implications", label: "Implications" },
];

// ---------------------------------------------------------------------------
// Era label
// ---------------------------------------------------------------------------

const eraLabels = [
  { range: "0-50", name: "Era I: Survival Trap", color: "#C5962B" },
  { range: "50-60", name: "Era II: Emergence Explosion", color: "#5B9BD5" },
  { range: "60-70", name: "Era III: Sustained Flourishing", color: "#6B9B7B" },
];

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function SimDiscovery() {
  const { wellbeing, structures, communication, maslow, innovations, eras, milestones, loaded } =
    useStatsData();

  const era1 = eras.era1_survival_trap;
  const era2 = eras.era2_emergence_explosion;
  const era3 = eras.era3_sustained_flourishing;

  return (
    <>
      {/* ── Hero ── */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-4">Key Findings</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            What happened when 12 LLM agents were placed in a world with basic
            needs, zero instructions, and no knowledge of each other? Every chart
            below is generated from real simulation data — 70 ticks, 22,648
            events, 1,604 messages.
          </p>
        </Container>
      </Section>

      {/* ── Main content ── */}
      <Section bg="cream" className="pt-0">
        <div className="mx-auto max-w-7xl px-6">
          <div className="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">
            <TableOfContents items={tocItems} />

            <div className="max-w-3xl pb-24">
              {/* ── Headline stats ── */}
              <article id="overview" className="scroll-mt-24 pb-12">
                <h2 className="mb-6">The Headline</h2>
                <p className="mb-8 leading-relaxed text-ink-light">
                  Twelve agents with Maslow-inspired drives — physiological needs
                  (food, water, material), safety, belonging, esteem, and
                  self-actualisation — were placed in a 15x15 resource grid. No
                  agent was told what to do, who the others were, or that building
                  was even possible. What emerged was a civilisation.
                </p>

                {loaded && (
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    <StatCard value="60" label="Structures Built" sub="from zero" />
                    <StatCard value="12" label="Innovations" sub="agent-invented" />
                    <StatCard
                      value="0.998"
                      label="Final Wellbeing"
                      sub="from 0.500"
                    />
                    <StatCard value="1,604" label="Messages" sub="unprompted" />
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Three eras ── */}
              <article id="three-eras" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Three Eras Emerged Naturally</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Without any external scripting, the simulation divided into
                  three distinct phases — each with qualitatively different
                  behaviour. The transitions were not programmed; they emerged
                  from the agents' collective decisions.
                </p>

                <div className="space-y-4">
                  {eraLabels.map(({ range, name, color }) => (
                    <div
                      key={range}
                      className="flex items-start gap-4 rounded-lg border border-border bg-warm-white p-4"
                    >
                      <div
                        className="mt-1 h-3 w-3 shrink-0 rounded-full"
                        style={{ backgroundColor: color }}
                      />
                      <div>
                        <p className="font-semibold text-ink">{name}</p>
                        <p className="text-sm text-ink-muted">Ticks {range}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {loaded && era1 && era2 && era3 && (
                  <Expandable title="Era comparison data">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-border text-left text-ink-muted">
                            <th className="py-2 pr-4">Metric</th>
                            <th className="py-2 pr-4">Era I (50 ticks)</th>
                            <th className="py-2 pr-4">Era II (10 ticks)</th>
                            <th className="py-2">Era III (10 ticks)</th>
                          </tr>
                        </thead>
                        <tbody className="text-ink-light">
                          <tr className="border-b border-border-light">
                            <td className="py-2 pr-4 font-medium text-ink">Structures built</td>
                            <td className="py-2 pr-4">{era1.structures_delta}</td>
                            <td className="py-2 pr-4">{era2.structures_delta}</td>
                            <td className="py-2">{era3.structures_delta}</td>
                          </tr>
                          <tr className="border-b border-border-light">
                            <td className="py-2 pr-4 font-medium text-ink">Build rate</td>
                            <td className="py-2 pr-4">{(era1.structures_delta / era1.duration).toFixed(2)}/tick</td>
                            <td className="py-2 pr-4">{(era2.structures_delta / era2.duration).toFixed(2)}/tick</td>
                            <td className="py-2">{(era3.structures_delta / era3.duration).toFixed(2)}/tick</td>
                          </tr>
                          <tr className="border-b border-border-light">
                            <td className="py-2 pr-4 font-medium text-ink">Wellbeing</td>
                            <td className="py-2 pr-4">{era1.wellbeing_start_mean.toFixed(2)} → {era1.wellbeing_end_mean.toFixed(2)}</td>
                            <td className="py-2 pr-4">{era2.wellbeing_start_mean.toFixed(2)} → {era2.wellbeing_end_mean.toFixed(2)}</td>
                            <td className="py-2">{era3.wellbeing_start_mean.toFixed(2)} → {era3.wellbeing_end_mean.toFixed(2)}</td>
                          </tr>
                          <tr className="border-b border-border-light">
                            <td className="py-2 pr-4 font-medium text-ink">Innovations</td>
                            <td className="py-2 pr-4">{era1.recipes_delta}</td>
                            <td className="py-2 pr-4">{era2.recipes_delta}</td>
                            <td className="py-2">{era3.recipes_delta}</td>
                          </tr>
                          <tr>
                            <td className="py-2 pr-4 font-medium text-ink">Maslow level</td>
                            <td className="py-2 pr-4">{era1.maslow_start_mean} → {era1.maslow_end_mean}</td>
                            <td className="py-2 pr-4">{era2.maslow_start_mean} → {era2.maslow_end_mean}</td>
                            <td className="py-2">{era3.maslow_start_mean} → {era3.maslow_end_mean}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </Expandable>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Wellbeing journey ── */}
              <article id="wellbeing" className="scroll-mt-24 py-12">
                <h2 className="mb-4">The Wellbeing Journey</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Every agent started at 0.500 wellbeing. By tick 70, the
                  population mean reached 0.998. But the path wasn't linear — it
                  oscillated as agents struggled, cooperated, built, and
                  eventually flourished. The shaded band shows the min-max range
                  across all 12 agents.
                </p>

                {loaded && wellbeing.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4">
                    <ResponsiveContainer width="100%" height={320}>
                      <AreaChart data={wellbeing} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Tick", position: "bottom", offset: 5, fontSize: 12, fill: "#8C8578" }}
                        />
                        <YAxis
                          domain={[0, 1.05]}
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Wellbeing", angle: -90, position: "insideLeft", offset: 0, fontSize: 12, fill: "#8C8578" }}
                        />
                        <Tooltip content={<ChartTooltip formatter={(v) => v.toFixed(3)} />} />
                        <EraShading />
                        <Area
                          dataKey="max"
                          stroke="none"
                          fill="#5B9BD5"
                          fillOpacity={0.15}
                          name="Max"
                        />
                        <Area
                          dataKey="min"
                          stroke="none"
                          fill="#FEFCF6"
                          fillOpacity={1}
                          name="Min"
                        />
                        <Line
                          dataKey="mean"
                          stroke="#5B9BD5"
                          strokeWidth={2.5}
                          dot={false}
                          name="Mean"
                          type="monotone"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                    <div className="mt-2 flex flex-wrap justify-center gap-6 text-xs text-ink-muted">
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-0.5 w-4 rounded bg-sky" /> Mean wellbeing
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-3 w-4 rounded bg-sky/15" /> Min-max range
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-0.5 w-4 border-t border-dashed border-gold" /> Era boundary
                      </span>
                    </div>
                  </div>
                )}

                <Callout variant="sage">
                  <p className="font-medium text-ink">
                    By Era III, every single agent had wellbeing above 0.97. The
                    gap between the weakest and strongest member of the
                    civilisation essentially closed.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* ── Innovation ── */}
              <article id="innovation" className="scroll-mt-24 py-12">
                <h2 className="mb-4">The Innovation-Implementation Gap</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  One of the most striking findings: 11 of 12 innovations were
                  discovered during Era I (ticks 0-50), when agents were still
                  struggling. But the building explosion didn't happen until Era
                  II (ticks 50-60), after a capability upgrade. The agents had
                  the ideas — they just couldn't execute them yet.
                </p>

                {loaded && innovations.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4">
                    <div className="space-y-2">
                      {innovations.map((inn, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-cream"
                        >
                          <div className="mt-1 flex h-6 w-10 shrink-0 items-center justify-center rounded bg-parchment text-xs font-mono font-semibold text-ink-muted">
                            t{inn.discovered_tick}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-ink">{inn.name}</p>
                            <p className="text-sm text-ink-muted truncate">
                              {inn.description}
                            </p>
                          </div>
                          <div className="shrink-0 text-right">
                            <p className="text-xs text-ink-muted">
                              Agent {inn.discovered_by}
                            </p>
                            <p className="text-xs font-medium" style={{ color: inn.times_built > 0 ? "#6B9B7B" : "#C88B93" }}>
                              {inn.times_built > 0 ? `Built ${inn.times_built}x` : "Never built"}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Callout variant="gold">
                  <p className="font-medium text-ink">
                    The agents invented things like Knowledge Hubs, Memory
                    Gardens, and Resource Exchanges — social infrastructure
                    concepts they were never told about. 6 of 12 innovations were
                    never built, suggesting the agents' creativity outpaced their
                    capacity.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* ── Maslow emergence ── */}
              <article id="maslow" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Maslow Emergence</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Agents had Maslow-inspired drives but were not told to climb a
                  hierarchy. Yet the population's mean Maslow level rose from 1.0
                  (physiological) to 8.0 (self-actualisation). By Era III, every
                  agent had reached the highest level — a complete traversal of
                  the hierarchy that took human societies millennia, compressed
                  into 70 ticks.
                </p>

                {loaded && maslow.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4">
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={maslow} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Tick", position: "bottom", offset: 5, fontSize: 12, fill: "#8C8578" }}
                        />
                        <YAxis
                          domain={[0, 9]}
                          ticks={[1, 2, 3, 4, 5, 6, 7, 8]}
                          tick={{ fontSize: 10, fill: "#8C8578" }}
                          label={{ value: "Maslow Level", angle: -90, position: "insideLeft", offset: 0, fontSize: 12, fill: "#8C8578" }}
                        />
                        <Tooltip content={<ChartTooltip formatter={(v) => v.toFixed(1)} />} />
                        <EraShading />
                        <Area
                          dataKey="max"
                          stroke="none"
                          fill="#C5962B"
                          fillOpacity={0.15}
                          name="Max"
                        />
                        <Area
                          dataKey="min"
                          stroke="none"
                          fill="#FEFCF6"
                          fillOpacity={1}
                          name="Min"
                        />
                        <Line
                          dataKey="mean"
                          stroke="#C5962B"
                          strokeWidth={2.5}
                          dot={false}
                          name="Mean"
                          type="monotone"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                    <div className="mt-2 flex flex-wrap justify-center gap-6 text-xs text-ink-muted">
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-0.5 w-4 rounded bg-gold" /> Mean Maslow level
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-3 w-4 rounded bg-gold/15" /> Min-max range
                      </span>
                    </div>
                  </div>
                )}

                <Expandable title="What are the Maslow levels?">
                  <div className="space-y-1.5 text-sm text-ink-light">
                    <p><span className="font-medium text-ink">1-2:</span> Physiological — securing food, water, material</p>
                    <p><span className="font-medium text-ink">3-4:</span> Safety — stable resource access, shelter</p>
                    <p><span className="font-medium text-ink">5-6:</span> Belonging — relationships, communication, community</p>
                    <p><span className="font-medium text-ink">7:</span> Esteem — specialisation, contribution, recognition</p>
                    <p><span className="font-medium text-ink">8:</span> Self-actualisation — innovation, mentoring, governance</p>
                  </div>
                </Expandable>
              </article>

              <div className="border-t border-border" />

              {/* ── Communication ── */}
              <article id="communication" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Communication Patterns</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  No agent was told to communicate. Yet they exchanged 1,604
                  messages across 70 ticks. Communication volume increased as the
                  civilisation grew more complex, peaking during the emergence
                  explosion — then dropping in Era III as agents became
                  self-sufficient and no longer needed to coordinate as intensely.
                </p>

                {loaded && communication.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4">
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={communication} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Tick", position: "bottom", offset: 5, fontSize: 12, fill: "#8C8578" }}
                        />
                        <YAxis
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Messages", angle: -90, position: "insideLeft", offset: 0, fontSize: 12, fill: "#8C8578" }}
                        />
                        <Tooltip content={<ChartTooltip />} />
                        <EraShading />
                        <Bar dataKey="count" fill="#5B9BD5" fillOpacity={0.7} name="Messages" radius={[2, 2, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Structures ── */}
              <article id="structures" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Building a Civilisation</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Structure count grew from 0 to 60 across 70 ticks. The growth
                  wasn't linear — it accelerated. Era I produced 41 structures in
                  50 ticks (0.82/tick). Era II produced 12 in 10 ticks
                  (1.20/tick). The agents were building faster as they became more
                  capable and organised.
                </p>

                {loaded && structures.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4">
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={structures} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Tick", position: "bottom", offset: 5, fontSize: 12, fill: "#8C8578" }}
                        />
                        <YAxis
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Total Structures", angle: -90, position: "insideLeft", offset: 0, fontSize: 12, fill: "#8C8578" }}
                        />
                        <Tooltip content={<ChartTooltip />} />
                        <EraShading />
                        <Area
                          dataKey="total"
                          stroke="#6B9B7B"
                          strokeWidth={2.5}
                          fill="#6B9B7B"
                          fillOpacity={0.15}
                          name="Structures"
                          type="monotone"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {loaded && era1 && era2 && era3 && (
                  <div className="mt-6 grid grid-cols-3 gap-3 text-center text-sm">
                    <div className="rounded-lg border border-border bg-warm-white p-3">
                      <p className="text-lg font-bold text-gold">{(era1.structures_delta / era1.duration).toFixed(2)}</p>
                      <p className="text-xs text-ink-muted">structures/tick (Era I)</p>
                    </div>
                    <div className="rounded-lg border border-border bg-warm-white p-3">
                      <p className="text-lg font-bold text-sky">{(era2.structures_delta / era2.duration).toFixed(2)}</p>
                      <p className="text-xs text-ink-muted">structures/tick (Era II)</p>
                    </div>
                    <div className="rounded-lg border border-border bg-warm-white p-3">
                      <p className="text-lg font-bold text-sage">{(era3.structures_delta / era3.duration).toFixed(2)}</p>
                      <p className="text-xs text-ink-muted">structures/tick (Era III)</p>
                    </div>
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Key moments ── */}
              <article id="key-moments" className="scroll-mt-24 py-12">
                <h2 className="mb-4">Key Moments</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  58 milestones were recorded by the simulation's observer system.
                  Here are the most significant:
                </p>

                {loaded && milestones.length > 0 && (
                  <>
                    <div className="space-y-3">
                      {milestones
                        .filter(
                          (m) =>
                            m.name === "First Contact" && m.tick === 0 ||
                            m.name === "First Structure" ||
                            m.name === "First Innovation" ||
                            m.name === "First Specialisation" ||
                            m.name === "First Collective Rule" ||
                            m.name === "Division of Labour" ||
                            m.name === "Innovation Wave"
                        )
                        .slice(0, 10)
                        .map((m, i) => (
                          <div
                            key={i}
                            className="flex gap-4 rounded-lg border border-border bg-warm-white p-4"
                          >
                            <div className="flex h-8 w-12 shrink-0 items-center justify-center rounded bg-parchment font-mono text-sm font-semibold text-ink-muted">
                              t{m.tick}
                            </div>
                            <div>
                              <p className="font-semibold text-ink">{m.name}</p>
                              <p className="mt-0.5 text-sm text-ink-light">{m.commentary}</p>
                            </div>
                          </div>
                        ))}
                    </div>
                    <Expandable title={`View all ${milestones.length} milestones`}>
                      <div className="max-h-96 space-y-2 overflow-y-auto pr-2">
                        {milestones.map((m, i) => (
                          <div
                            key={i}
                            className="flex gap-3 rounded px-2 py-1.5 text-sm hover:bg-parchment"
                          >
                            <span className="shrink-0 font-mono text-xs text-ink-muted w-8 text-right">
                              t{m.tick}
                            </span>
                            <span className="font-medium text-ink">{m.name}</span>
                            <span className="text-ink-muted truncate">
                              {m.commentary}
                            </span>
                          </div>
                        ))}
                      </div>
                    </Expandable>
                  </>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ── Implications ── */}
              <article id="implications" className="scroll-mt-24 py-12">
                <h2 className="mb-4">What This Suggests</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  These findings come from a single simulation run (n=1) with 12
                  agents over 70 ticks. We don't claim generalisability. But the
                  patterns are suggestive:
                </p>
                <ul className="mb-8 space-y-3 text-ink-light">
                  <li className="flex gap-3 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      <strong className="text-ink">Civilisation may be a natural attractor.</strong>{" "}
                      Given drives, constraints, and the ability to communicate,
                      agents converge on cooperation, specialisation, and
                      institution-building without being told to.
                    </span>
                  </li>
                  <li className="flex gap-3 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      <strong className="text-ink">Innovation precedes implementation.</strong>{" "}
                      The agents had ideas they couldn't execute — suggesting
                      creativity doesn't require capability, but implementation
                      does.
                    </span>
                  </li>
                  <li className="flex gap-3 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      <strong className="text-ink">Need hierarchies emerge from dynamics.</strong>{" "}
                      Maslow's hierarchy wasn't programmed as a goal — it was an
                      emergent property of agents pursuing basic drives in a
                      social environment.
                    </span>
                  </li>
                  <li className="flex gap-3 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      <strong className="text-ink">Capability upgrades have nonlinear effects.</strong>{" "}
                      A modest upgrade at tick 50 (removing a wellbeing ceiling)
                      triggered an explosion in building, wellbeing, and
                      cooperation — not because agents got new abilities, but
                      because constraints were relaxed.
                    </span>
                  </li>
                </ul>

                <Callout variant="sky">
                  <p className="font-medium text-ink">
                    This is one run with one model. The real power of this
                    approach lies in running hundreds of variations — different
                    agent counts, different constraints, different models — and
                    finding what's universal versus contingent. The{" "}
                    <Link to="/open-source" className="underline">
                      code is open source
                    </Link>{" "}
                    so anyone can do exactly that.
                  </p>
                </Callout>
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
                  to="/simulations"
                  className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
                >
                  Full Data
                </Link>
                <Link
                  to="/methodology"
                  className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
                >
                  Methodology
                </Link>
                <Link
                  to="/whitepaper"
                  className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
                >
                  Read the Paper
                </Link>
              </div>
            </div>
          </div>
        </div>
      </Section>
    </>
  );
}
