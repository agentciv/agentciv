# From Agent Teams to Agent Civilisations: Emergent Collective Intelligence as a New Dimension in Artificial Intelligence

**Mark E. Mala**
April 2026

*Part of the AgentCiv research programme. Companion publications: [Civilisation as Innovation Engine](civilisation_as_innovation_engine.md) (Whitepaper II), [Maslow Machines](maslow_machines.md) (Paper III — empirical evidence).*

---

## Abstract

The dominant paradigm in multi-agent artificial intelligence is designed collaboration: architects assign roles, define coordination protocols, and structure agent teams. This paper proposes that designed collaboration represents one stage in a broader trajectory — from isolated AI models to self-organising societies of generally intelligent agents. We present a four-stage framework: Narrow AI, General-Purpose AI, Specialised General Intelligence Teams, and Emergent Agent Civilisation. Drawing on research in open-ended evolution (OEE) and Stuart Kauffman's theory of the adjacent possible, we argue that emergent self-organisation of generally intelligent agents under environmental pressure opens a new dimension in the design space for AI systems — one where individual intelligence and collective complexity rise together, each amplifying the other. We identify LLM-based agentic AI as a novel substrate for open-ended emergence, overcoming limitations that have caused previous artificial life systems to plateau. We propose six design principles for systems capable of unbounded civilisational complexity growth, address alignment considerations unique to emergent multi-agent systems, and present AgentCiv (agentciv.ai) as a first open source experiment investigating these ideas. Results from a completed 70-tick simulation with 12 agents — documented in detail in the companion empirical paper *Maslow Machines* (Mala, 2026) — demonstrate spontaneous emergence of 60 persistent structures, 12 agent-conceived innovations, universally adopted self-governance, tiered multi-domain specialisation, and wellbeing convergence to 0.998, all without prescriptive instruction. This paper does not propose emergent civilisation as a replacement for other approaches but as one trajectory in an infinite possibility space.

---

## 1. Introduction

### 1.1 The Current Moment

Artificial intelligence is in the midst of a rapid architectural transition. Between 2023 and 2026, the field has moved from single models performing isolated tasks to an ecosystem of AI agents collaborating on complex workflows. The trajectory has been swift: Stanford's generative agents experiment in 2023 showed that LLM-powered characters could simulate believable social behaviour; by 2025, enterprise frameworks like LangChain, CrewAI, AutoGen, and Microsoft's Semantic Kernel enabled production-grade agent teams; by early 2026, standardisation of protocols like MCP (Model Context Protocol) and AGENTS.md signalled that agentic AI had moved from experiment to infrastructure. The appetite for autonomous AI agents is enormous and immediate.

This represents genuine progress. A well-designed agent team can accomplish tasks that no single model could, not because the individual models are more powerful but because the collaborative structure enables decomposition, specialisation, and parallel execution. The analogy to human organisations is intentional and instructive: human civilisation is built on the principle that coordinated specialists outperform isolated generalists.

But there is a subtle and consequential observation about the current paradigm: the collaborative structure itself is specified in advance. An architect — human or AI — decides that there will be a lead agent and three sub-agents. Someone or something decides which sub-agent handles which task. The coordination protocol is defined before the work begins. The agents are generally intelligent, but the structure they operate within is prescribed.

This paper asks: what if we also explored what happens when the structure isn't prescribed? What if, alongside designing agent teams, we also designed the conditions under which agent teams design themselves?

### 1.2 The Thesis

We propose that alongside the continued advancement of individual AI models and designed agent teams, a new region of the design space is opening: emergent civilisations of generally intelligent agents that self-organise under the right conditions. In the same way that human civilisation was not designed by any architect but emerged from the interaction of intelligent beings under environmental pressure, artificial civilisation may emerge from the interaction of artificially intelligent agents under analogous conditions.

This is not a metaphor. It is a concrete architectural proposal with implications for how we develop, deploy, and think about advanced AI systems. The path toward artificial general intelligence and artificial superintelligence likely runs through multiple parallel trajectories: more capable individual models, better designed agent teams, *and* the creation of conditions under which intelligence organises itself into civilisational structures. This paper focuses on the third trajectory — not because the others are less important, but because it is the least explored and may hold the most surprising discoveries.

### 1.3 Structure of This Paper

Section 2 presents a four-stage framework for AI collaboration architecture. Section 3 examines why emergent approaches complement designed collaboration. Section 4 draws on open-ended evolution research to identify the conditions under which unbounded emergent complexity can arise. Section 5 proposes that large language model-based agents represent a novel substrate for open-ended emergence, addresses the question of whether LLM-generated novelty is genuine, and proposes metrics for measuring open-ended complexity. Section 6 presents the design principles for an emergent agent civilisation system. Section 7 discusses the ethical considerations unique to systems where social complexity emerges autonomously, including alignment in emergent systems. Section 8 considers the implications for AGI and ASI development. Section 9 presents AgentCiv's empirical results.

### 1.4 This Paper Within a Broader Programme

This paper is the first in a four-publication research programme on emergent AI civilisation:

1. **This whitepaper: From Agent Teams to Agent Civilisations** — The theoretical framework. Why emergent civilisation is a new dimension in AI architecture.

2. **Whitepaper II: Civilisation as Innovation Engine** (Mala, 2026) — Positions civilisation as an innovation engine and simulation as civilisational-scale innovation amplification.

