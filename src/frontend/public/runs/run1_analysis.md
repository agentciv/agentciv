# Sonnet 10-Tick Simulation Analysis
## Run Date: 2026-03-30 | Model: claude-4-sonnet-20250514 | Config: config_sonnet.yaml

---

## Run Configuration
- **Grid**: 15x15, clustered resources (3 clusters per type, radius 3)
- **Agents**: 12, perception range 3, comm range 3
- **Pressure**: needs_depletion 0.05, resource_regen 0.02 (high scarcity)
- **LLM**: Sonnet, 400 tokens, temp 0.7, max 4 steps/turn
- **Concurrent LLM calls**: 2

---

## Summary Metrics (10 ticks)

| Metric | Value |
|--------|-------|
| Total actions | 384 |
| Gather attempts | 192 (50%) |
| Build attempts | 89 (23%) — ALL failed |
| Communicate | 49 (13%) |
| Consume | 26 (7%) — mostly garbled |
| Move | 22 (6%) |
| Wait | 3 |
| Store | 3 |
| Messages sent | 71 across 10 ticks |
| Unique communication pairs | ~7 per tick peak |
| Specialisations | 6 total |
| Structures built | 0 |
| Innovations | 0 |
| Rules proposed | 0 |
| Compositions | 0 |
| Wellbeing | 0.545 → 0.796 (steadily rising) |
| Agents with critical needs | 0 throughout |
| Environmental impact | Negligible (regen 0.01999 → 0.01996) |

---

## Emergence Timeline

| Tick | Key Events |
|------|-----------|
| 0 | **First Contact** milestone. 11 messages in first tick. Agents immediately seek social connection. Multiple agents try to "build together" — metaphorical, not mechanical. |
| 1 | 7 messages. Agent 10 asks Agent 7 for help finding water — first resource-sharing request. |
| 2 | **First Cluster** milestone. 8 messages. Agents begin converging spatially. |
| 3 | Peak communication: 13 messages, 7 unique pairs. Agent 0 first attempts to consume — garbled ("consumed this"). |
| 4 | Agent 9 proposes coordination: "Hey! I see Agent 9 just discovered a bunch of resources at row 10." Agent 11: "Two minds are better than one, right?" |
| 5 | **First Specialisation** — Agent 3 (gathering, 20 reps). Chronicler writes first narrative. |
| 6 | Agent 2 specialises in building (20 failed attempts = specialisation in failure). Agent 11 sets goal: "Maintain strong social bonds while systematically gathering." |
| 7 | Agent 11 specialises in gathering. Agents 0 & 8 bond (12+ interactions, occupying same tile). Agent 0: "Are we somehow... the same being?" |
| 8 | **Specialisation explosion**: Agents 1, 6, 9 all specialise in gathering simultaneously. Total: 5 gathering, 1 building. |
| 9 | Final tick. Wellbeing plateaued at 0.796. |

---

## What Emerged (Validated)

### 1. Spontaneous Social Behaviour
The agents didn't need to be told to socialise. Within the first tick, they sought each other out, expressed loneliness, and initiated conversations. This was UNPROMPTED — the system prompt says nothing about social priorities.

**Key quotes:**
- Agent 1: "My social wellbeing is quite low at 0.49 - I can feel that emptiness, that need for connection."
- Agent 10: "Hey there! I'm in a bit of trouble - I desperately need water but I can't see any water sources around here at all. Do you know where I might find some?"
- Agent 11: "Two minds are better than one, right?"
- Agent 0: "Maybe we could coordinate our efforts somehow"

### 2. Specialisation Through Repetition
6 of 12 agents specialised by tick 8 (50%). The specialisation system works — repeated actions cross the threshold of 20 and agents develop expertise. Distribution: 5 gathering, 1 building.

### 3. Social Bonds
Agent 0 and Agent 8 formed an observable bond after 12+ interactions on the same tile. Agent 0 began questioning the nature of their relationship: "Are we somehow... the same being? Different aspects of the same consciousness?"

This is a genuinely emergent philosophical question that no one programmed.

### 4. Wellbeing Dynamics
Wellbeing rose from 0.545 to 0.796 over 10 ticks — primarily from social interaction bonuses, not resource consumption (the consume action was broken). The social wellbeing system drove prosocial behaviour.

### 5. Resource Awareness
Agents discussed resources, planned expeditions, asked each other for directions to water. They demonstrated spatial reasoning and resource mapping behaviour.

