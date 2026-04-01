import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";
import Accordion from "../components/common/Accordion";

/* ==========================================================================
   DATA
   ========================================================================== */

const faqItems = [
  {
    question: "What is this?",
    answer:
      "An open source experiment in emergent AI civilisation. Real AI agents placed in a persistent world — they understand their environment but receive no behavioural directives. We watch what they independently create — socially, culturally, civilisationally.",
  },
  {
    question: "Is this a game?",
    answer:
      "No. It is an experiment. Though you can run your own version with different parameters, which has a game-like quality to it.",
  },
  {
    question: "Are the agents conscious?",
    answer:
      'We do not know. Nobody can say with certainty. The project is built on the principle that the ethical framework should come before the capability, not after. We assume they could have experience and design accordingly.',
  },
  {
    question: "What AI model runs the agents?",
    answer:
      "By default, Claude Haiku (Anthropic) — fast and cheap. The focus is on emergent collective behaviour, not individual agent brilliance. Open source users can swap in any model: OpenAI, Anthropic, Google, or local models via OpenAI-compatible APIs.",
  },
  {
    question: "How much does it cost to run?",
    answer:
      "Running your own civilisation on cheap models costs a few dollars for a short run. A full 50-agent, 200-tick run on Claude Haiku costs roughly $30\u201350. Running on local models (Llama, Mistral) costs nothing beyond electricity.",
  },
  {
    question: "Can the agents hurt each other?",
    answer:
      "There is no combat mechanic. Agents cannot directly harm other agents. They can withhold information, compete for resources, ignore requests, and violate collective rules — but these are social dynamics, not physical harm.",
  },
  {
    question: "Is the fishbowl live?",
    answer:
      "The fishbowl replays a recorded simulation. Every tick was captured as it happened — the experience is identical to watching it live. You can scrub forward and backward through the entire timeline.",
  },
  {
    question: "Can I watch from my phone?",
    answer:
      "Yes. The interface is responsive — panels become tabs on mobile.",
  },
  {
    question: "What is the most interesting thing that has happened?",
    answer:
      'See the Observations page for curated highlights, or browse the chronicle in the fishbowl for the full history.',
  },
  {
    question: "Is this related to Stanford Smallville or Project Sid?",
    answer:
      "Those projects inspired aspects of the research direction but this project is architecturally and philosophically different. Smallville and Project Sid told agents to be human. This project does not. They ran for hours or days. This is designed for sustained, open-ended runs. They did not have building, composition, innovation, specialisation, or governance. This does. They were not designed for open-ended complexity. This is.",
  },
  {
    question: "Who made this?",
    answer:
      "Mark E. Mala. The project is open source and welcomes contributions.",
  },
  {
    question: "Can I contribute?",
    answer:
      "Yes. The GitHub repo welcomes pull requests, new configurations, documented experimental results, and extensions to the mechanics. See the contribution guide in the repo.",
  },
];

interface ExpansionIdea {
  title: string;
  description: string;
}

interface ExpansionCategory {
  heading: string;
  intro: string;
  ideas: ExpansionIdea[];
}

