import React from 'react';
import { HospitalBrainOverview, TopKPIsSummary, HospitalSystemStatus } from '../../types/hospital_brain';
import { Shield, RefreshCw, Layers, ArrowUpRight, Activity, Cpu } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DemoCommandCenterViewProps {
  overview: HospitalBrainOverview | null;
  activeScenarioName?: string;
  isResetting: boolean;
  onReset: () => void;
}

export const DemoCommandCenterView: React.FC<DemoCommandCenterViewProps> = ({
  overview,
  activeScenarioName,
  isResetting,
  onReset,
}) => {
  if (!overview || !overview.kpis) return null;

  const kpis: TopKPIsSummary = overview.kpis;
  const status: HospitalSystemStatus = overview.hospital_status;

  return (
    <div className="space-y-4">
      {/* Hospital Simulation & Contingency Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900/90 to-purple-950/30 shadow-md">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
            <Cpu className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100">
                CAREX HOSPITAL OPERATIONS & CONTINGENCY SANDBOX
              </h2>
              <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
                ACTIVE MONITOR
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Active Operational Profile: <strong className="text-indigo-300 font-semibold">{activeScenarioName || 'Baseline Stable Operations'}</strong> — Multi-department telemetry streaming in real-time.
            </p>
          </div>
        </div>

        {/* Quick Links & Reset */}
        <div className="flex items-center gap-2.5">
          <Link
            to="/admin/hospital-brain"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            Hospital Brain
            <ArrowUpRight className="w-3 h-3 text-slate-400" />
          </Link>
          <Link
            to="/patients/1/journey"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            Patient Journey
            <ArrowUpRight className="w-3 h-3 text-slate-400" />
          </Link>
          <button
            onClick={onReset}
            disabled={isResetting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
            {isResetting ? 'Restoring Baseline...' : 'Reset to Baseline'}
          </button>
        </div>
      </div>

      {/* Live System Status Snapshot */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Hospital Capacity Load */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 flex flex-col justify-between">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Hospital Capacity
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span
              className={`text-2xl font-black font-mono ${
                kpis.hospital_capacity_percent >= 85
                  ? 'text-red-400'
                  : kpis.hospital_capacity_percent >= 70
                  ? 'text-amber-400'
                  : 'text-emerald-400'
              }`}
            >
              {kpis.hospital_capacity_percent}%
            </span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">Total aggregated census</span>
        </div>

        {/* System Health */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 flex flex-col justify-between">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            System State
          </span>
          <div className="flex items-center gap-1.5 mt-1">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                status === 'CRITICAL'
                  ? 'bg-red-500 animate-pulse'
                  : status === 'HIGH_LOAD' || status === 'WATCH'
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
            />
            <span className="text-sm font-bold text-slate-100 font-mono">
              {status}
            </span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">Telemetry health</span>
        </div>

        {/* Active Brain Alerts */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 flex flex-col justify-between">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Active Alerts
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span
              className={`text-2xl font-black font-mono ${
                kpis.active_intelligence_count > 0 ? 'text-amber-400' : 'text-slate-200'
              }`}
            >
              {kpis.active_intelligence_count}
            </span>
            {kpis.critical_alerts_count > 0 && (
              <span className="text-[10px] font-bold text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                {kpis.critical_alerts_count} Critical
              </span>
            )}
          </div>
          <span className="text-[10px] text-slate-400 mt-1">Brain action queue</span>
        </div>

        {/* Available Beds */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 flex flex-col justify-between">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Available Beds
          </span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-2xl font-black font-mono text-emerald-400">
              {kpis.available_beds_count}
            </span>
            <span className="text-xs text-slate-400 font-mono">/ {kpis.total_beds_count}</span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">All inpatient wards</span>
        </div>

        {/* Emergency Load */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 flex flex-col justify-between">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Emergency Center
          </span>
          <div className="flex items-baseline gap-1 mt-1">
            <span
              className={`text-2xl font-black font-mono ${
                kpis.active_emergency_count >= 5
                  ? 'text-red-400'
                  : kpis.active_emergency_count >= 3
                  ? 'text-amber-400'
                  : 'text-emerald-400'
              }`}
            >
              {kpis.active_emergency_count}
            </span>
            <span className="text-xs text-slate-400 font-mono">active</span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">Load: {kpis.emergency_load_level}</span>
        </div>

        {/* OPD Queue Wait Time */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5 flex flex-col justify-between">
          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
            Avg OPD Wait
          </span>
          <div className="flex items-baseline gap-1 mt-1">
            <span
              className={`text-2xl font-black font-mono ${
                kpis.opd_predicted_wait_minutes >= 45
                  ? 'text-red-400'
                  : kpis.opd_predicted_wait_minutes >= 30
                  ? 'text-amber-400'
                  : 'text-emerald-400'
              }`}
            >
              {kpis.opd_predicted_wait_minutes}
            </span>
            <span className="text-xs text-slate-400 font-mono">min</span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">ML Queue Forecast</span>
        </div>
      </div>
    </div>
  );
};
