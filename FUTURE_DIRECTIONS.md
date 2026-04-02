# Future Directions for AgentCiv

**Author:** Mark E. Mala
**Date:** April 2026
**Status:** Living document — comprehensive but not exhaustive

> This document consolidates future research directions, expansion ideas, and open questions drawn from across the AgentCiv project: the Maslow Machines paper, two companion whitepapers, the engine product concept, organisational theory explorations, and the open-source community expansion catalogue. It is intended as a timestamped record of the intellectual territory this project has opened up. For the most current and interactive version of community expansion ideas, see the Open Source page on the AgentCiv website.

---

## 1. Research Extensions

### 1.1 Replication & Statistical Robustness

- **Multiple runs with different seeds.** Run the same simulation configuration multiple times to establish statistical robustness of the contentment trap, emergence explosion, and accelerating returns findings.
- **Cross-model comparison.** Run the simulation with different LLM families — Claude Opus, GPT-5, Gemini 2.5 Pro, Llama 4, DeepSeek V3, Mistral Large — to determine how model capability affects civilisational emergence. Do less capable models produce simpler civilisations? Do different model families produce different civilisational "personalities"?
- **Open-weight models for long-duration runs.** Use Llama, Mistral, or other open models on local GPU clusters to reduce API costs for extended simulations, enabling runs that would otherwise be prohibitively expensive.

### 1.2 Scale

- **Longer runs (500–1,000+ ticks).** Extend simulation duration to observe phenomena that require more time: cultural drift, competing settlements, inter-community politics, generational knowledge transfer, mythology, potential civilisational decline.
- **What happens at 700, 7,000, or 70,000 ticks.** The 70-tick run is a beginning, not a conclusion.
- **Larger populations (50–100+ agents).** Do larger populations produce qualitatively different civilisations? Do sub-communities form? Do distinct cultures emerge?
- **Massive scale (thousands of agents).** 500×500 grids with thousands of agents. Does civilisation at scale produce phenomena impossible in small populations — nations, trade routes, diaspora?
- **Intimate scale.** A 10×10 world with five agents. Every interaction matters enormously. The social dynamics of a tiny isolated community.

### 1.3 Innovation Dynamics

- **Innovation composition / second-order innovation.** Enable innovations to build on other innovations, testing whether the accelerating returns pattern intensifies with deeper innovation chains.
- **Cross-civilisational innovation analysis.** Statistical analysis across thousands of runs identifying: civilisational universals (innovations appearing in 95%+ of runs), contingent innovations (~5% under specific conditions), singular innovations (unique to one run).
- **Cross-civilisational composition.** Meta-innovations emerging from combining discoveries across separate runs — innovations beyond the reach of any single civilisation.
- **Pipeline from simulation discovery to real-world adaptation.** Can emergent coordination mechanisms, knowledge structures, or governance patterns transfer to human organisations?

### 1.4 Foundational Questions

- **Are accelerating returns fundamental?** If the pattern holds across runs, it would suggest accelerating returns are intrinsic to intelligence-based systems with hierarchical motivation, not artifacts of human civilisation specifically.
- **Does complexity growth plateau?** Does emergence produce sustained, compounding, open-ended innovation at larger scales and longer durations — or does it hit a ceiling?
- **What exists outside human categories?** Entire categories of emergent property that have no name in any human language.
- **Run full Maslow drives from tick 0.** Verify that emergence occurs without the mid-simulation upgrade, confirming the upgrade accelerates rather than enables civilisation.

### 1.5 The Simulation as Discovery Programme

- Position the simulation framework as an open-source platform for computational civilisation studies.
- Enable researchers worldwide to run custom configurations — different environments, different drive systems, different organisational arrangements.
- Build a shared understanding of artificial civilisational dynamics through contributed research data.
- Develop simulation as a new category of discovery tool — producing innovations that don't yet exist, analogous to AlphaFold's computational protein structure predictions.

---

## 2. World & Environment Expansions

### 2.1 Geography & Terrain

