import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

// ---------------------------------------------------------------------------
// Paper definitions
// ---------------------------------------------------------------------------

interface Paper {
  id: string;
  title: string;
  type: string;
  author: string;
  date: string;
  abstract: string;
  sections: string[];
  githubPath: string;
  highlight?: boolean;
}

const PAPERS: Paper[] = [
  {
    id: "maslow-machines",
    title: "Maslow Machines: Emergent Civilisation in LLM Agent Societies Under Intrinsic Drive Hierarchies",
    type: "Empirical Research Paper",
    author: "Mark E. Mala",
    date: "April 2026",
    abstract:
      "We present results from AgentCiv, a simulation in which 12 LLM-powered agents (Claude Sonnet) equipped with Maslow-inspired intrinsic drives but zero instructions spontaneously develop communication, specialisation, innovation, governance, and collective flourishing over 70 time steps. The simulation produces 60 structures, 12 agent-invented innovations, and a complete traversal of the Maslow hierarchy from physiological needs to self-actualisation. We identify three emergent eras — a survival trap (ticks 0-50), an emergence explosion (50-60), and sustained flourishing (60-70) — and document an innovation-implementation gap where agents discover solutions they cannot yet execute.",
    sections: [
      "Introduction & Motivation",
      "Related Work",
      "System Architecture",
      "Experimental Design",
      "Results: Three Eras of Emergence",
      "Results: Innovation Dynamics",
      "Results: Existence Disclosure",
      "Discussion & Limitations",
      "8 Data-Driven Figures",
    ],
    githubPath: "paper/maslow_machines.md",
    highlight: true,
  },
  {
    id: "agent-teams-civilisations",
    title: "From Agent Teams to Agent Civilisations: Emergent Collective Intelligence as a New Dimension in AI",
    type: "Whitepaper I — Conceptual Framework",
    author: "Mark E. Mala",
    date: "March 2026",
    abstract:
      "The dominant paradigm in multi-agent AI is designed collaboration: architects assign roles, define coordination protocols, and structure agent teams. This paper proposes that designed collaboration represents one stage in a broader trajectory — from isolated AI models to self-organising societies of generally intelligent agents. We present a four-stage framework, identify LLM-based agentic AI as a novel substrate for open-ended emergence, propose six design principles for unbounded civilisational complexity, and present AgentCiv as a first open-source experiment.",
    sections: [
      "Four-Stage Framework",
      "LLM Agents as Novel Substrate",
      "Six Design Principles",
      "Ethics & Alignment",
      "Open-Ended Evolution Theory",
    ],
    githubPath: "paper/from_agent_teams_to_agent_civilisations.md",
  },
  {
    id: "innovation-engine",
    title: "Civilisation as Innovation Engine: How Agent Societies Generate Unbounded Novelty",
    type: "Whitepaper II — Innovation Theory",
    author: "Mark E. Mala",
    date: "March 2026",
    abstract:
      "We examine how multi-agent civilisations function as innovation engines, producing novel social technologies through a combination of individual creativity and collective evaluation. Drawing on Kauffman's adjacent possible theory, we analyse how the AgentCiv composition system enables agents to combine existing innovations into novel structures. We document 12 agent-invented innovations including Knowledge Hubs, Memory Gardens, and Resource Exchanges — social infrastructure concepts the agents were never told about.",
    sections: [
      "The Adjacent Possible",
      "Innovation as Collective Process",
      "Composition Mechanics",
      "Innovation-Implementation Gap",
      "Implications for Open-Ended Evolution",
    ],
    githubPath: "paper/civilisation_as_innovation_engine.md",
  },
  {
    id: "computational-org-theory",
    title: "Computational Organisational Theory: Using Agent Civilisations to Design Better Institutions",
    type: "Whitepaper III — Applied Theory",
    author: "Mark E. Mala",
    date: "Forthcoming",
    abstract:
      "This paper will explore how agent civilisation simulations can serve as a laboratory for organisational design — running hundreds of variants with different org structures, incentive systems, and governance models to discover what produces the best outcomes. Connected to the AgentCiv Engine developer tool.",
    sections: [],
    githubPath: "",
  },
];

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export default function Whitepaper() {
  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-4">Research Papers</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            Three complete papers documenting the AgentCiv experiment — from
            theoretical framework through empirical results. All authored by
            Mark E. Mala under open access. A fourth paper is forthcoming.
          </p>
        </Container>
      </Section>

      {/* Papers */}
      <Section bg="cream" className="pt-0">
        <Container narrow>
          <div className="space-y-8">
            {PAPERS.map((paper) => (
              <div
                key={paper.id}
                className={`rounded-xl border bg-warm-white px-6 py-6 md:px-8 md:py-8 ${
                  paper.highlight ? "border-sky/40 ring-1 ring-sky/20" : "border-border"
                }`}
              >
                {/* Type badge */}
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-3 py-0.5 text-xs font-medium ${
                      paper.highlight
                        ? "bg-sky/10 text-sky"
                        : paper.githubPath
                          ? "bg-gold/10 text-gold"
                          : "bg-ink-muted/10 text-ink-muted"
                    }`}
                  >
                    {paper.type}
                  </span>
                  {!paper.githubPath && (
                    <span className="rounded-full bg-parchment px-3 py-0.5 text-xs font-medium text-ink-muted">
                      Forthcoming
                    </span>
                  )}
                </div>

                {/* Title */}
                <h2 className="mb-2 text-xl font-semibold leading-snug text-ink">
                  {paper.title}
                </h2>
                <p className="mb-4 text-sm text-ink-muted">
                  {paper.author} · {paper.date}
                </p>

                {/* Abstract */}
                <p className="mb-5 text-sm leading-relaxed text-ink-light">
                  {paper.abstract}
                </p>

                {/* Sections */}
                {paper.sections.length > 0 && (
                  <div className="mb-5">
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">
                      Contents
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {paper.sections.map((s) => (
                        <span
                          key={s}
                          className="rounded-full border border-border-light bg-cream px-3 py-1 text-xs text-ink-muted"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                {paper.githubPath && (
                  <div className="flex flex-wrap gap-3">
                    <a
                      href={`https://github.com/agentciv/agentciv/blob/main/${paper.githubPath}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-full bg-ink px-5 py-2 text-sm font-semibold text-cream transition-all hover:bg-ink/90 hover:shadow-md"
                    >
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M8 2v9M4 7l4 4 4-4M2 13h12" />
                      </svg>
                      Read on GitHub
                    </a>
                    {paper.highlight && (
                      <Link
                        to="/discovery"
                        className="inline-flex items-center gap-1 rounded-full border border-border px-5 py-2 text-sm font-semibold text-ink transition-colors hover:bg-parchment"
                      >
                        View findings
                      </Link>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Paper figures preview */}
          <div className="mt-12">
            <h2 className="mb-4 text-xl font-semibold">Paper Figures</h2>
            <p className="mb-6 text-sm text-ink-light">
              8 data-driven figures generated from real simulation data. All
              embedded in the Maslow Machines paper and available separately.
            </p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { n: 1, label: "Comparison" },
                { n: 2, label: "Timeline" },
                { n: 3, label: "Wellbeing" },
                { n: 4, label: "Growth" },
                { n: 5, label: "Specialisation" },
                { n: 6, label: "Innovation" },
                { n: 7, label: "Self-Theory" },
                { n: 8, label: "Final Words" },
              ].map(({ n, label }) => (
                <a
                  key={n}
                  href={`https://github.com/agentciv/agentciv/blob/main/paper/figures/fig${n}_${label.toLowerCase()}.png`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-lg border border-border bg-warm-white p-3 text-center text-sm transition-colors hover:bg-parchment"
                >
                  <p className="font-mono text-xs text-ink-muted">Fig {n}</p>
                  <p className="font-medium text-ink">{label}</p>
                </a>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div className="mt-12 flex flex-wrap gap-4 border-t border-border pt-8 text-sm">
            <Link
              to="/discovery"
              className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
            >
              Key Findings
            </Link>
            <Link
              to="/science"
              className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
            >
              The Science
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
    </>
  );
}
