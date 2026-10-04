import axios, { AxiosError } from "axios";
import { LoginResponse, UserProfile } from "../types/auth";
import { AdminDashboardStats, RoleDashboardData } from "../types/dashboard";
import {
  Patient,
  PatientCreatePayload,
  DoctorWithUser,
  NurseWithUser,
  Appointment,
  AppointmentCreatePayload,
  AppointmentStatus,
  OpdToken,
  TokenQueueStatus,
  PatientLiveTokenStatus,
} from "../types/clinical";
import {
  EmergencyCase,
  EmergencyCaseCreatePayload,
  EmergencyCaseStatus,
  TriageLevel,
  Bed,
  Ward,
  BedDashboardStats,
  BedStatus,
  Admission,
  AdmissionCreatePayload,
  AdmissionStatus,
  BedTransferPayload,
  DischargePayload,
  ResourceCoordinationStatus,
} from "../types/emergency_ipd";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Request Interceptor: Attach JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("carex_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Unauthorized/Expired tokens
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const isLoginRequest = error.config?.url?.includes("/auth/login");
      if (!isLoginRequest) {
        localStorage.removeItem("carex_token");
        localStorage.removeItem("carex_user");
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth Endpoints
export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>("/auth/login", { email, password });
    return response.data;
  },

  getMe: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>("/auth/me");
    return response.data;
  },

  logout: async (): Promise<void> => {
    try {
      await api.post("/auth/logout");
    } finally {
      localStorage.removeItem("carex_token");
      localStorage.removeItem("carex_user");
    }
  },
};

// Patient Endpoints
export const patientsApi = {
  list: async (params?: { query?: string; gender?: string; blood_group?: string }): Promise<Patient[]> => {
    const response = await api.get<Patient[]>("/patients/", { params });
    return response.data;
  },

  getById: async (id: number): Promise<Patient> => {
    const response = await api.get<Patient>(`/patients/${id}`);
    return response.data;
  },

  create: async (data: PatientCreatePayload): Promise<Patient> => {
    const response = await api.post<Patient>("/patients/", data);
    return response.data;
  },

  update: async (id: number, data: Partial<PatientCreatePayload>): Promise<Patient> => {
    const response = await api.put<Patient>(`/patients/${id}`, data);
    return response.data;
  },
};

// Doctor Endpoints
export const doctorsApi = {
  list: async (params?: { department_id?: number; is_available?: boolean }): Promise<DoctorWithUser[]> => {
    const response = await api.get<DoctorWithUser[]>("/doctors/", { params });
    return response.data;
  },

  getById: async (userId: number): Promise<DoctorWithUser> => {
    const response = await api.get<DoctorWithUser>(`/doctors/${userId}`);
    return response.data;
  },

  create: async (data: any): Promise<DoctorWithUser> => {
    const response = await api.post<DoctorWithUser>("/doctors/", data);
    return response.data;
  },

  update: async (userId: number, data: any): Promise<any> => {
    const response = await api.put(`/doctors/${userId}`, data);
    return response.data;
  },
};

// Nurse Endpoints
export const nursesApi = {
  list: async (params?: { department_id?: number; is_on_duty?: boolean }): Promise<NurseWithUser[]> => {
    const response = await api.get<NurseWithUser[]>("/nurses/", { params });
    return response.data;
  },

  update: async (userId: number, data: any): Promise<any> => {
    const response = await api.put(`/nurses/${userId}`, data);
    return response.data;
  },
};

// Department Endpoints
export const departmentsApi = {
  list: async (): Promise<{ id: number; name: string; code: string; description?: string }[]> => {
    const response = await api.get("/departments/");
    return response.data;
  },
};

