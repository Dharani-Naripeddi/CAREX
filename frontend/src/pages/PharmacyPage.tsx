import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pharmacyApi } from "../services/api";
import {
  Medicine,
  MedicineBatch,
  Prescription,
  PharmacyTransaction,
  DispensePayload,
  ExpiryClassificationItem,
  LowStockAlertItem,
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
  Pill,
  Plus,
  Search,
  CheckCircle,
  Clock,
  AlertTriangle,
  Calendar,
  Layers,
  Activity,
  ArrowRight,
  TrendingDown,
  ShieldCheck,
  Building,
  RefreshCw,
  FileText,
  DollarSign,
  Package,
} from "lucide-react";

export const PharmacyPage: React.FC = () => {
  const { user } = useAuth();
  const { success, error: toastError } = useToast();
  const queryClient = useQueryClient();

  const isPharmacist = user?.role === "PHARMACIST" || user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN";

  // State
  const [activeTab, setActiveTab] = useState<"dispensing" | "medicines" | "batches" | "expiry" | "low_stock" | "transactions">("dispensing");
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [expiryCategoryFilter, setExpiryCategoryFilter] = useState("ALL");

  // Dispensing Modal State
  const [selectedPrescription, setSelectedPrescription] = useState<Prescription | null>(null);
  const [dispenseBatchSelections, setDispenseBatchSelections] = useState<Record<number, { batch_id: number; qty: number }>>({});
  const [dispenseNotes, setDispenseNotes] = useState("");

  // New Batch Modal State
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [batchMedicineId, setBatchMedicineId] = useState("");
  const [batchNumber, setBatchNumber] = useState("");
  const [batchQty, setBatchQty] = useState("");
  const [batchPurchasePrice, setBatchPurchasePrice] = useState("");
  const [batchSellingPrice, setBatchSellingPrice] = useState("");
  const [batchExpiryDate, setBatchExpiryDate] = useState("");
  const [batchSupplier, setBatchSupplier] = useState("");
  const [batchLocation, setBatchLocation] = useState("Main Pharmacy Shelf A-1");

  // New Medicine Modal State
  const [isMedModalOpen, setIsMedModalOpen] = useState(false);
  const [medCode, setMedCode] = useState("");
  const [medName, setMedName] = useState("");
  const [medGeneric, setMedGeneric] = useState("");
  const [medCategory, setMedCategory] = useState("Cardiovascular");
  const [medUnit, setMedUnit] = useState("Tablets");
  const [medReorder, setMedReorder] = useState("50");
  const [medMax, setMedMax] = useState("500");
  const [medPrice, setMedPrice] = useState("1.00");
  const [medMfg, setMedMfg] = useState("");

  // Queries
  const { data: stats } = useQuery({
    queryKey: ["pharmacyDashboardStats"],
    queryFn: pharmacyApi.getDashboardStats,
    refetchInterval: 10000,
  });

  const { data: prescriptions, isLoading: rxLoading } = useQuery<Prescription[]>({
    queryKey: ["pharmacyPrescriptions"],
    queryFn: () => pharmacyApi.getPrescriptions(),
    refetchInterval: 8000,
  });

  const { data: medicines, isLoading: medsLoading } = useQuery<Medicine[]>({
    queryKey: ["pharmacyMedicines"],
    queryFn: () => pharmacyApi.getMedicines(),
  });

  const { data: expiryItems, isLoading: expiryLoading } = useQuery<ExpiryClassificationItem[]>({
    queryKey: ["pharmacyExpiry"],
    queryFn: pharmacyApi.getExpiryAnalysis,
  });

  const { data: lowStockAlerts, isLoading: lowStockLoading } = useQuery<LowStockAlertItem[]>({
    queryKey: ["pharmacyLowStock"],
    queryFn: pharmacyApi.getLowStockAlerts,
  });

  const { data: transactions, isLoading: txnsLoading } = useQuery<PharmacyTransaction[]>({
    queryKey: ["pharmacyTransactions"],
    queryFn: () => pharmacyApi.getTransactions(),
  });

  // Mutations
  const dispenseMutation = useMutation({
    mutationFn: (payload: DispensePayload) => pharmacyApi.dispense(payload),
    onSuccess: () => {
      success("Dispensation Complete", "Medicines successfully dispensed, inventory updated, and patient notified.");
      setSelectedPrescription(null);
      queryClient.invalidateQueries({ queryKey: ["pharmacyPrescriptions"] });
      queryClient.invalidateQueries({ queryKey: ["pharmacyMedicines"] });
      queryClient.invalidateQueries({ queryKey: ["pharmacyDashboardStats"] });
      queryClient.invalidateQueries({ queryKey: ["pharmacyTransactions"] });
      queryClient.invalidateQueries({ queryKey: ["pharmacyLowStock"] });
    },
    onError: (err: any) => {
      toastError("Dispensing Failed", err.response?.data?.detail || "Could not complete dispensation.");
    },
  });

  const createBatchMutation = useMutation({
    mutationFn: (data: any) => pharmacyApi.addBatch(data),
    onSuccess: () => {
      success("Batch Received", "New medicine batch registered into inventory with purchase ledger entry.");
      setIsBatchModalOpen(false);
      setBatchNumber("");
      setBatchQty("");
      queryClient.invalidateQueries({ queryKey: ["pharmacyMedicines"] });
      queryClient.invalidateQueries({ queryKey: ["pharmacyDashboardStats"] });
      queryClient.invalidateQueries({ queryKey: ["pharmacyTransactions"] });
    },
    onError: (err: any) => {
      toastError("Batch Failed", err.response?.data?.detail || "Could not add batch.");
    },
  });

  const createMedMutation = useMutation({
    mutationFn: (data: any) => pharmacyApi.createMedicine(data),
    onSuccess: () => {
      success("Medicine Added", "New medication SKU added to pharmacy directory.");
      setIsMedModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["pharmacyMedicines"] });
    },
    onError: (err: any) => {
      toastError("Creation Failed", err.response?.data?.detail || "Could not add medicine.");
    },
  });

  const handleOpenDispenseModal = (rx: Prescription) => {
    setSelectedPrescription(rx);
    const initialBatchSelections: Record<number, { batch_id: number; qty: number }> = {};

    rx.items.forEach((item) => {
      // Auto-select first available non-expired batch for this medicine
      const med = medicines?.find((m) => m.id === item.medicine_id);
      const activeBatch = med?.batches?.find((b) => b.is_active && b.quantity > 0 && b.expiry_status !== "EXPIRED");
      if (activeBatch) {
        initialBatchSelections[item.id] = {
          batch_id: activeBatch.id,
          qty: item.quantity_prescribed - item.quantity_dispensed,
        };
      }
    });

    setDispenseBatchSelections(initialBatchSelections);
    setDispenseNotes("");
  };

  const handleExecuteDispense = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPrescription) return;

    const itemsPayload = Object.entries(dispenseBatchSelections).map(([pItemIdStr, data]) => ({
      prescription_item_id: parseInt(pItemIdStr),
      batch_id: data.batch_id,
      quantity: data.qty,
    }));

    if (itemsPayload.length === 0) {
      toastError("Selection Missing", "Please select available batches for the prescription items.");
      return;
    }

    dispenseMutation.mutate({
      prescription_id: selectedPrescription.id,
      items: itemsPayload,
      notes: dispenseNotes,
    });
  };

  // Filtered lists
  const pendingPrescriptions = (prescriptions || []).filter((rx) => rx.status !== "DISPENSED" && rx.status !== "CANCELLED");

  const filteredMedicines = (medicines || []).filter((m) => {
    if (categoryFilter !== "ALL" && m.category !== categoryFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return m.name.toLowerCase().includes(q) || m.generic_name.toLowerCase().includes(q) || m.code.toLowerCase().includes(q);
    }
    return true;
  });

  const filteredExpiry = (expiryItems || []).filter((e) => {
    if (expiryCategoryFilter !== "ALL" && e.category !== expiryCategoryFilter) return false;
    return true;
  });

  return (
    <PageContainer
      title="Pharmacy & Therapeutics"
      subtitle="Prescription dispensing engine, FEFO batch stock management, low-stock reorder intelligence, and auditable inventory ledger."
      badge={<Badge variant="info" dot>Central Pharmacy Active</Badge>}
      actions={
        <div className="flex items-center gap-2.5">
          {isPharmacist && (
            <>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Plus className="w-4 h-4" />}
                onClick={() => setIsBatchModalOpen(true)}
              >
                Receive Batch
              </Button>
              <Button
                variant="glow"
                size="sm"
                leftIcon={<Plus className="w-4 h-4" />}
                onClick={() => setIsMedModalOpen(true)}
              >
                Add Medicine SKU
              </Button>
            </>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* KPI Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <Card className="p-3 bg-slate-900/60">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-slate-400">Total SKUs</span>
              <Pill className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-xl font-extrabold text-white mt-1">{stats?.total_medicines || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Active catalogue</p>
          </Card>

          <Card className="p-3 bg-slate-900/60">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-slate-400">Total Stock</span>
              <Package className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-xl font-extrabold text-indigo-300 mt-1">{stats?.total_stock_units?.toLocaleString() || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Units in inventory</p>
          </Card>

          <Card className={`p-3 bg-slate-900/60 ${(stats?.low_stock_count || 0) > 0 ? "border-amber-500/40" : ""}`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-amber-400">Low Stock</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-xl font-extrabold text-amber-400 mt-1">{stats?.low_stock_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">At or below reorder</p>
          </Card>

          <Card className={`p-3 bg-slate-900/60 ${(stats?.expiring_soon_count || 0) > 0 ? "border-rose-500/30" : ""}`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-rose-400">Expiring in 30d</span>
              <Calendar className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-xl font-extrabold text-rose-400 mt-1">{stats?.expiring_soon_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Prioritize FEFO</p>
          </Card>

          <Card className="p-3 bg-slate-900/60">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-emerald-400">Today Dispensed</span>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xl font-extrabold text-emerald-400 mt-1">{stats?.today_dispensed_count || 0}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Prescriptions fulfilled</p>
          </Card>

          <Card className="p-3 bg-slate-900/60">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase text-teal-400">Today Revenue</span>
              <DollarSign className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-xl font-extrabold text-teal-400 mt-1">${stats?.today_dispensed_amount?.toFixed(2) || "0.00"}</div>
            <p className="text-[10px] text-slate-500 mt-0.5">Medication sales</p>
          </Card>
        </div>

        {/* Tab Strip */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveTab("dispensing")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "dispensing"
                  ? "bg-sky-500 text-white shadow-lg shadow-sky-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Prescriptions Dispensing ({pendingPrescriptions.length})
            </button>
            <button
              onClick={() => setActiveTab("medicines")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "medicines"
                  ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Medicines Directory ({medicines?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("expiry")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "expiry"
                  ? "bg-rose-500 text-white shadow-lg shadow-rose-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Expiry Management ({expiryItems?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("low_stock")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "low_stock"
                  ? "bg-amber-500 text-white shadow-lg shadow-amber-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Low Stock & Reorders ({lowStockAlerts?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("transactions")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "transactions"
                  ? "bg-teal-500 text-white shadow-lg shadow-teal-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Stock Ledger ({transactions?.length || 0})
            </button>
          </div>

          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search medicine, generic, code..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>
        </div>

        {/* Tab 1: Prescription Dispensing Worklist */}
        {activeTab === "dispensing" && (
          <div className="space-y-3">
            {rxLoading ? (
              <div className="py-16 text-center">
                <LoadingSpinner size="lg" label="Loading prescriptions queue..." />
              </div>
            ) : pendingPrescriptions.length === 0 ? (
              <Card className="p-12 text-center text-slate-400">
                <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                <h4 className="font-bold text-white text-base">All Prescriptions Dispensed</h4>
                <p className="text-xs mt-1">There are no pending prescriptions waiting in the pharmacy queue.</p>
              </Card>
            ) : (
              pendingPrescriptions.map((rx) => (
                <Card key={rx.id} hoverable className="p-4">
                  <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                    <div className="flex items-start gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-xs text-sky-400 shrink-0 mt-0.5">
                        <Pill className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono font-bold text-xs text-white">{rx.prescription_number}</span>
                          <Badge variant={rx.status === "PARTIALLY_DISPENSED" ? "warning" : "info"}>
                            {rx.status}
                          </Badge>
                          <span className="text-xs text-slate-400">
                            {new Date(rx.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>

                        <div className="text-sm font-bold text-white">
                          Patient: {rx.patient_name} <span className="text-xs text-slate-400 font-mono">({rx.patient_mrn})</span>
                        </div>

                        <p className="text-xs text-slate-400">
                          Prescribed by: <strong>Dr. {rx.doctor_name}</strong> • Diagnosis: {rx.diagnosis || "Routine Clinical Management"}
                        </p>

                        {/* Medications preview */}
                        <div className="flex items-center gap-2 flex-wrap pt-1">
                          {rx.items.map((itm) => (
                            <span
                              key={itm.id}
                              className={`text-[11px] px-2.5 py-0.5 rounded-lg border flex items-center gap-1.5 ${
                                itm.status === "DISPENSED"
                                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 line-through"
                                  : (itm.available_stock || 0) < itm.quantity_prescribed
                                  ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                                  : "bg-slate-900 border-slate-700 text-slate-200"
                              }`}
                            >
                              <strong>{itm.medicine_name}</strong> {itm.dosage} ({itm.quantity_prescribed} {itm.medicine_unit || "tabs"})
                              {(itm.available_stock || 0) < itm.quantity_prescribed && (
                                <span className="text-[9px] font-bold text-rose-400 font-mono">[Only {itm.available_stock || 0} in stock]</span>
                              )}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 w-full lg:w-auto justify-end pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                      {isPharmacist && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => handleOpenDispenseModal(rx)}
                          leftIcon={<CheckCircle className="w-4 h-4" />}
                        >
                          Check Stock & Dispense
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}

        {/* Tab 2: Medicines Directory */}
        {activeTab === "medicines" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {medsLoading ? (
                <div className="col-span-full py-16 text-center">
                  <LoadingSpinner size="lg" label="Loading medications directory..." />
                </div>
              ) : (
                filteredMedicines.map((m) => (
                  <Card key={m.id} hoverable className="p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <Badge variant="outline" size="sm" className="mb-1 font-mono">
                          {m.code}
                        </Badge>
                        <h4 className="font-bold text-sm text-white">{m.name}</h4>
                        <p className="text-[11px] text-slate-400 font-medium italic">{m.generic_name}</p>
                      </div>
                      <span className="text-base font-extrabold text-emerald-400 font-mono">
                        ${m.unit_price.toFixed(2)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                      <div>
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">Total Stock</span>
                        <span className={`font-mono font-bold text-sm ${m.is_low_stock ? "text-amber-400" : "text-white"}`}>
                          {m.total_stock} {m.unit}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-slate-500 block uppercase font-bold">Reorder Level</span>
                        <span className="font-mono text-slate-400 text-xs">{m.reorder_level} {m.unit}</span>
                      </div>
                    </div>

                    {m.is_low_stock && (
                      <div className="flex items-center justify-between text-[11px] bg-amber-500/10 border border-amber-500/20 text-amber-300 p-2 rounded-lg">
                        <span className="flex items-center gap-1 font-bold">
                          <AlertTriangle className="w-3.5 h-3.5" /> LOW STOCK
                        </span>
                        <span>Reorder: +{m.suggested_reorder_qty} units</span>
                      </div>
                    )}

                    <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                      <span>{m.manufacturer || "Standard Supply"}</span>
                      <span>{m.batches_count} active batch(es)</span>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Expiry Management */}
        {activeTab === "expiry" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {["ALL", "EXPIRED", "EXPIRING_WITHIN_7_DAYS", "EXPIRING_WITHIN_30_DAYS", "EXPIRING_WITHIN_90_DAYS"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setExpiryCategoryFilter(cat)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                    expiryCategoryFilter === cat
                      ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                      : "bg-slate-900 text-slate-400 border-slate-800 hover:text-white"
                  }`}
                >
                  {cat.replace(/_/g, " ")}
                </button>
              ))}
            </div>

            {expiryLoading ? (
              <div className="py-16 text-center">
                <LoadingSpinner size="lg" label="Analyzing expiry risk..." />
              </div>
            ) : filteredExpiry.length === 0 ? (
              <Card className="p-12 text-center text-slate-400">
                <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                <h4 className="font-bold text-white text-base">No Expiring Batches</h4>
                <p className="text-xs mt-1">All batches in inventory have valid extended shelf life.</p>
              </Card>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-slate-800">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold">
                    <tr>
                      <th className="p-3">Medicine Name</th>
                      <th className="p-3">Batch Number</th>
                      <th className="p-3">Quantity</th>
                      <th className="p-3">Expiry Date</th>
                      <th className="p-3">Days Remaining</th>
                      <th className="p-3">Risk Level</th>
                      <th className="p-3 text-right">Classification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {filteredExpiry.map((e, idx) => (
                      <tr key={idx} className={e.category === "EXPIRED" ? "bg-rose-950/20" : e.category === "EXPIRING_WITHIN_7_DAYS" ? "bg-rose-950/10" : ""}>
                        <td className="p-3 font-semibold text-white">
                          {e.medicine_name} <span className="text-slate-500 font-mono text-[11px]">({e.medicine_code})</span>
                        </td>
                        <td className="p-3 font-mono text-slate-300">{e.batch_number}</td>
                        <td className="p-3 font-mono font-bold text-white">{e.quantity}</td>
                        <td className="p-3 font-mono text-slate-300">{e.expiry_date}</td>
                        <td className="p-3 font-mono font-bold text-rose-400">
                          {e.days_remaining < 0 ? `${Math.abs(e.days_remaining)} days ago` : `${e.days_remaining} days`}
                        </td>
                        <td className="p-3">
                          <Badge variant={e.risk_level === "HIGH" ? "critical" : e.risk_level === "MEDIUM" ? "warning" : "info"}>
                            {e.risk_level} RISK
                          </Badge>
                        </td>
                        <td className="p-3 text-right">
                          <span className="font-mono text-[11px] text-slate-300">{e.category}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Low Stock & Reorders */}
        {activeTab === "low_stock" && (
          <div className="space-y-4">
            {lowStockLoading ? (
              <div className="py-16 text-center">
                <LoadingSpinner size="lg" label="Scanning stock levels..." />
              </div>
            ) : lowStockAlerts?.length === 0 ? (
              <Card className="p-12 text-center text-slate-400">
                <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                <h4 className="font-bold text-white text-base">Adequate Inventory Levels</h4>
                <p className="text-xs mt-1">All medicines are currently above configured reorder levels.</p>
              </Card>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-slate-800">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold">
                    <tr>
                      <th className="p-3">Medicine SKU</th>
                      <th className="p-3">Category</th>
                      <th className="p-3">Current Stock</th>
                      <th className="p-3">Reorder Threshold</th>
                      <th className="p-3">Max Stock</th>
                      <th className="p-3">Suggested Reorder Quantity</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {lowStockAlerts?.map((ls, idx) => (
                      <tr key={idx} className="bg-amber-950/10">
                        <td className="p-3 font-semibold text-white">
                          {ls.medicine_name} <span className="text-slate-500 font-mono text-[11px]">({ls.medicine_code})</span>
                        </td>
                        <td className="p-3 text-slate-400">{ls.category}</td>
                        <td className="p-3 font-mono font-extrabold text-amber-400 text-sm">
                          {ls.current_stock} {ls.unit}
                        </td>
                        <td className="p-3 font-mono text-slate-300">{ls.reorder_level} {ls.unit}</td>
                        <td className="p-3 font-mono text-slate-400">{ls.max_stock_level} {ls.unit}</td>
                        <td className="p-3 font-mono font-bold text-emerald-400">
                          +{ls.suggested_reorder_qty} {ls.unit}
                        </td>
                        <td className="p-3 text-right">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setBatchMedicineId(ls.medicine_id.toString());
                              setBatchQty(ls.suggested_reorder_qty.toString());
                              setIsBatchModalOpen(true);
                            }}
                          >
                            Receive Stock
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 5: Stock Transactions Ledger */}
        {activeTab === "transactions" && (
          <div className="space-y-4">
            {txnsLoading ? (
              <div className="py-16 text-center">
                <LoadingSpinner size="lg" label="Loading stock ledger..." />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-slate-800">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold">
                    <tr>
                      <th className="p-3">Txn #</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Medicine</th>
                      <th className="p-3">Batch</th>
                      <th className="p-3">Quantity Delta</th>
                      <th className="p-3">Total Amount</th>
                      <th className="p-3">Reference / Notes</th>
                      <th className="p-3">Performed By</th>
                      <th className="p-3 text-right">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {transactions?.map((t) => (
                      <tr key={t.id}>
                        <td className="p-3 font-mono font-bold text-sky-400">{t.transaction_number}</td>
                        <td className="p-3">
                          <Badge
                            variant={
                              t.transaction_type === "PURCHASE"
                                ? "success"
                                : t.transaction_type === "DISPENSE"
                                ? "info"
                                : "warning"
                            }
                          >
                            {t.transaction_type}
                          </Badge>
                        </td>
                        <td className="p-3 font-semibold text-white">{t.medicine_name}</td>
                        <td className="p-3 font-mono text-slate-400">{t.batch_number || "-"}</td>
                        <td className={`p-3 font-mono font-bold ${t.quantity > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {t.quantity > 0 ? `+${t.quantity}` : t.quantity}
                        </td>
                        <td className="p-3 font-mono text-white">${t.total_amount.toFixed(2)}</td>
                        <td className="p-3 text-slate-400 max-w-xs truncate">{t.notes || t.reference_id || "-"}</td>
                        <td className="p-3 text-slate-300">{t.performed_by_name || "Pharmacist"}</td>
                        <td className="p-3 text-right font-mono text-slate-500">
                          {new Date(t.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Modal 1: Dispense Prescription */}
        {selectedPrescription && (
          <Modal
            isOpen={!!selectedPrescription}
            onClose={() => setSelectedPrescription(null)}
            title={`Dispense Prescription — ${selectedPrescription.prescription_number}`}
            maxWidth="lg"
          >
            <form onSubmit={handleExecuteDispense} className="space-y-4">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-400 block">Patient</span>
                  <span className="font-bold text-white">{selectedPrescription.patient_name} ({selectedPrescription.patient_mrn})</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Prescribing Doctor</span>
                  <span className="font-bold text-sky-400">Dr. {selectedPrescription.doctor_name}</span>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Prescribed Items & Batch Allocation</h4>

                {selectedPrescription.items.map((item) => {
                  const med = medicines?.find((m) => m.id === item.medicine_id);
                  const activeBatches = (med?.batches || []).filter((b) => b.is_active && b.expiry_status !== "EXPIRED");
                  const currentSelection = dispenseBatchSelections[item.id] || { batch_id: 0, qty: item.quantity_prescribed };

                  return (
                    <div key={item.id} className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-bold text-sm text-white">{item.medicine_name}</span>
                          <span className="text-xs text-sky-400 ml-2">Dosage: {item.dosage} • {item.frequency}</span>
                        </div>
                        <span className="text-xs font-mono font-bold text-slate-300">
                          Prescribed: {item.quantity_prescribed} {item.medicine_unit || "tabs"}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                        <div>
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Select Batch (FEFO Order)</label>
                          <select
                            required
                            value={currentSelection.batch_id}
                            onChange={(e) => {
                              const bId = parseInt(e.target.value);
                              setDispenseBatchSelections((prev) => ({
                                ...prev,
                                [item.id]: { ...prev[item.id], batch_id: bId },
                              }));
                            }}
                            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                          >
                            <option value="">-- Choose Stock Batch --</option>
                            {activeBatches.map((b) => (
                              <option key={b.id} value={b.id}>
                                {b.batch_number} (Avail: {b.quantity}) — Exp: {b.expiry_date} [{b.storage_location || "Bin"}]
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Dispense Quantity</label>
                          <input
                            type="number"
                            min={1}
                            max={item.quantity_prescribed}
                            value={currentSelection.qty}
                            onChange={(e) => {
                              const q = parseInt(e.target.value) || 0;
                              setDispenseBatchSelections((prev) => ({
                                ...prev,
                                [item.id]: { ...prev[item.id], qty: q },
                              }));
                            }}
                            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Pharmacist Dispensing Notes</label>
                <input
                  type="text"
                  value={dispenseNotes}
                  onChange={(e) => setDispenseNotes(e.target.value)}
                  placeholder="Patient counseling provided, drug interaction check verified..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setSelectedPrescription(null)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={dispenseMutation.isPending}>
                  Confirm & Deduct Inventory
                </Button>
              </div>
            </form>
          </Modal>
        )}

        {/* Modal 2: Receive New Batch */}
        {isBatchModalOpen && (
          <Modal
            isOpen={isBatchModalOpen}
            onClose={() => setIsBatchModalOpen(false)}
            title="Receive New Medicine Batch Intake"
            maxWidth="md"
          >
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createBatchMutation.mutate({
                  medicine_id: parseInt(batchMedicineId),
                  batch_number: batchNumber,
                  quantity: parseInt(batchQty),
                  purchase_price: parseFloat(batchPurchasePrice),
                  selling_price: parseFloat(batchSellingPrice),
                  expiry_date: batchExpiryDate,
                  supplier: batchSupplier,
                  storage_location: batchLocation,
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1.5">Medicine SKU</label>
                <select
                  required
                  value={batchMedicineId}
                  onChange={(e) => {
                    setBatchMedicineId(e.target.value);
                    const med = medicines?.find((m) => m.id === parseInt(e.target.value));
                    if (med) {
                      setBatchSellingPrice(med.unit_price.toString());
                      setBatchPurchasePrice((med.unit_price * 0.65).toFixed(2));
                    }
                  }}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="">-- Choose Medicine --</option>
                  {medicines?.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.code}) — {m.category}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Batch Number</label>
                  <input
                    type="text"
                    required
                    value={batchNumber}
                    onChange={(e) => setBatchNumber(e.target.value)}
                    placeholder="e.g. BATCH-2026-X1"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Quantity Received</label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={batchQty}
                    onChange={(e) => setBatchQty(e.target.value)}
                    placeholder="e.g. 100"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Purchase Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={batchPurchasePrice}
                    onChange={(e) => setBatchPurchasePrice(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Selling Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={batchSellingPrice}
                    onChange={(e) => setBatchSellingPrice(e.target.value)}
                    placeholder="0.00"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Expiry Date</label>
                <input
                  type="date"
                  required
                  value={batchExpiryDate}
                  onChange={(e) => setBatchExpiryDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Supplier</label>
                  <input
                    type="text"
                    value={batchSupplier}
                    onChange={(e) => setBatchSupplier(e.target.value)}
                    placeholder="e.g. Apex Pharma Logistics"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Storage Bin / Location</label>
                  <input
                    type="text"
                    value={batchLocation}
                    onChange={(e) => setBatchLocation(e.target.value)}
                    placeholder="e.g. Shelf A-04"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setIsBatchModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={createBatchMutation.isPending}>
                  Record Batch Intake
                </Button>
              </div>
            </form>
          </Modal>
        )}

        {/* Modal 3: Add Medicine SKU */}
        {isMedModalOpen && (
          <Modal
            isOpen={isMedModalOpen}
            onClose={() => setIsMedModalOpen(false)}
            title="Create New Medicine Directory SKU"
            maxWidth="md"
          >
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMedMutation.mutate({
                  code: medCode,
                  name: medName,
                  generic_name: medGeneric,
                  category: medCategory,
                  unit: medUnit,
                  reorder_level: parseInt(medReorder),
                  max_stock_level: parseInt(medMax),
                  unit_price: parseFloat(medPrice),
                  manufacturer: medMfg,
                });
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Medicine Code</label>
                  <input
                    type="text"
                    required
                    value={medCode}
                    onChange={(e) => setMedCode(e.target.value)}
                    placeholder="e.g. MED-051"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Category</label>
                  <select
                    value={medCategory}
                    onChange={(e) => setMedCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  >
                    <option value="Cardiovascular">Cardiovascular</option>
                    <option value="Antibiotics">Antibiotics</option>
                    <option value="Analgesics">Analgesics</option>
                    <option value="Antidiabetic">Antidiabetic</option>
                    <option value="Gastrointestinal">Gastrointestinal</option>
                    <option value="Respiratory">Respiratory</option>
                    <option value="Critical Care">Critical Care</option>
                    <option value="IV Fluids">IV Fluids</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Brand / Product Name</label>
                <input
                  type="text"
                  required
                  value={medName}
                  onChange={(e) => setMedName(e.target.value)}
                  placeholder="e.g. Rosuvastatin 10mg"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Generic / Chemical Name</label>
                <input
                  type="text"
                  required
                  value={medGeneric}
                  onChange={(e) => setMedGeneric(e.target.value)}
                  placeholder="e.g. Rosuvastatin Calcium"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Unit</label>
                  <input
                    type="text"
                    required
                    value={medUnit}
                    onChange={(e) => setMedUnit(e.target.value)}
                    placeholder="Tablets"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Reorder Level</label>
                  <input
                    type="number"
                    required
                    value={medReorder}
                    onChange={(e) => setMedReorder(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">Selling Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={medPrice}
                    onChange={(e) => setMedPrice(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setIsMedModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={createMedMutation.isPending}>
                  Save Medicine SKU
                </Button>
              </div>
            </form>
          </Modal>
        )}
      </div>
    </PageContainer>
  );
};
