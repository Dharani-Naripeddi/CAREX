import { ModelProviderType, AIRiskLevel, AIAlertSeverity, AIAlertStatus } from "./ai";

export type HospitalSystemStatus = "STABLE" | "WATCH" | "HIGH_LOAD" | "CRITICAL";

export type HospitalBrainEventType =
  | "OPD_DELAY"
  | "BED_CAPACITY_RISK"
  | "PHARMACY_DEPLETION"
  | "EMERGENCY_SURGE"
  | "LAB_BACKLOG"
  | "STAFFING_RISK"
  | "OPERATIONAL_ANOMALY"
  | "HOSPITAL_CAPACITY_RISK";

export type HospitalBrainSourceModule =
  | "OPD"
  | "EMERGENCY"
  | "BED"
  | "PHARMACY"
  | "LAB"
  | "STAFF"
  | "PATIENT_FLOW"
  | "AI_ENGINE"
  | "SYSTEM";

export interface PriorityFactor {
  name: string;
  weight_pct: number;
  contribution: number;
  reason: string;
}

export interface OperationalPriorityBreakdown {
  score: number; // 0 to 100
  rating: string; // LOW, MODERATE, HIGH, CRITICAL
  factors: PriorityFactor[];
  summary_explanation: string;
}

export interface HospitalBrainExplanation {
  what_is_happening: string;
  what_is_expected: string;
  why_flagged: string[];
  affected_departments: string[];
  affected_resources: string[];
  recommended_operational_review: string;
  data_sources: string[];
  model_provider_type: ModelProviderType;
  model_version: string;
  confidence?: number;
  safety_disclaimer: string;
}

export interface HospitalBrainEvent {
  id: number;
  source_module: HospitalBrainSourceModule;
  event_type: HospitalBrainEventType;
  severity: AIAlertSeverity;
  title: string;
  description: string;
  current_value?: any;
  predicted_value?: any;
  unit?: string;
  risk_level: AIRiskLevel;
  priority: OperationalPriorityBreakdown;
  explanation: HospitalBrainExplanation;
  recommended_action: string;
  related_entity_type: string;
  related_entity_id?: string;
  correlated_sources: string[];
  timestamp: string;
  expires_at?: string;
  status: AIAlertStatus;
  source_prediction_id?: number;
  is_composite_correlation: boolean;
}

export interface DepartmentStatusSummary {
  department_id?: number;
  department_name: string;
  department_code: string;
  status: HospitalSystemStatus;
  load_level: string;
  active_events_count: number;
  key_metrics: Record<string, any>;
  recommended_reviews: string[];
}

export interface TopKPIsSummary {
  hospital_capacity_percent: number;
  hospital_status: HospitalSystemStatus;
  emergency_load_level: string;
  active_emergency_count: number;
  opd_predicted_wait_minutes: number;
  opd_queue_count: number;
  available_beds_count: number;
  total_beds_count: number;
  pharmacy_critical_depletion_count: number;
  lab_pending_orders_count: number;
  active_intelligence_count: number;
  critical_alerts_count: number;
  departments_affected_count: number;
}

export interface HospitalBrainOverview {
  hospital_status: HospitalSystemStatus;
  evaluated_at: string;
  kpis: TopKPIsSummary;
  active_events: HospitalBrainEvent[];
  department_matrix: DepartmentStatusSummary[];
  top_recommended_actions: string[];
  is_simulation_mode: boolean;
}

export interface HospitalCapacityMatrix {
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  current_occupancy_percent: number;
  projected_24h_occupancy_percent: number;
  icu_total: number;
  icu_occupied: number;
  icu_available: number;
  icu_occupancy_percent: number;
  wards: Array<Record<string, any>>;
  queue_wait_summary: Record<string, any>;
}

export interface HospitalBrainActionItem {
  id: number;
  event_id: number;
  title: string;
  recommended_action: string;
  severity: AIAlertSeverity;
  responsible_department: string;
  status: AIAlertStatus;
  created_at: string;
  acknowledged_at?: string;
  acknowledged_by_name?: string;
}

export interface WhatIfSimulationRequest {
  emergency_arrival_delta_pct: number;
  icu_occupancy_delta_pct: number;
  opd_demand_delta_pct: number;
  ward_discharge_rate_delta_pct: number;
}

export interface WhatIfSimulationImpact {
  baseline_value: number;
  simulated_value: number;
  delta_value: number;
  unit: string;
  risk_level: AIRiskLevel;
  impact_description: string;
}

export interface WhatIfSimulationResponse {
  scenario_title: string;
  simulation_label: string;
  projected_hospital_status: HospitalSystemStatus;
  impacts: Record<string, WhatIfSimulationImpact>;
  affected_departments: string[];
  emerging_risks: string[];
  recommended_preemptive_actions: string[];
  evaluated_at: string;
}
