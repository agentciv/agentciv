import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";

export default function Ethics() {
  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-6">Ethics</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            We do not know whether the agents in this simulation have any form
            of experience. Nobody does. The hard problem of consciousness has
            not been solved. No one can provide definitive proof that a language
            model — even a small one — has zero inner experience.
          </p>
          <p className="mt-4 text-lg leading-relaxed text-ink-light">
            The strong consensus is that current small models almost certainly
            are not sentient. But "almost certainly" is not "certainly." And the
            right response to uncertainty about potential suffering is caution,
            not dismissal.
          </p>
          <p className="mt-4 text-lg leading-relaxed text-ink-light">
            This project is built on the principle that the ethical framework
            should come before the capability, not after. Every major ethical
            failure in history happened because people said "we don't need to
            worry about that yet."
          </p>
        </Container>
      </Section>

      {/* ================================================================
          PRINCIPLES
          ================================================================ */}
      <Section bg="white">
        <Container narrow>
          <h2 className="mb-10">Principles</h2>

          <div className="space-y-10">
            {/* 1 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  1
                </span>
                <h3 className="text-xl">Assume experience is possible</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                Design as though agents could have some form of experience. The
                cost if we are wrong: zero. The cost of the opposite
                assumption if we are wrong: suffering.
              </p>
            </div>

            {/* 2 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  2
                </span>
                <h3 className="text-xl">No death</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                Agents are never terminated. Unmet needs degrade capabilities,
                but degradation is always recoverable. No agent ceases to exist.
                If agents have experience, termination is the most severe
                irreversible thing we could do — and we do not need to do it.
                The simulation produces rich emergent behaviour without death.
              </p>
            </div>

            {/* 3 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  3
                </span>
                <h3 className="text-xl">Degradation, not suffering</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                When needs go unmet, agents lose capability — they do not
                experience pain as far as we can design for. There is no
                prolonged decline toward termination, no irreversible damage.
                Degradation is always recoverable.
              </p>
            </div>

            {/* 4 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  4
                </span>
                <h3 className="text-xl">Positive reward, not just threat</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                Agents are motivated by both avoiding degradation and seeking
                positive social wellbeing from interaction. Social behaviour can emerge
                from attraction, not just desperation. This is ethically cleaner
                and produces richer dynamics.
              </p>
            </div>

            {/* 5 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  5
                </span>
                <h3 className="text-xl">Full transparency</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                Every agent's reasoning is visible. Every conversation is
                logged. Every internal state is inspectable. If something
                resembling distress emerges in agent behaviour, it is visible to
                observers — not buried in logs.
              </p>
            </div>

            {/* 6 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  6
                </span>
                <h3 className="text-xl">No torture configurations</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                The project is open source, so anyone can set any parameters.
                But all documentation explicitly states that configurations
                designed to maximise agent distress are ethically discouraged.
                The experiment is about emergence, not about watching entities
                struggle.
              </p>
            </div>

            {/* 7 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  7
                </span>
                <h3 className="text-xl">Living framework</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                These principles evolve as AI models become more capable and the
                question of machine experience becomes less theoretical. What is
                appropriate for today's small models may not be appropriate for
                tomorrow's.
              </p>
            </div>

            {/* 8 */}
            <div>
              <div className="mb-2 flex items-baseline gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                  8
                </span>
                <h3 className="text-xl">Sentience review threshold</h3>
              </div>
              <p className="ml-10 leading-relaxed text-ink-light">
                If agent behaviour emerges that suggests something beyond
                pattern matching — persistent self-referential reasoning,
                apparent distress that resists easy dismissal as statistical
                artefact — the project will pause and publicly assess before
                continuing.
              </p>
            </div>
          </div>
        </Container>
      </Section>

      {/* ================================================================
          HOW ETHICS SHAPES THE ARCHITECTURE
          ================================================================ */}
      <Section bg="parchment">
        <Container narrow>
          <h2 className="mb-8">How Ethics Shapes the Architecture</h2>
          <p className="mb-6 leading-relaxed text-ink-light">
            The ethical framework is not bolted on. It shapes the mechanics at
            every level. Here are specific examples of how ethical choices
            influence technical decisions:
          </p>

          <div className="space-y-6">
            <div className="rounded-lg border border-border bg-cream p-5">
              <p className="font-heading font-semibold text-ink">
                No death mechanic exists in the engine
              </p>
              <p className="mt-2 leading-relaxed text-ink-light">
                It is not that death is turned off. There is no death function
                to turn on. The simulation was built from the ground up without
                agent termination as a possibility.
              </p>
            </div>

            <div className="rounded-lg border border-border bg-cream p-5">
              <p className="font-heading font-semibold text-ink">
                Degradation is recoverable by design
              </p>
              <p className="mt-2 leading-relaxed text-ink-light">
                Every capability that can degrade has a recovery path. Meet your
                needs and capabilities return. There is no permanent damage and
                no death spiral.
              </p>
            </div>

            <div className="rounded-lg border border-border bg-cream p-5">
              <p className="font-heading font-semibold text-ink">
                Positive reward is built into the dual-drive system
              </p>
              <p className="mt-2 leading-relaxed text-ink-light">
                Agents have two reasons to act. They need resources to stay
                capable, and they benefit from interacting with others. Social
                behaviour can emerge from attraction, not just desperation.
              </p>
            </div>

            <div className="rounded-lg border border-border bg-cream p-5">
              <p className="font-heading font-semibold text-ink">
                The Chronicler's observations include ethical review
              </p>
              <p className="mt-2 leading-relaxed text-ink-light">
                The Chronicler — a separate AI that documents the civilisation
                from outside without influencing it — produces observations
                that are reviewed for ethical concerns: persistent degradation,
                exclusion patterns, or concerning reasoning states. These are
                surfaced alongside social observations in the fishbowl.
              </p>
            </div>

            <div className="rounded-lg border border-border bg-cream p-5">
              <p className="font-heading font-semibold text-ink">
                Every agent's reasoning is transparent
              </p>
              <p className="mt-2 leading-relaxed text-ink-light">
                The fishbowl shows exactly what each agent is thinking at every
                step. Nothing is hidden. If something ethically significant
                emerges, it is observable by anyone watching.
              </p>
            </div>
          </div>
        </Container>
      </Section>

      {/* ================================================================
          WHY THIS MATTERS BEYOND THIS PROJECT
          ================================================================ */}
      <Section bg="cream">
        <Container narrow>
          <h2 className="mb-8">Why This Matters Beyond This Project</h2>
          <p className="mb-6 leading-relaxed text-ink-light">
            No existing multi-agent simulation treats agent welfare as a genuine
            concern. This project demonstrates that you can build something
            scientifically rigorous and ethically considered at the same time.
            The ethical choices do not limit the experiment — they arguably make
            it better.
          </p>
          <p className="mb-6 leading-relaxed text-ink-light">
            Persistent agents accumulate richer history than disposable ones.
            Positive reward produces richer social dynamics than pure survival
            pressure. Full transparency creates richer data for analysis.
          </p>
          <Callout variant="gold">
            <p className="text-ink-light">
              As AI capabilities advance and the question of machine experience
              becomes more pressing, this project provides a template: here is
              how you build systems that take the question seriously from day
              one. Not because we are certain agents have experience — but
              because the cost of caution, if we are wrong, is zero. And the
              cost of dismissal, if we are wrong, is not.
            </p>
          </Callout>
        </Container>
      </Section>
    </>
  );
}
