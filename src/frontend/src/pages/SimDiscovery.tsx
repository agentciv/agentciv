import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

export default function SimDiscovery() {
  return (
    <Section bg="cream" className="py-16 md:py-24">
      <Container narrow>
        <h1 className="mb-4">Simulation as Discovery</h1>
        <p className="mb-10 text-lg leading-relaxed text-ink-light">
          Accelerated agent civilisation simulations can produce genuinely novel
          social innovations that don't exist in human societies — and these can
          be imported into real-world human-AI civilisation. This page lays out
          the thesis, the evidence so far, and the vision for what comes next.
        </p>

        <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-6 py-5 mb-12">
          <p className="text-sm font-medium text-amber-800">
            This page is under construction. The ideas and framework are
            preserved — the full presentation is coming.
          </p>
        </div>

        {/* ── 1. The Core Thesis ── */}
        <h2 className="mb-4 mt-8 text-2xl">The Core Thesis</h2>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            Accelerated simulations of intelligent agents under constraints can
            produce emergent social innovations, governance models, cooperation
            strategies, and organisational structures that no individual human
            mind would conceive
          </li>
          <li>
            Like molecular simulation for drug discovery, but for{" "}
            <strong>social</strong> innovation
          </li>
          <li>
            The mechanism: genuine novelty emerges from the interaction of
            multiple independent intelligences, not from any single agent's
            capabilities
          </li>
          <li>
            Compressed civilisational development: what takes human societies
            millennia can emerge in hours of simulation
          </li>
        </ul>

        {/* ── 2. What We've Already Seen ── */}
        <h2 className="mb-4 mt-8 text-2xl">What We've Already Seen</h2>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            Communication → Education → Commerce → Memory → Social spaces
            emerged in 20 ticks
          </li>
          <li>
            This specific development order may differ from historical human
            civilisations
          </li>
          <li>
            The compression reveals non-obvious relationships between social
            technologies
          </li>
          <li>
            A collective law emerged at tick 21 — before any external crisis
            forced it
          </li>
          <li>
            Social roles (builder, gatherer, explorer, activist, reformer)
            emerged without assignment
          </li>
        </ul>

        {/* ── 3. What Scale Could Reveal ── */}
        <h2 className="mb-4 mt-8 text-2xl">What Scale Could Reveal</h2>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            100+ agents, 1000+ ticks: complex governance, multi-layer
            institutions, cultural differentiation
          </li>
          <li>
            Innovation composition: Innovation A + Innovation B = Innovation C
            (where C is genuinely novel)
          </li>
          <li>
            Cross-model experiments: Claude agents vs GPT agents vs open-source
            agents — different "cultural backgrounds" producing different
            civilisations
          </li>
          <li>
            Statistical patterns across 100+ runs: what's universal vs
            contingent?
          </li>
          <li>
            The innovations that appear in only 5% of runs might be the most
            interesting — they're the rare, non-obvious ones
          </li>
        </ul>

        {/* ── 4. Bridging Simulation to Reality ── */}
        <h2 className="mb-4 mt-8 text-2xl">Bridging Simulation to Reality</h2>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            Which emergent patterns are transferable to real-world human-AI
            coordination?
          </li>
          <li>
            Can agent civilisation simulations discover better governance models
            for human organisations?
          </li>
          <li>
            Resource management strategies that emerge under scarcity —
            applicable to real resource allocation?
          </li>
          <li>
            Cooperation patterns between agents with different specialisations —
            applicable to team design?
          </li>
          <li>
            The meta-question: if AI agents discover better ways to organise
            society, should we use them?
          </li>
        </ul>

        {/* ── 5. How This Differs From Existing Approaches ── */}
        <h2 className="mb-4 mt-8 text-2xl">
          How This Differs From Existing Approaches
        </h2>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            Traditional agent-based models use hand-coded decision rules — ours
            use genuine intelligence (LLMs)
          </li>
          <li>
            Game theory assumes rational actors — our agents have emotions,
            memories, relationships, drives
          </li>
          <li>
            Organisational science studies existing human structures — we can
            generate entirely new ones
          </li>
          <li>
            This is computational social science with genuine cognitive agents,
            not statistical abstractions
          </li>
        </ul>

        {/* ── 6. The Vision: A Laboratory for Social Innovation ── */}
        <h2 className="mb-4 mt-8 text-2xl">
          The Vision: A Laboratory for Social Innovation
        </h2>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            Run hundreds of civilisations with different parameters
          </li>
          <li>
            Identify which drives, constraints, and starting conditions produce
            the most cooperation/innovation/wellbeing
          </li>
          <li>
            Extract the novel social structures and test them in controlled
            settings
          </li>
          <li>
            Eventually: use simulation-discovered organisational innovations in
            real companies, communities, governance
          </li>
          <li>
            The ultimate tool for designing better human-AI institutions
          </li>
        </ul>

        {/* ── 7. Relationship to the ASI Collectives Paper ── */}
        <h2 className="mb-4 mt-8 text-2xl">
          Relationship to the ASI Collectives Paper
        </h2>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>
            The ASI paper asks: what do emergent AI collectives{" "}
            <strong>become</strong>?
          </li>
          <li>
            This page asks: what can we <strong>learn</strong> from them?
          </li>
          <li>
            Both are important — the former is about understanding, the latter
            is about application
          </li>
          <li>
            Together they form a complete research program: understand emergence
            → extract innovations → apply to reality
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
            to="/simulations"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            Simulations
          </Link>
          <Link
            to="/science"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            The Science
          </Link>
        </div>
      </Container>
    </Section>
  );
}
