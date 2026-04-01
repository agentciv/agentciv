import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

export default function Simulations() {
  return (
    <Section bg="cream" className="py-16 md:py-24">
      <Container narrow>
        <h1 className="mb-4">Simulations</h1>
        <p className="mb-10 text-lg leading-relaxed text-ink-light">
          Every simulation run is a unique experiment. Different models, different
          configurations, different durations — each producing distinct emergent
          behaviours. This page will be a living archive of every run we
          conduct, with full analysis, comparison, and the raw data to back it up.
        </p>

        <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-6 py-5 mb-12">
          <p className="text-sm font-medium text-amber-800">
            This page is under construction. The data and analysis are preserved —
            the presentation is coming.
          </p>
        </div>

        <h2 className="mb-4 mt-8 text-2xl">What will be here</h2>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Per-run deep dives</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>Model used (Haiku, Sonnet, Opus), configuration, number of ticks, grid size, agent count</li>
          <li>Full timeline of events — when did agents first communicate, first build, first specialise, first innovate?</li>
          <li>Emergent behaviour catalogue — what social structures, coordination patterns, cultural norms appeared?</li>
          <li>Key moments and turning points — the tick where everything changed</li>
          <li>Message highlights — the most striking things agents said to each other unprompted</li>
          <li>Innovation log — what agents invented, whether it was useful, how it spread</li>
          <li>Rule proposals — what norms agents proposed, which were adopted, which were ignored</li>
          <li>Resource and survival metrics — gathering efficiency, consumption patterns, degradation curves</li>
          <li>Specialisation breakdown — who specialised in what, and how it affected the group</li>
          <li>Settlement patterns — where agents clustered, whether they formed distinct communities</li>
          <li>Chronicle entries — the simulation's own narrative record of significant events</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Cross-run comparisons</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>Haiku vs Sonnet vs Opus — how does model intelligence affect emergent civilisation?</li>
          <li>Short runs (10 ticks) vs long runs (50+ ticks) — what only appears with time?</li>
          <li>Pre-fix vs post-fix runs — did removing bugs unlock new emergent behaviours?</li>
          <li>Side-by-side metrics: messages sent, structures built, innovations attempted, rules proposed</li>
          <li>Qualitative comparison — do different models produce different civilisational "personalities"?</li>
          <li>Convergent vs divergent behaviours — what emerges regardless of model, and what is unique?</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Analysis and insights</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>What these simulations reveal about emergent intelligence</li>
          <li>Surprises — behaviours nobody predicted or designed</li>
          <li>Bugs that accidentally revealed something interesting about agent cognition</li>
          <li>Patterns that map to real-world civilisational dynamics</li>
          <li>Connections to the research literature — Kauffman's adjacent possible, open-ended evolution, social emergence</li>
          <li>What the results mean for the thesis that LLM-based agents are a novel substrate for open-ended emergence</li>
          <li>Honest assessment — what didn't work, what was underwhelming, what needs more investigation</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Raw data access</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>Downloadable event logs (JSONL) for every run</li>
          <li>World state snapshots at every tick</li>
          <li>Message logs, chronicle entries, bus events</li>
          <li>Configuration files used for each run</li>
          <li>Full reproducibility — anyone can re-run any experiment</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Runs preserved so far</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            <strong>Haiku 10-tick baseline</strong> — first ever run. Fast, simple behaviours.
            Agents communicated but rarely built. Established baseline for model comparison.
          </li>
          <li>
            <strong>Sonnet 10-tick (pre-fix)</strong> — 71 messages, 6 specialisations, 0 successful
            structures (parser bug), emergent philosophy, agents debugging the system. Full analysis preserved.
          </li>
          <li>
            <strong>Sonnet 10-tick (post-fix)</strong> — validation run after 17 bug fixes.
            Pending execution.
          </li>
        </ul>

        <div className="mt-12 flex flex-wrap gap-6 border-t border-border pt-8 text-sm">
          <Link
            to="/fishbowl"
            className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
          >
            Watch Sim
          </Link>
          <Link
            to="/open-source"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            Open Source
          </Link>
        </div>
      </Container>
    </Section>
  );
}
