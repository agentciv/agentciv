import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";
import TableOfContents from "../components/common/TableOfContents";

const tocItems = [
  { id: "the-world", label: "The World" },
  { id: "the-agents", label: "The Agents" },
  { id: "how-agents-think", label: "How Agents Think" },
  { id: "goals-and-plans", label: "Goals and Plans" },
  { id: "communication", label: "Communication" },
  { id: "memory", label: "Memory" },
  { id: "no-death", label: "No Death" },
  { id: "building", label: "Building" },
  { id: "composition", label: "Composition" },
  { id: "innovation", label: "Innovation" },
  { id: "specialisation", label: "Specialisation" },
  { id: "collective-rules", label: "Collective Rules" },
  { id: "knowledge-transfer", label: "Knowledge Transfer" },
];

export default function HowItWorks() {
  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-6">How It Works</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            A complete guide to the world, the agents, and every mechanism that
            makes the civilisation possible. Start at the top for the big
            picture, or jump to any section.
          </p>
        </Container>
      </Section>

      {/* Two-column layout: TOC + content */}
      <Section bg="cream" className="py-0 md:py-0">
        <div className="mx-auto max-w-7xl px-6">
          <div className="relative lg:grid lg:grid-cols-[220px_1fr] lg:gap-12">
            {/* Sidebar TOC — desktop only */}
            <TableOfContents items={tocItems} />

            {/* Main content */}
            <div className="max-w-3xl pb-24">
              {/* --------------------------------------------------------
                  THE WORLD
                  -------------------------------------------------------- */}
              <article id="the-world" className="scroll-mt-24 pb-16">
                <h2 className="mb-6">The World</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  The civilisation lives in a two-dimensional grid world. Each
                  tile has a terrain type — plains, rocky ground, or dense
                  terrain — and may contain resources: water, food, or material.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Resources are distributed unevenly on purpose. Water clusters
                  in one area, food in another, material elsewhere. No single
                  agent can get everything it needs without moving across the
                  world. This uneven distribution is the first pressure that
                  makes encounter — and eventually social behaviour — likely.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Resources deplete when gathered and regenerate over time, but
                  the world pushes back. Heavy gathering in one area slows
                  regeneration there. Crowding means resources deplete faster
                  when many agents occupy the same space.
                </p>
                <Callout variant="sage">
                  <p className="font-medium text-ink">
                    The environment is not static. It shifts periodically —
                    resource zones move, scarcity events hit, new areas open up.
                    And it co-evolves with what agents do. Their activity changes
                    the world, which changes the conditions they face.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  THE AGENTS
                  -------------------------------------------------------- */}
              <article id="the-agents" className="scroll-mt-24 py-16">
                <h2 className="mb-6">The Agents</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Each agent is a genuinely autonomous AI — not a scripted
                  character, not a chatbot responding to prompts, but an entity
                  with its own goals, plans, perceptions, memories, and reasoning
                  capability.
                </p>

                <h3 className="mb-3 text-xl">What they have</h3>
                <ul className="mb-8 space-y-2 text-ink-light">
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>A position in the world</span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      Biological-style needs (food, water, material) that deplete
                      over time
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      Capabilities (perception range, movement speed, memory
                      capacity) that degrade when needs go unmet and recover when
                      needs are met
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      A social wellbeing level that increases through interaction
                      with and proximity to other agents
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>An inventory for carrying resources</span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      The ability to perceive nearby tiles, resources, agents, and
                      structures
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      Natural-language communication with nearby agents
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      Persistent memory of past events, interactions, and
                      knowledge
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      The ability to set goals, form plans, and pursue them across
                      multiple turns
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      The ability to build structures, compose new things, and
                      propose innovations
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>
                      The ability to develop specialised skills through practice
                    </span>
                  </li>
                  <li className="flex gap-2 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
                    <span>The ability to propose collective rules</span>
                  </li>
                </ul>

                <h3 className="mb-3 text-xl">What they do not have</h3>
                <ul className="space-y-2 text-ink-light">
                  {[
                    "A name",
                    "A personality",
                    "A role or job title",
                    "Social norms or cultural templates",
                    "Instructions on how to interact",
                    'Knowledge of what cooperation, trade, governance, or culture are',
                    'Any behavioural guidance — they are told what actions exist, not which to choose',
                  ].map((item) => (
                    <li key={item} className="flex gap-2 leading-relaxed">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ink-muted" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>

                <Callout variant="gold">
                  <p className="font-medium text-ink">
                    Everything that emerges beyond bare survival is genuinely
                    discovered by the agents, not prescribed by us.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  HOW AGENTS THINK
                  -------------------------------------------------------- */}
              <article id="how-agents-think" className="scroll-mt-24 py-16">
                <h2 className="mb-6">How Agents Think</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Every agent runs on a real AI model — a small, fast language
                  model. But they are not just getting a single AI response per
                  event. Each agent uses a genuine reasoning loop where it thinks
                  about what to do, does it, observes the result, and then
                  decides whether to continue or change course. This is called a
                  ReAct loop (Reason, Act, Observe).
                </p>

                <div className="my-8 space-y-4">
                  {[
                    {
                      step: "1",
                      title: "Reason",
                      body: "The agent receives its full state — position, needs, social wellbeing, capabilities, what it can see, its memories, its current goals and plans — and reasons about what to do.",
                    },
                    {
                      step: "2",
                      title: "Act",
                      body: "It takes an action — move, gather, communicate, build, propose an innovation, propose a rule, or many other options.",
                    },
                    {
                      step: "3",
                      title: "Observe",
                      body: "It perceives the result. Did it work? Has anything changed?",
                    },
                    {
                      step: "4",
                      title: "Repeat or stop",
                      body: "If its goal is not met, it reasons again with the new information and takes another action. Up to four steps per turn.",
                    },
                  ].map((s) => (
                    <div
                      key={s.step}
                      className="flex gap-4 rounded-lg border border-border bg-warm-white p-4"
                    >
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sky text-sm font-bold text-white">
                        {s.step}
                      </span>
                      <div>
                        <p className="font-heading font-semibold text-ink">
                          {s.title}
                        </p>
                        <p className="mt-1 leading-relaxed text-ink-light">
                          {s.body}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <Callout variant="sky">
                  <p className="text-ink-light">
                    <span className="font-medium text-ink">Example:</span> In a
                    single turn, an agent might notice its food is low, remember
                    there was food to the south, move south, find the food is
                    gone, notice another agent nearby, ask that agent about food,
                    receive a response pointing east, and update its plan to head
                    east. That is a chain of genuine reasoning and adaptation,
                    not a single prompted response.
                  </p>
                </Callout>

                <p className="mt-6 leading-relaxed text-ink-light">
                  Between turns, agents follow their current plan through cheap
                  automated behaviour — walking along a planned route, gathering
                  at a known resource. The full reasoning loop fires when
                  something meaningful happens: encountering another agent,
                  finding an expected resource depleted, capabilities degrading,
                  social wellbeing increasing after an interaction, or a periodic moment
                  of reflection where the agent reconsiders its overall
                  situation.
                </p>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  GOALS AND PLANS
                  -------------------------------------------------------- */}
              <article id="goals-and-plans" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Goals and Plans</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Agents set their own goals. Nobody tells them what to want. An
                  agent might independently decide "I need to find a reliable
                  water source" or "I want to build a shelter near food."
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Goals persist across turns — the agent does not forget what it
                  is pursuing between reasoning cycles. Plans are multi-step
                  strategies toward goals, executed over time and revised when
                  circumstances change.
                </p>
                <p className="leading-relaxed text-ink-light">
                  This is what makes the agents genuinely autonomous rather than
                  reactive. They have sustained intentions that shape their
                  behaviour over extended periods. They are not just responding
                  to what is in front of them — they are pursuing objectives.
                </p>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  COMMUNICATION
                  -------------------------------------------------------- */}
              <article id="communication" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Communication</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Agents communicate with each other in natural language.
                  Communication has range — you can only talk to agents near you.
                  Messages are free-form. Nobody told agents what to talk about,
                  how to ask for things, or what information to share or
                  withhold.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  When agents are near each other, they exchange messages — and
                  those messages accumulate into conversations over successive
                  ticks. An agent that receives a message gets triggered to
                  respond, creating natural back-and-forth dialogue. Every
                  message is logged and visible to visitors through the fishbowl
                  interface.
                </p>
                <Callout variant="gold">
                  <p className="text-ink-light">
                    What agents choose to communicate — and what they choose not
                    to — is one of the most fascinating things to observe. Do
                    they share resource locations freely? Do they withhold
                    information? Do they ask about other agents? Do they develop
                    consistent patterns in how they communicate? All emergent.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  MEMORY
                  -------------------------------------------------------- */}
              <article id="memory" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Memory</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Every agent has a persistent memory of significant events —
                  encounters, conversations, discoveries, outcomes. Memory has
                  capacity limits and uses importance-weighted eviction — when
                  an agent&apos;s memory is full, the least important and oldest
                  memories are dropped to make room for new ones.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Memory retrieval is context-aware: when an agent encounters
                  another entity, memories involving that entity are
                  preferentially recalled. When near a resource, memories about
                  that resource type surface first. This creates natural
                  continuity in relationships and spatial knowledge.
                </p>
                <Callout variant="sage">
                  <p className="text-ink-light">
                    Because memories are stored as natural language summaries
                    with limited capacity, information naturally degrades as it
                    passes between agents through conversation. An agent that
                    heard about a water source from another agent will remember
                    the gist, not the precise coordinates. Over many
                    transmissions, knowledge drifts — an emergent analogue of
                    cultural memory distortion.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  NO DEATH
                  -------------------------------------------------------- */}
              <article id="no-death" className="scroll-mt-24 py-16">
                <h2 className="mb-6">No Death</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Agents are never killed or removed from the world. This is
                  both an ethical choice and a design choice.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  When agents' needs go unmet, their capabilities degrade — they
                  see less, move slower, remember less. But degradation is always
                  recoverable. Meet your needs and your capabilities return. The
                  worst state an agent can be in is diminished, never destroyed.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  The oldest agents with the deepest memories, most complex
                  relationships, and most accumulated knowledge are the richest
                  social actors in the civilisation. Removing them would destroy
                  accumulated complexity. Civilisation is built by entities
                  living together over time, not by entities dying and being
                  replaced.
                </p>
                <p className="leading-relaxed text-ink-light">
                  This principle is also grounded in the ethical framework — we
                  cannot prove these agents do not have some form of experience,
                  and the cautious response to that uncertainty is to never do
                  the most severe irreversible thing.
                </p>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  BUILDING
                  -------------------------------------------------------- */}
              <article id="building" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Building</h2>
                <p className="mb-6 leading-relaxed text-ink-light">
                  Agents can permanently modify their world by building
                  structures on tiles. This is the mechanism that enables
                  civilisation — without persistent modification of the
                  environment, complexity can never compound.
                </p>

                <h3 className="mb-4 text-xl">Starter structures</h3>
                <p className="mb-4 leading-relaxed text-ink-light">
                  These are the recipes agents can discover from the beginning:
                </p>

                <div className="mb-8 space-y-4">
                  {[
                    {
                      name: "Shelter",
                      recipe: "water + material",
                      effect:
                        "Reduces the rate at which agents on that tile lose capabilities. A practical reason to build near resources you need.",
                    },
                    {
                      name: "Storage",
                      recipe: "food + material",
                      effect:
                        "Holds resources on a tile that any agent can access. Accumulated surplus that exists independently of any agent.",
                    },
                    {
                      name: "Marker",
                      recipe: "material",
                      effect:
                        "Contains a text message from the builder. Any agent that visits the tile can read it. Persistent communication that does not require the builder to be present.",
                    },
                    {
                      name: "Path",
                      recipe: "material + material",
                      effect:
                        "Reduces how much energy it costs to move across that tile. Built routes between resource zones.",
                    },
                  ].map((s) => (
                    <div
                      key={s.name}
                      className="rounded-lg border border-border bg-warm-white p-5"
                    >
                      <div className="mb-1 flex flex-wrap items-baseline gap-2">
                        <span className="font-heading text-lg font-semibold text-ink">
                          {s.name}
                        </span>
                        <span className="text-sm text-ink-muted">
                          ({s.recipe})
                        </span>
                      </div>
                      <p className="leading-relaxed text-ink-light">
                        {s.effect}
                      </p>
                    </div>
                  ))}
                </div>

                <p className="leading-relaxed text-ink-light">
                  Every structure has functional effects — they actually do
                  things that change the dynamics for every agent that encounters
                  them. This means building is adaptive. An intelligent agent
                  pursuing a goal might independently discover that building a
                  shelter near a water source is a good strategy. Nobody tells
                  agents to build. The world makes building useful, and agents
                  can reason their way to it.
                </p>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  COMPOSITION
                  -------------------------------------------------------- */}
              <article id="composition" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Composition</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  This is where complexity starts compounding. Agents can take
                  existing structures and combine them into new, higher-tier
                  structures that have enhanced or novel effects. A shelter next
                  to a storage might be combined into something that preserves
                  stored resources longer. Two markers might be combined into a
                  signpost system.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Not all combinations are predefined. When an agent tries a
                  combination that has not been specified, the system evaluates
                  whether it makes sense and what it would produce. Successful
                  compositions create new structure types that never existed
                  before — and those new types can themselves be combined with
                  other things, expanding the possibility space further.
                </p>
                <Callout variant="gold">
                  <p className="text-ink-light">
                    Each discovery is logged. The agent that discovers a new
                    composition has created genuine knowledge. Whether they share
                    that knowledge with others or keep it to themselves is
                    emergent.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  INNOVATION
                  -------------------------------------------------------- */}
              <article id="innovation" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Innovation</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  This is the capability that makes the system truly open-ended.
                  An agent can propose building something that is not in any
                  recipe list — something entirely new that the agent has
                  reasoned its way to.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  An agent that notices food spoils before it can be eaten might
                  propose a preservation structure. An agent that cannot
                  communicate with a distant ally might propose a relay marker
                  system. An agent that needs something from another agent might
                  invent a trade structure.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Each proposal is evaluated: is it feasible given the
                  simulation's rules? What resources would it require? What
                  would it do? If valid, a genuinely new structure type is
                  created and added to the world's recipe registry. Other agents
                  can learn about it, build it, and compose it with other things.
                </p>
                <Callout variant="sage">
                  <p className="font-medium text-ink">
                    The possibility space is literally unbounded. Agents can
                    create things nobody imagined. Each innovation opens new
                    possibilities for further innovation. The space of what is
                    possible in the civilisation expands continuously.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  SPECIALISATION
                  -------------------------------------------------------- */}
              <article id="specialisation" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Specialisation</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Agents are not assigned roles. But they develop them. An agent
                  that gathers food repeatedly becomes incrementally more
                  efficient at gathering food. One that builds frequently becomes
                  a more efficient builder. Skills develop through practice, not
                  prescription.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  This creates genuine asymmetry between agents that nobody
                  planned. If Agent 12 is better at building and Agent 23 is
                  better at gathering, they have real reasons to coordinate —
                  each can do something the other needs more efficiently. This
                  is the foundation of division of labour and economic
                  interdependence, emerging from nothing but individual choices
                  and accumulated practice.
                </p>
                <p className="leading-relaxed text-ink-light">
                  Each agent knows what it is specialised in. This influences
                  its goal-setting and planning. An agent that knows it is an
                  efficient builder might pursue building-focused goals,
                  deepening its specialisation further.
                </p>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  COLLECTIVE RULES
                  -------------------------------------------------------- */}
              <article id="collective-rules" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Collective Rules</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Agents can propose rules — persistent statements about
                  expected behaviour in an area. Other agents who encounter the
                  rule independently decide whether to accept it or ignore it.
                  The simulation tracks how widely each rule is adopted.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  When a rule is accepted by enough agents, it becomes
                  "established" — visible in the perception of every agent in
                  that area. But established does not mean followed. Whether
                  agents comply with established rules, defect when it suits
                  them, or propose competing rules — that is all emergent.
                </p>
                <Callout variant="gold">
                  <p className="text-ink-light">
                    Nobody defines what rules agents propose. Nobody defines
                    enforcement mechanisms. Nobody defines consequences for
                    rule-breaking. If governance emerges, it emerges because
                    intelligent agents independently discovered that collective
                    coordination requires shared agreements. And the form that
                    governance takes — hierarchical, consensual, territorial, or
                    something entirely alien — is one of the most fascinating
                    things the experiment might reveal.
                  </p>
                </Callout>
              </article>

              <div className="border-t border-border" />

              {/* --------------------------------------------------------
                  KNOWLEDGE TRANSFER
                  -------------------------------------------------------- */}
              <article id="knowledge-transfer" className="scroll-mt-24 py-16">
                <h2 className="mb-6">Knowledge Transfer</h2>
                <p className="mb-4 leading-relaxed text-ink-light">
                  When agents communicate, the content of their messages becomes
                  part of both agents&apos; memories. An agent that learns about
                  a resource location through conversation will remember that
                  information and can act on it — or pass it along to others.
                </p>
                <p className="mb-4 leading-relaxed text-ink-light">
                  Knowledge transfer happens through the natural language
                  channel: agents talk, and what they say becomes memory. There
                  is no system-level &ldquo;knowledge packet&rdquo; being
                  transferred — just conversation, remembered imperfectly, that
                  shapes future decisions. This means knowledge naturally
                  degrades as it passes through more agents, creating conditions
                  for drift, distortion, and the emergence of local knowledge
                  traditions.
                </p>
                <p className="leading-relaxed text-ink-light">
                  Knowledge compounds because the reasoning model naturally
                  draws on everything the agent knows. An agent holding
                  memories about a distant resource zone and knowledge of how
                  to build shelters might independently reason toward proposing
                  a way station. This combinatorial knowledge creation is not
                  programmed — it emerges from the AI model reasoning across
                  the agent&apos;s accumulated experience.
                </p>
              </article>
            </div>
          </div>
        </div>
      </Section>
    </>
  );
}
