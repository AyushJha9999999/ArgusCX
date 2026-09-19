/**
 * Verification API client.
 *
 * The backend exposes every application endpoint below `/api/v1`. Keeping that
 * prefix in one place prevents individual dashboard pages from accidentally
 * calling an unversioned (and non-existent) route.
 */

const API_PREFIX = "/api/v1";

export type VerificationSignal = {
  confidence?: number;
  findings?: string;
};

export type VerificationCase = {
  id: string;
  session_id: string;
  state: string;
  routing?: string;
  risk_score?: number;
  signals?: Record<string, VerificationSignal>;
  reasoning_narrative?: string;
  created_at: string;
  order_id?: string;
  customer_ref?: string;
  category?: string;
  assurance_level?: string;
};

export type CasesResponse = {
  total: number;
  cases: VerificationCase[];
  limit: number;
  offset: number;
};

export type VerificationSession = {
  session_id: string;
  status: string;
  order_id?: string | null;
  assurance_level: string;
  challenges_total: number;
  challenges_completed: number;
  created_at: string;
  expires_at: string;
  completed_at?: string | null;
};

export type SessionsResponse = {
  total: number;
  sessions: VerificationSession[];
  limit: number;
  offset: number;
};

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

function getDashboardToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("arguscx_dashboard_token");
}

function toApiUrl(endpoint: string) {
  const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${API_PREFIX}${path}`;
}

export function getApiBaseUrl() {
  return "";
}

/**
 * Fetch an API response and report useful, typed failures to the UI. The
 * relative URL fallback intentionally uses the Next.js `/api` rewrite so a
 * dashboard deployed alongside its backend does not need a public hostname.
 */
export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;

  if (!headers.has("Content-Type") && !isFormData) {
    headers.set("Content-Type", "application/json");
  }

  const dashboardToken = getDashboardToken();
  if (dashboardToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${dashboardToken}`);
  }

  let response: Response;
  try {
    response = await fetch(toApiUrl(endpoint), {
      ...options,
      headers,
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiRequestError("ArgusCX API is unavailable through the configured proxy. Start the backend and try again.");
  }

  if (!response.ok) {
    let detail = "Request failed";
    try {
      const body: unknown = await response.json();
      if (typeof body === "object" && body !== null) {
        const value = (body as { detail?: unknown; error?: unknown }).detail
          ?? (body as { error?: unknown }).error;
        if (typeof value === "string") detail = value;
      }
    } catch {
      // A non-JSON error response is still represented by its status below.
    }
    
    if (response.status === 401) {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("arguscx_dashboard_token");
        window.location.href = "/login";
      }
    }
    
    throw new ApiRequestError(`${detail} (HTTP ${response.status})`, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getCases() {
  return fetchApi<CasesResponse>("/cases");
}

export function getCaseDetails(caseId: string) {
  return fetchApi<VerificationCase & { session?: Record<string, unknown> }>(`/cases/${encodeURIComponent(caseId)}`);
}

export function reviewCase(caseId: string, decision: "APPROVED" | "REJECTED" | "ESCALATED", notes: string) {
  return fetchApi<{ message: string; case_id: string; decision: string }>(`/cases/${encodeURIComponent(caseId)}/review`, {
    method: "POST",
    body: JSON.stringify({ reviewer_id: "dashboard_operator", decision, notes }),
  });
}

// Kept as an alias while pages migrate to the precise review terminology.
export const resolveCase = reviewCase;

export function getSessions(limit = 100) {
  return fetchApi<SessionsResponse>(`/sessions?limit=${encodeURIComponent(String(limit))}`);
}
