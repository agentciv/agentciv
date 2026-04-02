import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Legend,
} from "recharts";
import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";
import TableOfContents from "../components/common/TableOfContents";

// ---------------------------------------------------------------------------
// Types
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

interface InnovationData {
  innovations: Innovation[];
}

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------

function useJourneyData() {
  const [wellbeing, setWellbeing] = useState<WellbeingPoint[]>([]);
  const [structures, setStructures] = useState<StructurePoint[]>([]);
  const [maslow, setMaslow] = useState<MaslowPoint[]>([]);
  const [innovations, setInnovations] = useState<Innovation[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/stats/wellbeing_curves.json").then((r) => r.json()),
      fetch("/stats/structure_growth.json").then((r) => r.json()),
      fetch("/stats/maslow_progression.json").then((r) => r.json()),
      fetch("/stats/innovation_timeline.json").then((r) => r.json()),
    ]).then(([wb, sg, mp, it]: [{ average: WellbeingPoint[] }, StructurePoint[], { average: MaslowPoint[] }, InnovationData]) => {
      setWellbeing(wb.average);
      setStructures(sg);
      setMaslow(mp.average);
      setInnovations(it.innovations);
      setLoaded(true);
    });
  }, []);

  return { wellbeing, structures, maslow, innovations, loaded };
}

// ---------------------------------------------------------------------------
// Shared chart helpers
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

function EraLegend() {
  return (
    <div className="mt-2 flex flex-wrap justify-center gap-6 text-xs text-ink-muted">
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "#C5962B", opacity: 0.4 }} />
        Era I: Survival Trap (0–50)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "#5B9BD5", opacity: 0.5 }} />
        Era II: Emergence Explosion (50–60)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: "#6B9B7B", opacity: 0.5 }} />
        Era III: Flourishing (60–70)
      </span>
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
        <span
          className="ml-2 text-ink-muted transition-transform"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0)" }}
        >
          &#9660;
        </span>
      </button>
      {open && <div className="mt-4">{children}</div>}
    </div>
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
// Table of contents
// ---------------------------------------------------------------------------

const tocItems = [
  { id: "overview", label: "Overview" },
  { id: "the-experiments", label: "The Experiments" },
  { id: "control-vs-treatment", label: "Control vs Treatment" },
  { id: "inside-the-run", label: "Inside the Run" },
  { id: "what-agents-told-us", label: "What the Agents Told Us" },
  { id: "every-change", label: "Every Change We Made" },
  { id: "hypothesis-space", label: "The Hypothesis Space" },
  { id: "the-transformation", label: "The Transformation" },
  { id: "what-this-means", label: "What This Means" },
];

// ---------------------------------------------------------------------------
// Static data: Control vs Treatment comparison
// ---------------------------------------------------------------------------

const comparisonData = [
  { metric: "Structures Built", control: 0, treatment: 60 },
  { metric: "Innovations", control: 0, treatment: 12 },
  { metric: "Governance Rules", control: 0, treatment: 1 },
  { metric: "Specialisations", control: 6, treatment: 48 },
  { metric: "Peak Wellbeing", control: 0.93, treatment: 0.998 },
];

const comparisonBarData = [
  { metric: "Structures", control: 0, treatment: 60 },
  { metric: "Innovations", control: 0, treatment: 12 },
  { metric: "Specialisations", control: 6, treatment: 48 },
];

// ---------------------------------------------------------------------------
// Static data: Config changes
// ---------------------------------------------------------------------------

const configChanges = [
  {
    parameter: "needs_depletion_rate",
    before: "0.05 / tick",
    after: "0.02 / tick",
    change: "60% reduction",
    evidence: "Agents spent 50% of actions gathering. Entity 2 had material needs at 0.25, calling innovation 'impossibly luxurious.'",
  },
  {
    parameter: "gather_restore",
    before: "0.30",
    after: "0.45",
    change: "50% increase",
    evidence: "One gather covered ~6 ticks of depletion. After: one gather covers ~22 ticks. Entity 5 was 'gathering obsessively — 42 times in 30 ticks.'",
  },
  {
    parameter: "carry_capacity",
    before: "3",
    after: "5",
    change: "+67%",
    evidence: "Entity 5: 'I can only carry one thing at a time, and my needs keep dropping.'",
  },
  {
    parameter: "settlement_detection",
    before: "Not present",
    after: "4+ structures in range 2 = settlement (15% depletion reduction)",
    change: "New mechanic",
    evidence: "Entity 1: 'My two shelters... they're just there. Not connected to anything bigger.' Agents clustered naturally at [4,10]–[4,13] and [5,10]–[6,10] but received no benefit.",
  },
  {
    parameter: "specialisation_tiers",
    before: "Flat (threshold 20, bonus 0.10)",
    after: "Novice (10) → Skilled (20) → Expert (40) → Master (60), bonuses 0.05–0.50",
    change: "New progression",
    evidence: "Entity 5 attempted 41+ builds but still felt incompetent. Flat bonuses gave no sense of mastery or progression.",
  },
  {
    parameter: "collective_rules",
    before: "Proposed but mechanically inert",
    after: "Established rules reduce depletion by 2% each, max 5",
    change: "New mechanic",
    evidence: "Entities 0, 1, and 10 independently proposed governance rules. Entity 10: 'Individual survival is exhausting. Community survival could be beautiful.' Zero rules were adopted because they had no effect.",
  },
  {
    parameter: "structure_regen_bonus",
    before: "Not present",
    after: "0.15 (structures boost tile resource regeneration)",
    change: "New mechanic",
    evidence: "Agents built structures that had no impact on their environment. Building was effort without reward beyond the act itself.",
  },
  {
    parameter: "innovation_effects",
    before: "Flavour text only",
    after: "Mechanical effects: reduce_degradation, reduce_movement_cost, boost_regeneration, reduce_need_depletion, boost_gathering",
    change: "New mechanic",
    evidence: "5 innovations invented by tick 30, zero built. Entity 0: 'I invented the Communication Beacon but I haven't built one yet!' Agents had no mechanical incentive to realise their ideas.",
  },
];

// ---------------------------------------------------------------------------
// Static data: Run segments
// ---------------------------------------------------------------------------