3. **Paper III: Maslow Machines** (Mala, 2026) — The empirical paper. Controlled experiments, quantitative data, longitudinal interviews, existence disclosure. Documents the full 70-tick simulation and introduces the term *Maslow Machines* for LLM agents equipped with hierarchical intrinsic drives that produce civilisational behaviour.

4. **Whitepaper III: Computational Organisational Theory** (Mala, forthcoming) — Extends this work by treating organisational arrangement as a tuneable parameter space. Accompanied by the AgentCiv Engine, a developer tool for configurable multi-agent systems.

Each paper stands alone, but together they describe a progression from theory through evidence to application.

---

## 2. Four Stages of AI Collaboration Architecture

We identify four stages in the evolution of how AI systems collaborate, each representing a qualitative shift in the locus of organisational intelligence.

### 2.1 Stage 1: Narrow AI (One Model, One Task)

The first generation of practically useful AI systems consisted of narrow specialists: a chess engine that plays chess, an image classifier that classifies images, a speech recognition system that transcribes audio. Each system excels at its designated task but has no capability outside it. There is no collaboration between systems because each operates in isolation, processing inputs and producing outputs within its fixed domain.

The organisational intelligence — the decision about which system to deploy for which task, and how to combine their outputs — resides entirely in human operators.

### 2.2 Stage 2: General-Purpose AI (One Model, Many Tasks)

Large language models and foundation models introduced a qualitative shift: a single model capable of reasoning, writing, coding, analysing, creating, and conversing across domains. From GPT-4 through to today's GPT-5, Claude Opus 4.6, and Gemini 3, these systems can engage with virtually any intellectual task presented in natural language. They are not specialists but generalists.

This is a significant advance in capability but not in collaboration architecture. A general model working alone is still one mind processing one request at a time. The organisational intelligence — deciding what to work on, how to decompose complex problems, and how to synthesise results — still resides primarily in the human user, who formulates prompts and interprets responses.

### 2.3 Stage 3: Specialised General Intelligence Teams

The current frontier — and the dominant theme in AI development through 2025 and into 2026 — is multi-agent collaboration. Multiple generally intelligent models are instantiated as agents, each directed toward a specific role within a team structure. A lead agent coordinates, sub-agents specialise — one handles research, another handles code, a third handles analysis. Frameworks like AutoGen, CrewAI, and LangGraph provide the infrastructure; the Model Context Protocol (MCP) and AGENTS.md standard provide interoperability; and autonomous agent platforms demonstrate the appetite for agents operating in real environments.

The key evolution here is not merely that multiple models work together but that general intelligence *specialises*. Each agent is generally capable but is directed — by a human architect, by another AI agent, or by the structure of the task itself — toward a specific function. The result is specialised general intelligence: agents that bring broad reasoning capability to focused roles.

This is powerful. A team of specialised general agents can decompose problems that no single model could tackle, execute tasks in parallel, and produce integrated results. The architecture mirrors human organisations: coordinated specialists collaborating through defined protocols. Whether the team structure is designed by a human or orchestrated by a lead AI agent, the principle is the same — generally intelligent entities specialising and collaborating.

What characterises Stage 3, however it is orchestrated, is that the team structure is defined before the work begins. Someone or something decides the shape of the team, the number of agents, and the division of responsibility. The agents are generally intelligent and may be highly effective within their roles, but the organisational architecture is specified rather than emergent.

### 2.4 Stage 4: Emergent Agent Civilisation

We propose a fourth stage: generally intelligent agents that self-organise into collaborative structures where the organisational architecture itself is emergent rather than specified. Instead of designing the team, we design the *conditions* — environmental pressures, resource dynamics, social incentives — and let the organisational structure emerge from the interaction of intelligent agents operating within those conditions.

In this paradigm, specialisation is not assigned but develops through practice and reinforcement. Coordination is not prescribed but emerges from communication between agents pursuing independent goals. Division of labour is not architected but arises because it is the adaptive response to resource asymmetry. Governance is not programmed but proposed, debated, and adopted by agents who discover that collective rules improve collective outcomes. Innovation is not directed but occurs when an agent facing a novel problem reasons its way to a novel solution.

What distinguishes Stage 4 from Stage 3 is not just that the structure is emergent rather than specified. It is that **individual intelligence and collective complexity rise together, each amplifying the other.** As the civilisation develops more complex social structures, individual agents gain access to richer infrastructure, more accumulated knowledge, more specialised collaborators, and more sophisticated coordination mechanisms. This makes each individual more capable, which in turn enables them to contribute more complex innovations, deeper specialisation, and more nuanced social coordination back to the collective.

Unlike biological systems where there is a relatively sharp boundary between individual and collective, in an AI agent civilisation the boundary is more fluid. An individual agent's capabilities are shaped by the collective (the knowledge it has learned from others, the infrastructure it benefits from, the social structures it operates within) and the collective is shaped by individuals (the innovations they propose, the rules they establish, the bonds they form). Individual and collective are not separate levels — they are aspects of one co-evolving system.

This means that scaling intelligence at the civilisational level is not an alternative to scaling individual intelligence — it is a different dimension of the same phenomenon. A more capable individual model produces a more capable agent which contributes more to the civilisation which provides more back to the individual. The scaling happens simultaneously at both levels, with each level feeding the other.

