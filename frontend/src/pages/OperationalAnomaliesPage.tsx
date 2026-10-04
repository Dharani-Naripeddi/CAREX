import React, { useEffect, useState } from "react";
import { aiApi } from "../services/api";
import { AnomalyDetectionResponse, OperationalAnomalyItem } from "../types/ai";
import { AIModelStatusBadge } from "../components/ai/AIModelStatusBadge";
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  RefreshCw,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

export const OperationalAnomaliesPage: React.FC = () => {
  const [data, setData] = useState<AnomalyDetectionResponse | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await aiApi.detectAnomalies({
        domain: selectedDomain,
      });
      setData(res);
    } catch (e) {
      console.error("Failed to load anomaly detection:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDomain]);

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-rose-950/80 text-rose-300 border-rose-800";
      case "HIGH":
        return "bg-amber-950/80 text-amber-300 border-amber-800";
      case "WARNING":
        return "bg-yellow-950/80 text-yellow-300 border-yellow-800";
      case "INFO":
      default:
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800";
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-600/20 text-emerald-400 border border-emerald-500/30">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Hospital Operational Anomaly Detector
              </h1>
              <p className="text-xs text-slate-400">
                Z-Score & IQR Isolation deviation monitoring detecting sudden OPD surges, ER spikes, and bed bottlenecks
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {data && (
            <AIModelStatusBadge
              providerType={data.model_provider_type}
              version={data.model_version}
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

      {/* Domain Filters & Status Summary Bar */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          {["ALL", "OPD", "EMERGENCY", "BEDS", "LABORATORY", "PHARMACY"].map((d) => (
            <button
              key={d}
              onClick={() => setSelectedDomain(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                selectedDomain === d
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-900/30"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {d}
            </button>
          ))}
        </div>

        {data && (
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">
              Status:{" "}
              <strong
                className={
                  data.overall_system_status === "CRITICAL_SURGE"
                    ? "text-rose-400"
                    : data.overall_system_status === "ELEVATED_LOAD"
                    ? "text-amber-400"
                    : "text-emerald-400"
                }
              >
                {data.overall_system_status}
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Anomalies Metric Cards */}
      {data && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.anomalies.map((item) => (
              <div
                key={item.anomaly_key}
                className={`p-5 rounded-xl border shadow-lg space-y-3 transition-all ${
                  item.is_anomaly
                    ? item.severity === "CRITICAL"
                      ? "bg-rose-950/20 border-rose-800/80"
                      : "bg-amber-950/20 border-amber-800/80"
                    : "bg-slate-900 border-slate-800"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {item.is_anomaly ? (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    )}
                    <div>
                      <h4 className="text-sm font-bold text-white">{item.title}</h4>
                      <span className="text-[11px] text-slate-400 font-mono">
                        Domain: {item.domain}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(
                      item.severity
                    )}`}
                  >
                    {item.severity}
                  </span>
                </div>

                {/* Values & Deviation */}
                <div className="grid grid-cols-3 gap-2 text-xs bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60 text-center">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Current Telemetry</span>
                    <span className="font-extrabold text-white text-base">
                      {item.current_value} <span className="text-[11px] font-normal">{item.unit}</span>
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Baseline Expected</span>
                    <span className="font-bold text-slate-300 text-base">
                      {item.expected_value} <span className="text-[11px] font-normal">{item.unit}</span>
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Deviation</span>
                    <span
                      className={`font-extrabold text-base ${
                        item.percentage_deviation > 50
                          ? "text-rose-400"
                          : item.percentage_deviation > 20
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {item.percentage_deviation > 0 ? `+${item.percentage_deviation}%` : `${item.percentage_deviation}%`}
                    </span>
                  </div>
                </div>

                {/* Explanation */}
                <p className="text-xs text-slate-300 leading-relaxed">
                  {item.explanation_reason}
                </p>

                {/* Recommended Protocol */}
                <div className="pt-2 border-t border-slate-800/60 text-xs text-slate-200 flex items-start gap-1.5">
                  <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-indigo-300">Action:</strong> {item.recommended_action}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
