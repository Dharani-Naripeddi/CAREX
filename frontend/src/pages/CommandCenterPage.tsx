import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dashboardApi, patientsApi } from "../services/api";
import { PageContainer } from "../components/layout/PageContainer";
import { KPICard } from "../components/dashboard/KPICard";
import { TrendChart } from "../components/dashboard/TrendChart";
import { OccupancyChart } from "../components/dashboard/OccupancyChart";
import { TriageQueueTable } from "../components/dashboard/TriageQueueTable";
import { RecentActivityFeed } from "../components/dashboard/RecentActivityFeed";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { useToast } from "../hooks/useToast";
import {
  RotateCcw,
  UserPlus,
  BedDouble,
  FlaskConical,
  AlertTriangle,
  Sparkles,
  Download,
  Building,
} from "lucide-react";

export const CommandCenterPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const [activeModal, setActiveModal] = useState<string | null>(null);

  // Form State for Quick Patient Registration
  const [patientForm, setPatientForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    date_of_birth: "1990-01-01",
    gender: "Male",
    blood_group: "O+",
    address: "",
  });

  const {
    data: stats,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["adminDashboard"],
    queryFn: dashboardApi.getAdminStats,
    refetchInterval: 30000, // auto-refresh every 30 seconds
  });

  const createPatientMutation = useMutation({
    mutationFn: patientsApi.create,
    onSuccess: (newPatient) => {
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setActiveModal(null);
      setPatientForm({
        first_name: "",
        last_name: "",
        phone: "",
        email: "",
        date_of_birth: "1990-01-01",
        gender: "Male",
        blood_group: "O+",
        address: "",
      });
      success("Patient Registered", `${newPatient.full_name} (${newPatient.mrn}) created successfully. Count updated.`);
    },
    onError: (err: any) => {
      toastError("Registration Failed", err.response?.data?.detail || "Could not register patient.");
    },
  });

  const handlePatientSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const fName = patientForm.first_name.trim();
    const lName = patientForm.last_name.trim();
    const phone = patientForm.phone.trim();

    if (!fName || !/^[a-zA-Z\s\-']{2,50}$/.test(fName)) {
      toastError("Validation Error", "First Name must contain alphabets only (2-50 characters).");
      return;
    }
    if (!lName || !/^[a-zA-Z\s\-']{2,50}$/.test(lName)) {
      toastError("Validation Error", "Last Name must contain alphabets only (2-50 characters).");
      return;
    }
    if (!/^\d{10}$/.test(phone)) {
      toastError("Validation Error", "Mobile number must be numbers only and exactly 10 digits.");
      return;
    }

    createPatientMutation.mutate({
      first_name: fName,
      last_name: lName,
      phone: phone,
      email: patientForm.email?.trim() || undefined,
      date_of_birth: patientForm.date_of_birth,
      gender: patientForm.gender,
      blood_group: patientForm.blood_group || undefined,
      address: patientForm.address?.trim() || undefined,
    });
  };

  if (isLoading) {
    return (
      <PageContainer title="CAREX Hospital Command Center" subtitle="Connecting to clinical telemetry...">
        <div className="py-24">
          <LoadingSpinner size="lg" label="Synchronizing hospital telemetry and bed sensors..." />
        </div>
      </PageContainer>
    );
  }

  if (isError || !stats) {
    return (
      <PageContainer title="CAREX Hospital Command Center">
        <ErrorState
          title="Could not load Command Center telemetry"
          message="Failed to connect to the hospital dashboard service. Please ensure the backend server is running."
          onRetry={() => refetch()}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="CAREX Hospital Command Center"
      subtitle={`Live telemetry for ${stats.hospital_name} • Last sync: ${stats.last_updated}`}
      badge={<Badge variant="success" dot>Live Operations</Badge>}
      actions={
        <>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            isLoading={isFetching}
            leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Refresh Data
          </Button>
          <Button
            variant="glow"
            size="sm"
            onClick={() => setActiveModal("NEW_PATIENT")}
            leftIcon={<UserPlus className="w-3.5 h-3.5" />}
          >
            Register Patient
          </Button>
        </>
      }
    >
      <div className="space-y-6">
        {/* 8 Core Hospital KPIs Grid */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Critical Hospital KPIs (Phase 1 Baseline)
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">8 Live Metrics</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.kpis.map((kpi) => (
              <KPICard key={kpi.id} kpi={kpi} />
            ))}
          </div>
        </div>

        {/* Analytics Section: Trend Chart & Department Bed Occupancy */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TrendChart data={stats.weekly_trends} />
          </div>
          <div className="lg:col-span-1">
            <OccupancyChart departments={stats.department_occupancy} />
          </div>
        </div>

        {/* Operational Section: Emergency Triage Queue & Live Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-5 backdrop-blur-md">
              <TriageQueueTable patients={stats.triage_queue} />
            </div>
          </div>
          <div className="lg:col-span-1">
            <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-5 backdrop-blur-md">
              <RecentActivityFeed activities={stats.recent_activities} />
            </div>
          </div>
        </div>

        {/* Phase 4: Support Services Quick Navigation */}
        <div className="rounded-2xl bg-slate-900/70 border border-slate-800 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Hospital Support & Clinical Services (Phase 4)</h3>
              <p className="text-xs text-slate-400">Direct operational gateways to central pathology, therapeutics inventory, and revenue cycles.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <a
              href="/lab"
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-900/80 transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 group-hover:scale-110 transition-transform">
                  <FlaskConical className="w-4 h-4" />
                </div>
                <span className="text-xs text-sky-400 font-bold group-hover:translate-x-0.5 transition-transform">Access Portal →</span>
              </div>
              <h4 className="font-bold text-sm text-white">Diagnostic Pathology & Lab</h4>
              <p className="text-xs text-slate-400 mt-1">Accessioning, multi-parameter flag evaluation, and released reports.</p>
            </a>

            <a
              href="/pharmacy"
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-900/80 transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform">
                  <Building className="w-4 h-4 text-emerald-400" />
                </div>
                <span className="text-xs text-emerald-400 font-bold group-hover:translate-x-0.5 transition-transform">Access Portal →</span>
              </div>
              <h4 className="font-bold text-sm text-white">Central Pharmacy & Stocks</h4>
              <p className="text-xs text-slate-400 mt-1">FEFO batch inventory, reorder management, and dispensing ledger.</p>
            </a>

            <a
              href="/billing"
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900/80 transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                </div>
                <span className="text-xs text-indigo-400 font-bold group-hover:translate-x-0.5 transition-transform">Access Portal →</span>
              </div>
              <h4 className="font-bold text-sm text-white">Billing & Revenue Cycles</h4>
              <p className="text-xs text-slate-400 mt-1">Universal invoicing, payment settlements, and stay aggregators.</p>
            </a>
          </div>
        </div>
      </div>

      {/* Quick Action Modal: Patient Registration */}
      <Modal
        isOpen={activeModal === "NEW_PATIENT"}
        onClose={() => setActiveModal(null)}
        title="Register New Outpatient / Emergency Case"
        description="Create an immediate clinical intake record in the CAREX system."
      >
        <form onSubmit={handlePatientSubmit} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name (Alphabets only) *"
              placeholder="e.g. Michael"
              value={patientForm.first_name}
              maxLength={50}
              pattern="^[A-Za-z\s\-']{2,50}$"
              title="First name must contain alphabets only (min 2 characters)"
              onChange={(e) =>
                setPatientForm({
                  ...patientForm,
                  first_name: e.target.value.replace(/[^a-zA-Z\s\-']/g, ""),
                })
              }
              required
            />
            <Input
              label="Last Name (Alphabets only) *"
              placeholder="e.g. Henderson"
              value={patientForm.last_name}
              maxLength={50}
              pattern="^[A-Za-z\s\-']{2,50}$"
              title="Last name must contain alphabets only (min 2 characters)"
              onChange={(e) =>
                setPatientForm({
                  ...patientForm,
                  last_name: e.target.value.replace(/[^a-zA-Z\s\-']/g, ""),
                })
              }
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
              value={patientForm.phone}
              helperText={patientForm.phone ? `${patientForm.phone.length}/10 digits ${patientForm.phone.length === 10 ? "✓" : ""}` : "Numbers only, 10 digits"}
              onChange={(e) =>
                setPatientForm({
                  ...patientForm,
                  phone: e.target.value.replace(/\D/g, "").slice(0, 10),
                })
              }
              required
            />
            <Input
              label="Email (Optional)"
              type="email"
              placeholder="e.g. michael@example.com"
              value={patientForm.email}
              onChange={(e) => setPatientForm({ ...patientForm, email: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Date of Birth *"
              type="date"
              value={patientForm.date_of_birth}
              max={new Date().toISOString().split("T")[0]}
              min="1900-01-01"
              onChange={(e) => setPatientForm({ ...patientForm, date_of_birth: e.target.value })}
              required
            />
            <Select
              label="Gender"
              value={patientForm.gender}
              onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
              options={[
                { value: "Male", label: "Male" },
                { value: "Female", label: "Female" },
                { value: "Other", label: "Other" },
              ]}
            />
            <Select
              label="Blood Group"
              value={patientForm.blood_group}
              onChange={(e) => setPatientForm({ ...patientForm, blood_group: e.target.value })}
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
            />
          </div>

          <Input
            label="Residential Address (Optional)"
            placeholder="e.g. 742 Evergreen Terrace, Springfield"
            value={patientForm.address}
            onChange={(e) => setPatientForm({ ...patientForm, address: e.target.value })}
          />

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="ghost" size="sm" type="button" onClick={() => setActiveModal(null)}>
              Cancel
            </Button>
            <Button
              variant="glow"
              size="sm"
              type="submit"
              isLoading={createPatientMutation.isPending}
            >
              Complete Registration & Issue MRN
            </Button>
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
};
