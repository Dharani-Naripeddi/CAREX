import React from "react";
import { DepartmentStatusSummary, HospitalSystemStatus } from "../../types/hospital_brain";
import {
  Building2,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Layers,
  Clock,
  ArrowRight,
} from "lucide-react";

interface DepartmentStatusMatrixProps {
  departments: DepartmentStatusSummary[];
  onSelectDepartment?: (dept: DepartmentStatusSummary) => void;
  className?: string;
}

export const DepartmentStatusMatrix: React.FC<DepartmentStatusMatrixProps> = ({
  departments,
  onSelectDepartment,
  className = "",
}) => {
  const getStatusConfig = (status: HospitalSystemStatus) => {
    switch (status) {
      case "CRITICAL":
        return {
          dot: "bg-rose-500",
          badge: "bg-rose-950/80 text-rose-300 border-rose-700",
          border: "border-rose-900/60 bg-rose-950/20 hover:border-rose-600",
          statusText: "CRITICAL LOAD",
        };
      case "HIGH_LOAD":
        return {
          dot: "bg-amber-500",
          badge: "bg-amber-950/80 text-amber-300 border-amber-700",
          border: "border-amber-900/60 bg-amber-950/20 hover:border-amber-600",
          statusText: "HIGH LOAD",
        };
      case "WATCH":
        return {
          dot: "bg-yellow-500",
          badge: "bg-yellow-950/80 text-yellow-300 border-yellow-700",
          border: "border-yellow-900/60 bg-yellow-950/20 hover:border-yellow-600",
          statusText: "WATCH LEVEL",
        };
      case "STABLE":
      default:
        return {
          dot: "bg-emerald-500",
          badge: "bg-emerald-950/80 text-emerald-300 border-emerald-700",
          border: "border-slate-800 bg-slate-900/70 hover:border-slate-700",
          statusText: "NOMINAL",
        };
    }
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-indigo-400" />
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Department Operational Intelligence Matrix
          </h3>
        </div>
        <span className="text-xs text-slate-400">
          {departments.length} Units Monitored Real-Time
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {departments.map((dept, idx) => {
          const cfg = getStatusConfig(dept.status);
          return (
            <div
              key={idx}
              onClick={() => onSelectDepartment && onSelectDepartment(dept)}
              className={`p-4 rounded-xl border shadow-md backdrop-blur-md transition-all cursor-pointer ${cfg.border}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-sm font-bold text-white">{dept.department_name}</h4>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Code: {dept.department_code}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${cfg.dot} animate-pulse`} />
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${cfg.badge}`}>
                    {cfg.statusText}
                  </span>
                </div>
              </div>

              {/* Key Metrics Grid */}
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                {Object.entries(dept.key_metrics).slice(0, 2).map(([k, v]) => (
                  <div key={k}>
                    <span className="text-[10px] text-slate-400 uppercase block tracking-wider">
                      {k.replace(/_/g, " ")}
                    </span>
                    <strong className="text-white font-extrabold text-sm">{String(v)}</strong>
                  </div>
                ))}
              </div>

              {/* Recommended Reviews */}
              {dept.recommended_reviews.length > 0 && (
                <div className="mt-2.5 space-y-1 text-xs text-slate-300">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
                    Key Review Item:
                  </span>
                  <p className="text-xs text-slate-200 line-clamp-1">
                    {dept.recommended_reviews[0]}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
