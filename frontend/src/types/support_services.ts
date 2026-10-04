// Laboratory Types
export type LabOrderStatus = "PENDING" | "SAMPLE_COLLECTED" | "IN_PROGRESS" | "COMPLETED" | "VERIFIED" | "CANCELLED";
export type LabOrderPriority = "NORMAL" | "URGENT" | "STAT";
export type LabResultFlag = "NORMAL" | "LOW" | "HIGH" | "CRITICAL";
export type LabReportStatus = "DRAFT" | "RELEASED" | "ARCHIVED";

export interface LabTestParameterDef {
  name: string;
  unit?: string;
  min_val?: number;
  max_val?: number;
  critical_low?: number;
  critical_high?: number;
  text_range?: string;
}

export interface LabTest {
  id: number;
  code: string;
  name: string;
  category: string;
  department_id?: number;
  description?: string;
  sample_type: string;
  normal_range?: string;
  unit?: string;
  price: number;
  is_active: boolean;
  parameters: LabTestParameterDef[];
}

export interface LabResultParameter {
  id: number;
  parameter_name: string;
  result_value: string;
  numeric_value?: number;
  unit?: string;
  reference_range?: string;
  flag: LabResultFlag;
  is_critical: boolean;
}

export interface LabResult {
  id: number;
  order_id: number;
  patient_id: number;
  technician_id: number;
  technician_name?: string;
  result_summary?: string;
  technician_notes?: string;
  is_abnormal: boolean;
  is_critical: boolean;
  created_at: string;
  parameters: LabResultParameter[];
}

export interface LabReport {
  id: number;
  report_number: string;
  order_id: number;
  lab_result_id: number;
  patient_id: number;
  patient_name?: string;
  patient_mrn?: string;
  patient_age?: number;
  patient_gender?: string;
  doctor_id: number;
  doctor_name?: string;
  technician_id: number;
  technician_name?: string;
  verified_by_id?: number;
  verified_by_name?: string;
  report_date: string;
  status: LabReportStatus;
  test_name?: string;
  test_code?: string;
  sample_type?: string;
  clinical_impression?: string;
  conclusion?: string;
  print_html?: string;
  parameters: LabResultParameter[];
}

export interface LabOrder {
  id: number;
  order_number: string;
  patient_id: number;
  patient_name?: string;
  patient_mrn?: string;
  patient_gender?: string;
  patient_age?: number;
  doctor_id: number;
  doctor_name?: string;
  test_id: number;
  test_name?: string;
  test_code?: string;
  test_category?: string;
  test_price?: number;
  admission_id?: number;
  emergency_case_id?: number;
  priority: LabOrderPriority;
  status: LabOrderStatus;
  clinical_notes?: string;
  sample_type?: string;
  order_date: string;
  sample_collected_at?: string;
  completed_at?: string;
  verified_at?: string;
  test?: LabTest;
  result?: LabResult;
  report_id?: number;
  report_number?: string;
}

export interface LabOrderCreatePayload {
  patient_id: number;
  test_id: number;
  priority?: LabOrderPriority;
  clinical_notes?: string;
  sample_type?: string;
  admission_id?: number;
  emergency_case_id?: number;
}

export interface LabResultEntryPayload {
  result_summary?: string;
  technician_notes?: string;
  parameters: {
    parameter_name: string;
    result_value: string;
    numeric_value?: number;
    unit?: string;
    reference_range?: string;
    flag?: LabResultFlag;
    is_critical?: boolean;
  }[];
}

export interface LabWorkloadSummary {
  pending_count: number;
  sample_collected_count: number;
  in_progress_count: number;
  completed_count: number;
  verified_count: number;
  urgent_pending_count: number;
  today_total_orders: number;
}

// Pharmacy Types
export type PharmacyTransactionType = "PURCHASE" | "DISPENSE" | "ADJUSTMENT" | "RETURN" | "EXPIRED" | "DAMAGED";
export type PrescriptionStatus = "PENDING" | "PARTIALLY_DISPENSED" | "DISPENSED" | "CANCELLED";
export type PrescriptionItemStatus = "PENDING" | "PARTIALLY_DISPENSED" | "DISPENSED" | "OUT_OF_STOCK";

