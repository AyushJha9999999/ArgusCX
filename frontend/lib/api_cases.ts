export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
export const ARGUSCX_KEY = process.env.NEXT_PUBLIC_ARGUSCX_KEY || "acx_master_2026_hackathon";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  
  headers.set("X-ArgusCX-Key", ARGUSCX_KEY);

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    throw new Error(`API Error ${response.status}`);
  }
  if (response.status === 204) return null;
  return await response.json();
}

export async function getCases() {
  return fetchApi('/cases');
}

export async function getCaseDetails(case_id: string) {
  return fetchApi(`/cases/${case_id}`);
}

export async function resolveCase(case_id: string, decision: string, notes: string) {
  return fetchApi(`/cases/${case_id}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ decision, notes })
  });
}
