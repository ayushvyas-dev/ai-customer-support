const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface EventItem {
  id: number;
  gmail_message_id: string;
  status: "processing" | "processed" | "skipped" | "failed";
  attempts: number;
  error: string | null;
  result: Record<string, unknown> | null;
  created_at: string;
  processed_at: string | null;
}

export interface TicketItem {
  id: number;
  gmail_thread_id: string;
  customer_email: string;
  subject: string;
  category: string | null;
  status: "open" | "answered" | "escalated";
  proposed_action: string | null;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface MessageItem {
  id: number;
  ticket_id: number;
  gmail_message_id: string;
  direction: "in" | "out";
  from_address: string;
  body: string;
  created_at: string;
}

export interface KnowledgeBaseItem {
  id: number;
  section: string;
  title: string;
  content: string;
  updated_at: string;
}

export interface EventsResponse {
  items: EventItem[];
  total: number;
  stats: {
    total: number;
    processing: number;
    processed: number;
    skipped: number;
    failed: number;
  };
}

export interface TicketsResponse {
  items: TicketItem[];
  total: number;
  stats: {
    total: number;
    open: number;
    answered: number;
    escalated: number;
  };
}

export interface TicketDetailResponse {
  ticket: TicketItem;
  messages: MessageItem[];
}

export interface KnowledgeBaseResponse {
  items: KnowledgeBaseItem[];
  sections: string[];
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("support_token");
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("support_token", token);
  document.cookie = `support_token=${token}; path=/; max-age=604800; SameSite=Lax`;
}

export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("support_token");
  document.cookie = "support_token=; path=/; max-age=0";
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    removeToken();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}

export const api = {
  async login(username: string, password: string): Promise<{ token: string; username: string }> {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Invalid credentials");
    }

    const data = await res.json();
    setToken(data.token);
    return data;
  },

  async me(): Promise<{ username: string; authenticated: boolean }> {
    return request("/api/auth/me");
  },

  async getEvents(params: {
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<EventsResponse> {
    const query = new URLSearchParams();
    if (params.status && params.status !== "all") query.set("status", params.status);
    if (params.search) query.set("search", params.search);
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));

    const qs = query.toString();
    return request(`/api/events${qs ? `?${qs}` : ""}`);
  },

  async getEvent(id: number): Promise<EventItem> {
    return request(`/api/events/${id}`);
  },

  async getTickets(params: {
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<TicketsResponse> {
    const query = new URLSearchParams();
    if (params.status && params.status !== "all") query.set("status", params.status);
    if (params.search) query.set("search", params.search);
    if (params.limit) query.set("limit", String(params.limit));
    if (params.offset) query.set("offset", String(params.offset));

    const qs = query.toString();
    return request(`/api/tickets${qs ? `?${qs}` : ""}`);
  },

  async getTicket(id: number): Promise<TicketDetailResponse> {
    return request(`/api/tickets/${id}`);
  },

  async updateTicketStatus(
    id: number,
    data: { status: "open" | "answered" | "escalated"; category?: string; proposed_action?: string }
  ): Promise<{ status: string }> {
    return request(`/api/tickets/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async getKnowledgeBase(params: {
    section?: string;
    search?: string;
  } = {}): Promise<KnowledgeBaseResponse> {
    const query = new URLSearchParams();
    if (params.section && params.section !== "all") query.set("section", params.section);
    if (params.search) query.set("search", params.search);

    const qs = query.toString();
    return request(`/api/knowledge-base${qs ? `?${qs}` : ""}`);
  },

  async saveKnowledgeBase(entry: {
    section: string;
    title: string;
    content: string;
  }): Promise<{ id: number; status: string }> {
    return request("/api/knowledge-base", {
      method: "POST",
      body: JSON.stringify(entry),
    });
  },

  async updateKnowledgeBase(
    id: number,
    entry: {
      section: string;
      title: string;
      content: string;
    }
  ): Promise<{ id: number; status: string }> {
    return request(`/api/knowledge-base/${id}`, {
      method: "PUT",
      body: JSON.stringify(entry),
    });
  },

  async deleteKnowledgeBase(id: number): Promise<{ status: string; id: number }> {
    return request(`/api/knowledge-base/${id}`, {
      method: "DELETE",
    });
  },
};

