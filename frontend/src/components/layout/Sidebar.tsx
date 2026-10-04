import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import {
  LayoutDashboard,
  Users,
  Calendar,
  Ticket,
  Stethoscope,
  HeartPulse,
  ChevronLeft,
  ChevronRight,
  Activity,
  AlertTriangle,
  BedDouble,
  ShieldCheck,
  Building,
  FlaskConical,
  Pill,
  FileText,
  CreditCard,
  Clock,
  Brain,
  Sparkles,
  Layers,
  Cpu,
} from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  roles?: string[];
  badge?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const { user } = useAuth();
  const location = useLocation();

  const userRole = user?.role || "GUEST";

  const navigationSections: { title: string; items: NavItem[] }[] = [
    {
      title: "Hospital Command Center",
      items: [
        {
          title: "Operations & Capacity Simulator",
          href: "/admin/demo",
          icon: <Sparkles className="w-4 h-4 text-amber-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"],
          badge: "SIM",
        },
        {
          title: "Hospital Brain",
          href: "/admin/hospital-brain",
          icon: <Brain className="w-4 h-4 text-purple-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"],
          badge: "AI CORE",
        },
        {
          title: "Patient Care Journey",
          href: "/patients/1/journey",
          icon: <Layers className="w-4 h-4 text-purple-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST", "PATIENT"],
          badge: "360°",
        },
        {
          title: "Executive Overview",
          href: "/command-center",
          icon: <LayoutDashboard className="w-4 h-4" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN"],
        },
        {
          title: "Clinical Workspace",
          href: `/dashboard/${userRole.toLowerCase()}`,
          icon: <Activity className="w-4 h-4" />,
        },
      ],
    },
    {
      title: "Acute Care & Emergency",
      items: [
        {
          title: "Emergency & Triage",
          href: "/emergency",
          icon: <AlertTriangle className="w-4 h-4 text-rose-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE"],
          badge: "STAT",
        },
        {
          title: "Resource Coordination",
          href: "/resources",
          icon: <Activity className="w-4 h-4 text-sky-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"],
          badge: "Live",
        },
      ],
    },
    {
      title: "Inpatient & Bed Telemetry",
      items: [
        {
          title: "Inpatient (IPD) Care",
          href: "/ipd",
          icon: <BedDouble className="w-4 h-4 text-indigo-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE"],
        },
        {
          title: "Bed & Ward Matrix",
          href: "/beds",
          icon: <Building className="w-4 h-4 text-emerald-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"],
        },
      ],
    },
    {
      title: "Outpatient Operations (OPD)",
      items: [
        {
          title: "Master Patient Index",
          href: "/patients",
          icon: <Users className="w-4 h-4" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE"],
        },
        {
          title: "Appointments Roster",
          href: "/appointments",
          icon: <Calendar className="w-4 h-4" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE", "PATIENT"],
        },
        {
          title: "OPD Token Queue",
          href: "/opd-queue",
          icon: <Ticket className="w-4 h-4" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE", "PATIENT"],
          badge: "Live",
        },
      ],
    },
    {
      title: "Support & Clinical Services",
      items: [
        {
          title: "Laboratory Diagnostics",
          href: "/lab",
          icon: <FlaskConical className="w-4 h-4 text-sky-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECHNICIAN", "PATIENT", "NURSE", "RECEPTIONIST"],
        },
        {
          title: "Pharmacy & Inventory",
          href: "/pharmacy",
          icon: <Pill className="w-4 h-4 text-emerald-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "PHARMACIST", "DOCTOR", "RECEPTIONIST"],
        },
        {
          title: "Electronic Prescriptions",
          href: "/prescriptions",
          icon: <FileText className="w-4 h-4 text-teal-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "PHARMACIST", "PATIENT", "NURSE"],
        },
        {
          title: "Billing & Invoices",
          href: "/billing",
          icon: <CreditCard className="w-4 h-4 text-indigo-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "PATIENT"],
        },
      ],
    },
    {
      title: "AI Intelligence Layer",
      items: [
        {
          title: "AI Intelligence Center",
          href: "/admin/ai",
          icon: <Activity className="w-4 h-4 text-purple-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "PHARMACIST", "LAB_TECHNICIAN", "RECEPTIONIST"],
          badge: "AI",
        },
        {
          title: "OPD Queue Forecast",
          href: "/admin/ai/queue",
          icon: <Clock className="w-4 h-4 text-indigo-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE"],
        },
        {
          title: "Bed Capacity Horizons",
          href: "/admin/ai/bed-forecast",
          icon: <BedDouble className="w-4 h-4 text-cyan-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"],
        },
        {
          title: "Pharmacy Depletion AI",
          href: "/admin/ai/pharmacy",
          icon: <Pill className="w-4 h-4 text-emerald-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "PHARMACIST", "DOCTOR"],
        },
        {
          title: "Operational Anomalies",
          href: "/admin/ai/anomalies",
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE"],
          badge: "Alerts",
        },
        {
          title: "Document Intelligence",
          href: "/ai/documents",
          icon: <FileText className="w-4 h-4 text-sky-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "LAB_TECHNICIAN"],
        },
        {
          title: "AI Shift Handover",
          href: "/ai/handover",
          icon: <ShieldCheck className="w-4 h-4 text-teal-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "NURSE", "DOCTOR"],
        },
        {
          title: "Innovation & AI Matrix",
          href: "/admin/innovation",
          icon: <Cpu className="w-4 h-4 text-indigo-400" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"],
          badge: "TECH",
        },
      ],
    },
    {
      title: "Staff & Clinical Rosters",
      items: [
        {
          title: "Attending Doctors",
          href: "/doctors",
          icon: <Stethoscope className="w-4 h-4" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "RECEPTIONIST", "DOCTOR"],
        },
        {
          title: "Nursing Rosters",
          href: "/nurses",
          icon: <HeartPulse className="w-4 h-4" />,
          roles: ["SUPER_ADMIN", "HOSPITAL_ADMIN", "NURSE", "DOCTOR"],
        },
      ],
    },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen bg-slate-950/95 border-r border-slate-800/80 backdrop-blur-xl transition-all duration-300 flex flex-col justify-between ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80 bg-slate-900/30">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 shrink-0">
              <span className="font-mono font-black text-white text-base">CX</span>
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-extrabold text-sm tracking-wider text-white">CAREX</span>
                <span className="text-[10px] text-sky-400 font-medium">Healthcare OS</span>
              </div>
            )}
          </div>

          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
          {navigationSections.map((section, idx) => {
            const filteredItems = section.items.filter((item) => {
              if (!item.roles) return true;
              return item.roles.includes(userRole);
            });

            if (filteredItems.length === 0) return null;

            return (
              <div key={idx} className="space-y-1">
                {!collapsed && (
                  <h4 className="px-3 text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">
                    {section.title}
                  </h4>
                )}
                {filteredItems.map((item, itemIdx) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <NavLink
                      key={itemIdx}
                      to={item.href}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all group relative ${
                        isActive
                          ? "bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                      }`}
                    >
                      <span className="shrink-0">{item.icon}</span>
                      {!collapsed && (
                        <span className="flex-1 truncate">{item.title}</span>
                      )}
                      {!collapsed && item.badge && (
                        <span className="text-[9px] font-bold px-1.5 py-0.2 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* User Footer Profile */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-900/40">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 overflow-hidden shrink-0">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt={user.full_name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xs font-bold text-sky-400">
                {user?.full_name?.charAt(0) || "U"}
              </div>
            )}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-white truncate">{user?.full_name}</div>
              <div className="text-[10px] text-slate-400 truncate">{user?.role_display_name}</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
