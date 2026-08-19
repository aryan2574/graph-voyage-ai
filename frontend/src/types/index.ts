export interface TravelRequest {
  message: string;
  thread_id?: string | null;
}

export interface ApprovalRequest {
  thread_id: string;
  approved: boolean;
  feedback?: string;
}

export interface TravelResponse {
  success: boolean;
  thread_id: string;
  message?: string;
  answer?: string;
  requires_approval?: boolean;
  supervisor_reasoning?: string;
  agents_involved?: string[];
  guardrail_allowed?: boolean;
  latency_seconds?: number;
  error?: string;
}

export interface HealthResponse {
  status: string;
  message: string;
  features: string[];
}

export interface MetricsResponse {
  success: boolean;
  rolling_metrics: {
    total_requests: number;
    evaluated_count: number;
    pass_rate: number;
    safety_rate: number;
    avg_latency: number;
    p95_latency: number;
  };
  last_24_hours: {
    hourly_counts: number[];
    hourly_pass_rates: number[];
    labels: string[];
  };
  note: string;
}

export interface AgentInfo {
  name: string;
  icon: string;
  label: string;
}

export const AGENT_INFO: Record<string, AgentInfo> = {
  flight_agent: { name: 'flight_agent', icon: '✈️', label: 'Flight Agent' },
  hotel_agent: { name: 'hotel_agent', icon: '🏨', label: 'Hotel Agent' },
  weather_agent: { name: 'weather_agent', icon: '🌦️', label: 'Weather Agent' },
  budget_agent: { name: 'budget_agent', icon: '💰', label: 'Budget Agent' },
  itinerary_agent: { name: 'itinerary_agent', icon: '🗓️', label: 'Itinerary Agent' },
};