// Appointment Endpoints
export const appointmentsApi = {
  list: async (params?: {
    patient_id?: number;
    doctor_id?: number;
    department_id?: number;
    date?: string;
    status?: AppointmentStatus;
  }): Promise<Appointment[]> => {
    const response = await api.get<Appointment[]>("/appointments/", { params });
    return response.data;
  },

  create: async (data: AppointmentCreatePayload): Promise<Appointment> => {
    const response = await api.post<Appointment>("/appointments/", data);
    return response.data;
  },

  updateStatus: async (
    id: number,
    status: AppointmentStatus,
    options?: { cancellation_reason?: string; notes?: string }
  ): Promise<Appointment> => {
    const response = await api.put<Appointment>(`/appointments/${id}/status`, {
      status,
      ...options,
    });
    return response.data;
  },

  reschedule: async (id: number, data: { appointment_date: string; appointment_time: string; notes?: string }): Promise<Appointment> => {
    const response = await api.put<Appointment>(`/appointments/${id}/reschedule`, data);
    return response.data;
  },
};

// Token Endpoints
export const tokensApi = {
  generate: async (data: {
    patient_id: number;
    department_id: number;
    doctor_id?: number;
    appointment_id?: number;
    priority?: string;
  }): Promise<OpdToken> => {
    const response = await api.post<OpdToken>("/tokens/generate", data);
    return response.data;
  },

  getQueue: async (params?: { department_id?: number; doctor_id?: number }): Promise<TokenQueueStatus> => {
    const response = await api.get<TokenQueueStatus>("/tokens/queue", { params });
    return response.data;
  },

  getPatientStatus: async (patientId: number): Promise<PatientLiveTokenStatus> => {
    const response = await api.get<PatientLiveTokenStatus>(`/tokens/patient/${patientId}/status`);
    return response.data;
  },

  call: async (tokenId: number): Promise<OpdToken> => {
    const response = await api.put<OpdToken>(`/tokens/${tokenId}/call`);
    return response.data;
  },

  complete: async (tokenId: number): Promise<OpdToken> => {
    const response = await api.put<OpdToken>(`/tokens/${tokenId}/complete`);
    return response.data;
  },
};

// Emergency Endpoints
export const emergencyApi = {
  list: async (params?: { status?: EmergencyCaseStatus; triage_level?: TriageLevel }): Promise<EmergencyCase[]> => {
    const response = await api.get<EmergencyCase[]>("/emergency/", { params });
    return response.data;
  },

  getById: async (id: number): Promise<EmergencyCase> => {
    const response = await api.get<EmergencyCase>(`/emergency/${id}`);
    return response.data;
  },

  create: async (data: EmergencyCaseCreatePayload): Promise<EmergencyCase> => {
    const response = await api.post<EmergencyCase>("/emergency/", data);
    return response.data;
  },

  update: async (id: number, data: any): Promise<EmergencyCase> => {
    const response = await api.put<EmergencyCase>(`/emergency/${id}`, data);
    return response.data;
  },
};

// Bed & Ward Endpoints
export const bedsApi = {
  getDashboard: async (): Promise<BedDashboardStats> => {
    const response = await api.get<BedDashboardStats>("/beds/dashboard");
    return response.data;
  },

  listWards: async (): Promise<Ward[]> => {
    const response = await api.get<Ward[]>("/beds/wards");
    return response.data;
  },

  listBeds: async (params?: { ward_id?: number; status?: BedStatus }): Promise<Bed[]> => {
    const response = await api.get<Bed[]>("/beds/", { params });
    return response.data;
  },

  updateStatus: async (bedId: number, status: BedStatus): Promise<Bed> => {
    const response = await api.put<Bed>(`/beds/${bedId}/status`, { status });
    return response.data;
  },
};

