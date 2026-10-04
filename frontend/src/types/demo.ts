import { HospitalBrainEvent, HospitalSystemStatus } from './hospital_brain';

export interface DemoScenario {
  id?: number;
  code: string;
  title: string;
  name?: string; // backwards compatibility
  badge?: string;
  button_label?: string;
  category: string;
  description: string;
  target_metrics: Record<string, any>;
  affected_departments: string[];
  is_flagship: boolean;
  expected_events?: number;
  expected_intelligence?: string;
  expected_risks?: string[];
}

export interface DemoScenarioLaunchRequest {
  scenario_code: string;
}

export interface DemoScenarioResult {
  scenario_code: string;
  title?: string;
  name?: string;
  status?: string;
  message?: string;
  affected_departments?: string[];
  system_status?: HospitalSystemStatus;
  hospital_status?: HospitalSystemStatus;
  generated_events?: HospitalBrainEvent[];
  timestamp?: string;
  telemetry_impact?: Record<string, any>;
  pipeline_stage?: number;
}

export interface DemoResetResponse {
  status: string;
  message: string;
  baseline_kpis: Record<string, any>;
  reset_timestamp: string;
}

export interface DemoPipelineStep {
  step_number?: number;
  step_index?: number;
  step_name: string;
  department?: string;
  description: string;
  status?: string;
  output_summary?: string;
  is_completed: boolean;
  is_active?: boolean;
  detected_at?: string;
  contributing_signals?: string[];
}

export interface DemoPipelineProgress {
  active_scenario_code: string;
  active_scenario_title?: string;
  active_scenario_name?: string;
  hospital_status: HospitalSystemStatus;
  steps: DemoPipelineStep[];
  summary_recommendation?: string;
  total_steps?: number;
  completed_steps?: number;
  progress_pct?: number;
  started_at?: string;
}

export interface PatientJourneyEvent {
  stage_id: number;
  stage_name: string;
  timestamp: string;
  department: string;
  responsible_role: string;
  status: string;
  summary: string;
  details: Record<string, any>;
  ai_insight?: string;
  is_clinical_alert: boolean;
}

export interface PatientJourneyResponse {
  patient_id: number;
  mrn: string;
  patient_name: string;
  age?: number;
  gender?: string;
  blood_group?: string;
  allergies?: string[];
  current_medications?: string[];
  admission_status: string;
  events_count: number;
  journey_stages: PatientJourneyEvent[];
}
