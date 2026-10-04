import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { hospitalBrainApi } from "../services/api";
import { HospitalBrainOverview, HospitalBrainEvent, DepartmentStatusSummary } from "../types/hospital_brain";
import { HospitalBrainEventCard } from "../components/brain/HospitalBrainEventCard";
import { HospitalBrainWhyModal } from "../components/brain/HospitalBrainWhyModal";
import { DepartmentStatusMatrix } from "../components/brain/DepartmentStatusMatrix";
import { WhatIfSimulationPanel } from "../components/brain/WhatIfSimulationPanel";
import {
  Brain,
  Activity,
  Bed,
  Users,
  Pill,
  FlaskConical,
  AlertTriangle,
  RefreshCw,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Sliders,
  ChevronRight,
  Sparkles,
  ArrowRight,
  Layers,
} from "lucide-react";

export const HospitalBrainPage: React.FC = () => {
  const [data, setData] = useState<HospitalBrainOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterTab, setFilterTab] = useState<string>("ALL");
  const [selectedEvent, setSelectedEvent] = useState<HospitalBrainEvent | null>(null);
  const [whyModalOpen, setWhyModalOpen] = useState(false);
  const [activeViewTab, setActiveViewTab] = useState<"FEED" | "DEPARTMENTS" | "ACTIONS" | "SIMULATION">("FEED");

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await hospitalBrainApi.getOverview();
      setData(res);
    } catch (err) {
      console.error("Failed to load Hospital Brain overview:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // 30-second polling
    return () => clearInterval(interval);
  }, []);

  const handleOpenDetails = (event: HospitalBrainEvent) => {
    setSelectedEvent(event);
    setWhyModalOpen(true);
  };

  const getFilteredEvents = () => {
    if (!data) return [];
    let events = data.active_events;
    if (filterTab === "CRITICAL") {
      events = events.filter((e) => e.severity === "CRITICAL" || e.severity === "HIGH");
    } else if (filterTab === "COMPOSITE") {
      events = events.filter((e) => e.is_composite_correlation);
    } else if (filterTab === "RESOLVED") {
      events = events.filter((e) => e.status === "RESOLVED");
    }
    return events;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "CRITICAL":
        return "bg-rose-950/80 text-rose-300 border-rose-700 animate-pulse";
      case "HIGH_LOAD":
        return "bg-amber-950/80 text-amber-300 border-amber-700";
      case "WATCH":
        return "bg-yellow-950/80 text-yellow-300 border-yellow-700";
      case "STABLE":
      default:
        return "bg-emerald-950/80 text-emerald-300 border-emerald-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* Flagship Command Center Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 shadow-xl backdrop-blur-xl">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-500 text-white shadow-lg shadow-indigo-500/25">
            <Brain className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-black text-white tracking-tight">
                CAREX HOSPITAL BRAIN
              </h1>
              {data && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${getStatusBadge(data.hospital_status)}`}>
                  STATUS: {data.hospital_status}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Centralized real-time operational intelligence, multi-signal correlation, and proactive capacity forecasting
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-2 shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          <Link
            to="/admin/ai"
            className="px-3.5 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Activity className="w-3.5 h-3.5" /> AI Telemetry Hub
          </Link>
        </div>
      </div>

      {/* Top 6 KPI Summary Cards */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Hospital Capacity */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-md">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Hospital Capacity
            </span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-extrabold text-white">
                {data.kpis.hospital_capacity_percent}%
              </span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {data.kpis.available_beds_count} beds free
            </span>
          </div>

          {/* Emergency Load */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-md">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Emergency Load
            </span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className={`text-2xl font-extrabold ${data.kpis.emergency_load_level === "CRITICAL" ? "text-rose-400" : data.kpis.emergency_load_level === "HIGH" ? "text-amber-400" : "text-emerald-400"}`}>
                {data.kpis.emergency_load_level}
              </span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {data.kpis.active_emergency_count} active cases
            </span>
          </div>

          {/* OPD Queue */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-md">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              OPD Wait Time
            </span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-extrabold text-white">
                {data.kpis.opd_predicted_wait_minutes}m
              </span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {data.kpis.opd_queue_count} in queue
            </span>
          </div>

          {/* Bed Availability */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-md">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Available Beds
            </span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-extrabold text-cyan-400">
                {data.kpis.available_beds_count}
              </span>
              <span className="text-xs text-slate-400">/ {data.kpis.total_beds_count}</span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              Inpatient Wards
            </span>
          </div>

          {/* Pharmacy Risk */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-md">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Pharmacy Depletion
            </span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className={`text-2xl font-extrabold ${data.kpis.pharmacy_critical_depletion_count > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                {data.kpis.pharmacy_critical_depletion_count}
              </span>
              <span className="text-xs text-slate-400">SKUs</span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              &lt; 3 days stock
            </span>
          </div>

          {/* Lab Backlog */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-md">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Lab Backlog
            </span>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-2xl font-extrabold text-white">
                {data.kpis.lab_pending_orders_count}
              </span>
              <span className="text-xs text-slate-400">orders</span>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">
              Pending diagnostic tests
            </span>
          </div>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveViewTab("FEED")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeViewTab === "FEED"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-950/50"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <Brain className="w-3.5 h-3.5" /> Active Intelligence Stream ({data?.active_events.length || 0})
        </button>

        <button
          onClick={() => setActiveViewTab("DEPARTMENTS")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeViewTab === "DEPARTMENTS"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-950/50"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <Activity className="w-3.5 h-3.5" /> Department Matrix
        </button>

        <button
          onClick={() => setActiveViewTab("ACTIONS")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeViewTab === "ACTIONS"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-950/50"
              : "text-slate-400 hover:text-white hover:bg-slate-800/60"
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" /> Operational Action Center
        </button>

        <button
          onClick={() => setActiveViewTab("SIMULATION")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeViewTab === "SIMULATION"
              ? "bg-purple-600 text-white shadow-md shadow-purple-950/50"
              : "text-purple-300 hover:text-white hover:bg-purple-950/30"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" /> What-If Simulator
        </button>
      </div>

      {/* Main Tab Content */}
      {activeViewTab === "FEED" && (
        <div className="space-y-4">
          {/* Intelligence Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold">Filter Stream:</span>
              <button
                onClick={() => setFilterTab("ALL")}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                  filterTab === "ALL" ? "bg-slate-800 text-white font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                All Events
              </button>
              <button
                onClick={() => setFilterTab("CRITICAL")}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                  filterTab === "CRITICAL" ? "bg-rose-950/80 text-rose-300 border border-rose-800 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                Critical & High Only
              </button>
              <button
                onClick={() => setFilterTab("COMPOSITE")}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                  filterTab === "COMPOSITE" ? "bg-purple-950/80 text-purple-300 border border-purple-800 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                Composite Correlated Risks
              </button>
            </div>

            <span className="text-slate-400">
              Sorted by Operational Priority Score (0–100)
            </span>
          </div>

          {/* Events Feed */}
          {getFilteredEvents().length > 0 ? (
            <div className="space-y-3.5">
              {getFilteredEvents().map((event) => (
                <HospitalBrainEventCard
                  key={event.id}
                  event={event}
                  onOpenDetails={handleOpenDetails}
                  onStatusUpdated={loadData}
                />
              ))}
            </div>
          ) : (
            <div className="p-12 text-center bg-slate-900/40 border border-slate-800 rounded-2xl text-slate-400 text-xs">
              No operational events matching the selected filter. Hospital systems are running within nominal parameters.
            </div>
          )}
        </div>
      )}

      {activeViewTab === "DEPARTMENTS" && data && (
        <DepartmentStatusMatrix
          departments={data.department_matrix}
        />
      )}

      {activeViewTab === "ACTIONS" && data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Coordinated Operational Action Playbooks
            </h3>
            <span className="text-xs text-slate-400">
              {data.top_recommended_actions.length} Action Protocols Active
            </span>
          </div>

          <div className="space-y-3">
            {data.top_recommended_actions.map((act, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-start gap-3 shadow-md"
              >
                <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 shrink-0 mt-0.5">
                  <ArrowRight className="w-4 h-4" />
                </div>
                <div className="space-y-1 text-xs">
                  <strong className="text-white text-sm font-semibold block">Action Playbook #{idx + 1}</strong>
                  <p className="text-slate-300 leading-relaxed">{act}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeViewTab === "SIMULATION" && (
        <WhatIfSimulationPanel />
      )}

      {/* "Why?" Explainability Modal */}
      <HospitalBrainWhyModal
        event={selectedEvent}
        isOpen={whyModalOpen}
        onClose={() => setWhyModalOpen(false)}
      />
    </div>
  );
};
