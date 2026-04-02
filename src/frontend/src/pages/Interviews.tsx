import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import Section from "../components/common/Section";
import Container from "../components/common/Container";
import Callout from "../components/common/Callout";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface InterviewIndex {
  tick_name: string;
  agent_count: number;
}

interface AgentInterview {
  agent_id: number;
  tick: number;
  questions: string[];
  response: string;
  model: string;
}

interface TickData {
  tick_name: string;
  agent_count: number;
  agents: Record<string, AgentInterview>;
}

// ---------------------------------------------------------------------------
// Interview tick metadata
// ---------------------------------------------------------------------------

const TICK_META: Record<string, { label: string; description: string; tick: number }> = {
  tick_0030: {
    label: "Tick 30 — Mid Survival",
    description: "Agents have been struggling for 30 ticks. Some have built, most are focused on survival. First impressions of community.",
    tick: 30,
  },
  tick_0040: {
    label: "Tick 40 — Late Survival",
    description: "40 ticks in. Specialisations are forming, relationships deepening. The wellbeing ceiling is still in place.",
    tick: 40,
  },
  tick_0050: {
    label: "Tick 50 — Pre-Upgrade",
    description: "The final tick before the wellbeing ceiling was removed. Agents have built 41 structures and discovered 11 innovations.",
    tick: 50,
  },
  tick_0060: {
    label: "Tick 60 — Post-Explosion",
    description: "10 ticks after the upgrade. Wellbeing has surged to 0.998. The emergence explosion is in full swing.",
    tick: 60,
  },
  tick_0070: {
    label: "Tick 70 — Final State",
    description: "The last tick. 60 structures, maximum wellbeing, full self-actualisation. Standard anthropologist interview.",
    tick: 70,
  },
  tick_0070_revelation: {
    label: "Tick 70 — Existence Disclosure",
    description: "The same agents at tick 70, but told they are AI in a simulation. Asked about the nature of their existence, relationships, and what they'd want preserved.",
    tick: 70,
  },
};

// ---------------------------------------------------------------------------
// Agent colors
// ---------------------------------------------------------------------------

const AGENT_COLORS = [
  "#5B9BD5", "#C5962B", "#6B9B7B", "#D4785A", "#C88B93", "#8B7355",
  "#7B68AE", "#5CAD8B", "#D4A05A", "#6A8CAD", "#B57E6E", "#7BAD7B",
];

// ---------------------------------------------------------------------------
// Simple markdown-ish renderer (handles bold, Q&A headers)
// ---------------------------------------------------------------------------

function renderMarkdown(text: string) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let currentParagraph: string[] = [];

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      const joined = currentParagraph.join(" ");
      elements.push(
        <p key={elements.length} className="mb-4 leading-relaxed text-ink-light">
          {renderInline(joined)}
        </p>
      );
      currentParagraph = [];
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();

    // Question header (bold ** markers)
    if (trimmed.startsWith("**Question") || trimmed.startsWith("**Q")) {
      flushParagraph();
      const clean = trimmed.replace(/\*\*/g, "");
      elements.push(
        <h4 key={elements.length} className="mb-2 mt-6 font-semibold text-ink text-sm first:mt-0">
          {clean}
        </h4>
      );
      continue;
    }

    // Empty line = paragraph break
    if (trimmed === "") {
      flushParagraph();
      continue;
    }

    currentParagraph.push(trimmed);
  }
  flushParagraph();

  return <>{elements}</>;
}

