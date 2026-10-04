export interface KPIItem {
  id: string;
  title: string;
  value: string;
  numeric_value: number;
  change_percentage: number;
  is_positive: boolean;
  status: "normal" | "warning" | "critical" | "info";
  subtext: string;
  icon_name: string;
}

export interface TrendPoint {
  time: string;
  opd_admissions: number;
  emergency_cases: number;
  discharges: number;
}

export interface DepartmentOccupancy {
  department: string;
  occupied_beds: number;
  total_beds: number;
  occupancy_rate: number;
  status: "normal" | "warning" | "critical";
}

export interface TriagePatient {
  id: string;
  patient_name: string;
  age: number;
  gender: string;
  chief_complaint: string;
  priority: "P1_CRITICAL" | "P2_URGENT" | "P3_NON_URGENT";
  wait_time_minutes: number;
  assigned_doctor?: string | null;
  department: string;
}

export interface RecentActivity {
  id: number;
  timestamp: string;
  user_name: string;
  role: string;
  action: string;
  details: string;
  category: "ADMISSION" | "PRESCRIPTION" | "LAB" | "DISCHARGE" | "SYSTEM";
}

export interface AdminDashboardStats {
  hospital_name: string;
  last_updated: string;
  kpis: KPIItem[];
  weekly_trends: TrendPoint[];
  department_occupancy: DepartmentOccupancy[];
  triage_queue: TriagePatient[];
  recent_activities: RecentActivity[];
}

export interface QuickActionItem {
  title: string;
  action: string;
  icon: string;
  color: string;
}

export interface RecentRecordItem {
  id: string;
  title: string;
  status: string;
  time: string;
  meta: string;
}

export interface RoleDashboardData {
  role: string;
  title: string;
  description: string;
  stats: KPIItem[];
  quick_actions: QuickActionItem[];
  recent_records: RecentRecordItem[];
}
