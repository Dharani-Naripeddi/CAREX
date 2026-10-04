import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { billingApi, patientsApi, ipdApi } from "../services/api";
import {
  Invoice,
  InvoiceItem,
  Payment,
  BillingItem,
  BillingCategory,
  InvoicePaymentStatus,
  PaymentMethod,
  AdmissionDischargeBillingSummary,
  BillingDashboardStats,
} from "../types/support_services";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { useToast } from "../hooks/useToast";
import { useAuth } from "../hooks/useAuth";
import {
  CreditCard,
  Plus,
  Search,
  DollarSign,
  Printer,
  Calendar,
  Layers,
  Activity,
  Receipt,
  FileText,
  ShieldCheck,
  CheckCircle,
  Clock,
  AlertTriangle,
  Building,
  ArrowUpRight,
  TrendingUp,
  Percent,
} from "lucide-react";

export const BillingPage: React.FC = () => {
  const { user } = useAuth();
  const { success, error: toastError } = useToast();
  const queryClient = useQueryClient();

  const isBillingStaff = user?.role === "RECEPTIONIST" || user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN";

  // State
  const [activeTab, setActiveTab] = useState<"invoices" | "rate_sheet" | "discharge_estimator">("invoices");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Invoice Details / Print View Modal
  const [viewInvoice, setViewInvoice] = useState<Invoice | null>(null);

  // Payment Recording Modal
  const [paymentInvoice, setPaymentInvoice] = useState<Invoice | null>(null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("CARD");
  const [paymentRef, setPaymentRef] = useState("");
  const [paymentNotes, setPaymentNotes] = useState("");

  // New Invoice Builder Modal
  const [isNewInvoiceModalOpen, setIsNewInvoiceModalOpen] = useState(false);
  const [newInvPatientId, setNewInvPatientId] = useState("");
  const [newInvDueDate, setNewInvDueDate] = useState("");
  const [newInvNotes, setNewInvNotes] = useState("");
  const [newInvItems, setNewInvItems] = useState<
    {
      description: string;
      category: BillingCategory;
      quantity: number;
      unit_price: number;
      discount: number;
      tax_percent: number;
    }[]
  >([
    {
      description: "General Outpatient Consultation",
      category: "CONSULTATION",
      quantity: 1,
      unit_price: 50.0,
      discount: 0,
      tax_percent: 0,
    },
  ]);

  // Inpatient Discharge Estimator State
  const [selectedAdmissionId, setSelectedAdmissionId] = useState<string>("");

  // Queries
  const { data: stats } = useQuery<BillingDashboardStats>({
    queryKey: ["billingDashboardStats"],
    queryFn: billingApi.getDashboardStats,
    refetchInterval: 10000,
  });

  const { data: invoices, isLoading: invoicesLoading, isError, refetch } = useQuery<Invoice[]>({
    queryKey: ["billingInvoices", statusFilter],
    queryFn: () => billingApi.getInvoices({ status: statusFilter !== "ALL" ? statusFilter : undefined }),
    refetchInterval: 8000,
  });

  const { data: billingItems, isLoading: itemsLoading } = useQuery<BillingItem[]>({
    queryKey: ["billingItems"],
    queryFn: () => billingApi.getItems(),
  });

  const { data: patients } = useQuery({
    queryKey: ["patientsList"],
    queryFn: () => patientsApi.list(),
  });

  const { data: admissions } = useQuery({
    queryKey: ["activeAdmissions"],
    queryFn: () => ipdApi.listAdmissions({ status: "ADMITTED" }),
  });

  const { data: admissionSummary, isLoading: summaryLoading } = useQuery<AdmissionDischargeBillingSummary>({
    queryKey: ["admissionSummary", selectedAdmissionId],
    queryFn: () => billingApi.getAdmissionSummary(parseInt(selectedAdmissionId)),
    enabled: !!selectedAdmissionId,
  });

  // Mutations
  const recordPaymentMutation = useMutation({
    mutationFn: ({ invoiceId, payload }: { invoiceId: number; payload: any }) =>
      billingApi.recordPayment(invoiceId, payload),
    onSuccess: () => {
      success("Payment Processed", "Payment successfully posted to patient invoice.");
      setPaymentInvoice(null);
      setPaymentAmount("");
      setPaymentRef("");
      setPaymentNotes("");
      queryClient.invalidateQueries({ queryKey: ["billingInvoices"] });
      queryClient.invalidateQueries({ queryKey: ["billingDashboardStats"] });
    },
    onError: (err: any) => {
      toastError("Payment Failed", err.response?.data?.detail || "Could not process payment.");
    },
  });

  const createInvoiceMutation = useMutation({
    mutationFn: (payload: any) => billingApi.createInvoice(payload),
    onSuccess: () => {
      success("Invoice Created", "New clinical hospital bill generated and transmitted to patient account.");
      setIsNewInvoiceModalOpen(false);
      setNewInvPatientId("");
      setNewInvNotes("");
      setNewInvItems([
        {
          description: "General Outpatient Consultation",
          category: "CONSULTATION",
          quantity: 1,
          unit_price: 50.0,
          discount: 0,
          tax_percent: 0,
        },
      ]);
      queryClient.invalidateQueries({ queryKey: ["billingInvoices"] });
      queryClient.invalidateQueries({ queryKey: ["billingDashboardStats"] });
    },
    onError: (err: any) => {
      toastError("Creation Failed", err.response?.data?.detail || "Could not generate invoice.");
    },
  });

  const handlePrint = () => {
    window.print();
  };

  const handleAddItemRow = () => {
    setNewInvItems((prev) => [
      ...prev,
      {
        description: "",
        category: "OTHER",
        quantity: 1,
        unit_price: 0,
        discount: 0,
        tax_percent: 0,
      },
    ]);
  };

  const handleRemoveItemRow = (idx: number) => {
    setNewInvItems((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleItemFieldChange = (idx: number, field: string, val: any) => {
    setNewInvItems((prev) =>
      prev.map((item, i) => {
        if (i !== idx) return item;
        return { ...item, [field]: val };
      })
    );
  };

  const handleSelectPredefinedItem = (idx: number, billingItemIdStr: string) => {
    const bItem = billingItems?.find((b) => b.id === parseInt(billingItemIdStr));
    if (bItem) {
      setNewInvItems((prev) =>
        prev.map((item, i) => {
          if (i !== idx) return item;
          return {
            ...item,
            description: bItem.name,
            category: bItem.category,
            unit_price: bItem.unit_price,
            tax_percent: bItem.tax_percent,
          };
        })
      );
    }
  };

  // Filtered invoices
  const filteredInvoices = (invoices || []).filter((inv) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchNum = inv.invoice_number.toLowerCase().includes(q);
      const matchPat = inv.patient_name?.toLowerCase().includes(q) || inv.patient_mrn?.toLowerCase().includes(q);
      return matchNum || matchPat;
    }
    return true;
  });

  const getStatusBadge = (st: InvoicePaymentStatus) => {
    switch (st) {
      case "PAID":
        return <Badge variant="success">PAID IN FULL</Badge>;
      case "PARTIALLY_PAID":
        return <Badge variant="warning">PARTIALLY PAID</Badge>;
      case "UNPAID":
        return <Badge variant="critical">UNPAID / PENDING</Badge>;
      case "CANCELLED":
        return <Badge variant="outline">CANCELLED</Badge>;
    }
  };

  return (
    <PageContainer
      title="Billing & Revenue Cycle Management"
      subtitle="Universal hospital invoicing, itemized clinical charges, multi-channel payment reconciliation, and inpatient stay aggregators."
      badge={<Badge variant="info" dot>Revenue Engine Active</Badge>}
      actions={
        <div className="flex items-center gap-2.5">
          {isBillingStaff && (
            <Button
              variant="glow"
              size="sm"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setIsNewInvoiceModalOpen(true)}
            >
              Generate Patient Invoice
            </Button>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* KPI Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card className="p-3 bg-slate-900/60">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-slate-400">Today's Revenue</span>
              <DollarSign className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xl font-extrabold text-emerald-400 mt-1">
              ${stats?.today_revenue?.toFixed(2) || "0.00"}
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">{stats?.today_payments_count || 0} payments recorded</p>
          </Card>

          <Card className="p-3 bg-slate-900/60">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-slate-400">Monthly Revenue</span>
              <TrendingUp className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-xl font-extrabold text-sky-300 mt-1">
              ${stats?.month_revenue?.toFixed(2) || "0.00"}
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">Month to date collection</p>
          </Card>

          <Card className="p-3 bg-slate-900/60 border-amber-500/30">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-amber-400">Outstanding Invoices</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-xl font-extrabold text-amber-400 mt-1">
              {stats?.outstanding_bills_count || 0}
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">Unpaid or partial bills</p>
          </Card>

          <Card className="p-3 bg-slate-900/60 border-rose-500/30">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-rose-400">Unpaid Receivables</span>
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-xl font-extrabold text-rose-400 mt-1">
              ${stats?.total_unpaid_amount?.toFixed(2) || "0.00"}
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">Pending collection balance</p>
          </Card>
        </div>

        {/* Tab Strip */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveTab("invoices")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "invoices"
                  ? "bg-sky-500 text-white shadow-lg shadow-sky-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              All Invoices ({invoices?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("rate_sheet")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "rate_sheet"
                  ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Services Rate Sheet ({billingItems?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("discharge_estimator")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "discharge_estimator"
                  ? "bg-teal-500 text-white shadow-lg shadow-teal-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Inpatient Discharge Estimator
            </button>
          </div>

          {activeTab === "invoices" && (
            <div className="flex items-center gap-3">
              <div className="relative flex-1 sm:w-64">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search invoice #, patient, MRN..."
                  className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="UNPAID">Unpaid Only</option>
                <option value="PARTIALLY_PAID">Partially Paid</option>
                <option value="PAID">Paid in Full</option>
              </select>
            </div>
          )}
        </div>

        {/* Tab 1: Invoices List */}
        {activeTab === "invoices" && (
          <div className="space-y-3">
            {invoicesLoading ? (
              <div className="py-16 text-center">
                <LoadingSpinner size="lg" label="Loading invoices..." />
              </div>
            ) : isError ? (
              <ErrorState onRetry={() => refetch()} />
            ) : filteredInvoices.length === 0 ? (
              <Card className="p-12 text-center text-slate-400">
                <Receipt className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h4 className="font-bold text-white text-base">No Invoices Found</h4>
                <p className="text-xs mt-1">There are no billing records matching the selected criteria.</p>
              </Card>
            ) : (
              filteredInvoices.map((inv) => (
                <Card key={inv.id} hoverable className="p-4">
                  <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                    <div className="flex items-start gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-xs text-sky-400 shrink-0 mt-0.5">
                        <Receipt className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono font-bold text-xs text-white">{inv.invoice_number}</span>
                          {getStatusBadge(inv.payment_status)}
                          <span className="text-xs text-slate-400">
                            Date: {new Date(inv.date).toLocaleDateString()}
                          </span>
                        </div>

                        <div className="text-sm font-bold text-white">
                          Patient: {inv.patient_name} <span className="text-xs text-slate-400 font-mono">({inv.patient_mrn})</span>
                        </div>

                        <div className="flex items-center gap-4 text-xs text-slate-400 flex-wrap">
                          <span>Total: <strong className="text-white">${inv.total_amount.toFixed(2)}</strong></span>
                          <span>•</span>
                          <span>Paid: <strong className="text-emerald-400">${inv.paid_amount.toFixed(2)}</strong></span>
                          <span>•</span>
                          <span>Balance Due: <strong className={inv.balance_amount > 0 ? "text-rose-400" : "text-slate-400"}>${inv.balance_amount.toFixed(2)}</strong></span>
                        </div>

                        {inv.notes && (
                          <p className="text-[11px] text-slate-400 italic bg-slate-900/60 px-2.5 py-1 rounded-lg border border-slate-800/80">
                            {inv.notes}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 w-full lg:w-auto justify-end pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setViewInvoice(inv)}
                        leftIcon={<FileText className="w-3.5 h-3.5" />}
                      >
                        View & Print Bill
                      </Button>

                      {isBillingStaff && inv.balance_amount > 0 && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => {
                            setPaymentInvoice(inv);
                            setPaymentAmount(inv.balance_amount.toString());
                          }}
                          leftIcon={<CreditCard className="w-3.5 h-3.5" />}
                        >
                          Record Payment
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Tab 2: Services Rate Sheet */}
        {activeTab === "rate_sheet" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {itemsLoading ? (
                <div className="col-span-full py-16 text-center">
                  <LoadingSpinner size="lg" label="Loading charge master rate sheet..." />
                </div>
              ) : (
                billingItems?.map((item) => (
                  <Card key={item.id} hoverable className="p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge variant="outline" size="sm" className="mb-1 font-mono">
                          {item.code}
                        </Badge>
                        <h4 className="font-bold text-sm text-white">{item.name}</h4>
                        <p className="text-[11px] text-sky-400 font-medium">{item.category}</p>
                      </div>
                      <span className="text-base font-extrabold text-emerald-400 font-mono">
                        ${item.unit_price.toFixed(2)}
                      </span>
                    </div>

                    <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Tax Applicable: {item.tax_percent}%</span>
                      <span className="text-emerald-400 font-semibold">Active Charge Item</span>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Inpatient Stay Estimator */}
        {activeTab === "discharge_estimator" && (
          <div className="space-y-6">
            <Card className="p-4 bg-slate-900/60 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white">Select Inpatient Admission to Aggregate Charges</h3>
                  <p className="text-xs text-slate-400">Aggregates room stay duration, laboratory orders, dispensed medications, and clinical fees.</p>
                </div>
              </div>

              <div className="max-w-md">
                <select
                  value={selectedAdmissionId}
                  onChange={(e) => setSelectedAdmissionId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="">-- Choose Active Inpatient Admission --</option>
                  {admissions?.map((adm: any) => (
                    <option key={adm.id} value={adm.id}>
                      {adm.admission_number} — {adm.patient_name} [{adm.ward_name} / Bed {adm.bed_number}]
                    </option>
                  ))}
                </select>
              </div>
            </Card>

            {selectedAdmissionId && (
              summaryLoading ? (
                <div className="py-16 text-center">
                  <LoadingSpinner size="lg" label="Calculating inpatient aggregate charges..." />
                </div>
              ) : admissionSummary ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Summary Breakdown */}
                  <div className="lg:col-span-2 space-y-4">
                    <Card className="p-5 space-y-4">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <div>
                          <h4 className="font-bold text-base text-white">Stay Summary: {admissionSummary.patient_name}</h4>
                          <p className="text-xs text-slate-400">Admission #{admissionSummary.admission_number} • {admissionSummary.stay_days} Days Billed</p>
                        </div>
                        <span className="font-mono font-bold text-sm text-sky-400">
                          ${admissionSummary.daily_room_rate.toFixed(2)} / day
                        </span>
                      </div>

                      <div className="space-y-2 text-xs">
                        <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                          <span className="text-slate-300">Room & Bed Charges ({admissionSummary.stay_days} days × ${admissionSummary.daily_room_rate})</span>
                          <span className="font-mono font-bold text-white">${admissionSummary.room_charges_total.toFixed(2)}</span>
                        </div>

                        <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                          <span className="text-slate-300">Diagnostic Laboratory Charges</span>
                          <span className="font-mono font-bold text-white">${admissionSummary.lab_charges_total.toFixed(2)}</span>
                        </div>

                        <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                          <span className="text-slate-300">Pharmacy & Dispensed Medications</span>
                          <span className="font-mono font-bold text-white">${admissionSummary.pharmacy_charges_total.toFixed(2)}</span>
                        </div>

                        <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                          <span className="text-slate-300">Procedures & Attending Consultations</span>
                          <span className="font-mono font-bold text-white">${admissionSummary.procedure_charges_total.toFixed(2)}</span>
                        </div>
                      </div>
                    </Card>
                  </div>

                  {/* Total Card */}
                  <div>
                    <Card className="p-5 space-y-4 bg-gradient-to-br from-slate-900 to-slate-950 border-sky-500/30">
                      <h4 className="font-bold text-sm uppercase tracking-wider text-slate-400">Estimated Total Bill</h4>

                      <div className="space-y-2 text-xs pt-2 border-t border-slate-800">
                        <div className="flex items-center justify-between text-slate-400">
                          <span>Subtotal</span>
                          <span className="font-mono text-white">${admissionSummary.estimated_subtotal.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between text-slate-400">
                          <span>Applicable Tax</span>
                          <span className="font-mono text-white">${admissionSummary.estimated_tax.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between text-base font-extrabold text-white pt-2 border-t border-slate-800">
                          <span>Estimated Net Total</span>
                          <span className="text-emerald-400 font-mono">${admissionSummary.estimated_total.toFixed(2)}</span>
                        </div>
                      </div>

                      <Button
                        variant="glow"
                        className="w-full"
                        onClick={() => {
                          setNewInvPatientId(admissionSummary.patient_id.toString());
                          setNewInvItems([
                            {
                              description: `Inpatient Stay Room Charges (${admissionSummary.stay_days} Days)`,
                              category: "ROOM",
                              quantity: admissionSummary.stay_days,
                              unit_price: admissionSummary.daily_room_rate,
                              discount: 0,
                              tax_percent: 5.0,
                            },
                            {
                              description: "Inpatient Clinical Laboratory Diagnostic Panel",
                              category: "LAB",
                              quantity: 1,
                              unit_price: admissionSummary.lab_charges_total || 55.0,
                              discount: 0,
                              tax_percent: 0,
                            },
                            {
                              description: "Inpatient Pharmacy Medications Dispensed",
                              category: "MEDICINE",
                              quantity: 1,
                              unit_price: admissionSummary.pharmacy_charges_total || 48.0,
                              discount: 0,
                              tax_percent: 0,
                            },
                          ]);
                          setIsNewInvoiceModalOpen(true);
                        }}
                      >
                        Convert to Official Discharge Invoice
                      </Button>
                    </Card>
                  </div>
                </div>
              ) : null
            )}
          </div>
        )}

        {/* Modal 1: Printable Official Invoice View */}
        {viewInvoice && (
          <Modal
            isOpen={!!viewInvoice}
            onClose={() => setViewInvoice(null)}
            title={`Hospital Clinical Invoice — ${viewInvoice.invoice_number}`}
            maxWidth="xl"
          >
            <div className="space-y-6">
              <div id="printable-invoice" className="p-6 bg-slate-900/90 rounded-2xl border border-slate-800 text-white space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center font-mono font-black text-white text-lg">
                      CX
                    </div>
                    <div>
                      <h2 className="font-extrabold text-base tracking-wider text-white">CAREX METROPOLITAN HOSPITAL</h2>
                      <p className="text-[11px] text-slate-400">Department of Patient Accounts & Financial Services • Tax ID: CX-9842-881</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest block">INVOICE NUMBER</span>
                    <span className="font-mono font-bold text-sm text-sky-400">{viewInvoice.invoice_number}</span>
                  </div>
                </div>

                {/* Patient & Billing Metadata */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Billed To (Patient)</span>
                    <span className="font-extrabold text-white text-sm">{viewInvoice.patient_name}</span>
                    <span className="text-[11px] text-slate-400 block">MRN: {viewInvoice.patient_mrn}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Billing Date</span>
                    <span className="font-mono text-slate-300">{new Date(viewInvoice.date).toLocaleDateString()}</span>
                    <span className="text-[11px] text-slate-400 block">Due: {viewInvoice.due_date ? new Date(viewInvoice.due_date).toLocaleDateString() : "Due upon receipt"}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Payment Status</span>
                    {getStatusBadge(viewInvoice.payment_status)}
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Generated By</span>
                    <span className="font-bold text-white">{viewInvoice.created_by_name || "Cashier Desk"}</span>
                  </div>
                </div>

                {/* Itemized Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border border-slate-800">
                    <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold">
                      <tr>
                        <th className="p-3">Category</th>
                        <th className="p-3">Service / Item Description</th>
                        <th className="p-3 text-center">Qty</th>
                        <th className="p-3 text-right">Unit Price</th>
                        <th className="p-3 text-right">Tax (%)</th>
                        <th className="p-3 text-right">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {viewInvoice.items.map((item, idx) => (
                        <tr key={idx}>
                          <td className="p-3">
                            <Badge variant="outline" size="sm">{item.category}</Badge>
                          </td>
                          <td className="p-3 font-semibold text-white">{item.description}</td>
                          <td className="p-3 text-center font-mono">{item.quantity}</td>
                          <td className="p-3 text-right font-mono">${item.unit_price.toFixed(2)}</td>
                          <td className="p-3 text-right font-mono text-slate-400">{item.tax_percent}%</td>
                          <td className="p-3 text-right font-mono font-bold text-white">${item.total_price.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Totals Summary */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-4 border-t border-slate-800">
                  <div className="text-xs text-slate-400 max-w-sm">
                    {viewInvoice.notes && <p className="italic">Note: {viewInvoice.notes}</p>}
                    <p className="mt-1 text-[11px] text-slate-500">Thank you for choosing CAREX Metropolitan Hospital for your healthcare needs.</p>
                  </div>

                  <div className="w-full sm:w-64 space-y-2 text-xs bg-slate-950 p-4 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between text-slate-400">
                      <span>Subtotal</span>
                      <span className="font-mono text-white">${viewInvoice.subtotal.toFixed(2)}</span>
                    </div>
                    {viewInvoice.discount_amount > 0 && (
                      <div className="flex items-center justify-between text-emerald-400">
                        <span>Discount Applied</span>
                        <span className="font-mono">-${viewInvoice.discount_amount.toFixed(2)}</span>
                      </div>
                    )}
                    {viewInvoice.tax_amount > 0 && (
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Tax</span>
                        <span className="font-mono text-white">+${viewInvoice.tax_amount.toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between text-sm font-extrabold text-white pt-2 border-t border-slate-800">
                      <span>Grand Total</span>
                      <span className="font-mono">${viewInvoice.total_amount.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-emerald-400 pt-1">
                      <span>Paid to Date</span>
                      <span className="font-mono font-bold">-${viewInvoice.paid_amount.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm font-black text-rose-400 pt-2 border-t border-slate-800">
                      <span>Balance Outstanding</span>
                      <span className="font-mono">${viewInvoice.balance_amount.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* Payment History */}
                {viewInvoice.payments && viewInvoice.payments.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-slate-800">
                    <h5 className="font-bold text-xs uppercase tracking-wider text-slate-400">Settlement / Payment Ledger</h5>
                    <div className="space-y-1.5 text-xs">
                      {viewInvoice.payments.map((p) => (
                        <div key={p.id} className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800">
                          <span className="font-mono text-sky-400">{p.payment_number} — {p.payment_method} ({p.reference_number || "Direct Deposit"})</span>
                          <span className="font-mono font-bold text-emerald-400">+${p.amount.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between gap-3 pt-2">
                <Button variant="outline" size="sm" onClick={() => setViewInvoice(null)}>
                  Close
                </Button>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handlePrint}
                  leftIcon={<Printer className="w-4 h-4" />}
                >
                  Print Official Invoice
                </Button>
              </div>
            </div>
          </Modal>
        )}

        {/* Modal 2: Record Payment */}
        {paymentInvoice && (
          <Modal
            isOpen={!!paymentInvoice}
            onClose={() => setPaymentInvoice(null)}
            title={`Record Payment — ${paymentInvoice.invoice_number}`}
            maxWidth="md"
          >
            <form
              onSubmit={(e) => {
                e.preventDefault();
                recordPaymentMutation.mutate({
                  invoiceId: paymentInvoice.id,
                  payload: {
                    amount: parseFloat(paymentAmount),
                    payment_method: paymentMethod,
                    reference_number: paymentRef,
                    notes: paymentNotes,
                  },
                });
              }}
              className="space-y-4"
            >
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-400 block">Patient</span>
                  <span className="font-bold text-white">{paymentInvoice.patient_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Outstanding Balance</span>
                  <span className="font-mono font-bold text-rose-400 text-sm">
                    ${paymentInvoice.balance_amount.toFixed(2)}
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Payment Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  min={0.01}
                  max={paymentInvoice.balance_amount}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono font-bold"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Payment Method</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="CARD">Credit / Debit Card</option>
                  <option value="UPI">UPI / Digital QR</option>
                  <option value="CASH">Cash at Counter</option>
                  <option value="OTHER">Insurance / Wire Transfer</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Transaction Reference Number</label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                  placeholder="e.g. TXN-VISA-8821 or UPI-REF-9923"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Cashier Notes</label>
                <input
                  type="text"
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  placeholder="Settlement receipt notes..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setPaymentInvoice(null)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={recordPaymentMutation.isPending}>
                  Post Payment & Issue Receipt
                </Button>
              </div>
            </form>
          </Modal>
        )}

        {/* Modal 3: New Invoice Builder */}
        {isNewInvoiceModalOpen && (
          <Modal
            isOpen={isNewInvoiceModalOpen}
            onClose={() => setIsNewInvoiceModalOpen(false)}
            title="Generate Clinical Hospital Bill"
            maxWidth="lg"
          >
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createInvoiceMutation.mutate({
                  patient_id: parseInt(newInvPatientId),
                  due_date: newInvDueDate || undefined,
                  notes: newInvNotes,
                  items: newInvItems,
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Patient</label>
                <select
                  required
                  value={newInvPatientId}
                  onChange={(e) => setNewInvPatientId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="">-- Choose Patient --</option>
                  {patients?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} ({p.mrn}) — {p.gender}, {p.age} yrs
                    </option>
                  ))}
                </select>
              </div>

              {/* Items List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Line Items</h4>
                  <Button variant="outline" size="sm" type="button" onClick={handleAddItemRow} leftIcon={<Plus className="w-3.5 h-3.5" />}>
                    Add Item
                  </Button>
                </div>

                <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                  {newInvItems.map((item, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                      <div className="grid grid-cols-12 gap-2">
                        <div className="col-span-5">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Predefined Item</label>
                          <select
                            onChange={(e) => handleSelectPredefinedItem(idx, e.target.value)}
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none"
                          >
                            <option value="">-- Select or Type Custom --</option>
                            {billingItems?.map((b) => (
                              <option key={b.id} value={b.id}>
                                {b.name} (${b.unit_price})
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="col-span-7">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Description</label>
                          <input
                            type="text"
                            required
                            value={item.description}
                            onChange={(e) => handleItemFieldChange(idx, "description", e.target.value)}
                            placeholder="Item description"
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-12 gap-2 items-center">
                        <div className="col-span-3">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Category</label>
                          <select
                            value={item.category}
                            onChange={(e) => handleItemFieldChange(idx, "category", e.target.value)}
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none"
                          >
                            <option value="CONSULTATION">Consultation</option>
                            <option value="ROOM">Room</option>
                            <option value="LAB">Lab</option>
                            <option value="MEDICINE">Medicine</option>
                            <option value="PROCEDURE">Procedure</option>
                            <option value="OTHER">Other</option>
                          </select>
                        </div>

                        <div className="col-span-2">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Qty</label>
                          <input
                            type="number"
                            min={1}
                            value={item.quantity}
                            onChange={(e) => handleItemFieldChange(idx, "quantity", parseFloat(e.target.value) || 1)}
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none font-mono"
                          />
                        </div>

                        <div className="col-span-3">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Unit Price ($)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={item.unit_price}
                            onChange={(e) => handleItemFieldChange(idx, "unit_price", parseFloat(e.target.value) || 0)}
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none font-mono"
                          />
                        </div>

                        <div className="col-span-2">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Tax (%)</label>
                          <input
                            type="number"
                            step="0.5"
                            value={item.tax_percent}
                            onChange={(e) => handleItemFieldChange(idx, "tax_percent", parseFloat(e.target.value) || 0)}
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none font-mono"
                          />
                        </div>

                        <div className="col-span-2 text-right pt-4">
                          {newInvItems.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveItemRow(idx)}
                              className="text-xs text-rose-400 hover:text-rose-300 font-bold"
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Notes / Billing Instructions</label>
                <input
                  type="text"
                  value={newInvNotes}
                  onChange={(e) => setNewInvNotes(e.target.value)}
                  placeholder="e.g. Interim outpatient visit billing..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setIsNewInvoiceModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={createInvoiceMutation.isPending}>
                  Create Invoice
                </Button>
              </div>
            </form>
          </Modal>
        )}
      </div>
    </PageContainer>
  );
};