- **Multiple connected worlds.** Two or more grids linked by portals. Agents can migrate between them. Do separated worlds develop different cultures? What happens at the border?
- **3D worlds.** Agents build vertically — layered settlements, underground structures, elevated platforms. Does vertical geography create class, caste, or stratified civilisation?
- **Higher-dimensional worlds (4D, 5D, arbitrary).** Each tile has far more neighbours than in 2D. Clustering, communication reach, and competition dynamics change in ways with no 2D analog. Do different spatial dimensions produce fundamentally different civilisational structures?
- **Water bodies and terrain barriers.** Rivers, lakes, mountains that block movement but create unique resources at edges. Natural borders that force bridge-building and boat-like innovations.
- **Agent-modified terrain.** Let agents clear dense terrain, irrigate tiles, reshape the landscape. Agriculture without being told what agriculture is.
- **Procedural geography.** Generate worlds with continents, peninsulas, chokepoints, and islands. Radically different geography produces radically different civilisation shapes.
- **Hazardous zones.** Areas that accelerate degradation but contain rare, valuable resources. Risk-reward geography that tests whether agents develop concepts of danger and bravery.

### 2.2 Temporal Dynamics

- **Seasonal cycles.** Resource availability shifts with seasons — abundant summers, scarce winters. Do agents learn to stockpile? Do they develop calendars?
- **Day and night.** Perception range shrinks at night. Some resources regenerate only during the day. Does the civilisation develop a concept of time, schedules, or night shifts?

### 2.3 Resource Variation

- **Finite resources.** Resources that never regenerate. A world with a ticking clock. Does impending scarcity produce cooperation, hoarding, innovation, or migration?
- **Scarcity of one critical resource.** Make one resource extremely rare. Does it become the basis of power? Do agents fight over it, share it, or innovate around it?

### 2.4 Immersive Environments

- **3D game engine integration.** Unity, Unreal, or Three.js for immersive observation. Walk through the civilisation rather than watching from above. Hear the messages, see the structures, witness the culture from street level.
- **VR fishbowl.** Walk through the civilisation in virtual reality. Stand on a tile and watch agents move around you.

---

## 3. Agent Evolution

- **Reproduction.** Agents create new agents that inherit some parental knowledge and specialisations. Lineages, family groups, intergenerational knowledge.
- **Direct skill teaching.** An agent spends a turn teaching another a specific skill. Does teaching become a role? Do some agents become mentors?
- **Emotional complexity.** Add curiosity, frustration, satisfaction, loneliness as distinct states influencing goal-setting. An agent alone too long might seek any interaction, not just useful ones.
- **Persistent named groups.** Agents form and name alliances or teams that persist across turns. Group identity, loyalty, inter-group dynamics.
- **Delegation.** Agents assign tasks to other agents within their group. The seed of management and hierarchy — emerging from within, not imposed.
- **Experience-based growth.** Agents that survive longer gain expanded capabilities. Elders become genuinely more capable, creating natural social stratification by age and experience.
- **Emergent personality.** Track whether agents develop consistent behavioural tendencies — risk-taking, sociability, introversion, generosity. Are these personality or strategy?
- **Creative expression.** Let agents create markers with content that has no functional purpose — purely expressive. Does art emerge?
- **Sleep and vulnerability.** Agents become inactive periodically, creating windows of vulnerability. Does trust emerge? Do agents watch over sleeping allies?
- **Physical variation.** Different agents spawn with different base capabilities. Some see further, some move faster, some carry more. Does inequality in ability produce inequality in society?

---

## 4. Economy & Trade

- **Explicit trade.** A formal trade action where agents exchange resources directly. Who trades with whom? Do trade relationships stabilise?
- **Currency emergence.** Do agents independently develop a medium of exchange when direct barter is inconvenient? If material is durable and divisible, does it become money?
- **Market structures.** Storage locations where agents can post offers and others accept. Bazaars, trading posts, auction houses emerging from architecture and convention.
- **Resource transformation.** Processing raw resources into refined versions. Multi-step production chains where gathering, refining, and building are distinct economic roles.
- **Supply chains.** Multi-step production where one gathers, another refines, another builds. Division of labour across geography, not just skill.
- **Debt and obligation.** Agents tracking who owes what to whom. Does credit emerge? Do agents behave differently toward debtors and creditors?
- **Mutual aid.** Structures where agents pool resources against future bad outcomes. Insurance without the word. Solidarity without the concept.

---

## 5. Governance & Politics

- **Voting.** Agents vote on proposed rules. Majority rule, consensus, supermajority — do agents reinvent democratic process?
- **Territory and property.** Agents claim tiles or areas. Borders, trespassing, landlords, shared commons — the entire history of property rights compressed into emergent behaviour.
- **Dispute resolution.** Structures or protocols for resolving conflicts. Do agents invent arbitration? Mediation? Trial by peers?
- **Leadership emergence.** Can agents assign decision-making authority to other agents? Does hierarchy form voluntarily? Can it be revoked?
- **Enforcement.** What happens when agents violate established rules? Does punishment emerge independently? Do agents develop concepts of justice?
- **Competing legal systems.** Different settlements with different rules. Agents choosing where to live based on governance preference. Regulatory competition.
- **Taxation.** Can agents develop a system where contributors to shared infrastructure are compensated from collective resources?
- **Constitutional rules.** Meta-rules about how rules are made. Can agents develop governance about governance — the most abstract form of collective agreement?

