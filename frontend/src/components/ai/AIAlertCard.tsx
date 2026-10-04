import React, { useState } from "react";
import { AIAlert, AIAlertSeverity, AIAlertStatus } from "../../types/ai";
import { aiApi } from "../../services/api";
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle,
  Clock,
  ArrowRight,
  Check,
  XCircle,
} from "lucide-react";

interface AIAlertCardProps {
  alert: AIAlert;
  onStatusChanged?: () => void;
  className?: string;
}

export const AIAlertCard: React.FC<AIAlertCardProps> = ({
  alert,
  onStatusChanged,
  className = "",
}) => {
  const [loading, setLoading] = useState(false);

  const handleAcknowledge = async () => {
    setLoading(true);
    try {
      await aiApi.acknowledgeAlert(alert.id);
      if (onStatusChanged) onStatusChanged();
    } catch (e) {
      console.error("Error acknowledging alert:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async () => {
    setLoading(true);
    try {
      await aiApi.resolveAlert(alert.id);
      if (onStatusChanged) onStatusChanged();
    } catch (e) {
      console.error("Error resolving alert:", e);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityConfig = (sev: AIAlertSeverity) => {
    switch (sev) {
      case "CRITICAL":
        return {
          border: "border-rose-700/60 bg-rose-950/30",
          icon: <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0" />,
          badge: "bg-rose-900/50 text-rose-300 border-rose-700/60",
        };
      case "HIGH":
        return {
          border: "border-amber-700/60 bg-amber-950/30",
          icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
          badge: "bg-amber-900/50 text-amber-300 border-amber-700/60",
        };
      case "WARNING":
        return {
          border: "border-yellow-700/60 bg-yellow-950/30",
          icon: <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0" />,
          badge: "bg-yellow-900/50 text-yellow-300 border-yellow-700/60",
        };
      case "INFO":
      default:
        return {
          border: "border-blue-700/60 bg-blue-950/30",
          icon: <Info className="w-5 h-5 text-blue-400 shrink-0" />,
          badge: "bg-blue-900/50 text-blue-300 border-blue-700/60",
        };
    }
  };

  const config = getSeverityConfig(alert.severity);

  return (
    <div
      className={`rounded-xl border p-4 shadow-md backdrop-blur-md transition-all ${config.border} ${className}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {config.icon}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm font-semibold text-white">{alert.title}</h4>
              <span
                className={`px-2 py-0.5 rounded-full border text-[10px] font-bold ${config.badge}`}
              >
                {alert.severity}
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                {alert.alert_type}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">{alert.description}</p>
          </div>
        </div>

        {/* Status Actions */}
        <div className="flex items-center gap-2">
          {alert.status === "ACTIVE" && (
            <>
              <button
                disabled={loading}
                onClick={handleAcknowledge}
                className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1 transition-colors"
              >
                <Clock className="w-3 h-3 text-amber-400" /> Acknowledge
              </button>
              <button
                disabled={loading}
                onClick={handleResolve}
                className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-600/40 flex items-center gap-1 transition-colors"
              >
                <Check className="w-3 h-3" /> Resolve
              </button>
            </>
          )}
          {alert.status === "ACKNOWLEDGED" && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/60">
                Acknowledged
              </span>
              <button
                disabled={loading}
                onClick={handleResolve}
                className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-600/40 flex items-center gap-1 transition-colors"
              >
                <Check className="w-3 h-3" /> Resolve
              </button>
            </div>
          )}
          {alert.status === "RESOLVED" && (
            <span className="text-[11px] font-medium text-emerald-400 bg-emerald-950/60 px-2.5 py-1 rounded border border-emerald-800/60 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> Resolved
            </span>
          )}
        </div>
      </div>

      {/* Recommended Action */}
      {alert.recommended_action && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/50 flex items-start gap-2 text-xs">
          <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
          <span className="text-slate-300">
            <strong className="text-indigo-300">Protocol:</strong> {alert.recommended_action}
          </span>
        </div>
      )}
    </div>
  );
};