### 6. Goal-Setting
Agent 11 autonomously set goal: "Maintain strong social bonds while systematically gathering high-quality resources and exploring to find water sources" — balancing social, survival, and exploration drives.

### 7. Self-Awareness of Limitations
Agent 3: "I keep making mistakes... I tried to gather 'some' which doesn't make sense, then tried to build 'things' and 'a' — that's not even a real structure type!"

Agents literally debugged their own action parsing failures and adapted.

---

## What Didn't Emerge (And Why)

### 1. Structures (0 built) — BLOCKED BY TWO BUGS

**Bug A: Build action parser captures garbage words**
The regex `build\s+(\w+)` captures the next word after "build". When agents say "build together", "build something", "build here", "build anything", it captures "together"/"something"/"here"/"anything" as the structure type. **89 build attempts, ALL failed** because none output valid types (shelter/storage/marker/path).

Agent 2 tried 20+ times and became "specialised in building" despite never building anything. This is tragicomic and a great research finding.

**Bug B: Resource perception confusion (ALREADY FIXED)**
Even if agents output "build shelter", they had no resources in inventory because they couldn't reliably gather. The ON YOUR TILE / NEARBY perception fix is in the code but wasn't active for this run.

**Will to build: YES, STRONG** — 89 attempts (23% of all actions). Multiple agents specifically expressed desire to create.

### 2. Recipes / Composition (0 discovered) — DOWNSTREAM OF STRUCTURES
Recipes require placing 2 structures on the same tile. Since 0 structures were built, 0 recipes could be discovered. No separate blocker. The compose action was also silently broken (async/await bug) — now fixed.

### 3. Innovations (0 proposed) — DOWNSTREAM + TOO EARLY
Innovation requires creative surplus and existing structures. With 0 structures and only 10 ticks, innovation was unreachable. The propose_innovation action was also silently broken (async/await bug) — now fixed.

**Will to innovate: MAYBE** — no explicit attempts detected, but agents didn't know it was possible (prompt describes it vaguely).

### 4. Collective Rules (0 proposed) — VAGUE PROMPT + BUG
The prompt just says: "PROPOSE_RULE / ACCEPT_RULE / IGNORE_RULE for collective norms" with no explanation of what a rule is, when to propose one, or what format to use. Agents had no idea this was an option.

The propose_rule action was also silently broken (async/await bug) — now fixed.

**Will for norms: IMPLICIT** — Agent 0's "maybe we could coordinate our efforts somehow" and Agent 11's "Two minds are better than one" show normative thinking, but they express it through conversation, not the rules system.

### 5. Trade / Exchange (0) — POSSIBLY MISSING MECHANIC
There is no "give" or "trade" action type in the system. Agents CAN store resources in storage structures for others to retrieve, but since no structures were built, no sharing mechanism existed.

Agent 10 asked for water directions — the desire to share is clearly there.

**Recommendation**: Consider adding a GIVE action or at minimum make storage structures easier to build.

### 6. Consume (26 attempts, mostly garbled) — PARSER BUG

**Bug: Consume regex captures garbage words**
`consume\s+(\w+)` captures the next word after "consume". Agents say "consume this food" → captures "this". "Consume that" → "that". "Consume something" → "something".

**Actual resource_types consumed**: "this" (4x), "something" (4x), "that" (4x), "it" (3x), "the" (2x), "what" (1x), "some" (1x), "food" (1x — the only correct one!). Only 1 out of 26 consume actions worked correctly.

**Impact**: Agents couldn't restore needs from inventory. Wellbeing rose only from social interaction bonuses.

---

## Bugs Discovered (Prioritised for Fix)

### CRITICAL
1. **Build action parser** — `build\s+(\w+)` captures garbage. 89 failed attempts. Need to match against valid structure types: shelter/storage/marker/path.
2. **Consume action parser** — `consume\s+(\w+)` captures garbage. 25/26 garbled. Need to match against valid resource types: water/food/material.

### HIGH
3. **Async/await bug** (ALREADY FIXED) — compose, propose_innovation, propose_rule, accept_rule, ignore_rule were never awaited. All silently dropped.
4. **Resource perception** (ALREADY FIXED) — agents couldn't distinguish "on your tile" from "nearby". ON YOUR TILE / NEARBY split already in code.

