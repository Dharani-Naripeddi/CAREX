import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { emergencyApi, patientsApi, doctorsApi, nursesApi, ipdApi, bedsApi } from "../services/api";
import {
  EmergencyCase,
  EmergencyCaseCreatePayload,
  TriageLevel,
  ConsciousnessLevel,
  EmergencyCaseStatus,
} from "../types/emergency_ipd";
import { PageContainer } from "../components/layout/PageContainer";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/Table";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Badge } from "../components/ui/Badge";
import { Modal } from "../components/ui/Modal";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { useToast } from "../hooks/useToast";
import {
  AlertTriangle,
  HeartPulse,
  Activity,
  BedDouble,
  Clock,
  ShieldAlert,
  UserPlus,
  Stethoscope,
  Filter,
  Eye,
  CheckCircle2,
  ChevronRight,
  Flame,
} from "lucide-react";

export const EmergencyPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [selectedTriageFilter, setSelectedTriageFilter] = useState<string>("");
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>("");

  // Modals
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [viewingCase, setViewingCase] = useState<EmergencyCase | null>(null);
  const [admittingCase, setAdmittingCase] = useState<EmergencyCase | null>(null);

  // Form State for Emergency Registration
  const [formData, setFormData] = useState<EmergencyCaseCreatePayload>({
    patient_name: "",
    age: 45,
    gender: "Male",
    symptoms: "",
    injury_type: "",
    heart_rate: 110,
    bp_systolic: 120,
    bp_diastolic: 80,
    spo2: 95.0,
    temperature: 37.0,
    respiratory_rate: 20,
    consciousness: "ALERT",
  });

  // Admission Modal State
  const [selectedWardId, setSelectedWardId] = useState<number | undefined>(undefined);
  const [selectedBedId, setSelectedBedId] = useState<number | undefined>(undefined);
  const [selectedDocId, setSelectedDocId] = useState<number | undefined>(undefined);
  const [expectedDays, setExpectedDays] = useState<number>(3);

  // Queries
  const { data: cases, isLoading, isError, refetch } = useQuery({
    queryKey: ["emergencyCases", selectedStatusFilter, selectedTriageFilter],
    queryFn: () =>
      emergencyApi.list({
        status: (selectedStatusFilter as EmergencyCaseStatus) || undefined,
        triage_level: (selectedTriageFilter as TriageLevel) || undefined,
      }),
    refetchInterval: 5000, // Live poll every 5s
  });

  const { data: wards } = useQuery({
    queryKey: ["wards"],
    queryFn: bedsApi.listWards,
  });

  const { data: availableBeds } = useQuery({
    queryKey: ["availableBeds", selectedWardId],
    queryFn: () => bedsApi.listBeds({ ward_id: selectedWardId, status: "AVAILABLE" }),
    enabled: !!selectedWardId,
  });

  const { data: doctors } = useQuery({
    queryKey: ["doctors"],
    queryFn: () => doctorsApi.list(),
  });

  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(),
  });

  // Mutations
  const createEmergencyMutation = useMutation({
    mutationFn: emergencyApi.create,
    onSuccess: (newCase) => {
      queryClient.invalidateQueries({ queryKey: ["emergencyCases"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setIsRegisterModalOpen(false);
      setViewingCase(newCase);
      success(
        `Emergency Registered (${newCase.triage_level})`,
        `Case #${newCase.case_number} registered with Priority Level ${newCase.triage_level}.`
      );
    },
    onError: (err: any) => {
      toastError("Registration Failed", err.response?.data?.detail || "Could not register emergency case.");
    },
  });

  const admitEmergencyMutation = useMutation({
    mutationFn: ipdApi.admit,
    onSuccess: (adm) => {
      queryClient.invalidateQueries({ queryKey: ["emergencyCases"] });
      queryClient.invalidateQueries({ queryKey: ["admissions"] });
      queryClient.invalidateQueries({ queryKey: ["beds"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setAdmittingCase(null);
      success("Patient Admitted to IPD", `Admission #${adm.admission_number} confirmed for Bed ${adm.bed_number}.`);
    },
    onError: (err: any) => {
      toastError("Admission Failed", err.response?.data?.detail || "Could not admit patient to IPD.");
    },
  });

  const getTriageBadge = (level: TriageLevel) => {
    switch (level) {
      case "RED":
        return <Badge variant="critical" dot>LEVEL 1 • RED (STAT)</Badge>;
      case "ORANGE":
        return <Badge variant="warning" dot>LEVEL 2 • ORANGE</Badge>;
      case "YELLOW":
        return <Badge variant="warning">LEVEL 3 • YELLOW</Badge>;
      case "GREEN":
        return <Badge variant="success">LEVEL 4 • GREEN</Badge>;
    }
  };

  return (
    <PageContainer
      title="Emergency Department & Acute Triage Center"
      subtitle="Rapid emergency intake, real-time vital signs capture, transparent rule-based triage decision support, and immediate bed allocations."
      badge={<Badge variant="critical" dot>{cases?.length || 0} Emergency Cases</Badge>}
      actions={
        <Button
          variant="destructive"
          size="sm"
          onClick={() => {
            setIsRegisterModalOpen(true);
            setSelectedDocId(doctors?.[0]?.user_id);
          }}
          leftIcon={<AlertTriangle className="w-4 h-4" />}
        >
          Register Emergency Patient
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Triage Protocol Info Banner */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-md flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400 shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Transparent Rule-Based Triage Protocol Active (ESI / MTS Standards)
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                AI decision support only. Final clinical decision must be made by qualified healthcare professionals.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedTriageFilter}
              onChange={(e) => setSelectedTriageFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-rose-500"
            >
              <option value="">All Triage Levels</option>
              <option value="RED">RED (Immediate Resuscitation)</option>
              <option value="ORANGE">ORANGE (Emergent - 10m)</option>
              <option value="YELLOW">YELLOW (Urgent - 30m)</option>
              <option value="GREEN">GREEN (Non-Urgent)</option>
            </select>

            <select
              value={selectedStatusFilter}
              onChange={(e) => setSelectedStatusFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-rose-500"
            >
              <option value="">All Case Statuses</option>
              <option value="TRIAGED">Triaged / Active</option>
              <option value="ADMITTED_IPD">Admitted to IPD</option>
              <option value="DISCHARGED">Discharged</option>
            </select>
          </div>
        </div>

        {/* Emergency Cases Table */}
        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Connecting to Emergency telemetry..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : cases && cases.length === 0 ? (
          <EmptyState
            title="No emergency cases currently active"
            description="Emergency resuscitation bays are currently available."
            actionLabel="Register Emergency Patient"
            onAction={() => setIsRegisterModalOpen(true)}
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Case # & Arrival</TableHead>
                <TableHead>Patient Details</TableHead>
                <TableHead>Triage Priority</TableHead>
                <TableHead>Physiological Vitals</TableHead>
                <TableHead>Presenting Symptoms</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cases?.map((c) => (
                <TableRow
                  key={c.id}
                  className={c.triage_level === "RED" ? "bg-rose-950/15 hover:bg-rose-950/25" : undefined}
                >
                  <TableCell>
                    <div className="font-mono text-xs font-bold text-rose-400">{c.case_number}</div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {new Date(c.arrival_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="font-bold text-white text-xs">{c.patient_name}</div>
                    <div className="text-[10px] text-slate-400">{c.age}y • {c.gender}</div>
                  </TableCell>

                  <TableCell>{getTriageBadge(c.triage_level)}</TableCell>

                  <TableCell className="text-xs text-slate-300 font-mono">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-bold ${c.spo2 < 90 ? "text-rose-400 animate-pulse" : "text-sky-400"}`}
                      >
                        SpO2: {c.spo2}%
                      </span>
                      <span>•</span>
                      <span className={c.heart_rate > 130 ? "text-rose-400 font-bold" : "text-slate-300"}>
                        HR: {c.heart_rate}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      BP: {c.bp_systolic}/{c.bp_diastolic} • {c.consciousness}
                    </div>
                  </TableCell>

                  <TableCell className="text-xs text-slate-300 max-w-xs">
                    <div className="truncate font-medium text-white">{c.symptoms}</div>
                    {c.injury_type && (
                      <div className="text-[10px] text-amber-400 truncate mt-0.5">{c.injury_type}</div>
                    )}
                  </TableCell>

                  <TableCell>
                    <Badge variant={c.status === "ADMITTED_IPD" ? "info" : c.status === "DISCHARGED" ? "success" : "warning"}>
                      {c.status}
                    </Badge>
                  </TableCell>

                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setViewingCase(c)}
                        title="View Triage Decision Support"
                        leftIcon={<Eye className="w-3.5 h-3.5" />}
                      >
                        Triage
                      </Button>

                      {c.status !== "ADMITTED_IPD" && c.status !== "DISCHARGED" && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => {
                            setAdmittingCase(c);
                            setSelectedWardId(wards?.[0]?.id);
                            setSelectedDocId(doctors?.[0]?.user_id);
                          }}
                          title="Admit to Inpatient Bed"
                          leftIcon={<BedDouble className="w-3.5 h-3.5" />}
                        >
                          Admit
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

      {/* Emergency Registration Modal */}
      <Modal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        title="Emergency Case Intake & Triage Registration"
        description="Captures vital signs and computes transparent rule-based triage priority."
        maxWidth="xl"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createEmergencyMutation.mutate(formData);
          }}
          className="space-y-4 max-h-[75vh] overflow-y-auto pr-1"
        >
          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Patient Name *"
              placeholder="e.g. Marcus Vance"
              value={formData.patient_name}
              onChange={(e) => setFormData({ ...formData, patient_name: e.target.value })}
              required
            />
            <Input
              label="Age *"
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: Number(e.target.value) })}
              required
            />
            <Select
              label="Gender *"
              options={[
                { value: "Male", label: "Male" },
                { value: "Female", label: "Female" },
                { value: "Other", label: "Other" },
              ]}
              value={formData.gender}
              onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Presenting Symptoms *"
              placeholder="e.g. Acute chest tightness, diaphoresis, dyspnea"
              value={formData.symptoms}
              onChange={(e) => setFormData({ ...formData, symptoms: e.target.value })}
              required
            />
            <Input
              label="Injury / Trauma Type"
              placeholder="e.g. Blunt Chest Trauma, Compound Fracture, None"
              value={formData.injury_type || ""}
              onChange={(e) => setFormData({ ...formData, injury_type: e.target.value })}
            />
          </div>

          {/* Vitals Grid */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2">
              <HeartPulse className="w-4 h-4" />
              Emergency Physiological Vital Signs
            </h4>
            <div className="grid grid-cols-3 gap-3">
              <Input
                label="Heart Rate (bpm) *"
                type="number"
                value={formData.heart_rate}
                onChange={(e) => setFormData({ ...formData, heart_rate: Number(e.target.value) })}
                required
              />
              <Input
                label="Systolic BP (mmHg) *"
                type="number"
                value={formData.bp_systolic}
                onChange={(e) => setFormData({ ...formData, bp_systolic: Number(e.target.value) })}
                required
              />
              <Input
                label="Diastolic BP (mmHg) *"
                type="number"
                value={formData.bp_diastolic}
                onChange={(e) => setFormData({ ...formData, bp_diastolic: Number(e.target.value) })}
                required
              />
              <Input
                label="Oxygen Saturation SpO2 (%) *"
                type="number"
                step="0.1"
                value={formData.spo2}
                onChange={(e) => setFormData({ ...formData, spo2: Number(e.target.value) })}
                required
              />
              <Input
                label="Temperature (°C) *"
                type="number"
                step="0.1"
                value={formData.temperature}
                onChange={(e) => setFormData({ ...formData, temperature: Number(e.target.value) })}
                required
              />
              <Input
                label="Respiratory Rate (/min) *"
                type="number"
                value={formData.respiratory_rate}
                onChange={(e) => setFormData({ ...formData, respiratory_rate: Number(e.target.value) })}
                required
              />
            </div>

            <Select
              label="Consciousness Level (AVPU Scale) *"
              options={[
                { value: "ALERT", label: "ALERT • Fully awake & oriented" },
                { value: "VOICE", label: "VOICE • Responds to vocal stimuli" },
                { value: "PAIN", label: "PAIN • Responds to painful stimuli only" },
                { value: "UNRESPONSIVE", label: "UNRESPONSIVE • Comatose / Unresponsive" },
              ]}
              value={formData.consciousness}
              onChange={(e) => setFormData({ ...formData, consciousness: e.target.value as ConsciousnessLevel })}
            />
          </div>

          <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-sky-400 shrink-0" />
            <span>AI decision support only. Final clinical decision must be made by qualified healthcare professionals.</span>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button type="button" variant="ghost" size="sm" onClick={() => setIsRegisterModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="destructive" size="sm" isLoading={createEmergencyMutation.isPending}>
              Register Case & Compute Triage
            </Button>
          </div>
        </form>
      </Modal>

      {/* Triage Decision Support Detail Modal */}
      {viewingCase && (
        <Modal
          isOpen={!!viewingCase}
          onClose={() => setViewingCase(null)}
          title={`Triage Decision Support • Case #${viewingCase.case_number}`}
          description={`Patient: ${viewingCase.patient_name} (${viewingCase.age}y ${viewingCase.gender})`}
          maxWidth="lg"
        >
          <div className="space-y-4 pt-2">
            {/* Triage Level Result Header */}
            <div
              className={`p-4 rounded-2xl border-2 flex items-center justify-between ${
                viewingCase.triage_level === "RED"
                  ? "bg-rose-950/30 border-rose-500/60 text-rose-300"
                  : viewingCase.triage_level === "ORANGE"
                  ? "bg-amber-950/30 border-amber-500/60 text-amber-300"
                  : viewingCase.triage_level === "YELLOW"
                  ? "bg-yellow-950/30 border-yellow-500/60 text-yellow-300"
                  : "bg-emerald-950/30 border-emerald-500/60 text-emerald-300"
              }`}
            >
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest block">
                  TRIAGE OPERATIONAL PRIORITY
                </span>
                <h3 className="text-xl font-extrabold text-white">
                  LEVEL {viewingCase.triage_level === "RED" ? "1 • RED" : viewingCase.triage_level === "ORANGE" ? "2 • ORANGE" : viewingCase.triage_level === "YELLOW" ? "3 • YELLOW" : "4 • GREEN"}
                </h3>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono font-bold block">
                  SpO2: {viewingCase.spo2}% • HR: {viewingCase.heart_rate} bpm
                </span>
                <span className="text-[11px] text-slate-300">
                  BP: {viewingCase.bp_systolic}/{viewingCase.bp_diastolic} • {viewingCase.consciousness}
                </span>
              </div>
            </div>

            {/* Contributing Factors */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Contributing Physiological Factors
              </h4>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                {viewingCase.contributing_factors?.map((factor, i) => (
                  <li key={i}>{factor}</li>
                ))}
              </ul>
            </div>

            {/* Recommended Operational Action */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-sky-500/30 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Recommended Operational Action
              </h4>
              <p className="text-xs text-slate-200 leading-relaxed font-medium">
                {viewingCase.recommended_action}
              </p>
            </div>

            {/* Mandatory Disclaimer */}
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 italic">
              "{viewingCase.disclaimer}"
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button variant="ghost" size="sm" onClick={() => setViewingCase(null)}>
                Close
              </Button>
              {viewingCase.status !== "ADMITTED_IPD" && (
                <Button
                  variant="glow"
                  size="sm"
                  onClick={() => {
                    const c = viewingCase;
                    setViewingCase(null);
                    setAdmittingCase(c);
                    setSelectedWardId(wards?.[0]?.id);
                    setSelectedDocId(doctors?.[0]?.user_id);
                  }}
                  leftIcon={<BedDouble className="w-4 h-4" />}
                >
                  Admit to Inpatient Bed
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Admit Emergency Case to IPD Modal */}
      {admittingCase && (
        <Modal
          isOpen={!!admittingCase}
          onClose={() => setAdmittingCase(null)}
          title={`Admit Emergency Patient to Inpatient (IPD)`}
          description={`Case #${admittingCase.case_number} • Patient: ${admittingCase.patient_name}`}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (selectedWardId && selectedBedId && selectedDocId) {
                // If patient_id not set on emergency case, use first seeded patient for DB link
                const patId = admittingCase.patient_id || patients?.[0]?.id || 1;
                admitEmergencyMutation.mutate({
                  patient_id: patId,
                  admitting_doctor_id: selectedDocId,
                  ward_id: selectedWardId,
                  bed_id: selectedBedId,
                  admission_reason: `Emergency Admission: ${admittingCase.symptoms} (${admittingCase.triage_level})`,
                  expected_stay_days: expectedDays,
                  emergency_case_id: admittingCase.id,
                });
              }
            }}
            className="space-y-4 pt-2"
          >
            <Select
              label="Select Inpatient Ward *"
              options={
                wards?.map((w) => ({
                  value: w.id,
                  label: `${w.name} (${w.available_beds} beds available)`,
                })) || []
              }
              value={selectedWardId}
              onChange={(e) => setSelectedWardId(Number(e.target.value))}
            />

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Select Available Bed *
              </label>
              {availableBeds && availableBeds.length > 0 ? (
                <select
                  value={selectedBedId || ""}
                  onChange={(e) => setSelectedBedId(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                  required
                >
                  <option value="">Choose Bed...</option>
                  {availableBeds.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.bed_number} {b.has_ventilator ? "(Ventilator Support)" : "(High-flow O2)"}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/30 text-xs text-rose-300">
                  No beds currently available in this ward. Please select a different ward.
                </div>
              )}
            </div>

            <Select
              label="Attending / Admitting Doctor *"
              options={
                doctors?.map((doc) => ({
                  value: doc.user_id,
                  label: `${doc.full_name} (${doc.specialization})`,
                })) || []
              }
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(Number(e.target.value))}
            />

            <Input
              label="Expected Hospital Stay (Days) *"
              type="number"
              value={expectedDays}
              onChange={(e) => setExpectedDays(Number(e.target.value))}
              required
            />

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setAdmittingCase(null)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="glow"
                size="sm"
                disabled={!selectedBedId}
                isLoading={admitEmergencyMutation.isPending}
              >
                Confirm Bed Allocation & Admission
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </PageContainer>
  );
};