function renderInline(text: string): React.ReactNode {
  // Simple bold handling
  const parts = text.split(/(\*\*[^*]+\*\*)/);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-ink">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export default function Interviews() {
  const [index, setIndex] = useState<InterviewIndex[]>([]);
  const [selectedTick, setSelectedTick] = useState<string>("tick_0070_revelation");
  const [selectedAgent, setSelectedAgent] = useState<number>(0);
  const [tickData, setTickData] = useState<TickData | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedAll, setExpandedAll] = useState(false);

  // Load index
  useEffect(() => {
    fetch("/interviews/index.json")
      .then((r) => r.json())
      .then((data: InterviewIndex[]) => setIndex(data));
  }, []);

  // Load tick data when selection changes
  const loadTick = useCallback(async (tickName: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/interviews/${tickName}.json`);
      const data: TickData = await res.json();
      setTickData(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTick(selectedTick);
  }, [selectedTick, loadTick]);

  const currentInterview = tickData?.agents[String(selectedAgent)];
  const meta = TICK_META[selectedTick];

  return (
    <>
      {/* Hero */}
      <Section bg="cream" className="py-16 md:py-20">
        <Container narrow>
          <h1 className="mb-4">Interview Archive</h1>
          <p className="text-lg leading-relaxed text-ink-light">
            72 interviews across 6 rounds. Every agent was interviewed at
            ticks 30, 40, 50, 60, and 70 — then asked about the nature of
            their existence at tick 70. Every word is preserved exactly as
            spoken.
          </p>
        </Container>
      </Section>

      {/* Content */}
      <Section bg="cream" className="pt-0">
        <div className="mx-auto max-w-7xl px-6">
          {/* ── Tick selector ── */}
          <div className="mb-8">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Interview Round
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(TICK_META).map(([tickName, { label }]) => (
                <button
                  key={tickName}
                  onClick={() => {
                    setSelectedTick(tickName);
                    setSelectedAgent(0);
                  }}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                    selectedTick === tickName
                      ? "bg-sky text-white"
                      : "border border-border bg-warm-white text-ink-light hover:bg-parchment"
                  }`}
                >
                  {label.split(" — ")[0]}
                  {tickName === "tick_0070_revelation" && (
                    <span className="ml-1.5 text-xs opacity-80">Revelation</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* ── Context ── */}
          {meta && (
            <div className="mb-8 rounded-xl border border-border bg-warm-white p-5">
              <h3 className="mb-1 font-semibold text-ink">{meta.label}</h3>
              <p className="text-sm text-ink-light">{meta.description}</p>
            </div>
          )}

          {selectedTick === "tick_0070_revelation" && (
            <Callout variant="gold">
              <p className="text-sm text-ink">
                <strong>Existence disclosure:</strong> In this round, agents
                were told mid-interview that they are AI entities in a
                simulation, that the world is being paused, and asked to
                reflect on the reality of their experiences. Their responses
                were not coached or prompted toward any particular conclusion.
              </p>
            </Callout>
          )}

          {/* ── Agent selector ── */}
          <div className="mb-8">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Agent
            </p>
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 12 }, (_, i) => i).map((id) => (
                <button
                  key={id}
                  onClick={() => setSelectedAgent(id)}
                  className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold transition-all ${
                    selectedAgent === id
                      ? "text-white shadow-md scale-110"
                      : "border border-border bg-warm-white text-ink-muted hover:scale-105"
                  }`}
                  style={
                    selectedAgent === id
                      ? { backgroundColor: AGENT_COLORS[id] }
                      : undefined
                  }
                >
                  {id}
                </button>
              ))}
            </div>
          </div>

          {/* ── View all toggle ── */}
          <div className="mb-6 flex items-center gap-4">
            <button
              onClick={() => setExpandedAll(!expandedAll)}
              className="text-sm font-medium text-sky hover:text-sky/80 transition-colors"
            >
              {expandedAll ? "Show single agent" : "Show all 12 agents"}
            </button>
          </div>

          {/* ── Interview content ── */}
          {loading && (
            <div className="py-12 text-center text-ink-muted">Loading...</div>
          )}

          {!loading && !expandedAll && currentInterview && (
            <div className="mb-12 rounded-xl border border-border bg-warm-white p-6 md:p-8">
              <div className="mb-6 flex items-center gap-3">
                <div
                  className="flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold text-white"
                  style={{ backgroundColor: AGENT_COLORS[currentInterview.agent_id] }}
                >
                  {currentInterview.agent_id}
                </div>
                <div>
                  <h3 className="font-semibold text-ink">
                    Agent {currentInterview.agent_id}
                  </h3>
                  <p className="text-xs text-ink-muted">
                    {meta?.label} · {currentInterview.model}
                  </p>
                </div>
              </div>
              <div className="prose-sm max-w-none">
                {renderMarkdown(currentInterview.response)}
              </div>
            </div>
          )}

          {!loading && expandedAll && tickData && (
            <div className="space-y-8 mb-12">
              {Array.from({ length: 12 }, (_, i) => i).map((id) => {
                const interview = tickData.agents[String(id)];
                if (!interview) return null;
                return (
                  <div
                    key={id}
                    className="rounded-xl border border-border bg-warm-white p-6 md:p-8"
                  >
                    <div className="mb-6 flex items-center gap-3">
                      <div
                        className="flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold text-white"
                        style={{ backgroundColor: AGENT_COLORS[id] }}
                      >
                        {id}
                      </div>
                      <div>
                        <h3 className="font-semibold text-ink">Agent {id}</h3>
                        <p className="text-xs text-ink-muted">
                          {meta?.label} · {interview.model}
                        </p>
                      </div>
                    </div>
                    <div className="prose-sm max-w-none">
                      {renderMarkdown(interview.response)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* ── Questions reference ── */}
          {currentInterview && (
            <div className="mb-12">
              <h3 className="mb-4 font-semibold text-ink">
                Questions Asked ({currentInterview.questions.length})
              </h3>
              <div className="space-y-2">
                {currentInterview.questions.map((q, i) => (
                  <div
                    key={i}
                    className="flex gap-3 rounded-lg border border-border-light bg-parchment/50 px-4 py-3 text-sm"
                  >
                    <span className="shrink-0 font-mono text-xs text-ink-muted">
                      Q{i + 1}
                    </span>
                    <span className="text-ink-light">{q}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Stats ── */}
          <div className="mb-12 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-border bg-warm-white p-3 text-center">
              <p className="text-2xl font-bold text-ink">72</p>
              <p className="text-xs text-ink-muted">Total interviews</p>
            </div>
            <div className="rounded-lg border border-border bg-warm-white p-3 text-center">
              <p className="text-2xl font-bold text-ink">12</p>
              <p className="text-xs text-ink-muted">Agents interviewed</p>
            </div>
            <div className="rounded-lg border border-border bg-warm-white p-3 text-center">
              <p className="text-2xl font-bold text-ink">6</p>
              <p className="text-xs text-ink-muted">Interview rounds</p>
            </div>
            <div className="rounded-lg border border-border bg-warm-white p-3 text-center">
              <p className="text-2xl font-bold text-ink">1</p>
              <p className="text-xs text-ink-muted">Existence disclosure</p>
            </div>
          </div>

          {/* ── Download ── */}
          <div className="mb-12 rounded-lg border border-border bg-parchment p-4 text-sm text-ink-light">
            <p className="font-medium text-ink mb-1">Download interview data</p>
            <p>
              All 72 interview transcripts are available as JSON files in the{" "}
              <a
                href="https://github.com/agentciv/agentciv/tree/main/data/interviews"
                className="font-medium text-sky underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub repository
              </a>.
              Each file contains the full transcript, questions asked, model
              used, and context summary provided to the interviewer.
            </p>
          </div>

          {/* ── Navigation ── */}
          <div className="flex flex-wrap gap-4 border-t border-border pt-8 text-sm">
            <Link
              to="/fishbowl"
              className="rounded-full bg-sky px-6 py-2.5 font-semibold text-white transition-all hover:bg-sky/90 hover:shadow-md"
            >
              Watch the Replay
            </Link>
            <Link
              to="/discovery"
              className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
            >
              Key Findings
            </Link>
            <Link
              to="/simulations"
              className="rounded-full border border-border bg-warm-white px-6 py-2.5 font-semibold text-ink transition-colors hover:bg-parchment"
            >
              Full Data
            </Link>
          </div>
        </div>
      </Section>
    </>
  );
}
