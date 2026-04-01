/**
 * FishbowlGuide — a comprehensive visual guide overlay that teaches users
 * how to interpret everything they see in the fishbowl.
 *
 * Toggled via a "?" button in the fishbowl top bar.
 */

import { useState } from "react";

// ---------------------------------------------------------------------------
// Colours (matching the design system)
// ---------------------------------------------------------------------------

const C = {
  cream: "#FEFCF6",
  warmWhite: "#FFFAF0",
  ink: "#2D2A24",
  inkLight: "#5C5648",
  inkMuted: "#8C8578",
  border: "#E8E2D6",
  sky: "#5B9BD5",
  skyLight: "#A8CDE8",
  sage: "#6B9B7B",
  rose: "#C88B93",
  gold: "#C5962B",
  goldLight: "#E8D59A",
  goldPale: "#FDF6E3",
  earth: "#8B7355",
  earthLight: "#BBA88D",
  ember: "#D4785A",
  parchment: "#F3EDE0",
};

// ---------------------------------------------------------------------------
// Small visual legend swatches
// ---------------------------------------------------------------------------

function Dot({ color, size = 10, glow }: { color: string; size?: number; glow?: string }) {
  return (
    <span
      className="inline-block shrink-0 rounded-full"
      style={{
        width: size,
        height: size,
        backgroundColor: color,
        boxShadow: glow ? `0 0 6px 2px ${glow}` : undefined,
        verticalAlign: "middle",
      }}
    />
  );
}

function Swatch({ color }: { color: string }) {
  return (
    <span
      className="inline-block shrink-0 rounded"
      style={{
        width: 24,
        height: 14,
        backgroundColor: color,
        border: `1px solid ${C.border}`,
        verticalAlign: "middle",
      }}
    />
  );
}

