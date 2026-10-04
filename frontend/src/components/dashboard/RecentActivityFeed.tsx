import React from "react";
import { RecentActivity } from "../../types/dashboard";
import { Badge } from "../ui/Badge";
import { Stethoscope, FlaskConical, Pill, UserPlus, ShieldAlert, Activity } from "lucide-react";

interface RecentActivityFeedProps {
  activities: RecentActivity[];
}

export const RecentActivityFeed: React.FC<RecentActivityFeedProps> = ({ activities }) => {
  const getCategoryIcon = (category: RecentActivity["category"]) => {
    switch (category) {
      case "PRESCRIPTION":
        return <Pill className="w-4 h-4 text-purple-400" />;
      case "LAB":
        return <FlaskConical className="w-4 h-4 text-sky-400" />;
      case "ADMISSION":
        return <UserPlus className="w-4 h-4 text-emerald-400" />;
      case "DISCHARGE":
        return <Stethoscope className="w-4 h-4 text-amber-400" />;
      default:
        return <Activity className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-white flex items-center gap-2">
          <Activity className="w-4 h-4 text-sky-400" />
          Live Clinical Activity & Audit Trail
        </h4>
        <Badge variant="neutral" size="sm">Realtime</Badge>
      </div>

      <div className="space-y-2.5">
        {activities.map((act) => (
          <div
            key={act.id}
            className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
          >
            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
              {getCategoryIcon(act.category)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-white truncate">
                  {act.user_name}
                  <span className="ml-2 text-[10px] font-normal text-slate-400">({act.role})</span>
                </span>
                <span className="text-[10px] text-slate-500 shrink-0 font-mono">{act.timestamp}</span>
              </div>
              <p className="text-xs font-medium text-sky-300 mt-0.5">{act.action}</p>
              <p className="text-[11px] text-slate-400 mt-0.5 truncate">{act.details}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
