import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { aiApi } from "../services/api";
import { AIInsightsResponse } from "../types/ai";
import { AIAlertCard } from "../components/ai/AIAlertCard";
import { AIPredictionCard } from "../components/ai/AIPredictionCard";
import { AIModelStatusBadge } from "../components/ai/AIModelStatusBadge";
import {
  Brain,
  Sparkles,
  Users,
  Bed,
  Pill,
  Activity,
  FileText,
  Clock,
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";

export const AiDashboardPage: React.FC = () => {
  const [data, setData] = useState<AIInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [scenarioMessage, setScenarioMessage] = useState<string | null>(null);
  const [triggeringScenario, setTriggeringScenario] = useState(false);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const res = await aiApi.getInsights();
      setData(res);
    } catch (e) {
      console.error("Failed to load AI insights:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  const handleTriggerScenario = async (scenarioType: string) => {
    setTriggeringScenario(true);
    setScenarioMessage(null);
    try {
      const res = await aiApi.triggerSimulation({ scenario_type: scenarioType });
      setScenarioMessage(res.message);
      await fetchInsights();
    } catch (e) {
      console.error("Simulation trigger failed:", e);
    } finally {
      setTriggeringScenario(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                AI Intelligence Center
              </h1>
              <p className="text-xs text-slate-400">
                Predictive clinical operations, capacity forecasting, and automated anomaly detection
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchInsights}
            disabled={loading}
            className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-2 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Telemetry
          </button>
          <Link
            to="/admin/ai/history"
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium flex items-center gap-2 shadow-md shadow-indigo-900/30 transition-colors"
          >
            <Clock className="w-3.5 h-3.5" /> AI Audit Log
          </Link>
        </div>
      </div>

      {/* Controlled Non-Destructive Simulation Bar */}
      <div className="p-4 bg-slate-900/90 border border-indigo-900/40 rounded-2xl shadow-xl backdrop-blur-md space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">
              Controlled Clinical & Operational Scenario Simulations
            </h3>
          </div>
          <span className="text-[11px] text-slate-400">
            Safe live demo injection • Zero data corruption
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <button
            disabled={triggeringScenario}
            onClick={() => handleTriggerScenario("OPD_DELAY")}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-indigo-950/60 border border-slate-700/80 hover:border-indigo-500/50 text-left transition-all group"
          >
            <div className="text-xs font-semibold text-white group-hover:text-indigo-300 flex items-center justify-between">
              <span>OPD Delay Surge</span>
              <Play className="w-3 h-3 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">
              Cardiology wait time spike & delay
            </p>
          </button>

          <button
            disabled={triggeringScenario}
            onClick={() => handleTriggerScenario("ICU_CAPACITY")}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-rose-950/60 border border-slate-700/80 hover:border-rose-500/50 text-left transition-all group"
          >
            <div className="text-xs font-semibold text-white group-hover:text-rose-300 flex items-center justify-between">
              <span>ICU Capacity Crisis</span>
              <Play className="w-3 h-3 text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">
              96% occupancy & ventilator reserve
            </p>
          </button>

          <button
            disabled={triggeringScenario}
            onClick={() => handleTriggerScenario("PHARMACY_DEPLETION")}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-amber-950/60 border border-slate-700/80 hover:border-amber-500/50 text-left transition-all group"
          >
            <div className="text-xs font-semibold text-white group-hover:text-amber-300 flex items-center justify-between">
              <span>Critical Stockout</span>
              <Play className="w-3 h-3 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">
              Azithromycin 1.4 days supply
            </p>
          </button>

          <button
            disabled={triggeringScenario}
            onClick={() => handleTriggerScenario("EMERGENCY_SURGE")}
            className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-purple-950/60 border border-slate-700/80 hover:border-purple-500/50 text-left transition-all group"
          >
            <div className="text-xs font-semibold text-white group-hover:text-purple-300 flex items-center justify-between">
              <span>Emergency Code Yellow</span>
              <Play className="w-3 h-3 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">
              Trauma cluster & resus mobilization
            </p>
          </button>
        </div>

        {scenarioMessage && (
          <div className="p-2.5 rounded-lg bg-indigo-950/50 border border-indigo-800/60 text-xs text-indigo-200 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>{scenarioMessage}</span>
          </div>
        )}
      </div>

      {/* Real-Time Domain Intelligence Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* OPD Queue */}
        <Link
          to="/admin/ai/queue"
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 transition-all shadow-lg hover:shadow-indigo-950/30 group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Users className="w-5 h-5" />
            </div>
            <span className="text-xs text-slate-400 group-hover:text-indigo-300 flex items-center gap-1 font-medium">
              View Forecast <ArrowRight className="w-3 h-3" />
            </span>
          </div>
          <div className="mt-3">
            <h4 className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              OPD Queue Forecast
            </h4>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {data?.quick_status?.opd?.estimated_wait_minutes ?? 0}m
              </span>
              <span className="text-xs text-slate-400">
                ({data?.quick_status?.opd?.waiting_count ?? 0} in queue)
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-xs">
              <span className="px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 text-[10px] font-semibold">
                +{data?.quick_status?.opd?.delay_minutes ?? 0}m Delay Risk
              </span>
            </div>
          </div>
        </Link>

        {/* Bed Capacity */}
        <Link
          to="/admin/ai/bed-forecast"
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition-all shadow-lg hover:shadow-cyan-950/30 group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <Bed className="w-5 h-5" />
            </div>
            <span className="text-xs text-slate-400 group-hover:text-cyan-300 flex items-center gap-1 font-medium">
              View Horizons <ArrowRight className="w-3 h-3" />
            </span>
          </div>
          <div className="mt-3">
            <h4 className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Bed Capacity Forecast
            </h4>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {data?.quick_status?.beds?.projected_24h_percent ?? 0}%
              </span>
              <span className="text-xs text-slate-400">24h Projection</span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-xs">
              <span className="text-[11px] text-slate-300">
                {data?.quick_status?.beds?.available_beds ?? 0} /{" "}
                {data?.quick_status?.beds?.total_beds ?? 0} beds available
              </span>
            </div>
          </div>
        </Link>

        {/* Pharmacy Intelligence */}
        <Link
          to="/admin/ai/pharmacy"
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-purple-500/50 transition-all shadow-lg hover:shadow-purple-950/30 group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
              <Pill className="w-5 h-5" />
            </div>
            <span className="text-xs text-slate-400 group-hover:text-purple-300 flex items-center gap-1 font-medium">
              View Inventory <ArrowRight className="w-3 h-3" />
            </span>
          </div>
          <div className="mt-3">
            <h4 className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Pharmacy Depletion
            </h4>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {data?.quick_status?.pharmacy?.critical_count ?? 0}
              </span>
              <span className="text-xs text-rose-400 font-medium">Critical Stockouts</span>
            </div>
            <div className="mt-2 text-xs text-slate-400">
              Stock Value: ${(data?.quick_status?.pharmacy?.total_stock_value ?? 0).toLocaleString()}
            </div>
          </div>
        </Link>

        {/* Operational Anomalies */}
        <Link
          to="/admin/ai/anomalies"
          className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/50 transition-all shadow-lg hover:shadow-emerald-950/30 group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Activity className="w-5 h-5" />
            </div>
            <span className="text-xs text-slate-400 group-hover:text-emerald-300 flex items-center gap-1 font-medium">
              View Detector <ArrowRight className="w-3 h-3" />
            </span>
          </div>
          <div className="mt-3">
            <h4 className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Operational Anomalies
            </h4>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {data?.quick_status?.anomalies?.anomalies_detected_count ?? 0}
              </span>
              <span className="text-xs text-slate-400">Surges Detected</span>
            </div>
            <div className="mt-2 text-xs">
              <span className="px-2 py-0.5 rounded bg-emerald-950/70 text-emerald-300 text-[10px] font-semibold">
                Status: {data?.quick_status?.anomalies?.overall_status ?? "NORMAL"}
              </span>
            </div>
          </div>
        </Link>
      </div>

      {/* Main Grid: Live AI Operational Alerts & Recent Predictions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active AI Alerts Stream (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Live AI Operational Alerts Stream ({data?.alerts?.length || 0})
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-medium">Autonomous Trigger Engine</span>
          </div>

          {data?.alerts && data.alerts.length > 0 ? (
            <div className="space-y-3">
              {data.alerts.map((alert) => (
                <AIAlertCard key={alert.id} alert={alert} onStatusChanged={fetchInsights} />
              ))}
            </div>
          ) : (
            <div className="p-8 text-center bg-slate-900/50 border border-slate-800 rounded-xl text-slate-400 text-xs">
              No active operational anomalies or capacity risks detected. All systems nominal.
            </div>
          )}
        </div>

        {/* Recent AI Predictions Stream (1 Col) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Recent AI Insights
              </h3>
            </div>
            <Link to="/admin/ai/history" className="text-xs text-indigo-400 hover:underline">
              View All
            </Link>
          </div>

          {data?.predictions && data.predictions.length > 0 ? (
            <div className="space-y-3">
              {data.predictions.slice(0, 3).map((pred) => (
                <AIPredictionCard
                  key={pred.id}
                  prediction={pred}
                  onFeedbackSubmitted={fetchInsights}
                />
              ))}
            </div>
          ) : (
            <div className="p-8 text-center bg-slate-900/50 border border-slate-800 rounded-xl text-slate-400 text-xs">
              No recent predictions logged.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