// Inpatient (IPD) Admissions Endpoints
export const ipdApi = {
  listAdmissions: async (params?: { status?: AdmissionStatus; ward_id?: number; patient_id?: number }): Promise<Admission[]> => {
    const response = await api.get<Admission[]>("/ipd/admissions", { params });
    return response.data;
  },

  admit: async (data: AdmissionCreatePayload): Promise<Admission> => {
    const response = await api.post<Admission>("/ipd/admissions", data);
    return response.data;
  },

  transfer: async (admissionId: number, data: BedTransferPayload): Promise<any> => {
    const response = await api.post(`/ipd/admissions/${admissionId}/transfer`, data);
    return response.data;
  },

  discharge: async (admissionId: number, data: DischargePayload): Promise<Admission> => {
    const response = await api.post<Admission>(`/ipd/admissions/${admissionId}/discharge`, data);
    return response.data;
  },
};

// Resource Coordination Endpoints
export const resourcesApi = {
  getCoordination: async (): Promise<ResourceCoordinationStatus> => {
    const response = await api.get<ResourceCoordinationStatus>("/resources/coordination");
    return response.data;
  },
};

// Dashboard Endpoints
export const dashboardApi = {
  getAdminStats: async (): Promise<AdminDashboardStats> => {
    const response = await api.get<AdminDashboardStats>("/dashboard/admin");
    return response.data;
  },

  getRoleStats: async (roleName: string): Promise<RoleDashboardData> => {
    const response = await api.get<RoleDashboardData>(`/dashboard/role/${roleName}`);
    return response.data;
  },
};

// Phase 4: Laboratory Management Endpoints
export const labApi = {
  getTests: async (params?: { category?: string; active_only?: boolean }) => {
    const response = await api.get("/lab/tests", { params });
    return response.data;
  },

  createTest: async (data: any) => {
    const response = await api.post("/lab/tests", data);
    return response.data;
  },

  getOrders: async (params?: { status?: string; priority?: string; patient_id?: number; doctor_id?: number }) => {
    const response = await api.get("/lab/orders", { params });
    return response.data;
  },

  getOrderById: async (orderId: number) => {
    const response = await api.get(`/lab/orders/${orderId}`);
    return response.data;
  },

  createOrder: async (data: any) => {
    const response = await api.post("/lab/orders", data);
    return response.data;
  },

  collectSample: async (orderId: number) => {
    const response = await api.post(`/lab/orders/${orderId}/collect-sample`);
    return response.data;
  },

  startTest: async (orderId: number) => {
    const response = await api.post(`/lab/orders/${orderId}/start-test`);
    return response.data;
  },

  enterResults: async (orderId: number, data: any) => {
    const response = await api.post(`/lab/orders/${orderId}/results`, data);
    return response.data;
  },

  verifyReport: async (orderId: number, data?: { clinical_impression?: string; conclusion?: string }) => {
    const response = await api.post(`/lab/orders/${orderId}/verify`, null, { params: data });
    return response.data;
  },

  getReports: async (params?: { patient_id?: number; doctor_id?: number }) => {
    const response = await api.get("/lab/reports", { params });
    return response.data;
  },

  getWorkloadSummary: async () => {
    const response = await api.get("/lab/workload-summary");
    return response.data;
  },
};

// Phase 4: Pharmacy Management Endpoints
export const pharmacyApi = {
  getMedicines: async (params?: { category?: string; query?: string; low_stock_only?: boolean }) => {
    const response = await api.get("/pharmacy/medicines", { params });
    return response.data;
  },

  createMedicine: async (data: any) => {
    const response = await api.post("/pharmacy/medicines", data);
    return response.data;
  },

  addBatch: async (data: any) => {
    const response = await api.post("/pharmacy/batches", data);
    return response.data;
  },

  getExpiryAnalysis: async () => {
    const response = await api.get("/pharmacy/expiry");
    return response.data;
  },

  getLowStockAlerts: async () => {
    const response = await api.get("/pharmacy/low-stock");
    return response.data;
  },

  getTransactions: async (params?: { medicine_id?: number; transaction_type?: string }) => {
    const response = await api.get("/pharmacy/transactions", { params });
    return response.data;
  },

  getPrescriptions: async (params?: { status?: string; patient_id?: number; doctor_id?: number }) => {
    const response = await api.get("/pharmacy/prescriptions", { params });
    return response.data;
  },

  createPrescription: async (data: any) => {
    const response = await api.post("/pharmacy/prescriptions", data);
    return response.data;
  },

  dispense: async (data: any) => {
    const response = await api.post("/pharmacy/dispense", data);
    return response.data;
  },

  getDashboardStats: async () => {
    const response = await api.get("/pharmacy/dashboard-stats");
    return response.data;
  },
};

