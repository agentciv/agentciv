/**
 * REST API client for the Agent Civilisation backend.
 *
 * All paths are relative ("/api/...") so that Vite's dev proxy or a
 * production reverse-proxy transparently forwards them to the backend.
 */

import type {
  WorldStateResponse,
  AgentListResponse,
  AgentDetailResponse,
  MemoryListResponse,
  InteractionListResponse,
  StructureListResponse,
  RecipeListResponse,
  RuleListResponse,
  ChronicleResponse,
  MilestoneListResponse,
  NarrativeListResponse,
  StatsResponse,
} from "../types";

// ---------------------------------------------------------------------------
// Generic fetcher
// ---------------------------------------------------------------------------

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText} — ${path}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Public API functions
// ---------------------------------------------------------------------------

export async function fetchState(): Promise<WorldStateResponse> {
  return get<WorldStateResponse>("/api/state");
}

export async function fetchHistoryState(tick: number): Promise<WorldStateResponse> {
  return get<WorldStateResponse>(`/api/state/history/${tick}`);
}

export async function fetchAgents(): Promise<AgentListResponse> {
  return get<AgentListResponse>("/api/agents");
}

export async function fetchAgent(id: number): Promise<AgentDetailResponse> {
  return get<AgentDetailResponse>(`/api/agents/${id}`);
}

export async function fetchAgentMemories(id: number): Promise<MemoryListResponse> {
  return get<MemoryListResponse>(`/api/agents/${id}/memories`);
}

export async function fetchAgentInteractions(
  id: number,
  partnerId?: number,
): Promise<InteractionListResponse> {
  const params = partnerId != null ? `?partner_id=${partnerId}` : "";
  return get<InteractionListResponse>(`/api/agents/${id}/interactions${params}`);
}

export async function fetchStructures(): Promise<StructureListResponse> {
  return get<StructureListResponse>("/api/structures");
}

export async function fetchRecipes(): Promise<RecipeListResponse> {
  return get<RecipeListResponse>("/api/recipes");
}

export async function fetchRules(): Promise<RuleListResponse> {
  return get<RuleListResponse>("/api/rules");
}

export async function fetchChronicle(params?: {
  since_tick?: number;
  type?: string;
}): Promise<ChronicleResponse> {
  const qs = new URLSearchParams();
  if (params?.since_tick != null) qs.set("since_tick", String(params.since_tick));
  if (params?.type) qs.set("type", params.type);
  const suffix = qs.toString() ? `?${qs}` : "";
  return get<ChronicleResponse>(`/api/chronicle${suffix}`);
}

export async function fetchMilestones(): Promise<MilestoneListResponse> {
  return get<MilestoneListResponse>("/api/chronicle/milestones");
}

export async function fetchNarratives(): Promise<NarrativeListResponse> {
  return get<NarrativeListResponse>("/api/chronicle/narratives");
}

export async function fetchStats(): Promise<StatsResponse> {
  return get<StatsResponse>("/api/stats");
}
