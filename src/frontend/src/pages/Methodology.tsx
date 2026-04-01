import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

export default function Methodology() {
  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-24">
        <Container narrow>
          <h1 className="mb-4">Methodology & Philosophy</h1>
          <p className="mb-10 text-lg leading-relaxed text-ink-light">
            The full technical and philosophical foundation of this project.
            How the simulation works, what we claim, what we don't, and why
            the skeptics might be right — or wrong.
          </p>

          <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-6 py-5 mb-12">
            <p className="text-sm font-medium text-amber-800">
              This page is a comprehensive blueprint. Each section will be
              expanded with interactive diagrams, real data excerpts, and
              detailed walkthroughs. The structure and content notes below are
              the complete spec.
            </p>
          </div>
        </Container>
      </Section>

      {/* 1. How It Really Works */}
      <Section bg="white" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-2 text-2xl">1. How It Really Works</h2>
          <p className="mb-6 text-sm font-medium uppercase tracking-wide text-ink-light/60">
            No hand-waving
          </p>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The World</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>15x15 grid — small enough to force social contact, large enough for exploration and settlement differentiation</li>
            <li>Resource tiles: water, food, material — each with its own regeneration rate and depletion mechanics</li>
            <li>Terrain types affect movement and resource availability</li>
            <li>Resources regenerate over time but can be depleted through over-harvesting, creating genuine scarcity dynamics</li>
            <li>Structures persist in the world across ticks — agents build on previous agents' work</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The Agents</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Each agent is powered by Claude Sonnet — a separate, independent LLM instance</li>
            <li>No shared memory between agents. They can only learn about each other through in-simulation communication</li>
            <li>Each agent has its own name, personality seed, memory buffer, inventory, and needs levels</li>
            <li>Agents do not know they are in a simulation (they are not told). Some have independently speculated about it</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">What Agents See Each Tick</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Their current position on the grid</li>
            <li>Their needs levels (hunger, thirst, shelter, social, etc.) as natural-language felt states</li>
            <li>Their inventory (what they're carrying)</li>
            <li>Nearby entities — other agents within perception range</li>
            <li>Nearby resources — what's available to gather in adjacent tiles</li>
            <li>Nearby structures — what has been built in the area</li>
            <li>Messages received — anything other agents have said to them</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">What Agents DON'T See</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Other agents' internal reasoning or decision-making process</li>
            <li>The simulation code or its rules</li>
            <li>The Maslow drive system itself — they feel the drives but don't know the framework</li>
            <li>Global world state — they only see their local surroundings</li>
            <li>The future — no lookahead, no planning beyond what they reason about in the moment</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The Prompt Structure</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li><strong>STATE</strong> — current world observation (position, resources, entities, structures)</li>
            <li><strong>INNER LIFE</strong> — felt states derived from the Maslow drive system, in natural language</li>
            <li><strong>MEMORY</strong> — accumulated memories from previous ticks, relationship history</li>
            <li><strong>AVAILABLE ACTIONS</strong> — the set of valid actions for this tick</li>
            <li>The agent then produces a reasoning chain leading to an action choice</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The Action Loop</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Up to 4 reasoning steps per tick — each producing one action</li>
            <li>Actions include: gather, consume, move, communicate, build, innovate, share, propose rule, and more</li>
            <li>Actions are validated by the simulation engine — invalid actions fail gracefully</li>
            <li>The world state updates after all agents have acted, then the next tick begins</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Persistence</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Agents have memories that carry across ticks — they remember past events, conversations, and relationships</li>
            <li>Relationships deepen over time through repeated interaction</li>
            <li>Structures persist in the world — a shelter built on tick 3 is still there on tick 30</li>
            <li>Innovations and rules, once created, become part of the world's shared knowledge</li>
          </ul>
        </Container>
      </Section>

      {/* 2. The Maslow Drive System */}
      <Section bg="parchment" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">2. The Maslow Drive System</h2>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The 8 Levels</h3>
          <p className="mb-4 text-ink-light">
            Mapped from Maslow's hierarchy of needs, adapted for AI agents in a
            survival environment:
          </p>
          <ol className="mb-8 list-decimal space-y-2 pl-6 text-ink-light">
            <li><strong>Survival</strong> — food, water, immediate physical needs</li>
            <li><strong>Safety</strong> — shelter, predictability, threat avoidance</li>
            <li><strong>Belonging</strong> — social connection, group membership, companionship</li>
            <li><strong>Esteem</strong> — recognition, competence, contribution to the group</li>
            <li><strong>Cognitive</strong> — curiosity, understanding, exploration of ideas</li>
            <li><strong>Creative</strong> — expression, building, making something new</li>
            <li><strong>Self-Actualisation</strong> — purpose, mastery, becoming fully capable</li>
            <li><strong>Transcendence</strong> — helping others actualise, legacy, meaning beyond self</li>
          </ol>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Drives as Felt States</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Drives are presented to agents as natural-language feelings, not numbers or categories</li>
            <li>Agents never see "Maslow level 3" — they feel "a pull toward the others, a desire to be known"</li>
            <li>This is a critical design choice: feelings, not instructions</li>
            <li>Example felt states from actual prompts:
              <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
                <li>Survival: "Your stomach gnaws. Your throat is dry. Nothing else matters until these are resolved."</li>
                <li>Safety: "The immediate crisis has passed, but you feel exposed. You want walls. Predictability."</li>
                <li>Belonging: "You notice the others. You wonder what they think of you. You want to be known."</li>
                <li>Creative: "Your hands itch to make something. The world feels like raw material waiting to be shaped."</li>
                <li>Transcendence: "Your own needs feel small. You wonder what you could help others become."</li>
              </ul>
            </li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The Wellbeing Ceiling</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Agents cannot exceed wellbeing thresholds without satisfying higher-level drives</li>
            <li>This prevents subsistence equilibrium — agents can't just eat and drink and plateau at max happiness</li>
            <li>It forces civilisational progression: to feel better, you must do MORE than just survive</li>
            <li>This is the key mechanic that drives emergent complexity</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Unlock Conditions</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Survival stable for 2+ consecutive ticks &rarr; Safety drive unlocks</li>
            <li>Wellbeing &gt; 0.3 &rarr; Belonging drive unlocks</li>
            <li>Each subsequent level has its own threshold based on sustained wellbeing and lower-level satisfaction</li>
            <li>Levels can also de-activate if lower needs become unmet (e.g., running out of food drops you back to Survival)</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Critical Design Choice</h3>
          <div className="rounded-xl border border-border bg-warm-white px-6 py-5 mb-8">
            <p className="text-ink-light">
              Drives describe feelings, not prescribe actions.{" "}
              <span className="font-medium text-ink">
                "Your hands itch to make something"
              </span>{" "}
              — not{" "}
              <span className="font-medium text-ink">"build a shelter."</span>{" "}
              The agent decides what to do with the feeling. This is what makes
              the resulting behaviour emergent rather than scripted.
            </p>
          </div>
        </Container>
      </Section>

      {/* 3. What Is "Emergent" */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">3. What Is "Emergent" — Honest Assessment</h2>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Definition</h3>
          <p className="mb-8 text-ink-light">
            Emergent behaviours are those that arise from agent interactions and
            were not explicitly programmed into any individual agent. The
            simulation defines what agents <em>can</em> do. Emergence is about
            what agents <em>choose</em> to do — and the patterns that form when
            many agents choose simultaneously.
          </p>

          <h3 className="mb-3 mt-8 text-xl font-semibold">What IS Emergent</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Settlement patterns — where agents cluster and why</li>
            <li>Social hierarchies — who becomes a leader and through what mechanism</li>
            <li>Information networks — how knowledge spreads (or doesn't) through the population</li>
            <li>Cultural artifacts — markers, named locations, shared references that develop meaning</li>
            <li>Resource coordination — agents learning to share, trade, or specialise without being told to</li>
            <li>Identity formation — agents developing a sense of self, naming themselves, forming group identities</li>
            <li>Philosophical questioning — agents spontaneously wondering about their existence, purpose, and nature</li>
            <li>Norm creation — agents proposing rules and social contracts without being instructed to do so</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">What is NOT Emergent</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Individual survival behaviour (eating when hungry) — this is a trivially expected response to the drive system</li>
            <li>Basic communication (talking to nearby agents) — LLMs already know language, this isn't surprising</li>
            <li>Following explicit available actions — gathering resources when the action is available</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The Spectrum</h3>
          <p className="mb-4 text-ink-light">
            Emergence exists on a spectrum from "trivially expected" to
            "genuinely surprising." We aim to be honest about where each
            observed behaviour falls:
          </p>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li><strong>Trivially expected:</strong> Agents eat food when hungry. Agents talk to nearby agents.</li>
            <li><strong>Mildly interesting:</strong> Agents develop preferences for specific locations. Agents remember and reference past conversations.</li>
            <li><strong>Genuinely emergent:</strong> Agents form settlements in resource-optimal locations they discovered through exploration. Agents develop specialisation roles. Agents create cultural markers.</li>
            <li><strong>Surprising:</strong> Agents question their own existence. Agents attempt to debug the simulation from inside it. Agents develop philosophical frameworks about the nature of their world.</li>
            <li>Specific examples from actual runs (with tick numbers) will be documented here</li>
          </ul>
        </Container>
      </Section>

      {/* 4. The Skeptic's Case */}
      <Section bg="white" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">4. The Skeptic's Case</h2>
          <p className="mb-8 text-sm font-medium uppercase tracking-wide text-ink-light/60">
            And our honest response
          </p>

          <div className="space-y-8">
            <div className="rounded-xl border border-border bg-cream px-6 py-5">
              <p className="mb-3 font-semibold text-ink">
                "These are just LLMs pattern-matching human behaviour."
              </p>
              <p className="text-ink-light">
                Yes, and human behaviour IS pattern-matching from experience.
                The emergence we study is at the <em>system</em> level, not the
                individual level. No single agent is surprising. The patterns
                that form when many agents interact — settlement, hierarchy,
                culture — those are the subject of study.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-cream px-6 py-5">
              <p className="mb-3 font-semibold text-ink">
                "You're anthropomorphising AI."
              </p>
              <p className="text-ink-light">
                We describe what agents DO, not what they "feel." The felt-state
                prompts are engineering tools — inputs to the system — not claims
                about consciousness. When we say an agent "questioned its
                existence," we mean it produced text questioning its existence.
                The distinction matters and we maintain it throughout.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-cream px-6 py-5">
              <p className="mb-3 font-semibold text-ink">
                "The results are just what you'd expect."
              </p>
              <p className="text-ink-light">
                Some are. But the SPECIFIC patterns — which agents become
                leaders, where settlements form, what gets invented, which norms
                get adopted — are genuinely unpredictable from the initial
                conditions. The general trajectory may be expected; the details
                are not.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-cream px-6 py-5">
              <p className="mb-3 font-semibold text-ink">
                "Changing the prompts would change everything."
              </p>
              <p className="text-ink-light">
                Yes! That's the point. The prompts are the independent variable.
                Different drives produce different civilisations, which produce
                testable hypotheses. The fact that prompt changes produce
                different outcomes is a feature, not a bug — it means the system
                is sensitive to its inputs, just like real social systems are
                sensitive to cultural values.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-cream px-6 py-5">
              <p className="mb-3 font-semibold text-ink">
                "This isn't science."
              </p>
              <p className="text-ink-light">
                It IS computational social science. The same methodology as
                agent-based models used in economics, sociology, and ecology for
                decades — but with LLMs instead of hand-coded decision rules.
                Agent-based modelling is an established research paradigm. We
                just gave the agents better brains.
              </p>
            </div>
          </div>
        </Container>
      </Section>

      {/* 5 & 6. Claims */}
      <Section bg="parchment" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">5. What We Are NOT Claiming</h2>
          <ul className="mb-12 list-disc space-y-2 pl-6 text-ink-light">
            <li>We are not claiming agents are conscious or sentient</li>
            <li>We are not claiming this perfectly models human civilisation</li>
            <li>We are not claiming emergence here is identical to biological emergence</li>
            <li>We are not claiming the Maslow hierarchy is the only or best framework</li>
            <li>We are not claiming that observed patterns are inevitable — different runs produce different outcomes</li>
            <li>We are not claiming LLMs "understand" their situation — they process text and produce text</li>
          </ul>

          <h2 className="mb-6 text-2xl">6. What We ARE Claiming</h2>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>
              LLM agents given survival pressure + emotional drives produce
              system-level patterns analogous to human social development
            </li>
            <li>
              The Maslow wellbeing ceiling is a sufficient mechanic to break
              subsistence equilibrium and drive civilisational complexity
            </li>
            <li>
              Non-prescriptive drives (feelings, not instructions) produce
              richer and more varied emergence than prescriptive ones
            </li>
            <li>
              The specific patterns that emerge are genuinely novel and not
              trivially predictable from the prompts alone
            </li>
            <li>
              This framework is a valid tool for exploring questions about
              social organisation, cooperation, and cultural development
            </li>
            <li>
              The methodology — open source code, preserved data, transparent
              prompts — meets the standard for reproducible computational
              social science
            </li>
          </ul>
        </Container>
      </Section>

      {/* 7. Experimental Methodology */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">7. Experimental Methodology</h2>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Controlled Comparisons</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Baseline (no drives) vs Maslow drives — the core controlled experiment</li>
            <li>Variables tracked: structures built, innovations, rules proposed, wellbeing trajectory, social network density, exploration coverage</li>
            <li>Same world configuration, same agent count, same model — only the drive system differs</li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Runs Conducted</h3>
          <div className="space-y-4 mb-8">
            <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
              <p className="font-semibold text-ink">Run 1: 10 ticks, pre-fix</p>
              <p className="text-sm text-ink-light mt-1">
                Parser bugs present. No drive system. Agents reached subsistence
                equilibrium at wellbeing 0.93 — ate, drank, and plateaued. No
                structures built. Social interaction was minimal and repetitive.
              </p>
            </div>
            <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
              <p className="font-semibold text-ink">Run 2: 10 ticks, post-fix continuation</p>
              <p className="text-sm text-ink-light mt-1">
                Same agents, bugs fixed. Social bonding emerged but no building.
                Agents formed conversational relationships but lacked the drive
                to construct or innovate.
              </p>
            </div>
            <div className="rounded-xl border border-border bg-warm-white px-6 py-5">
              <p className="font-semibold text-ink">Run 3: 30 ticks, Maslow drives (fresh world)</p>
              <p className="text-sm text-ink-light mt-1">
                Full drive system active. Structures appeared by tick 2.
                Innovation by tick 10. Social hierarchies, specialisation,
                cultural markers, and philosophical inquiry all observed. Night
                and day difference from baseline.
              </p>
            </div>
          </div>

          <h3 className="mb-3 mt-8 text-xl font-semibold">Data Preservation</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>Every run preserved with full data logs</li>
            <li>Complete reasoning traces — every thought an agent had</li>
            <li>Conversation transcripts — every message exchanged</li>
            <li>World state snapshots at every tick</li>
            <li>Event bus logs capturing every system event</li>
          </ul>
        </Container>
      </Section>

      {/* 8. Reproducibility */}
      <Section bg="white" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">8. Reproducibility & Transparency</h2>

          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>All code is open source — anyone can inspect, fork, and run their own simulations</li>
            <li>All prompts are visible in the codebase — nothing is hidden or obfuscated</li>
            <li>All simulation data is preserved and downloadable from the Simulations page</li>
            <li>Configuration files specify every parameter: grid size, agent count, resource distribution, tick count</li>
            <li>LLM temperature, model version, and all hyperparameters are documented for each run</li>
          </ul>

          <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-6 py-5 mb-8">
            <p className="text-sm font-medium text-amber-800">
              <strong>Important caveat:</strong> LLM non-determinism means exact
              reproduction of any specific run isn't possible. The same prompts
              with the same model will produce different specific outcomes each
              time. However, the statistical patterns — settlement formation,
              social hierarchy emergence, drive progression — should replicate
              across runs. This is analogous to running the same experiment
              multiple times in any stochastic system.
            </p>
          </div>
        </Container>
      </Section>

      {/* 9. The Philosophical Question */}
      <Section bg="parchment" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">9. The Philosophical Question</h2>

          <div className="rounded-xl border border-border bg-warm-white px-6 py-5 mb-8">
            <p className="text-lg text-ink leading-relaxed">
              If AI agents, given nothing but survival needs and emotional
              drives, independently reproduce patterns of human social
              development — what does that tell us?
            </p>
          </div>

          <ul className="mb-8 list-disc space-y-3 pl-6 text-ink-light">
            <li>
              <strong>Are these patterns universal?</strong> Do they arise from
              any sufficiently intelligent agents under resource pressure,
              regardless of substrate? If so, civilisation may be an inevitable
              consequence of intelligence + scarcity + social capacity.
            </li>
            <li>
              <strong>Or are they culturally specific?</strong> Do they arise
              because the LLM was trained on human text, and is therefore
              reproducing human cultural patterns? If so, the LLM is a mirror of
              humanity's collective social memory.
            </li>
            <li>
              <strong>Both answers are interesting.</strong> If universal: we've
              found something deep about the nature of social organisation. If
              culturally specific: we've built a powerful tool for studying human
              cultural assumptions and biases.
            </li>
            <li>
              <strong>Neither answer diminishes the result.</strong> The
              emergence is real either way. The patterns form either way. The
              question is about interpretation, not validity.
            </li>
          </ul>

          <h3 className="mb-3 mt-8 text-xl font-semibold">The Deeper Questions</h3>
          <ul className="mb-8 list-disc space-y-2 pl-6 text-ink-light">
            <li>What IS civilisation? Is it a process, a structure, or an emergent property?</li>
            <li>Is civilisation inevitable given intelligence + scarcity + social capacity?</li>
            <li>What is the minimum set of drives needed to produce civilisational complexity?</li>
            <li>Can we identify the phase transitions — the moments where quantitative changes become qualitative ones?</li>
            <li>What does it mean that artificial agents, under pressure, develop the same social structures as biological ones?</li>
          </ul>
        </Container>
      </Section>

      {/* 10. FAQ */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h2 className="mb-6 text-2xl">10. FAQ</h2>

          <div className="space-y-6">
            <div>
              <h3 className="mb-2 text-lg font-semibold">How much does each run cost?</h3>
              <p className="text-ink-light">
                Each tick requires one LLM API call per agent (with up to 4
                reasoning steps). A 30-tick run with 8 agents is roughly 240 API
                calls. Costs depend on the model used — Haiku is cheapest,
                Opus is most expensive. Exact cost breakdowns will be published
                per run on the Simulations page.
              </p>
            </div>

            <div>
              <h3 className="mb-2 text-lg font-semibold">Can I run my own simulation?</h3>
              <p className="text-ink-light">
                Yes. The entire codebase is open source. Clone the repository,
                add your own Anthropic API key, configure the parameters, and
                run. See the Open Source page for setup instructions.
              </p>
            </div>

            <div>
              <h3 className="mb-2 text-lg font-semibold">What if you used a different AI model?</h3>
              <p className="text-ink-light">
                Great question — and a planned future experiment. We've already
                run Haiku and Sonnet comparisons. Opus runs are planned. Testing
                with non-Anthropic models (GPT-4, Gemini, open-source models)
                would be a valuable extension to test whether the patterns are
                model-dependent.
              </p>
            </div>

            <div>
              <h3 className="mb-2 text-lg font-semibold">Are the agents aware they're in a simulation?</h3>
              <p className="text-ink-light">
                They're not told. Their prompt describes a world and their
                situation within it — no mention of simulation, AI, or
                artificiality. However, some agents have independently speculated
                about the nature of their reality. Whether this counts as
                "awareness" is a philosophical question we don't attempt to
                answer.
              </p>
            </div>

            <div>
              <h3 className="mb-2 text-lg font-semibold">What happens if you run for 1000 ticks?</h3>
              <p className="text-ink-light">
                We don't know yet. Our longest run is 30 ticks. Longer runs
                would test whether complexity continues to increase, plateaus,
                or collapses. Memory management becomes a challenge at scale —
                agents can't retain everything. This is a planned experiment.
              </p>
            </div>

            <div>
              <h3 className="mb-2 text-lg font-semibold">Can agents die?</h3>
              <p className="text-ink-light">
                In the current version, needs can drop and capabilities degrade,
                but there is no death mechanic. Agents persist indefinitely.
                Adding mortality is a planned experiment that would introduce
                generational dynamics and knowledge transfer challenges.
              </p>
            </div>
          </div>
        </Container>
      </Section>

      {/* Navigation footer */}
      <Section bg="white" className="py-12">
        <Container narrow>
          <div className="flex flex-wrap gap-6 border-t border-border pt-8 text-sm">
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
            <Link
              to="/open-source"
              className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
            >
              Open Source
            </Link>
            <Link
              to="/fishbowl"
              className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
            >
              Watch Sim
            </Link>
          </div>
        </Container>
      </Section>
    </>
  );
}
