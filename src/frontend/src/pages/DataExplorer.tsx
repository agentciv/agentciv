import { useEffect, useState, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BusEvent {
  type: string;
  tick: number;
  timestamp: number;
  agent_id: number | null;
  data: Record<string, unknown>;
}

interface ChunkMeta {
  name: string;
  start_tick: number;
  end_tick: number;
  file: string;
}

// ---------------------------------------------------------------------------
// Event type categories & display config
// ---------------------------------------------------------------------------

const EVENT_CATEGORIES: Record<string, { label: string; color: string; types: string[] }> = {
  thinking: {
    label: "Thinking",
    color: "#7B68AE",
    types: ["reasoning_step", "observation", "goal_set", "plan_updated"],
  },
  actions: {
    label: "Actions",
    color: "#5B9BD5",
    types: ["action_taken", "agentic_turn_start", "agentic_turn_end"],
  },
  social: {
    label: "Social",
    color: "#C5962B",
    types: ["message_sent", "rule_proposed", "rule_accepted", "rule_established"],
  },
  building: {
    label: "Building",
    color: "#6B9B7B",
    types: ["structure_built", "innovation_succeeded", "innovation_failed"],
  },
  survival: {
    label: "Survival",
    color: "#D4785A",
    types: [
      "resource_consumed",
      "resource_given",
      "resource_stored",
      "maintenance_consumed",
      "wellbeing_changed",
      "degradation_changed",
      "needs_critical",
    ],
  },
  knowledge: {
    label: "Knowledge",
    color: "#5CAD8B",
    types: ["specialisation_gained", "marker_read"],
  },
  system: {
    label: "System",
    color: "#8C8578",
    types: ["tick_start", "tick_end", "watcher_tick_report", "watcher_milestone", "watcher_narrative"],
  },
};

const TYPE_TO_CATEGORY: Record<string, string> = {};
for (const [cat, { types }] of Object.entries(EVENT_CATEGORIES)) {
  for (const t of types) TYPE_TO_CATEGORY[t] = cat;
}

function eventColor(type: string): string {
  const cat = TYPE_TO_CATEGORY[type];
  return cat ? EVENT_CATEGORIES[cat].color : "#8C8578";
}

function eventLabel(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ---------------------------------------------------------------------------
// Agent colors
// ---------------------------------------------------------------------------

const AGENT_COLORS = [
  "#5B9BD5", "#C5962B", "#6B9B7B", "#D4785A", "#C88B93", "#8B7355",
  "#7B68AE", "#5CAD8B", "#D4A05A", "#6A8CAD", "#B57E6E", "#7BAD7B",
];

// ---------------------------------------------------------------------------
// Format event data for display
// ---------------------------------------------------------------------------

function formatEventData(ev: BusEvent): string {
  const d = ev.data;
  switch (ev.type) {
    case "reasoning_step":
      return String(d.response ?? d.reasoning ?? "").slice(0, 500);
    case "action_taken":
      return `${d.action}${d.reasoning ? ` — ${String(d.reasoning).slice(0, 200)}` : ""}`;
    case "message_sent":
      return `Agent ${d.sender_id} → Agent ${d.receiver_id}: "${String(d.content ?? "").slice(0, 300)}"`;
    case "structure_built": {
      const pos = d.position as { x: number; y: number } | undefined;
      return `Built ${d.structure_type}${pos ? ` at (${pos.x},${pos.y})` : ""}`;
    }
    case "innovation_succeeded":
      return `Discovered "${d.name}" — ${String(d.description ?? "").slice(0, 200)}`;
    case "innovation_failed":
      return `Failed to innovate: ${String(d.reason ?? d.name ?? "")}`;
    case "rule_proposed":
      return `Proposed: "${String(d.text ?? "").slice(0, 300)}"`;
    case "rule_accepted":
    case "rule_established":
      return `Rule ${d.rule_id}${d.text ? `: "${String(d.text).slice(0, 200)}"` : ""} (${(Number(d.adoption_rate ?? 0) * 100).toFixed(0)}% adoption)`;
    case "goal_set":
      return String(d.goal ?? "");
    case "observation":
      return String(d.observation ?? d.summary ?? JSON.stringify(d)).slice(0, 300);
    case "plan_updated":
      return Array.isArray(d.plan) ? d.plan.join(" → ") : String(d.plan ?? "");
    case "specialisation_gained":
      return `Specialised in ${d.activity} (count: ${d.count})`;
    case "needs_critical":
      return `${d.need} critically low: ${d.level}`;
    case "wellbeing_changed":
      return `${Number(d.old ?? 0).toFixed(3)} → ${Number(d.new ?? d.value ?? 0).toFixed(3)}`;
    case "watcher_milestone":
      return `${d.name}: ${String(d.commentary ?? "").slice(0, 300)}`;
    case "watcher_narrative":
      return String(d.text ?? "").slice(0, 500);
    case "watcher_tick_report": {
      const pop = d.population as Record<string, unknown> | undefined;
      const comm = d.communication as Record<string, unknown> | undefined;
      const structs = d.structures as Record<string, unknown> | undefined;
      const parts = [];
      if (pop) parts.push(`pop: ${pop.total}, wb: ${Number(pop.avg_wellbeing ?? 0).toFixed(2)}`);
      if (comm) parts.push(`msgs: ${comm.messages_sent}`);
      if (structs) parts.push(`structures: ${structs.total}`);
      return parts.join(" · ") || JSON.stringify(d).slice(0, 200);
    }
    default:
      return JSON.stringify(d).slice(0, 300);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export default function DataExplorer() {
  const [chunks, setChunks] = useState<ChunkMeta[]>([]);
  const [events, setEvents] = useState<BusEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Filters
  const [tickRange, setTickRange] = useState<[number, number]>([60, 70]);
  const [activeCategories, setActiveCategories] = useState<Set<string>>(
    new Set(Object.keys(EVENT_CATEGORIES))
  );
  const [agentFilter, setAgentFilter] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedEvents, setExpandedEvents] = useState<Set<number>>(new Set());

  // Load chunk index
  useEffect(() => {
    fetch("/replay_data/metadata.json")
      .then((r) => r.json())
      .then((m) => setChunks(m.event_chunks));
  }, []);

  // Load events for tick range
  const loadEvents = useCallback(async () => {
    if (chunks.length === 0) return;
    setLoading(true);
    try {
      const relevant = chunks.filter(
        (c) => c.start_tick <= tickRange[1] && c.end_tick >= tickRange[0]
      );
      const allEvents: BusEvent[] = [];
      for (const chunk of relevant) {
        const res = await fetch(`/replay_data/${chunk.file}`);
        const data: BusEvent[] = await res.json();
        allEvents.push(...data);
      }
      setEvents(allEvents);
      setLoaded(true);
    } finally {
      setLoading(false);
    }
  }, [chunks, tickRange]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // Get active event types from categories
  const activeTypes = useMemo(() => {
    const types = new Set<string>();
    for (const cat of activeCategories) {
      const cfg = EVENT_CATEGORIES[cat];
      if (cfg) cfg.types.forEach((t) => types.add(t));
    }
    return types;
  }, [activeCategories]);

  // Filtered events
  const filtered = useMemo(() => {
    const lowerQuery = searchQuery.toLowerCase();
    return events.filter((ev) => {
      if (ev.tick < tickRange[0] || ev.tick > tickRange[1]) return false;
      if (!activeTypes.has(ev.type)) return false;
      if (agentFilter !== null && ev.agent_id !== agentFilter) return false;
      if (lowerQuery) {
        const text = formatEventData(ev).toLowerCase();
        const typeName = ev.type.toLowerCase();
        if (!text.includes(lowerQuery) && !typeName.includes(lowerQuery)) return false;
      }
      return true;
    });
  }, [events, tickRange, activeTypes, agentFilter, searchQuery]);

  // Paginate (show first N)
  const [showCount, setShowCount] = useState(100);
  const visible = filtered.slice(0, showCount);

  const toggleCategory = (cat: string) => {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
    setShowCount(100);
  };

  const toggleExpand = (idx: number) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-4">Data Explorer</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            Every event from the simulation — every thought, every action,
            every message, every building. 22,648 events across 70 ticks, fully
            searchable and filterable. Complete transparency.
          </p>
        </Container>
      </Section>

      {/* Controls + content */}
      <Section bg="cream" className="pt-0">
        <div className="mx-auto max-w-7xl px-6">
          {/* ── Controls ── */}
          <div className="mb-8 space-y-4 rounded-xl border border-border bg-warm-white p-5">
            {/* Tick range */}
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Tick Range
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {[
                  [0, 10],
                  [10, 20],
                  [20, 30],
                  [30, 40],
                  [40, 50],
                  [50, 60],
                  [60, 70],
                  [0, 70],
                ].map(([s, e]) => (
                  <button
                    key={`${s}-${e}`}
                    onClick={() => { setTickRange([s, e]); setShowCount(100); }}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                      tickRange[0] === s && tickRange[1] === e
                        ? "bg-sky text-white"
                        : "border border-border bg-cream text-ink-muted hover:bg-parchment"
                    }`}
                  >
                    {s === 0 && e === 70 ? "All" : `${s}-${e}`}
                  </button>
                ))}
              </div>
            </div>

            {/* Category filters */}
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">
                Event Types
              </p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(EVENT_CATEGORIES).map(([cat, { label, color }]) => (
                  <button
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
                      activeCategories.has(cat)
                        ? "text-white"
                        : "border border-border bg-cream text-ink-muted"
                    }`}
                    style={activeCategories.has(cat) ? { backgroundColor: color } : undefined}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Agent filter + search */}
            <div className="flex flex-wrap items-end gap-4">
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Agent
                </p>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    onClick={() => setAgentFilter(null)}
                    className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                      agentFilter === null
                        ? "bg-ink text-cream"
                        : "border border-border bg-cream text-ink-muted hover:bg-parchment"
                    }`}
                  >
                    All
                  </button>
                  {Array.from({ length: 12 }, (_, i) => i).map((id) => (
                    <button
                      key={id}
                      onClick={() => setAgentFilter(agentFilter === id ? null : id)}
                      className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-all ${
                        agentFilter === id ? "text-white" : "border border-border bg-cream text-ink-muted"
                      }`}
                      style={agentFilter === id ? { backgroundColor: AGENT_COLORS[id] } : undefined}
                    >
                      {id}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex-1 min-w-[200px]">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Search
                </p>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => { setSearchQuery(e.target.value); setShowCount(100); }}
                  placeholder="Search event content..."
                  className="w-full rounded-lg border border-border bg-cream px-3 py-2 text-sm text-ink placeholder-ink-muted focus:border-sky focus:outline-none focus:ring-1 focus:ring-sky"
                />
              </div>
            </div>
          </div>

          {/* ── Stats bar ── */}
          <div className="mb-4 flex flex-wrap items-center gap-4 text-sm text-ink-muted">
            <span>
              Showing <strong className="text-ink">{visible.length}</strong> of{" "}
              <strong className="text-ink">{filtered.length.toLocaleString()}</strong> events
              {filtered.length !== events.length && (
                <span> (filtered from {events.length.toLocaleString()})</span>
              )}
            </span>
            {loading && <span className="text-sky">Loading...</span>}
          </div>

          {/* ── Event list ── */}
          {loaded && (
            <div className="space-y-1">
              {visible.map((ev, i) => {
                const isExpanded = expandedEvents.has(i);
                const summary = formatEventData(ev);
                return (
                  <div
                    key={i}
                    className="rounded-lg border border-border-light bg-warm-white transition-colors hover:border-border"
                  >
                    <button
                      onClick={() => toggleExpand(i)}
                      className="flex w-full items-start gap-3 px-4 py-2.5 text-left"
                    >
                      {/* Tick */}
                      <span className="mt-0.5 shrink-0 w-8 font-mono text-xs text-ink-muted text-right">
                        {ev.tick}
                      </span>

                      {/* Type badge */}
                      <span
                        className="mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase text-white"
                        style={{ backgroundColor: eventColor(ev.type) }}
                      >
                        {ev.type.split("_")[0]}
                      </span>

                      {/* Agent */}
                      {ev.agent_id !== null ? (
                        <span
                          className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
                          style={{ backgroundColor: AGENT_COLORS[ev.agent_id % AGENT_COLORS.length] }}
                        >
                          {ev.agent_id}
                        </span>
                      ) : (
                        <span className="mt-0.5 h-5 w-5 shrink-0" />
                      )}

                      {/* Content preview */}
                      <span className="flex-1 min-w-0 text-sm text-ink-light truncate">
                        <span className="font-medium text-ink">
                          {eventLabel(ev.type)}
                        </span>
                        {summary && (
                          <span className="ml-2 text-ink-muted">
                            {summary.slice(0, 120)}{summary.length > 120 ? "..." : ""}
                          </span>
                        )}
                      </span>
                    </button>

                    {/* Expanded detail */}
                    {isExpanded && (
                      <div className="border-t border-border-light px-4 py-3 text-sm">
                        <div className="mb-2 flex flex-wrap gap-4 text-xs text-ink-muted">
                          <span>Type: <strong>{ev.type}</strong></span>
                          <span>Tick: <strong>{ev.tick}</strong></span>
                          {ev.agent_id !== null && <span>Agent: <strong>{ev.agent_id}</strong></span>}
                        </div>
                        <div className="whitespace-pre-wrap leading-relaxed text-ink-light">
                          {summary}
                        </div>
                        <details className="mt-3">
                          <summary className="cursor-pointer text-xs text-ink-muted hover:text-ink">
                            Raw JSON
                          </summary>
                          <pre className="mt-2 max-h-60 overflow-auto rounded bg-parchment p-3 text-xs font-mono text-ink-muted">
                            {JSON.stringify(ev.data, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Load more */}
          {showCount < filtered.length && (
            <div className="mt-6 text-center">
              <button
                onClick={() => setShowCount((c) => c + 200)}
                className="rounded-full border border-border bg-warm-white px-6 py-2.5 text-sm font-medium text-ink-light transition-colors hover:bg-parchment"
              >
                Show more ({Math.min(200, filtered.length - showCount)} of{" "}
                {(filtered.length - showCount).toLocaleString()} remaining)
              </button>
            </div>
          )}

          {/* Navigation */}
          <div className="mt-12 flex flex-wrap gap-4 border-t border-border pt-8 text-sm">
            <Link
              to="/fishbowl"
              className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
            >
              Watch the Replay
            </Link>
            <Link
              to="/simulations"
              className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
            >
              Charts & Profiles
            </Link>
            <Link
              to="/interviews"
              className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
            >
              Interviews
            </Link>
          </div>
        </div>
      </Section>
    </>
  );
}