export interface MedicineBatch {
  id: number;
  medicine_id: number;
  batch_number: string;
  quantity: number;
  initial_quantity: number;
  purchase_price: number;
  selling_price: number;
  manufacturing_date?: string;
  expiry_date: string;
  days_to_expiry?: number;
  expiry_status?: string;
  risk_level?: string;
  supplier?: string;
  storage_location?: string;
  is_active: boolean;
}

export interface Medicine {
  id: number;
  code: string;
  name: string;
  generic_name: string;
  category: string;
  manufacturer?: string;
  unit: string;
  reorder_level: number;
  max_stock_level: number;
  unit_price: number;
  is_active: boolean;
  total_stock: number;
  batches_count: number;
  is_low_stock: boolean;
  suggested_reorder_qty: number;
  batches: MedicineBatch[];
}

export interface MedicineCreatePayload {
  code: string;
  name: string;
  generic_name: string;
  category: string;
  manufacturer?: string;
  unit?: string;
  reorder_level?: number;
  max_stock_level?: number;
  unit_price?: number;
  is_active?: boolean;
}

export interface MedicineBatchCreatePayload {
  medicine_id: number;
  batch_number: string;
  quantity: number;
  purchase_price: number;
  selling_price: number;
  manufacturing_date?: string;
  expiry_date: string;
  supplier?: string;
  storage_location?: string;
}

export interface PharmacyTransaction {
  id: number;
  transaction_number: string;
  medicine_id: number;
  medicine_name?: string;
  medicine_code?: string;
  batch_id?: number;
  batch_number?: string;
  transaction_type: PharmacyTransactionType;
  quantity: number;
  unit_price: number;
  total_amount: number;
  reference_type?: string;
  reference_id?: string;
  notes?: string;
  performed_by_id?: number;
  performed_by_name?: string;
  created_at: string;
}

export interface PrescriptionItem {
  id: number;
  prescription_id: number;
  medicine_id: number;
  medicine_name?: string;
  medicine_code?: string;
  medicine_unit?: string;
  unit_price?: number;
  available_stock?: number;
  dosage: string;
  frequency: string;
  duration: string;
  quantity_prescribed: number;
  quantity_dispensed: number;
  instructions?: string;
  status: PrescriptionItemStatus;
}

export interface Prescription {
  id: number;
  prescription_number: string;
  patient_id: number;
  patient_name?: string;
  patient_mrn?: string;
  doctor_id: number;
  doctor_name?: string;
  appointment_id?: number;
  admission_id?: number;
  emergency_case_id?: number;
  diagnosis?: string;
  notes?: string;
  status: PrescriptionStatus;
  created_at: string;
  items: PrescriptionItem[];
}

export interface PrescriptionCreatePayload {
  patient_id: number;
  appointment_id?: number;
  admission_id?: number;
  emergency_case_id?: number;
  diagnosis?: string;
  notes?: string;
  items: {
    medicine_id: number;
    dosage: string;
    frequency: string;
    duration: string;
    quantity_prescribed: number;
    instructions?: string;
  }[];
}

export interface DispensePayload {
  prescription_id: number;
  items: {
    prescription_item_id: number;
    batch_id: number;
    quantity: number;
  }[];
  notes?: string;
}

export interface Dispensing {
  id: number;
  dispensing_number: string;
  prescription_id: number;
  prescription_number?: string;
  patient_id: number;
  patient_name?: string;
  pharmacist_id: number;
  pharmacist_name?: string;
  total_amount: number;
  notes?: string;
  created_at: string;
}

export interface ExpiryClassificationItem {
  medicine_id: number;
  medicine_name: string;
  medicine_code: string;
  batch_id: number;
  batch_number: string;
  quantity: number;
  expiry_date: string;
  days_remaining: number;
  category: string;
  risk_level: string;
}

