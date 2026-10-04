import React, { useEffect, useState } from "react";
import { aiApi } from "../services/api";
import { AIPrediction } from "../types/ai";
import { AIModelStatusBadge } from "../components/ai/AIModelStatusBadge";
import {
  Clock,
  Sparkles,
  Search,
  Filter,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

export const AiHistoryPage: React.FC = () => {
  const [predictions, setPredictions] = useState<AIPrediction[]>([]);
  const [selectedType, setSelectedType] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await aiApi.getPredictions({
        prediction_type: selectedType || undefined,
        limit: 50,
      });
      setPredictions(res || []);
    } catch (e) {
      console.error("Failed to load AI predictions:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [selectedType]);

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case "CRITICAL":
        return "bg-rose-950/80 text-rose-300 border-rose-800";
      case "HIGH":
        return "bg-amber-950/80 text-amber-300 border-amber-800";
      case "MEDIUM":
        return "bg-yellow-950/80 text-yellow-300 border-yellow-800";
      case "LOW":
      default:
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                AI Traceability & Prediction Audit Trail
              </h1>
              <p className="text-xs text-slate-400">
                Complete historical record of model invocations, confidence scores, explanations, and user feedback
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={loadHistory}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Filter */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center gap-4">
        <div className="w-full sm:w-80">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Filter by Intelligence Domain
          </label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Predictions</option>
            <option value="QUEUE_WAIT_TIME">OPD Queue Wait-Time</option>
            <option value="BED_OCCUPANCY">Bed Capacity Forecast</option>
            <option value="PHARMACY_DEPLETION">Pharmacy Stock Depletion</option>
            <option value="TRIAGE_ASSESSMENT">Emergency Triage Decision Support</option>
            <option value="CLINICAL_SUMMARY">Medical Document Intelligence</option>
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Prediction Domain</th>
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Model Engine</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">Generated Time</th>
                <th className="py-3 px-4">Summary Explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {predictions.map((p) => (
                <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    {p.prediction_type.replace(/_/g, " ")}
                  </td>
                  <td className="py-3 px-4 text-slate-300 font-mono text-[11px]">
                    {p.entity_type} {p.entity_id ? `(${p.entity_id})` : ""}
                  </td>
                  <td className="py-3 px-4">
                    <AIModelStatusBadge
                      providerType={p.model_provider_type}
                      version={p.model_version}
                      confidence={p.confidence}
                    />
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRiskBadge(
                        p.risk_level
                      )}`}
                    >
                      {p.risk_level}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                    {new Date(p.generated_at).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="py-3 px-4 text-slate-300 max-w-xs truncate">
                    {p.explanation?.summary || JSON.stringify(p.prediction_value)}
                  </td>
                </tr>
              ))}
              {predictions.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No predictions recorded for the selected filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
