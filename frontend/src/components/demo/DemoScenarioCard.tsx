import React from 'react';
import { DemoScenario } from '../../types/demo';
import { Play, Sparkles, Activity, AlertTriangle, ShieldCheck } from 'lucide-react';

interface DemoScenarioCardProps {
  scenario: DemoScenario;
  isActive: boolean;
  isLaunching: boolean;
  onLaunch: (code: string) => void;
}

export const DemoScenarioCard: React.FC<DemoScenarioCardProps> = ({
  scenario,
  isActive,
  isLaunching,
  onLaunch,
}) => {
  const getBadgeStyle = (category: string, isFlagship: boolean) => {
    if (isFlagship) {
      return 'bg-gradient-to-r from-red-500/20 to-amber-500/20 text-red-400 border-red-500/30';
    }
    switch (category) {
      case 'BASELINE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'CLINICAL':
      case 'CAPACITY':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'SUPPLY':
      case 'DIAGNOSTIC':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  return (
    <div
      className={`relative flex flex-col justify-between rounded-xl border p-5 transition-all duration-300 ${
        isActive
          ? 'border-indigo-500/80 bg-indigo-950/20 shadow-lg shadow-indigo-950/50 ring-1 ring-indigo-500/50'
          : scenario.is_flagship
          ? 'border-red-500/30 bg-slate-900/80 hover:border-red-500/60 shadow-md shadow-red-950/20'
          : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900/90'
      }`}
    >
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between gap-3 mb-2.5">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${getBadgeStyle(
                scenario.category,
                scenario.is_flagship
              )}`}
            >
              {scenario.badge || scenario.category}
            </span>
            {scenario.is_flagship && (
              <span className="flex items-center gap-1 text-[11px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/30 animate-pulse">
                <Sparkles className="w-3 h-3 text-amber-400" />
                CRITICAL PROTOCOL
              </span>
            )}
          </div>
          {isActive && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              Active State
            </span>
          )}
        </div>

        <h3 className="text-base font-bold text-slate-100 mb-1.5 flex items-center gap-2">
          {scenario.title || scenario.name}
        </h3>

        <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed">
          {scenario.description}
        </p>

        {/* Affected Departments */}
        <div className="mb-4">
          <div className="text-[11px] font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
            Affected Units:
          </div>
          <div className="flex flex-wrap gap-1.5">
            {(scenario.affected_departments || ["Hospital Wide"]).map((dept) => (
              <span
                key={dept}
                className="text-[11px] px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-slate-300 font-mono"
              >
                {dept}
              </span>
            ))}
          </div>
        </div>

        {/* Target Metrics */}
        {scenario.target_metrics && Object.keys(scenario.target_metrics).length > 0 && (
          <div className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-2.5 mb-4 space-y-1">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Activity className="w-3 h-3 text-indigo-400" />
              Target Simulation Impact
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
              {Object.entries(scenario.target_metrics).map(([key, val]) => (
                <div key={key} className="flex flex-col">
                  <span className="text-[10px] text-slate-400 capitalize">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <span className="font-semibold text-slate-200">
                    {typeof val === 'number' ? `${val}%` : String(val)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="pt-2 border-t border-slate-800/60">
        <button
          type="button"
          onClick={() => onLaunch(scenario.code)}
          disabled={isLaunching}
          className={`w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer active:scale-95 ${
            isLaunching
              ? 'bg-indigo-700/80 text-white cursor-wait'
              : isActive
              ? 'bg-emerald-700/40 text-emerald-300 border border-emerald-500/50 hover:bg-emerald-700/60'
              : scenario.is_flagship
              ? 'bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white shadow-md shadow-red-950/50'
              : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-950/50'
          }`}
        >
          {isLaunching ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Injecting Signals...
            </>
          ) : isActive ? (
            <>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Active (Click to Re-run)
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              {scenario.button_label || "Launch Scenario"}
            </>
          )}
        </button>
      </div>
    </div>
  );
};