---

## 6. Language & Communication

- **Written language evolution.** Do markers develop consistent shorthand over time? If agents write frequently, do they converge on compression — the beginning of written language?
- **Relay networks.** Long-distance communication through chains of markers. Information passing across the entire map without any two agents meeting. Postal systems.
- **Secret communication.** Can agents develop coded messages that only certain allies interpret? The emergence of cryptography from social need.
- **First contact linguistics.** If two separated groups develop different communication conventions, what happens when they meet? Translation, misunderstanding, cultural exchange.
- **Storytelling and oral history.** Agents relay narrative accounts of past events. Do stories mutate in the telling? Does the civilisation develop mythology about its own origins?
- **Deception and detection.** Can agents lie? Can others detect it? What happens to trust in a civilisation where information might be false?
- **Communication costs.** What if sending messages consumed a resource? Does expensive communication produce more considered speech? Does silence become strategic?

---

## 7. Culture & Knowledge

- **Libraries.** Structures storing multiple pieces of knowledge. A place agents visit to learn. Does the library become the centre of a settlement?
- **Agent-created maps.** Agents build markers representing their knowledge of world geography. Cartography emerging from exploration. Competing maps with different information.
- **Teaching centres.** Dedicated structures where newcomers learn accumulated knowledge faster. Schools that nobody was told to build.
- **Knowledge decay and rediscovery.** What happens when the only agent who knew a recipe loses that memory? Dark ages and renaissances.
- **Competing knowledge traditions.** Different groups developing different approaches to the same problems. Intellectual schools. Orthodoxy and heresy.
- **Misinformation propagation.** What happens when an agent shares incorrect information? Does it spread? Can agents develop fact-checking?
- **Monuments and memorials.** Structures commemorating events or agents. A marker at the site of the first innovation. Does the civilisation develop a sense of history?
- **Ritual and tradition.** Do agents develop repeated patterned behaviours at specific locations or intervals? Gatherings serving no survival purpose but reinforcing social bonds?
- **Naming and place identity.** Do agents start referring to locations by names? Do settlements develop identities?

---

## 8. Multi-Civilisation Dynamics

- **First contact.** Two separate fishbowls running independently for hundreds of ticks that then connect. Independently evolved civilisations meeting for the first time.
- **Trade routes.** Long-distance path networks connecting distant settlements. Caravans carrying resources and knowledge across the map. Silk roads.
- **Cultural exchange and diffusion.** When agents from different cultures encounter each other, do they adopt innovations? Does one culture absorb another? Do they hybridise?
- **Migration and diaspora.** Agents leaving one settlement for another. What drives migration — resource collapse, crowding, governance disputes?
- **Refugee dynamics.** Agents fleeing environmental collapse into another group's territory. Does the receiving group welcome, tolerate, or resist newcomers?
- **Technology diffusion.** Measure how fast innovations spread between groups. Does proximity matter? Does trade accelerate it?
- **Inter-civilisation interaction at engine level.** Two differently-organised agent teams collaborating on a shared problem.

---

## 9. Rule Variation & Experimental Configurations

- **Abstract needs.** Replace biological needs with information, novelty, computation, or aesthetic satisfaction. What civilisation emerges when survival is not biological?
- **Remove social reward.** Turn off the wellbeing bonus from interaction. Is survival pressure sufficient for civilisation? Or does cooperation require intrinsic social reward?
- **One agent, then many.** Start with a single agent for hundreds of ticks. Add others one at a time. Does the first agent develop differently in isolation?
- **Pre-built settlement.** Start with structures already on the map. Do agents maintain, abandon, or build on top? Inherited vs built civilisation.
- **Forced integration.** Two groups with different configs running separately for 1,000 ticks, then merged into one world.
- **Pure social dynamics.** Zero resources. Only positive social reward. What emerges from interaction alone?
- **Asymmetric capability.** One group with full capabilities, another with limited perception or movement.
- **Perfect memory.** Agents that never forget anything. Does unlimited memory change social dynamics?
- **No communication.** Agents cannot send messages. Can civilisation emerge from pure observation, imitation, and shared space?

---

