import React, { useState, useEffect } from "react";
import { clsx } from "clsx";
import {
  Bell,
  Search,
  ChevronDown,
  User,
  LogOut,
  ShieldCheck,
  Building,
  Clock,
  Sparkles,
  CheckCircle,
  Zap,
  Flame,
  Activity,
  BedDouble,
  RotateCcw,
} from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import { Badge } from "../ui/Badge";
import { RoleEnum } from "../../types/auth";
import { NotificationDropdown } from "./NotificationDropdown";
import { demoApi } from "../../services/api";
import { useToast } from "../../hooks/useToast";
import { useQueryClient } from "@tanstack/react-query";

export const TopNavbar: React.FC = () => {
  const { user, logout, login } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError, info } = useToast();

  const [time, setTime] = useState<string>("");
  const [showRoleDropdown, setShowRoleDropdown] = useState(false);
  const [showSimDropdown, setShowSimDropdown] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [simLoading, setSimLoading] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const demoAccounts: { role: RoleEnum; label: string; email: string; desc: string }[] = [
    { role: "SUPER_ADMIN", label: "Super Admin", email: "superadmin@carex.health", desc: "Global Control & System Governance" },
    { role: "HOSPITAL_ADMIN", label: "Hospital Admin", email: "admin@carex.health", desc: "Facility Ops & Command Center" },
    { role: "DOCTOR", label: "Doctor / Physician", email: "dr.sharma@carex.health", desc: "Cardiology Inpatient/OPD Queue" },
    { role: "NURSE", label: "Registered Nurse", email: "nurse.sarah@carex.health", desc: "Ward 4B Vitals & MAR" },
    { role: "RECEPTIONIST", label: "Front Desk Lead", email: "reception@carex.health", desc: "OPD Tokens & Registration" },
    { role: "PHARMACIST", label: "Clinical Pharmacist", email: "pharmacy@carex.health", desc: "Dispensing & Stock Alert" },
    { role: "LAB_TECHNICIAN", label: "Lab Technician", email: "lab@carex.health", desc: "Specimen Testing & STAT flags" },
    { role: "PATIENT", label: "Patient", email: "patient.john@carex.health", desc: "Health Portal & Prescriptions" },
  ];

  const handleRoleSwitch = async (email: string, role: RoleEnum) => {
    setShowRoleDropdown(false);
    await login(email, "Carex#2026");
    if (role === "SUPER_ADMIN" || role === "HOSPITAL_ADMIN") {
      navigate("/dashboard");
    } else {
      navigate(`/workspace/${role.toLowerCase()}`);
    }
  };

  const handleLaunchScenario = async (scenarioCode: string, name: string) => {
    setShowSimDropdown(false);
    setSimLoading(true);
    try {
      if (scenarioCode === "RESET") {
        await demoApi.resetDemo();
        success("Hospital Reset", "Restored hospital operations to stable baseline telemetry.");
      } else {
        await demoApi.launchScenario(scenarioCode);
        success("Dynamic Scenario Injected", `Activated dynamic scenario: ${name}`);
      }
      queryClient.invalidateQueries();
    } catch (err: any) {
      toastError("Simulation Error", err.response?.data?.detail || "Could not launch simulation scenario.");
    } finally {
      setSimLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Hospital Name & Live Status */}
      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Building className="w-4 h-4 text-sky-400" />
          <span>CAREX Metropolitan Medical Center</span>
        </div>

        <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-flex shrink-0" />
          <span className="hidden md:inline">Command Center Live</span>
        </div>
      </div>

      {/* Right: Clock, Live Simulator, Quick Role Switcher, Notifications, Profile */}
      <div className="flex items-center gap-3">
        {/* Live Clock */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span>{time}</span>
          <span className="text-[10px] text-slate-500 font-sans">LOCAL</span>
        </div>

        {/* Dynamic Scenario Simulator Quick-Trigger */}
        <div className="relative">
          <button
            type="button"
            onClick={() => {
              setShowSimDropdown(!showSimDropdown);
              setShowRoleDropdown(false);
              setShowNotifications(false);
            }}
            disabled={simLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/40 text-xs font-semibold text-amber-300 hover:border-amber-400 transition-colors shadow-sm cursor-pointer"
          >
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Operations Simulator</span>
            <ChevronDown className="w-3 h-3 text-amber-400/70" />
          </button>

          {showSimDropdown && (
            <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-2 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-amber-400 flex items-center justify-between">
                <span>Operational Stress Testing</span>
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="py-1 space-y-1">
                <button
                  onClick={() => handleLaunchScenario("OPD_SURGE", "OPD Outpatient Surge")}
                  className="w-full text-left px-3 py-2 rounded-xl text-xs hover:bg-slate-800 text-slate-300 transition-colors flex items-center gap-2.5"
                >
                  <Activity className="w-4 h-4 text-sky-400 shrink-0" />
                  <div>
                    <div className="font-semibold text-white">OPD Patient Surge</div>
                    <div className="text-[10px] text-slate-400">Queue wait times spike to 65+ min</div>
                  </div>
                </button>

                <button
                  onClick={() => handleLaunchScenario("ACUTE_TRAUMA", "Acute Trauma Inflow")}
                  className="w-full text-left px-3 py-2 rounded-xl text-xs hover:bg-slate-800 text-slate-300 transition-colors flex items-center gap-2.5"
                >
                  <Flame className="w-4 h-4 text-rose-400 shrink-0" />
                  <div>
                    <div className="font-semibold text-white">Acute Trauma Inflow</div>
                    <div className="text-[10px] text-slate-400">Level 1 ER intake with critical vitals</div>
                  </div>
                </button>

                <button
                  onClick={() => handleLaunchScenario("ICU_SATURATION", "ICU Bed Saturation")}
                  className="w-full text-left px-3 py-2 rounded-xl text-xs hover:bg-slate-800 text-slate-300 transition-colors flex items-center gap-2.5"
                >
                  <BedDouble className="w-4 h-4 text-purple-400 shrink-0" />
                  <div>
                    <div className="font-semibold text-white">ICU Saturation Crisis</div>
                    <div className="text-[10px] text-slate-400">ICU beds exceed 95% threshold</div>
                  </div>
                </button>

                <div className="pt-1 mt-1 border-t border-slate-800">
                  <button
                    onClick={() => handleLaunchScenario("RESET", "Stable Baseline")}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs hover:bg-slate-800 text-emerald-400 transition-colors flex items-center gap-2.5"
                  >
                    <RotateCcw className="w-4 h-4 shrink-0" />
                    <div>
                      <div className="font-semibold">Reset to Stable Baseline</div>
                      <div className="text-[10px] text-slate-400">Restore normal hospital operations</div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Role Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setShowRoleDropdown(!showRoleDropdown);
              setShowSimDropdown(false);
              setShowNotifications(false);
            }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gradient-to-r from-sky-950/60 to-slate-900 border border-sky-500/30 text-xs font-medium text-sky-300 hover:border-sky-400 transition-colors shadow-sm"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
            <span className="hidden sm:inline">Role:</span>
            <span className="font-bold text-white truncate max-w-[110px]">
              {user?.role_display_name || user?.role}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {showRoleDropdown && (
            <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-2 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                <span>Switch Demo Role</span>
                <Sparkles className="w-3 h-3 text-sky-400" />
              </div>
              <div className="max-h-80 overflow-y-auto py-1 space-y-1">
                {demoAccounts.map((acc) => (
                  <button
                    key={acc.role}
                    onClick={() => handleRoleSwitch(acc.email, acc.role)}
                    className={clsx(
                      "w-full text-left px-3 py-2 rounded-xl text-xs transition-colors flex items-start gap-2.5",
                      user?.role === acc.role
                        ? "bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30"
                        : "hover:bg-slate-800 text-slate-300"
                    )}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white truncate">{acc.label}</span>
                        {user?.role === acc.role && (
                          <CheckCircle className="w-3.5 h-3.5 text-sky-400" />
                        )}
                      </div>
                      <p className="text-[10px] text-slate-400 truncate mt-0.5">{acc.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Notifications Bell */}
        <NotificationDropdown
          isOpen={showNotifications}
          onToggle={() => {
            setShowNotifications(!showNotifications);
            setShowRoleDropdown(false);
            setShowSimDropdown(false);
          }}
          onClose={() => setShowNotifications(false)}
        />

        {/* Sign Out Button */}
        <button
          onClick={handleLogout}
          className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
