export type ModelProviderType =
  | "TRAINED_ML"
  | "STATISTICAL_MODEL"
  | "RULE_BASED"
  | "FALLBACK_SIMULATION";

export type AIRiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AIAlertSeverity = "INFO" | "WARNING" | "HIGH" | "CRITICAL";

export type AIAlertStatus = "ACTIVE" | "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED";

export interface StandardAIExplanation {
  summary: string;
  reasons: string[];
  contributing_factors?: Array<{ param: string; value: string; status: string }>;
  recommended_action: string;
}

export interface AIPrediction {
  id: number;
  prediction_type: string;
  entity_type: string;
  entity_id?: string;
  prediction_value: any;
  risk_level: AIRiskLevel;
  confidence?: number;
  model_name: string;
  model_version: string;
  model_provider_type: ModelProviderType;
  explanation: StandardAIExplanation;
  recommended_action: string;
  generated_at: string;
}

export interface AIAlert {
  id: number;
  alert_type: string;
  severity: AIAlertSeverity;
  title: string;
  description: string;
  reason: string[] | any;
  recommended_action: string;
  related_entity: string;
  related_entity_id?: string;
  status: AIAlertStatus;
  created_at: string;
  acknowledged_at?: string;
}

export interface QueueTrendPoint {
  time_slot: string;
  tokens_served: number;
  avg_wait_minutes: number;
  projected_wait_minutes: number;
}

export interface OpdQueuePredictionResponse {
  department_id?: number;
  department_name?: string;
  doctor_id?: number;
  doctor_name?: string;
  current_waiting_count: number;
  current_serving_token?: string;
  estimated_wait_minutes: number;
  historical_avg_wait_minutes: number;
  predicted_delay_minutes: number;
  risk_level: AIRiskLevel;
  confidence?: number;
  model_provider_type: ModelProviderType;
  model_version: string;
  explanation: StandardAIExplanation;
  recommended_action: string;
  doctor_utilization_percent: number;
  hourly_trend: QueueTrendPoint[];
  alert_triggered: boolean;
}

export interface ForecastHorizonPoint {
  horizon_hours: number;
  projected_occupancy_percent: number;
  projected_admissions: number;
  projected_discharges: number;
  net_bed_delta: number;
  risk_level: AIRiskLevel;
}

export interface WardForecastSummary {
  ward_id: number;
  ward_name: string;
  ward_type: string;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  current_occupancy_percent: number;
  projected_24h_occupancy_percent: number;
  risk_level: AIRiskLevel;
}

export interface BedPredictionResponse {
  ward_id?: number;
  ward_name?: string;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  current_occupancy_percent: number;
  horizons: ForecastHorizonPoint[];
  ward_breakdown: WardForecastSummary[];
  overall_risk_level: AIRiskLevel;
  confidence?: number;
  model_provider_type: ModelProviderType;
  model_version: string;
  explanation: StandardAIExplanation;
  recommended_action: string;
  alert_triggered: boolean;
}

export interface ConsumptionTrendPoint {
  date_label: string;
  units_dispensed: number;
  daily_average: number;
  stock_level_at_end_of_day: number;
}

export interface MedicineDepletionForecast {
  medicine_id: number;
  medicine_code: string;
  medicine_name: string;
  category: string;
  current_stock: number;
  reorder_level: number;
  max_stock_level: number;
  avg_daily_consumption: number;
  estimated_days_remaining: number;
  predicted_depletion_date?: string;
  recommended_reorder_quantity: number;
  risk_level: AIRiskLevel;
  expiry_risk_category?: string;
  confidence?: number;
  model_provider_type: ModelProviderType;
  explanation: StandardAIExplanation;
  recommended_action: string;
}

export interface PharmacyPredictionResponse {
  total_medicines_analyzed: number;
  critical_depletion_count: number;
  high_depletion_count: number;
  total_stock_value: number;
  top_depletion_risks: MedicineDepletionForecast[];
  selected_medicine_forecast?: MedicineDepletionForecast;
  consumption_trend_chart: ConsumptionTrendPoint[];
  overall_risk_level: AIRiskLevel;
  model_provider_type: ModelProviderType;
  model_version: string;
  alert_triggered: boolean;
}

