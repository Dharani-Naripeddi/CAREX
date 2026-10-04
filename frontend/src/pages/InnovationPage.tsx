import React from 'react';
import {
  Cpu,
  Brain,
  Shield,
  Layers,
  Activity,
  CheckCircle2,
  FileCheck,
  AlertOctagon,
  Sparkles,
  GitBranch,
  Network,
  Clock,
  Pill,
  Mic,
  FileText,
  Users,
} from 'lucide-react';

export const InnovationPage: React.FC = () => {
  const aiCapabilities = [
    {
      id: 1,
      name: 'OPD Queue Wait-Time Forecasting',
      category: 'OPERATIONAL INTELLIGENCE',
      provider: 'TRAINED_ML',
      providerBadge: 'Gradient Boosting (XGBoost / LightGBM)',
      description:
        'Continuous regression on historical doctor consultation pacing, day-of-week arrival vectors, token queue length, and departmental backlog.',
      inputSignals: ['Doctor pacing rate', 'Queue depth', 'Time of day', 'Token priority'],
      output: 'Predicted minutes to consultation with 95% confidence intervals',
      latency: '< 12ms',
    },
    {
      id: 2,
      name: 'Bed Occupancy & Turnover Prediction',
      category: 'CAPACITY MANAGEMENT',
      provider: 'STATISTICAL_MODEL',
      providerBadge: 'Time-Series Decomposition & Survival Analysis',
      description:
        'Calculates 24-hour and 48-hour forward bed availability across General Wards, ICU, CCU, and Step-down units using discharge trajectory modeling.',
      inputSignals: ['Length of stay (LOS)', 'Discharge probability', 'Active admissions', 'Bed turnover time'],
      output: 'Projected bed saturation percentage and early bottleneck alerts',
      latency: '< 15ms',
    },
    {
      id: 3,
      name: 'Pharmacy Stock Depletion Velocity Engine',
      category: 'SUPPLY CHAIN FORECASTING',
      provider: 'STATISTICAL_MODEL',
      providerBadge: 'Consumption Velocity & Moving Averages',
      description:
        'Monitors high-risk antibiotics, insulin, and emergency therapeutics against active inpatient census consumption rates to trigger proactive reorder POs.',
      inputSignals: ['Daily dispensing rate', 'Inpatient census', 'Batch expiry dates', 'Safety stock buffer'],
      output: 'Depletion date estimation and emergency replenishment trigger',
      latency: '< 8ms',
    },
    {
      id: 4,
      name: 'Emergency Triage Decision Support (CDSS)',
      category: 'CLINICAL DECISION SUPPORT',
      provider: 'TRAINED_ML',
      providerBadge: 'Supervised Multi-Class Classifier + Clinical Rules',
      description:
        'Assists triage nurses by synthesizing SpO2, systolic BP, heart rate, Glasgow Coma Scale, and chief symptoms into standard Emergency Severity Index levels.',
      inputSignals: ['Physiological vitals', 'Pain score', 'Symptom acuity', 'Age comorbidities'],
      output: 'Recommended triage priority (Red/Orange/Yellow/Green) with contributing factor weights',
      latency: '< 20ms',
    },
    {
      id: 5,
      name: 'Medical Document Intelligence',
      category: 'NATURAL LANGUAGE PROCESSING',
      provider: 'TRAINED_ML',
      providerBadge: 'BioBERT / Clinical NER Entity Extraction',
      description:
        'Automatically parses unstructured discharge summaries, operative notes, and lab diagnostic slips into structured parameters with confidence ratings.',
      inputSignals: ['OCR text streams', 'Clinical document strings', 'Diagnostic parameters'],
      output: 'Extracted key-value clinical entities with confidence scores',
      latency: '< 45ms',
    },
    {
      id: 6,
      name: 'Voice-to-Clinical-Note Dictation',
      category: 'SPEECH INTELLIGENCE',
      provider: 'TRAINED_ML',
      providerBadge: 'Whisper-based ASR + Medical Lexicon Tuning',
      description:
        'Real-time doctor voice capture into SOAP (Subjective, Objective, Assessment, Plan) formatted electronic health records.',
      inputSignals: ['Raw audio stream', 'Doctor specialization context'],
      output: 'Structured SOAP consultation notes with automated ICD-10 suggestions',
      latency: '< 120ms',
    },
    {
      id: 7,
      name: 'Nursing Shift Handover Intelligence',
      category: 'WORKFLOW COORDINATION',
      provider: 'RULE_BASED',
      providerBadge: 'Deterministic Clinical Synthesis Engine',
      description:
        'Synthesizes 12-hour vitals volatility, new medication orders, pending STAT labs, and critical alerts into an automated SBAR handover briefing.',
      inputSignals: ['Vitals history', 'Active orders', 'Lab alerts', 'Doctor notes'],
      output: 'Complete SBAR briefing document for incoming registered nurses',
      latency: '< 10ms',
    },
    {
      id: 8,
      name: 'Operational Anomaly Detection & Cross-Correlation',
      category: 'HOSPITAL BRAIN CORE',
      provider: 'TRAINED_ML',
      providerBadge: 'Isolation Forest & Graph Signal Correlator',
      description:
        'Detects compound hospital strain by correlating OPD token surges with emergency bay occupancy and diagnostic TAT delays.',
      inputSignals: ['Cross-department telemetry', 'Queue anomalies', 'Discharge delays'],
      output: 'Composite 0-100 Operational Priority Score and Action Center alerts',
      latency: '< 18ms',
    },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
              <Cpu className="w-6 h-6 text-indigo-400" />
              CAREX Innovation &amp; AI Intelligence Architecture
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              SIH Technical Dossier
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Comprehensive breakdown of CAREX intelligence models, explainability engines, clinical safety guardrails, and hospital orchestration pipelines.
          </p>
        </div>
      </div>

      {/* Flagship Pillars Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 to-slate-900/80 p-5 shadow-lg">
          <div className="p-2.5 rounded-lg bg-indigo-500/20 text-indigo-400 w-fit mb-3">
            <Brain className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-100 mb-1">
            Centralized Hospital Brain
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Eliminates traditional siloed departmental software by aggregating OPD, IPD, Emergency, Labs, and Pharmacy into a unified graph intelligence layer with 0–100 operational priority scoring.
          </p>
        </div>

        <div className="rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-950/40 to-slate-900/80 p-5 shadow-lg">
          <div className="p-2.5 rounded-lg bg-purple-500/20 text-purple-400 w-fit mb-3">
            <Layers className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-100 mb-1">
            Explainable AI (XAI)
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Every operational alert and clinical prediction provides transparent, auditable reasoning factors, feature weights, and suggested human-in-the-loop clinical protocols.
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 to-slate-900/80 p-5 shadow-lg">
          <div className="p-2.5 rounded-lg bg-emerald-500/20 text-emerald-400 w-fit mb-3">
            <Shield className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-100 mb-1">
            Clinical Safety Guardrails
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Strict human-in-the-loop architecture. All clinical orders, triage decisions, and prescription verifications require licensed medical professional approval.
          </p>
        </div>
      </div>

      {/* 8 AI Capabilities Matrix */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            The 8 Autonomous AI Capabilities Matrix
          </h2>
          <span className="text-xs font-mono text-slate-400">
            Production-Ready Architecture
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {aiCapabilities.map((cap) => (
            <div
              key={cap.id}
              className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 hover:border-slate-700 hover:bg-slate-900/90 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-indigo-400 uppercase">
                    {cap.category}
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {cap.latency} latency
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-100 mb-1">
                  {cap.name}
                </h3>

                <div className="inline-block text-[11px] font-mono font-medium text-slate-300 bg-slate-950/80 px-2 py-1 rounded border border-slate-800 mb-3">
                  {cap.providerBadge}
                </div>

                <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                  {cap.description}
                </p>
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-800/80 text-xs">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Input Telemetry Streams:
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {cap.inputSignals.map((sig, i) => (
                      <span
                        key={i}
                        className="text-[11px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60"
                      >
                        {sig}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Synthesized Output:
                  </span>
                  <span className="text-xs text-indigo-300 font-medium mt-0.5 block">
                    {cap.output}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Non-Diagnostic Clinical AI Compliance Notice */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-950/10 p-4 text-xs text-amber-200 flex items-start gap-3">
        <AlertOctagon className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="font-bold text-amber-300 block">
            Clinical Decision Support System (CDSS) Regulatory Disclosures:
          </strong>
          <p className="leading-relaxed text-amber-200/90">
            CAREX is engineered as an operational intelligence and clinical decision support platform. In compliance with medical device software standards, CAREX does NOT autonomously diagnose diseases, prescribe medications, or replace certified clinical judgment. All clinical triage scores, drug interaction alerts, and care pathways require explicit verification by authorized medical practitioners.
          </p>
        </div>
      </div>
    </div>
  );
};