export interface LowStockAlertItem {
  medicine_id: number;
  medicine_name: string;
  medicine_code: string;
  category: string;
  current_stock: number;
  reorder_level: number;
  max_stock_level: number;
  suggested_reorder_qty: number;
  unit: string;
}

export interface PharmacyDashboardStats {
  total_medicines: number;
  total_stock_units: number;
  low_stock_count: number;
  expiring_soon_count: number;
  expired_count: number;
  today_dispensed_count: number;
  today_dispensed_amount: number;
}

// Billing Types
export type BillingCategory = "CONSULTATION" | "ROOM" | "LAB" | "MEDICINE" | "PROCEDURE" | "OTHER";
export type InvoicePaymentStatus = "UNPAID" | "PARTIALLY_PAID" | "PAID" | "CANCELLED";
export type PaymentMethod = "CASH" | "CARD" | "UPI" | "OTHER";

export interface BillingItem {
  id: number;
  code: string;
  name: string;
  category: BillingCategory;
  unit_price: number;
  tax_percent: number;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export interface InvoiceItem {
  id: number;
  invoice_id: number;
  billing_item_id?: number;
  description: string;
  category: BillingCategory;
  quantity: number;
  unit_price: number;
  discount: number;
  tax_percent: number;
  total_price: number;
  reference_type?: string;
  reference_id?: string;
}

export interface Payment {
  id: number;
  payment_number: string;
  invoice_id: number;
  patient_id: number;
  patient_name?: string;
  amount: number;
  payment_method: PaymentMethod;
  reference_number?: string;
  notes?: string;
  payment_date: string;
  recorded_by_id?: number;
  recorded_by_name?: string;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  patient_id: number;
  patient_name?: string;
  patient_mrn?: string;
  patient_phone?: string;
  patient_email?: string;
  patient_address?: string;
  appointment_id?: number;
  admission_id?: number;
  emergency_case_id?: number;
  date: string;
  due_date?: string;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  balance_amount: number;
  payment_status: InvoicePaymentStatus;
  notes?: string;
  created_by_id?: number;
  created_by_name?: string;
  created_at: string;
  items: InvoiceItem[];
  payments: Payment[];
}

export interface InvoiceCreatePayload {
  patient_id: number;
  appointment_id?: number;
  admission_id?: number;
  emergency_case_id?: number;
  due_date?: string;
  notes?: string;
  items: {
    billing_item_id?: number;
    description: string;
    category: BillingCategory;
    quantity: number;
    unit_price: number;
    discount?: number;
    tax_percent?: number;
    reference_type?: string;
    reference_id?: string;
  }[];
}

export interface PaymentCreatePayload {
  amount: number;
  payment_method: PaymentMethod;
  reference_number?: string;
  notes?: string;
}

export interface AdmissionDischargeBillingSummary {
  admission_id: number;
  admission_number: string;
  patient_id: number;
  patient_name: string;
  stay_days: number;
  daily_room_rate: number;
  room_charges_total: number;
  lab_charges_total: number;
  pharmacy_charges_total: number;
  procedure_charges_total: number;
  other_charges_total: number;
  estimated_subtotal: number;
  estimated_tax: number;
  estimated_total: number;
  existing_invoices_count: number;
  unpaid_balance: number;
}

export interface BillingDashboardStats {
  today_revenue: number;
  month_revenue: number;
  outstanding_bills_count: number;
  total_unpaid_amount: number;
  today_invoices_count: number;
  today_payments_count: number;
}

// Notification Types
export type NotificationType = "INFO" | "SUCCESS" | "WARNING" | "CRITICAL" | "ALERT";
export type NotificationPriority = "LOW" | "NORMAL" | "HIGH" | "URGENT";

export interface AppNotification {
  id: number;
  user_id?: number;
  role_target?: string;
  type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  related_entity?: string;
  related_entity_id?: string;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCountResponse {
  unread_count: number;
  critical_unread_count: number;
}
