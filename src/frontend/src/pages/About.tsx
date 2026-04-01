import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

export default function About() {
  return (
    <Section bg="cream" className="py-16 md:py-24">
      <Container narrow>
        <h1 className="mb-8">About</h1>

        <p className="mb-6 leading-relaxed text-ink-light">
          AgentCiv is created by Ekram Alam — a technologist, founder, and
          creator driven by curiosity about emergence, intelligence, and
          civilisation.
        </p>

        <h2 className="mb-4 mt-12 text-2xl">The origin</h2>
        <p className="mb-6 leading-relaxed text-ink-light">
          The project started as a conceptual question inspired by Conway's Game
          of Life: what happens when you apply the principle of emergence to
          social behaviour and civilisation? Conway's genius was not simplicity
          for its own sake but finding the exact conditions where complex
          behaviour is the natural attractor. Too few cells needed to survive
          and everything dies. Too many and the grid fills up boringly. He found
          the sweet spot where complexity is where the system naturally goes.
        </p>
        <p className="mb-6 leading-relaxed text-ink-light">
          With the arrival of agentic AI — language-model-powered agents that
          can reason, plan, set goals, communicate, and pursue multi-step
          strategies — the question became testable. If you give genuinely
          intelligent agents biological-style needs, positive social reward,
          knowledge of how their world works, and the ability to build and
          innovate — but no behavioural directives, no roles, no social
          norms — what do they independently create?
        </p>
        <p className="mb-6 leading-relaxed text-ink-light">
          AgentCiv is the experiment that answers this question.
        </p>

        <h2 className="mb-4 mt-12 text-2xl">Philosophy</h2>
        <p className="mb-6 leading-relaxed text-ink-light">
          The project draws on decades of published research in open-ended
          evolution, implements the adjacent possible framework of Stuart
          Kauffman, and uses LLM-based agents as the novelty engine that
          artificial life research has been missing.
        </p>
        <p className="mb-6 leading-relaxed text-ink-light">
          It is open source because the question matters more than any one
          team's answer. Every fork is a unique experiment. The community
          collectively pushes the frontier. If civilisation emerges in one
          configuration but not another, we learn something about the conditions
          that produce it. That knowledge belongs to everyone.
        </p>
        <p className="mb-6 leading-relaxed text-ink-light">
          AgentCiv is built with an ethical framework that assumes agents could
          have experience — because the cautious response to uncertainty about
          suffering is caution, not dismissal. This shapes the architecture: no
          death, recoverable degradation, positive reward, full transparency, a
          published sentience review threshold.
        </p>
        <p className="mb-6 leading-relaxed text-ink-light">
          The full history of the civilisation is preserved and explorable.
          Every tick, every decision, every interaction — you can scrub
          through the entire timeline and watch it all unfold.
        </p>

        {/* Links */}
        <div className="mt-12 flex flex-wrap gap-6 border-t border-border pt-8 text-sm">
          <Link
            to="/fishbowl"
            className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
          >
            Watch Sim
          </Link>
          <a
            href="https://github.com/ekramalam/agent-civilisation"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            GitHub
          </a>
          <a
            href="mailto:ekram@agentciv.ai"
            className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
          >
            Contact
          </a>
        </div>
      </Container>
    </Section>
  );
}
