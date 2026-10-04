export type TriageLevel = "RED" | "ORANGE" | "YELLOW" | "GREEN";
export type ConsciousnessLevel = "ALERT" | "VOICE" | "PAIN" | "UNRESPONSIVE";
export type EmergencyCaseStatus = "ACTIVE" | "TRIAGED" | "ADMITTED_IPD" | "DISCHARGED" | "DECEASED";

export interface EmergencyCase {
  id: number;
  case_number: string;
  patient_id?: number | null;
  patient_name: string;
  age: number;
  gender: string;
  arrival_time: string;
  symptoms: string;
  injury_type?: string | null;
  heart_rate: number;
  bp_systolic: number;
  bp_diastolic: number;
  spo2: number;
  temperature: number;
  respiratory_rate: number;
  consciousness: ConsciousnessLevel;
  triage_level: TriageLevel;
  contributing_factors: string[];
  recommended_action: string;
  triage_notes?: string | null;
  status: EmergencyCaseStatus;
  doctor_id?: number | null;
  nurse_id?: number | null;
  doctor_name?: string | null;
  nurse_name?: string | null;
  created_at: string;
  updated_at: string;
  disclaimer: string;
}

export interface EmergencyCaseCreatePayload {
  patient_id?: number;
  patient_name: string;
  age: number;
  gender: string;
  symptoms: string;
  injury_type?: string;
  heart_rate: number;
  bp_systolic: number;
  bp_diastolic: number;
  spo2: number;
  temperature: number;
  respiratory_rate: number;
  consciousness: ConsciousnessLevel;
  doctor_id?: number;
  nurse_id?: number;
}

export type BedStatus = "AVAILABLE" | "OCCUPIED" | "RESERVED" | "CLEANING" | "MAINTENANCE";
export type RoomType = "ICU" | "GENERAL_WARD" | "SEMI_PRIVATE" | "PRIVATE" | "ISOLATION";

export interface Bed {
  id: number;
  bed_number: string;
  ward_id: number;
  room_id?: number | null;
  status: BedStatus;
  has_oxygen_support: boolean;
  has_ventilator: boolean;
  ward_name?: string | null;
  room_number?: string | null;
  current_admission_id?: number | null;
  patient_name?: string | null;
  patient_mrn?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Ward {
  id: number;
  name: string;
  code: string;
  description?: string | null;
  floor: string;
  wing: string;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  occupancy_rate: number;
  is_active: boolean;
}

export interface BedDashboardStats {
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  reserved_beds: number;
  maintenance_beds: number;
  cleaning_beds: number;
  occupancy_rate: number;
  icu_occupancy_rate: number;
  wards: Ward[];
}

export type AdmissionStatus = "ADMITTED" | "TRANSFERRED" | "DISCHARGED";
export type DischargeCondition =
  | "RECOVERED"
  | "IMPROVED"
  | "STABLE"
  | "TRANSFERRED_EXTERNAL"
  | "AGAINST_MEDICAL_ADVICE"
  | "DECEASED";

export interface Admission {
  id: number;
  admission_number: string;
  patient_id: number;
  admitting_doctor_id: number;
  ward_id: number;
  bed_id: number;
  admission_date: string;
  discharge_date?: string | null;
  admission_reason: string;
  expected_stay_days: number;
  status: AdmissionStatus;
  emergency_case_id?: number | null;
  discharge_diagnosis?: string | null;
  discharge_summary?: string | null;
  discharge_condition?: DischargeCondition | null;
  discharge_medications: Array<{ name: string; dosage: string; duration: string }>;
  follow_up_instructions?: string | null;
  discharged_by_id?: number | null;
  patient_name: string;
  patient_mrn: string;
  doctor_name: string;
  ward_name: string;
  bed_number: string;
  discharged_by_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdmissionCreatePayload {
  patient_id: number;
  admitting_doctor_id: number;
  ward_id: number;
  bed_id: number;
  admission_reason: string;
  expected_stay_days?: number;
  emergency_case_id?: number;
}

export interface BedTransferPayload {
  to_bed_id: number;
  transfer_reason: string;
}

export interface DischargePayload {
  discharge_diagnosis: string;
  discharge_summary: string;
  discharge_condition: DischargeCondition;
  discharge_medications?: Array<{ name: string; dosage: string; duration: string }>;
  follow_up_instructions?: string;
}

export type ResourceAvailability = "AVAILABLE" | "BUSY" | "UNAVAILABLE";

export interface ResourceItem {
  name: string;
  resource_type: string;
  status: ResourceAvailability;
  current_capacity: number;
  total_capacity: number;
  utilization_percentage: number;
  details: string;
}

export interface ResourceCoordinationStatus {
  last_updated: string;
  overall_status: ResourceAvailability;
  resources: ResourceItem[];
  operational_recommendations: string[];
  disclaimer: string;
}
