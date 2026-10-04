import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pharmacyApi, patientsApi } from "../services/api";
import { Prescription, PrescriptionItem, Medicine, PrescriptionStatus } from "../types/support_services";
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
  Printer,
  FileText,
  Clock,
  CheckCircle,
  Calendar,
  Layers,
  Activity,
  ShieldCheck,
  UserCheck,
} from "lucide-react";

export const PrescriptionsPage: React.FC = () => {
  const { user } = useAuth();
  const { success, error: toastError } = useToast();
  const queryClient = useQueryClient();

  const isDoctor = user?.role === "DOCTOR" || user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN";
  const isPatient = user?.role === "PATIENT";

  // State
  const [activeTab, setActiveTab] = useState<"all" | "pending" | "dispensed">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewPrescription, setViewPrescription] = useState<Prescription | null>(null);
  const [isNewRxModalOpen, setIsNewRxModalOpen] = useState(false);

  // New Prescription Form State
  const [patientId, setPatientId] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [rxNotes, setRxNotes] = useState("");
  const [rxItems, setRxItems] = useState<
    {
      medicine_id: string;
      dosage: string;
      frequency: string;
      duration: string;
      quantity_prescribed: number;
      instructions: string;
    }[]
  >([
    {
      medicine_id: "",
      dosage: "1 tab",
      frequency: "1-0-1 (After food)",
      duration: "5 days",
      quantity_prescribed: 10,
      instructions: "Take with full glass of water.",
    },
  ]);

  // Queries
  const { data: prescriptions, isLoading: rxLoading, isError, refetch } = useQuery<Prescription[]>({
    queryKey: ["prescriptionsList"],
    queryFn: () => pharmacyApi.getPrescriptions(),
    refetchInterval: 8000,
  });

  const { data: medicines } = useQuery<Medicine[]>({
    queryKey: ["pharmacyMedicines"],
    queryFn: () => pharmacyApi.getMedicines(),
  });

  const { data: patients } = useQuery({
    queryKey: ["patientsList"],
    queryFn: () => patientsApi.list(),
  });

  // Mutations
  const createRxMutation = useMutation({
    mutationFn: (payload: any) => pharmacyApi.createPrescription(payload),
    onSuccess: () => {
      success("Prescription Signed", "Prescription electronically authorized and transmitted to central pharmacy.");
      setIsNewRxModalOpen(false);
      setPatientId("");
      setDiagnosis("");
      setRxNotes("");
      setRxItems([
        {
          medicine_id: "",
          dosage: "1 tab",
          frequency: "1-0-1 (After food)",
          duration: "5 days",
          quantity_prescribed: 10,
          instructions: "Take with full glass of water.",
        },
      ]);
      queryClient.invalidateQueries({ queryKey: ["prescriptionsList"] });
    },
    onError: (err: any) => {
      toastError("Error", err.response?.data?.detail || "Could not create prescription.");
    },
  });

  const handleAddItemRow = () => {
    setRxItems((prev) => [
      ...prev,
      {
        medicine_id: "",
        dosage: "1 tab",
        frequency: "1-0-0 (Morning)",
        duration: "7 days",
        quantity_prescribed: 7,
        instructions: "",
      },
    ]);
  };

  const handleRemoveItemRow = (idx: number) => {
    setRxItems((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleItemChange = (idx: number, field: string, val: any) => {
    setRxItems((prev) =>
      prev.map((item, i) => {
        if (i !== idx) return item;
        return { ...item, [field]: val };
      })
    );
  };

  const handlePrint = () => {
    window.print();
  };

  // Filtered list
  const filteredPrescriptions = (prescriptions || []).filter((rx) => {
    if (activeTab === "pending" && (rx.status === "DISPENSED" || rx.status === "CANCELLED")) return false;
    if (activeTab === "dispensed" && rx.status !== "DISPENSED") return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchNum = rx.prescription_number.toLowerCase().includes(q);
      const matchPat = rx.patient_name?.toLowerCase().includes(q) || rx.patient_mrn?.toLowerCase().includes(q);
      const matchDoc = rx.doctor_name?.toLowerCase().includes(q);
      return matchNum || matchPat || matchDoc;
    }
    return true;
  });

  const getStatusBadge = (st: PrescriptionStatus) => {
    switch (st) {
      case "DISPENSED":
        return <Badge variant="success">DISPENSED</Badge>;
      case "PARTIALLY_DISPENSED":
        return <Badge variant="warning">PARTIALLY DISPENSED</Badge>;
      case "PENDING":
        return <Badge variant="info">PENDING DISPENSING</Badge>;
      case "CANCELLED":
        return <Badge variant="outline">CANCELLED</Badge>;
    }
  };

  return (
    <PageContainer
      title="Electronic Prescriptions & Regimens"
      subtitle="Digital doctor prescription authoring, structured dosage titrations, pharmacy dispense tracking, and clinical compliance records."
      badge={<Badge variant="info" dot>e-Prescriptions Active</Badge>}
      actions={
        <div className="flex items-center gap-2.5">
          {isDoctor && (
            <Button
              variant="glow"
              size="sm"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => setIsNewRxModalOpen(true)}
            >
              Write Prescription
            </Button>
          )}
        </div>
      }
    >
      <div className="space-y-6">
        {/* Tab & Search Strip */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "all"
                  ? "bg-sky-500 text-white shadow-lg shadow-sky-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              All Prescriptions ({prescriptions?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("pending")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "pending"
                  ? "bg-amber-500 text-white shadow-lg shadow-amber-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Pending Dispensing ({(prescriptions || []).filter((p) => p.status === "PENDING" || p.status === "PARTIALLY_DISPENSED").length})
            </button>
            <button
              onClick={() => setActiveTab("dispensed")}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === "dispensed"
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              Fulfilled & Dispensed ({(prescriptions || []).filter((p) => p.status === "DISPENSED").length})
            </button>
          </div>

          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Rx #, patient, doctor..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
          </div>
        </div>

        {/* Prescriptions List */}
        <div className="space-y-3">
          {rxLoading ? (
            <div className="py-16 text-center">
              <LoadingSpinner size="lg" label="Loading prescriptions ledger..." />
            </div>
          ) : isError ? (
            <ErrorState onRetry={() => refetch()} />
          ) : filteredPrescriptions.length === 0 ? (
            <Card className="p-12 text-center text-slate-400">
              <Pill className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h4 className="font-bold text-white text-base">No Prescriptions Found</h4>
              <p className="text-xs mt-1">No electronic prescriptions matching the filter criteria.</p>
            </Card>
          ) : (
            filteredPrescriptions.map((rx) => (
              <Card key={rx.id} hoverable className="p-4">
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                  <div className="flex items-start gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-xs text-sky-400 shrink-0 mt-0.5">
                      <Pill className="w-5 h-5" />
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-bold text-xs text-white">{rx.prescription_number}</span>
                        {getStatusBadge(rx.status)}
                        <span className="text-xs text-slate-400 font-mono">
                          {new Date(rx.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <div className="text-sm font-bold text-white">
                        Patient: {rx.patient_name} <span className="text-xs text-slate-400 font-mono">({rx.patient_mrn})</span>
                      </div>

                      <p className="text-xs text-slate-400">
                        Prescribed by: <strong className="text-slate-200">Dr. {rx.doctor_name}</strong> • Diagnosis: {rx.diagnosis || "General Clinical Care"}
                      </p>

                      <div className="flex items-center gap-2 flex-wrap pt-1">
                        {rx.items.map((itm) => (
                          <span
                            key={itm.id}
                            className="text-[11px] px-2.5 py-0.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200"
                          >
                            <strong>{itm.medicine_name}</strong> {itm.dosage} • {itm.frequency} ({itm.quantity_prescribed} {itm.medicine_unit || "tabs"})
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 w-full lg:w-auto justify-end pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setViewPrescription(rx)}
                      leftIcon={<FileText className="w-3.5 h-3.5" />}
                    >
                      View & Print Slip
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>

        {/* Modal 1: Printable Prescription Slip */}
        {viewPrescription && (
          <Modal
            isOpen={!!viewPrescription}
            onClose={() => setViewPrescription(null)}
            title={`Electronic Prescription Slip — ${viewPrescription.prescription_number}`}
            maxWidth="lg"
          >
            <div className="space-y-6">
              <div id="printable-prescription" className="p-6 bg-slate-900/90 rounded-2xl border border-slate-800 text-white space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center font-mono font-black text-white text-lg">
                      CX
                    </div>
                    <div>
                      <h2 className="font-extrabold text-base tracking-wider text-white">CAREX METROPOLITAN HOSPITAL</h2>
                      <p className="text-[11px] text-slate-400">Department of Clinical Medicine & Outpatient Services</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest block">PRESCRIPTION NUMBER</span>
                    <span className="font-mono font-bold text-sm text-sky-400">{viewPrescription.prescription_number}</span>
                  </div>
                </div>

                {/* Patient & Doctor Details */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Patient Name</span>
                    <span className="font-extrabold text-white text-sm">{viewPrescription.patient_name}</span>
                    <span className="text-[11px] text-slate-400 block">MRN: {viewPrescription.patient_mrn}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Attending Doctor</span>
                    <span className="font-bold text-white">Dr. {viewPrescription.doctor_name}</span>
                    <span className="text-[11px] text-slate-400 block">Specialist Consultant</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 block font-bold">Date Authorized</span>
                    <span className="font-mono text-slate-300">{new Date(viewPrescription.created_at).toLocaleDateString()}</span>
                    <span className="block">{getStatusBadge(viewPrescription.status)}</span>
                  </div>
                </div>

                {/* Diagnosis */}
                <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-xs">
                  <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Clinical Diagnosis & Findings</span>
                  <p className="font-semibold text-sky-300">{viewPrescription.diagnosis || "Routine Medical Treatment"}</p>
                </div>

                {/* Medications Table */}
                <div className="space-y-2">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 flex items-center justify-between">
                    <span>Rx — Prescribed Medication Regimen</span>
                    <span className="text-[10px] text-slate-400 font-normal">Valid for hospital dispensing</span>
                  </h4>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border border-slate-800">
                      <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-bold">
                        <tr>
                          <th className="p-3">#</th>
                          <th className="p-3">Medication</th>
                          <th className="p-3">Dosage</th>
                          <th className="p-3">Frequency</th>
                          <th className="p-3">Duration</th>
                          <th className="p-3 text-center">Qty</th>
                          <th className="p-3">Instructions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {viewPrescription.items.map((itm, idx) => (
                          <tr key={idx}>
                            <td className="p-3 font-mono text-slate-500">{idx + 1}</td>
                            <td className="p-3 font-bold text-white">{itm.medicine_name}</td>
                            <td className="p-3 font-mono text-slate-300">{itm.dosage}</td>
                            <td className="p-3 text-slate-300">{itm.frequency}</td>
                            <td className="p-3 text-slate-400">{itm.duration}</td>
                            <td className="p-3 text-center font-mono font-bold text-white">{itm.quantity_prescribed}</td>
                            <td className="p-3 text-slate-400 italic">{itm.instructions || "-"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Doctor's Signature */}
                <div className="flex items-center justify-between pt-6 border-t border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">Pharmacy Note</span>
                    <p className="text-[11px] text-slate-400">Dispense only with verified batch lot number and patient counseling.</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">Authorized Digital Signature</span>
                    <span className="text-emerald-400 font-bold flex items-center justify-end gap-1">
                      <ShieldCheck className="w-4 h-4" /> Dr. {viewPrescription.doctor_name}
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between gap-3 pt-2">
                <Button variant="outline" size="sm" onClick={() => setViewPrescription(null)}>
                  Close
                </Button>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handlePrint}
                  leftIcon={<Printer className="w-4 h-4" />}
                >
                  Print Prescription Slip
                </Button>
              </div>
            </div>
          </Modal>
        )}

        {/* Modal 2: Doctor Prescription Writer */}
        {isNewRxModalOpen && (
          <Modal
            isOpen={isNewRxModalOpen}
            onClose={() => setIsNewRxModalOpen(false)}
            title="Author Electronic Prescription"
            maxWidth="lg"
          >
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const itemsPayload = rxItems.map((itm) => ({
                  medicine_id: parseInt(itm.medicine_id),
                  dosage: itm.dosage,
                  frequency: itm.frequency,
                  duration: itm.duration,
                  quantity_prescribed: itm.quantity_prescribed,
                  instructions: itm.instructions,
                }));

                createRxMutation.mutate({
                  patient_id: parseInt(patientId),
                  diagnosis: diagnosis,
                  notes: rxNotes,
                  items: itemsPayload,
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Select Patient</label>
                <select
                  required
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                >
                  <option value="">-- Choose Patient from MPI --</option>
                  {patients?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} ({p.mrn}) — {p.gender}, {p.age} yrs
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Clinical Diagnosis / Indication</label>
                <input
                  type="text"
                  required
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="e.g. Acute Coronary Syndrome, Post-PCI Titration"
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              {/* Items List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Medications</h4>
                  <Button variant="outline" size="sm" type="button" onClick={handleAddItemRow} leftIcon={<Plus className="w-3.5 h-3.5" />}>
                    Add Medicine
                  </Button>
                </div>

                <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                  {rxItems.map((item, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                      <div className="grid grid-cols-12 gap-2">
                        <div className="col-span-8">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Medicine</label>
                          <select
                            required
                            value={item.medicine_id}
                            onChange={(e) => handleItemChange(idx, "medicine_id", e.target.value)}
                            className="w-full px-2 py-1.5 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none"
                          >
                            <option value="">-- Choose Medicine --</option>
                            {medicines?.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name} ({m.generic_name}) — Stock: {m.total_stock} {m.unit}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="col-span-4">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Dosage</label>
                          <input
                            type="text"
                            required
                            value={item.dosage}
                            onChange={(e) => handleItemChange(idx, "dosage", e.target.value)}
                            placeholder="e.g. 20mg or 1 tab"
                            className="w-full px-2 py-1.5 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none font-mono"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-12 gap-2 items-center">
                        <div className="col-span-4">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Frequency</label>
                          <input
                            type="text"
                            value={item.frequency}
                            onChange={(e) => handleItemChange(idx, "frequency", e.target.value)}
                            placeholder="e.g. 1-0-1 (BD)"
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none"
                          />
                        </div>

                        <div className="col-span-3">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Duration</label>
                          <input
                            type="text"
                            value={item.duration}
                            onChange={(e) => handleItemChange(idx, "duration", e.target.value)}
                            placeholder="5 days"
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none"
                          />
                        </div>

                        <div className="col-span-3">
                          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Qty Prescribed</label>
                          <input
                            type="number"
                            min={1}
                            value={item.quantity_prescribed}
                            onChange={(e) => handleItemChange(idx, "quantity_prescribed", parseInt(e.target.value) || 1)}
                            className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none font-mono"
                          />
                        </div>

                        <div className="col-span-2 text-right pt-4">
                          {rxItems.length > 1 && (
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
                <label className="text-xs font-bold text-slate-300 block mb-1">Patient Instructions / Precautions</label>
                <input
                  type="text"
                  value={rxNotes}
                  onChange={(e) => setRxNotes(e.target.value)}
                  placeholder="e.g. Take after meals, avoid grapefruit juice..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button variant="outline" type="button" onClick={() => setIsNewRxModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="glow" type="submit" isLoading={createRxMutation.isPending}>
                  Sign & Authorize Prescription
                </Button>
              </div>
            </form>
          </Modal>
        )}
      </div>
    </PageContainer>
  );
};
