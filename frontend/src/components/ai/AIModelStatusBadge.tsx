import React from "react";
import { ModelProviderType } from "../../types/ai";
import { Cpu, Activity, ShieldCheck, Zap } from "lucide-react";

interface AIModelStatusBadgeProps {
  providerType: ModelProviderType;
  version?: string;
  confidence?: number;
  className?: string;
}

export const AIModelStatusBadge: React.FC<AIModelStatusBadgeProps> = ({
  providerType,
  version,
  confidence,
  className = "",
}) => {
  const getBadgeConfig = () => {
    switch (providerType) {
      case "TRAINED_ML":
        return {
          label: "Trained ML",
          icon: <Cpu className="w-3 h-3 text-purple-400" />,
          bg: "bg-purple-950/60 border-purple-800/60 text-purple-200",
          dot: "bg-purple-400",
        };
      case "STATISTICAL_MODEL":
        return {
          label: "Statistical Engine",
          icon: <Activity className="w-3 h-3 text-cyan-400" />,
          bg: "bg-cyan-950/60 border-cyan-800/60 text-cyan-200",
          dot: "bg-cyan-400",
        };
      case "RULE_BASED":
        return {
          label: "Clinical Guidelines",
          icon: <ShieldCheck className="w-3 h-3 text-emerald-400" />,
          bg: "bg-emerald-950/60 border-emerald-800/60 text-emerald-200",
          dot: "bg-emerald-400",
        };
      case "FALLBACK_SIMULATION":
      default:
        return {
          label: "Operational Estimate",
          icon: <Zap className="w-3 h-3 text-amber-400" />,
          bg: "bg-amber-950/60 border-amber-800/60 text-amber-200",
          dot: "bg-amber-400",
        };
    }
  };

  const config = getBadgeConfig();

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium backdrop-blur-sm ${config.bg} ${className}`}
      title={
        confidence !== undefined
          ? `Model Confidence: ${(confidence * 100).toFixed(0)}%`
          : "Deterministic Rule-Based / Operational Estimate"
      }
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot} animate-pulse`} />
      {config.icon}
      <span>{config.label}</span>
      {version && (
        <span className="text-[10px] opacity-70 border-l border-current/20 pl-1.5">
          {version}
        </span>
      )}
      {confidence !== undefined && (
        <span className="text-[10px] font-semibold opacity-90 border-l border-current/20 pl-1.5">
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
};
