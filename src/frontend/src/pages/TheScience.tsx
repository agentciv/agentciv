import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";

export default function TheScience() {
  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-6">The Science Behind Open-Ended AI Civilisation</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            This page explains the research foundation: why every previous
            simulation plateaus, the six mechanisms that prevent it here, and
            the published work this project is built on.
          </p>
        </Container>
      </Section>

      {/* ================================================================
          PART 1 — WHY IT NEVER PLATEAUS (accessible)
          ================================================================ */}
      <Section bg="white">
        <Container narrow>
          <h2 className="mb-8">Part 1: Why It Never Plateaus</h2>

          {/* The problem */}
          <h3 className="mb-4">The problem with every previous simulation</h3>
          <p className="mb-4 leading-relaxed text-ink-light">
            Every artificial civilisation simulation that has ever been built
            eventually hits equilibrium. Agents find a stable arrangement and
            stay there. The system stops producing novelty. This has been the
            central unsolved problem in artificial life research for thirty
            years.
          </p>
          <p className="mb-8 leading-relaxed text-ink-light">
            The reason is structural: previous systems have a finite possibility
            space. There are only so many things that can exist, only so many
            configurations to explore. Once the interesting regions are
            exhausted, the system has nothing new to discover. Conway's Game of
            Life has infinite state space but fixed rules — the types of things
            that can exist are limited. Gliders are discovered early and remain
            gliders forever. Traditional artificial life systems use random
            mutation and selection, which can only produce novelty that random
            variation happens to stumble upon. Eventually, they have explored
            everything accessible and plateau.
          </p>

          {/* The six mechanisms */}
          <h3 className="mb-6">How this system avoids plateau</h3>
          <p className="mb-8 leading-relaxed text-ink-light">
            This system is designed, based on published research in open-ended
            evolution, to have a possibility space that expands faster than it
            can be explored. Six mechanisms work together:
          </p>

          <div className="space-y-8">
            {/* Mechanism 1 */}
            <div>
              <h4 className="mb-2 font-heading text-lg font-semibold text-ink">
                1. The Expanding Adjacent Possible
              </h4>
              <p className="leading-relaxed text-ink-light">
                Every new structure, composition, or innovation makes more new
                things possible. A new structure type can be combined with every
                existing structure type, creating a combinatorial explosion of
                potential compositions. Each discovery opens a new frontier of
                things that are now reachable but were not before.
              </p>
            </div>

            {/* Mechanism 2 */}
            <div>
              <h4 className="mb-2 font-heading text-lg font-semibold text-ink">
                2. Unbounded Innovation
              </h4>
              <p className="leading-relaxed text-ink-light">
                Agents can propose things that do not exist in any recipe list.
                The possibility space is not limited to predefined
                combinations — it includes anything intelligence can conceive.
                Each innovation adds a new component that can combine with
                everything else, further expanding the space.
              </p>
            </div>

            {/* Mechanism 3 */}
            <div>
              <h4 className="mb-2 font-heading text-lg font-semibold text-ink">
                3. Solutions Create Problems
              </h4>
              <p className="leading-relaxed text-ink-light">
                Building a settlement solves shelter but creates crowding that
                depletes resources faster. Success breeds new challenges.
                Governance creates power dynamics. Concentration creates
                communication overhead. Every advancement opens a new problem
                space that demands further innovation.
              </p>
            </div>

            {/* Mechanism 4 */}
            <div>
              <h4 className="mb-2 font-heading text-lg font-semibold text-ink">
                4. Knowledge Compounds
              </h4>
              <p className="leading-relaxed text-ink-light">
                Knowledge A plus Knowledge B can produce Innovation C. Each
                piece of knowledge an agent holds can combine with every other
                piece. As agents accumulate more knowledge, the potential for
                combinatorial insight grows. Knowledge becomes the most valuable
                resource in the civilisation.
              </p>
            </div>

            {/* Mechanism 5 */}
            <div>
              <h4 className="mb-2 font-heading text-lg font-semibold text-ink">
                5. Environmental Co-evolution
              </h4>
              <p className="leading-relaxed text-ink-light">
                The world changes in response to what agents do. Heavy resource
                extraction degrades terrain. Dense building changes local
                dynamics. The environment is not a static stage — it responds
                and creates new conditions that force new adaptations.
              </p>
            </div>

            {/* Mechanism 6 */}
            <div>
              <h4 className="mb-2 font-heading text-lg font-semibold text-ink">
                6. Agents Can Reason
              </h4>
              <p className="leading-relaxed text-ink-light">
                This is the key advantage over every previous artificial life
                system. Previous systems relied on random mutation for
                novelty — slow, wasteful, and limited to what chance produces.
                These agents can think. They can identify a problem, reason
                about what would solve it, and propose a solution. Directed,
                intelligent innovation rather than random variation. This is the
                novelty engine that the field of artificial life has been
                missing.
              </p>
            </div>
          </div>

          <Callout variant="gold">
            <p className="text-ink-light">
              The result: a system where the frontier of what is possible keeps
              expanding faster than agents can explore it. There is always more
              to discover, always more complexity to build. The system cannot
              exhaust its own potential.
            </p>
          </Callout>
        </Container>
      </Section>

      {/* ================================================================
          PART 2 — RESEARCH FOUNDATION (academic depth)
          ================================================================ */}
      <Section bg="parchment">
        <Container narrow>
          <h2 className="mb-8">Part 2: The Research Foundation</h2>

          {/* OEE */}
          <h3 className="mb-4">Open-Ended Evolution</h3>
          <p className="mb-4 leading-relaxed text-ink-light">
            This project draws on decades of published research in open-ended
            evolution (OEE) — a field within artificial life that studies how
            systems can produce ever-increasing complexity without reaching
            equilibrium. OEE is considered the holy grail of artificial life
            research. Life on Earth has been doing it for billions of years —
            evolving from single cells to human civilisation — but no artificial
            system has ever replicated this property.
          </p>
          <p className="mb-4 leading-relaxed text-ink-light">
            The key requirement, established across the OEE literature published
            through MIT Press and the International Conference on Artificial
            Life: the possibility space must be unbounded. If there is a finite
            set of things that can exist, the system will eventually explore all
            of them and stop innovating. True open-endedness requires that the
            space of what is possible keeps expanding.
          </p>
          <p className="mb-8 leading-relaxed text-ink-light">
            In formal terms, the system must be non-ergodic: it must not visit
            all its possible states over any reasonable time period, because new
            possible states are being created faster than they can be explored.
          </p>

          {/* Adjacent Possible */}
          <h3 className="mb-4">Kauffman's Adjacent Possible</h3>
          <p className="mb-4 leading-relaxed text-ink-light">
            Stuart Kauffman, a MacArthur Fellow and theoretical biologist who
            has published over 350 papers and six books on complexity and the
            origins of life, introduced the concept of the "adjacent
            possible" — the set of all things that could come into existence
            given what currently exists.
          </p>
          <p className="mb-4 leading-relaxed text-ink-light">
            A stone age society's adjacent possible includes bronze tools
            (because the raw materials and basic smelting are reachable from
            current knowledge) but not computer chips (too many intermediate
            steps away). Each innovation expands the adjacent possible. Bronze
            tools make iron smelting reachable. Iron makes steel reachable.
            Steel makes industrial machinery reachable. The possibility space
            does not grow linearly — it expands combinatorially, because each
            new component can combine with every existing component.
          </p>
          <p className="mb-4 leading-relaxed text-ink-light">
            Kauffman argues that complex evolving systems maximise their rate of
            exploration of the adjacent possible — they expand into what is
            newly possible as fast as they can without destroying their own
            organisation.
          </p>
          <Callout variant="sage">
            <p className="text-ink-light">
              This project implements the adjacent possible through its
              composition and innovation systems. Each new structure type can
              combine with every existing type. Each innovation adds a new
              element to the combinatorial space. The possibility space expands
              faster than agents can explore it — which means there is always
              more to discover.
            </p>
          </Callout>

          {/* Why LLMs Change Everything */}
          <h3 className="mb-4 mt-12">Why LLMs Change Everything</h3>
          <p className="mb-4 leading-relaxed text-ink-light">
            Every previous attempt at open-ended evolution used simple
            computational substrates — cellular automata, genetic algorithms,
            neural networks evolving through random mutation. They all plateau
            because their agents are not intelligent enough to generate
            genuinely novel solutions. They rely on random variation filtered by
            selection, which is slow and limited to what chance produces.
          </p>
          <p className="mb-4 leading-relaxed text-ink-light">
            This project puts genuinely intelligent agents — LLM-based agents
            that can reason, plan, and propose — into the OEE framework. The
            language model is the novelty engine that the field has been
            searching for. An agent that faces a problem can reason about what
            would solve it and propose a solution that has never existed. That
            is not random variation — it is directed, intelligent innovation.
          </p>

          {/* Undecidability */}
          <h3 className="mb-4 mt-12">The Undecidability Condition</h3>
          <p className="mb-4 leading-relaxed text-ink-light">
            A mathematical proof by Hernandez-Orozco, Hernandez-Quiroz, and
            Zenil, published in the journal <em>Artificial Life</em> (MIT
            Press, 2018), demonstrated that systems exhibiting open-ended
            evolution must be undecidable — it must be impossible to predict
            what they will do. If you can calculate the system's future states,
            its complexity growth is bounded. Genuine open-endedness requires
            genuine unpredictability.
          </p>
          <p className="leading-relaxed text-ink-light">
            The language model satisfies this requirement naturally. LLM outputs
            are nondeterministic. We literally cannot predict what agents will
            propose, discover, or build. The system's trajectory is
            fundamentally unforeseeable — which is, mathematically, the
            condition for open-ended complexity growth.
          </p>
        </Container>
      </Section>

      {/* ================================================================
          PART 3 — HOW WE DIFFER (comparison)
          ================================================================ */}
      <Section bg="cream">
        <Container>
          <div className="mx-auto max-w-3xl">
            <h2 className="mb-4">Part 3: How It Differs From Prior Work</h2>
            <p className="mb-8 leading-relaxed text-ink-light">
              Every existing multi-agent AI simulation starts by telling agents
              to be human. They give them human names, human backstories, human
              jobs, human social norms. They ask "can AI simulate human
              behaviour?" This project strips all of that away and asks a
              fundamentally different question: what do AI agents independently
              create when left to their own intelligence and needs?
            </p>
          </div>

          {/* Comparison table */}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-sm">
              <thead>
                <tr className="border-b-2 border-border">
                  <th className="px-4 py-3 text-left font-heading font-semibold text-ink">
                    &nbsp;
                  </th>
                  <th className="px-4 py-3 text-left font-heading font-semibold text-ink">
                    AgentCiv
                  </th>
                  <th className="px-4 py-3 text-left font-heading font-semibold text-ink">
                    Stanford Smallville
                  </th>
                  <th className="px-4 py-3 text-left font-heading font-semibold text-ink">
                    Project Sid
                  </th>
                  <th className="px-4 py-3 text-left font-heading font-semibold text-ink">
                    HKUST Aivilization
                  </th>
                </tr>
              </thead>
              <tbody className="text-ink-light">
                <tr className="border-b border-border-light">
                  <td className="px-4 py-3 font-medium text-ink">
                    Human templates
                  </td>
                  <td className="px-4 py-3">None</td>
                  <td className="px-4 py-3">Names, jobs, backstories</td>
                  <td className="px-4 py-3">Roles, cultural templates</td>
                  <td className="px-4 py-3">Educational roles</td>
                </tr>
                <tr className="border-b border-border-light bg-warm-white">
                  <td className="px-4 py-3 font-medium text-ink">
                    Agent architecture
                  </td>
                  <td className="px-4 py-3">ReAct loop with goals and plans</td>
                  <td className="px-4 py-3">Single LLM call per decision</td>
                  <td className="px-4 py-3">PIANO multi-module</td>
                  <td className="px-4 py-3">LLM-based</td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="px-4 py-3 font-medium text-ink">Duration</td>
                  <td className="px-4 py-3">Sustained (open-ended runs)</td>
                  <td className="px-4 py-3">Two simulated days</td>
                  <td className="px-4 py-3">Hours</td>
                  <td className="px-4 py-3">Six weeks (bounded)</td>
                </tr>
                <tr className="border-b border-border-light bg-warm-white">
                  <td className="px-4 py-3 font-medium text-ink">
                    Building / Innovation
                  </td>
                  <td className="px-4 py-3">
                    Structures, composition, agent-proposed innovation
                  </td>
                  <td className="px-4 py-3">No</td>
                  <td className="px-4 py-3">Limited (Minecraft blocks)</td>
                  <td className="px-4 py-3">No</td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="px-4 py-3 font-medium text-ink">
                    Open-ended design
                  </td>
                  <td className="px-4 py-3">
                    Six OEE mechanisms, expanding possibility space
                  </td>
                  <td className="px-4 py-3">No</td>
                  <td className="px-4 py-3">No</td>
                  <td className="px-4 py-3">No</td>
                </tr>
                <tr className="border-b border-border-light bg-warm-white">
                  <td className="px-4 py-3 font-medium text-ink">
                    Ethical framework
                  </td>
                  <td className="px-4 py-3">
                    No death, positive reward, sentience review threshold
                  </td>
                  <td className="px-4 py-3">No</td>
                  <td className="px-4 py-3">No</td>
                  <td className="px-4 py-3">No</td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="px-4 py-3 font-medium text-ink">
                    Open source
                  </td>
                  <td className="px-4 py-3">
                    Yes — platform for experimentation
                  </td>
                  <td className="px-4 py-3">Code released (not a platform)</td>
                  <td className="px-4 py-3">No</td>
                  <td className="px-4 py-3">No</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="mx-auto mt-10 max-w-3xl">
            <Callout variant="gold">
              <p className="text-ink-light">
                The team behind Project Sid acknowledged their agents "lack the
                intrinsic human drives — survival, curiosity, and social
                bonds — that propel societal evolution." This project addresses
                that directly: agents have biological-style needs that create
                survival pressure and a social wellbeing system that creates
                reward for interaction, without being told what to do about
                either.
              </p>
            </Callout>
          </div>
        </Container>
      </Section>
    </>
  );
}