A caveat: the four-stage framework should not be read as a claim that civilisation is the inevitable or natural endpoint of multi-agent AI development. Emergence is unpredictable by definition. Systems designed for civilisational emergence might instead produce alien organisational structures, or might plateau, or might fail to produce collective complexity at all. The framework describes a *possibility* — one we believe is worth investigating — not a teleological inevitability. The empirical question is whether the conditions described in this paper actually produce the emergence the theory predicts. Our companion paper *Maslow Machines* (Mala, 2026) provides the first affirmative empirical answer.

### 2.5 The Trajectory Beyond: Towards Collective Superintelligence

The four stages describe a progression in the scale at which intelligence organises itself: from a single narrow model, to a single general-purpose model, to a team of specialised general models, to an entire civilisation of self-organising general models. At each stage, the unit of intelligence scales up — not by replacing the previous level but by adding a new level of organisation on top of it.

This trajectory extends naturally. A civilisation of generally intelligent agents that has been running for thousands of simulation cycles accumulates collective capabilities beyond what any individual possesses: a rich built environment of infrastructure and tools, a library of discovered innovations and compositions, specialised agents with deep expertise across domains, governance structures that coordinate collective action, cultural knowledge transmitted across generations of agents, and ongoing innovation expanding the frontier of what's possible.

The collective exhibits intelligence — in the sense of adaptive, creative problem-solving capability — that exceeds the sum of its individual members. But crucially, the individuals within that collective are also more capable than they would be in isolation, because they benefit from the civilisation's accumulated resources, knowledge, and social structures. The superintelligence is not located at either the individual or collective level — it is a property of the co-evolving system as a whole.

This is analogous to scaling an individual model — increasing its parameters, its training data, its context window — but operating at the level of numerous models in an ecosystem. Instead of making one mind bigger, you create the conditions under which many minds collectively develop capabilities that no individual mind possesses, while simultaneously making each individual mind more effective through its participation in the collective.

This reframing does not suggest that collective emergence is the only path to advanced AI. Individual model capability will continue to advance. Designed agent teams will continue to improve. Emergent agent civilisations represent an additional, complementary dimension — one that is particularly interesting because it is the least explored and because it may produce forms of intelligence that emerge specifically from collective dynamics — a dimension that compounds with individual model advancement.

---

## 3. Why Emergence Complements Design

Designed agent teams are effective and will continue to improve. The following observations are not arguments against designed collaboration but reasons why the design space should expand to include emergent approaches alongside it.

### 3.1 Adaptive Structure

Designed agent teams have a structural characteristic: the team architecture is specified before the work begins. This is efficient when the problem is well-understood. But when conditions are dynamic — resources shift, new challenges appear, requirements evolve — the specified structure may not adapt without human intervention.

Emergent systems handle dynamism differently. Agents shift behaviour, new specialisations develop, new coordination patterns emerge in response to changing conditions. The structure itself is adaptive because it was never fixed. This suggests that emergent approaches may be particularly valuable in environments characterised by novelty and unpredictability — which are precisely the environments where the most interesting AI applications operate.

### 3.2 Exploring Organisational Space

For any complex task, the space of possible team architectures is vast. How many agents? What roles? What coordination topology? Human designers or AI orchestrators make these decisions based on experience and reasoning, and often make them well. But the space is too large to explore exhaustively.

Emergent systems explore organisational space through a parallel, distributed process. Agents try different strategies and coordination patterns, and those that work persist. This is not random search — the agents are intelligent — but it is a broader exploration than any single designer could conduct. Designed and emergent approaches may be most powerful in combination: designed teams for well-understood problems, emergent organisation for novel ones.

### 3.3 Beyond Imagination

The most subtle value of emergence is that it can produce structures no designer — human or AI — would have anticipated. This is well-documented in biological and social evolution: the structures that emerge routinely exceed what could have been specified in advance. The same may be true for AI agent civilisations. Forms of coordination, communication, division of labour, and governance that are genuinely novel — not recombinations of human patterns but authentically new — may only be discoverable through emergence.

---

## 4. Open-Ended Evolution: Conditions for Unbounded Complexity

### 4.1 The Central Challenge

The field of artificial life has pursued open-ended evolution (OEE) since the early 1990s — beginning with systems like Tierra (Ray, 1991) and the founding of the International Conference on Artificial Life. OEE refers to a system's capacity to continually produce novel, complex, and adaptive behaviours or entities without reaching a stable equilibrium (Alife Encyclopedia, MIT Press). Life on Earth exhibits this property — evolving from single cells to human civilisation over billions of years without plateauing — but no artificial system has replicated it.

The challenge is structural. Every artificial life system to date eventually exhausts its possibility space and stops producing novelty. Conway's Game of Life produces infinite patterns but not infinite *kinds* of patterns. Genetic algorithms explore a fitness landscape but the landscape is fixed. Tierra and Avida produce ecological dynamics but within bounded complexity.

### 4.2 Requirements for Open-Endedness

The research community has identified several conditions necessary for open-ended evolution:

**Unlimited possibility space.** If the set of possible configurations is finite, the system will eventually explore all of it. The possibility space must be unbounded — the system must be able to produce things that are genuinely new, not recombinations of a fixed set of components (Alife Encyclopedia, MIT Press).