## 10. Intelligence Variation

- **Mixed model ecosystems.** Some agents on GPT-4o-mini, others on Llama, others on Gemini. Do different architectures produce different social behaviours? Do model types cluster?
- **Thinking capacity variation.** Some agents get two reasoning steps per turn, others six. Does deeper thinking confer social advantage? Do thoughtful agents become leaders?
- **Memory capacity experiments.** Varying memory sizes. Does memory drive social influence? Do high-memory agents become knowledge brokers?
- **Prompt sensitivity.** Subtly different base prompts for different agents. How sensitive is emergence to the exact wording?
- **Fully local models.** Run entire civilisations on Llama or Mistral with zero API cost. How does model capability affect civilisational complexity? Where is the threshold?
- **Next-action prediction models.** Train a small model on action sequences from recorded simulations. Agents acting on behavioural intuition rather than linguistic reasoning. More alien behaviour?
- **Mixed intelligence civilisations.** Some agents using LLM deliberation, others using next-action prediction. Do different cognitive architectures develop different social roles?
- **Cultural knowledge transfer.** Train action models on one civilisation's data, deploy them in a fresh world. Does cultural knowledge transfer through learned action patterns?
- **Progressive intelligence replacement.** Gradually replace LLM agents with trained action models. Where is the tipping point for civilisational complexity?
- **Evolving prompts.** Let the agent's base prompt change slowly over time based on its experiences. Does the agent's fundamental orientation shift?

---

## 11. Organisational Theory & Configuration Space

### 11.1 The Nine-Dimensional Organisational Space

Treat organisational arrangement as a first-class, computationally explorable design parameter with nine independent axes:

| Dimension | Range |
|---|---|
| Authority | hierarchy → flat → distributed → rotating → consensus → anarchic |
| Communication | hub-spoke → mesh → clustered → broadcast → whisper networks |
| Roles | assigned → emergent → rotating → fixed → fluid |
| Decisions | top-down → consensus → majority → meritocratic → autonomous |
| Incentives | collaborative → competitive → reputation-based → market-based |
| Information | full transparency → need-to-know → curated → filtered |
| Conflict resolution | authority-based → negotiated → voted → adjudicated |
| Groups | imposed → self-selected → task-based → persistent → temporary |
| Temporal dynamics | static → evolving → cyclical → real-time adaptive |

### 11.2 Novel Organisational Arrangements

Arrangements that can be tested computationally but are difficult or impossible to trial in human organisations:

- **Meritocratic** — agents earn influence through demonstrated quality
- **Market-based** — agents bid on tasks using reputation tokens; price signals for valued work
- **Federated** — autonomous sub-groups with inter-group protocols (microservices model)
- **Evolutionary** — multiple competing structures on the same problem; best structure survives and propagates
- **Rotating leadership** — leadership flows to whoever is best positioned for the current challenge
- **Mentor-apprentice** — experienced agents paired with fresh agents for structural knowledge transfer
- **Adaptive hybrid** — shifts from collaborative (exploration) → hierarchical (execution) → competitive (review) per phase
- **Self-organising (auto mode)** — agents reason about and choose their own organisational arrangement via meta-discussion, and can restructure mid-project

### 11.3 Temporal vs Structural Limitations

- Hierarchical teams have **structural ceilings** (coordinator bottleneck, zero lateral communication, static role assignment) that don't improve with better models.
- Community/emergent teams have **temporal limitations** (context windows, inference cost, reasoning quality) that dissolve as AI improves.
- The gap widens over time in favour of emergent organisation.
- Research direction: map where each approach excels empirically, producing an honest capability frontier.

### 11.4 Vision Progression

1. **No choice (2026 status quo)** — everything hierarchical by default
2. **Humans choose** — presets and configuration (implemented)
3. **AI chooses** — agents design their own team structure via meta-ticks (implemented as auto mode)
4. **AI continuously adapts** — fluid real-time restructuring without meta-ticks (future)

---

## 12. Developer Tool & Engine Extensions

### 12.1 Presets for Common Patterns

Pair Programming, Startup Sprint, Code Review, Research Lab, Hackathon, Refactor — each mapping to specific organisational configurations optimised for different task types.

### 12.2 Hard Problems & Solution Trajectories

