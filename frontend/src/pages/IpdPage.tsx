import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ipdApi, patientsApi, doctorsApi, bedsApi } from "../services/api";
import {
  Admission,
  AdmissionCreatePayload,
  AdmissionStatus,
  DischargeCondition,
} from "../types/emergency_ipd";
import { PageContainer } from "../components/layout/PageContainer";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/Table";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Badge } from "../components/ui/Badge";
import { Modal } from "../components/ui/Modal";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { useToast } from "../hooks/useToast";
import {
  BedDouble,
  UserPlus,
  ArrowRightLeft,
  LogOut,
  Calendar,
  Building,
  Filter,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Plus,
  Search,
  Sparkles,
  RefreshCw,
  Zap,
  Activity,
  User,
} from "lucide-react";

export const IpdPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError, info } = useToast();

  const [statusFilter, setStatusFilter] = useState<string>("ADMITTED");
  const [selectedWardFilter, setSelectedWardFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals
  const [isAdmitModalOpen, setIsAdmitModalOpen] = useState(false);
  const [transferringAdmission, setTransferringAdmission] = useState<Admission | null>(null);
  const [dischargingAdmission, setDischargingAdmission] = useState<Admission | null>(null);
  const [viewingSummary, setViewingSummary] = useState<Admission | null>(null);

  // New Admission Form State
  const [patientMode, setPatientMode] = useState<"EXISTING" | "NEW">("EXISTING");
  const [patientSearchTerm, setPatientSearchTerm] = useState("");
  const [admitPatientId, setAdmitPatientId] = useState<number | undefined>(undefined);

  // New Patient Registration Fields (Inline)
  const [newPatientFirst, setNewPatientFirst] = useState("");
  const [newPatientLast, setNewPatientLast] = useState("");
  const [newPatientPhone, setNewPatientPhone] = useState("");
  const [newPatientGender, setNewPatientGender] = useState("Male");
  const [newPatientDob, setNewPatientDob] = useState("1988-06-15");
  const [newPatientBlood, setNewPatientBlood] = useState("O+");
  const [isCreatingPatient, setIsCreatingPatient] = useState(false);

  const [admitDoctorId, setAdmitDoctorId] = useState<number | undefined>(undefined);
  const [admitWardId, setAdmitWardId] = useState<number | undefined>(undefined);
  const [admitBedId, setAdmitBedId] = useState<number | undefined>(undefined);
  const [admitReason, setAdmitReason] = useState("");
  const [admitExpectedDays, setAdmitExpectedDays] = useState(3);

  // Transfer Form
  const [transferWardId, setTransferWardId] = useState<number | undefined>(undefined);
  const [transferBedId, setTransferBedId] = useState<number | undefined>(undefined);
  const [transferReason, setTransferReason] = useState("");

  // Discharge Form
  const [dischargeDiagnosis, setDischargeDiagnosis] = useState("");
  const [dischargeSummaryText, setDischargeSummaryText] = useState("");
  const [dischargeCondition, setDischargeCondition] = useState<DischargeCondition>("IMPROVED");
  const [medName, setMedName] = useState("");
  const [medDose, setMedDose] = useState("");
  const [medDuration, setMedDuration] = useState("");
  const [dischargeMeds, setDischargeMeds] = useState<Array<{ name: string; dosage: string; duration: string }>>([]);
  const [followUpNotes, setFollowUpNotes] = useState("");

  // Queries with auto-polling for real-time responsiveness
  const { data: admissions, isLoading, isError, refetch } = useQuery({
    queryKey: ["admissions", statusFilter, selectedWardFilter],
    queryFn: () =>
      ipdApi.listAdmissions({
        status: (statusFilter as AdmissionStatus) || undefined,
        ward_id: selectedWardFilter ? Number(selectedWardFilter) : undefined,
      }),
    refetchInterval: 5000,
  });

  const { data: wards, refetch: refetchWards } = useQuery({
    queryKey: ["wards"],
    queryFn: bedsApi.listWards,
    refetchInterval: 5000,
  });

  const { data: availableBedsForAdmit } = useQuery({
    queryKey: ["availableBedsForAdmit", admitWardId],
    queryFn: () => bedsApi.listBeds({ ward_id: admitWardId, status: "AVAILABLE" }),
    enabled: !!admitWardId,
    refetchInterval: 4000,
  });

  const { data: allBedsInWard } = useQuery({
    queryKey: ["allBedsInWard", admitWardId],
    queryFn: () => bedsApi.listBeds({ ward_id: admitWardId }),
    enabled: !!admitWardId,
  });

  const { data: availableBedsForTransfer } = useQuery({
    queryKey: ["availableBedsForTransfer", transferWardId],
    queryFn: () => bedsApi.listBeds({ ward_id: transferWardId, status: "AVAILABLE" }),
    enabled: !!transferWardId,
  });

  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(),
  });

  const { data: doctors } = useQuery({
    queryKey: ["doctors"],
    queryFn: () => doctorsApi.list(),
  });

  // Dynamic Bed Auto-Selection Effect for Admission
  useEffect(() => {
    if (availableBedsForAdmit && availableBedsForAdmit.length > 0) {
      if (!admitBedId || !availableBedsForAdmit.some((b) => b.id === admitBedId)) {
        setAdmitBedId(availableBedsForAdmit[0].id);
      }
    } else {
      setAdmitBedId(undefined);
    }
  }, [availableBedsForAdmit, admitWardId]);

  // Dynamic Transfer Bed Auto-Selection
  useEffect(() => {
    if (availableBedsForTransfer && availableBedsForTransfer.length > 0) {
      if (!transferBedId || !availableBedsForTransfer.some((b) => b.id === transferBedId)) {
        setTransferBedId(availableBedsForTransfer[0].id);
      }
    } else {
      setTransferBedId(undefined);
    }
  }, [availableBedsForTransfer, transferWardId]);

  // Mutations
  const createAdmissionMutation = useMutation({
    mutationFn: ipdApi.admit,
    onSuccess: (adm) => {
      queryClient.invalidateQueries({ queryKey: ["admissions"] });
      queryClient.invalidateQueries({ queryKey: ["beds"] });
      queryClient.invalidateQueries({ queryKey: ["wards"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setIsAdmitModalOpen(false);
      success("Inpatient Admitted", `Admission #${adm.admission_number} confirmed for Bed ${adm.bed_number}.`);
    },
    onError: (err: any) => {
      toastError("Admission Failed", err.response?.data?.detail || "Could not complete admission.");
    },
  });

  const transferBedMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => ipdApi.transfer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admissions"] });
      queryClient.invalidateQueries({ queryKey: ["beds"] });
      queryClient.invalidateQueries({ queryKey: ["wards"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setTransferringAdmission(null);
      success("Bed Transferred", "Patient successfully transferred to new ward bed.");
    },
    onError: (err: any) => {
      toastError("Transfer Failed", err.response?.data?.detail || "Could not transfer bed.");
    },
  });

  const dischargeMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => ipdApi.discharge(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admissions"] });
      queryClient.invalidateQueries({ queryKey: ["beds"] });
      queryClient.invalidateQueries({ queryKey: ["wards"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setDischargingAdmission(null);
      success("Patient Discharged", "Discharge summary compiled and bed freed for cleaning.");
    },
    onError: (err: any) => {
      toastError("Discharge Failed", err.response?.data?.detail || "Could not complete discharge.");
    },
  });

  // Quick Action: Free up or clean a bed in current ward
  const quickFreeBed = async () => {
    if (!allBedsInWard || allBedsInWard.length === 0) return;
    const nonAvailBed = allBedsInWard.find((b) => b.status !== "AVAILABLE") || allBedsInWard[0];
    try {
      await bedsApi.updateStatus(nonAvailBed.id, "AVAILABLE");
      await queryClient.invalidateQueries({ queryKey: ["availableBedsForAdmit"] });
      await queryClient.invalidateQueries({ queryKey: ["wards"] });
      await queryClient.invalidateQueries({ queryKey: ["beds"] });
      setAdmitBedId(nonAvailBed.id);
      success("Bed Made Available", `Bed ${nonAvailBed.bed_number} has been dynamically transitioned to AVAILABLE.`);
    } catch (err: any) {
      toastError("Bed Update Error", err.response?.data?.detail || "Failed to make bed available.");
    }
  };

  // Quick Action: Switch to first available ward
  const switchToAvailableWard = () => {
    const wardWithBeds = wards?.find((w) => w.available_beds > 0);
    if (wardWithBeds) {
      setAdmitWardId(wardWithBeds.id);
      info("Ward Switched", `Switched to ${wardWithBeds.name} with ${wardWithBeds.available_beds} available beds.`);
    }
  };

  // Open modal with smart defaults
  const handleOpenAdmitModal = () => {
    setIsAdmitModalOpen(true);
    setPatientMode("EXISTING");
    setAdmitPatientId(patients?.[0]?.id);
    setAdmitDoctorId(doctors?.[0]?.user_id);
    // Auto-pick first ward with available beds
    const wardWithBeds = wards?.find((w) => w.available_beds > 0) || wards?.[0];
    setAdmitWardId(wardWithBeds?.id);
    setAdmitReason("Post-operative recovery & continuous vital monitoring");
    setAdmitExpectedDays(3);
  };

  // Dynamic Case Auto-Filler
  const handleAutoFillDemoCase = () => {
    const sampleCases = [
      { reason: "Acute appendicitis post-laparoscopic appendectomy", days: 3 },
      { reason: "Exacerbation of acute severe asthma with respiratory distress", days: 4 },
      { reason: "Post-percutaneous coronary intervention (PCI) monitoring", days: 2 },
      { reason: "Type 2 diabetic ketoacidosis with fluid electrolyte management", days: 5 },
      { reason: "Bilateral community-acquired pneumonia on IV antibiotics", days: 6 },
    ];
    const picked = sampleCases[Math.floor(Math.random() * sampleCases.length)];
    setAdmitReason(picked.reason);
    setAdmitExpectedDays(picked.days);

    if (patients && patients.length > 0) {
      const randPatient = patients[Math.floor(Math.random() * patients.length)];
      setAdmitPatientId(randPatient.id);
    }
    if (doctors && doctors.length > 0) {
      const randDoc = doctors[Math.floor(Math.random() * doctors.length)];
      setAdmitDoctorId(randDoc.user_id);
    }
    const wardWithBeds = wards?.find((w) => w.available_beds > 0) || wards?.[0];
    if (wardWithBeds) setAdmitWardId(wardWithBeds.id);
    info("Demo Case Populated", `Loaded realistic admission scenario: ${picked.reason}`);
  };

  // Handle Admission Submission (Handles both Existing & Dynamic New Patient)
  const handleAdmissionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!admitDoctorId || !admitWardId || !admitBedId) {
      toastError("Missing Fields", "Please select attending physician, ward, and available bed.");
      return;
    }

    let finalPatientId = admitPatientId;

    if (patientMode === "NEW") {
      const fName = newPatientFirst.trim();
      const lName = newPatientLast.trim();
      const phone = newPatientPhone.trim();

      if (!fName || !/^[a-zA-Z\s\-']{2,50}$/.test(fName)) {
        toastError("Validation Error", "Patient First Name must contain alphabets only (2-50 characters).");
        return;
      }
      if (!lName || !/^[a-zA-Z\s\-']{2,50}$/.test(lName)) {
        toastError("Validation Error", "Patient Last Name must contain alphabets only (2-50 characters).");
        return;
      }
      if (!/^\d{10}$/.test(phone)) {
        toastError("Validation Error", "Patient Mobile Number must be numbers only and exactly 10 digits.");
        return;
      }
      try {
        setIsCreatingPatient(true);
        const createdPatient = await patientsApi.create({
          first_name: fName,
          last_name: lName,
          date_of_birth: newPatientDob,
          gender: newPatientGender,
          blood_group: newPatientBlood,
          phone: phone,
          email: `${fName.toLowerCase()}.${lName.toLowerCase()}@example.com`,
          address: "Metropolitan Area",
        });
        finalPatientId = createdPatient.id;
        queryClient.invalidateQueries({ queryKey: ["patients"] });
        success("New Patient Registered", `Created patient ${createdPatient.full_name} (${createdPatient.mrn})`);
      } catch (err: any) {
        toastError("Patient Registration Error", err.response?.data?.detail || "Could not create new patient record.");
        setIsCreatingPatient(false);
        return;
      } finally {
        setIsCreatingPatient(false);
      }
    }

    if (finalPatientId) {
      createAdmissionMutation.mutate({
        patient_id: finalPatientId,
        admitting_doctor_id: admitDoctorId,
        ward_id: admitWardId,
        bed_id: admitBedId,
        admission_reason: admitReason,
        expected_stay_days: admitExpectedDays,
      });
    }
  };

  const handleAddMed = () => {
    if (medName.trim() && medDose.trim()) {
      setDischargeMeds([
        ...dischargeMeds,
        { name: medName.trim(), dosage: medDose.trim(), duration: medDuration.trim() || "14 days" },
      ]);
      setMedName("");
      setMedDose("");
      setMedDuration("");
    }
  };

  // Filter admissions based on search query
  const filteredAdmissions = (admissions || []).filter((adm) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      adm.patient_name?.toLowerCase().includes(q) ||
      adm.patient_mrn?.toLowerCase().includes(q) ||
      adm.admission_number?.toLowerCase().includes(q) ||
      adm.ward_name?.toLowerCase().includes(q) ||
      adm.bed_number?.toLowerCase().includes(q) ||
      adm.doctor_name?.toLowerCase().includes(q) ||
      adm.admission_reason?.toLowerCase().includes(q)
    );
  });

  // Filter patients for dropdown search
  const filteredPatientsList = (patients || []).filter((p) => {
    if (!patientSearchTerm.trim()) return true;
    const q = patientSearchTerm.toLowerCase();
    return (
      p.full_name?.toLowerCase().includes(q) ||
      p.mrn?.toLowerCase().includes(q) ||
      p.phone?.toLowerCase().includes(q)
    );
  });

  const totalAvailableBeds = wards?.reduce((acc, w) => acc + (w.available_beds || 0), 0) || 0;
  const totalOccupiedBeds = wards?.reduce((acc, w) => acc + (w.occupied_beds || 0), 0) || 0;

  return (
    <PageContainer
      title="Inpatient Department (IPD) Admissions & Wards"
      subtitle="Comprehensive inpatient care management, dynamic bed allocations, inter-ward transfers, and clinical discharge summaries."
      badge={<Badge variant="info" dot>{admissions?.length || 0} Inpatients Active</Badge>}
      actions={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetch();
              refetchWards();
              success("Refreshed", "Inpatient and bed telemetry synchronized.");
            }}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Live Refresh
          </Button>
          <Button
            variant="glow"
            size="sm"
            onClick={handleOpenAdmitModal}
            leftIcon={<UserPlus className="w-4 h-4" />}
          >
            Admit Inpatient
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Dynamic Telemetry Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Active Inpatients</span>
              <Activity className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div className="text-xl font-black text-white mt-1">
              {admissions?.filter((a) => a.status === "ADMITTED").length || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Currently occupying hospital beds</div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Free Hospital Beds</span>
              <BedDouble className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-xl font-black text-emerald-400 mt-1">{totalAvailableBeds} Beds</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Ready for immediate intake</div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Bed Occupancy</span>
              <Building className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-xl font-black text-indigo-300 mt-1">
              {totalAvailableBeds + totalOccupiedBeds > 0
                ? `${Math.round((totalOccupiedBeds / (totalAvailableBeds + totalOccupiedBeds)) * 100)}%`
                : "0%"}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {totalOccupiedBeds} occupied / {totalAvailableBeds + totalOccupiedBeds} total
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>Discharged History</span>
              <LogOut className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-xl font-black text-amber-300 mt-1">
              {admissions?.filter((a) => a.status === "DISCHARGED").length || 0}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Completed clinical care cycles</div>
          </div>
        </div>

        {/* Dynamic Filter & Search Bar */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-md">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <span className="text-xs font-bold text-slate-300">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="ADMITTED">Active Inpatients (Admitted)</option>
                <option value="DISCHARGED">Discharged Patients</option>
                <option value="">All Admissions History</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-slate-400" />
              <select
                value={selectedWardFilter}
                onChange={(e) => setSelectedWardFilter(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="">All Hospital Wards ({wards?.length || 0})</option>
                {wards?.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name} ({w.available_beds} free beds)
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Live Search Box */}
          <div className="relative min-w-[240px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search patient, MRN, bed, doctor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
        </div>

        {/* Admissions Table */}
        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Loading Inpatient admissions..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : filteredAdmissions && filteredAdmissions.length === 0 ? (
          <EmptyState
            title="No inpatient records found"
            description={
              searchQuery
                ? `No active inpatients matching "${searchQuery}".`
                : "No active inpatients match the selected filters."
            }
            actionLabel="Admit Patient"
            onAction={handleOpenAdmitModal}
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Admission # & Date</TableHead>
                <TableHead>Patient Details</TableHead>
                <TableHead>Ward & Bed Number</TableHead>
                <TableHead>Attending Physician</TableHead>
                <TableHead>Admission Reason</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAdmissions.map((adm) => (
                <TableRow key={adm.id}>
                  <TableCell>
                    <div className="font-mono text-xs font-bold text-sky-400">{adm.admission_number}</div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {new Date(adm.admission_date).toLocaleDateString()}
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="font-bold text-white text-xs">{adm.patient_name}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{adm.patient_mrn}</div>
                  </TableCell>

                  <TableCell className="text-xs text-slate-300">
                    <div className="font-semibold text-white">{adm.ward_name}</div>
                    <span className="inline-block text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 mt-0.5">
                      Bed: {adm.bed_number}
                    </span>
                  </TableCell>

                  <TableCell className="text-xs text-slate-300">
                    {adm.doctor_name}
                  </TableCell>

                  <TableCell className="text-xs text-slate-300 max-w-xs truncate">
                    {adm.admission_reason}
                  </TableCell>

                  <TableCell>
                    <Badge variant={adm.status === "ADMITTED" ? "success" : "neutral"} dot={adm.status === "ADMITTED"}>
                      {adm.status}
                    </Badge>
                  </TableCell>

                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {adm.status === "ADMITTED" ? (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setTransferringAdmission(adm);
                              const targetWard = wards?.find((w) => w.id !== adm.ward_id && w.available_beds > 0) || wards?.[0];
                              setTransferWardId(targetWard?.id);
                            }}
                            title="Transfer Bed"
                            leftIcon={<ArrowRightLeft className="w-3.5 h-3.5" />}
                          >
                            Transfer
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => {
                              setDischargingAdmission(adm);
                              setDischargeDiagnosis(adm.admission_reason);
                              setDischargeSummaryText("");
                              setDischargeMeds([]);
                            }}
                            title="Process Discharge"
                            leftIcon={<LogOut className="w-3.5 h-3.5" />}
                          >
                            Discharge
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setViewingSummary(adm)}
                          leftIcon={<FileText className="w-3.5 h-3.5" />}
                        >
                          Summary
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Dynamic Admit Inpatient Modal */}
      <Modal
        isOpen={isAdmitModalOpen}
        onClose={() => setIsAdmitModalOpen(false)}
        title="Admit Patient to Inpatient Ward (IPD)"
        description="Dynamic admission intake, auto-bed assignment, and instant patient onboarding."
        maxWidth="lg"
      >
        <form onSubmit={handleAdmissionSubmit} className="space-y-4 pt-1">
          {/* Quick Demo Helper & Mode Switcher */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => setPatientMode("EXISTING")}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                  patientMode === "EXISTING"
                    ? "bg-sky-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Existing Patient
              </button>
              <button
                type="button"
                onClick={() => setPatientMode("NEW")}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
                  patientMode === "NEW"
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Plus className="w-3.5 h-3.5" />
                New Patient Intake
              </button>
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAutoFillDemoCase}
              leftIcon={<Sparkles className="w-3.5 h-3.5 text-amber-400" />}
            >
              Auto-Fill Demo
            </Button>
          </div>

          {/* Patient Selection or Registration */}
          {patientMode === "EXISTING" ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Select Registered Patient *
                </label>
                <span className="text-[11px] text-slate-400">
                  {filteredPatientsList.length} patients found
                </span>
              </div>

              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter patients by name, MRN, phone..."
                  value={patientSearchTerm}
                  onChange={(e) => setPatientSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <select
                value={admitPatientId || ""}
                onChange={(e) => setAdmitPatientId(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                required
              >
                {filteredPatientsList.length > 0 ? (
                  filteredPatientsList.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} ({p.mrn}) • Phone: {p.phone} • Age: {p.age || "Adult"}
                    </option>
                  ))
                ) : (
                  <option value="">No matching patients found. Click 'New Patient Intake' above.</option>
                )}
              </select>
            </div>
          ) : (
            <div className="p-3.5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 space-y-3">
              <div className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                <User className="w-4 h-4" />
                <span>Fast Patient Intake & Onboarding</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  label="First Name (Alphabets only) *"
                  placeholder="e.g. David"
                  value={newPatientFirst}
                  maxLength={50}
                  pattern="^[A-Za-z\s\-']{2,50}$"
                  title="First name must contain alphabets only (min 2 characters)"
                  onChange={(e) => setNewPatientFirst(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                  required
                />
                <Input
                  label="Last Name (Alphabets only) *"
                  placeholder="e.g. Miller"
                  value={newPatientLast}
                  maxLength={50}
                  pattern="^[A-Za-z\s\-']{2,50}$"
                  title="Last name must contain alphabets only (min 2 characters)"
                  onChange={(e) => setNewPatientLast(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                  required
                />
              </div>
              <div className="grid grid-cols-3 gap-2">
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
                <Select
                  label="Gender"
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
                    { value: "AB+", label: "AB+" },
                  ]}
                  value={newPatientBlood}
                  onChange={(e) => setNewPatientBlood(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Attending Doctor & Clinical Ward */}
          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Attending / Admitting Doctor *"
              options={
                doctors?.map((doc) => ({
                  value: doc.user_id,
                  label: `${doc.full_name} (${doc.specialization})`,
                })) || []
              }
              value={admitDoctorId}
              onChange={(e) => setAdmitDoctorId(Number(e.target.value))}
            />

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Inpatient Ward *
              </label>
              <select
                value={admitWardId || ""}
                onChange={(e) => setAdmitWardId(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                required
              >
                {wards?.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name} — {w.available_beds > 0 ? `🟢 ${w.available_beds} Free Beds` : "🔴 Full (0 Free)"}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Dynamic Available Bed Selection & Auto-Rescue */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Select Available Bed *
              </label>
              {availableBedsForAdmit && availableBedsForAdmit.length > 0 && (
                <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {availableBedsForAdmit.length} beds ready
                </span>
              )}
            </div>

            {availableBedsForAdmit && availableBedsForAdmit.length > 0 ? (
              <select
                value={admitBedId || ""}
                onChange={(e) => setAdmitBedId(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                required
              >
                {availableBedsForAdmit.map((b) => (
                  <option key={b.id} value={b.id}>
                    Bed {b.bed_number} {b.has_ventilator ? "• [Ventilator]" : "• [High-Flow O2]"}
                  </option>
                ))}
              </select>
            ) : (
              <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs text-rose-300 space-y-2">
                <div className="flex items-center gap-2 font-bold text-rose-200">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>No available beds in this ward.</span>
                </div>
                <p className="text-[11px] text-slate-300">
                  All beds in this unit are currently occupied or undergoing sanitation.
                </p>
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  {wards && wards.some((w) => w.available_beds > 0) && (
                    <Button
                      type="button"
                      variant="glow"
                      size="sm"
                      onClick={switchToAvailableWard}
                      leftIcon={<Zap className="w-3.5 h-3.5" />}
                    >
                      ⚡ Switch to Ward with Free Beds
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={quickFreeBed}
                    leftIcon={<Sparkles className="w-3.5 h-3.5 text-sky-400" />}
                  >
                    ✨ Quick-Free a Bed in this Ward
                  </Button>
                </div>
              </div>
            )}
          </div>

          <Input
            label="Admission Reason / Clinical Indication *"
            placeholder="e.g. Post-operative recovery following laparoscopic cholecystectomy"
            value={admitReason}
            onChange={(e) => setAdmitReason(e.target.value)}
            required
          />

          <Input
            label="Expected Stay (Days) *"
            type="number"
            value={admitExpectedDays}
            onChange={(e) => setAdmitExpectedDays(Number(e.target.value))}
            required
          />

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button type="button" variant="ghost" size="sm" onClick={() => setIsAdmitModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="glow"
              size="sm"
              disabled={!admitBedId || isCreatingPatient}
              isLoading={createAdmissionMutation.isPending || isCreatingPatient}
              leftIcon={<CheckCircle2 className="w-4 h-4" />}
            >
              {patientMode === "NEW" ? "Register & Admit Inpatient" : "Confirm Inpatient Admission"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Bed Transfer Modal */}
      {transferringAdmission && (
        <Modal
          isOpen={!!transferringAdmission}
          onClose={() => setTransferringAdmission(null)}
          title={`Transfer Bed • ${transferringAdmission.patient_name}`}
          description={`Currently in ${transferringAdmission.ward_name} (Bed: ${transferringAdmission.bed_number})`}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (transferBedId) {
                transferBedMutation.mutate({
                  id: transferringAdmission.id,
                  data: {
                    to_bed_id: transferBedId,
                    transfer_reason: transferReason,
                  },
                });
              }
            }}
            className="space-y-4 pt-2"
          >
            <Select
              label="Destination Ward *"
              options={
                wards?.map((w) => ({
                  value: w.id,
                  label: `${w.name} (${w.available_beds} free)`,
                })) || []
              }
              value={transferWardId}
              onChange={(e) => setTransferWardId(Number(e.target.value))}
            />

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Destination Bed *
              </label>
              {availableBedsForTransfer && availableBedsForTransfer.length > 0 ? (
                <select
                  value={transferBedId || ""}
                  onChange={(e) => setTransferBedId(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                  required
                >
                  <option value="">Choose Bed...</option>
                  {availableBedsForTransfer.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.bed_number}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/30 text-xs text-rose-300">
                  No beds available in selected destination ward.
                </div>
              )}
            </div>

            <Input
              label="Clinical Reason for Transfer *"
              placeholder="e.g. Patient stabilized; transferred from CCU to Step-Down Ward"
              value={transferReason}
              onChange={(e) => setTransferReason(e.target.value)}
              required
            />

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setTransferringAdmission(null)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="glow"
                size="sm"
                disabled={!transferBedId}
                isLoading={transferBedMutation.isPending}
              >
                Execute Bed Transfer
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Discharge Patient Modal */}
      {dischargingAdmission && (
        <Modal
          isOpen={!!dischargingAdmission}
          onClose={() => setDischargingAdmission(null)}
          title={`Discharge Summary • ${dischargingAdmission.patient_name}`}
          description={`Admission #${dischargingAdmission.admission_number} • Bed: ${dischargingAdmission.bed_number}`}
          maxWidth="lg"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              dischargeMutation.mutate({
                id: dischargingAdmission.id,
                data: {
                  discharge_diagnosis: dischargeDiagnosis,
                  discharge_summary: dischargeSummaryText,
                  discharge_condition: dischargeCondition,
                  discharge_medications: dischargeMeds,
                  follow_up_instructions: followUpNotes,
                },
              });
            }}
            className="space-y-4 max-h-[75vh] overflow-y-auto pr-1"
          >
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Final Discharge Diagnosis *"
                placeholder="e.g. Acute Coronary Syndrome (STEMI), revascularized"
                value={dischargeDiagnosis}
                onChange={(e) => setDischargeDiagnosis(e.target.value)}
                required
              />

              <Select
                label="Discharge Clinical Condition *"
                options={[
                  { value: "RECOVERED", label: "RECOVERED (Fully resolved)" },
                  { value: "IMPROVED", label: "IMPROVED (Clinically stable)" },
                  { value: "STABLE", label: "STABLE" },
                  { value: "TRANSFERRED_EXTERNAL", label: "Transferred to Tertiary Center" },
                  { value: "AGAINST_MEDICAL_ADVICE", label: "Discharged Against Medical Advice (DAMA)" },
                ]}
                value={dischargeCondition}
                onChange={(e) => setDischargeCondition(e.target.value as DischargeCondition)}
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Hospital Course & Discharge Clinical Summary *
              </label>
              <textarea
                rows={3}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                placeholder="Detail hospital clinical trajectory, interventions performed, and recovery..."
                value={dischargeSummaryText}
                onChange={(e) => setDischargeSummaryText(e.target.value)}
                required
              />
            </div>

            {/* Discharge Medications Builder */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                Discharge Medication Prescriptions
              </h4>
              <div className="grid grid-cols-3 gap-2">
                <Input
                  placeholder="Medication (e.g. Atorvastatin 40mg)"
                  value={medName}
                  onChange={(e) => setMedName(e.target.value)}
                />
                <Input
                  placeholder="Dosage (e.g. 1 tab PO OD in evening)"
                  value={medDose}
                  onChange={(e) => setMedDose(e.target.value)}
                />
                <Input
                  placeholder="Duration (e.g. 30 days)"
                  value={medDuration}
                  onChange={(e) => setMedDuration(e.target.value)}
                />
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handleAddMed} leftIcon={<Plus className="w-3 h-3" />}>
                Add Medication
              </Button>

              <div className="space-y-1 pt-1">
                {dischargeMeds.map((m, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200">
                    <span><strong>{m.name}</strong> — {m.dosage} ({m.duration})</span>
                    <button
                      type="button"
                      onClick={() => setDischargeMeds(dischargeMeds.filter((_, i) => i !== idx))}
                      className="text-slate-400 hover:text-rose-400"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <Input
              label="Follow-up Instructions & Appointments"
              placeholder="e.g. Cardiology OPD in 2 weeks with repeat lipid panel"
              value={followUpNotes}
              onChange={(e) => setFollowUpNotes(e.target.value)}
            />

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setDischargingAdmission(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="secondary" size="sm" isLoading={dischargeMutation.isPending}>
                Complete Discharge & Free Bed
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* View Historical Discharge Summary Modal */}
      {viewingSummary && (
        <Modal
          isOpen={!!viewingSummary}
          onClose={() => setViewingSummary(null)}
          title={`Discharge Summary • ${viewingSummary.patient_name}`}
          description={`Admission #${viewingSummary.admission_number} • Discharged on ${viewingSummary.discharge_date ? new Date(viewingSummary.discharge_date).toLocaleDateString() : 'N/A'}`}
        >
          <div className="space-y-3 pt-2 text-xs text-slate-300">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400 block font-semibold">Diagnosis:</span>
              <span className="text-white font-bold">{viewingSummary.discharge_diagnosis || "N/A"}</span>
              <span className="text-slate-400 block font-semibold mt-2">Condition:</span>
              <Badge variant="success">{viewingSummary.discharge_condition || "STABLE"}</Badge>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-slate-400 block font-semibold">Clinical Course:</span>
              <p className="mt-1 text-slate-200">{viewingSummary.discharge_summary || "No summary recorded."}</p>
            </div>

            {viewingSummary.follow_up_instructions && (
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400 block font-semibold">Follow-up:</span>
                <p className="mt-1 text-slate-200">{viewingSummary.follow_up_instructions}</p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </PageContainer>
  );
};