function StructureIcon({ type }: { type: "shelter" | "storage" | "marker" | "path" | "innovation" }) {
  const s = 18;
  return (
    <svg width={s} height={s} viewBox="0 0 18 18" className="inline-block shrink-0" style={{ verticalAlign: "middle" }}>
      {type === "shelter" && (
        <polygon points="9,3 3,14 15,14" fill={C.earthLight} stroke={C.earth} strokeWidth="1" />
      )}
      {type === "storage" && (
        <rect x="3" y="5" width="12" height="8" rx="1" fill={C.goldLight} stroke={C.gold} strokeWidth="1" />
      )}
      {type === "marker" && (
        <>
          <circle cx="9" cy="9" r="5" fill="none" stroke={C.inkMuted} strokeWidth="1" />
          <circle cx="9" cy="9" r="1.5" fill={C.inkMuted} />
        </>
      )}
      {type === "path" && (
        <line x1="2" y1="9" x2="16" y2="9" stroke={C.earthLight} strokeWidth="3" strokeLinecap="round" />
      )}
      {type === "innovation" && (
        <>
          <circle cx="9" cy="9" r="5" fill={C.goldPale} stroke={C.gold} strokeWidth="1" />
          <circle cx="9" cy="9" r="5" fill="rgba(197,150,43,0.3)" />
        </>
      )}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Section component
// ---------------------------------------------------------------------------

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6 last:mb-0">
      <h3
        className="mb-3 text-base font-semibold"
        style={{ fontFamily: "Lora, Georgia, serif", color: C.ink }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}

function LegendRow({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-start gap-3 py-1.5">
      <span className="mt-0.5 flex w-6 justify-center">{icon}</span>
      <span className="text-sm leading-relaxed" style={{ color: C.inkLight }}>{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function FishbowlGuideButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center justify-center rounded-full text-xs font-bold transition-colors"
      style={{
        width: 22,
        height: 22,
        backgroundColor: C.parchment,
        color: C.inkMuted,
        border: `1px solid ${C.border}`,
      }}
      title="How to read the fishbowl"
    >
      ?
    </button>
  );
}

export function FishbowlGuideOverlay({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<"map" | "panels" | "controls">("map");

  return (
    <div
      className="absolute inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(45, 42, 36, 0.5)" }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl shadow-xl"
        style={{
          backgroundColor: C.cream,
          border: `1px solid ${C.border}`,
        }}
      >
        {/* Header */}
        <div
          className="sticky top-0 z-10 flex items-center justify-between border-b px-6 py-4"
          style={{ backgroundColor: C.cream, borderColor: C.border }}
        >
          <h2
            className="text-xl font-semibold"
            style={{ fontFamily: "Lora, Georgia, serif", color: C.ink }}
          >
            How to Read the Fishbowl
          </h2>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-lg transition-colors"
            style={{ color: C.inkMuted, backgroundColor: C.parchment }}
          >
            &times;
          </button>
        </div>

        {/* Tab bar */}
        <div className="flex border-b px-6" style={{ borderColor: C.border }}>
          {(["map", "panels", "controls"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="px-4 py-2.5 text-sm font-medium capitalize transition-colors"
              style={{
                color: tab === t ? C.sky : C.inkMuted,
                borderBottom: tab === t ? `2px solid ${C.sky}` : "2px solid transparent",
              }}
            >
              {t === "map" ? "The Map" : t === "panels" ? "Side Panels" : "Controls"}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          {tab === "map" && <MapGuide />}
          {tab === "panels" && <PanelsGuide />}
          {tab === "controls" && <ControlsGuide />}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab content
// ---------------------------------------------------------------------------

function MapGuide() {
  return (
    <>
      <p className="mb-5 text-sm leading-relaxed" style={{ color: C.inkLight }}>
        The map is a living landscape. Every colour, shape, and movement
        represents something real happening in the simulation.
      </p>

      <Section title="Terrain">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          The background of the map is the landscape the agents live on. Different
          terrain types affect how easily agents can move.
        </p>
        <LegendRow icon={<Swatch color="#F5F0E3" />} label="Plains — easy to cross, most common terrain" />
        <LegendRow icon={<Swatch color="#D4C8B8" />} label="Rocky ground — slower to cross, costs more energy to traverse" />
        <LegendRow icon={<Swatch color="#C8D8C4" />} label="Dense terrain — hardest to cross, thick and overgrown" />
      </Section>

      <Section title="Resources">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          Resources are blended into the terrain as subtle colour tints. Richer
          colour means more resources available in that area.
        </p>
        <LegendRow icon={<Swatch color="#A8CDE8" />} label="Water — blue tint. Agents need water to stay capable." />
        <LegendRow icon={<Swatch color="#D4C878" />} label="Food — golden tint. Agents need food to stay capable." />
        <LegendRow icon={<Swatch color="#BBA88D" />} label="Material — brown tint. Used for building structures." />
        <p className="mt-2 text-xs" style={{ color: C.inkMuted }}>
          Resources regenerate slowly but deplete when gathered. Watch for areas
          becoming bare as agents exhaust them.
        </p>
      </Section>

      <Section title="Agents">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          Each dot on the map is an AI agent — a genuinely thinking entity making
          its own decisions. Their appearance tells you about their state.
        </p>
        <LegendRow
          icon={<Dot color={C.sage} size={12} />}
          label="Healthy agent — green means all needs are being met, full capability"
        />
        <LegendRow
          icon={<Dot color={C.rose} size={8} />}
          label="Degraded agent — pink/rose and smaller. Needs aren't being met, capabilities are reduced. Always recoverable."
        />
        <LegendRow
          icon={
            <span className="relative inline-flex items-center justify-center" style={{ width: 20, height: 20 }}>
              <span
                className="absolute rounded-full"
                style={{
                  width: 20,
                  height: 20,
                  background: "rgba(197, 150, 43, 0.25)",
                  boxShadow: "0 0 8px 3px rgba(197, 150, 43, 0.35)",
                }}
              />
              <Dot color={C.sage} size={12} />
            </span>
          }
          label="High social wellbeing — warm golden halo that gently pulses. This agent is thriving from social interaction."
        />
        <LegendRow
          icon={
            <span className="relative inline-flex items-center justify-center" style={{ width: 20, height: 20 }}>
              <span
                className="absolute rounded-full"
                style={{
                  width: 18,
                  height: 18,
                  background: "rgba(147, 112, 219, 0.2)",
                  boxShadow: "0 0 6px 2px rgba(147, 112, 219, 0.3)",
                }}
              />
              <Dot color={C.sage} size={10} />
            </span>
          }
          label="High curiosity — violet glow. This agent is driven to explore or create."
        />
        <div className="mt-3 rounded-lg p-3" style={{ backgroundColor: C.goldPale }}>
          <p className="text-xs leading-relaxed" style={{ color: C.inkLight }}>
            <strong>Specialisation rings:</strong> A coloured ring around an agent means they've
            developed expertise through repeated practice. <span style={{ color: C.sage }}>Green ring</span> = gathering specialist.{" "}
            <span style={{ color: C.earth }}>Brown ring</span> = building specialist.{" "}
            <span style={{ color: C.sky }}>Blue ring</span> = social/communication specialist.
          </p>
        </div>
        <div className="mt-3 rounded-lg p-3" style={{ backgroundColor: C.warmWhite }}>
          <p className="text-xs leading-relaxed" style={{ color: C.inkLight }}>
            <strong>Thought bubbles:</strong> When agents think or speak, a small bubble appears
            above them. Italic text is internal reasoning. Blue text is a message to another agent.
          </p>
        </div>
      </Section>

      <Section title="Structures">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          Agents can build structures that persist in the world. Each shape represents
          a different type. Structures slowly decay if not maintained.
        </p>
        <LegendRow icon={<StructureIcon type="shelter" />} label="Shelter — reduces capability degradation for agents nearby. Triangle shape." />
        <LegendRow icon={<StructureIcon type="storage" />} label="Storage — stores extra resources for later use. Rectangle shape." />
        <LegendRow icon={<StructureIcon type="marker" />} label="Marker — a persistent message left for other agents to read. Circle with dot." />
        <LegendRow icon={<StructureIcon type="path" />} label="Path — connects tiles and reduces movement cost. Earthy lines between tiles." />
        <LegendRow icon={<StructureIcon type="innovation" />} label="Innovation — something entirely new that an agent invented. Gold shimmer glow." />
        <p className="mt-2 text-xs" style={{ color: C.inkMuted }}>
          Tiles with structures have a warm golden tint. Areas with many structures are the
          beginnings of settlements.
        </p>
      </Section>

      <Section title="Communication">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          When agents talk to each other, a blue line briefly appears between them.
          The line fades after a couple of seconds. Watch for clusters of
          conversation — that's where social dynamics are forming.
        </p>
        <div className="flex items-center gap-3 py-1.5">
          <svg width="40" height="12" className="shrink-0">
            <line x1="2" y1="6" x2="38" y2="6" stroke={C.skyLight} strokeWidth="2" />
          </svg>
          <span className="text-sm" style={{ color: C.inkLight }}>Solid line = direct conversation between two agents</span>
        </div>
        <div className="flex items-center gap-3 py-1.5">
          <svg width="40" height="12" className="shrink-0">
            <line x1="2" y1="6" x2="38" y2="6" stroke={C.skyLight} strokeWidth="2" strokeDasharray="4 4" />
          </svg>
          <span className="text-sm" style={{ color: C.inkLight }}>Dashed line = broadcast message (speaking to anyone nearby)</span>
        </div>
      </Section>
    </>
  );
}

function PanelsGuide() {
  return (
    <>
      <p className="mb-5 text-sm leading-relaxed" style={{ color: C.inkLight }}>
        The side panels show you what's happening beneath the surface — the
        thinking, the conversations, and the history of the civilisation.
      </p>

      <Section title="Event Feed (top right)">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          A stream of events from the simulation. Everything an agent does
          shows up here. You can filter by category:
        </p>
        <LegendRow icon={<Dot color={C.sky} />} label="Reasoning — what agents are thinking, their goals, their plans" />
        <LegendRow icon={<Dot color={C.sage} />} label="Conversations — agents talking to each other in natural language" />
        <LegendRow icon={<Dot color={C.gold} />} label="Building — structures built, compositions discovered, innovations" />
        <LegendRow icon={<Dot color={C.inkMuted} />} label="Chronicler — observations from the meta-AI that documents the civilisation from outside (not an agent)" />
        <p className="mt-2 text-xs" style={{ color: C.inkMuted }}>
          The feed shows the most recent 200 events. Click a filter toggle
          to show or hide that category.
        </p>
      </Section>

      <Section title="Agent Inspector (bottom right)">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          Click any agent on the map to select it. The inspector panel shows
          everything about that individual:
        </p>
        <ul className="space-y-2 text-sm" style={{ color: C.inkLight }}>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Needs</strong> — coloured bars showing water, food, material, social wellbeing, curiosity, and overall capability. When physical needs drop, the agent degrades.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Goals</strong> — what the agent is currently trying to achieve (self-set, not programmed).</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Plan</strong> — the multi-step strategy the agent has devised to reach its goal.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Inventory</strong> — what resources the agent is currently carrying.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Specialisations</strong> — skills developed through repeated practice.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Memory tab</strong> — the agent's actual memories of past events and interactions.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Bonds tab</strong> — relationships with other agents, showing sentiment and bond strength.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Messages tab</strong> — log of who this agent has talked to and what they said.</span>
          </li>
        </ul>
      </Section>

      <Section title="Chronicle (tab next to Inspector)">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          The chronicle is the history of the civilisation, maintained by The
          Chronicler — a separate AI that observes the simulation from outside.
          It is not an agent and cannot influence the world. It only documents:
        </p>
        <ul className="space-y-2 text-sm" style={{ color: C.inkLight }}>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Milestones</strong> — one-time firsts: first contact between agents, first structure built, first innovation, first collective rule. These mark the civilisation's progress.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Narratives</strong> — periodic written observations by The Chronicler summarising what has emerged so far.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.rose }}>&#9679;</span>
            <span><strong>Ethical flags</strong> — alerts when an agent has been in a degraded state for too long, or is being socially excluded. Part of the project's ethical monitoring.</span>
          </li>
        </ul>
      </Section>
    </>
  );
}

function ControlsGuide() {
  return (
    <>
      <p className="mb-5 text-sm leading-relaxed" style={{ color: C.inkLight }}>
        You can navigate the map and interact with the world.
      </p>

      <Section title="Navigation">
        <div className="space-y-3 text-sm" style={{ color: C.inkLight }}>
          <div className="flex gap-3 items-start">
            <kbd className="shrink-0 rounded border px-2 py-0.5 text-xs font-mono" style={{ borderColor: C.border, backgroundColor: C.warmWhite }}>Scroll</kbd>
            <span>Zoom in and out. Scroll up to zoom in, down to zoom out.</span>
          </div>
          <div className="flex gap-3 items-start">
            <kbd className="shrink-0 rounded border px-2 py-0.5 text-xs font-mono" style={{ borderColor: C.border, backgroundColor: C.warmWhite }}>Drag</kbd>
            <span>Click and hold anywhere on the map, then move your mouse to pan around the world.</span>
          </div>
          <div className="flex gap-3 items-start">
            <kbd className="shrink-0 rounded border px-2 py-0.5 text-xs font-mono" style={{ borderColor: C.border, backgroundColor: C.warmWhite }}>Double-click</kbd>
            <span>Quick zoom in to wherever you double-click.</span>
          </div>
        </div>
      </Section>

      <Section title="Selecting agents">
        <div className="space-y-3 text-sm" style={{ color: C.inkLight }}>
          <div className="flex gap-3 items-start">
            <kbd className="shrink-0 rounded border px-2 py-0.5 text-xs font-mono" style={{ borderColor: C.border, backgroundColor: C.warmWhite }}>Click</kbd>
            <span>Click on any agent (coloured dot) to select it. A blue ring appears around the selected agent, and the Inspector panel on the right shows their full details.</span>
          </div>
          <div className="flex gap-3 items-start">
            <kbd className="shrink-0 rounded border px-2 py-0.5 text-xs font-mono" style={{ borderColor: C.border, backgroundColor: C.warmWhite }}>Hover</kbd>
            <span>Hover over any agent to see a quick tooltip showing their ID, social wellbeing, and current goal.</span>
          </div>
        </div>
      </Section>

      <Section title="What to watch for">
        <p className="mb-3 text-sm" style={{ color: C.inkLight }}>
          The fishbowl rewards patience. Here are things worth paying attention to:
        </p>
        <ul className="space-y-2 text-sm" style={{ color: C.inkLight }}>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Clustering</strong> — do agents gather near resources? Do groups form?</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Conversations</strong> — watch the blue lines. Are agents talking more? Who talks to whom?</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Building</strong> — when the first structure appears, that's a milestone. Where do they build? Near resources or near each other?</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Resource depletion</strong> — areas lose colour as agents gather. Do they move on or deplete everything?</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Specialisation rings</strong> — when coloured rings start appearing, agents are developing expertise.</span>
          </li>
          <li className="flex gap-2">
            <span style={{ color: C.gold }}>&#9679;</span>
            <span><strong>Gold shimmer</strong> — that's an innovation. Something no one programmed. Read the feed to see what it is.</span>
          </li>
        </ul>
      </Section>
    </>
  );
}