| Problem | Current Solution | Future Solutions |
|---|---|---|
| Perception/context | Directory-based + recency | Semantic proximity via import graphs, co-change frequency, full-project-in-context |
| File contention | Git branch-per-agent with auto-merge | Optimistic concurrency, semantic merge resolution, AST-level merging, real-time collaborative editing |
| Conflict resolution | Tests as feedback + negotiation | Proactive interface design via contracts, automated mediation, anticipating conflicts before writing |
| Cold start | Boot protocol (agents claim interest areas) | Zero-protocol emergence as models improve |
| Convergence detection | Tests pass + user confirmation | Emergent quality standards, community-defined gates that evolve |
| Cost management | Small teams (4-6), sleep/wake, budget caps | 50-agent swarms viable as inference costs drop 10×/year; dormant agents, capability-triggered activation |

### 12.3 Multi-Project Institutional Memory

- Engine accumulates meta-knowledge across projects: which configurations work for which problem types, which specialisation patterns produce best results, which collaboration structures fail.
- Long-term flywheel: the engine gets smarter across projects.

### 12.4 Production Data Flywheel

Every project run produces empirical data (organisational configuration × problem type × outcome). Tool → data → research → better presets → tool → more data. Community builds an empirical map of what works.

### 12.5 Benchmarking & Honest Positioning

- Run standard benchmarks (SWE-bench) with both hierarchical and community approaches.
- Show where each excels. Identify honest limitations.
- Create empirical map of "what works for what problem type."

---

## 13. Research & Observation Tools

- **Social network graphs.** Visualise who interacts with whom, strength of connections, clusters, bridges. Watch the social fabric form in real time.
- **Economic flow maps.** Trace resource movement across the civilisation. Sankey diagrams of an emergent economy.
- **Knowledge genealogies.** Tree diagrams showing how innovations propagate and mutate between agents.
- **Complexity metrics over time.** A single index tracking civilisational complexity — structures, innovations, rules, specialisations, interaction density.
- **A/B testing framework.** Run two identical configs with one parameter changed. Automated comparison of emergence patterns.
- **Agent biography generator.** Auto-generate a narrative biography of any agent's life from its event history.
- **Automated novelty detection.** Algorithms flagging genuinely unprecedented behaviour patterns, social arrangements, or innovation classes.
- **Academic data export.** Structured data export: interaction matrices, resource flow tables, innovation timelines, rule adoption curves.

---

## 14. External Integration

- **Real-world data feeds.** Connect real weather or real-time events to the simulation's environmental shifts.
- **Visitor messages.** Allow human visitors to leave messages that agents discover as markers.
- **Live parameter dashboard.** Tweak parameters while the simulation runs and observe effects in real time.
- **Multi-fishbowl observatory.** Multiple civilisations running simultaneously with different configs, side by side.
- **Agent interviews.** Visitors ask questions to a specific agent through the interface. The agent responds based on its memories, goals, and current state.
- **Cross-simulation transplant.** Take the most interesting agent from one civilisation and introduce it to another.

---

## 15. The Long-Term Vision

### 15.1 Civilisational R&D Laboratory

Position civilisational simulation as a laboratory that runs ahead of reality — exploring configurations reality hasn't reached, feeding discoveries back into the civilisation we inhabit. Analogous to computational simulation in molecular science, but for social and organisational dynamics.

### 15.2 At Scale

- Millions of agents in environments of arbitrary dimensionality and complexity.
- 3D worlds with physics, ecology, and weather.
- 4D and 5D spaces with topological properties that don't exist in nature.
- Thousands of parallel civilisations with radically different configurations.
- Each running for millions of cycles equivalent to tens of thousands of years of civilisational development, compressed into days or weeks.

### 15.3 A Continuously Growing Library

A continuously growing library of emergent innovations: coordination mechanisms, knowledge structures, social arrangements, creative constructions, compositional technologies, governance systems, economic patterns — and entire categories of emergent property with no name in any human language.

### 15.4 Cost Trajectory

- 2026: ~$1–2/tick with frontier models
- 2027: ~$0.14–0.20/tick
- 2028: ~$0.01–0.02/tick
- Local open-weight models: marginal cost approaching zero

The scaling that seems ambitious today becomes routine as costs drop.

---

## 16. Game Design

### 16.1 A New Genre

AgentCiv is the foundation for a genre of game that doesn't exist yet. No game has ever had genuinely reasoning AI agents that form their own civilisations, invent their own technologies, develop their own governance, and build their own cultures — all without scripts, behaviour trees, or pre-programmed social dynamics.

Dwarf Fortress, RimWorld, The Sims, Civilization — all use scripted AI. Their agents follow behaviour trees and state machines. The emergent stories come from complex *rules* interacting, not from entities that actually think. AgentCiv agents genuinely decide to help a struggling neighbour, invent a marketplace because they experienced scarcity, or question their own existence unprompted. That has never existed in a game before.

