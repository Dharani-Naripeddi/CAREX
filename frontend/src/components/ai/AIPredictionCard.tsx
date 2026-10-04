import React, { useState } from "react";
import { AIPrediction, AIRiskLevel } from "../../types/ai";
import { AIModelStatusBadge } from "./AIModelStatusBadge";
import { aiApi } from "../../services/api";
import {
  HelpCircle,
  ArrowRight,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface AIPredictionCardProps {
  prediction: AIPrediction;
  onFeedbackSubmitted?: () => void;
  className?: string;
}

export const AIPredictionCard: React.FC<AIPredictionCardProps> = ({
  prediction,
  onFeedbackSubmitted,
  className = "",
}) => {
  const [showDetails, setShowDetails] = useState(true);
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFeedback = async (rating: "USEFUL" | "NOT_USEFUL") => {
    setIsSubmitting(true);
    try {
      await aiApi.submitFeedback({
        rating,
        prediction_id: prediction.id,
      });
      setFeedbackSent(rating);
      if (onFeedbackSubmitted) onFeedbackSubmitted();
    } catch (e) {
      console.error("Feedback submission error:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRiskBadge = (risk: AIRiskLevel) => {
    switch (risk) {
      case "CRITICAL":
        return "bg-rose-950/70 text-rose-300 border-rose-800/80";
      case "HIGH":
        return "bg-amber-950/70 text-amber-300 border-amber-800/80";
      case "MEDIUM":
        return "bg-yellow-950/70 text-yellow-300 border-yellow-800/80";
      case "LOW":
      default:
        return "bg-emerald-950/70 text-emerald-300 border-emerald-800/80";
    }
  };

  return (
    <div
      className={`bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-xl p-5 shadow-lg backdrop-blur-md transition-all duration-200 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">
              {prediction.prediction_type.replace(/_/g, " ")}
            </h4>
            <span className="text-[11px] text-slate-400">
              Entity: {prediction.entity_type} {prediction.entity_id ? `(${prediction.entity_id})` : ""}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${getRiskBadge(
              prediction.risk_level
            )}`}
          >
            {prediction.risk_level} RISK
          </span>
          <AIModelStatusBadge
            providerType={prediction.model_provider_type}
            version={prediction.model_version}
            confidence={prediction.confidence}
          />
        </div>
      </div>

      {/* Summary / Result Value */}
      <div className="my-3 text-slate-200 text-sm font-medium">
        <p>{prediction.explanation?.summary || JSON.stringify(prediction.prediction_value)}</p>
      </div>

      {/* Accordion Toggle for Why? Factors */}
      <div className="mt-2">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex items-center justify-between w-full py-1.5 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
            Why? Contributing Factors ({prediction.explanation?.reasons?.length || 0})
          </span>
          {showDetails ? (
            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          )}
        </button>

        {showDetails && (
          <div className="mt-2 pl-3 border-l-2 border-indigo-500/30 space-y-1.5">
            {prediction.explanation?.reasons?.map((reason, idx) => (
              <div key={idx} className="text-xs text-slate-300 flex items-start gap-1.5">
                <span className="text-indigo-400 font-bold">•</span>
                <span>{reason}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommended Action */}
      {prediction.recommended_action && (
        <div className="mt-4 p-3 rounded-lg bg-indigo-950/40 border border-indigo-900/40 flex items-start gap-2.5">
          <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-[11px] font-semibold text-indigo-300 uppercase tracking-wider block">
              Recommended Action
            </span>
            <p className="text-xs text-slate-200 mt-0.5">{prediction.recommended_action}</p>
          </div>
        </div>
      )}

      {/* Footer & Feedback */}
      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
        <span className="text-[11px]">
          Generated: {new Date(prediction.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>

        <div className="flex items-center gap-1.5">
          {feedbackSent ? (
            <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" /> Feedback Received
            </span>
          ) : (
            <>
              <span className="text-[11px] text-slate-400 mr-1">Feedback:</span>
              <button
                disabled={isSubmitting}
                onClick={() => handleFeedback("USEFUL")}
                className="p-1 rounded hover:bg-emerald-950/60 text-slate-400 hover:text-emerald-300 transition-colors"
                title="Accurate & Helpful"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={isSubmitting}
                onClick={() => handleFeedback("NOT_USEFUL")}
                className="p-1 rounded hover:bg-rose-950/60 text-slate-400 hover:text-rose-300 transition-colors"
                title="Needs Review"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
