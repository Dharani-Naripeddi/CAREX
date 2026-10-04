import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tokensApi, departmentsApi, patientsApi } from "../services/api";
import { PageContainer } from "../components/layout/PageContainer";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { Select } from "../components/ui/Select";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { useToast } from "../hooks/useToast";
import {
  Users,
  Clock,
  Volume2,
  CheckCircle2,
  Building,
  Plus,
  Play,
  RotateCcw,
  UserPlus,
  Search,
  User,
  Sparkles,
} from "lucide-react";

export const OpdQueuePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [selectedDeptId, setSelectedDeptId] = useState<number | undefined>(undefined);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);

  // Modal Mode: "NEW_PATIENT" vs "EXISTING_PATIENT"
  const [modalMode, setModalMode] = useState<"NEW_PATIENT" | "EXISTING_PATIENT">("NEW_PATIENT");

  // New Patient Form State
  const [patientFirstName, setPatientFirstName] = useState("");
  const [patientLastName, setPatientLastName] = useState("");
  const [patientPhone, setPatientPhone] = useState("");
  const [patientGender, setPatientGender] = useState("Male");
  const [patientDob, setPatientDob] = useState("1996-03-20");

  // Existing Patient State
  const [patientSearch, setPatientSearch] = useState("");
  const [newPatientId, setNewPatientId] = useState<number | undefined>(undefined);
  const [newPriority, setNewPriority] = useState("NORMAL");
  const [isIssuing, setIsIssuing] = useState(false);

  // Queries
  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.list,
  });

  const { data: queueData, isLoading, refetch } = useQuery({
    queryKey: ["tokenQueue", selectedDeptId],
    queryFn: () => tokensApi.getQueue({ department_id: selectedDeptId }),
    refetchInterval: 5000, // Live poll every 5s for hospital queue display
  });

  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(),
  });

  // Filter existing patients
  const filteredPatients = (patients || []).filter((p) => {
    if (!patientSearch.trim()) return true;
    const q = patientSearch.toLowerCase();
    return (
      p.full_name?.toLowerCase().includes(q) ||
      p.mrn?.toLowerCase().includes(q) ||
      p.phone?.toLowerCase().includes(q)
    );
  });

  const callTokenMutation = useMutation({
    mutationFn: (tokenId: number) => tokensApi.call(tokenId),
    onSuccess: (tok) => {
      queryClient.invalidateQueries({ queryKey: ["tokenQueue"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      success("Patient Called", `Now paging token ${tok.token_code} to consultation room.`);
    },
    onError: (err: any) => {
      toastError("Call Failed", err.response?.data?.detail || "Could not page token.");
    },
  });

  const completeTokenMutation = useMutation({
    mutationFn: (tokenId: number) => tokensApi.complete(tokenId),
    onSuccess: (tok) => {
      queryClient.invalidateQueries({ queryKey: ["tokenQueue"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      success("Consultation Completed", `Token ${tok.token_code} serviced successfully.`);
    },
    onError: (err: any) => {
      toastError("Completion Failed", err.response?.data?.detail || "Could not complete token.");
    },
  });

  const handleIssueToken = async (e: React.FormEvent) => {
    e.preventDefault();
    const targetDeptId = selectedDeptId || departments?.[0]?.id;
    if (!targetDeptId) {
      toastError("Error", "Please select a department.");
      return;
    }

    setIsIssuing(true);
    try {
      let targetPatientId = newPatientId;

      if (modalMode === "NEW_PATIENT") {
        const fName = patientFirstName.trim();
        const lName = patientLastName.trim();
        const phone = patientPhone.trim();

        if (!fName || !/^[a-zA-Z\s\-']{2,50}$/.test(fName)) {
          toastError("Validation Error", "Patient First Name must contain alphabets only (2-50 characters).");
          setIsIssuing(false);
          return;
        }
        if (!lName || !/^[a-zA-Z\s\-']{2,50}$/.test(lName)) {
          toastError("Validation Error", "Patient Last Name must contain alphabets only (2-50 characters).");
          setIsIssuing(false);
          return;
        }
        if (!/^\d{10}$/.test(phone)) {
          toastError("Validation Error", "Patient Mobile Number must be numbers only and exactly 10 digits.");
          setIsIssuing(false);
          return;
        }

        // Register patient dynamically
        const newPat = await patientsApi.create({
          first_name: fName,
          last_name: lName,
          phone: phone,
          date_of_birth: patientDob,
          gender: patientGender,
          blood_group: "O+",
        });
        targetPatientId = newPat.id;
      }

      if (!targetPatientId) {
        toastError("Error", "No patient selected.");
        setIsIssuing(false);
        return;
      }

      const tok = await tokensApi.generate({
        patient_id: targetPatientId,
        department_id: targetDeptId,
        priority: newPriority,
      });

      queryClient.invalidateQueries({ queryKey: ["tokenQueue"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });

      success("Token Issued", `OPD Token ${tok.token_code} issued successfully. Estimated wait: ~${tok.estimated_wait_minutes} mins.`);
      setIsGenerateModalOpen(false);

      // Reset
      setPatientFirstName("");
      setPatientLastName("");
      setPatientPhone("");
    } catch (err: any) {
      toastError("Issue Failed", err.response?.data?.detail || "Could not issue token.");
    } finally {
      setIsIssuing(false);
    }
  };

  const currentCalled = queueData?.waiting_tokens.find(
    (t) => t.status === "CALLED" || t.status === "IN_ROOM"
  );

  return (
    <PageContainer
      title="OPD Live Queue & Patient Token System"
      subtitle="Real-time outpatient tokens, waiting queue telemetry, and digital consultation calling."
      badge={<Badge variant="success" dot>Live Telemetry (5s auto-sync)</Badge>}
      actions={
        <Button
          variant="glow"
          size="sm"
          onClick={() => {
            setIsGenerateModalOpen(true);
            if (patients && patients.length > 0) {
              setNewPatientId(patients[0].id);
            }
          }}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Issue Walk-in Token
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Department Queue Selector */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-4 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-sky-400" />
            <span className="text-xs font-bold text-slate-300">Department Queue Board:</span>
            <select
              value={selectedDeptId || ""}
              onChange={(e) => setSelectedDeptId(e.target.value ? Number(e.target.value) : undefined)}
              className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Hospital Departments</option>
              {departments?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-sky-400" />
              Total in Queue: <strong className="text-white">{queueData?.total_in_queue || 0}</strong>
            </span>
            <Button variant="ghost" size="sm" onClick={() => refetch()} leftIcon={<RotateCcw className="w-3 h-3" />}>
              Refresh
            </Button>
          </div>
        </div>

        {/* Live Call Center Hero Banner */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1 p-6 rounded-2xl bg-gradient-to-br from-sky-950/40 via-slate-900/80 to-slate-950 border-2 border-sky-500/40 shadow-xl flex flex-col justify-between items-center text-center relative overflow-hidden">
            <div className="absolute top-3 right-3">
              <span className="flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-widest text-sky-400 flex items-center justify-center gap-1.5">
                <Volume2 className="w-4 h-4 text-sky-400 animate-pulse" />
                NOW CALLING / IN ROOM
              </span>
              <p className="text-xs text-slate-400">{queueData?.department_name}</p>
            </div>

            <div className="my-4">
              <div className="text-5xl font-extrabold font-mono text-white tracking-wider drop-shadow-md">
                {currentCalled ? currentCalled.token_code : "---"}
              </div>
              {currentCalled && (
                <div className="mt-2 text-xs font-semibold text-sky-300">
                  {currentCalled.patient_name} ({currentCalled.patient_mrn})
                </div>
              )}
            </div>

            {currentCalled ? (
              <Button
                variant="secondary"
                size="sm"
                className="w-full"
                onClick={() => completeTokenMutation.mutate(currentCalled.id)}
                isLoading={completeTokenMutation.isPending}
                leftIcon={<CheckCircle2 className="w-4 h-4" />}
              >
                Complete Consultation
              </Button>
            ) : (
              <p className="text-[11px] text-slate-500">Consultation room ready for next patient.</p>
            )}
          </div>

          {/* Waiting Queue List */}
          <div className="md:col-span-2 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
              <span>Waiting Patients Queue ({queueData?.waiting_tokens.length || 0})</span>
              <span className="text-[10px] text-slate-500 font-normal">Sorted by sequence & priority</span>
            </h3>

            {isLoading ? (
              <div className="py-12">
                <LoadingSpinner size="md" label="Updating live queue..." />
              </div>
            ) : queueData?.waiting_tokens && queueData.waiting_tokens.length === 0 ? (
              <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
                No patients currently waiting in this department queue.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[460px] overflow-y-auto pr-1">
                {queueData?.waiting_tokens.map((token) => (
                  <Card
                    key={token.id}
                    hoverable
                    className={`p-3.5 transition-all ${
                      token.status === "CALLED"
                        ? "border-sky-500/60 bg-sky-950/20"
                        : "hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-sm text-sky-400">
                          #{token.token_number}
                        </div>
                        <div>
                          <div className="font-bold text-white text-xs font-mono">{token.token_code}</div>
                          <div className="text-[11px] text-slate-300 font-semibold truncate max-w-[120px]">
                            {token.patient_name}
                          </div>
                        </div>
                      </div>

                      {token.priority === "STAT" ? (
                        <Badge variant="critical">STAT</Badge>
                      ) : token.priority === "URGENT" ? (
                        <Badge variant="warning">URGENT</Badge>
                      ) : (
                        <Badge variant="neutral">Normal</Badge>
                      )}
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-sky-400" />
                        ~{token.estimated_wait_minutes} min wait
                      </span>

                      {token.status === "ISSUED" ? (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => callTokenMutation.mutate(token.id)}
                          isLoading={callTokenMutation.isPending}
                          leftIcon={<Play className="w-3 h-3" />}
                        >
                          Call Patient
                        </Button>
                      ) : token.status === "CALLED" ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => completeTokenMutation.mutate(token.id)}
                          isLoading={completeTokenMutation.isPending}
                          leftIcon={<CheckCircle2 className="w-3 h-3" />}
                        >
                          Complete
                        </Button>
                      ) : (
                        <Badge variant="success">Serviced</Badge>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dynamic Generate Walk-in Token Modal */}
      <Modal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        title="Issue Walk-in OPD Token"
        description="Generates daily sequential token code with real-time wait telemetry."
        maxWidth="lg"
      >
        <form onSubmit={handleIssueToken} className="space-y-4 pt-2">
          {/* Mode Switcher */}
          <div className="p-1 rounded-xl bg-slate-950 border border-slate-800 grid grid-cols-2 gap-1">
            <button
              type="button"
              onClick={() => setModalMode("NEW_PATIENT")}
              className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                modalMode === "NEW_PATIENT"
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <UserPlus className="w-4 h-4" />
              <span>Direct Walk-in Intake</span>
            </button>
            <button
              type="button"
              onClick={() => setModalMode("EXISTING_PATIENT")}
              className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                modalMode === "EXISTING_PATIENT"
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Search className="w-4 h-4" />
              <span>Search Registered Patients</span>
            </button>
          </div>

          {modalMode === "NEW_PATIENT" ? (
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="First Name (Alphabets only) *"
                  placeholder="e.g. John"
                  value={patientFirstName}
                  maxLength={50}
                  pattern="^[A-Za-z\s\-']{2,50}$"
                  title="First name must contain alphabets only (min 2 characters)"
                  onChange={(e) => setPatientFirstName(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                  required
                />
                <Input
                  label="Last Name (Alphabets only) *"
                  placeholder="e.g. Doe"
                  value={patientLastName}
                  maxLength={50}
                  pattern="^[A-Za-z\s\-']{2,50}$"
                  title="Last name must contain alphabets only (min 2 characters)"
                  onChange={(e) => setPatientLastName(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
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
                  value={patientPhone}
                  helperText={patientPhone ? `${patientPhone.length}/10 digits ${patientPhone.length === 10 ? "✓" : ""}` : "Numbers only, 10 digits"}
                  onChange={(e) => setPatientPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                  required
                />
                <Select
                  label="Gender *"
                  options={[
                    { value: "Male", label: "Male" },
                    { value: "Female", label: "Female" },
                    { value: "Other", label: "Other" },
                  ]}
                  value={patientGender}
                  onChange={(e) => setPatientGender(e.target.value)}
                />
              </div>
            </div>
          ) : (
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search patient by name, MRN, phone..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <select
                  value={newPatientId}
                  onChange={(e) => setNewPatientId(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                  required
                >
                  {filteredPatients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} ({p.mrn}) • Phone: {p.phone}
                    </option>
                  ))}
                  {filteredPatients.length === 0 && (
                    <option disabled value="">
                      No patients found. Switch to Direct Walk-in Intake.
                    </option>
                  )}
                </select>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Department *"
              options={
                departments?.map((d) => ({
                  value: d.id,
                  label: d.name,
                })) || []
              }
              value={selectedDeptId || departments?.[0]?.id}
              onChange={(e) => setSelectedDeptId(Number(e.target.value))}
            />

            <Select
              label="Priority Triage *"
              options={[
                { value: "NORMAL", label: "Normal (Standard Walk-in)" },
                { value: "URGENT", label: "Urgent (Priority fast-track)" },
                { value: "STAT", label: "STAT / Immediate Resuscitation" },
              ]}
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button type="button" variant="ghost" size="sm" onClick={() => setIsGenerateModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="glow"
              size="sm"
              isLoading={isIssuing}
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Issue Walk-in Token
            </Button>
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
};