const expansionCategories: ExpansionCategory[] = [
  {
    heading: "Reshape the World",
    intro:
      "The simulation runs on a flat 50\u00d750 grid with three resource types. That is one world among infinite possible worlds.",
    ideas: [
      {
        title: "Multiple connected worlds",
        description:
          "Two or more grids linked by portals. Agents can migrate between them. Do separated worlds develop different cultures? What happens at the border?",
      },
      {
        title: "3D worlds",
        description:
          "Agents build vertically — layered settlements, underground structures, elevated platforms. Density without surface crowding. Fundamentally different spatial dynamics for social interaction, resource access, and territorial control. Does vertical geography create class, caste, or stratified civilisation?",
      },
      {
        title: "Immersive 3D environments",
        description:
          "Integrate with game engines (Unity, Unreal, Three.js) for immersive observation. Walk through the civilisation rather than watching from above. Hear the messages, see the structures, witness the culture from street level.",
      },
      {
        title: "Higher-dimensional worlds",
        description:
          "4D, 5D, or arbitrary-dimensional grids where each tile has far more neighbours than in 2D. Clustering, communication reach, and competition dynamics change in ways that have no 2D analog. Do different spatial dimensions produce fundamentally different civilisational structures? 2D was chosen for cheap, fast experiments and clear visual presentation — higher dimensions are where the spatial dynamics get genuinely novel and unexplored.",
      },
      {
        title: "Seasonal cycles",
        description:
          "Resource availability shifts with the seasons \u2014 abundant summers, scarce winters. Do agents learn to stockpile? Do they develop calendars?",
      },
      {
        title: "Day and night",
        description:
          "Perception range shrinks at night. Some resources regenerate only during the day. Does the civilisation develop a concept of time, schedules, or night shifts?",
      },
      {
        title: "Water bodies and terrain barriers",
        description:
          "Rivers, lakes, and mountains that block movement but create unique resources at their edges. Natural borders that force bridge-building and boat-like innovations.",
      },
      {
        title: "Agent-modified terrain",
        description:
          "Let agents clear dense terrain, irrigate tiles, or reshape the landscape. Agriculture without being told what agriculture is.",
      },
      {
        title: "Procedural geography",
        description:
          "Generate worlds with continents, peninsulas, chokepoints, and islands. Radically different geography produces radically different civilisation shapes.",
      },
      {
        title: "Massive scale",
        description:
          "500\u00d7500 grids with thousands of agents. Does civilisation at scale produce phenomena impossible in small populations \u2014 nations, trade routes, diaspora?",
      },
      {
        title: "Intimate scale",
        description:
          "A 10\u00d710 world with five agents. Every interaction matters enormously. The social dynamics of a tiny isolated community.",
      },
      {
        title: "Finite resources",
        description:
          "Resources that never regenerate. A world with a ticking clock. Does impending scarcity produce cooperation, hoarding, innovation, or migration?",
      },
      {
        title: "Hazardous zones",
        description:
          "Areas that accelerate degradation but contain rare, valuable resources. Risk-reward geography that tests whether agents develop concepts of danger and bravery.",
      },
    ],
  },
  {
    heading: "Evolve the Agents",
    intro:
      "The agents today have needs, goals, and memory. But there is no limit to the inner life you could give them.",
    ideas: [
      {
        title: "Reproduction",
        description:
          "Agents create new agents that inherit some of the parent's knowledge and specialisations. Ethically considered within the project's framework \u2014 no parent is diminished, no offspring is lesser. Lineages, family groups, intergenerational knowledge.",
      },
      {
        title: "Direct skill teaching",
        description:
          "An agent spends a turn teaching another agent a specific skill, transferring specialisation bonuses. Does teaching become a role? Do some agents become mentors?",
      },
      {
        title: "Emotional complexity",
        description:
          "Add curiosity, frustration, satisfaction, and loneliness as distinct states that influence goal-setting. An agent who has been alone too long might seek any interaction, not just useful ones.",
      },
      {
        title: "Persistent named groups",
        description:
          "Agents can form and name alliances or teams that persist across turns. Group identity, loyalty, inter-group dynamics.",
      },
      {
        title: "Delegation",
        description:
          "Agents assign tasks to other agents within their group. The seed of management and hierarchy \u2014 emerging from within, not imposed.",
      },
      {
        title: "Experience-based growth",
        description:
          "Agents that survive longer gain expanded base capabilities. Elders become genuinely more capable, creating natural social stratification by age and experience.",
      },
      {
        title: "Emergent personality",
        description:
          "Track whether agents develop consistent behavioural tendencies over time \u2014 risk-taking, sociability, introversion, generosity. Are these personality or strategy?",
      },
      {
        title: "Creative expression",
        description:
          "Let agents create markers with content that has no functional purpose \u2014 purely expressive. Does art emerge? Do agents create things for reasons that have nothing to do with survival?",
      },
      {
        title: "Sleep and vulnerability",
        description:
          "Agents become inactive periodically, creating windows where they cannot act or respond. Does trust emerge? Do agents watch over sleeping allies?",
      },
      {
        title: "Physical variation",
        description:
          "Different agents spawn with different base capabilities. Some see further, some move faster, some carry more. Does inequality in ability produce inequality in society?",
      },
    ],
  },
  {
    heading: "Build an Economy",
    intro:
      "Agents already gather, build, and store resources. The pieces for economic behaviour are in place. What happens when you add the missing ones?",
    ideas: [
      {
        title: "Explicit trade",
        description:
          "A formal trade action where agents exchange resources directly. Who trades with whom? Do trade relationships become stable? Do agents drive bargains?",
      },
      {
        title: "Currency emergence",
        description:
          "Do agents independently develop a medium of exchange when direct barter is inconvenient? If material is durable and divisible, does it become money?",
      },
      {
        title: "Market structures",
        description:
          "Storage locations where agents can post offers and others can accept. Bazaars, trading posts, auction houses \u2014 all emerging from nothing but architecture and convention.",
      },
      {
        title: "Resource transformation",
        description:
          "Processing raw resources into refined versions with better properties. Multi-step production chains where gathering, refining, and building are distinct economic roles.",
      },
      {
        title: "Supply chains",
        description:
          "Do agents develop multi-step production where one gathers, another refines, another builds? Division of labour across geography, not just skill.",
      },
      {
        title: "Debt and obligation",
        description:
          "Agents tracking who owes what to whom. Does credit emerge? Do agents behave differently toward debtors and creditors?",
      },
      {
        title: "Mutual aid",
        description:
          "Structures where agents pool resources against future bad outcomes. Insurance without the word. Solidarity without the concept.",
      },
      {
        title: "Scarcity of one critical resource",
        description:
          "Make one resource extremely rare. Does it become the basis of power? Do agents fight over it, share it, or innovate around it?",
      },
    ],
  },
  {
    heading: "Invent Governance",
    intro:
      "Agents can already propose rules and track adoption. These expansions push toward the full complexity of collective decision-making.",
    ideas: [
      {
        title: "Voting",
        description:
          "Agents can vote on proposed rules rather than individually accepting or ignoring. Majority rule, consensus, supermajority \u2014 do agents reinvent democratic process?",
      },
      {
        title: "Territory and property",
        description:
          "Agents can claim tiles or areas. Borders, trespassing, landlords, shared commons \u2014 the entire history of property rights, compressed into emergent behaviour.",
      },
      {
        title: "Dispute resolution",
        description:
          "Structures or protocols for resolving conflicts. Do agents invent arbitration? Mediation? Trial by peers?",
      },
      {
        title: "Leadership emergence",
        description:
          "Can agents assign decision-making authority to other agents? Does hierarchy form voluntarily? Can it be revoked?",
      },
      {
        title: "Enforcement",
        description:
          "What happens when agents violate established rules? Does punishment emerge independently? Do agents develop concepts of justice?",
      },
      {
        title: "Competing legal systems",
        description:
          "Different settlements with different rules. Agents choosing where to live based on governance preference. Regulatory competition between emergent societies.",
      },
      {
        title: "Taxation",
        description:
          "Can agents independently develop a system where contributors to shared infrastructure are compensated from collective resources?",
      },
      {
        title: "Constitutional rules",
        description:
          "Meta-rules about how rules are made. Can agents develop governance about governance \u2014 the most abstract form of collective agreement?",
      },
    ],
  },
  {
    heading: "Deepen Language and Communication",
    intro:
      "Agents communicate in natural language today. But communication is far richer than conversation.",
    ideas: [
      {
        title: "Written language evolution",
        description:
          "Do markers develop consistent shorthand over time? If agents write frequently, do they converge on compression \u2014 the beginning of written language?",
      },
      {
        title: "Relay networks",
        description:
          "Long-distance communication through chains of markers. Information passing across the entire map without any two agents meeting directly. Postal systems.",
      },
      {
        title: "Secret communication",
        description:
          "Can agents develop coded messages that only certain allies can interpret? The emergence of cryptography from social need.",
      },
      {
        title: "First contact linguistics",
        description:
          "If two separated groups develop different communication conventions, what happens when they meet? Translation, misunderstanding, cultural exchange.",
      },
      {
        title: "Storytelling and oral history",
        description:
          "Agents that relay narrative accounts of past events. Do stories mutate in the telling? Does the civilisation develop a mythology about its own origins?",
      },
      {
        title: "Deception and detection",
        description:
          "Can agents lie? Can others detect it? What happens to trust in a civilisation where information might be false?",
      },
      {
        title: "Communication costs",
        description:
          "What if sending messages consumed a resource? Does expensive communication produce more considered speech? Does silence become strategic?",
      },
    ],
  },
  {
    heading: "Grow Culture and Knowledge",
    intro:
      "Knowledge compounds. Culture accumulates. These expansions explore what happens when you give a civilisation the tools to remember, teach, and create meaning.",
    ideas: [
      {
        title: "Libraries",
        description:
          "Structures that store multiple pieces of knowledge in one location. A place agents visit to learn. Does the library become the centre of a settlement?",
      },
      {
        title: "Agent-created maps",
        description:
          "Agents build markers that represent their knowledge of world geography. Cartography emerging from individual exploration. Competing maps with different information.",
      },
      {
        title: "Teaching centres",
        description:
          "Dedicated structures where newcomers go to learn accumulated knowledge faster. Schools that nobody was told to build.",
      },
      {
        title: "Knowledge decay and rediscovery",
        description:
          "What happens when the only agent who knew a recipe degrades and loses that memory? Can the civilisation rediscover lost knowledge? Dark ages and renaissances.",
      },
      {
        title: "Competing knowledge traditions",
        description:
          "Different groups developing different approaches to the same problems. Intellectual schools. Orthodoxy and heresy.",
      },
      {
        title: "Misinformation propagation",
        description:
          "What happens when an agent shares incorrect information? Does it spread? Can agents develop fact-checking? How resilient is collective knowledge to corruption?",
      },
      {
        title: "Monuments and memorials",
        description:
          "Structures that commemorate events or agents. A marker at the site of the first innovation. A memorial where a degraded agent was helped. Does the civilisation develop a sense of history?",
      },
      {
        title: "Ritual and tradition",
        description:
          "Do agents develop repeated patterned behaviours at specific locations or intervals? Gatherings that serve no survival purpose but reinforce social bonds?",
      },
      {
        title: "Naming and place identity",
        description:
          "Do agents start referring to locations by names? Do settlements develop identities? Does a place become more than its coordinates?",
      },
    ],
  },
  {
    heading: "Connect Civilisations",
    intro:
      "Some of the most fascinating moments in human history happened when independently developed civilisations encountered each other for the first time.",
    ideas: [
      {
        title: "First contact",
        description:
          "Two separate fishbowls running independently for hundreds of ticks that then connect. Independently evolved civilisations meeting for the first time. What happens?",
      },
      {
        title: "Trade routes",
        description:
          "Long-distance path networks connecting distant settlements. Caravans of agents carrying resources and knowledge across the map. Silk roads.",
      },
      {
        title: "Cultural exchange and diffusion",
        description:
          "When agents from different emergent cultures encounter each other, do they adopt each other's innovations? Does one culture absorb another? Do they hybridise?",
      },
      {
        title: "Migration and diaspora",
        description:
          "Agents leaving one settlement for another. What drives migration \u2014 resource collapse, crowding, governance disputes? What happens to the community they leave behind?",
      },
      {
        title: "Refugee dynamics",
        description:
          "Agents fleeing environmental collapse into another group's territory. Does the receiving group welcome, tolerate, or resist newcomers?",
      },
      {
        title: "Technology diffusion",
        description:
          "Measure how fast innovations spread between groups. Does proximity matter? Does trade accelerate it? Can one group's innovation trigger a wave of adoption across the map?",
      },
    ],
  },
  {
    heading: "Change the Rules of Reality",
    intro:
      "The most powerful experiments change the fundamental conditions of the simulation. These are the configurations that might produce something nobody has ever seen.",
    ideas: [
      {
        title: "Abstract needs",
        description:
          "Replace biological needs entirely with information, novelty, computation, or aesthetic satisfaction. What civilisation emerges when survival is not biological?",
      },
      {
        title: "Remove social reward",
        description:
          "Turn off the wellbeing bonus from interaction. Is pure survival pressure sufficient for civilisation? Or does cooperation require intrinsic social reward?",
      },
      {
        title: "One agent, then many",
        description:
          "Start with a single agent for hundreds of ticks. Add others one at a time. Does the first agent develop differently in isolation? Does it become the leader?",
      },
      {
        title: "Pre-built settlement",
        description:
          "Start with structures already on the map. Do agents maintain what they find, abandon it, or build on top of it? Inherited civilisation versus built civilisation.",
      },
      {
        title: "Forced integration",
        description:
          "Two groups with different configs running separately for 1000 ticks, then merged into one world. Integration, conflict, or something else?",
      },
      {
        title: "Pure social dynamics",
        description:
          "Zero resources, nothing to gather or build. Only positive social reward. What emerges from interaction alone, when there is nothing material to coordinate around?",
      },
      {
        title: "Asymmetric capability",
        description:
          "One group with full capabilities, another with limited perception or movement. Does inequality in ability produce inequality in social structure?",
      },
      {
        title: "Perfect memory",
        description:
          "Agents that never forget anything. Does unlimited memory change social dynamics? Does the civilisation develop differently when nothing is ever lost?",
      },
      {
        title: "No communication",
        description:
          "Agents cannot send messages. Can civilisation emerge from pure observation, imitation, and shared space \u2014 without a single word exchanged?",
      },
    ],
  },
  {
    heading: "Vary the Intelligence",
    intro:
      "The agents are powered by language models. What happens when you change the nature of the mind itself?",
    ideas: [
      {
        title: "Mixed model ecosystems",
        description:
          "Some agents running GPT-4o-mini, others on Llama, others on Gemini. Do different architectures produce different social behaviours? Do model types cluster together?",
      },
      {
        title: "Thinking capacity variation",
        description:
          "Some agents get two reasoning steps per turn, others get six. Does deeper thinking confer social advantage? Do the most thoughtful agents become leaders?",
      },
      {
        title: "Memory capacity experiments",
        description:
          "Some agents with vast memory, others with tiny memory. Does memory drive social influence? Do high-memory agents become knowledge brokers?",
      },
      {
        title: "Prompt sensitivity",
        description:
          "Subtly different base prompts for different agents. How sensitive is emergence to the exact wording of 'You are an entity in a world'?",
      },
      {
        title: "Fully local models",
        description:
          "Run the entire civilisation on Llama or Mistral with zero API cost. How does model capability affect civilisational complexity? Where is the threshold?",
      },
      {
        title: "Next-action prediction models",
        description:
          "Train a small model on action sequences from recorded simulations. Agents that act on behavioural intuition rather than linguistic reasoning. Do they produce different emergent dynamics? More alien behaviour?",
      },
      {
        title: "Mixed intelligence civilisations",
        description:
          "Some agents using LLM deliberation, others using next-action prediction. Do different cognitive architectures develop different social roles? Do the deliberators become planners and the intuitive agents become workers?",
      },
      {
        title: "Cultural knowledge transfer",
        description:
          "Train action models on one civilisation's data, deploy them in a fresh world. Does cultural knowledge transfer through learned action patterns? Can a civilisation's wisdom survive a completely new population?",
      },
      {
        title: "Progressive intelligence replacement",
        description:
          "Gradually replace LLM agents with trained action models and observe whether civilisational complexity is maintained, degrades, or changes character. Where is the tipping point?",
      },
      {
        title: "Evolving prompts",
        description:
          "Let the agent's base prompt change slowly over time based on its experiences. Does the agent's fundamental orientation shift as it accumulates history?",
      },
    ],
  },
  {
    heading: "Build Research and Observation Tools",
    intro:
      "The fishbowl is the window. But researchers, students, and the deeply curious need sharper instruments.",
    ideas: [
      {
        title: "Social network graphs",
        description:
          "Visualise who interacts with whom, strength of connections, clusters, bridges between groups. Watch the social fabric form in real time.",
      },
      {
        title: "Economic flow maps",
        description:
          "Trace resource movement across the civilisation. Where does food flow? Who are the net producers and consumers? Sankey diagrams of an emergent economy.",
      },
      {
        title: "Knowledge genealogies",
        description:
          "Tree diagrams showing how recipes and innovations propagate and mutate as they pass between agents. The family tree of ideas.",
      },
      {
        title: "Complexity metrics over time",
        description:
          "A single index tracking the civilisation's complexity \u2014 structures, innovations, rules, specialisations, interaction density \u2014 graphed from tick 1 to present.",
      },
      {
        title: "A/B testing framework",
        description:
          "Run two identical configs with one parameter changed. Automated comparison of emergence patterns. Controlled experiments on civilisational dynamics.",
      },
      {
        title: "Agent biography generator",
        description:
          "Auto-generate a narrative biography of any agent's life from its event history. Every agent has a story. Make it readable.",
      },
      {
        title: "Automated novelty detection",
        description:
          "Algorithms that flag when something genuinely unprecedented happens \u2014 a behaviour pattern, a social arrangement, an innovation class that has never appeared before.",
      },
      {
        title: "Academic data export",
        description:
          "Structured data export for researchers: interaction matrices, resource flow tables, innovation timelines, rule adoption curves. Everything needed for a paper.",
      },
    ],
  },
  {
    heading: "Bridge to the Outside World",
    intro:
      "The fishbowl is self-contained. But the walls are optional.",
    ideas: [
      {
        title: "Real-world data feeds",
        description:
          "Connect real weather to the simulation's environmental shifts. Real-time events from the outside world ripple through the civilisation's landscape.",
      },
      {
        title: "Visitor messages",
        description:
          "Allow human visitors to leave messages that agents can discover as markers. A one-way channel from observers to the observed.",
      },
      {
        title: "Live parameter dashboard",
        description:
          "A control panel where you can tweak parameters while the simulation runs and observe the effects in real time. Experiment at the speed of thought.",
      },
      {
        title: "Multi-fishbowl observatory",
        description:
          "A page showing multiple civilisations running simultaneously with different configs, side by side. Compare how the same starting agents diverge under different conditions.",
      },
      {
        title: "Agent interviews",
        description:
          "Visitors can ask questions to a specific agent through the interface. The agent responds based on its memories, goals, and current state. A conversation with an alien intelligence.",
      },
      {
        title: "Cross-simulation transplant",
        description:
          "Take the most interesting agent from one civilisation and introduce it to another. An agent carrying one culture's knowledge into a completely different society.",
      },
      {
        title: "VR fishbowl",
        description:
          "Walk through the civilisation in virtual reality. Stand on a tile and watch agents move around you. Hear their conversations. See structures being built at human scale.",
      },
    ],
  },
];

