# World Grid Map — Visual Design Principles

The world grid map is the first thing a visitor sees. It must work as a standalone visual — beautiful enough to screenshot, clear enough to understand in seconds, rich enough to reward sustained attention.

## 1. Immediately Comprehensible

A first-time visitor should understand what they're looking at within 3 seconds: a living world with agents moving through a landscape of resources. No legend required for the basics. Colour, shape, and motion should carry the core meaning before any text is read.

## 2. Aesthetically Beautiful

This is not a debug visualisation. The map should feel like a piece of data art — closer to a NYT interactive or a Fernanda Viégas piece than a game engine debug view. Colour palettes should be intentional, not default. Terrain should feel organic, not gridded. The overall impression should be: "I want to explore this."

## 3. Readable Social Fabric

The map must make social behaviour visible at a glance. Clusters of agents should be visually obvious. Communication lines or proximity halos should reveal who is interacting. Movement patterns (migration, gathering, social seeking) should emerge from the visual without needing to click anything.

## 4. Agent Personality Through Visuals

Even though agents have no assigned personality, their emergent state should be visually encoded. An agent who is degraded should look different from a thriving one. An agent who has been social should look different from an isolated one. Wellbeing, degradation, and social history should all be readable from the agent's visual representation.

## 5. Natural Resource Zones

Resource clusters should feel like natural features of the landscape — oases, forests, quarries — not coloured grid cells. The transition between resource-rich and resource-poor areas should be smooth. Resource depletion and regeneration should be visually animated so the world feels alive even when no agents are moving.

## 6. Clean and Minimal

No chrome. No unnecessary UI elements on the map itself. The map is the experience. Controls, filters, and information panels live at the edges. The centre of the screen is pure world. Think: Apple Maps satellite view, not Google Maps with every label on.

## 7. Shareability

The map at any given moment should produce a beautiful screenshot. This is the image that goes on the GitHub README, on Twitter, in articles. Design for the screenshot. If the default view doesn't look good as a static image, the design isn't done.

## 8. Animation and Visual Life

The fishbowl must feel alive, not like a data grid that updates. This requires smooth interpolated animation between simulation states:

- **Agent movement**: Agents glide smoothly between tiles over the interval between ticks. Never snap or jump. Movement should feel organic — like watching people walk through a village from above.
- **Interactions**: Communication lines between agents fade in, pulse softly during active exchange, fade out. Not binary on/off.
- **Structure building**: New structures materialise with a subtle build animation. Not instant pop-in.
- **Agent state changes**: Wellbeing glow breathes slowly. Degradation dimming transitions gradually. Nothing changes instantly.
- **New arrivals**: Gentle fade-in over a second or two.
- **Environmental changes**: Resource regeneration and depletion shift tile colours gradually, not in steps.

The overall visual rhythm should feel like watching a nature documentary aerial shot of a village ��� continuous, smooth, organic movement. The simulation updates in discrete ticks but the frontend must present continuous motion. This is non-negotiable for the visitor experience. A beautiful, smoothly animated fishbowl is what makes people stay and what makes screenshots compelling.

## 9. Visual Representation of Civilisational Complexity

A visitor must be able to look at the map and instantly see where civilisation is thriving versus where it's undeveloped. Complexity must be visually legible at a glance:

- **Size scales with complexity**: Starter structures are small, simple icons. Composed structures are larger. Multi-tier compositions are larger still. Clusters of advanced structures visually fill their area. The difference between a lone shelter and a developed settlement should be as obvious as the difference between a farmhouse and a city block from satellite view.
- **Visual tier progression**: Structures get more visually prominent as they increase in complexity. Starter structures are muted and simple. Compositions are more defined. Higher-tier structures have more visual presence. Agent-proposed innovations have a distinct visual signature — a shimmer, unique colour, or glow — signalling something genuinely novel that was invented, not predefined.
- **Colour evolution of developed areas**: Raw terrain is natural colours. As tiles accumulate structures, the colour palette subtly warms and shifts. Heavily developed areas have a distinct civilisational warmth that undeveloped terrain lacks. Development zones versus wilderness should be distinguishable from colour alone.
- **Infrastructure networks rendered as connections**: Paths between tiles render as visible lines or trails connecting locations, not just individual tile markers. A network of paths looks like a road system. This is one of the most visually powerful indicators of civilisation — road networks emerging on a previously empty map.
- **Activity density communicates life**: Developed areas show more agents, more interaction lines, more movement trails, more visual events. A thriving settlement pulses with activity. A remote area is visually quiet. The busyness of an area tells you its civilisational intensity.
- **Timeline scrubbing tells the visual story**: Dragging from tick 1 to present should show the map transforming — empty terrain to scattered dots to first structures to paths to settlements to complex developed zones. This visual progression IS the civilisation's story and should be beautiful and compelling to watch as a time-lapse.
- **Zoom levels**: Macro view shows the civilisational pattern — developed areas, networks, activity density. Zooming in reveals detail — specific structures, their tier, who built them, what they do. Both levels must be visually clear and beautiful.

The test: if you screenshot the fishbowl at tick 1 and again at tick 10,000, the two images should look dramatically different. The second should show visible civilisation — networks, developed zones, activity centres, complex structures — that the first doesn't have. That visual transformation over time is the single most compelling proof that the experiment works.

---

**This visual quality is not polish to add later. It is a core requirement for Phase 3.**
