import React, { useState } from "react";
import { Modal } from "../ui/Modal";
import { aiApi } from "../../services/api";
import { VoiceTranscriptionResponse, StructuredClinicalNoteDraft } from "../../types/ai";
import { AIModelStatusBadge } from "./AIModelStatusBadge";
import {
  Mic,
  Square,
  Sparkles,
  FileText,
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCcw,
  Save,
} from "lucide-react";

interface VoiceNoteAssistantModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNoteApproved?: (note: StructuredClinicalNoteDraft, formattedSummary: string) => void;
  patientId?: number;
  patientName?: string;
}

export const VoiceNoteAssistantModal: React.FC<VoiceNoteAssistantModalProps> = ({
  isOpen,
  onClose,
  onNoteApproved,
  patientId,
  patientName,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [timerInterval, setTimerInterval] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VoiceTranscriptionResponse | null>(null);

  // Editable Draft state
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [duration, setDuration] = useState("");
  const [examinationNotes, setExaminationNotes] = useState("");
  const [assessmentPlan, setAssessmentPlan] = useState("");
  const [vitals, setVitals] = useState<Record<string, string>>({});

  const startRecording = () => {
    setIsRecording(true);
    setRecordingSeconds(0);
    const interval = setInterval(() => {
      setRecordingSeconds((prev) => prev + 1);
    }, 1000);
    setTimerInterval(interval);
  };

  const stopAndProcess = async (useDemo: boolean = false) => {
    if (timerInterval) clearInterval(timerInterval);
    setIsRecording(false);
    setLoading(true);

    try {
      const res = await aiApi.transcribeVoice({
        patient_id: patientId,
        use_demo_sample: useDemo,
        audio_text: useDemo
          ? undefined
          : "Patient reports acute persistent dry cough and fever for 3 days. Temperature 101.4 F, BP 130/85. Chest auscultation shows mild expiratory wheezing. Plan CBC, Chest X-ray, bronchodilator.",
      });

      setResult(res);
      setChiefComplaint(res.structured_note.chief_complaint);
      setDuration(res.structured_note.duration || "3 days");
      setExaminationNotes(res.structured_note.examination_notes);
      setAssessmentPlan(res.structured_note.suggested_assessment_plan);
      setVitals(res.structured_note.vital_signs_mentioned || {});
    } catch (e) {
      console.error("Transcription error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = () => {
    if (result && onNoteApproved) {
      const updatedDraft: StructuredClinicalNoteDraft = {
        chief_complaint: chiefComplaint,
        duration,
        vital_signs_mentioned: vitals,
        associated_symptoms: result.structured_note.associated_symptoms,
        examination_notes: examinationNotes,
        suggested_assessment_plan: assessmentPlan,
      };
      const formatted = `**Chief Complaint:** ${chiefComplaint} (${duration})\n**Exam:** ${examinationNotes}\n**Plan:** ${assessmentPlan}`;
      onNoteApproved(updatedDraft, formatted);
    }
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="AI Voice-to-Clinical-Note Assistant"
      maxWidth="xl"
    >
      <div className="space-y-4">
        {/* Safety Disclaimer */}
        <div className="p-3 bg-amber-950/40 border border-amber-800/50 rounded-lg text-xs text-amber-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>Clinical Safety Requirement:</strong> AI assists clinical note structuring.
            Physician must review, edit, and confirm all fields before saving to chart.
          </span>
        </div>

        {patientName && (
          <div className="text-xs text-slate-400">
            Target Patient: <strong className="text-slate-200">{patientName}</strong>
          </div>
        )}

        {/* Audio Recording Control Bar */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {isRecording ? (
              <button
                onClick={() => stopAndProcess(false)}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-medium text-xs flex items-center gap-2 shadow-lg shadow-rose-900/40 animate-pulse"
              >
                <Square className="w-3.5 h-3.5 fill-current" /> Stop Recording ({recordingSeconds}s)
              </button>
            ) : (
              <button
                onClick={startRecording}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium text-xs flex items-center gap-2 shadow-lg shadow-indigo-900/40"
              >
                <Mic className="w-3.5 h-3.5" /> Start Dictation
              </button>
            )}

            <button
              onClick={() => stopAndProcess(true)}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-medium text-xs flex items-center gap-1.5 border border-slate-700"
            >
              <Play className="w-3 h-3 text-cyan-400" /> Insert Sample Voice Note
            </button>
          </div>

          {result && (
            <AIModelStatusBadge
              providerType={result.model_provider_type}
              version={result.model_version}
            />
          )}
        </div>

        {loading && (
          <div className="p-8 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400 animate-spin" />
            Structuring spoken clinical transcription with CAREX NLP...
          </div>
        )}

        {/* Structured Draft Editor */}
        {result && (
          <div className="space-y-3 bg-slate-900/60 p-4 border border-slate-800 rounded-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h5 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-indigo-400" /> Structured Clinical Note Draft
              </h5>
              <span className="text-[11px] text-amber-400 font-medium">Doctor Sign-Off Required</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">
                  Chief Complaint
                </label>
                <input
                  type="text"
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">
                  Duration
                </label>
                <input
                  type="text"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">
                Clinical Examination Findings
              </label>
              <textarea
                rows={2}
                value={examinationNotes}
                onChange={(e) => setExaminationNotes(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">
                Assessment & Suggested Management Plan
              </label>
              <textarea
                rows={2}
                value={assessmentPlan}
                onChange={(e) => setAssessmentPlan(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Action Buttons */}
            <div className="pt-2 flex justify-end gap-2">
              <button
                onClick={onClose}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium"
              >
                Discard
              </button>
              <button
                onClick={handleApprove}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium flex items-center gap-1.5 shadow-md"
              >
                <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Insert into Consultation Note
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