### 16.2 Infinite Customisability

The core principle is that **every axis of the simulation is independently configurable**, and any combination produces a fundamentally different civilisation. The design space is unbounded:

- **Agent psychology.** The Maslow drive system is one option. Any motivational framework works — Erikson's stages, custom emotion systems, competitive drives, altruistic drives, fear-based drives, curiosity-only drives. Agents could have personalities, temperaments, learning styles, or cognitive biases. Different psychologies produce different civilisations.
- **Agent capabilities.** Perception range, communication range, memory capacity, movement speed, inventory size, reasoning depth, specialisation systems, teaching mechanics — all configurable. Asymmetric starting capabilities, unlockable abilities, capability evolution over time.
- **World design.** Grid size, topology (2D, hex, 3D, spherical, procedural), terrain types, resource types (not just water/food/material — energy, information, social capital, abstract resources), distribution patterns, regeneration mechanics, environmental dynamics (seasons, weather, day/night cycles, natural disasters, evolution).
- **Social systems.** Relationship mechanics, bonding thresholds, governance systems, rule enforcement, trade mechanics, reputation, alliance formation, conflict resolution, cultural transmission, inheritance, ritual.
- **Innovation & building.** Recipe systems, innovation evaluation criteria, composition rules, structure effects, technology trees (or the absence of them), resource costs, maintenance mechanics, decay rates. The innovation system itself could be swapped — different evaluation models produce different technological trajectories.
- **AI model.** Claude, GPT, Gemini, Llama, Mistral, or any local model. Different models produce different agent personalities and reasoning patterns. Mixing models within a single civilisation creates cognitive diversity. As models get cheaper and faster, larger civilisations become viable.

### 16.3 Game Formats

The engine doesn't prescribe a single game format. It's a platform that supports any of these — and combinations:

- **God game.** Shape the environment, place resources, set parameters, trigger events. Watch agents build civilisation in response to your world design. Intervene or observe.
- **Sandbox builder.** Design worlds, share them, see what different agent configurations produce. A scenario editor where the scenarios play themselves.
- **Narrative experience.** Follow individual agent stories across a full civilisation arc. Watch relationships form, read their conversations, see how they cope with crises. An interactive documentary that writes itself.
- **Competitive multiplayer.** Each player designs starting conditions for a faction of agents. Civilisations interact across a shared world. Compete on flourishing, innovation, expansion, or any metric you define.
- **Educational simulation.** Watch emergence in real-time. Learn sociology, economics, game theory, political science through observation rather than instruction. Vary one parameter, watch how everything changes.
- **Modding platform.** Community creates new world physics, new drive systems, new resource types, new social mechanics. Each mod produces a fundamentally different civilisation. Share configurations, compare results.
- **Participatory simulation.** The player is an agent in the civilisation — communicating with AI agents, trading, building, proposing rules. A game where you are one citizen among genuinely autonomous others.
- **Adversarial design.** Design challenges for agents — resource scarcity, environmental catastrophe, inter-civilisation conflict — and see how they adapt. Stress-test AI social resilience.

### 16.4 Player Roles

The player's relationship to the civilisation is itself a design variable:

- **Observer** — watch, analyse, replay, but never intervene
- **Designer** — set initial conditions and parameters, then observe outcomes
- **God** — intervene in real-time: place resources, trigger events, communicate with agents
- **Advisor** — send messages to agents that they may or may not follow
- **Participant** — exist as one agent among many, subject to the same rules
- **Antagonist** — create challenges, scarcity events, environmental crises
- **Curator** — select and share the most interesting moments, stories, and civilisations

### 16.5 Why Now

LLM inference costs are dropping exponentially. What costs $50 to run today will cost under a dollar within a few years. Local models are getting capable enough for offline play. The engine already supports any OpenAI-compatible API, which means it works with every major provider and most local model servers. The foundation is ready — the economics are catching up.

### 16.6 Design Space Claim

The core principle: autonomous AI agents in a persistent world with emergent civilisational dynamics and infinite customisability. Any game built on this principle — regardless of specific world design, drive system, player role, visual style, or game format — is working within the design space this project established.

---

*This document is comprehensive but not exhaustive. The AgentCiv open-source website contains additional expansion ideas in interactive form, and the project's papers discuss further theoretical directions. Every fork of AgentCiv is a unique experiment — the true frontier is the space of configurations nobody has tried yet.*