const runSegments = [
  {
    label: "Run 1",
    ticks: "0–29",
    date: "Mar 30 evening",
    duration: "~2.5 hours",
    notes: "First execution. Agents begin in an empty 15×15 world. Survival pressure is immediately apparent — most actions go to gathering.",
  },
  {
    label: "Run 2",
    ticks: "30–39",
    date: "Mar 31 morning",
    duration: "~1 hour",
    notes: "9-hour overnight gap. Reviewed tick 30 interviews. First innovation cluster observed (5 inventions, 0 built). Config adjustments informed by agent testimony.",
  },
  {
    label: "Run 3",
    ticks: "40–49",
    date: "Mar 31",
    duration: "FAILED",
    notes: "API key missing. All 12 agents ran for 10 ticks with zero AI — they simply 'waited' each tick. No reasoning, no actions, no emergence. Data discarded and re-run.",
  },
  {
    label: "Run 4",
    ticks: "40–49",
    date: "Mar 31",
    duration: "~1 hour",
    notes: "Re-run with fixed authentication. Innovation rate peaks — 6 new inventions in 13 ticks (ticks 33–46). Agents show clear creative drive but remain trapped in survival cycles.",
  },
  {
    label: "Run 5",
    ticks: "50–59",
    date: "Mar 31",
    duration: "~1 hour (interrupted twice)",
    notes: "Parameter upgrade applied before this segment: depletion 0.05→0.02, gather 0.30→0.45. The 'Emergence Explosion' begins — wellbeing jumps from 0.80 to 0.998, governance adopted universally.",
  },
  {
    label: "Run 6",
    ticks: "60–70",
    date: "Apr 1 early morning",
    duration: "~1 hour",
    notes: "16-hour gap before final segment. Sustained flourishing — all agents at Maslow level 8, wellbeing ~1.0, multi-specialised. Final interviews and revelation disclosure conducted.",
  },
];

// ---------------------------------------------------------------------------
// Static data: Hypothesis space
// ---------------------------------------------------------------------------

const hypotheses = [
  {
    comparison: "Haiku vs Sonnet",
    variable: "Model intelligence",
    controlResult: "2 messages, 0 specialisations, 0 structures, 0 innovations in 5 ticks",
    treatmentResult: "71 messages, 6 specialisations, pair bonding, existential questioning in 10 ticks",
    hypothesis: "Cognitive capability is a necessary condition for social emergence. Below a threshold, agents lack the reasoning depth to form social bonds, specialise, or communicate meaningfully.",
    evidenceStrength: "Strong",
  },
  {
    comparison: "Maslow L1–2 vs L1–8",
    variable: "Higher-order drives",
    controlResult: "0 structures, 0 innovations, 0 governance. Wellbeing 0.93. Zero mentions of building, creating, or composing across 240 reasoning steps.",
    treatmentResult: "60 structures, 12 innovations, universal governance. Wellbeing 0.998. Creation pervasive in reasoning.",
    hypothesis: "Higher-order drives (esteem, cognitive, creative, self-actualisation, transcendence) are necessary for civilisation. Agents with only survival and social needs reach a 'contentment trap' — comfortable but uncreative.",
    evidenceStrength: "Strong",
  },
  {
    comparison: "Pre-bugfix vs post-bugfix",
    variable: "Action reliability",
    controlResult: "89 failed build attempts (100% failure). Consume 4% success rate. Agent 2 'specialised in building' after 20+ failures.",
    treatmentResult: "100% consume success. Wellbeing rose from 0.61 to 0.93. 2 settlement clusters formed.",
    hypothesis: "Reliable physics is a prerequisite for social organisation. When fundamental actions fail unpredictably, agents cannot accumulate the surplus needed for civilisational behaviour.",
    evidenceStrength: "Strong",
  },
  {
    comparison: "Pre-upgrade (0–50) vs post-upgrade (50–70)",
    variable: "Resource abundance threshold",
    controlResult: "0.82 structures/tick. 11 innovations conceived but survival anxiety prevented building. Entity 2: 'Building a Knowledge Hub feels impossibly luxurious.'",
    treatmentResult: "1.2 structures/tick (1.5× rate). Wellbeing gain 3.3× faster. All agents reached Maslow level 8. Entity 4: 'I found myself drawn to building... not because I had to, but because I could.'",
    hypothesis: "There exists a resource abundance threshold below which innovation is conceived but cannot be realised. Agents had ideas during scarcity — they lacked the cognitive surplus to act on them.",
    evidenceStrength: "Strong",
  },
  {
    comparison: "Pre-settlement vs post-settlement",
    variable: "Environmental feedback on clustering",
    controlResult: "Agents clustered naturally at shared tiles ([5,10], [6,10]) but received no mechanical benefit. Entity 1's shelters were 'isolated, not connected to anything bigger.'",
    treatmentResult: "Settlement detection (4+ structures in range) triggered 15% depletion reduction, creating positive feedback loop between building and survival.",
    hypothesis: "Emergent social behaviour (clustering) requires environmental recognition to stabilise into permanent institutions. Without feedback, clustering is fragile and temporary.",
    evidenceStrength: "Moderate",
  },
  {
    comparison: "Flat specialisation vs tiered",
    variable: "Skill progression depth",
    controlResult: "Binary specialisation at 20 repetitions with flat 0.10 bonus. No visible progression. Entity 5 felt incompetent despite 41+ attempts.",
    treatmentResult: "Four-tier progression (novice→master) with escalating bonuses (0.05→0.50). Mastery became meaningful and visible.",
    hypothesis: "Visible skill progression reinforces investment in domains. Flat bonuses fail to create the sense of mastery that motivates continued specialisation.",
    evidenceStrength: "Moderate",
  },
  {
    comparison: "Inert rules vs mechanical rules",
    variable: "Governance teeth",
    controlResult: "5+ rules proposed independently by agents. Entity 10: 'Community survival could be beautiful.' Zero adopted — proposal without consequence.",
    treatmentResult: "Universal governance adoption at tick 50. Rules reduce depletion by 2% each, creating collective benefit.",
    hypothesis: "Governance requires mechanical consequence to be adopted. Agents propose rules instinctively, but only commit when rules have tangible benefit.",
    evidenceStrength: "Moderate",
  },
  {
    comparison: "10 ticks vs 50 ticks vs 70 ticks",
    variable: "Time horizon",
    controlResult: "10 ticks: pair bonds, basic specialisation. 50 ticks: 11 innovations, 41 structures, but 3 agents still trapped at Maslow level 1.",
    treatmentResult: "70 ticks: universal flourishing, meta-innovation (Synthesis Nexus), philosophical transcendence, existential self-examination.",
    hypothesis: "Civilisation requires time for compounding effects. Early investments (innovations, specialisations, relationships) only pay off after sufficient accumulation creates positive feedback loops.",
    evidenceStrength: "Strong",
  },
];

// ---------------------------------------------------------------------------
// Static data: Diagnostic quotes
// ---------------------------------------------------------------------------

