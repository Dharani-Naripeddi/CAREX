import React, { useState } from "react";
import { HospitalBrainEvent } from "../../types/hospital_brain";
import { AIAlertSeverity, AIAlertStatus, AIRiskLevel } from "../../types/ai";
import { AIModelStatusBadge } from "../ai/AIModelStatusBadge";
import { hospitalBrainApi } from "../../services/api";
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  Clock,
  CheckCircle,
  HelpCircle,
  ArrowRight,
  Layers,
  Sparkles,
  ShieldAlert,
  Activity,
  Check,
} from "lucide-react";

interface HospitalBrainEventCardProps {
  event: HospitalBrainEvent;
  onOpenDetails: (event: HospitalBrainEvent) => void;
  onStatusUpdated?: () => void;
  className?: string;
}

export const HospitalBrainEventCard: React.FC<HospitalBrainEventCardProps> = ({
  event,
  onOpenDetails,
  onStatusUpdated,
  className = "",
}) => {
  const [loading, setLoading] = useState(false);

  const handleAcknowledge = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setLoading(true);
    try {
      await hospitalBrainApi.acknowledgeEvent(event.id);
      if (onStatusUpdated) onStatusUpdated();
    } catch (err) {
      console.error("Acknowledge failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setLoading(true);
    try {
      await hospitalBrainApi.resolveEvent(event.id);
      if (onStatusUpdated) onStatusUpdated();
    } catch (err) {
      console.error("Resolve failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityStyle = (sev: AIAlertSeverity) => {
    switch (sev) {
      case "CRITICAL":
        return {
          border: "border-rose-700/80 bg-rose-950/20 hover:border-rose-500",
          badge: "bg-rose-950/80 text-rose-300 border-rose-700",
          icon: <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0" />,
          priorityBg: "bg-rose-600 text-white",
        };
      case "HIGH":
        return {
          border: "border-amber-700/80 bg-amber-950/20 hover:border-amber-500",
          badge: "bg-amber-950/80 text-amber-300 border-amber-700",
          icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
          priorityBg: "bg-amber-600 text-white",
        };
      case "WARNING":
        return {
          border: "border-yellow-700/80 bg-yellow-950/20 hover:border-yellow-500",
          badge: "bg-yellow-950/80 text-yellow-300 border-yellow-700",
          icon: <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />,
          priorityBg: "bg-yellow-600 text-slate-900",
        };
      case "INFO":
      default:
        return {
          border: "border-blue-700/80 bg-blue-950/20 hover:border-blue-500",
          badge: "bg-blue-950/80 text-blue-300 border-blue-700",
          icon: <Info className="w-5 h-5 text-blue-400 shrink-0" />,
          priorityBg: "bg-blue-600 text-white",
        };
    }
  };

  const config = getSeverityStyle(event.severity);

  return (
    <div
      onClick={() => onOpenDetails(event)}
      className={`rounded-2xl border p-5 shadow-lg backdrop-blur-md transition-all cursor-pointer group ${config.border} ${className}`}
    >
      {/* Card Header: Score, Severity, Title, Correlation Badges */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {config.icon}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                {event.title}
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-bold ${config.badge}`}>
                {event.severity}
              </span>
              {event.is_composite_correlation && (
                <span className="px-2 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-700 text-[10px] font-semibold flex items-center gap-1">
                  <Layers className="w-3 h-3" /> Composite Crisis
                </span>
              )}
            </div>

            <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
              {event.description}
            </p>
          </div>
        </div>

        {/* Priority Score Meter */}
        <div className="flex flex-col items-end shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
              Priority Score
            </span>
            <span className={`px-2 py-0.5 rounded-md text-xs font-black shadow-md ${config.priorityBg}`}>
              {event.priority.score}/100
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-medium mt-0.5">
            Rating: <strong className="text-slate-200">{event.priority.rating}</strong>
          </span>
        </div>
      </div>

      {/* Correlated Sources & Affected Departments */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-400 text-[11px]">Affected:</span>
          {event.explanation.affected_departments.map((dept, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-200 text-[10px] font-medium border border-slate-700"
            >
              {dept}
            </span>
          ))}
        </div>

        {/* Model Transparency */}
        <AIModelStatusBadge
          providerType={event.explanation.model_provider_type}
          version={event.explanation.model_version}
          confidence={event.explanation.confidence}
        />
      </div>

      {/* Recommended Action Protocol */}
      {event.recommended_action && (
        <div className="mt-3 p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-start gap-2.5">
          <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <strong className="text-indigo-300 font-semibold">Recommended Operational Protocol:</strong>{" "}
            <span className="text-slate-200">{event.recommended_action}</span>
          </div>
        </div>
      )}

      {/* Action Footer */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-slate-400 text-[11px]">
          <Clock className="w-3.5 h-3.5" />
          <span>{new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
          <span className="font-mono text-slate-500">• Module: {event.source_module}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onOpenDetails(event);
            }}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-1 transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5 text-indigo-400" /> View "Why?"
          </button>

          {event.status === "ACTIVE" && (
            <>
              <button
                disabled={loading}
                onClick={handleAcknowledge}
                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-1 transition-colors"
              >
                <Clock className="w-3 h-3 text-amber-400" /> Acknowledge
              </button>
              <button
                disabled={loading}
                onClick={handleResolve}
                className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium flex items-center gap-1 shadow-md shadow-emerald-950/40 transition-colors"
              >
                <Check className="w-3.5 h-3.5" /> Resolve
              </button>
            </>
          )}

          {event.status === "ACKNOWLEDGED" && (
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-950/70 text-amber-300 border border-amber-800">
                Acknowledged
              </span>
              <button
                disabled={loading}
                onClick={handleResolve}
                className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium flex items-center gap-1 shadow-md shadow-emerald-950/40 transition-colors"
              >
                <Check className="w-3.5 h-3.5" /> Resolve
              </button>
            </div>
          )}

          {event.status === "RESOLVED" && (
            <span className="px-2.5 py-0.5 rounded text-[11px] font-medium bg-emerald-950/70 text-emerald-300 border border-emerald-800 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> Resolved
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