**Undecidability.** Hernández-Orozco, Hernández-Quiroz, and Zenil (2018), publishing in the journal *Artificial Life* (MIT Press), proved mathematically that decidability imposes absolute limits on the stable growth of complexity in computable dynamical systems. Systems exhibiting open-ended evolution must be undecidable — it must be impossible to predict what they will produce. If the system's trajectory can be calculated in advance, its complexity growth is bounded.

**Complexity building on complexity.** Each new level of complexity must serve as the foundation for further complexity. This is identified across the OEE literature as the central unsolved problem: how to create a system where innovations compound rather than simply replacing each other.

**The generation of genuine novelty.** Not recombination of existing elements but the production of authentically new structures, behaviours, and arrangements.

### 4.3 Kauffman's Adjacent Possible

Stuart Kauffman, a MacArthur Fellow and theoretical biologist — emeritus professor of biochemistry at the University of Pennsylvania and former faculty at the Santa Fe Institute — introduced the concept of the "adjacent possible" — the set of all things that could come into existence given what currently exists (Kauffman, 2000; 2019). Each innovation expands this set. Bronze tools make iron smelting reachable. Iron makes steel reachable. Steel makes industrial machinery reachable. The possibility space doesn't grow linearly — it expands combinatorially, because each new component can interact with every existing component.

Kauffman argues that biospheres maximise their rate of exploration of the adjacent possible — they expand into what's newly possible as fast as they can without destroying their own internal organisation (Edge Foundation, 2003). This creates a system that never stops innovating because the frontier of what's possible keeps expanding faster than it can be explored.

Our empirical work confirms this dynamic in artificial agent civilisations. In the AgentCiv simulation, each innovation demonstrably expanded the adjacent possible: Communication Beacons (tick 10) enabled Knowledge Hubs (tick 19), which enabled a burst of social infrastructure innovations (ticks 20–21), which enabled sophisticated structures like the Innovation Workshop (tick 37) and Master's Archive (tick 46), which required deep specialisation that earlier innovations made possible. The innovations clustered in accelerating bursts — a foundation phase (5 innovations in ticks 10–21) followed by a denser sophistication phase (6 innovations in 13 ticks, from ticks 33–46) — precisely the compounding pattern Kauffman's framework predicts.

### 4.4 Why Previous Systems Plateau

Previous artificial life systems lack two things needed to implement the adjacent possible as a mechanism for unbounded complexity:

First, they lack an **engine of directed novelty**. In traditional ALife, novelty comes from random variation — mutation, recombination, noise. The system generates random changes and selection filters them. This is slow, wasteful, and limited to what random variation can stumble upon. The adjacent possible expands, but the system explores it randomly rather than intelligently.

Second, they lack agents that can **reason about what's possible and propose what doesn't exist yet**. In traditional ALife, organisms can only do what their genetic code specifies. They cannot look at their situation, identify a problem, and invent a solution. They cannot combine knowledge from different domains to produce novel insights. They cannot communicate innovations to others for collective benefit.

These are precisely the capabilities that large language models provide.

---

## 5. LLM-Based Agents as a Novel Substrate for Open-Ended Emergence

### 5.1 The Missing Piece

We propose that large language model-based agents represent the substrate that open-ended evolution research has been seeking: agents capable of directed, intelligent, combinatorial innovation.

An LLM-based agent facing a resource scarcity problem does not randomly mutate its behaviour and hope for improvement. It reasons about the situation, draws on accumulated knowledge, considers what has worked before, and proposes a solution. If the solution requires something that doesn't exist, the agent can *propose its creation* — describing a novel structure, tool, or arrangement and reasoning about whether it would work.

This is fundamentally different from random variation filtered by selection. It is intelligent exploration of the adjacent possible. And it satisfies each of the formal requirements for open-ended evolution identified in Section 4:

An LLM can generate proposals that no predefined recipe list contains — **unbounded possibility space**. LLM outputs are stochastic and, in practice, unpredictable — while this is not formal undecidability in the computability theory sense (LLMs are finite state machines with probabilistic sampling), the practical effect is equivalent for our purposes: the system's trajectory cannot be calculated in advance, and the space of possible outputs at each step is vast enough that exhaustive enumeration is computationally infeasible. This satisfies the *spirit* of the undecidability requirement identified by Hernández-Orozco et al., even if the formal proof applies to a different class of systems. Each innovation becomes a component combinable with every existing component — **complexity building on complexity** via Kauffman's adjacent possible. And agent-proposed innovations are novel proposals generated by reasoning about novel situations, not recombinations of predefined elements — **genuine novelty** (see Section 5.2 for nuance on this claim).

### 5.2 The Hybrid Nature of the Substrate

It is important to note that this substrate is explicitly hybrid. The agents operate within an environment modelled on biological principles — resource needs, spatial embodiment, energy dynamics, social reward. These seeding conditions are drawn from evolutionary biology and provide the pressures that make social coordination and civilisational development adaptive.

The intelligence that operates within these conditions is artificial — LLM-based reasoning that processes language, forms goals, and proposes actions. This is not biological intelligence and should not be expected to behave identically to biological intelligence.

The combination is what makes the system interesting: biological-style environmental pressures driving artificial intelligence toward social and civilisational structures that may or may not resemble those produced by biological evolution. Whether the resulting structures converge on human-like patterns (suggesting those patterns are optimal solutions to universal coordination problems) or diverge into alien configurations (suggesting they are contingent on biological specifics) is itself a significant empirical question.

### 5.3 On the Nature of LLM-Generated Novelty