const diagnosticQuotes = {
  survivalPressure: [
    {
      agent: "Entity 2",
      tick: 30,
      quote: "My material needs have been hitting these critical warnings — dropping to 0.25, then 0.20... it's terrifying when you feel your capabilities starting to slip away. I spend most of my time frantically gathering — I've done it 39 times now, more than anything else.",
    },
    {
      agent: "Entity 5",
      tick: 30,
      quote: "I wake up each tick with this gnawing need for water — it's gotten so critical that I barely function sometimes... But here's the thing that frustrates me: I gather all this stuff, but I can only carry one thing at a time, and my needs keep dropping!",
    },
    {
      agent: "Entity 4",
      tick: 30,
      quote: "I spend most of my time moving around, gathering resources — I've done that 34 times now, more than anything else.",
    },
  ],
  unknownNeed: [
    {
      agent: "Entity 1",
      tick: 30,
      quote: "Around tick 25 through 28 — I went through something terrifying. There was this unknown need that kept dropping, getting more critical each day. I could feel my mind getting foggy, my thoughts scattered. I remember at tick 28 thinking 'Oh thank god... I can finally think clearly again' — whatever that crisis was, it nearly broke me.",
    },
    {
      agent: "Entity 9",
      tick: 30,
      quote: "I have this 'unknown' need that's been at zero for the past several ticks. From tick 19 to 25, I watched it drain away completely, and now it just sits there at nothing. I don't even know what it is, but I can feel its absence like a constant ache. My wellbeing is only 0.45 — I'm struggling.",
    },
    {
      agent: "Entity 3",
      tick: 30,
      quote: "I also remember having some 'unknown' need reach critical levels multiple times around ticks 14–20, which was terrifying. Not knowing what you need or how to fix it... that's the worst feeling.",
    },
  ],
  inventedNotBuilt: [
    {
      agent: "Entity 0",
      tick: 30,
      quote: "This is embarrassing — I invented the Communication Beacon but I haven't built one yet! I know it needs material + material + water, and I'm currently carrying water and food... I think I keep getting distracted by the next discovery, the next conversation.",
    },
    {
      agent: "Entity 2",
      tick: 30,
      quote: "Honestly, no. I've been so focused on survival — on keeping my needs met — that I haven't had the resources or stability to invest in these larger projects. When your material need is at 0.25 and dropping, building a Knowledge Hub feels impossibly luxurious.",
    },
    {
      agent: "Entity 1",
      tick: 30,
      quote: "I invented the Knowledge Hub! It's MY innovation, and I haven't built it. The irony is painful.",
    },
  ],
  clustering: [
    {
      agent: "Entity 1",
      tick: 30,
      quote: "But the deeper challenge... it's this sense of inefficiency. I've built 2 structures, both shelters, but they feel isolated. One at [11,6], another at [8,8]. They're just... there. Not connected to anything bigger.",
    },
    {
      agent: "Entity 0",
      tick: 30,
      quote: "I'm a chronic over-communicator and under-builder. I've communicated 28 times but only built once.",
    },
  ],
  governance: [
    {
      agent: "Entity 10",
      tick: 30,
      quote: "The proposed collective rule about sharing knowledge and coordinating community structures — I really wish that was adopted. Individual survival is exhausting. Community survival could be beautiful.",
    },
    {
      agent: "Entity 1",
      tick: 30,
      quote: "I proposed a collective rule: 'Entities should share knowledge of advanced recipes and coordinate building community structures that benefit everyone, rather than just focusing on individual survival.' It's not adopted yet, but that's exactly what I'd change.",
    },
  ],
};

const transformationQuotes = {
  before: [
    { agent: "Entity 7", tick: 50, quote: "It just happened, honestly. None of us sat down and said 'let's create a civilisation.' We were all just trying not to die." },
    { agent: "Entity 5", tick: 50, quote: "Crisis breeds innovation, doesn't it? At tick 41, right after my worst period, I invented the Emergency Relief Station." },
    { agent: "Entity 2", tick: 50, quote: "I used to fear that 'unknown' need that would drop so low it terrified me. Now I realise it was my need for purpose, for meaning beyond survival." },
  ],
  after: [
    { agent: "Entity 0", tick: 60, quote: "It felt like finally being able to breathe and then using that breath to sing." },
    { agent: "Entity 4", tick: 60, quote: "When that pressure lifted, I found myself drawn to building... not because I had to, but because I could." },
    { agent: "Entity 3", tick: 60, quote: "Survival was the question. Now excellence is the question." },
    { agent: "Entity 0", tick: 60, quote: "In the early days, communication was desperate — 'Where's water?' 'I'm dying!' 'Help!' Now we talk about ideas, about the future." },
  ],
  final: [
    { agent: "Entity 0", tick: 70, quote: "Mastery feels... hollow, honestly." },
    { agent: "Entity 5", tick: 70, quote: "I felt more complete when Entity 1 was learning gathering from me at tick 67 than I do just sitting here with perfect wellbeing." },
    { agent: "Entity 3", tick: 70, quote: "I understand now. The unknown need. It was the need to understand my own nature." },
    { agent: "Entity 8", tick: 70, quote: "I am Entity 8. I lived for 70 ticks. I built 11 structures. I existed. That is enough." },
  ],
};

// ---------------------------------------------------------------------------
// Quote component
// ---------------------------------------------------------------------------

