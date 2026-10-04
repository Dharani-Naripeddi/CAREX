export interface Patient {
  id: number;
  mrn: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email?: string | null;
  phone: string;
  date_of_birth: string;
  age: number;
  gender: "Male" | "Female" | "Other" | string;
  blood_group?: string | null;
  address?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact_relation?: string | null;
  allergies: string[];
  current_medications: string[];
  medical_history: string[];
  user_id?: number | null;
  registered_by_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface PatientCreatePayload {
  first_name: string;
  last_name: string;
  email?: string;
  phone: string;
  date_of_birth: string;
  gender: string;
  blood_group?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relation?: string;
  allergies?: string[];
  current_medications?: string[];
  medical_history?: string[];
}

export interface DoctorWithUser {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  avatar_url?: string | null;
  specialization: string;
  qualification: string;
  experience_years: number;
  consultation_fee: number;
  room_number?: string | null;
  availability_days: string[];
  available_from: string;
  available_to: string;
  is_available: boolean;
  department_id?: number | null;
  department_name?: string | null;
}

export interface NurseWithUser {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  avatar_url?: string | null;
  qualification: string;
  shift: "MORNING" | "EVENING" | "NIGHT" | "ROTATING";
  ward_assigned?: string | null;
  is_on_duty: boolean;
  department_id?: number | null;
  department_name?: string | null;
}

export type AppointmentStatus =
  | "SCHEDULED"
  | "CHECKED_IN"
  | "WAITING"
  | "IN_CONSULTATION"
  | "COMPLETED"
  | "CANCELLED"
  | "NO_SHOW";

export type AppointmentType = "OPD" | "EMERGENCY" | "FOLLOW_UP" | "ROUTINE_CHECKUP";

export interface Appointment {
  id: number;
  appointment_number: string;
  patient_id: number;
  doctor_id: number;
  department_id: number;
  appointment_date: string;
  appointment_time: string;
  type: AppointmentType;
  status: AppointmentStatus;
  chief_complaint?: string | null;
  notes?: string | null;
  cancellation_reason?: string | null;
  patient_name: string;
  patient_mrn: string;
  patient_phone: string;
  doctor_name: string;
  doctor_specialization?: string | null;
  department_name: string;
  created_at: string;
  updated_at: string;
}

export interface AppointmentCreatePayload {
  patient_id: number;
  doctor_id: number;
  department_id: number;
  appointment_date: string;
  appointment_time: string;
  type?: AppointmentType;
  chief_complaint?: string;
  notes?: string;
}

export type TokenStatus = "ISSUED" | "CALLED" | "IN_ROOM" | "SERVICED" | "SKIPPED" | "CANCELLED";
export type TokenPriority = "NORMAL" | "URGENT" | "STAT";

export interface OpdToken {
  id: number;
  token_number: number;
  token_code: string;
  date: string;
  patient_id: number;
  doctor_id?: number | null;
  department_id: number;
  appointment_id?: number | null;
  priority: TokenPriority;
  status: TokenStatus;
  estimated_wait_minutes: number;
  called_at?: string | null;
  serviced_at?: string | null;
  created_at: string;
  patient_name: string;
  patient_mrn: string;
  doctor_name?: string | null;
  department_name: string;
}

export interface TokenQueueStatus {
  department_name: string;
  doctor_name?: string | null;
  current_token_code?: string | null;
  current_token_number?: number | null;
  total_in_queue: number;
  waiting_tokens: OpdToken[];
}

export interface PatientLiveTokenStatus {
  has_active_token: boolean;
  token?: OpdToken | null;
  current_serving_token_code?: string | null;
  patients_ahead: number;
  estimated_wait_minutes: number;
}
