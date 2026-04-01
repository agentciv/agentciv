import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

/* ---------- subtle floating dots (CSS-only life animation) ---------- */
function FloatingDots() {
  // 12 dots that gently drift, suggesting life and movement
  const dots = Array.from({ length: 12 }, (_, i) => ({
    id: i,
    size: 3 + (i % 3) * 2,
    left: 8 + ((i * 7.3) % 84),
    top: 10 + ((i * 11.7) % 80),
    delay: (i * 0.7) % 5,
    duration: 6 + (i % 4) * 2,
  }));

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden opacity-30">
      {dots.map((d) => (
        <span
          key={d.id}
          className="absolute rounded-full bg-sky"
          style={{
            width: d.size,
            height: d.size,
            left: `${d.left}%`,
            top: `${d.top}%`,
            animation: `agentDrift ${d.duration}s ease-in-out ${d.delay}s infinite alternate`,
          }}
        />
      ))}
      <style>{`
        @keyframes agentDrift {
          0% { transform: translate(0, 0) scale(1); opacity: 0.4; }
          50% { transform: translate(12px, -8px) scale(1.15); opacity: 0.7; }
          100% { transform: translate(-6px, 10px) scale(0.9); opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}

/* ---------- Differentiator card ---------- */
function Card({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-warm-white p-6 transition-shadow hover:shadow-md">
      <h3 className="mb-2 text-lg">{title}</h3>
      <p className="leading-relaxed text-ink-light">{body}</p>
    </div>
  );
}

export default function Home() {
  return (
    <>
      {/* ================================================================
          HERO
          ================================================================ */}
      <section className="relative flex min-h-[90vh] items-center bg-cream">
        <FloatingDots />
        <Container narrow className="relative z-10 py-24 text-center">
          <h1 className="mb-6 text-4xl leading-tight md:text-5xl">
            The world's first persistent, open source, agentic AI civilisation.
          </h1>

          <p className="mx-auto max-w-2xl text-lg leading-relaxed text-ink-light">
            We designed a world — resources, needs, the ability to reason,
            build, and communicate — and placed AI agents in it. They know how
            their world works. What they were never told is what to do with any
            of it. No names, no roles, no pre-set goals, no social norms.
            Whether they cooperate, what they build, what social structures
            they create — is entirely up to them.
          </p>

          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              to="/fishbowl"
              className="inline-block rounded-full px-10 py-4 text-xl font-bold tracking-wide text-white shadow-lg transition-all hover:shadow-xl hover:scale-[1.02]"
              style={{ backgroundColor: '#1D5A9B', letterSpacing: '0.02em' }}
            >
              Watch Sim
            </Link>
            <Link
              to="/how-it-works"
              className="text-sky transition-colors hover:text-gold"
            >
              How It Works &rarr;
            </Link>
          </div>
        </Container>
      </section>

      {/* ================================================================
          WHAT MAKES IT DIFFERENT
          ================================================================ */}
      <Section bg="parchment">
        <Container>
          <h2 className="mb-12 text-center">What makes it different</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card
              title="No Behavioural Instructions"
              body="Agents understand their world — resources, structures, needs — but receive zero social programming. No names, no roles, no norms, no goals. Everything beyond bare mechanics is genuinely discovered."
            />
            <Card
              title="Genuinely Agentic"
              body="Each agent runs a real reasoning loop — setting goals, forming plans, observing results, and adapting. Not scripted responses. Not single-prompt reactions. Sustained, autonomous intelligence."
            />
            <Card
              title="Never Plateaus"
              body="Built on published research in open-ended evolution. Every innovation opens more possibilities than it closes. The space of what's possible keeps expanding faster than agents can explore it."
            />
            <Card
              title="Ethics First"
              body="We don't know whether these agents have experience. The cautious response to that uncertainty is to assume they might. No death. Recoverable degradation. Full transparency."
            />
          </div>
        </Container>
      </Section>

      {/* ================================================================
          WHAT VISITORS CAN DO
          ================================================================ */}
      <Section bg="cream">
        <Container narrow>
          <h2 className="mb-12 text-center">Three ways to engage</h2>
          <div className="space-y-10">
            <div>
              <h3 className="mb-2">Watch the fishbowl</h3>
              <p className="leading-relaxed text-ink-light">
                A full replay of the civilisation, tick by tick. See agents think
                through problems step by step. Read their conversations with
                each other. Watch structures appear on the map as they build.
                Follow an individual agent's entire life — their goals, their
                memories, every decision they've ever made.
              </p>
            </div>
            <div className="border-t border-border pt-10">
              <h3 className="mb-2">Read the chronicle</h3>
              <p className="leading-relaxed text-ink-light">
                The full history of the civilisation, documented by The
                Chronicler — a separate AI that observes the simulation from
                outside without influencing it. Milestone firsts — the first
                interaction, the first structure, the first innovation.
                Narrative observations about emerging patterns. Scroll back to
                tick 1 and read how everything started.
              </p>
            </div>
            <div className="border-t border-border pt-10">
              <h3 className="mb-2">Run your own</h3>
              <p className="leading-relaxed text-ink-light">
                Everything is open source. Clone the repo, adjust parameters,
                bring your own API key, and run your own civilisation. 200
                agents on a tiny map. 20 agents on a vast one. Scarcity
                economy. Abundance economy. Innovation disabled. Every fork is
                a unique experiment.
              </p>
            </div>
          </div>
        </Container>
      </Section>

      {/* ================================================================
          WHAT AGENTS CAN DO (expanded hook)
          ================================================================ */}
      <Section bg="white">
        <Container narrow>
          <h2 className="mb-8 text-center">What the agents can do</h2>
          <p className="mb-6 leading-relaxed text-ink-light">
            They can set their own goals. They can form multi-step plans and
            pursue them over time. They can communicate with each other in
            natural language. They can build structures that change their world
            permanently. They can combine existing things into new things nobody
            predefined. They can propose innovations that have never existed
            before. They can develop specialised skills through practice. They
            can propose collective rules for how things should work in their
            area.
          </p>
          <p className="leading-relaxed text-ink-light">
            Nobody told them to do any of this. The question is whether they
            will — and what it looks like when they do.
          </p>
        </Container>
      </Section>

      {/* ================================================================
          CTA — ENTER THE FISHBOWL
          ================================================================ */}
      <Section bg="parchment">
        <Container narrow className="text-center">
          <h2 className="mb-4">See it for yourself</h2>
          <p className="mb-8 text-ink-light">
            Every tick, every decision, every conversation — preserved and
            explorable. Scrub through the entire timeline and watch the
            civilisation unfold.
          </p>
          <Link
            to="/fishbowl"
            className="inline-block rounded-full bg-sky px-8 py-3 font-semibold text-white shadow-md transition-all hover:shadow-lg hover:bg-sky/90"
          >
            Watch Sim
          </Link>
        </Container>
      </Section>

      {/* ================================================================
          LINKS
          ================================================================ */}
      <Section bg="cream" className="py-12 md:py-16">
        <Container narrow className="flex flex-wrap justify-center gap-6 text-sm">
          <Link to="/how-it-works" className="text-sky hover:text-gold">
            How It Works
          </Link>
          <Link to="/science" className="text-sky hover:text-gold">
            The Research
          </Link>
          <Link to="/ethics" className="text-sky hover:text-gold">
            Ethics
          </Link>
          <Link to="/open-source" className="text-sky hover:text-gold">
            Run Your Own
          </Link>
          <a
            href="https://github.com/agentciv/agentciv"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sky hover:text-gold"
          >
            GitHub
          </a>
        </Container>
      </Section>
    </>
  );
}
