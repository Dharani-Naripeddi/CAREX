import React, { useEffect, useState } from "react";
import { aiApi } from "../services/api";
import { PharmacyPredictionResponse, MedicineDepletionForecast } from "../types/ai";
import { AIModelStatusBadge } from "../components/ai/AIModelStatusBadge";
import {
  Pill,
  TrendingDown,
  AlertOctagon,
  Sparkles,
  ArrowRight,
  RefreshCw,
  ShoppingCart,
  Calendar,
  Layers,
  AlertTriangle,
} from "lucide-react";

export const PharmacyIntelligencePage: React.FC = () => {
  const [data, setData] = useState<PharmacyPredictionResponse | null>(null);
  const [selectedMedId, setSelectedMedId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await aiApi.predictPharmacy({
        medicine_id: selectedMedId ? parseInt(selectedMedId) : undefined,
        days_history: 30,
      });
      setData(res);
    } catch (e) {
      console.error("Failed to load pharmacy depletion forecast:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedMedId]);

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
            <div className="p-2 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30">
              <Pill className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Pharmacy Stock Depletion & Inventory Intelligence
              </h1>
              <p className="text-xs text-slate-400">
                FEFO consumption velocity model predicting pharmaceutical runout countdowns and automated reorder triggers
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

      {/* Overview Stat Counters */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Formulary SKUs Analyzed
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                {data.total_medicines_analyzed}
              </span>
              <span className="text-xs text-slate-400">active pharmaceuticals</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Critical Depletion Risks
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-rose-400">
                {data.critical_depletion_count}
              </span>
              <span className="text-xs text-rose-300">&lt; 3 days stock</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Reorder Threshold Alerts
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-amber-400">
                {data.high_depletion_count}
              </span>
              <span className="text-xs text-amber-300">&lt; 7 days stock</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Total Inventory Valuation
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">
                ${data.total_stock_value.toLocaleString()}
              </span>
              <span className="text-xs text-slate-400">managed value</span>
            </div>
          </div>
        </div>
      )}

      {/* Top Depletion Risks List */}
      {data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Prioritized Stock Depletion & Reorder Forecast
              </h3>
            </div>
            <span className="text-xs text-slate-400">
              Sorted by days of supply remaining ascending
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.top_depletion_risks.map((med) => (
              <div
                key={med.medicine_id}
                className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-lg space-y-3 relative overflow-hidden"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-bold text-white">{med.medicine_name}</h4>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {med.medicine_code} • {med.category}
                    </span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border shrink-0 ${getRiskBadge(
                      med.risk_level
                    )}`}
                  >
                    {med.risk_level}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Current Stock</span>
                    <span className="font-extrabold text-white text-base">
                      {med.current_stock} <span className="text-xs font-normal">units</span>
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Velocity</span>
                    <span className="font-bold text-slate-200">
                      {med.avg_daily_consumption} /day
                    </span>
                  </div>
                </div>

                <div className="space-y-1 text-xs">
                  <div className="flex items-center justify-between text-slate-300">
                    <span>Days Remaining:</span>
                    <strong
                      className={
                        med.estimated_days_remaining <= 3 ? "text-rose-400" : "text-amber-400"
                      }
                    >
                      {med.estimated_days_remaining} days
                    </strong>
                  </div>
                  {med.predicted_depletion_date && (
                    <div className="flex items-center justify-between text-slate-400 text-[11px]">
                      <span>Runout Date:</span>
                      <span className="text-slate-300">{med.predicted_depletion_date}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between text-slate-400 text-[11px]">
                    <span>Suggested Reorder:</span>
                    <strong className="text-indigo-400 font-bold">
                      +{med.recommended_reorder_quantity} units
                    </strong>
                  </div>
                </div>

                {/* Protocol Note */}
                <div className="pt-2 border-t border-slate-800/60 text-[11px] text-slate-300 flex items-start gap-1.5">
                  <ArrowRight className="w-3 h-3 text-purple-400 shrink-0 mt-0.5" />
                  <span>{med.recommended_action}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
