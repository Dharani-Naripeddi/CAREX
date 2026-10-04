import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { labApi, patientsApi } from "../services/api";
import {
  LabOrder,
  LabTest,
  LabReport,
  LabOrderPriority,
  LabOrderStatus,
  LabResultFlag,
  LabResultEntryPayload,
} from "../types/support_services";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Modal } from "../components/ui/Modal";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { useToast } from "../hooks/useToast";
import { useAuth } from "../hooks/useAuth";
import {
  FlaskConical,
  Plus,
  Search,
  Filter,
  CheckCircle,
  Clock,
  AlertTriangle,
  FileText,
  Printer,
  ChevronRight,
  ShieldCheck,
  UserCheck,
  Building,
  Calendar,
  Layers,
  Activity,
  Droplet,
  Send,
  User,
  UserPlus,
} from "lucide-react";

export const LaboratoryPage: React.FC = () => {
  const { user } = useAuth();
  const { success, error: toastError } = useToast();
  const queryClient = useQueryClient();

  const isLabTech = user?.role === "LAB_TECHNICIAN" || user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN";
  const isDoctor = user?.role === "DOCTOR" || user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN";

  // State
  const [activeTab, setActiveTab] = useState<"orders" | "pending_collection" | "in_progress" | "completed" | "verified" | "catalogue">("orders");
  const [searchQuery, setSearchQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [selectedOrder, setSelectedOrder] = useState<LabOrder | null>(null);
  const [viewReportModal, setViewReportModal] = useState<LabOrder | null>(null);
  const [isResultModalOpen, setIsResultModalOpen] = useState(false);
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);

  // Result entry form state
  const [resultSummary, setResultSummary] = useState("");
  const [technicianNotes, setTechnicianNotes] = useState("");
  const [parameterValues, setParameterValues] = useState<Record<string, { val: string; num?: number; flag?: LabResultFlag }>>({});

  // New Lab Order form state
  const [orderMode, setOrderMode] = useState<"EXISTING_PATIENT" | "NEW_PATIENT">("EXISTING_PATIENT");
  const [orderPatientSearch, setOrderPatientSearch] = useState("");
  const [orderPatientId, setOrderPatientId] = useState<string>("");
  const [orderTestId, setOrderTestId] = useState<string>("");
  const [orderPriority, setOrderPriority] = useState<LabOrderPriority>("NORMAL");
  const [orderNotes, setOrderNotes] = useState("");

  // Direct patient intake state
  const [newPatientFirst, setNewPatientFirst] = useState("");
  const [newPatientLast, setNewPatientLast] = useState("");
  const [newPatientPhone, setNewPatientPhone] = useState("");
  const [newPatientDob, setNewPatientDob] = useState("1990-01-01");
  const [newPatientGender, setNewPatientGender] = useState("Male");
  const [newPatientBlood, setNewPatientBlood] = useState("O+");
  const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);

  // Queries
  const { data: workload, refetch: refetchWorkload } = useQuery({
    queryKey: ["labWorkload"],
    queryFn: labApi.getWorkloadSummary,
    refetchInterval: 4000,
  });

  const { data: tests, isLoading: testsLoading } = useQuery<LabTest[]>({
    queryKey: ["labTests"],
    queryFn: () => labApi.getTests(),
  });

  const { data: orders, isLoading: ordersLoading, isError, refetch: refetchOrders } = useQuery<LabOrder[]>({
    queryKey: ["labOrders", priorityFilter],
    queryFn: () => labApi.getOrders({ priority: priorityFilter !== "ALL" ? priorityFilter : undefined }),
    refetchInterval: 4000,
  });

  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(),
  });

  // Mutations
  const collectSampleMutation = useMutation({
    mutationFn: (orderId: number) => labApi.collectSample(orderId),
    onSuccess: () => {
      success("Sample Accessioned", "Specimen collected and assigned to laboratory worklist.");
      queryClient.invalidateQueries({ queryKey: ["labOrders"] });
      queryClient.invalidateQueries({ queryKey: ["labWorkload"] });
      refetchOrders();
      refetchWorkload();
    },
    onError: (err: any) => {
      toastError("Action Failed", err.response?.data?.detail || "Could not collect sample.");
    },
  });

  const startTestMutation = useMutation({
    mutationFn: (orderId: number) => labApi.startTest(orderId),
    onSuccess: () => {
      success("Test Started", "Order transitioned to In-Progress bench processing.");
      queryClient.invalidateQueries({ queryKey: ["labOrders"] });
      queryClient.invalidateQueries({ queryKey: ["labWorkload"] });
      refetchOrders();
      refetchWorkload();
    },
  });

  const enterResultsMutation = useMutation({
    mutationFn: ({ orderId, payload }: { orderId: number; payload: LabResultEntryPayload }) =>
      labApi.enterResults(orderId, payload),
    onSuccess: () => {
      success("Results Entered", "Diagnostic results recorded and flags calculated. Order is now Ready for Review.");
      setIsResultModalOpen(false);
      setSelectedOrder(null);
      queryClient.invalidateQueries({ queryKey: ["labOrders"] });
      queryClient.invalidateQueries({ queryKey: ["labWorkload"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      refetchOrders();
      refetchWorkload();
    },
    onError: (err: any) => {
      toastError("Error", err.response?.data?.detail || "Could not save results.");
    },
  });

  const verifyReportMutation = useMutation({
    mutationFn: (orderId: number) => labApi.verifyReport(orderId),
    onSuccess: () => {
      success("Report Verified & Released", "Diagnostic report released to attending physician and patient.");
      setViewReportModal(null);
      queryClient.invalidateQueries({ queryKey: ["labOrders"] });
      queryClient.invalidateQueries({ queryKey: ["labWorkload"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      refetchOrders();
      refetchWorkload();
    },
  });

  const handleOpenOrderModal = () => {
    setIsOrderModalOpen(true);
    if (patients && patients.length > 0 && !orderPatientId) {
      setOrderPatientId(patients[0].id.toString());
    }
    if (tests && tests.length > 0 && !orderTestId) {
      setOrderTestId(tests[0].id.toString());
    }
  };

  const handleOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const testIdNum = parseInt(orderTestId);
    if (!testIdNum) {
      toastError("Validation Error", "Please select a diagnostic laboratory test.");
      return;
    }

    setIsSubmittingOrder(true);
    try {
      let targetPatientId = parseInt(orderPatientId);

      if (orderMode === "NEW_PATIENT") {
        const fName = newPatientFirst.trim();
        const lName = newPatientLast.trim();
        const phone = newPatientPhone.trim();

        if (!fName || !/^[a-zA-Z\s\-']{2,50}$/.test(fName)) {
          toastError("Validation Error", "Patient First Name must contain alphabets only (2-50 characters).");
          setIsSubmittingOrder(false);
          return;
        }
        if (!lName || !/^[a-zA-Z\s\-']{2,50}$/.test(lName)) {
          toastError("Validation Error", "Patient Last Name must contain alphabets only (2-50 characters).");
          setIsSubmittingOrder(false);
          return;
        }
        if (!/^\d{10}$/.test(phone)) {
          toastError("Validation Error", "Patient Mobile Number must be numbers only and exactly 10 digits.");
          setIsSubmittingOrder(false);
          return;
        }

        const createdPatient = await patientsApi.create({
          first_name: fName,
          last_name: lName,
          phone: phone,
          date_of_birth: newPatientDob,
          gender: newPatientGender,
          blood_group: newPatientBlood,
          email: `${fName.toLowerCase()}.${lName.toLowerCase()}@example.com`,
        });

        targetPatientId = createdPatient.id;
        queryClient.invalidateQueries({ queryKey: ["patients"] });
        success("Patient Registered", `${createdPatient.full_name} (${createdPatient.mrn}) created in MPI.`);
      }

      if (!targetPatientId) {
        toastError("Validation Error", "Please choose an existing patient or fill in new patient details.");
        setIsSubmittingOrder(false);
        return;
      }

      await labApi.createOrder({
        patient_id: targetPatientId,
        test_id: testIdNum,
        priority: orderPriority,
        clinical_notes: orderNotes,
      });

      success("Lab Order Placed", "New diagnostic laboratory order transmitted to pathology queue.");
      setIsOrderModalOpen(false);
      setOrderNotes("");
      setOrderPatientId("");
      setNewPatientFirst("");
      setNewPatientLast("");
      setNewPatientPhone("");
      queryClient.invalidateQueries({ queryKey: ["labOrders"] });
      queryClient.invalidateQueries({ queryKey: ["labWorkload"] });
      refetchOrders();
      refetchWorkload();
    } catch (err: any) {
      toastError("Order Failed", err.response?.data?.detail || "Could not place lab order.");
    } finally {
      setIsSubmittingOrder(false);
    }
  };

  const handleOpenResultEntry = (order: LabOrder) => {
    setSelectedOrder(order);
    setResultSummary(order.result?.result_summary || "");
    setTechnicianNotes(order.result?.technician_notes || "");

    const initialParamVals: Record<string, { val: string; num?: number; flag?: LabResultFlag }> = {};
    const currentTest = tests?.find((t) => t.id === order.test_id);
    if (order.result?.parameters && order.result.parameters.length > 0) {
      order.result.parameters.forEach((p) => {
        initialParamVals[p.parameter_name] = {
          val: p.result_value,
          num: p.numeric_value,
          flag: p.flag,
        };
      });
    } else if (currentTest?.parameters) {
      currentTest.parameters.forEach((p: any) => {
        initialParamVals[p.name] = { val: "", num: undefined, flag: "NORMAL" };
      });
    }
    setParameterValues(initialParamVals);
    setIsResultModalOpen(true);
  };

  const handleParamValueChange = (paramName: string, val: string, paramDef?: any) => {
    const numericVal = parseFloat(val);
    const isNum = !isNaN(numericVal);

    let flag: LabResultFlag = "NORMAL";
    if (isNum && paramDef) {
      if (paramDef.critical_low !== undefined && numericVal < paramDef.critical_low) flag = "CRITICAL";
      else if (paramDef.critical_high !== undefined && numericVal > paramDef.critical_high) flag = "CRITICAL";
      else if (paramDef.min_val !== undefined && numericVal < paramDef.min_val) flag = "LOW";
      else if (paramDef.max_val !== undefined && numericVal > paramDef.max_val) flag = "HIGH";
    }

    setParameterValues((prev) => ({
      ...prev,
      [paramName]: {
        val,
        num: isNum ? numericVal : undefined,
        flag,
      },
    }));
  };

  const handleSubmitResults = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;

    const paramsPayload = Object.entries(parameterValues).map(([pName, data]) => ({
      parameter_name: pName,
      result_value: data.val || "0",
      numeric_value: data.num,
      flag: data.flag || "NORMAL",
      is_critical: data.flag === "CRITICAL",
    }));

    enterResultsMutation.mutate({
      orderId: selectedOrder.id,
      payload: {
        result_summary: resultSummary,
        technician_notes: technicianNotes,
        parameters: paramsPayload,
      },
    });
  };

  const handlePrintReport = () => {
    window.print();
  };

  // Filtered orders
  const filteredOrders = (orders || []).filter((o) => {
    // Tab filter
    if (activeTab === "pending_collection" && o.status !== "PENDING") return false;
    if (activeTab === "in_progress" && o.status !== "IN_PROGRESS" && o.status !== "SAMPLE_COLLECTED") return false;
    if (activeTab === "completed" && o.status !== "COMPLETED") return false;
    if (activeTab === "verified" && o.status !== "VERIFIED") return false;

    // Search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchNum = o.order_number.toLowerCase().includes(q);
      const matchPat = o.patient_name?.toLowerCase().includes(q) || o.patient_mrn?.toLowerCase().includes(q);
      const matchTest = o.test_name?.toLowerCase().includes(q) || o.test_code?.toLowerCase().includes(q);
      if (!matchNum && !matchPat && !matchTest) return false;
    }

    return true;
  });

  const getPriorityBadge = (prio: LabOrderPriority) => {
    switch (prio) {
      case "STAT":
        return <Badge variant="critical" className="animate-pulse">STAT Resuscitation</Badge>;
      case "URGENT":
        return <Badge variant="warning">Urgent</Badge>;
      default:
        return <Badge variant="info">Routine</Badge>;
    }
  };

  const getStatusBadge = (st: LabOrderStatus) => {
    switch (st) {
      case "PENDING":
        return <Badge variant="outline">Pending Sample</Badge>;
      case "SAMPLE_COLLECTED":
        return <Badge variant="info">Sample Collected</Badge>;
      case "IN_PROGRESS":
        return <Badge variant="warning">In Progress</Badge>;
      case "COMPLETED":
        return <Badge variant="info" className="bg-teal-500/20 text-teal-300 border-teal-500/30">Ready for Review</Badge>;
      case "VERIFIED":
        return <Badge variant="success">Verified & Released</Badge>;
      case "CANCELLED":
        return <Badge variant="critical">Cancelled</Badge>;
    }
  };

  const getFlagBadge = (flag: LabResultFlag) => {
    switch (flag) {
      case "CRITICAL":
        return <Badge variant="critical">CRITICAL</Badge>;
      case "HIGH":
        return <Badge variant="warning">HIGH</Badge>;
      case "LOW":
        return <Badge variant="info">LOW</Badge>;
      default:
        return <Badge variant="success">NORMAL</Badge>;
    }
  };

  return (
    <PageContainer
      title="Diagnostic Laboratory & Pathology"
      subtitle="Specimen collection, structured multi-parameter analysis, automated reference ranges, and verified diagnostic reports."
      badge={<Badge variant="info" dot>Central Diagnostics Unit</Badge>}
      actions={
        <div className="flex items-center gap-2.5">
          {isDoctor && (
            <Button
              variant="glow"
              size="sm"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={handleOpenOrderModal}
            >
              Order Lab Test
            </Button>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* KPI Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <Card
            hoverable
            onClick={() => { setActiveTab("orders"); setPriorityFilter("ALL"); }}
            className={`p-3 cursor-pointer transition-all ${
              activeTab === "orders" && priorityFilter === "ALL" ? "bg-slate-800/90 ring-1 ring-sky-400" : "bg-slate-900/60"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-slate-400">Total Orders</span>
              <FlaskConical className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-xl font-extrabold text-white mt-1">{workload?.today_total_orders || orders?.length || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Orders logged</p>
          </Card>

          <Card
            hoverable
            onClick={() => { setActiveTab("orders"); setPriorityFilter("STAT"); }}
            className={`p-3 cursor-pointer transition-all border-rose-500/30 ${
              priorityFilter === "STAT" ? "bg-rose-950/40 ring-1 ring-rose-500" : "bg-slate-900/60"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-rose-400">STAT / Urgent</span>
              <AlertTriangle className="w-4 h-4 text-rose-400 animate-pulse" />
            </div>
            <div className="text-xl font-extrabold text-rose-400 mt-1">{workload?.urgent_pending_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">High priority</p>
          </Card>

          <Card
            hoverable
            onClick={() => setActiveTab("pending_collection")}
            className={`p-3 cursor-pointer transition-all ${
              activeTab === "pending_collection" ? "bg-slate-800/90 ring-1 ring-amber-400" : "bg-slate-900/60"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-amber-400">Pending Sample</span>
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-xl font-extrabold text-white mt-1">{workload?.pending_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Awaiting collection</p>
          </Card>

          <Card
            hoverable
            onClick={() => setActiveTab("in_progress")}
            className={`p-3 cursor-pointer transition-all ${
              activeTab === "in_progress" ? "bg-slate-800/90 ring-1 ring-indigo-400" : "bg-slate-900/60"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-indigo-400">In Progress</span>
              <Activity className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-xl font-extrabold text-white mt-1">{workload?.in_progress_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Bench analyzers</p>
          </Card>

          <Card
            hoverable
            onClick={() => setActiveTab("completed")}
            className={`p-3 cursor-pointer transition-all ${
              activeTab === "completed" ? "bg-slate-800/90 ring-1 ring-teal-400" : "bg-slate-900/60"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-teal-400">Completed</span>
              <CheckCircle className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-xl font-extrabold text-teal-300 mt-1">{workload?.completed_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Ready for review</p>
          </Card>

          <Card
            hoverable
            onClick={() => setActiveTab("verified")}
            className={`p-3 cursor-pointer transition-all ${
              activeTab === "verified" ? "bg-slate-800/90 ring-1 ring-emerald-400" : "bg-slate-900/60"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-emerald-400">Verified</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xl font-extrabold text-emerald-400 mt-1">{workload?.verified_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Released reports</p>
          </Card>
        </div>

        {/* Tab Navigation & Search */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveTab("orders")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "orders"
                  ? "bg-sky-500 text-white shadow-lg shadow-sky-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              All Orders ({orders?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("pending_collection")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "pending_collection"
                  ? "bg-amber-500 text-white shadow-lg shadow-amber-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Sample Collection ({workload?.pending_count || 0})
            </button>
            <button
              onClick={() => setActiveTab("in_progress")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "in_progress"
                  ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              In Progress ({workload?.in_progress_count || 0})
            </button>
            <button
              onClick={() => setActiveTab("completed")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "completed"
                  ? "bg-teal-500 text-white shadow-lg shadow-teal-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Ready for Review ({workload?.completed_count || 0})
            </button>
            <button
              onClick={() => setActiveTab("verified")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "verified"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Released Reports ({workload?.verified_count || 0})
            </button>
            <button
              onClick={() => setActiveTab("catalogue")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "catalogue"
                  ? "bg-sky-600 text-white shadow-lg shadow-sky-600/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Test Catalogue ({tests?.length || 0})
            </button>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative flex-1 sm:w-64">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search order #, patient, test..."
                className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>

            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="STAT">STAT Only</option>
              <option value="URGENT">Urgent Only</option>
              <option value="NORMAL">Normal</option>
            </select>
          </div>
        </div>

        {/* Main Content Area */}
        {activeTab === "catalogue" ? (
          /* Catalogue View */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {testsLoading ? (
              <div className="col-span-full py-16 text-center">
                <LoadingSpinner size="lg" label="Loading test directory..." />
              </div>
            ) : (
              tests?.map((t) => (
                <Card key={t.id} hoverable className="p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <Badge variant="outline" size="sm" className="mb-1 font-mono">
                        {t.code}
                      </Badge>
                      <h4 className="font-bold text-sm text-white">{t.name}</h4>
                      <p className="text-[11px] text-sky-400 font-medium">{t.category}</p>
                    </div>
                    <span className="text-base font-extrabold text-emerald-400 font-mono">${t.price.toFixed(2)}</span>
                  </div>

                  <p className="text-xs text-slate-400 line-clamp-2">{t.description || "Routine diagnostic evaluation panel."}</p>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Droplet className="w-3.5 h-3.5 text-rose-400" />
                      {t.sample_type}
                    </span>
                    <span>{t.parameters?.length || 1} parameter(s)</span>
                  </div>
                </Card>
              ))
            )}
          </div>
        ) : (
          /* Orders List View */
          <div className="space-y-3">
            {ordersLoading ? (
              <div className="py-16 text-center">
                <LoadingSpinner size="lg" label="Accessing laboratory worklist..." />
              </div>
            ) : isError ? (
              <ErrorState onRetry={() => refetchOrders()} />
            ) : filteredOrders.length === 0 ? (
              <Card className="p-12 text-center text-slate-400">
                <FlaskConical className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h4 className="font-bold text-white text-base">No Laboratory Orders Found</h4>
                <p className="text-xs mt-1">There are no orders matching the selected filter criteria.</p>
              </Card>
            ) : (
              filteredOrders.map((o) => (
                <Card key={o.id} hoverable className="p-4 transition-all">
                  <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                    {/* Left: Order Info & Patient */}
                    <div className="flex items-start gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-xs text-sky-400 shrink-0 mt-0.5">
                        <FlaskConical className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono font-bold text-xs text-white">{o.order_number}</span>
                          {getPriorityBadge(o.priority)}
                          {getStatusBadge(o.status)}
                          {o.result?.is_critical && (
                            <Badge variant="critical">CRITICAL RESULTS</Badge>
                          )}
                        </div>

                        <div className="text-sm font-bold text-slate-200">
                          {o.test_name?.includes(`(${o.test_code})`) ? o.test_name : `${o.test_name} (${o.test_code})`}
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
                          <span>Patient: <strong className="text-white">{o.patient_name}</strong> ({o.patient_mrn})</span>
                          <span>•</span>
                          <span>Doctor: {o.doctor_name?.startsWith("Dr.") ? o.doctor_name : `Dr. ${o.doctor_name}`}</span>
                          <span>•</span>
                          <span>Specimen: {o.sample_type || "Blood"}</span>
                        </div>

                        {o.clinical_notes && (
                          <p className="text-[11px] text-slate-400 italic bg-slate-900/60 px-2.5 py-1 rounded-lg border border-slate-800/80">
                            Notes: {o.clinical_notes}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center gap-2 w-full lg:w-auto justify-end pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                      {isLabTech && o.status === "PENDING" && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => collectSampleMutation.mutate(o.id)}
                          isLoading={collectSampleMutation.isPending}
                          leftIcon={<Droplet className="w-3.5 h-3.5" />}
                        >
                          Collect Sample
                        </Button>
                      )}

                      {isLabTech && o.status === "SAMPLE_COLLECTED" && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => startTestMutation.mutate(o.id)}
                          leftIcon={<Activity className="w-3.5 h-3.5" />}
                        >
                          Start Test
                        </Button>
                      )}

                      {isLabTech && o.status === "IN_PROGRESS" && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => handleOpenResultEntry(o)}
                          leftIcon={<CheckCircle className="w-3.5 h-3.5" />}
                        >
                          Enter Results
                        </Button>
                      )}

                      {o.status === "COMPLETED" && (
                        <div className="flex items-center gap-2">
                          {isLabTech && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenResultEntry(o)}
                            >
                              Edit Results
                            </Button>
                          )}
                          <Button
                            variant="glow"
                            size="sm"
                            onClick={() => setViewReportModal(o)}
                            leftIcon={<ShieldCheck className="w-3.5 h-3.5" />}
                          >
                            Review & Verify Report
                          </Button>
                        </div>
                      )}

                      {o.status === "VERIFIED" && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setViewReportModal(o)}
                          leftIcon={<FileText className="w-3.5 h-3.5" />}
                        >
                          View Released Report
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Modal 1: Structured Result Entry */}
        {isResultModalOpen && selectedOrder && (
          <Modal
            isOpen={isResultModalOpen}
            onClose={() => setIsResultModalOpen(false)}
            title={`Enter Laboratory Results — ${selectedOrder.order_number}`}
            maxWidth="lg"
          >
            <form onSubmit={handleSubmitResults} className="space-y-4">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-400 block">Patient</span>
                  <span className="font-bold text-white">{selectedOrder.patient_name} ({selectedOrder.patient_mrn})</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Test Panel</span>
                  <span className="font-bold text-sky-400">{selectedOrder.test_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Priority</span>
                  {getPriorityBadge(selectedOrder.priority)}
                </div>
              </div>

              {/* Parameter Input Rows */}
              <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                <div className="grid grid-cols-12 gap-2 text-[10px] font-bold uppercase text-slate-400 px-2">
                  <span className="col-span-4">Parameter Name</span>
                  <span className="col-span-3">Result Value</span>
                  <span className="col-span-2">Units</span>
                  <span className="col-span-3">Reference Range / Flag</span>
                </div>

                {(tests?.find((t) => t.id === selectedOrder.test_id)?.parameters || selectedOrder.test?.parameters || []).map((pDef: any, idx: number) => {
                  const curr = parameterValues[pDef.name] || { val: "", flag: "NORMAL" };
                  return (
                    <div
                      key={idx}
                      className="grid grid-cols-12 gap-2 items-center p-2 rounded-xl bg-slate-900 border border-slate-800"
                    >
                      <div className="col-span-4 font-semibold text-xs text-white truncate">
                        {pDef.name}
                      </div>
                      <div className="col-span-3">
                        <input
                          type="text"
                          required
                          value={curr.val}
                          onChange={(e) => handleParamValueChange(pDef.name, e.target.value, pDef)}
                          placeholder="e.g. 14.5"
                          className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                        />
                      </div>
                      <div className="col-span-2 text-xs text-slate-400 truncate">
                        {pDef.unit || "-"}
                      </div>
                      <div className="col-span-3 flex items-center justify-between gap-1 text-[11px]">
                        <span className="text-slate-500 truncate">
                          {pDef.min_val !== undefined ? `${pDef.min_val}-${pDef.max_val}` : pDef.text_range || "Norm"}
                        </span>
                        {getFlagBadge(curr.flag || "NORMAL")}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="space-y-3 pt-2 border-t border-slate-800">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Clinical Interpretation Summary</label>
                  <input
                    type="text"
                    value={resultSummary}
                    onChange={(e) => setResultSummary(e.target.value)}
                    placeholder="Brief findings summary for doctor..."
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Internal Technician Notes (Hidden from patient)</label>
                  <input
                    type="text"
                    value={technicianNotes}
                    onChange={(e) => setTechnicianNotes(e.target.value)}
                    placeholder="Analyzer lot numbers, calibration checks, or specimen quality notes..."
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setIsResultModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={enterResultsMutation.isPending}>
                  Save & Complete Test
                </Button>
              </div>
            </form>
          </Modal>
        )}

        {/* Modal 2: Diagnostic Report Viewer & Print Sheet */}
        {viewReportModal && (
          <Modal
            isOpen={!!viewReportModal}
            onClose={() => setViewReportModal(null)}
            title={`Diagnostic Laboratory Report — ${viewReportModal.test_name}`}
            maxWidth="xl"
          >
            <div className="space-y-6">
              {/* Print-friendly Report Container */}
              <div id="printable-lab-report" className="p-6 bg-slate-900/90 rounded-2xl border border-slate-800 text-white space-y-6">
                {/* Header with Hospital Brand */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center font-mono font-black text-white text-lg">
                      CX
                    </div>
                    <div>
                      <h2 className="font-extrabold text-base tracking-wider text-white">CAREX METROPOLITAN HOSPITAL</h2>
                      <p className="text-[11px] text-slate-400">Department of Diagnostic Pathology & Clinical Chemistry • CAP / NABL Accredited</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest block">REPORT NUMBER</span>
                    <span className="font-mono font-bold text-sm text-sky-400">{viewReportModal.report_number || `RPT-${viewReportModal.order_number}`}</span>
                  </div>
                </div>

                {/* Patient & Order Metadata */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Patient Name</span>
                    <span className="font-extrabold text-white text-sm">{viewReportModal.patient_name}</span>
                    <span className="text-[11px] text-slate-400 block">{viewReportModal.patient_gender}, {viewReportModal.patient_age} yrs</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">MRN</span>
                    <span className="font-mono font-bold text-sky-300">{viewReportModal.patient_mrn}</span>
                    <span className="text-[11px] text-slate-400 block">Order: {viewReportModal.order_number}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Referring Doctor</span>
                    <span className="font-bold text-white">{viewReportModal.doctor_name?.startsWith("Dr.") ? viewReportModal.doctor_name : `Dr. ${viewReportModal.doctor_name}`}</span>
                    <span className="text-[11px] text-slate-400 block">Specimen: {viewReportModal.sample_type || "Blood"}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Date & Time</span>
                    <span className="font-mono text-slate-300">{new Date(viewReportModal.order_date).toLocaleDateString()}</span>
                    <span className="block">{getStatusBadge(viewReportModal.status)}</span>
                  </div>
                </div>

                {/* Parameter Results Table */}
                <div className="space-y-2">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 flex items-center justify-between">
                    <span>{viewReportModal.test_name} — Structured Results</span>
                    <span className="text-[10px] text-slate-400 font-normal">Method: Automated Spectrophotometry / Flow Cytometry</span>
                  </h4>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border border-slate-800">
                      <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold">
                        <tr>
                          <th className="p-3">Investigation / Parameter</th>
                          <th className="p-3">Result</th>
                          <th className="p-3">Unit</th>
                          <th className="p-3">Biological Reference Range</th>
                          <th className="p-3 text-right">Interpretation Flag</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {viewReportModal.result?.parameters?.map((p, idx) => (
                          <tr key={idx} className={p.flag === "CRITICAL" ? "bg-rose-950/20" : p.flag !== "NORMAL" ? "bg-amber-950/10" : ""}>
                            <td className="p-3 font-semibold text-white">{p.parameter_name}</td>
                            <td className="p-3 font-mono font-bold text-white text-sm">{p.result_value}</td>
                            <td className="p-3 text-slate-400">{p.unit || "-"}</td>
                            <td className="p-3 text-slate-400 font-mono">{p.reference_range || "Normal"}</td>
                            <td className="p-3 text-right">{getFlagBadge(p.flag)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Clinical Notes & Interpretation */}
                <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1.5 text-xs">
                  <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">Pathologist Interpretation & Impression</span>
                  <p className="text-slate-300">
                    {viewReportModal.result?.result_summary || "Laboratory findings verified. Please correlate with clinical signs and patient baseline."}
                  </p>
                </div>

                {/* Sign-off Footer */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-6 border-t border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">Performed By</span>
                    <span className="font-semibold text-slate-300">Amanda Foster, MLS</span>
                    <p className="text-[10px] text-slate-500">Certified Medical Lab Technologist</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">Electronically Verified By</span>
                    <span className="font-semibold text-sky-400">Dr. Rajesh Sharma, MD</span>
                    <p className="text-[10px] text-slate-500">Consultant Pathologist</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">Official Seal</span>
                    <span className="text-emerald-400 font-bold flex items-center justify-end gap-1">
                      <ShieldCheck className="w-4 h-4" /> CAREX VERIFIED
                    </span>
                  </div>
                </div>
              </div>

              {/* Modal Action Buttons */}
              <div className="flex items-center justify-between gap-3 pt-2">
                <Button variant="outline" size="sm" onClick={() => setViewReportModal(null)}>
                  Close
                </Button>

                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handlePrintReport}
                    leftIcon={<Printer className="w-4 h-4" />}
                  >
                    Print Report
                  </Button>

                  {(isLabTech || isDoctor) && viewReportModal.status !== "VERIFIED" && (
                    <Button
                      variant="glow"
                      size="sm"
                      onClick={() => verifyReportMutation.mutate(viewReportModal.id)}
                      isLoading={verifyReportMutation.isPending}
                      leftIcon={<ShieldCheck className="w-4 h-4" />}
                    >
                      Verify & Release Report
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </Modal>
        )}

        {/* Modal 3: Order Lab Test */}
        {isOrderModalOpen && (
          <Modal
            isOpen={isOrderModalOpen}
            onClose={() => setIsOrderModalOpen(false)}
            title="Order Diagnostic Laboratory Test"
            maxWidth="lg"
          >
            <form onSubmit={handleOrderSubmit} className="space-y-4">
              {/* Patient Selection Mode Toggle */}
              <div className="grid grid-cols-2 gap-2 p-1 bg-slate-950/80 rounded-xl border border-slate-800">
                <button
                  type="button"
                  onClick={() => setOrderMode("EXISTING_PATIENT")}
                  className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                    orderMode === "EXISTING_PATIENT"
                      ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <Search className="w-4 h-4" />
                  <span>Select Registered Patient ({patients?.length || 0})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setOrderMode("NEW_PATIENT")}
                  className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                    orderMode === "NEW_PATIENT"
                      ? "bg-emerald-500 text-white shadow-md shadow-emerald-500/25"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Direct Patient Intake (Fill Details)</span>
                </button>
              </div>

              {/* MODE 1: EXISTING PATIENT SELECTION */}
              {orderMode === "EXISTING_PATIENT" ? (
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search patient by name, MRN (CRX-...), or phone..."
                      value={orderPatientSearch}
                      onChange={(e) => setOrderPatientSearch(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-300 block mb-1.5">Select Patient from MPI *</label>
                    <select
                      required
                      value={orderPatientId}
                      onChange={(e) => setOrderPatientId(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                    >
                      <option value="">-- Choose Patient from MPI --</option>
                      {(patients || [])
                        .filter((p) => {
                          const q = orderPatientSearch.toLowerCase().trim();
                          if (!q) return true;
                          return (
                            p.full_name.toLowerCase().includes(q) ||
                            p.mrn.toLowerCase().includes(q) ||
                            p.phone?.toLowerCase().includes(q)
                          );
                        })
                        .map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.full_name} ({p.mrn}) — {p.gender}, {p.age} yrs • Phone: {p.phone}
                          </option>
                        ))}
                    </select>
                  </div>
                </div>
              ) : (
                /* MODE 2: DIRECT PATIENT INTAKE WITH CONSTRAINTS */
                <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-300">
                    <User className="w-4 h-4" />
                    <span>Patient Intake Demographics (Auto-creates MPI record)</span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      label="First Name (Alphabets only) *"
                      placeholder="e.g. Johnathan"
                      value={newPatientFirst}
                      maxLength={50}
                      pattern="^[A-Za-z\s\-']{2,50}$"
                      title="First name must contain alphabets only (min 2 characters)"
                      onChange={(e) => setNewPatientFirst(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                      required
                    />
                    <Input
                      label="Last Name (Alphabets only) *"
                      placeholder="e.g. Watson"
                      value={newPatientLast}
                      maxLength={50}
                      pattern="^[A-Za-z\s\-']{2,50}$"
                      title="Last name must contain alphabets only (min 2 characters)"
                      onChange={(e) => setNewPatientLast(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      label="Mobile Number (10 digits) *"
                      placeholder="e.g. 9876543210"
                      inputMode="numeric"
                      type="tel"
                      maxLength={10}
                      pattern="[0-9]{10}"
                      title="Mobile number must be numbers only and exactly 10 digits"
                      value={newPatientPhone}
                      helperText={newPatientPhone ? `${newPatientPhone.length}/10 digits ${newPatientPhone.length === 10 ? "✓" : ""}` : "Numbers only, 10 digits"}
                      onChange={(e) => setNewPatientPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                      required
                    />
                    <Input
                      label="Date of Birth *"
                      type="date"
                      value={newPatientDob}
                      max={new Date().toISOString().split("T")[0]}
                      min="1900-01-01"
                      onChange={(e) => setNewPatientDob(e.target.value)}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Select
                      label="Gender *"
                      options={[
                        { value: "Male", label: "Male" },
                        { value: "Female", label: "Female" },
                        { value: "Other", label: "Other" },
                      ]}
                      value={newPatientGender}
                      onChange={(e) => setNewPatientGender(e.target.value)}
                    />
                    <Select
                      label="Blood Group"
                      options={[
                        { value: "O+", label: "O+" },
                        { value: "O-", label: "O-" },
                        { value: "A+", label: "A+" },
                        { value: "A-", label: "A-" },
                        { value: "B+", label: "B+" },
                        { value: "B-", label: "B-" },
                        { value: "AB+", label: "AB+" },
                        { value: "AB-", label: "AB-" },
                      ]}
                      value={newPatientBlood}
                      onChange={(e) => setNewPatientBlood(e.target.value)}
                    />
                  </div>
                </div>
              )}

              {/* Lab Test Panel & Priority */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1.5">Diagnostic Test Panel *</label>
                  <select
                    required
                    value={orderTestId}
                    onChange={(e) => setOrderTestId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  >
                    <option value="">-- Choose Laboratory Test --</option>
                    {tests?.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.code}) — ${t.price.toFixed(2)} [{t.category}]
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1.5">Order Priority *</label>
                  <select
                    value={orderPriority}
                    onChange={(e) => setOrderPriority(e.target.value as LabOrderPriority)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  >
                    <option value="NORMAL">NORMAL — Routine Diagnostic Workup</option>
                    <option value="URGENT">URGENT — Priority Inpatient / Pre-Op</option>
                    <option value="STAT">STAT — Critical Resuscitation / Trauma</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1.5">Clinical Notes / Indication</label>
                <textarea
                  rows={2}
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  placeholder="Clinical indication, suspected condition, or special specimen instructions..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setIsOrderModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={isSubmittingOrder}>
                  Transmit Lab Order
                </Button>
              </div>
            </form>
          </Modal>
        )}
      </div>
    </PageContainer>
  );
};
