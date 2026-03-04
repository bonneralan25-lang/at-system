const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  // Leads
  getLeads: (params?: string) =>
    request<Lead[]>(`/api/leads${params ? `?${params}` : ""}`),
  getLead: (id: string) => request<LeadDetail>(`/api/leads/${id}`),

  // Estimates
  getEstimates: (params?: string) =>
    request<Estimate[]>(`/api/estimates${params ? `?${params}` : ""}`),
  getEstimate: (id: string) => request<EstimateDetail>(`/api/estimates/${id}`),
  approveEstimate: (id: string) =>
    request<Estimate>(`/api/estimates/${id}/approve`, { method: "POST" }),
  rejectEstimate: (id: string, notes: string) =>
    request<Estimate>(`/api/estimates/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    }),
  adjustEstimate: (id: string, low: number, high: number, notes: string) =>
    request<Estimate>(`/api/estimates/${id}`, {
      method: "PUT",
      body: JSON.stringify({ estimate_low: low, estimate_high: high, owner_notes: notes }),
    }),

  // Settings
  getPricing: () => request<PricingConfig[]>(`/api/settings/pricing`),
  updatePricing: (service_type: string, config: object) =>
    request<PricingConfig>(`/api/settings/pricing`, {
      method: "PUT",
      body: JSON.stringify({ service_type, config }),
    }),

  // Stats
  getStats: () => request<DashboardStats>(`/api/stats`),
};

// --- Types ---
export type ServiceType = "fence_staining" | "pressure_washing";
export type LeadStatus = "new" | "estimated" | "approved" | "rejected" | "sent";
export type EstimateStatus = "pending" | "approved" | "rejected" | "adjusted";

export interface Lead {
  id: string;
  ghl_contact_id: string;
  service_type: ServiceType;
  status: LeadStatus;
  address: string;
  created_at: string;
  form_data: Record<string, string>;
}

export interface LeadDetail extends Lead {
  estimate?: EstimateDetail;
}

export interface Estimate {
  id: string;
  lead_id: string;
  service_type: ServiceType;
  status: EstimateStatus;
  estimate_low: number;
  estimate_high: number;
  owner_notes: string | null;
  created_at: string;
  approved_at: string | null;
  lead?: Lead;
}

export interface EstimateDetail extends Estimate {
  inputs: Record<string, string | number | boolean>;
  breakdown: BreakdownItem[];
}

export interface BreakdownItem {
  label: string;
  value: number;
  note?: string;
}

export interface PricingConfig {
  service_type: ServiceType;
  config: Record<string, unknown>;
  updated_at: string;
}

export interface DashboardStats {
  pending_estimates: number;
  leads_this_week: number;
  approved_this_month: number;
  revenue_estimate_this_month: number;
}