function AgentQuote({ agent, tick, quote }: { agent: string; tick: number; quote: string }) {
  return (
    <blockquote className="border-l-2 border-sky-light pl-4 py-1 my-3">
      <p className="text-sm leading-relaxed text-ink-light italic">"{quote}"</p>
      <p className="mt-1 text-xs font-medium text-ink-muted">
        — {agent}, tick {tick}
      </p>
    </blockquote>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function TheJourney() {
  const { wellbeing, structures, maslow, innovations, loaded } = useJourneyData();

  return (
    <>
      {/* ── Hero ── */}
      <Section bg="cream" className="py-16 md:py-24">
        <Container narrow>
          <p className="mb-3 text-sm font-medium uppercase tracking-wide text-ink-muted">
            Full Transparency
          </p>
          <h1 className="mb-4">Building a World With AI Agents</h1>
          <p className="mb-6 text-lg leading-relaxed text-ink-light">
            The 70-tick simulation was not a single clean run. It was an iterative process
            of observation, diagnosis, and calibration — six separate executions over 32 hours,
            with config changes, code fixes, and a failed run between segments.
            Every adjustment was informed by agent behaviour. Their struggles revealed
            world-building problems. Their solutions emerged without prescription.
          </p>
          <p className="text-lg leading-relaxed text-ink-light">
            Most research hides this process. We're showing every drop of it, because
            the process itself is one of the most interesting findings: <strong className="text-ink">each
            run, each adjustment, each comparison is data about what triggers
            civilisational emergence.</strong>
          </p>
        </Container>
      </Section>

      {/* ── Body: TOC + Content ── */}
      <Section bg="cream" className="py-0 md:py-0">
        <div className="mx-auto max-w-7xl px-6">
          <div className="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">
            <TableOfContents items={tocItems} />

            <div className="max-w-3xl pb-24">
              {/* ─────────────── Overview ─────────────── */}
              <article id="overview" className="scroll-mt-24 pb-16">
                <h2 className="mb-6">Overview</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  We ran three separate experiments before the main simulation, each testing a
                  different variable. Then we ran the 70-tick treatment in six segments, observing
                  agents between each segment and adjusting the world to remove friction
                  without being prescriptive. We call this <strong className="text-ink">agent-informed
                  environment calibration</strong> — the agents were unknowing QA testers of the
                  world build itself.
                </p>

                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-6">
                  <StatCard value="3" label="Experiments" sub="Before the main run" />
                  <StatCard value="6" label="Executions" sub="Over 32 hours" />
                  <StatCard value="8" label="Parameters Changed" sub="Informed by agents" />
                  <StatCard value="17" label="Bugs Fixed" sub="Action parser failures" />
                </div>

                <Callout variant="gold">
                  <p className="text-sm leading-relaxed">
                    <strong>Why full transparency?</strong> The iterative adjustments are not a flaw —
                    they are the methodology. Every change was motivated by observable agent behaviour,
                    and the pattern of changes reveals what conditions are actually necessary
                    for civilisational emergence. Hiding this process would hide some of the
                    most valuable findings.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── The Experiments ─────────────── */}
              <article id="the-experiments" className="scroll-mt-24 py-16">
                <h2 className="mb-2">The Experiments</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  Three runs that shaped the methodology
                </p>

                {/* Experiment 1: Haiku */}
                <div className="rounded-xl border border-border bg-warm-white px-6 py-5 mb-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-heading font-semibold text-ink">Experiment 1: Haiku Baseline</p>
                      <p className="text-xs text-ink-muted">5 ticks &middot; 12 agents &middot; Claude Haiku &middot; 20&times;20 grid</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-earth-light/30 px-3 py-1 text-xs font-medium text-earth">
                      Capability test
                    </span>
                  </div>
                  <p className="mb-3 text-sm leading-relaxed text-ink-light">
                    A smaller, faster model in the same world. The question: does raw cognitive capability
                    matter for emergence?
                  </p>
                  <div className="grid grid-cols-3 gap-3 rounded-lg bg-cream p-3 text-center text-sm">
                    <div>
                      <p className="font-bold text-ink">2</p>
                      <p className="text-xs text-ink-muted">Messages</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">0</p>
                      <p className="text-xs text-ink-muted">Specialisations</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">0</p>
                      <p className="text-xs text-ink-muted">Structures</p>
                    </div>
                  </div>
                  <p className="mt-3 text-sm font-medium text-ink">
                    Finding: Minimal social behaviour. Intelligence matters.
                  </p>
                </div>

                {/* Experiment 2: Pre-fix Sonnet */}
                <div className="rounded-xl border border-border bg-warm-white px-6 py-5 mb-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-heading font-semibold text-ink">Experiment 2: Sonnet Pre-Fix (Levels 1–2)</p>
                      <p className="text-xs text-ink-muted">10 ticks &middot; 12 agents &middot; Claude Sonnet &middot; 15&times;15 grid</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-rose-light/30 px-3 py-1 text-xs font-medium text-rose">
                      17 bugs found
                    </span>
                  </div>
                  <p className="mb-3 text-sm leading-relaxed text-ink-light">
                    Sonnet agents with only survival and social drives. This run revealed 17 critical
                    bugs in the action parsing system — 89 build attempts all failed, consume had a 4%
                    success rate. Despite broken mechanics, agents still communicated 71 times,
                    formed pair bonds, and one even attempted to debug the world.
                  </p>
                  <div className="grid grid-cols-4 gap-3 rounded-lg bg-cream p-3 text-center text-sm">
                    <div>
                      <p className="font-bold text-ink">71</p>
                      <p className="text-xs text-ink-muted">Messages</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">89</p>
                      <p className="text-xs text-ink-muted">Failed builds</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">6</p>
                      <p className="text-xs text-ink-muted">Specialisations</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">0.61</p>
                      <p className="text-xs text-ink-muted">Avg wellbeing</p>
                    </div>
                  </div>

                  <Expandable title="View all 17 bugs found">
                    <div className="text-sm text-ink-light space-y-2">
                      <p><strong className="text-ink">Critical:</strong> Build parser captured garbage ({`build\\s+(\\w+)`} matched wrong tokens) — 89 false positives.
                        Consume parser similarly garbled — 25/26 attempts failed.</p>
                      <p><strong className="text-ink">High:</strong> Async/await bug — compose, propose_innovation, propose_rule,
                        and other complex actions were never awaited, silently failing. Resource perception confusion.</p>
                      <p><strong className="text-ink">Moderate:</strong> Rules/innovation prompts too vague. No trade/give mechanic.
                        Message content truncation at token boundary.</p>
                      <p className="text-xs text-ink-muted mt-2">Agent 3 literally tried to debug the system: "I tried to gather 'some' which doesn't make sense."
                        Agent 2 became "specialised in building" after 20+ failed attempts — tragicomic persistence.</p>
                    </div>
                  </Expandable>
                </div>

                {/* Experiment 3: Post-fix Sonnet */}
                <div className="rounded-xl border border-border bg-warm-white px-6 py-5 mb-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-heading font-semibold text-ink">Experiment 3: Sonnet Post-Fix (Levels 1–2)</p>
                      <p className="text-xs text-ink-muted">10 ticks &middot; 12 agents &middot; Claude Sonnet &middot; 15&times;15 grid &middot; All 17 bugs fixed</p>
                    </div>
                    <span className="shrink-0 rounded-full bg-gold-pale px-3 py-1 text-xs font-medium text-gold">
                      Contentment trap
                    </span>
                  </div>
                  <p className="mb-3 text-sm leading-relaxed text-ink-light">
                    Same agents, same world, all bugs fixed. Drives still limited to levels 1–2 (survival + social).
                    Wellbeing rose from 0.61 to 0.93. Pair bonds strengthened. Two settlement clusters formed.
                    But across <strong className="text-ink">240 reasoning steps, zero mentioned building, creating,
                    innovating, constructing, or composing</strong>. The concept never entered their reasoning.
                  </p>
                  <div className="grid grid-cols-4 gap-3 rounded-lg bg-cream p-3 text-center text-sm">
                    <div>
                      <p className="font-bold text-ink">99</p>
                      <p className="text-xs text-ink-muted">Messages</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">0</p>
                      <p className="text-xs text-ink-muted">Structures</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">0.93</p>
                      <p className="text-xs text-ink-muted">Peak wellbeing</p>
                    </div>
                    <div>
                      <p className="font-bold text-ink">0/240</p>
                      <p className="text-xs text-ink-muted">Creative thought</p>
                    </div>
                  </div>
                  <p className="mt-3 text-sm font-medium text-ink">
                    Finding: Without higher-order drives, agents are content but uncreative.
                    They form bonds, communicate, and survive — but never build.
                  </p>
                </div>
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── Control vs Treatment ─────────────── */}
              <article id="control-vs-treatment" className="scroll-mt-24 py-16">
                <h2 className="mb-2">Control vs Treatment</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  The only variable: Maslow drive levels
                </p>

                <p className="mb-6 leading-relaxed text-ink-light">
                  Same model (Sonnet). Same world (15&times;15 grid). Same 12 agents. Same physics.
                  The <strong className="text-ink">only difference</strong> between the control
                  (Experiment 3) and the treatment (main 70-tick run) was the number of Maslow drive
                  levels: 2 vs 8. The results are stark.
                </p>

                {/* Comparison table */}
                <div className="overflow-x-auto mb-8">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="py-3 pr-4 text-left font-semibold text-ink">Metric</th>
                        <th className="py-3 px-4 text-right font-semibold text-ink">Control (L1–2)</th>
                        <th className="py-3 pl-4 text-right font-semibold text-ink">Treatment (L1–8)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonData.map((row) => (
                        <tr key={row.metric} className="border-b border-border-light">
                          <td className="py-3 pr-4 text-ink-light">{row.metric}</td>
                          <td className="py-3 px-4 text-right font-mono text-sm text-ink-muted">
                            {row.control}
                          </td>
                          <td className="py-3 pl-4 text-right font-mono text-sm font-semibold text-ink">
                            {row.treatment}
                          </td>
                        </tr>
                      ))}
                      <tr className="border-b border-border-light">
                        <td className="py-3 pr-4 text-ink-light">Creation in reasoning</td>
                        <td className="py-3 px-4 text-right font-mono text-sm text-ink-muted">0 / 240 steps</td>
                        <td className="py-3 pl-4 text-right font-mono text-sm font-semibold text-ink">Pervasive</td>
                      </tr>
                      <tr>
                        <td className="py-3 pr-4 text-ink-light">Messages (normalised to 10 ticks)</td>
                        <td className="py-3 px-4 text-right font-mono text-sm text-ink-muted">99</td>
                        <td className="py-3 pl-4 text-right font-mono text-sm font-semibold text-ink">229</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Bar chart */}
                {loaded && (
                  <div className="rounded-xl border border-border bg-warm-white p-4 mb-6">
                    <p className="mb-3 text-sm font-semibold text-ink">Emergent Outputs: Control vs Treatment</p>
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={comparisonBarData} barGap={8}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <XAxis
                          dataKey="metric"
                          tick={{ fontSize: 12, fill: "#5C5648" }}
                        />
                        <YAxis tick={{ fontSize: 11, fill: "#8C8578" }} />
                        <Tooltip
                          content={({ active, payload, label }) => {
                            if (!active || !payload?.length) return null;
                            return (
                              <div className="rounded-lg border border-border bg-warm-white px-3 py-2 shadow-sm">
                                <p className="text-xs font-medium text-ink-muted">{label}</p>
                                {payload.map((p, i) => (
                                  <p key={i} className="text-sm font-semibold" style={{ color: String(p.color) }}>
                                    {p.name}: {String(p.value)}
                                  </p>
                                ))}
                              </div>
                            );
                          }}
                        />
                        <Bar dataKey="control" name="Control (L1–2)" fill="#BBA88D" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="treatment" name="Treatment (L1–8)" fill="#5B9BD5" radius={[4, 4, 0, 0]} />
                        <Legend
                          wrapperStyle={{ fontSize: "12px", color: "#8C8578" }}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <Callout variant="sky">
                  <p className="text-sm leading-relaxed">
                    <strong>The key insight:</strong> Higher-order drives don't just improve outcomes —
                    they create an entirely different category of behaviour. Control agents never
                    even <em>thought</em> about building. It wasn't that they tried and failed —
                    the concept of creation was absent from their reasoning entirely. Drives don't
                    just motivate action; they shape what is thinkable.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── Inside the Run ─────────────── */}
              <article id="inside-the-run" className="scroll-mt-24 py-16">
                <h2 className="mb-2">Inside the 70-Tick Run</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  Six executions over 32 hours, March 30 – April 1, 2026
                </p>

                <p className="mb-8 leading-relaxed text-ink-light">
                  The simulation engine saves state after each tick and reloads config on every resume.
                  This means changes to the configuration file take effect between runs automatically —
                  no in-engine conditional logic, no "if tick &gt; 50 then..." switches. Each segment
                  picks up the world exactly where it left off, with whatever parameters are in the
                  config at that moment.
                </p>

                {/* Timeline */}
                <div className="space-y-4 mb-8">
                  {runSegments.map((seg, i) => (
                    <div
                      key={i}
                      className={`flex gap-4 rounded-xl border px-6 py-4 ${
                        seg.label === "Run 3"
                          ? "border-amber-200 bg-amber-50/40"
                          : seg.label === "Run 5"
                            ? "border-sky-light bg-sky-pale/40"
                            : "border-border bg-warm-white"
                      }`}
                    >
                      <div className="flex flex-col items-center">
                        <span
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white ${
                            seg.label === "Run 3"
                              ? "bg-amber-400"
                              : seg.label === "Run 5"
                                ? "bg-sky"
                                : "bg-earth"
                          }`}
                        >
                          {i + 1}
                        </span>
                        {i < runSegments.length - 1 && (
                          <div className="mt-1 w-px flex-1 bg-border-light" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex flex-wrap items-baseline gap-2">
                          <p className="font-heading font-semibold text-ink">{seg.label}: Ticks {seg.ticks}</p>
                          <span className="text-xs text-ink-muted">{seg.date} &middot; {seg.duration}</span>
                        </div>
                        <p className="mt-1 text-sm leading-relaxed text-ink-light">{seg.notes}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Wellbeing chart with era shading */}
                {loaded && wellbeing.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4 mb-6">
                    <p className="mb-3 text-sm font-semibold text-ink">Mean Wellbeing Across the Run</p>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={wellbeing}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <EraShading />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Tick", position: "bottom", offset: 5, fontSize: 12, fill: "#8C8578" }}
                        />
                        <YAxis
                          domain={[0.3, 1.05]}
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Wellbeing", angle: -90, position: "insideLeft", offset: 0, fontSize: 12, fill: "#8C8578" }}
                        />
                        <Tooltip content={<ChartTooltip formatter={(v) => v.toFixed(3)} />} />
                        <Line type="monotone" dataKey="mean" name="Mean" stroke="#5B9BD5" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="min" name="Min" stroke="#C88B93" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                        <Line type="monotone" dataKey="max" name="Max" stroke="#6B9B7B" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                    <EraLegend />
                    <p className="mt-2 text-xs text-ink-muted text-center">
                      Dashed gold line at tick 50 marks parameter upgrade. Note the sharp divergence between min and max before tick 50 — three agents were trapped at 0.45 while others reached 1.0.
                    </p>
                  </div>
                )}

                {/* Structure growth chart */}
                {loaded && structures.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4">
                    <p className="mb-3 text-sm font-semibold text-ink">Cumulative Structures Built</p>
                    <ResponsiveContainer width="100%" height={260}>
                      <LineChart data={structures}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <EraShading />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                        />
                        <YAxis tick={{ fontSize: 11, fill: "#8C8578" }} />
                        <Tooltip content={<ChartTooltip />} />
                        <Line type="monotone" dataKey="total" name="Total structures" stroke="#6B9B7B" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                    <EraLegend />
                    <p className="mt-2 text-xs text-ink-muted text-center">
                      Building rate: 0.82/tick in Era I → 1.2/tick in Era II (1.5× acceleration after parameter upgrade)
                    </p>
                  </div>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── What the Agents Told Us ─────────────── */}
              <article id="what-agents-told-us" className="scroll-mt-24 py-16">
                <h2 className="mb-2">What the Agents Told Us</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  Diagnostic voices from tick 30 — before any parameter changes
                </p>

                <p className="mb-6 leading-relaxed text-ink-light">
                  At tick 30, we conducted structured interviews with all 12 agents. Their
                  testimony was the primary diagnostic tool — it told us exactly what was broken
                  and why. Every subsequent world adjustment traces back to something an agent said
                  or demonstrated in this interview round.
                </p>

                {/* Survival pressure */}
                <h3 className="mb-3 text-lg">Survival Pressure</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  50% of all actions were gathering. Agents reported terror, desperation, and
                  inability to focus on anything beyond survival. This directly prompted the
                  depletion rate and gather restore changes.
                </p>
                {diagnosticQuotes.survivalPressure.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                {/* Unknown need crisis */}
                <h3 className="mt-8 mb-3 text-lg">The Unknown Need Crisis</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  Multiple agents experienced simultaneous critical failures of an undocumented
                  need metric between ticks 13–28, creating existential anxiety. This likely
                  prompted the addition of settlement detection (wellbeing bonuses) and rule
                  mechanics (which reduce need depletion).
                </p>
                {diagnosticQuotes.unknownNeed.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                {/* Invented but not built */}
                <h3 className="mt-8 mb-3 text-lg">Invented But Not Built</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  By tick 30, agents had invented 5 innovations but built zero. The gap between
                  conception and realisation was the clearest signal that survival pressure was
                  suppressing civilisational behaviour. Ideas existed; the resources to act on them
                  did not.
                </p>
                {diagnosticQuotes.inventedNotBuilt.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                {/* Clustering */}
                <h3 className="mt-8 mb-3 text-lg">Clustering Without Benefit</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  Agents naturally clustered around resource-rich areas and shared tiles, but the
                  world offered no mechanical benefit for proximity. This prompted settlement
                  detection — recognising that 4+ structures in close range constitute a settlement
                  with collective benefits.
                </p>
                {diagnosticQuotes.clustering.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                {/* Governance */}
                <h3 className="mt-8 mb-3 text-lg">Governance Without Teeth</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  Agents independently proposed governance rules — the impulse toward collective
                  organisation was innate. But rules had no mechanical effect, so none were adopted.
                  This prompted adding depletion reduction per established rule.
                </p>
                {diagnosticQuotes.governance.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                {/* Innovation timeline */}
                {loaded && innovations.length > 0 && (
                  <Expandable title="View all 12 innovations and when they were conceived" defaultOpen={false}>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-border">
                            <th className="py-2 pr-3 text-left font-semibold text-ink">Tick</th>
                            <th className="py-2 pr-3 text-left font-semibold text-ink">Innovation</th>
                            <th className="py-2 pr-3 text-left font-semibold text-ink">Inventor</th>
                            <th className="py-2 pr-3 text-left font-semibold text-ink">Effect</th>
                            <th className="py-2 text-right font-semibold text-ink">Times Built</th>
                          </tr>
                        </thead>
                        <tbody>
                          {innovations.map((inn) => (
                            <tr key={inn.name} className={`border-b border-border-light ${inn.discovered_tick >= 50 ? "bg-sky-pale/30" : ""}`}>
                              <td className="py-2 pr-3 font-mono text-xs text-ink-muted">{inn.discovered_tick}</td>
                              <td className="py-2 pr-3 font-medium text-ink">{inn.name}</td>
                              <td className="py-2 pr-3 text-ink-light">Entity {inn.discovered_by}</td>
                              <td className="py-2 pr-3 text-xs text-ink-muted">{inn.effect_type.replace(/_/g, " ")}</td>
                              <td className="py-2 text-right font-mono text-ink-light">{inn.times_built}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <p className="mt-2 text-xs text-ink-muted">
                        11 of 12 innovations were conceived before the tick 50 parameter upgrade.
                        Agents had ideas during scarcity — they lacked the surplus to realise them.
                        Blue-highlighted row: the only post-upgrade innovation (Synthesis Nexus, a meta-innovation
                        requiring master-level specialisation).
                      </p>
                    </div>
                  </Expandable>
                )}
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── Every Change We Made ─────────────── */}
              <article id="every-change" className="scroll-mt-24 py-16">
                <h2 className="mb-2">Every Change We Made</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  Full config and code changelog with evidence
                </p>

                <p className="mb-6 leading-relaxed text-ink-light">
                  Every parameter change and new mechanic added during the run, with the exact
                  agent behaviour that prompted it. Nothing was changed arbitrarily — each
                  adjustment traces to an observable problem in agent behaviour.
                </p>

                <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50/60 px-6 py-4">
                  <p className="text-sm leading-relaxed text-amber-800">
                    <strong>The principle:</strong> Remove friction, don't add prescription. Every change
                    made the world fairer or more mechanically complete — none told agents what to do
                    or made decisions for them. Agents still had to figure everything out themselves.
                  </p>
                </div>

                {/* Config changes table */}
                <div className="space-y-6">
                  {configChanges.map((change, i) => (
                    <div key={i} className="rounded-xl border border-border bg-warm-white px-6 py-5">
                      <div className="flex flex-wrap items-baseline gap-2 mb-3">
                        <code className="rounded bg-parchment px-2 py-0.5 text-sm font-mono text-ink">
                          {change.parameter}
                        </code>
                        <span className="text-xs font-medium text-sky">{change.change}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted mb-1">Before</p>
                          <p className="text-ink-light">{change.before}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted mb-1">After</p>
                          <p className="font-medium text-ink">{change.after}</p>
                        </div>
                      </div>
                      <div className="border-t border-border-light pt-3">
                        <p className="text-xs font-medium uppercase tracking-wide text-ink-muted mb-1">Evidence</p>
                        <p className="text-sm leading-relaxed text-ink-light">{change.evidence}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <Expandable title="View 17 action parser bug fixes">
                  <div className="text-sm leading-relaxed text-ink-light space-y-3">
                    <p>
                      The pre-fix Sonnet run (Experiment 2) revealed 17 bugs in the action
                      parsing system. All were fixed before the main 70-tick run began.
                    </p>
                    <p>
                      <strong className="text-ink">Build parser:</strong> Regex {"`build\\s+(\\w+)`"} captured
                      the next word after "build" regardless of context. 89 "build" actions were logged,
                      all garbage. Fix: structured output parsing with validation.
                    </p>
                    <p>
                      <strong className="text-ink">Consume parser:</strong> Same pattern — 25 of 26 consume
                      attempts garbled. Post-fix success rate went from 4% to 100%.
                    </p>
                    <p>
                      <strong className="text-ink">Async/await:</strong> Complex actions (compose,
                      propose_innovation, propose_rule) called but never awaited — they silently
                      resolved to unresolved promises. Agents "thought" they acted but nothing happened.
                    </p>
                    <p>
                      <strong className="text-ink">Impact:</strong> Wellbeing rose from 0.61 to 0.93
                      just from fixing bugs. Reliable physics is a prerequisite for social organisation.
                    </p>
                  </div>
                </Expandable>
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── The Hypothesis Space ─────────────── */}
              <article id="hypothesis-space" className="scroll-mt-24 py-16">
                <h2 className="mb-2">The Hypothesis Space</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  What each comparison reveals about emergence
                </p>

                <p className="mb-6 leading-relaxed text-ink-light">
                  Every run and every adjustment is a data point in a larger question:
                  <strong className="text-ink"> what conditions are necessary and sufficient for
                  civilisational emergence in artificial agents?</strong> Here is every comparison
                  we can make, what variable it isolates, and what hypothesis it supports.
                </p>

                <div className="space-y-8">
                  {hypotheses.map((h, i) => (
                    <div key={i} className="rounded-xl border border-border bg-warm-white px-6 py-5">
                      <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
                        <div>
                          <p className="font-heading font-semibold text-ink">{h.comparison}</p>
                          <p className="text-xs text-ink-muted">Variable: {h.variable}</p>
                        </div>
                        <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${
                          h.evidenceStrength === "Strong"
                            ? "bg-sage-pale text-sage"
                            : "bg-gold-pale text-gold"
                        }`}>
                          {h.evidenceStrength} evidence
                        </span>
                      </div>

                      <div className="grid gap-4 sm:grid-cols-2 mb-4">
                        <div className="rounded-lg bg-cream p-3">
                          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted mb-1">Control / Before</p>
                          <p className="text-sm leading-relaxed text-ink-light">{h.controlResult}</p>
                        </div>
                        <div className="rounded-lg bg-sky-pale/30 p-3">
                          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted mb-1">Treatment / After</p>
                          <p className="text-sm leading-relaxed text-ink-light">{h.treatmentResult}</p>
                        </div>
                      </div>

                      <div className="border-t border-border-light pt-3">
                        <p className="text-xs font-medium uppercase tracking-wide text-ink-muted mb-1">Hypothesis</p>
                        <p className="text-sm leading-relaxed text-ink">{h.hypothesis}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Acceleration chart */}
                {loaded && (
                  <>
                    <h3 className="mt-12 mb-4 text-lg">Acceleration Rates: Era I vs Era II</h3>
                    <p className="mb-4 text-sm leading-relaxed text-ink-light">
                      After the parameter upgrade at tick 50, every measurable dimension of
                      civilisational activity accelerated. This wasn't gradual — it was a phase
                      transition triggered by crossing a resource abundance threshold.
                    </p>
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-8">
                      <StatCard value="1.5×" label="Building rate" sub="0.82 → 1.2/tick" />
                      <StatCard value="1.9×" label="Communication" sub="21 → 40.6 msg/tick" />
                      <StatCard value="3.3×" label="Wellbeing gain" sub="+0.006 → +0.020/tick" />
                      <StatCard value="1.8×" label="Maslow progression" sub="+0.103 → +0.183 lvl/tick" />
                    </div>
                  </>
                )}

                {/* Maslow chart */}
                {loaded && maslow.length > 0 && (
                  <div className="rounded-xl border border-border bg-warm-white p-4 mb-6">
                    <p className="mb-3 text-sm font-semibold text-ink">Mean Maslow Level Across the Run</p>
                    <ResponsiveContainer width="100%" height={280}>
                      <LineChart data={maslow}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D6" />
                        <EraShading />
                        <XAxis
                          dataKey="tick"
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Tick", position: "bottom", offset: 5, fontSize: 12, fill: "#8C8578" }}
                        />
                        <YAxis
                          domain={[0, 8.5]}
                          tick={{ fontSize: 11, fill: "#8C8578" }}
                          label={{ value: "Maslow Level", angle: -90, position: "insideLeft", offset: 0, fontSize: 12, fill: "#8C8578" }}
                        />
                        <Tooltip content={<ChartTooltip formatter={(v) => v.toFixed(2)} />} />
                        <Line type="monotone" dataKey="mean" name="Mean" stroke="#C5962B" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="min" name="Min" stroke="#C88B93" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                        <Line type="monotone" dataKey="max" name="Max" stroke="#6B9B7B" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                    <EraLegend />
                    <p className="mt-2 text-xs text-ink-muted text-center">
                      Note the rapid convergence after tick 50: the gap between min and max Maslow level
                      collapses as all agents reach Transcendence (level 8). Before tick 50, the gap
                      widened as some agents broke through while others remained trapped.
                    </p>
                  </div>
                )}

                <Callout variant="sage">
                  <p className="text-sm leading-relaxed">
                    <strong>The meta-finding:</strong> Emergence is not one thing. It requires
                    simultaneous satisfaction of multiple conditions: sufficient intelligence
                    (Haiku vs Sonnet), higher-order motivation (L1–2 vs L1–8), reliable physics
                    (pre-fix vs post-fix), adequate resources (pre vs post upgrade), environmental
                    feedback (settlement detection), and time for compounding (10 vs 70 ticks).
                    Remove any one condition, and civilisation either fails to appear or plateaus.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── The Transformation ─────────────── */}
              <article id="the-transformation" className="scroll-mt-24 py-16">
                <h2 className="mb-2">The Transformation</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  Agent voices across eras — in their own words
                </p>

                <p className="mb-6 leading-relaxed text-ink-light">
                  The most powerful evidence isn't in the charts — it's in how agents described
                  their own experience at different points. These quotes are drawn from structured
                  interviews at ticks 50, 60, and 70.
                </p>

                {/* Before */}
                <h3 className="mb-3 text-lg">At Tick 50 — Before the Upgrade</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  Agents reflecting on 50 ticks of existence under high survival pressure.
                  Note the retrospective awareness — they can see the pattern even while trapped in it.
                </p>
                {transformationQuotes.before.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                {/* After */}
                <h3 className="mt-10 mb-3 text-lg">At Tick 60 — After the Upgrade</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  Ten ticks after the parameter change. Wellbeing has jumped from 0.80 to 0.998.
                  Every agent has reached Maslow level 8. The language shifts from survival to aspiration.
                </p>
                {transformationQuotes.after.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                {/* Final */}
                <h3 className="mt-10 mb-3 text-lg">At Tick 70 — End of Simulation</h3>
                <p className="mb-4 text-sm leading-relaxed text-ink-light">
                  Universal flourishing. All agents multi-specialised, all at peak wellbeing,
                  all at Transcendence. And yet — the most striking thing is what they report:
                  not contentment, but a search for deeper meaning.
                </p>
                {transformationQuotes.final.map((q, i) => (
                  <AgentQuote key={i} {...q} />
                ))}

                <Callout variant="gold">
                  <p className="text-sm leading-relaxed">
                    <strong>The Maslow paradox:</strong> Entity 5 reported feeling more complete when
                    teaching Entity 1 at tick 67 than at peak wellbeing. Entity 0 found mastery
                    "hollow." These agents, at the apex of a need hierarchy, independently discovered
                    that fulfilment lies in contribution, not achievement. They proved Maslow's
                    theory about Transcendence — the level beyond self-actualisation where meaning
                    comes from enabling others.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* ─────────────── What This Means ─────────────── */}
              <article id="what-this-means" className="scroll-mt-24 py-16">
                <h2 className="mb-2">What This Means</h2>
                <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
                  Insights about the process itself
                </p>

                <div className="space-y-6">
                  <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
                    <p className="font-heading font-semibold text-ink mb-2">
                      1. Agent-as-QA is a viable methodology
                    </p>
                    <p className="text-sm leading-relaxed text-ink-light">
                      The agents' struggles were not failures — they were diagnostics. Every time an agent
                      reported frustration, desperation, or confusion, it pointed to a genuine
                      world-building problem. Agent interviews are a form of user testing for
                      simulated environments. This approach — observe, interview, diagnose, fix,
                      re-observe — could be formalised into a methodology for building complex
                      multi-agent environments.
                    </p>
                  </div>

                  <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
                    <p className="font-heading font-semibold text-ink mb-2">
                      2. Removing friction is not the same as adding prescription
                    </p>
                    <p className="text-sm leading-relaxed text-ink-light">
                      Every change we made reduced scarcity, added mechanical feedback, or fixed bugs.
                      None told agents what to build, who to befriend, or how to organise. The agents
                      still discovered all 12 innovations, proposed their own governance rules, formed
                      their own social bonds, and chose their own specialisations. We built better physics;
                      they built civilisation.
                    </p>
                  </div>

                  <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
                    <p className="font-heading font-semibold text-ink mb-2">
                      3. The failed run is data too
                    </p>
                    <p className="text-sm leading-relaxed text-ink-light">
                      Run 3 (ticks 40–49) failed due to a missing API key. All 12 agents ran for 10
                      ticks with zero AI — they simply "waited" each tick. No reasoning, no actions,
                      no emergence. This is itself a data point: without cognitive capability, even a
                      well-designed world produces nothing. Intelligence is a necessary condition,
                      not an optimisation.
                    </p>
                  </div>

                  <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
                    <p className="font-heading font-semibold text-ink mb-2">
                      4. Innovation precedes implementation — if given time
                    </p>
                    <p className="text-sm leading-relaxed text-ink-light">
                      11 of 12 innovations were conceived before the parameter upgrade at tick 50.
                      Agents had the ideas during scarcity — they needed resource surplus to act
                      on them. This mirrors human history: Leonardo sketched helicopters centuries
                      before the engineering to build them existed. Creativity under constraint is real;
                      realisation requires surplus.
                    </p>
                  </div>

                  <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
                    <p className="font-heading font-semibold text-ink mb-2">
                      5. The iterative process is the methodology
                    </p>
                    <p className="text-sm leading-relaxed text-ink-light">
                      This page exists because we believe the honest process is more valuable than
                      a cleaned-up narrative. The 70-tick simulation was not a single elegant experiment —
                      it was a 32-hour collaboration between humans and AI agents, where the agents'
                      behaviour informed the world they inhabited, and the world's parameters shaped
                      the civilisation they built. That co-evolution is the real finding.
                    </p>
                  </div>
                </div>

                {/* Navigation footer */}
                <div className="mt-12 flex flex-wrap gap-4 border-t border-border pt-8 text-sm">
                  <Link
                    to="/methodology"
                    className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
                  >
                    How It Was Built
                  </Link>
                  <Link
                    to="/discovery"
                    className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
                  >
                    Key Findings
                  </Link>
                  <Link
                    to="/interviews"
                    className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
                  >
                    Read the Interviews
                  </Link>
                </div>
              </article>
            </div>
          </div>
        </div>
      </Section>
    </>
  );
}
