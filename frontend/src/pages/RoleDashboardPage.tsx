import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi, tokensApi } from "../services/api";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { useToast } from "../hooks/useToast";
import { useAuth } from "../hooks/useAuth";
import {
  Users,
  Activity,
  Calendar,
  CalendarCheck,
  Ticket,
  HeartPulse,
  Pill,
  FlaskConical,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Volume2,
} from "lucide-react";

export const RoleDashboardPage: React.FC = () => {
  const { roleName } = useParams<{ roleName: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { success } = useToast();

  const currentRole = roleName || user?.role || "DOCTOR";

  // Queries
  const { data: dashboard, isLoading, isError, refetch } = useQuery({
    queryKey: ["roleDashboard", currentRole],
    queryFn: () => dashboardApi.getRoleStats(currentRole),
    refetchInterval: 10000,
  });

  // Patient Live Token status if role is PATIENT
  const { data: patientTokenStatus } = useQuery({
    queryKey: ["patientLiveToken", user?.id],
    queryFn: () => tokensApi.getPatientStatus(1), // Demo Johnathan Doe ID 1
    enabled: currentRole.toUpperCase() === "PATIENT",
    refetchInterval: 5000,
  });

  // Dynamic icon mapper
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case "Users":
        return <Users className="w-5 h-5" />;
      case "Calendar":
        return <Calendar className="w-5 h-5" />;
      case "CalendarCheck":
        return <CalendarCheck className="w-5 h-5" />;
      case "Ticket":
        return <Ticket className="w-5 h-5" />;
      case "HeartPulse":
        return <HeartPulse className="w-5 h-5" />;
      case "Pill":
        return <Pill className="w-5 h-5" />;
      case "FlaskConical":
        return <FlaskConical className="w-5 h-5" />;
      case "AlertTriangle":
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  const handleActionClick = (actionCode: string) => {
    switch (actionCode) {
      case "REGISTER_PATIENT":
        navigate("/patients");
        break;
      case "GENERATE_TOKEN":
      case "LIVE_QUEUE":
        navigate("/opd-queue");
        break;
      case "BOOK_APPOINTMENT":
      case "BOOK_VISIT":
        navigate("/appointments");
        break;
      case "VIEW_PATIENT_RECORDS":
      case "VIEW_REPORTS":
      case "VIEW_LAB_REPORTS":
      case "ORDER_LAB":
      case "VIEW_LAB_ORDERS":
      case "VIEW_LAB_CATALOGUE":
        navigate("/lab");
        break;
      case "WRITE_PRESCRIPTION":
      case "VIEW_PRESCRIPTIONS":
        navigate("/prescriptions");
        break;
      case "DISPENSE_MEDS":
      case "VIEW_INVENTORY":
      case "EXPIRY_TRACKER":
      case "LOW_STOCK_ALERTS":
      case "RESTOCK_BATCH":
        navigate("/pharmacy");
        break;
      case "VIEW_BILLING":
      case "PAY_INVOICE":
      case "GENERATE_INVOICE":
      case "COLLECT_PAYMENT":
        navigate("/billing");
        break;
      case "VIEW_EMERGENCY":
      case "EMERGENCY_INTAKE":
        navigate("/emergency");
        break;
      case "VIEW_IPD_ADMISSIONS":
        navigate("/ipd");
        break;
      case "VIEW_BED_MATRIX":
        navigate("/beds");
        break;
      case "START_CONSULTATION":
        navigate("/appointments");
        break;
      default:
        success("Action Triggered", `Navigating to ${actionCode} module.`);
        break;
    }
  };

  if (isLoading) {
    return (
      <PageContainer title="Loading Console...">
        <div className="py-24">
          <LoadingSpinner size="lg" label="Connecting to clinical telemetry..." />
        </div>
      </PageContainer>
    );
  }

  if (isError || !dashboard) {
    return (
      <PageContainer title="Operational Console">
        <ErrorState onRetry={() => refetch()} />
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={dashboard.title}
      subtitle={dashboard.description}
      badge={<Badge variant="info" dot>{dashboard.role} Role Active</Badge>}
    >
      <div className="space-y-6">
        {/* Live Patient Token Tracking Banner for Patient Role */}
        {currentRole.toUpperCase() === "PATIENT" && patientTokenStatus?.has_active_token && (
          <div className="p-5 rounded-2xl bg-gradient-to-r from-sky-950/60 via-indigo-950/40 to-slate-900 border-2 border-sky-500/50 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
                <Ticket className="w-7 h-7 animate-pulse" />
              </div>
              <div>
                <span className="text-[11px] font-bold uppercase tracking-widest text-sky-400">
                  YOUR LIVE OPD TOKEN STATUS TODAY
                </span>
                <div className="text-2xl font-extrabold text-white font-mono flex items-center gap-2">
                  <span>{patientTokenStatus.token?.token_code}</span>
                  <Badge variant="warning">{patientTokenStatus.token?.status}</Badge>
                </div>
                <p className="text-xs text-slate-300">
                  Department: <strong>{patientTokenStatus.token?.department_name}</strong>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6 text-center">
              <div>
                <span className="text-[10px] text-slate-400 block uppercase">Currently Serving</span>
                <span className="text-lg font-bold font-mono text-emerald-400">
                  {patientTokenStatus.current_serving_token_code || "Starting Soon"}
                </span>
              </div>
              <div className="border-l border-slate-700 pl-6">
                <span className="text-[10px] text-slate-400 block uppercase">Patients Ahead</span>
                <span className="text-lg font-bold text-amber-400">
                  {patientTokenStatus.patients_ahead}
                </span>
              </div>
              <div className="border-l border-slate-700 pl-6">
                <span className="text-[10px] text-slate-400 block uppercase">Est. Wait</span>
                <span className="text-lg font-bold text-sky-400">
                  ~{patientTokenStatus.estimated_wait_minutes} mins
                </span>
              </div>
            </div>

            <Button
              variant="glow"
              size="sm"
              onClick={() => navigate("/opd-queue")}
              leftIcon={<Volume2 className="w-4 h-4" />}
            >
              View Full Display Board
            </Button>
          </div>
        )}

        {/* 4 Role KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {dashboard.stats.map((kpi) => (
            <Card key={kpi.id} hoverable className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    {kpi.title}
                  </p>
                  <h3 className="text-2xl font-extrabold text-white mt-1">{kpi.value}</h3>
                </div>
                <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-sky-400">
                  {getIcon(kpi.icon_name || "")}
                </div>
              </div>
              <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span>{kpi.subtext}</span>
                {kpi.change_percentage !== 0 && (
                  <span
                    className={`flex items-center gap-0.5 font-bold ${
                      kpi.is_positive ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {kpi.is_positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    {Math.abs(kpi.change_percentage)}%
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>

        {/* Quick Actions Strip */}
        <div className="space-y-2.5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Quick Operational Directives
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {dashboard.quick_actions.map((qa, index) => (
              <button
                key={index}
                onClick={() => handleActionClick(qa.action)}
                className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-sky-500/50 hover:bg-slate-800/50 transition-all text-left group flex items-center justify-between"
              >
                <div className="space-y-1">
                  <p className="text-xs font-bold text-white group-hover:text-sky-400 transition-colors">
                    {qa.title}
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono">{qa.action}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400 group-hover:translate-x-0.5 transition-all" />
              </button>
            ))}
          </div>
        </div>

        {/* Live Operational Queue Table */}
        <Card hoverable={false}>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-sm font-bold text-white">
                Live Worklist & Operational Records
              </CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">
                Current clinical encounters, appointments, and pending orders for this role.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (currentRole === "DOCTOR" || currentRole === "PATIENT") {
                  navigate("/appointments");
                } else if (currentRole === "RECEPTIONIST") {
                  navigate("/patients");
                } else {
                  navigate("/opd-queue");
                }
              }}
            >
              View All in Module
            </Button>
          </CardHeader>

          <CardContent className="pt-0">
            {dashboard.recent_records && dashboard.recent_records.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No active records in the current queue.
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {dashboard.recent_records.map((rec: any, idx: number) => (
                  <div key={idx} className="py-3 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-xs text-sky-400">
                        #{idx + 1}
                      </div>
                      <div>
                        <div className="font-bold text-white text-xs">{rec.title}</div>
                        <div className="text-[11px] text-slate-400">{rec.meta || rec.id}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 text-right">
                      <div>
                        <div className="text-xs text-slate-300 font-medium">{rec.time}</div>
                        <Badge variant="info" className="mt-0.5">{rec.status}</Badge>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          if (rec.id?.startsWith("APT-")) {
                            navigate("/appointments");
                          } else if (rec.id?.startsWith("CRX-")) {
                            navigate("/patients");
                          } else {
                            navigate("/opd-queue");
                          }
                        }}
                      >
                        Open
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  );
};
