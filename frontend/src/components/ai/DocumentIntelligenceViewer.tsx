import React, { useState } from "react";
import { DocumentAnalysisResponse, ExtractedParameter } from "../../types/ai";
import { AIModelStatusBadge } from "./AIModelStatusBadge";
import { aiApi } from "../../services/api";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
} from "lucide-react";

interface DocumentIntelligenceViewerProps {
  document: DocumentAnalysisResponse;
  onVerified?: () => void;
  className?: string;
}

export const DocumentIntelligenceViewer: React.FC<DocumentIntelligenceViewerProps> = ({
  document,
  onVerified,
  className = "",
}) => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [isVerified, setIsVerified] = useState(document.is_verified);

  const handleVerify = async () => {
    if (!document.document_id) return;
    setIsVerifying(true);
    try {
      await aiApi.verifyDocument(document.document_id);
      setIsVerified(true);
      if (onVerified) onVerified();
    } catch (e) {
      console.error("Document verification error:", e);
    } finally {
      setIsVerifying(false);
    }
  };

  const getFlagBadge = (flag: string) => {
    switch (flag) {
      case "CRITICAL":
        return "bg-rose-950/70 text-rose-300 border-rose-800/80";
      case "HIGH":
        return "bg-amber-950/70 text-amber-300 border-amber-800/80";
      case "LOW":
        return "bg-cyan-950/70 text-cyan-300 border-cyan-800/80";
      case "NORMAL":
      default:
        return "bg-emerald-950/70 text-emerald-300 border-emerald-800/80";
    }
  };

  return (
    <div
      className={`bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-md space-y-4 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/70 pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">{document.file_name}</h4>
            <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
              <span>{document.document_type}</span>
              {document.patient_name && <span>• Patient: {document.patient_name}</span>}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isVerified ? (
            <span className="px-2.5 py-1 rounded-full bg-emerald-950/70 text-emerald-300 border border-emerald-800/80 text-xs font-semibold flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Verified by Clinician
            </span>
          ) : (
            <button
              disabled={isVerifying || !document.document_id}
              onClick={handleVerify}
              className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium flex items-center gap-1.5 transition-colors shadow-md disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" /> Verify & Sign Off
            </button>
          )}

          <AIModelStatusBadge
            providerType={document.model_provider_type}
            version={document.model_version}
            confidence={document.confidence}
          />
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-400">
        <strong className="text-slate-300">Disclaimer:</strong> {document.disclaimer}
      </div>

      {/* Structured Lab Parameters Table */}
      <div>
        <h5 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Extracted Biological Parameters (
          {document.extracted_parameters.length})
        </h5>

        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-2.5 px-3">Parameter</th>
                <th className="py-2.5 px-3">Extracted Result</th>
                <th className="py-2.5 px-3">Unit</th>
                <th className="py-2.5 px-3">Biological Range</th>
                <th className="py-2.5 px-3">Observation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/50">
              {document.extracted_parameters.map((param, idx) => (
                <tr
                  key={idx}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    param.is_abnormal ? "bg-amber-950/10" : ""
                  }`}
                >
                  <td className="py-2 px-3 font-medium text-slate-200">
                    {param.parameter_name}
                  </td>
                  <td className="py-2 px-3 font-mono font-semibold text-white">
                    {param.result_value}
                  </td>
                  <td className="py-2 px-3 text-slate-400">{param.unit}</td>
                  <td className="py-2 px-3 text-slate-400">{param.reference_range}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-semibold ${getFlagBadge(
                        param.flag
                      )}`}
                    >
                      {param.flag === "HIGH" && <ArrowUpRight className="w-3 h-3" />}
                      {param.flag === "LOW" && <ArrowDownRight className="w-3 h-3" />}
                      {param.flag}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Summary Card */}
      <div className="p-3.5 bg-indigo-950/30 border border-indigo-900/50 rounded-xl space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h5 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">
            Diagnostic Findings Summary
          </h5>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed">{document.ai_summary}</p>
      </div>
    </div>
  );
};
