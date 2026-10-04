import React, { useEffect, useState } from "react";
import { aiApi, bedsApi } from "../services/api";
import { ShiftHandoverResponse, PatientHandoverSummaryItem } from "../types/ai";
import { AIModelStatusBadge } from "../components/ai/AIModelStatusBadge";
import {
  ClipboardList,
  CheckCircle2,
  AlertTriangle,
  Clock,
  User,
  Bed,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  FileCheck,
} from "lucide-react";

export const AiShiftHandoverPage: React.FC = () => {
  const [wards, setWards] = useState<any[]>([]);
  const [selectedWard, setSelectedWard] = useState<string>("1");
  const [selectedShift, setSelectedShift] = useState<string>("MORNING");
  const [loading, setLoading] = useState(true);
  const [handover, setHandover] = useState<ShiftHandoverResponse | null>(null);
  const [isApproving, setIsApproving] = useState(false);
  const [observationsText, setObservationsText] = useState("");

  const loadHandover = async () => {
    setLoading(true);
    try {
      const wardRes = await bedsApi.listWards();
      setWards(wardRes || []);

      const res = await aiApi.generateHandover({
        ward_id: selectedWard ? parseInt(selectedWard) : undefined,
        shift_name: selectedShift,
      });
      setHandover(res);
      setObservationsText(res.important_observations);
    } catch (e) {
      console.error("Failed to generate shift handover:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHandover();
  }, [selectedWard, selectedShift]);

  const handleApprove = async () => {
    if (!handover?.handover_id) return;
    setIsApproving(true);
    try {
      await aiApi.approveHandover(handover.handover_id, {
        important_observations: observationsText,
      });
      await loadHandover();
    } catch (e) {
      console.error("Approval error:", e);
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-teal-600/20 text-teal-400 border border-teal-500/30">
              <ClipboardList className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                AI Nursing Shift Handover Assistant
              </h1>
              <p className="text-xs text-slate-400">
                Automated clinical summarization across active inpatients, pending diagnostic investigations, and MAR checklists
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {handover && (
            <AIModelStatusBadge
              providerType={handover.model_provider_type}
              version={handover.model_version}
            />
          )}
          <button
            onClick={loadHandover}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>
      </div>

      {/* Ward & Shift Filter Bar */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Select Ward
            </label>
            <select
              value={selectedWard}
              onChange={(e) => setSelectedWard(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500"
            >
              {wards.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} ({w.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Shift Window
            </label>
            <select
              value={selectedShift}
              onChange={(e) => setSelectedShift(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500"
            >
              <option value="MORNING">Morning Shift (07:00 – 15:00)</option>
              <option value="EVENING">Evening Shift (15:00 – 23:00)</option>
              <option value="NIGHT">Night Shift (23:00 – 07:00)</option>
            </select>
          </div>
        </div>

        {handover && (
          <div className="flex items-center gap-2">
            {handover.is_approved ? (
              <span className="px-3 py-1 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800 text-xs font-semibold flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" /> Shift Approved by {handover.from_nurse_name}
              </span>
            ) : (
              <button
                disabled={isApproving}
                onClick={handleApprove}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-teal-950/40 transition-colors"
              >
                <FileCheck className="w-4 h-4" /> Review & Approve Shift Handover
              </button>
            )}
          </div>
        )}
      </div>

      {/* Patient Cards Grid */}
      {handover && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Active Inpatients Handover ({handover.patient_summaries.length} Admitted Patients)
            </h3>
            <span className="text-xs text-amber-400 font-medium">
              {handover.high_priority_patients} High Acuity Profiles
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {handover.patient_summaries.map((p) => (
              <div
                key={p.admission_id}
                className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-lg space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400">
                      <User className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">{p.patient_name}</h4>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {p.patient_mrn} • Bed: {p.bed_number}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      p.priority === "HIGH"
                        ? "bg-rose-950/80 text-rose-300 border-rose-800"
                        : "bg-emerald-950/80 text-emerald-300 border-emerald-800"
                    }`}
                  >
                    {p.priority} PRIORITY
                  </span>
                </div>

                {/* Vitals Bar */}
                <div className="grid grid-cols-4 gap-1 text-[11px] bg-slate-950/60 p-2 rounded-lg border border-slate-800/80 text-center">
                  {Object.entries(p.latest_vitals).map(([k, v]) => (
                    <div key={k}>
                      <span className="text-slate-400 block text-[9px]">{k}</span>
                      <strong className="text-slate-200">{v}</strong>
                    </div>
                  ))}
                </div>

                {/* Observations */}
                <p className="text-xs text-slate-300 leading-relaxed">
                  {p.important_observations}
                </p>

                {/* Key Nursing Tasks */}
                <div className="space-y-1 text-xs">
                  <span className="text-[11px] font-semibold text-slate-400 block">
                    Next Shift Action Items:
                  </span>
                  {p.key_tasks.map((task, idx) => (
                    <div key={idx} className="flex items-start gap-1.5 text-slate-300">
                      <span className="text-teal-400 font-bold">•</span>
                      <span>{task}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Shift Checklist & Notes */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-lg space-y-4">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" /> Nursing Team Shift Checklist
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {handover.next_shift_checklist.map((item, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-start gap-2 text-xs text-slate-300"
                >
                  <input
                    type="checkbox"
                    defaultChecked
                    className="mt-0.5 rounded bg-slate-800 border-slate-700 text-teal-600 focus:ring-0"
                  />
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Nurse Shift Handover Notes (Editable)
              </label>
              <textarea
                rows={3}
                value={observationsText}
                onChange={(e) => setObservationsText(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
