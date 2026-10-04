import React from "react";
import { Modal } from "../ui/Modal";
import { HospitalBrainEvent } from "../../types/hospital_brain";
import { AIModelStatusBadge } from "../ai/AIModelStatusBadge";
import {
  Brain,
  HelpCircle,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Layers,
  Sparkles,
  Info,
  CheckCircle2,
} from "lucide-react";

interface HospitalBrainWhyModalProps {
  event: HospitalBrainEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

export const HospitalBrainWhyModal: React.FC<HospitalBrainWhyModalProps> = ({
  event,
  isOpen,
  onClose,
}) => {
  if (!event) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Hospital Brain Explainability & Contributing Factors"
      maxWidth="2xl"
    >
      <div className="space-y-5">
        {/* Header Summary */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-indigo-400" />
              <h4 className="text-sm font-bold text-white">{event.title}</h4>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-800 text-xs font-bold">
                {event.severity} SEVERITY
              </span>
              <AIModelStatusBadge
                providerType={event.explanation.model_provider_type}
                version={event.explanation.model_version}
                confidence={event.explanation.confidence}
              />
            </div>
          </div>
          <p className="text-xs text-slate-300">{event.description}</p>
        </div>

        {/* 1. What is Happening? & What is Expected? */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
            <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-cyan-400" /> What is happening?
            </h5>
            <p className="text-xs text-slate-200 leading-relaxed">
              {event.explanation.what_is_happening}
            </p>
          </div>

          <div className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
            <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-indigo-400" /> What is expected?
            </h5>
            <p className="text-xs text-slate-200 leading-relaxed">
              {event.explanation.what_is_expected}
            </p>
          </div>
        </div>

        {/* 2. Why is CAREX Flagging This? (Contributing Telemetry) */}
        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-2.5">
          <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800 pb-2">
            <Sparkles className="w-4 h-4 text-indigo-400" /> Why is CAREX Flagging This? (Contributing Telemetry Signals)
          </h5>

          <div className="space-y-2 pl-1">
            {event.explanation.why_flagged.map((reason, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs text-slate-200">
                <span className="text-indigo-400 font-bold mt-0.5">•</span>
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 3. Operational Priority Score Breakdown */}
        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Operational Priority Score Breakdown
            </h5>
            <span className="text-xs font-black text-indigo-300 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800">
              {event.priority.score}/100 ({event.priority.rating})
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800/80">
                <tr>
                  <th className="py-2 px-2">Scoring Dimension</th>
                  <th className="py-2 px-2">Weight</th>
                  <th className="py-2 px-2">Contribution</th>
                  <th className="py-2 px-2">Factor Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {event.priority.factors.map((f, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2 px-2 font-medium text-slate-200">{f.name}</td>
                    <td className="py-2 px-2 text-slate-400">{f.weight_pct}%</td>
                    <td className="py-2 px-2 font-bold text-indigo-400">+{f.contribution}</td>
                    <td className="py-2 px-2 text-slate-300">{f.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 4. Affected Area & Recommended Operational Protocol */}
        <div className="p-4 bg-indigo-950/40 border border-indigo-900/60 rounded-xl space-y-2.5">
          <div className="flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-indigo-400" />
            <h5 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
              Recommended Operational Review & Playbook
            </h5>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed">
            {event.recommended_action}
          </p>

          <div className="pt-2 border-t border-indigo-900/40 flex flex-wrap items-center gap-4 text-xs text-slate-300">
            <div>
              <strong className="text-indigo-300">Departments:</strong>{" "}
              {event.explanation.affected_departments.join(", ")}
            </div>
            <div>
              <strong className="text-indigo-300">Resources:</strong>{" "}
              {event.explanation.affected_resources.join(", ")}
            </div>
          </div>
        </div>

        {/* Safety Disclaimer */}
        <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs text-slate-400 flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <span>
            <strong>Clinical Safety Requirement:</strong> {event.explanation.safety_disclaimer}
          </span>
        </div>
      </div>
    </Modal>
  );
};
