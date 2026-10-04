import React from 'react';
import { DemoPipelineProgress } from '../../types/demo';
import { CheckCircle2, Clock, Zap, AlertTriangle, ArrowRight } from 'lucide-react';

interface DemoPipelineIndicatorProps {
  progress: DemoPipelineProgress | null;
  loading?: boolean;
}

export const DemoPipelineIndicator: React.FC<DemoPipelineIndicatorProps> = ({
  progress,
  loading = false,
}) => {
  if (!progress || !progress.steps) return null;

  const totalSteps = progress.total_steps ?? progress.steps.length;
  const completedSteps = progress.completed_steps ?? progress.steps.filter((s) => s.is_completed).length;
  const progressPct = progress.progress_pct ?? (totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0);
  const scenarioTitle = progress.active_scenario_title || progress.active_scenario_name;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg shadow-black/40">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              6-Stage Hospital Brain Intelligence Pipeline
              {scenarioTitle && (
                <span className="text-xs font-normal text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                  {scenarioTitle}
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-400">
              Autonomous telemetry ingestion, machine learning inference, cross-module signal correlation &amp; simulation
            </p>
          </div>
        </div>

        {/* Progress Bar & Percentage */}
        <div className="flex items-center gap-3">
          <div className="w-32 bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700/60">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <span className="text-xs font-mono font-bold text-slate-200">
            {completedSteps}/{totalSteps} Stages ({progressPct}%)
          </span>
        </div>
      </div>

      {/* 6 Steps Progression Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {progress.steps.map((step, idx) => {
          const stepNum = step.step_number || step.step_index || idx + 1;
          const isDone = step.is_completed;
          const isAlert = step.status === 'ALERT_TRIGGERED' || (step.is_active && !isDone);
          const summaryText = step.output_summary || step.description || step.contributing_signals?.join(', ');

          return (
            <div
              key={stepNum}
              className={`relative flex flex-col justify-between rounded-lg border p-3 transition-all duration-200 ${
                isAlert
                  ? 'border-amber-500/40 bg-amber-950/20'
                  : isDone
                  ? 'border-emerald-500/30 bg-emerald-950/10'
                  : 'border-slate-800 bg-slate-950/40'
              }`}
            >
              {/* Step Number & Status Badge */}
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/40">
                  STEP 0{stepNum}
                </span>
                {isAlert ? (
                  <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-400">
                    <AlertTriangle className="w-3 h-3 text-amber-400" />
                    Active
                  </span>
                ) : isDone ? (
                  <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    Done
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[10px] text-slate-400">
                    <Clock className="w-3 h-3 text-slate-400" />
                    Pending
                  </span>
                )}
              </div>

              {/* Step Name */}
              <div className="mb-2">
                <h4 className="text-xs font-semibold text-slate-200 leading-tight mb-1">
                  {step.step_name}
                </h4>
                {step.department && (
                  <span className="text-[10px] text-indigo-400 font-mono block">
                    {step.department}
                  </span>
                )}
              </div>

              {/* Output Summary */}
              {summaryText && (
                <div className="mt-auto pt-2 border-t border-slate-800/80">
                  <div className="text-[11px] text-slate-300 line-clamp-2 leading-relaxed bg-slate-900/60 p-1.5 rounded border border-slate-800 font-sans">
                    {summaryText}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