// Phase 4: Billing Management Endpoints
export const billingApi = {
  getItems: async (params?: { category?: string; active_only?: boolean }) => {
    const response = await api.get("/billing/items", { params });
    return response.data;
  },

  createItem: async (data: any) => {
    const response = await api.post("/billing/items", data);
    return response.data;
  },

  getInvoices: async (params?: { status?: string; patient_id?: number }) => {
    const response = await api.get("/billing/invoices", { params });
    return response.data;
  },

  getInvoiceById: async (id: number) => {
    const response = await api.get(`/billing/invoices/${id}`);
    return response.data;
  },

  createInvoice: async (data: any) => {
    const response = await api.post("/billing/invoices", data);
    return response.data;
  },

  recordPayment: async (invoiceId: number, data: any) => {
    const response = await api.post(`/billing/invoices/${invoiceId}/payments`, data);
    return response.data;
  },

  getAdmissionSummary: async (admissionId: number) => {
    const response = await api.get(`/billing/admissions/${admissionId}/summary`);
    return response.data;
  },

  getDashboardStats: async () => {
    const response = await api.get("/billing/dashboard-stats");
    return response.data;
  },
};

// Phase 4: Notifications System Endpoints
export const notificationsApi = {
  list: async (params?: { unread_only?: boolean; limit?: number }) => {
    const response = await api.get("/notifications/", { params });
    return response.data;
  },

  getUnreadCount: async () => {
    const response = await api.get("/notifications/unread-count");
    return response.data;
  },

  markAsRead: async (id: number) => {
    const response = await api.post(`/notifications/${id}/read`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await api.post("/notifications/read-all");
    return response.data;
  },
};

// Phase 5: AI Intelligence Layer Endpoints
export const aiApi = {
  getInsights: async (params?: { status?: string; severity?: string; limit?: number }) => {
    const response = await api.get("/ai/insights", { params });
    return response.data;
  },

  predictQueue: async (data: { department_id?: number; doctor_id?: number }) => {
    const response = await api.post("/ai/queue/predict", data);
    return response.data;
  },

  predictBeds: async (data: { ward_id?: number }) => {
    const response = await api.post("/ai/beds/predict", data);
    return response.data;
  },

  predictPharmacy: async (data: { medicine_id?: number; days_history?: number }) => {
    const response = await api.post("/ai/pharmacy/predict", data);
    return response.data;
  },

  assessTriage: async (data: any, case_id?: number) => {
    const response = await api.post("/ai/triage/assess", data, { params: { case_id } });
    return response.data;
  },

  analyzeDocument: async (data: { file_name: string; file_type?: string; patient_id?: number; document_type?: string; raw_text?: string }) => {
    const response = await api.post("/ai/documents/analyze", data);
    return response.data;
  },

  verifyDocument: async (documentId: number) => {
    const response = await api.post(`/ai/documents/${documentId}/verify`);
    return response.data;
  },

  transcribeVoice: async (data: { audio_text?: string; patient_id?: number; use_demo_sample?: boolean }) => {
    const response = await api.post("/ai/voice/transcribe", data);
    return response.data;
  },

  generateHandover: async (data: { ward_id?: number; shift_name?: string; to_nurse_id?: number }) => {
    const response = await api.post("/ai/handover/generate", data);
    return response.data;
  },

  approveHandover: async (handoverId: number, data?: { important_observations?: string; next_shift_checklist?: string[]; to_nurse_id?: number }) => {
    const response = await api.post(`/ai/handover/${handoverId}/approve`, data);
    return response.data;
  },

  detectAnomalies: async (data: { domain?: string }) => {
    const response = await api.post("/ai/anomalies/detect", data);
    return response.data;
  },

  getAlerts: async (params?: { status?: string; severity?: string; limit?: number }) => {
    const response = await api.get("/ai/alerts", { params });
    return response.data;
  },

  acknowledgeAlert: async (alertId: number) => {
    const response = await api.post(`/ai/alerts/${alertId}/acknowledge`);
    return response.data;
  },

  resolveAlert: async (alertId: number) => {
    const response = await api.post(`/ai/alerts/${alertId}/resolve`);
    return response.data;
  },

  getPredictions: async (params?: { prediction_type?: string; limit?: number }) => {
    const response = await api.get("/ai/predictions", { params });
    return response.data;
  },

  submitFeedback: async (data: { rating: string; notes?: string; prediction_id?: number; alert_id?: number }) => {
    const response = await api.post("/ai/feedback", data);
    return response.data;
  },

  triggerSimulation: async (data: { scenario_type: string }) => {
    const response = await api.post("/ai/simulation/trigger", data);
    return response.data;
  },
};

// Phase 6: Hospital Brain Central Intelligence Endpoints
export const hospitalBrainApi = {
  getOverview: async () => {
    const response = await api.get("/hospital-brain/overview");
    return response.data;
  },

  getEvents: async (params?: { status?: string; severity?: string; limit?: number }) => {
    const response = await api.get("/hospital-brain/events", { params });
    return response.data;
  },

  getActiveEvents: async (limit?: number) => {
    const response = await api.get("/hospital-brain/events/active", { params: { limit } });
    return response.data;
  },

  getEventById: async (eventId: number) => {
    const response = await api.get(`/hospital-brain/events/${eventId}`);
    return response.data;
  },

  acknowledgeEvent: async (eventId: number) => {
    const response = await api.post(`/hospital-brain/events/${eventId}/acknowledge`);
    return response.data;
  },

  resolveEvent: async (eventId: number) => {
    const response = await api.post(`/hospital-brain/events/${eventId}/resolve`);
    return response.data;
  },

  getDepartments: async () => {
    const response = await api.get("/hospital-brain/departments");
    return response.data;
  },

  getCapacity: async () => {
    const response = await api.get("/hospital-brain/capacity");
    return response.data;
  },

  getActions: async () => {
    const response = await api.get("/hospital-brain/actions");
    return response.data;
  },

  runSimulation: async (data: {
    emergency_arrival_delta_pct?: number;
    icu_occupancy_delta_pct?: number;
    opd_demand_delta_pct?: number;
    ward_discharge_rate_delta_pct?: number;
  }) => {
    const response = await api.post("/hospital-brain/simulation", data);
    return response.data;
  },
};

// Phase 7: SIH Demo Mode & End-to-End Patient Journey Endpoints
export const demoApi = {
  getScenarios: async () => {
    const response = await api.get("/demo/scenarios");
    return response.data;
  },

  launchScenario: async (scenario_code: string) => {
    const response = await api.post("/demo/launch", { scenario_code });
    return response.data;
  },

  resetDemo: async () => {
    const response = await api.post("/demo/reset");
    return response.data;
  },

  getPipelineProgress: async () => {
    const response = await api.get("/demo/pipeline-progress");
    return response.data;
  },

  getOverview: async () => {
    const response = await api.get("/demo/overview");
    return response.data;
  },
};

export const patientJourneyApi = {
  getJourney: async (patientId: number) => {
    const response = await api.get(`/patients/${patientId}/journey`);
    return response.data;
  },
};

// System Health
export const healthApi = {
  check: async () => {
    const response = await api.get("/health/");
    return response.data;
  },
};