export interface TriageAIResponse {
  triage_level: string;
  color_hex: string;
  risk_level: AIRiskLevel;
  contributing_factors: string[];
  vital_flags: Array<{ param: string; value: string; status: string }>;
  recommended_action: string;
  target_assessment_time_minutes: number;
  model_provider_type: ModelProviderType;
  model_version: string;
  explanation: StandardAIExplanation;
  disclaimer: string;
}

export interface ExtractedParameter {
  parameter_name: string;
  result_value: string;
  numeric_value?: number;
  unit: string;
  reference_range: string;
  flag: string; // NORMAL, LOW, HIGH, CRITICAL
  is_abnormal: boolean;
}

export interface DocumentAnalysisResponse {
  document_id?: number;
  file_name: string;
  file_type: string;
  document_type: string;
  patient_id?: number;
  patient_name?: string;
  extracted_parameters: ExtractedParameter[];
  abnormal_parameters_count: number;
  ai_summary: string;
  key_findings: string[];
  risk_level: AIRiskLevel;
  confidence?: number;
  model_provider_type: ModelProviderType;
  model_version: string;
  is_verified: boolean;
  disclaimer: string;
}

export interface StructuredClinicalNoteDraft {
  chief_complaint: string;
  duration?: string;
  vital_signs_mentioned: Record<string, string>;
  associated_symptoms: string[];
  examination_notes: string;
  suggested_assessment_plan: string;
}

export interface VoiceTranscriptionResponse {
  raw_transcript: string;
  structured_note: StructuredClinicalNoteDraft;
  formatted_clinical_summary: string;
  model_provider_type: ModelProviderType;
  model_version: string;
  doctor_verification_required: boolean;
  disclaimer: string;
}

export interface PatientHandoverSummaryItem {
  admission_id: number;
  admission_number: string;
  patient_id: number;
  patient_name: string;
  patient_mrn: string;
  bed_number: string;
  ward_name: string;
  priority: AIRiskLevel;
  current_status: string;
  latest_vitals: Record<string, string>;
  pending_investigations: string[];
  active_medications: string[];
  key_tasks: string[];
  important_observations: string;
}

export interface ShiftHandoverResponse {
  handover_id?: number;
  ward_id?: number;
  ward_name?: string;
  shift_name: string;
  from_nurse_id: number;
  from_nurse_name: string;
  to_nurse_id?: number;
  total_patients: number;
  high_priority_patients: number;
  patient_summaries: PatientHandoverSummaryItem[];
  important_observations: string;
  next_shift_checklist: string[];
  ai_notes: string;
  status: string;
  is_approved: boolean;
  approved_by_name?: string;
  created_at: string;
  model_provider_type: ModelProviderType;
  model_version: string;
  disclaimer: string;
}

export interface OperationalAnomalyItem {
  anomaly_key: string;
  title: string;
  domain: string;
  severity: AIAlertSeverity;
  current_value: number;
  expected_value: number;
  unit: string;
  percentage_deviation: number;
  is_anomaly: boolean;
  explanation_reason: string;
  recommended_action: string;
  detected_at: string;
}

export interface AnomalyDetectionResponse {
  total_metrics_evaluated: number;
  anomalies_detected_count: number;
  critical_anomalies_count: number;
  high_anomalies_count: number;
  anomalies: OperationalAnomalyItem[];
  overall_system_status: string;
  model_provider_type: ModelProviderType;
  model_version: string;
  evaluated_at: string;
}

export interface AIInsightsResponse {
  summary: {
    active_alerts_count: number;
    critical_alerts_count: number;
    total_predictions_count: number;
    overall_system_status: string;
    evaluated_at: string;
  };
  alerts: AIAlert[];
  predictions: AIPrediction[];
  quick_status: {
    opd: {
      waiting_count: number;
      estimated_wait_minutes: number;
      delay_minutes: number;
      risk: AIRiskLevel;
      model_provider: ModelProviderType;
    };
    beds: {
      occupancy_percent: number;
      projected_24h_percent: number;
      risk: AIRiskLevel;
      available_beds: number;
      total_beds: number;
      model_provider: ModelProviderType;
    };
    pharmacy: {
      critical_count: number;
      high_count: number;
      risk: AIRiskLevel;
      total_stock_value: number;
      model_provider: ModelProviderType;
    };
    anomalies: {
      anomalies_detected_count: number;
      critical_count: number;
      overall_status: string;
    };
  };
}