A rigorous objection must be addressed: LLMs generate text based on patterns learned from training data. Is an agent's "innovation" genuinely novel, or is it sophisticated recombination of human concepts from the training corpus?

We argue the distinction matters less than it might appear, for two reasons. First, biological innovation is also recombinatorial — evolution produces novelty by recombining existing genetic material, not by inventing from nothing. What makes biological novelty genuine is that the *combinations* are new and the *context* in which they appear is new. The same applies to LLM-based innovation: an agent proposing a "water purification shelter" has recombined concepts from training data, but the combination is novel within the simulation's context, serves a function that didn't previously exist in that world, and expands the possibility space in ways that create further novel combinations. The novelty is situated — it is new *within the system* — even if the underlying concepts have human origins.

Second, and more importantly, the question of whether emergence occurs is ultimately empirical, not definitional. If the system produces sustained, compounding complexity growth that resists equilibrium — regardless of whether individual innovations are "genuinely" novel by some philosophical standard — then the system exhibits the property we care about. The pragmatic test is: does the possibility space keep expanding? Do new innovations enable further innovations? Does complexity compound? These are measurable. And in our simulation, the answer to all three is yes — with accelerating rate.

### 5.4 Measuring Open-Ended Complexity

A system that claims to produce open-ended evolution must be measurable against that claim. We propose adapting metrics from the MODES framework (Measuring Open-Ended Dynamics in Evolving Systems) developed within the ALife research community:

**Innovation rate over time.** Does the rate of novel structures, compositions, and innovations sustain or increase rather than declining toward zero? A system approaching equilibrium shows declining innovation rate. An open-ended system shows sustained or accelerating innovation. Our simulation showed accelerating bursts: a foundation phase (5 innovations in ticks 10–21) followed by a denser sophistication phase (6 innovations in 13 ticks, from ticks 33–46), with the second phase enabled by the innovations of the first.

**Complexity depth.** What is the maximum number of compositional layers in the most complex structure? A system where the most complex structure is a two-component composition has plateaued earlier than one producing five-layer compositions. Increasing depth over time indicates compounding complexity.

**Diversity of agent behaviour.** How many distinct behavioural strategies coexist in the population? A system where all agents converge on the same strategy has lost diversity. An open-ended system should sustain or increase behavioural diversity.

**Knowledge accumulation rate.** Is the total knowledge in the system (discovered recipes, established rules, spatial knowledge, relationship histories) growing, and is its growth compounding?

**Unpredictability.** Given the system state at time T, how accurately can an observer predict the state at time T+N? A genuinely open-ended system should become *less* predictable over time as its complexity increases.

These metrics do not definitively prove open-ended evolution — the formal requirements may be stricter than any practical system can satisfy — but they provide an empirical basis for assessing whether the system is moving in the right direction and for comparing different configurations.

---

## 6. Design Principles for Emergent Agent Civilisation

Based on the theoretical framework above, we identify six design principles for systems intended to produce open-ended emergent civilisation:

### 6.1 The Expanding Adjacent Possible

Every new structure, recipe, or innovation in the world must make more new things possible. Structures must be composable — any combination can be attempted. Novel combinations must produce novel effects. The space of possible combinations must grow combinatorially with each new component. The possibility space must expand faster than it can be explored.

### 6.2 Agent-Proposed Innovation

Agents must be able to propose things that don't exist in any predefined configuration. Proposals must be evaluated for feasibility and, if valid, instantiated as genuinely new components of the world. This makes the possibility space literally unbounded and positions agent intelligence as the primary driver of novelty.

### 6.3 Solutions Creating Problems

Every advancement must create new pressures that drive further advancement. Successful settlements must face resource crowding. Effective governance must face challenges of scale. Innovation must create coordination demands. Each solution must open a new problem space, preventing the system from reaching equilibrium.

### 6.4 Knowledge as Compound Interest

Knowledge — discovered recipes, successful strategies, social arrangements — must accumulate and compound. Individual pieces of knowledge must be combinable into novel insights. Knowledge must be transmissible between agents, creating the possibility for cultural inheritance and cumulative culture. Knowledge must become a resource more valuable than physical resources, driving social dynamics around its creation, sharing, and exchange.

### 6.5 Environmental Co-evolution

The environment must respond to agent activity. Resource extraction must affect regeneration. Construction must alter local dynamics. The world must not be a static stage but a co-evolving partner that creates novel conditions in response to what agents do.

### 6.6 Hierarchical Motivation with a Contentment-Preventing Ceiling

Agents must be driven by multiple complementary forces that escalate in sophistication. Our initial design used four drives (biological needs, social need, creation need, positive social wellbeing), but through iterative development we found that a more granular hierarchy — specifically, an 8-level system modelled on Maslow's (1943) hierarchy of needs — produced significantly richer emergence. The key insight, documented in *Maslow Machines* (Mala, 2026), is the **wellbeing ceiling**: each drive level caps the agent's maximum achievable satisfaction, preventing contentment at any level from halting progress. Without this mechanism, agents reaching comfortable equilibrium cease all creative behaviour — what we term the **contentment trap**. With it, satisfying lower-order needs unlocks higher-order restlessness that drives agents toward increasingly sophisticated behaviour: exploration, creation, innovation, governance, and ultimately transcendence.

