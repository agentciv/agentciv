import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

export default function Whitepaper() {
  return (
    <Section bg="cream" className="py-16 md:py-24">
      <Container narrow>
        <h1 className="mb-4">Whitepaper</h1>
        <p className="mb-10 text-lg leading-relaxed text-ink-light">
          The theoretical foundation behind AgentCiv — a peer-reviewed-quality
          paper proposing emergent agent civilisation as a new dimension in
          artificial intelligence research.
        </p>

        {/* Paper header */}
        <div className="mb-10 rounded-xl border border-border bg-warm-white px-8 py-8">
          <h2 className="mb-2 text-xl leading-snug">
            From Agent Teams to Agent Civilisations: Emergent Collective
            Intelligence as a New Dimension in Artificial Intelligence
          </h2>
          <p className="mb-4 text-sm text-ink-light">
            Mark E. Mala &middot; March 2026
          </p>
          <p className="leading-relaxed text-ink-light">
            The dominant paradigm in multi-agent AI is designed collaboration:
            architects assign roles, define coordination protocols, and structure
            agent teams. This paper proposes that designed collaboration
            represents one stage in a broader trajectory — from isolated AI
            models to self-organising societies of generally intelligent agents.
            We present a four-stage framework, identify LLM-based agentic AI as
            a novel substrate for open-ended emergence, propose six design
            principles for unbounded civilisational complexity, and present
            AgentCiv as a first open-source experiment.
          </p>

          {/* Download button — placeholder until PDF is generated */}
          <div className="mt-6">
            <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-5 py-4">
              <p className="text-sm font-medium text-amber-800">
                PDF download coming soon. The paper is complete — we are
                finalising the formatted version.
              </p>
            </div>
            {/*
            <a
              href="/agentciv_whitepaper.pdf"
              download
              className="inline-flex items-center gap-2 rounded-full bg-ink px-6 py-2.5 font-semibold text-cream transition-all hover:bg-ink/90 hover:shadow-md"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 2v9M4 7l4 4 4-4M2 13h12" />
              </svg>
              Download PDF
            </a>
            */}
          </div>
        </div>

        <h2 className="mb-4 mt-12 text-2xl">What the paper covers</h2>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Core thesis</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>A four-stage framework: Narrow AI → General-Purpose AI → Specialised General Intelligence Teams → Emergent Agent Civilisation</li>
          <li>Emergent civilisation as a complement to designed agent teams, not a replacement</li>
          <li>Individual intelligence and collective complexity rise together — each amplifying the other</li>
          <li>The trajectory beyond: towards collective superintelligence</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Theoretical foundations</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>Why emergence complements design — adaptive structure, novel solutions, scalable complexity</li>
          <li>Open-ended evolution (OEE) research — Bedau, Packard, Taylor, Banzhaf, and the conditions for unbounded complexity</li>
          <li>Stuart Kauffman's adjacent possible — how new possibilities emerge from combinations of existing elements</li>
          <li>Why previous artificial life systems plateaued and how LLM-based agents overcome those limitations</li>
          <li>Whether LLM-generated novelty is "genuine" — and why the question matters less than the evidence</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Design principles</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>Six principles for systems capable of unbounded civilisational complexity growth</li>
          <li>Environmental pressure without prescription — drives without directives</li>
          <li>The innovation engine — open-ended creation evaluated by other AI</li>
          <li>The composition engine — Kauffman's adjacent possible as a concrete mechanism</li>
          <li>Collective rule formation — governance that emerges from agent proposals</li>
          <li>Cultural transmission — knowledge that persists and evolves</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Ethics and alignment</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>Alignment considerations unique to emergent multi-agent systems</li>
          <li>The moral status question — treating agents as if they could have experience</li>
          <li>No death, recoverable degradation, positive reward — ethical architecture</li>
          <li>Full transparency and observability as a design requirement</li>
          <li>Published sentience review threshold</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">AgentCiv as evidence</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>Preliminary results — spontaneous social coordination, persistent partnerships, division of labour, cooperative planning</li>
          <li>Architecture walkthrough — the simulation engine, agentic loop, innovation system, composition engine</li>
          <li>What emerged in the first simulation cycles and what it means</li>
          <li>Honest assessment of limitations and open questions</li>
        </ul>

        <h3 className="mb-3 mt-8 text-xl font-semibold">Implications</h3>
        <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
          <li>What emergent civilisation means for AGI and ASI development</li>
          <li>The relationship between individual scaling and collective scaling</li>
          <li>New research directions this opens up</li>
          <li>Why this matters beyond AI — what it tells us about civilisation itself</li>
        </ul>

        <div className="mt-12 flex flex-wrap gap-6 border-t border-border pt-8 text-sm">
          <Link
            to="/science"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            The Science
          </Link>
          <Link
            to="/simulations"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            Simulations
          </Link>
          <a
            href="https://github.com/agentciv/agentciv"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            GitHub
          </a>
        </div>
      </Container>
    </Section>
  );
}