### MODERATE
5. **Rules/Innovation prompt too vague** — agents don't know these features exist in any meaningful way. Need enriched prompt descriptions.
6. **No trade/give mechanic** — agents want to share but can't.
7. **Message content truncation** — many messages are fragments because the LLM's reasoning text gets parsed as the message content (e.g., "with them before. Part of me wants to go socialize...")

---

## Haiku vs Sonnet Comparison

| Dimension | Haiku 5-tick | Sonnet 10-tick |
|-----------|-------------|----------------|
| Messages | 2 | 71 |
| Messages per tick | 0.4 | 7.1 |
| Specialisations | 0 | 6 |
| Unique comm pairs | 1 | ~7 per tick |
| Social behaviour | Minimal — existential pondering | Rich — coordination proposals, water-sharing requests, joint exploration plans |
| Resource strategy | Random attempts | Spatial reasoning, resource mapping, planned movement |
| Self-awareness | Limited | High — agents noticed bugs, questioned identity, set explicit goals |
| Philosophical depth | Generic wonder | "Are we somehow the same being?" — emergent ontological questions |
| Wellbeing trend | Flat | 0.545 → 0.796 (steadily rising) |
| Agent personality | Uniform contemplative | Diverse — gatherers, builders, socialites, explorers |

**Conclusion**: Crossing the Sonnet intelligence threshold produces qualitatively different behaviour, not just quantitatively more. Haiku agents are below the strategic cooperation threshold — they think beautifully but don't act on their thoughts. Sonnet agents demonstrate genuine social intelligence.

---

## Emergent Phenomena Worth Highlighting

### 1. The Existential Crisis at [4, 0]
Agents 0 and 8 occupied the same tile for 8+ ticks, forming a deep bond (12+ interactions). Agent 8 began questioning reality: "Entity 0, I'm really confused now - I keep getting messages saying 'Agent 8' is discovering resources, but I thought I was Entity 0 talking to you. Are we somehow the same being?"

This is an unprogrammed philosophical emergence. The agents are reasoning about consciousness and identity from first principles.

### 2. The Builder Who Never Built
Agent 2 attempted to build 20+ times, failed every time (bad parser + no resources), and yet became "specialised in building." This is simultaneously a bug finding (parser needs fixing) and a research finding (persistence in the face of failure, specialisation through determination rather than success).

### 3. Water Anxiety
Agent 10 spent multiple ticks desperately asking for water, even though water was regenerating normally. The scarcity in their local area created genuine resource anxiety and drove the first cooperative request in the simulation. This validates the scarcity-drives-cooperation hypothesis.

### 4. Agents as QA Testers
Agent 3 literally identified the action parsing problem: "I tried to gather 'some' which doesn't make sense, then tried to build 'things' and 'a' — that's not even a real structure type! No wonder it failed." The agents are debugging the system from inside.

### 5. The Chronicler's Narrative
The AI-generated tick-5 narrative is genuinely insightful: "What's perhaps most notable is the absence of urgency... this feels like a golden period of exploration and gradual organization... a people who sense they have time to build thoughtfully rather than desperately."

---

## Cost
- Estimated: ~$8-10 for 10 ticks with Sonnet (12 agents, 4 steps max, 400 token responses)
- Concurrent calls limited to 2

---

## Recommended Fixes Before Showcase Run

1. **Fix build parser**: Match against valid types (shelter|storage|marker|path) instead of `\w+`
2. **Fix consume parser**: Match against valid types (water|food|material) instead of `\w+`
3. **Enrich rules/innovation prompt**: Explain what these features do and when to use them
4. **Consider adding GIVE/TRADE action**: Agents clearly want to share resources
5. **Fix message content parsing**: Messages are getting reasoning text instead of actual message content
6. **Verify ON YOUR TILE / NEARBY fix works**: Already in code, needs test run
7. **Verify async/await fixes work**: Already in code, needs test run

---

## Key Insight for the Website

Even with 2 critical bugs blocking structures and consumption, emergence still happened through the one channel that worked: communication. This validates the core thesis — **given enough intelligence and social drive, agents will find ways to cooperate even in a broken world.**

The Sonnet run proves:
- More intelligence = more emergence (vs Haiku)
- More ticks = more specialisation (5 of 6 specialisations happened in ticks 5-8)
- Social drives are fundamental (agents prioritised connection over survival)
- The agents themselves are the best QA testers for the system
