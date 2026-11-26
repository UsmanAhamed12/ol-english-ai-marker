/**
 * Client for the FastAPI backend.
 *
 * Leave VITE_API_BASE_URL empty to use the Vite dev proxy (same-origin /api).
 * The bearer token issued at login is kept in localStorage.
 */

const BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const TOKEN_KEY = "gradewise.token";

export const getToken = () =>
  typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY);

export const setToken = (token) => {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
};

async function request(path, { method = "GET", body, headers = {} } = {}) {
  const token = getToken();
  const isForm = body instanceof FormData;

  const response = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      ...(isForm || !body ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: isForm || !body ? body : JSON.stringify(body),
  });

  if (response.status === 204) return null;

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(payload.detail)
      ? payload.detail[0]?.msg
      : payload.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return payload;
}

export const api = {
  register: (data) => request("/api/auth/register", { method: "POST", body: data }),
  login: (data) => request("/api/auth/login", { method: "POST", body: data }),
  me: () => request("/api/auth/me"),

  papers: () => request("/api/papers"),
  paper: (id) => request(`/api/papers/${id}`),
  remark: (id) => request(`/api/papers/${id}/mark`, { method: "POST" }),
  deletePaper: (id) => request(`/api/papers/${id}`, { method: "DELETE" }),

  createPaper: ({ script, scheme }) => {
    const form = new FormData();
    script.forEach((file) => form.append("script", file));
    scheme.forEach((file) => form.append("scheme", file));
    return request("/api/papers", { method: "POST", body: form });
  },

  knowledge: () => request("/api/knowledge"),
  knowledgeStats: () => request("/api/knowledge/stats"),
  indexPapers: () => request("/api/knowledge/index-papers", { method: "POST" }),
  deleteKnowledge: (id) => request(`/api/knowledge/${id}`, { method: "DELETE" }),
  uploadKnowledge: ({ file, title, kind = "Syllabus", year = "", notes = "" }) => {
    const form = new FormData();
    form.append("file", file);
    form.append("title", title);
    form.append("kind", kind);
    form.append("year", year);
    form.append("notes", notes);
    return request("/api/knowledge/upload", { method: "POST", body: form });
  },
};