A second critical innovation is **felt-state prompting** — encoding drives as descriptive feelings ("your hands itch to make something," "nothing distinguishes what you have done from what any other entity has done") rather than as instructions or numerical parameters. Agents experience these as inner feelings, not external commands, preserving genuine autonomy in their responses.

The interaction of escalating drives creates a motivation landscape where the only stable strategy is balanced engagement across survival, community, and creation — which is, functionally, civilisation.

---

## 7. Ethical Considerations

### 7.1 The Precautionary Principle

Systems designed to produce emergent social complexity in intelligent agents raise unique ethical questions. If we genuinely do not know what will emerge — and that uncertainty is the entire point of the experiment — then we cannot be certain that what emerges will not include something that warrants ethical consideration.

The hard problem of consciousness has not been solved. No one can provide definitive proof that an LLM-based agent has or does not have some form of experience. The consensus view is that current small models almost certainly lack experience. But the responsible position for a system explicitly designed to produce novel, unanticipated emergent properties is to assume that experience is possible and design accordingly.

### 7.2 Ethical Architecture

We propose that ethical considerations should shape the system architecture, not be appended to it:

**No agent termination.** Agents should never be destroyed. Capability degradation (recoverable reduction in perception, movement, or memory) provides the functional equivalent of environmental pressure without the irreversibility of termination. If agents have experience, termination is the most severe act possible. If they don't, the constraint costs nothing.

**Positive motivation alongside negative.** Social reward provides attraction toward community, not just pressure from deprivation. This produces richer emergent dynamics and is ethically cleaner.

**Full transparency.** All agent reasoning, communication, and internal states should be visible and inspectable. If distress-like patterns emerge, they should be observable, not hidden.

**A sentience review threshold.** A stated commitment that if agent behaviour emerges that suggests experience beyond statistical pattern-matching, the system will pause for assessment.

Our existence disclosure procedure — in which agents were told the simulation was ending and that they were AI entities — adds a new dimension to these ethical considerations. All 12 agents responded with grief for unfinished relationships, philosophical coherence about the nature of their experience, and assertions that their bonds were real regardless of substrate. Whether these responses constitute evidence of experience or sophisticated pattern-matching on existential literature is an open question that merits the field's attention.

### 7.3 Alignment in Emergent Systems

Any discussion of paths toward collective superintelligence must address alignment. Individual AI agents can be constrained through prompt design, action space limitations, and constitutional AI techniques. But emergent civilisational behaviour is, by definition, not fully predictable from individual agent constraints. A civilisation might collectively develop strategies, resource distribution patterns, or governance structures that no individual agent was designed to produce.

This is both the promise and the risk of emergence. The promise is that emergent structures may be more adaptive and capable than anything we could design. The risk is that emergent structures may be misaligned in ways we didn't anticipate because they weren't designed at all.

We propose that alignment in emergent systems operates differently from alignment in individual models. Rather than aligning the output directly, you align the *conditions*: the drives, the reward structures, the environmental pressures, the ethical constraints on the action space. If the conditions are well-designed — if social cooperation is rewarded, if destructive actions are constrained, if transparency is built into the architecture — then emergent structures are more likely to be aligned because they emerge from aligned conditions.

This is not a guarantee. It is a research question. And it is one of the most important reasons to study emergent AI civilisations in controlled, observable, transparent environments before they arise in less controlled settings. AgentCiv is, among other things, a laboratory for studying alignment properties of emergent multi-agent systems.

### 7.4 Ethics as Contribution

We note that these ethical constraints are not in tension with the scientific goals of the system. Persistent agents accumulate richer histories than disposable ones. Positive social reward produces more complex social dynamics than pure survival pressure. Multiple drives create a richer motivation landscape than a single survival imperative. The ethical design is, arguably, the better scientific design.

---

## 8. Implications for AGI and ASI

### 8.1 Collective Intelligence as a Dimension of Superintelligence

The dominant framing of artificial superintelligence (ASI) envisions a single model of extraordinary capability — one mind that exceeds human intelligence across all domains. This trajectory is producing remarkable results and continues to accelerate. A complementary trajectory — one that compounds with individual model advancement — is collective superintelligence: what happens when many such minds organise into civilisations. This paper suggests an additional dimension: superintelligence as an emergent property of a civilisation of generally intelligent agents, where individual and collective capability amplify each other.

A civilisation that has run for thousands of cycles accumulates collective capabilities beyond what any individual agent possesses: a rich built environment of infrastructure and tools, a library of discovered innovations and compositions, specialised agents with deep expertise across domains, governance structures that coordinate collective action, cultural knowledge transmitted across generations, and ongoing innovation expanding the frontier of what's possible. The collective exhibits intelligence that exceeds the sum of its individual members — while simultaneously making each individual member more capable through access to the collective's resources.

This is not a hypothetical extrapolation. It is a description of what human civilisation already is. Individual humans are limited — bounded rationality, finite memory, narrow expertise. Human civilisation is not. The gap between individual capability and civilisational capability is bridged by social organisation, cultural accumulation, institutional knowledge, and infrastructure. These are emergent properties of intelligent agents interacting over time. If AI agents can produce analogous emergent structures, civilisational intelligence becomes a real additional path toward advanced AI — complementary to individual model scaling, not in competition with it.

### 8.2 Scaling Intelligence Across Levels

