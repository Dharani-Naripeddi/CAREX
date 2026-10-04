import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { aiApi, patientsApi } from "../services/api";
import { DocumentAnalysisResponse } from "../types/ai";
import { DocumentIntelligenceViewer } from "../components/ai/DocumentIntelligenceViewer";
import {
  FileText,
  Upload,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  FileCode,
  ArrowRight,
  User,
} from "lucide-react";

export const DocumentAiPage: React.FC = () => {
  const [selectedPatientId, setSelectedPatientId] = useState<string>("");
  const [fileName, setFileName] = useState("diagnostic_pathology_report.pdf");
  const [documentType, setDocumentType] = useState("LABORATORY_REPORT");
  const [rawText, setRawText] = useState(
    `CAREX METROPOLITAN HOSPITAL - CLINICAL BIOCHEMISTRY & HEMATOLOGY\nPatient: Johnathan Doe (CRX-2026-0001)\nInvestigation Parameters:\nHemoglobin (Hb): 10.4 g/dL (Reference: 12.0 - 17.5)\nTotal Leukocyte Count (WBC): 14.8 10^3/uL (Reference: 4.5 - 11.0)\nPlatelet Count: 285 10^3/uL (Reference: 150 - 450)\nFasting Blood Glucose: 138 mg/dL (Reference: 70 - 100)\nSerum Creatinine: 1.1 mg/dL (Reference: 0.6 - 1.2)\nSerum Potassium (K+): 4.2 mEq/L (Reference: 3.5 - 5.0)`
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DocumentAnalysisResponse | null>(null);

  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(),
  });

  const handlePatientChange = (patientId: string) => {
    setSelectedPatientId(patientId);
    const p = patients?.find((item) => item.id.toString() === patientId);
    if (p) {
      setRawText(
        `CAREX METROPOLITAN HOSPITAL - CLINICAL BIOCHEMISTRY & HEMATOLOGY\nPatient: ${p.full_name} (${p.mrn})\nAge: ${p.age} | Gender: ${p.gender} | Blood: ${p.blood_group || 'Unknown'}\nInvestigation Parameters:\nHemoglobin (Hb): 10.4 g/dL (Reference: 12.0 - 17.5)\nTotal Leukocyte Count (WBC): 14.8 10^3/uL (Reference: 4.5 - 11.0)\nPlatelet Count: 285 10^3/uL (Reference: 150 - 450)\nFasting Blood Glucose: 138 mg/dL (Reference: 70 - 100)\nSerum Creatinine: 1.1 mg/dL (Reference: 0.6 - 1.2)\nSerum Potassium (K+): 4.2 mEq/L (Reference: 3.5 - 5.0)`
      );
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await aiApi.analyzeDocument({
        file_name: fileName,
        file_type: "PDF",
        document_type: documentType,
        raw_text: rawText,
      });
      setResult(res);
    } catch (e) {
      console.error("Document analysis failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Medical Document Intelligence
              </h1>
              <p className="text-xs text-slate-400">
                Automated clinical entity extraction, biological reference range matching, and diagnostic findings summary
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Upload / Input Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Ingestion Card */}
        <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-lg space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Upload className="w-3.5 h-3.5 text-indigo-400" /> Ingest Diagnostic Document
            </h3>
            <span className="text-[11px] text-slate-400">PDF / JPG / OCR Text</span>
          </div>

          <div>
            <label className="text-[11px] font-medium text-slate-400 block mb-1">
              Populate from Registered Patient (MPI)
            </label>
            <select
              value={selectedPatientId}
              onChange={(e) => handlePatientChange(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 mb-3"
            >
              <option value="">-- Choose Patient from Master Index --</option>
              {patients?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name} ({p.mrn}) — {p.gender}, {p.age} yrs
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">
                File Identifier
              </label>
              <input
                type="text"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">
                Document Category
              </label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="LABORATORY_REPORT">Laboratory Pathology Report</option>
                <option value="DISCHARGE_SUMMARY">Discharge Summary</option>
                <option value="RADIOLOGY_REPORT">Radiology Diagnostic Note</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-medium text-slate-400 block mb-1">
              Document Text / Extracted OCR Stream
            </label>
            <textarea
              rows={7}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              className="w-full bg-slate-950 font-mono border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            disabled={loading}
            onClick={handleAnalyze}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-950/40 transition-all"
          >
            {loading ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin" /> Analyzing Document with CAREX AI...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" /> Extract Biological Parameters & Findings
              </>
            )}
          </button>
        </div>

        {/* Output Viewer */}
        <div>
          {result ? (
            <DocumentIntelligenceViewer document={result} />
          ) : (
            <div className="h-full p-8 border-2 border-dashed border-slate-800 rounded-xl flex flex-col items-center justify-center text-center space-y-2 text-slate-500">
              <FileCode className="w-10 h-10 text-slate-600" />
              <p className="text-xs">
                Submit or ingest a medical laboratory document on the left to view extracted biological parameters and AI summary findings.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
