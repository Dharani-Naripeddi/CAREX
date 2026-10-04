import React from "react";
import {
  Users,
  Stethoscope,
  BedDouble,
  Activity,
  HeartPulse,
  AlertTriangle,
  FlaskConical,
  Pill,
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  CheckCircle,
  FileText,
  CreditCard,
  Bell,
  ShieldCheck,
  ScrollText,
  Database,
  Cpu,
  Ticket,
  Truck,
  AlertOctagon,
  CheckCircle2,
} from "lucide-react";
import { KPIItem } from "../../types/dashboard";
import { clsx } from "clsx";

const iconMap: Record<string, React.ReactNode> = {
  Users: <Users className="w-5 h-5" />,
  Stethoscope: <Stethoscope className="w-5 h-5" />,
  BedDouble: <BedDouble className="w-5 h-5" />,
  Activity: <Activity className="w-5 h-5" />,
  HeartPulse: <HeartPulse className="w-5 h-5" />,
  AlertTriangle: <AlertTriangle className="w-5 h-5" />,
  FlaskConical: <FlaskConical className="w-5 h-5" />,
  Pill: <Pill className="w-5 h-5" />,
  Calendar: <Calendar className="w-5 h-5" />,
  Clock: <Clock className="w-5 h-5" />,
  CheckCircle: <CheckCircle className="w-5 h-5" />,
  CheckCircle2: <CheckCircle2 className="w-5 h-5" />,
  FileText: <FileText className="w-5 h-5" />,
  CreditCard: <CreditCard className="w-5 h-5" />,
  Bell: <Bell className="w-5 h-5" />,
  ShieldCheck: <ShieldCheck className="w-5 h-5" />,
  ScrollText: <ScrollText className="w-5 h-5" />,
  Database: <Database className="w-5 h-5" />,
  Cpu: <Cpu className="w-5 h-5" />,
  Ticket: <Ticket className="w-5 h-5" />,
  Truck: <Truck className="w-5 h-5" />,
  AlertOctagon: <AlertOctagon className="w-5 h-5" />,
};

export const KPICard: React.FC<{ kpi: KPIItem }> = ({ kpi }) => {
  const statusStyles = {
    normal: {
      border: "border-slate-800 hover:border-sky-500/30",
      iconBg: "bg-sky-500/10 text-sky-400 border border-sky-500/20",
      glow: "hover:shadow-sky-950/40",
    },
    warning: {
      border: "border-amber-500/30 hover:border-amber-500/50",
      iconBg: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
      glow: "hover:shadow-amber-950/40",
    },
    critical: {
      border: "border-rose-500/40 hover:border-rose-500/60 bg-rose-950/10",
      iconBg: "bg-rose-500/15 text-rose-400 border border-rose-500/30",
      glow: "hover:shadow-rose-950/50 shadow-rose-950/20",
    },
    info: {
      border: "border-slate-800 hover:border-cyan-500/30",
      iconBg: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20",
      glow: "hover:shadow-cyan-950/40",
    },
  };

  const currentStatus = statusStyles[kpi.status] || statusStyles.normal;
  const icon = iconMap[kpi.icon_name] || <Activity className="w-5 h-5" />;

  return (
    <div
      className={clsx(
        "rounded-2xl bg-slate-900/70 p-5 backdrop-blur-md transition-all duration-300 hover:-translate-y-1 shadow-lg border",
        currentStatus.border,
        currentStatus.glow
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider line-clamp-1">
          {kpi.title}
        </span>
        <div className={clsx("w-9 h-9 rounded-xl flex items-center justify-center shrink-0", currentStatus.iconBg)}>
          {icon}
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-2 mb-2">
        <span className="text-2xl font-extrabold tracking-tight text-white">{kpi.value}</span>
        {kpi.change_percentage !== 0 && (
          <span
            className={clsx(
              "inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full border",
              kpi.is_positive
                ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                : "text-rose-400 bg-rose-500/10 border-rose-500/30"
            )}
          >
            {kpi.is_positive ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {Math.abs(kpi.change_percentage)}%
          </span>
        )}
      </div>

      <p className="text-[11px] text-slate-400 truncate">{kpi.subtext}</p>
    </div>
  );
};