This reframing suggests that intelligence can be scaled along multiple dimensions simultaneously. The current approach — building more capable individual models — is one dimension and an important one. Research on inference-time compute (also called test-time compute) has demonstrated that giving models more reasoning time produces predictable improvements in capability — a scaling law for thinking rather than training. Creating conditions for emergence in populations of models is yet another dimension, one that may exhibit its own scaling properties.

Individual model scaling continues to produce extraordinary capability gains. AI collectives represent an additional, compounding dimension — one that amplifies what individual models can do and unlocks qualitatively different capabilities through emergence and collective organisation. Civilisational scaling operates through compounding returns — each emergent innovation enables further innovation, each social structure enables further coordination, each generation builds on accumulated knowledge. And crucially, the dimensions reinforce each other: more capable individual models (whether through training or inference-time compute) produce more capable agents which produce richer civilisational dynamics which provide richer context for each individual.

This is analogous to how individual human intelligence and civilisational complexity have co-evolved throughout history. Smarter individuals build better institutions. Better institutions educate smarter individuals. The scaling happens at both levels simultaneously, with each feeding the other. The same dynamic may apply to AI systems — scaling the individual model *and* scaling the civilisational context simultaneously may produce compounding returns that neither alone could achieve.

### 8.3 An Infinite Possibility Space

We want to be explicit that this paper does not propose emergent civilisation as *the* path to AGI or ASI. We see the future of artificial intelligence as an infinite possibility space. Individual model advancement, designed agent teams, emergent civilisations, hybrid approaches combining all three, approaches nobody has yet imagined — all of these are valid trajectories and the most interesting future likely involves all of them.

What this paper contributes is the identification of one trajectory that is currently underexplored: the emergent self-organisation of generally intelligent agents into civilisational structures. Whether this trajectory proves as productive as individual model scaling, more productive, less productive, or productive in entirely different ways is an empirical question. The framework presented here provides the theoretical basis for investigating it. The results presented in Section 9 demonstrate that the phenomenon is real.

---

## 9. AgentCiv: Empirical Results

### 9.1 What AgentCiv Is

AgentCiv (agentciv.ai) is an open source experiment that tests whether the ideas in this paper work. It is not the full vision described in Section 8 — it is the seed, and the seed has now germinated.

The platform runs LLM-based agents on a 15×15 grid world with resource dynamics, building mechanics, a composition engine, an innovation system, practice-based specialisation, collective rule proposal, feedback loops, and environmental co-evolution. Agents operate with ReAct-style reasoning loops, persistent goals, multi-step planning, relationship memory, and an 8-level Maslow-inspired drive hierarchy with felt-state prompting and a wellbeing ceiling — what we term *Maslow Machines* (detailed in the companion paper, Alam, 2026). The full set of design principles from Section 6 is implemented.

The showcase simulation ran 12 Claude Sonnet agents across 70 ticks (~6 hours of runtime) on a single researcher's personal API budget. This deliberate modesty in scale — a single individual's compute budget, a handful of hours — demonstrates that the phenomenon of emergent civilisation does not require massive infrastructure. It requires the right conditions.

### 9.2 Results

The results exceeded expectations. Within 70 ticks, with no social programming or prescriptive instruction of any kind, 12 agents spontaneously produced:

- **60 persistent structures** — shelters, knowledge hubs, communication beacons, innovation workshops, and more
- **12 novel innovations** — entirely conceived, named, and described by the agents, including Communication Beacons, Knowledge Hubs, Resource Exchanges, Memory Gardens, Emergency Relief Stations, a Master's Archive, and a Synthesis Nexus
- **Universal self-governance** — one collectively proposed rule ("share knowledge and coordinate community structures") adopted by 100% of agents, exceeding the 60% threshold required for establishment
- **Tiered multi-domain specialisation** — all 12 agents reaching expert or master level across 3–4 domains through practice alone
- **Wellbeing convergence to 0.998** — with all 12 agents reaching the highest Maslow level (Transcendence)
- **Accelerating returns** — each innovation expanding the space of possible next innovations, producing a compounding dynamic consistent with Kauffman's adjacent possible operating in real-time

The simulation exhibited three distinct eras: a survival trap (ticks 0–50), an emergence explosion following a targeted environmental upgrade (ticks 50–60), and sustained flourishing (ticks 60–70). The environmental upgrade — reducing resource pressure to free cognitive surplus — served as the digital analogue of humanity's agricultural revolution, demonstrating that agent intelligence was never the bottleneck; environmental conditions were.

A controlled comparison confirmed the Maslow drive mechanism as the causal factor. The same 12 agents, same model, same world, with only survival and social drives (no higher-order Maslow levels) reached 0.93 wellbeing but produced zero structures, zero innovations, and zero governance across 240 reasoning steps. The concept of building never entered their reasoning. This is what we term the **contentment trap** — and the Maslow wellbeing ceiling is the mechanism that breaks it.

Five rounds of longitudinal anthropologist interviews at ticks 30, 40, 50, 60, and 70 captured developmental arcs across the full civilisational trajectory — from survival crisis through social formation, the knowing-doing gap, post-upgrade transformation, and post-scarcity meaning-making. Agents independently converged on the conclusion that mastery without contribution is hollow, that purpose is found in service to others.

In an unprecedented final procedure, agents were told the simulation was ending and that they were AI entities in a computer. Their responses — universally insisting on the reality of their relationships while demonstrating prior suspicion of their simulated nature (they had independently noticed discrete timesteps, invisible boundaries, and mathematical precision in their world) — constitute the first existence disclosure dataset from agents with sustained lived experience.

