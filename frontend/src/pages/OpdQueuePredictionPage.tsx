import React, { useEffect, useState } from "react";
import { aiApi, departmentsApi, doctorsApi } from "../services/api";
import { OpdQueuePredictionResponse } from "../types/ai";
import { AIModelStatusBadge } from "../components/ai/AIModelStatusBadge";
import {
  Users,
  Clock,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Activity,
} from "lucide-react";

export const OpdQueuePredictionPage: React.FC = () => {
  const [prediction, setPrediction] = useState<OpdQueuePredictionResponse | null>(null);
  const [departments, setDepartments] = useState<any[]>([]);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [selectedDoc, setSelectedDoc] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [deptRes, docRes] = await Promise.all([
        departmentsApi.list(),
        doctorsApi.list(),
      ]);
      setDepartments(deptRes || []);
      setDoctors(docRes || []);

      const pred = await aiApi.predictQueue({
        department_id: selectedDept ? parseInt(selectedDept) : undefined,
        doctor_id: selectedDoc ? parseInt(selectedDoc) : undefined,
      });
      setPrediction(pred);
    } catch (e) {
      console.error("Failed to load OPD queue prediction:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDept, selectedDoc]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                OPD Queue Wait-Time Prediction
              </h1>
              <p className="text-xs text-slate-400">
                Supervised regression & pacing model forecasting clinic wait durations, queue delays, and throughput
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {prediction && (
            <AIModelStatusBadge
              providerType={prediction.model_provider_type}
              version={prediction.model_version}
              confidence={prediction.confidence}
            />
          )}
          <button
            onClick={loadData}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>
      </div>

      {/* Filter Selector Bar */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex flex-wrap items-center gap-4">
        <div className="flex-1 min-w-[200px]">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Filter by Department
          </label>
          <select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Hospital OPD Clinics</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.code})
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Filter by Attending Doctor
          </label>
          <select
            value={selectedDoc}
            onChange={(e) => setSelectedDoc(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Attending Physicians</option>
            {doctors.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.full_name} — {doc.department?.name || "General"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Metric Cards */}
      {prediction && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Estimated Wait Time */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Estimated Wait Time
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {prediction.estimated_wait_minutes}
              </span>
              <span className="text-xs text-slate-400 font-medium">minutes</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              Baseline SLA: {prediction.historical_avg_wait_minutes} mins
            </p>
          </div>

          {/* Queue Congestion / Delay */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Predicted Queue Delay
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span
                className={`text-3xl font-extrabold ${
                  prediction.predicted_delay_minutes > 15 ? "text-amber-400" : "text-emerald-400"
                }`}
              >
                +{prediction.predicted_delay_minutes}
              </span>
              <span className="text-xs text-slate-400 font-medium">mins delay</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5">
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  prediction.risk_level === "CRITICAL"
                    ? "bg-rose-950 text-rose-300"
                    : prediction.risk_level === "HIGH"
                    ? "bg-amber-950 text-amber-300"
                    : "bg-emerald-950 text-emerald-300"
                }`}
              >
                {prediction.risk_level} RISK
              </span>
            </div>
          </div>

          {/* Active Waiting Patients */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Active Queue Size
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {prediction.current_waiting_count}
              </span>
              <span className="text-xs text-slate-400 font-medium">patients waiting</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              Now Serving Token:{" "}
              <strong className="text-indigo-300">
                {prediction.current_serving_token || "None"}
              </strong>
            </p>
          </div>

          {/* Doctor Utilization */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Doctor Utilization
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {prediction.doctor_utilization_percent}%
              </span>
              <span className="text-xs text-slate-400 font-medium">capacity load</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
              <div
                className="bg-indigo-500 h-1.5 rounded-full"
                style={{ width: `${Math.min(100, prediction.doctor_utilization_percent)}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Hourly Queue Trend & Explanation Grid */}
      {prediction && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Hourly Trend Bar Breakdown (2 Cols) */}
          <div className="lg:col-span-2 p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-indigo-400" />
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Hourly Queue & Wait-Time Progression
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">Past 6 Hours Telemetry</span>
            </div>

            <div className="space-y-3">
              {prediction.hourly_trend.map((trend, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300">{trend.time_slot}</span>
                    <span className="text-slate-400">
                      Tokens: <strong className="text-white">{trend.tokens_served}</strong> | Avg
                      Wait: <strong className="text-white">{trend.avg_wait_minutes}m</strong> |
                      Projected:{" "}
                      <strong className="text-indigo-400">{trend.projected_wait_minutes}m</strong>
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden flex">
                    <div
                      className="bg-indigo-600 h-2"
                      style={{
                        width: `${Math.min(
                          100,
                          (trend.projected_wait_minutes / (prediction.estimated_wait_minutes || 60)) *
                            100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Why? Contributing Factors & Recommended Protocol (1 Col) */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-lg space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Operational Intelligence ("Why?")
              </h3>
            </div>

            <div className="space-y-2.5">
              {prediction.explanation?.reasons?.map((reason, idx) => (
                <div key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-indigo-400 font-bold">•</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>

            {/* Protocol Card */}
            <div className="mt-4 p-3.5 bg-indigo-950/40 border border-indigo-900/50 rounded-lg space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-300">
                <ArrowRight className="w-3.5 h-3.5 text-indigo-400" /> Recommended Action
              </div>
              <p className="text-xs text-slate-200 leading-relaxed">
                {prediction.recommended_action}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
