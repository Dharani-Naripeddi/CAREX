import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { patientJourneyApi, patientsApi } from '../services/api';
import { PatientJourneyResponse, PatientJourneyEvent } from '../types/demo';
import {
  Layers,
  User,
  Calendar,
  Clock,
  Activity,
  FileText,
  Pill,
  Bed,
  CreditCard,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ChevronDown,
  Stethoscope,
} from 'lucide-react';

export const PatientJourneyPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [patientId, setPatientId] = useState<number>(Number(id) || 1);
  const [journey, setJourney] = useState<PatientJourneyResponse | null>(null);
  const [patientsList, setPatientsList] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Load available patients for selector
  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await patientsApi.list();
        const items = Array.isArray(res) ? res : (res as any)?.items || [];
        setPatientsList(items);
      } catch (err) {
        console.error('Failed to load patients list:', err);
      }
    };
    fetchPatients();
  }, []);

  // Fetch journey when patientId changes
  useEffect(() => {
    const fetchJourney = async () => {
      try {
        setLoading(true);
        const data = await patientJourneyApi.getJourney(patientId);
        setJourney(data);
      } catch (err) {
        console.error('Failed to load patient journey:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchJourney();
  }, [patientId]);

  const handlePatientSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = Number(e.target.value);
    setPatientId(newId);
    navigate(`/patients/${newId}/journey`);
  };

  const getStageIcon = (stageName: string) => {
    if (stageName.includes('Registration')) return <User className="w-4 h-4" />;
    if (stageName.includes('Appointment')) return <Calendar className="w-4 h-4" />;
    if (stageName.includes('Token') || stageName.includes('OPD')) return <Clock className="w-4 h-4" />;
    if (stageName.includes('Emergency') || stageName.includes('Triage')) return <Activity className="w-4 h-4" />;
    if (stageName.includes('Lab') || stageName.includes('Diagnostic')) return <FileText className="w-4 h-4" />;
    if (stageName.includes('Prescription') || stageName.includes('Pharmacy')) return <Pill className="w-4 h-4" />;
    if (stageName.includes('Admission') || stageName.includes('Bed')) return <Bed className="w-4 h-4" />;
    if (stageName.includes('Billing') || stageName.includes('Invoice')) return <CreditCard className="w-4 h-4" />;
    return <Stethoscope className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
              <Layers className="w-6 h-6 text-purple-400" />
              Unified Patient Care Journey
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
              End-to-End Care Orchestration
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Complete longitudinal patient trajectory across Registration, OPD, Emergency, Labs, Pharmacy, Inpatient, and Billing.
          </p>
        </div>

        {/* Patient Switcher Dropdown */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-medium text-slate-400 hidden sm:block">
            Select Patient:
          </label>
          <div className="relative">
            <select
              value={patientId}
              onChange={handlePatientSelect}
              className="appearance-none bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 pr-8 focus:ring-2 focus:ring-purple-500 focus:outline-none cursor-pointer"
            >
              {patientsList.map((p: any) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} ({p.mrn})
                </option>
              ))}
              {patientsList.length === 0 && (
                <option value={patientId}>Patient #{patientId} (Demo)</option>
              )}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center p-12">
          <div className="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
        </div>
      )}

      {journey && !loading && (
        <>
          {/* Patient Profile Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/40">
            <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300 font-bold text-lg">
                  {journey.patient_name.charAt(0)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-slate-100">
                      {journey.patient_name}
                    </h2>
                    <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-purple-300 border border-purple-500/30">
                      {journey.mrn}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400 mt-1">
                    <span>Age: <strong>{journey.age || '42'}</strong></span>
                    <span>Gender: <strong>{journey.gender || 'Male'}</strong></span>
                    <span>Blood Group: <strong className="text-red-400">{journey.blood_group || 'O+'}</strong></span>
                    <span>
                      Status:{' '}
                      <span className="font-semibold text-emerald-400">
                        {journey.admission_status}
                      </span>
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  {journey.events_count} Clinical Milestones
                </span>
              </div>
            </div>

            {/* Allergies & Current Medications Bar */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3 text-xs">
              <div className="flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                    Documented Allergies
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {journey.allergies && journey.allergies.length > 0 ? (
                      journey.allergies.map((a: string, i: number) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[11px]">
                          {a}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-400">No known allergies</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
                <Pill className="w-3.5 h-3.5 text-indigo-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                    Active Medications
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {journey.current_medications && journey.current_medications.length > 0 ? (
                      journey.current_medications.map((m: string, i: number) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[11px]">
                          {m}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-400">Standard formulary</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Timeline of Care Stages */}
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              Chronological Care Trajectory &amp; AI Decision Logs
            </h3>

            <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
              {journey.journey_stages.map((stage: PatientJourneyEvent) => {
                const isAlert = stage.is_clinical_alert;

                return (
                  <div key={stage.stage_id} className="relative group">
                    {/* Timeline Dot */}
                    <div
                      className={`absolute -left-[1.85rem] top-1.5 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
                        isAlert
                          ? 'border-red-500 bg-red-950 text-red-400 ring-4 ring-red-500/10 animate-pulse'
                          : 'border-purple-500 bg-slate-900 text-purple-400 group-hover:scale-110'
                      }`}
                    >
                      {getStageIcon(stage.stage_name)}
                    </div>

                    {/* Stage Card */}
                    <div
                      className={`rounded-xl border p-4 transition-all duration-200 ${
                        isAlert
                          ? 'border-red-500/30 bg-red-950/10 hover:border-red-500/50'
                          : 'border-slate-800 bg-slate-900/70 hover:border-slate-700 hover:bg-slate-900/90'
                      }`}
                    >
                      {/* Top Bar: Stage Name, Time, Role */}
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
                            STAGE 0{stage.stage_id}
                          </span>
                          <h4 className="text-sm font-bold text-slate-100">
                            {stage.stage_name}
                          </h4>
                          <span className="text-xs text-purple-400 font-mono">
                            • {stage.department}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {stage.timestamp}
                          </span>
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800/90 border border-slate-700 text-slate-300">
                            {stage.responsible_role}
                          </span>
                        </div>
                      </div>

                      {/* Summary */}
                      <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                        {stage.summary}
                      </p>

                      {/* Structured Details Grid */}
                      {stage.details && Object.keys(stage.details).length > 0 && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 text-xs">
                          {Object.entries(stage.details).map(([k, v]) => (
                            <div key={k} className="flex flex-col">
                              <span className="text-[10px] text-slate-400 uppercase tracking-wider">
                                {k}
                              </span>
                              <span className="font-semibold text-slate-200 mt-0.5">
                                {String(v)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* AI Intelligence Insight Box */}
                      {stage.ai_insight && (
                        <div className="flex items-start gap-2 bg-gradient-to-r from-purple-950/30 to-indigo-950/30 border border-purple-500/20 p-2.5 rounded-lg text-xs text-purple-200">
                          <Sparkles className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                          <div className="space-y-0.5">
                            <span className="text-[10px] uppercase font-bold tracking-wider text-purple-300">
                              CAREX Decision Support Telemetry:
                            </span>
                            <p className="text-xs text-purple-200/90">
                              {stage.ai_insight}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
