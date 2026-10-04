import React, { useEffect, useState } from "react";
import { aiApi, bedsApi } from "../services/api";
import { BedPredictionResponse, ForecastHorizonPoint, WardForecastSummary } from "../types/ai";
import { AIModelStatusBadge } from "../components/ai/AIModelStatusBadge";
import {
  Bed,
  Clock,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  RefreshCw,
  Activity,
  Layers,
} from "lucide-react";

export const BedForecastPage: React.FC = () => {
  const [prediction, setPrediction] = useState<BedPredictionResponse | null>(null);
  const [wards, setWards] = useState<any[]>([]);
  const [selectedWard, setSelectedWard] = useState<string>("1");
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const wardRes = await bedsApi.listWards();
      setWards(wardRes || []);

      const pred = await aiApi.predictBeds({
        ward_id: selectedWard ? parseInt(selectedWard) : undefined,
      });
      setPrediction(pred);
    } catch (e) {
      console.error("Failed to load Bed capacity forecast:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedWard]);

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
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-600/20 text-cyan-400 border border-cyan-500/30">
              <Bed className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Bed Capacity & Inpatient Horizon Forecasting
              </h1>
              <p className="text-xs text-slate-400">
                Stochastic Markov time-series forecasting 6h, 12h, and 24h occupancy across critical care, ICU, and step-down wards
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

      {/* Ward Filter */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center gap-4">
        <div className="w-full sm:w-80">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Filter Ward Scope
          </label>
          <select
            value={selectedWard}
            onChange={(e) => setSelectedWard(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            <option value="">Hospital-Wide (All Wards & Units)</option>
            {wards.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name} ({w.code})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 6h, 12h, 24h Forecast Horizon Cards */}
      {prediction && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {prediction.horizons.map((h) => (
            <div
              key={h.horizon_hours}
              className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg relative overflow-hidden"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" /> {h.horizon_hours}-Hour Horizon
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRiskBadge(
                    h.risk_level
                  )}`}
                >
                  {h.risk_level}
                </span>
              </div>

              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-white">
                  {h.projected_occupancy_percent}%
                </span>
                <span className="text-xs text-slate-400">projected occupancy</span>
              </div>

              <div className="w-full bg-slate-800 rounded-full h-2 mt-3 overflow-hidden">
                <div
                  className={`h-2 rounded-full ${
                    h.projected_occupancy_percent > 90
                      ? "bg-rose-500"
                      : h.projected_occupancy_percent > 80
                      ? "bg-amber-500"
                      : "bg-cyan-500"
                  }`}
                  style={{ width: `${Math.min(100, h.projected_occupancy_percent)}%` }}
                />
              </div>

              <div className="mt-3 grid grid-cols-3 text-center border-t border-slate-800/80 pt-2.5 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 block">Admissions</span>
                  <span className="font-semibold text-slate-200">+{h.projected_admissions}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block">Discharges</span>
                  <span className="font-semibold text-slate-200">-{h.projected_discharges}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block">Net Delta</span>
                  <span
                    className={`font-semibold ${
                      h.net_bed_delta > 0 ? "text-amber-400" : "text-emerald-400"
                    }`}
                  >
                    {h.net_bed_delta > 0 ? `+${h.net_bed_delta}` : h.net_bed_delta} beds
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Ward Breakdown Table & Protocol */}
      {prediction && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Ward Breakdown Table (2 Cols) */}
          <div className="lg:col-span-2 p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Ward-by-Ward Capacity & Risk Distribution
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">
                {prediction.ward_breakdown.length} Wards Tracked
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Ward</th>
                    <th className="py-2 px-3">Total Beds</th>
                    <th className="py-2 px-3">Occupied</th>
                    <th className="py-2 px-3">Available</th>
                    <th className="py-2 px-3">Current</th>
                    <th className="py-2 px-3">24h Forecast</th>
                    <th className="py-2 px-3">Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {prediction.ward_breakdown.map((w) => (
                    <tr key={w.ward_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 px-3 font-medium text-slate-200">{w.ward_name}</td>
                      <td className="py-2.5 px-3 text-slate-300">{w.total_beds}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{w.occupied_beds}</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-semibold">
                        {w.available_beds}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {w.current_occupancy_percent}%
                      </td>
                      <td className="py-2.5 px-3 font-bold text-cyan-300">
                        {w.projected_24h_occupancy_percent}%
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRiskBadge(
                            w.risk_level
                          )}`}
                        >
                          {w.risk_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Operational Intelligence ("Why?") (1 Col) */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-lg space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Capacity Analysis ("Why?")
              </h3>
            </div>

            <div className="space-y-2.5">
              {prediction.explanation?.reasons?.map((reason, idx) => (
                <div key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-cyan-400 font-bold">•</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>

            {/* Recommended Protocol */}
            <div className="mt-4 p-3.5 bg-cyan-950/40 border border-cyan-900/50 rounded-lg space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-300">
                <ArrowRight className="w-3.5 h-3.5 text-cyan-400" /> Bed Management Protocol
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
