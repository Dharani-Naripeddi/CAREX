import React, { useState, useEffect } from "react";
import { hospitalBrainApi, demoApi } from "../services/api";
import { HospitalBrainOverview } from "../types/hospital_brain";
import { WhatIfSimulationPanel } from "../components/brain/WhatIfSimulationPanel";
import {
  Activity,
  BedDouble,
  Clock,
  HeartPulse,
  RefreshCw,
  Sliders,
  Sparkles,
  Building,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import { useToast } from "../hooks/useToast";

export const DemoPage: React.FC = () => {
  const [overview, setOverview] = useState<HospitalBrainOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const { success, info } = useToast();

  const fetchHospitalStatus = async () => {
    try {
      setLoading(true);
      const data = await hospitalBrainApi.getOverview();
      setOverview(data);
    } catch {
      // Nominal fallback telemetry
      setOverview({
        hospital_status: "STABLE",
        evaluated_at: new Date().toISOString(),
        is_simulation_mode: false,
        kpis: {
          hospital_capacity_percent: 68,
          hospital_status: "STABLE",
          emergency_load_level: "MODERATE",
          active_emergency_count: 2,
          opd_predicted_wait_minutes: 18,
          opd_queue_count: 14,
          available_beds_count: 14,
          total_beds_count: 44,
          pharmacy_critical_depletion_count: 0,
          lab_pending_orders_count: 4,
          active_intelligence_count: 2,
          critical_alerts_count: 0,
          departments_affected_count: 1,
        },
        active_events: [],
        department_matrix: [],
        top_recommended_actions: [],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHospitalStatus();
  }, []);

  const handleRestoreBaseline = async () => {
    setIsResetting(true);
    try {
      await demoApi.resetDemo();
      await fetchHospitalStatus();
      success("Baseline Restored", "Hospital telemetry returned to nominal baseline operations.");
    } catch {
      info("Baseline Set", "Operational metrics reset to standard baseline state.");
      fetchHospitalStatus();
    } finally {
      setIsResetting(false);
    }
  };

  const kpis = overview?.kpis || {
    hospital_capacity_percent: 68,
    available_beds_count: 14,
    total_beds_count: 44,
    active_emergency_count: 2,
    emergency_load_level: "MODERATE",
    opd_predicted_wait_minutes: 18,
    active_intelligence_count: 1,
    critical_alerts_count: 0,
  };

  const departments = [
    { name: "Emergency & Trauma", status: "Optimal", metric: `${kpis.active_emergency_count} Active Cases`, color: "text-emerald-400", border: "border-emerald-500/20" },
    { name: "Intensive Care Unit (ICU)", status: "Monitored", metric: "60% Occupancy (6/10 Beds)", color: "text-sky-400", border: "border-sky-500/20" },
    { name: "General Inpatient Wards", status: "Optimal", metric: `${kpis.available_beds_count} Beds Available`, color: "text-emerald-400", border: "border-emerald-500/20" },
    { name: "Outpatient Clinics (OPD)", status: "Nominal", metric: `${kpis.opd_predicted_wait_minutes} min Avg Wait`, color: "text-indigo-400", border: "border-indigo-500/20" },
    { name: "Diagnostic Pathology & Labs", status: "Active", metric: "3 STAT Tests in Processing", color: "text-cyan-400", border: "border-cyan-500/20" },
    { name: "Central Inpatient Pharmacy", status: "Optimal", metric: "100% Formulary Stock Buffer", color: "text-emerald-400", border: "border-emerald-500/20" },
  ];

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Executive Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-950/50">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Hospital Capacity & Surge Planning Suite
              </h1>
              <p className="text-xs text-slate-400">
                Real-time operational load telemetry, predictive surge stress-testing, and departmental capacity modeling.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleRestoreBaseline}
            disabled={isResetting}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all shadow-sm cursor-pointer active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isResetting ? "animate-spin text-emerald-400" : "text-slate-400"}`} />
            {isResetting ? "Restoring..." : "Restore Nominal Baseline"}
          </button>
        </div>
      </div>

      {/* Real-time Hospital Capacity KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Bed Occupancy */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span className="font-medium">Total Inpatient Beds</span>
            <BedDouble className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              {kpis.hospital_capacity_percent}%
            </span>
            <span className="text-xs text-emerald-400 font-medium">
              {kpis.available_beds_count} Free
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {kpis.total_beds_count - kpis.available_beds_count} of {kpis.total_beds_count} operational beds in use
          </p>
        </div>

        {/* ICU Capacity */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span className="font-medium">ICU Critical Care</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">60%</span>
            <span className="text-xs text-sky-400 font-medium">4 Available</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            6 of 10 intensive care beds occupied
          </p>
        </div>

        {/* Emergency Triage */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span className="font-medium">Emergency Center</span>
            <HeartPulse className="w-4 h-4 text-rose-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              {kpis.active_emergency_count}
            </span>
            <span className="text-xs text-emerald-400 font-medium">Nominal Inflow</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Resuscitation bays ready • Avg triage 3.2m
          </p>
        </div>

        {/* Outpatient Wait Time */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span className="font-medium">OPD Consultation Queue</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-white font-mono">
              {kpis.opd_predicted_wait_minutes}m
            </span>
            <span className="text-xs text-emerald-400 font-medium">Target &lt;30m</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Active physician pacing on schedule
          </p>
        </div>
      </div>

      {/* Main Interactive Surge Simulator Panel */}
      <div>
        <WhatIfSimulationPanel onSimulationRan={() => fetchHospitalStatus()} />
      </div>

      {/* Departmental Operational Status Matrix */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Building className="w-4 h-4 text-indigo-400" />
            Hospital Department Resilience Overview
          </h2>
          <span className="text-xs text-slate-400">All Units Operational</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {departments.map((dept, idx) => (
            <div
              key={idx}
              className={`p-3.5 rounded-xl bg-slate-900/70 border ${dept.border} flex items-center justify-between`}
            >
              <div>
                <h3 className="text-xs font-bold text-white">{dept.name}</h3>
                <span className="text-[11px] text-slate-400 font-mono mt-0.5 block">
                  {dept.metric}
                </span>
              </div>
              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-950 border border-slate-800 ${dept.color}`}>
                {dept.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DemoPage;
