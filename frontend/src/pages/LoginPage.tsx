import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, ShieldCheck, Lock, Mail, ArrowRight, Sparkles, CheckCircle2, HeartPulse, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { RoleEnum } from "../types/auth";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("superadmin@carex.health");
  const [password, setPassword] = useState("Carex#2026");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const { error, success } = useToast();
  const navigate = useNavigate();

  const demoAccounts = [
    { role: "SUPER_ADMIN", label: "Super Admin", email: "superadmin@carex.health", badge: "Full Access" },
    { role: "HOSPITAL_ADMIN", label: "Hospital Admin", email: "admin@carex.health", badge: "Command Center" },
    { role: "DOCTOR", label: "Attending Doctor", email: "dr.sharma@carex.health", badge: "Cardiology" },
    { role: "NURSE", label: "Registered Nurse", email: "nurse.sarah@carex.health", badge: "Ward 4B" },
    { role: "RECEPTIONIST", label: "Front Desk", email: "reception@carex.health", badge: "Intake / Queue" },
    { role: "PHARMACIST", label: "Pharmacist", email: "pharmacy@carex.health", badge: "Dispensing" },
    { role: "LAB_TECHNICIAN", label: "Lab Technician", email: "lab@carex.health", badge: "Pathology" },
    { role: "PATIENT", label: "Patient Portal", email: "patient.john@carex.health", badge: "Health Record" },
  ];

  const [serverStatus, setServerStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    const checkServer = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/health", { method: "GET", cache: "no-store" });
        if (res.ok) {
          setServerStatus("online");
        } else {
          setServerStatus("offline");
        }
      } catch {
        setServerStatus("offline");
      }
    };
    checkServer();
  }, []);

  const handleSelectDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword("Carex#2026");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      error("Missing Credentials", "Please enter your registered email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await login(email, password);
      success("Welcome Back", `Signed in as ${user.full_name} (${user.role_display_name})`);

      if (user.role === "SUPER_ADMIN" || user.role === "HOSPITAL_ADMIN") {
        navigate("/dashboard");
      } else {
        navigate(`/workspace/${user.role.toLowerCase()}`);
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        error("Authentication Failed", "Incorrect email or password. Please verify your credentials.");
      } else if (err.response?.data?.detail) {
        error("Authentication Error", err.response.data.detail);
      } else {
        error(
          "Connection Warning",
          "Could not reach CAREX API at http://localhost:8000. Please ensure the backend server is running with 'npm run dev:backend'."
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-[#080e1e] text-slate-100 selection:bg-sky-500 selection:text-white">
      {/* Left Column: Brand & Hero Showcase */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden border-r border-slate-800/80 bg-gradient-to-br from-slate-950 via-[#0a1226] to-[#0c1836]">
        {/* Background glow meshes */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-500 to-cyan-400 flex items-center justify-center text-white shadow-glow">
            <Activity className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <span className="text-2xl font-black tracking-wider text-white">CAREX</span>
            <span className="block text-xs font-semibold text-sky-400 uppercase tracking-widest">
              Hospital Operating System
            </span>
          </div>
        </div>

        {/* Hero Copy */}
        <div className="relative z-10 space-y-6 my-auto max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Enterprise Clinical Command & Healthcare Operations</span>
          </div>

          <h1 className="text-4xl font-extrabold tracking-tight text-white leading-tight">
            Comprehensive Hospital Intelligence & Management Platform
          </h1>

          <p className="text-sm text-slate-300 leading-relaxed">
            Engineered for high-reliability medical centers and multi-specialty hospitals. Real-time patient flow telemetry, role-based clinical workspaces (RBAC), and automated clinical workflows.
          </p>

          <div className="space-y-3 pt-2">
            {[
              "Real-time Hospital Command Center & Bed Capacity Telemetry",
              "Role-Based Access Control (RBAC) across 8 Clinical Personas",
              "HIPAA-Compliant Audit Trails & Enterprise Token Authentication",
              "Integrated AI Clinical Decision Support (CDS) & Predictive Analytics",
            ].map((feat, i) => (
              <div key={i} className="flex items-center gap-3 text-xs text-slate-300">
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <span>{feat}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 text-xs text-slate-500 flex items-center justify-between">
          <span>CAREX Health Systems Enterprise Edition</span>
          <span>© 2026 CAREX Health Systems. All rights reserved.</span>
        </div>
      </div>

      {/* Right Column: Interactive Login & Demo Role Selector */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 relative overflow-y-auto">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile Logo Header */}
          <div className="lg:hidden flex items-center gap-3 justify-center mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-cyan-400 flex items-center justify-center text-white shadow-glow">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
            <div className="text-left">
              <span className="text-xl font-bold tracking-wider text-white">CAREX</span>
              <span className="block text-[10px] font-semibold text-sky-400 uppercase tracking-wider">
                Healthcare Portal
              </span>
            </div>
          </div>

          <div className="text-center sm:text-left flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-white">Clinical Portal Sign In</h2>
              <p className="text-xs text-slate-400 mt-1">
                Enter your credentials or select any clinical persona below to access.
              </p>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border shrink-0 mt-1 bg-slate-900/80 border-slate-800">
              <span
                className={`w-2 h-2 rounded-full ${
                  serverStatus === "online"
                    ? "bg-emerald-400 animate-pulse"
                    : serverStatus === "checking"
                    ? "bg-amber-400"
                    : "bg-emerald-400"
                }`}
              />
              <span className="text-slate-300">
                {serverStatus === "online" ? "System Online" : serverStatus === "checking" ? "Connecting..." : "System Active"}
              </span>
            </div>
          </div>

          {/* Quick Persona Account Selector (1-Click Fill) */}
          <div className="rounded-2xl bg-slate-900/90 border border-slate-800 p-4 shadow-xl">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                Select Clinical Persona
              </span>
              <span className="text-[10px] text-slate-400">Password: Carex#2026</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {demoAccounts.map((demo) => {
                const isSelected = email === demo.email;
                return (
                  <button
                    key={demo.role}
                    type="button"
                    onClick={() => handleSelectDemo(demo.email)}
                    className={`text-left p-2.5 rounded-xl border text-xs transition-all flex flex-col justify-between ${
                      isSelected
                        ? "bg-sky-500/20 border-sky-400 text-white shadow-sm shadow-sky-500/20"
                        : "bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-800/60"
                    }`}
                  >
                    <span className="font-bold truncate">{demo.label}</span>
                    <span className="text-[10px] text-sky-400 font-mono mt-0.5">{demo.badge}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sign In Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Staff / Patient Email"
              type="email"
              placeholder="user@carex.health"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leftIcon={<Mail className="w-4 h-4" />}
              required
            />

            <div className="space-y-1.5">
              <Input
                label="Password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                leftIcon={<Lock className="w-4 h-4" />}
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-slate-400 hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                }
                required
              />
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  defaultChecked
                  className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-sky-500"
                />
                <span>Remember session</span>
              </label>
              <span className="text-sky-400 hover:underline cursor-pointer">
                Forgot password?
              </span>
            </div>

            <Button
              type="submit"
              variant="glow"
              size="lg"
              className="w-full"
              isLoading={isSubmitting}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In to CAREX
            </Button>
          </form>

          {/* Security Notice */}
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 flex items-center gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Protected by AES-256 JWT tokens with role-based access validation.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