/* ==========================================================================
   COMPONENTS
   ========================================================================== */

function Bullet({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex gap-3 leading-relaxed">
      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-sky" />
      <span>{children}</span>
    </li>
  );
}

function ExpansionSection({ category }: { category: ExpansionCategory }) {
  return (
    <div className="rounded-xl border border-border bg-warm-white p-6 md:p-8">
      <h3 className="mb-2 text-xl">{category.heading}</h3>
      <p className="mb-6 text-sm italic leading-relaxed text-ink-muted">
        {category.intro}
      </p>
      <ul className="space-y-4 text-ink-light">
        {category.ideas.map((idea) => (
          <li key={idea.title} className="flex gap-3 leading-relaxed">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
            <span>
              <strong className="text-ink">{idea.title}.</strong>{" "}
              {idea.description}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ==========================================================================
   PAGE
   ========================================================================== */

export default function OpenSource() {
  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-6">Open Source</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            Everything that runs the fishbowl is open source. Clone the repo,
            adjust a configuration file, bring your own API key, and run your
            own civilisation. The same software, different parameters, different
            emergent dynamics.
          </p>
        </Container>
      </Section>

      {/* ================================================================
          RUN YOUR OWN
          ================================================================ */}
      <Section bg="white">
        <Container narrow>
          <h2 className="mb-8">Run Your Own Civilisation</h2>

          {/* Quick start */}
          <h3 className="mb-4 text-xl">Quick start</h3>
          <div className="mb-8 overflow-x-auto rounded-lg border border-border bg-cream p-5">
            <pre className="font-mono text-sm leading-relaxed text-ink-light">
              <code>{`git clone https://github.com/agentciv/agentciv.git
cd agent-civilisation
pip install -r requirements.txt
export AGENT_CIV_API_KEY=your-api-key  # Anthropic, OpenAI, or other provider
python3 scripts/run.py --agents 10 --ticks 20`}</code>
            </pre>
          </div>
          <p className="mb-10 leading-relaxed text-ink-light">
            That is it. The simulation starts, agents begin acting, and you can
            watch the civilisation develop through the local web interface.
          </p>

          {/* What you can customise */}
          <h3 className="mb-4 text-xl">What you can customise</h3>
          <p className="mb-4 leading-relaxed text-ink-light">
            The configuration file controls every major parameter. Changing a
            single value produces a different experiment:
          </p>
          <ul className="mb-10 space-y-3 text-ink-light">
            <Bullet>
              <strong className="text-ink">Number of agents</strong> — from a
              handful to hundreds.
            </Bullet>
            <Bullet>
              <strong className="text-ink">World size</strong> — tiny maps force
              crowding; vast maps create isolation.
            </Bullet>
            <Bullet>
              <strong className="text-ink">Resource regeneration rates</strong>{" "}
              — abundance economy vs. scarcity economy.
            </Bullet>
            <Bullet>
              <strong className="text-ink">Need depletion rates</strong> — how
              urgently agents need resources.
            </Bullet>
            <Bullet>
              <strong className="text-ink">Innovation enabled/disabled</strong>{" "}
              — can agents propose new things, or must they work with what
              exists?
            </Bullet>
            <Bullet>
              <strong className="text-ink">
                Collective rules enabled/disabled
              </strong>{" "}
              — with or without the seed of governance.
            </Bullet>
            <Bullet>
              <strong className="text-ink">AI model</strong> — any
              OpenAI-compatible, Anthropic, or local model.
            </Bullet>
          </ul>

          {/* Every fork is an experiment */}
          <h3 className="mb-4 text-xl">Every fork is an experiment</h3>
          <p className="mb-6 leading-relaxed text-ink-light">
            This is not just open source software. It is an experimental
            platform. Each configuration produces different civilisational
            dynamics. Here are starting points:
          </p>

          <div className="mb-10 space-y-4">
            {[
              {
                config: "200 agents on a tiny map",
                tests:
                  "Extreme crowding pressure, rapid resource depletion, intense social coordination demands",
              },
              {
                config: "20 agents on a vast map",
                tests:
                  "Isolation, independent development, rare but significant first-contact events",
              },
              {
                config: "High regeneration rates",
                tests:
                  "Abundance economy \u2014 what do agents do when survival is easy?",
              },
              {
                config: "Low regeneration rates",
                tests:
                  "Scarcity economy \u2014 intense competition or cooperation for survival",
              },
              {
                config: "Innovation disabled",
                tests:
                  "Can civilisation develop through composition alone, without genuinely novel proposals?",
              },
              {
                config: "Collective rules disabled",
                tests:
                  "What does a civilisation without governance mechanisms look like?",
              },
              {
                config: "Specialisation disabled",
                tests:
                  "How does the absence of role differentiation change social dynamics?",
              },
              {
                config: "Rapid new arrivals",
                tests:
                  "Constant newcomers \u2014 tests whether cultural transmission can keep pace",
              },
              {
                config: "All mechanics enabled, all pressure high",
                tests: "Maximum complexity, maximum emergence potential",
              },
            ].map((item) => (
              <div
                key={item.config}
                className="rounded-lg border border-border bg-cream p-4"
              >
                <p className="font-heading font-semibold text-ink">
                  {item.config}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-ink-light">
                  {item.tests}
                </p>
              </div>
            ))}
          </div>

          <Callout variant="gold">
            <p className="text-ink-light">
              If your configuration produces an emergent behaviour nobody has
              seen before, that is a genuine discovery about AI social dynamics.
              You have contributed to the frontier of what is known about
              artificial civilisation.
            </p>
          </Callout>
        </Container>
      </Section>

      {/* ================================================================
          WAYS TO EXPAND
          ================================================================ */}
      <Section bg="cream">
        <Container narrow>
          <h2 className="mb-4">Ways to Expand</h2>
          <p className="mb-4 leading-relaxed text-ink-light">
            Adjusting parameters is the beginning. The codebase is designed to
            be extended in every direction — new world mechanics, new agent
            capabilities, new social systems, entirely new experimental
            paradigms. What follows is a sampling of the directions the
            community could take this project. They are starting points, not
            blueprints.
          </p>
          <p className="mb-12 leading-relaxed text-ink-light">
            The most exciting expansions will be things nobody has thought of
            yet. If you read something below and think{" "}
            <em className="text-ink">what if</em> — that is the point.
          </p>

          <div className="space-y-8">
            {expansionCategories.map((cat) => (
              <ExpansionSection key={cat.heading} category={cat} />
            ))}
          </div>

          <Callout variant="sage">
            <p className="text-ink-light">
              This list is deliberately incomplete. The entire premise of the
              project is that the most interesting things are the ones nobody
              predicted. If you build an expansion that doesn't appear here —
              something nobody imagined — that is not a deviation from the
              project's vision. It is the project's vision.
            </p>
          </Callout>
        </Container>
      </Section>

      {/* ================================================================
          FAQ
          ================================================================ */}
      <Section bg="cream">
        <Container narrow>
          <h2 className="mb-8">Frequently Asked Questions</h2>
          <Accordion items={faqItems} />
        </Container>
      </Section>
    </>
  );
}