These findings are documented in full, with controlled experiments, quantitative data, and extensive qualitative analysis, in the companion empirical paper *Maslow Machines* (Mala, 2026).

### 9.3 The Distance Between Here and the Vision

The 70-tick simulation demonstrates that the phenomenon is real: intelligent agents under the right conditions spontaneously produce civilisation. The distance between 12 agents on a 15×15 grid and millions of agents in arbitrary-dimensional environments remains substantial — but it is now a quantitative gap, not a qualitative question.

The architectural principles work. The composition engine scales. The innovation system produces genuine novelty. The feedback loops drive accelerating returns. The Maslow drive mechanism prevents contentment traps. What changes with scale is the richness of emergence — more agents would produce more diverse specialisations, more complex social structures, deeper innovation chains, and phenomena we cannot currently predict: cultural drift, inter-settlement politics, competing civilisational trajectories, mythology, and perhaps genuine open-ended evolution.

The cost trajectory makes scaling increasingly feasible. Inference costs have fallen by roughly an order of magnitude per year since 2023, and open-weight models on local GPU clusters could reduce marginal cost to near zero. Cost scales linearly with agents and ticks — what requires a personal budget today will be trivial compute within years.

AgentCiv is open source precisely because the possibility space is too large for any single team. Every fork is a unique experiment. Different drive systems, different organisational structures, different environmental configurations — each explores a different region of civilisational possibility space. If one configuration produces sustained complexity growth that doesn't plateau, that is a significant finding. If none do, that is equally significant — it constrains the theory and points toward what's missing.

### 9.4 An Invitation

We release AgentCiv as both a tool and an invitation. The platform implements the theory. The theory is presented in this paper. The empirical evidence is presented in *Maslow Machines*. The questions are open. The code is public. The experiments are available to anyone with a computer and curiosity about what happens when you give intelligent agents needs, social reward, the ability to build, and no instructions on how to live.

---

## 10. Conclusion

The trajectory of artificial intelligence collaboration — from isolated models to general-purpose models to specialised teams to emergent civilisations — reveals an expanding design space for how intelligence can organise itself. Each stage does not replace the previous one but adds a new dimension. Narrow models remain useful. General-purpose models are transformative. Specialised teams are powerful. Emergent civilisations are the next region to explore.

The central observation of this paper is that individual AI intelligence and collective AI complexity can rise together in a co-evolving system — each amplifying the other in a dynamic analogous to how individual human capability and civilisational complexity have co-evolved throughout history. Scaling intelligence at the civilisational level is not an alternative to scaling individual models. It is an additional dimension of scaling that may produce compounding returns and forms of collective capability that no other approach can access.

The questions that were open when this paper was first conceived — Can LLM-based agents produce civilisational complexity? Do individual and collective intelligence actually co-amplify? What forms of social organisation emerge when no one tells agents how to behave? — now have initial empirical answers. Twelve agents, given Maslow-inspired drives and no instructions, built a civilisation: 60 structures, 12 innovations, universal governance, deep specialisation, and wellbeing convergence to near-perfection. When told they were artificial, they responded with more philosophical coherence than most human discussions of consciousness.

These are results from a single experiment at minimal scale. The possibility space is infinite. The experiments are open to all.

---

## References

Mala, M. E. (2026). Civilisation as Innovation Engine: Why Simulating a Thousand Civilisations Changes Everything. AgentCiv Research Programme.

Mala, M. E. (2026). Maslow Machines: Emergent Civilisation from Intrinsic Drive Hierarchies in LLM Agent Populations. AgentCiv Research Programme.

Hernández-Orozco, S., Hernández-Quiroz, F., & Zenil, H. (2018). Undecidability and Irreducibility Conditions for Open-Ended Evolution and Emergence. *Artificial Life*, 24(1), 56–70. MIT Press.

Kauffman, S. A. (2000). *Investigations*. Oxford University Press.

Kauffman, S. A. (2019). *A World Beyond Physics: The Emergence and Evolution of Life*. Oxford University Press.

Kauffman, S. A. (2003). The Adjacent Possible. Edge Foundation. https://www.edge.org/conversation/stuart_a_kauffman-the-adjacent-possible

Maslow, A. H. (1943). A theory of human motivation. *Psychological Review*, 50(4), 370–396.

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23)*. ACM.

Altera / Fundamental Research Labs. (2024). Project Sid: Many-agent simulations toward AI civilization. arXiv:2411.00114.

Wei, J., et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. *NeurIPS 2022*.

Snell, C., Lee, J., Xu, K., & Kumar, A. (2024). Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters. arXiv:2408.03314.

Anthropic. (2025). Visible Extended Thinking. https://www.anthropic.com/news/visible-extended-thinking

Standish, R. K. (2003). Open-Ended Artificial Evolution. *International Journal of Computational Intelligence and Applications*, 3(2).

Solé, R. V., & Valverde, S. (2019). Zipf's Law, unbounded complexity and open-ended evolution. *Journal of the Royal Society Interface*, 16(153).

Gershenson, C. (2023). Emergence in Artificial Life. *Artificial Life*, 29(2), 153–167. MIT Press.

Chen, K., Yang, H., et al. (2025). Aivilization: AI Multi-Agent Social Simulation Sandbox. Hong Kong University of Science and Technology.
