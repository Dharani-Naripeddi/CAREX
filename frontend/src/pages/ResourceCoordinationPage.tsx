import React from "react";
import { useQuery } from "@tanstack/react-query";
import { resourcesApi } from "../services/api";
import { ResourceAvailability, ResourceItem } from "../types/emergency_ipd";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import {
  Activity,
  HeartPulse,
  Stethoscope,
  BedDouble,
  Wind,
  FlaskConical,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  AlertTriangle,
  Clock,
  CheckCircle2,
} from "lucide-react";

export const ResourceCoordinationPage: React.FC = () => {
  const { data: coordination, isLoading, isError, refetch } = useQuery({
    queryKey: ["resourceCoordination"],
    queryFn: resourcesApi.getCoordination,
    refetchInterval: 5000,
  });

  const getStatusBadge = (status: ResourceAvailability) => {
    switch (status) {
      case "AVAILABLE":
        return <Badge variant="success" dot>AVAILABLE</Badge>;
      case "BUSY":
        return <Badge variant="warning" dot>BUSY (High Load)</Badge>;
      case "UNAVAILABLE":
        return <Badge variant="critical" dot>UNAVAILABLE (Full)</Badge>;
    }
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case "DOCTORS":
        return <Stethoscope className="w-5 h-5 text-sky-400" />;
      case "NURSES":
        return <HeartPulse className="w-5 h-5 text-emerald-400" />;
      case "ICU_BEDS":
        return <BedDouble className="w-5 h-5 text-rose-400" />;
      case "GENERAL_BEDS":
        return <BedDouble className="w-5 h-5 text-indigo-400" />;
      case "OXYGEN_SUPPORT":
        return <Wind className="w-5 h-5 text-teal-400" />;
      case "LABORATORY":
        return <FlaskConical className="w-5 h-5 text-purple-400" />;
      default:
        return <Activity className="w-5 h-5 text-sky-400" />;
    }
  };

  return (
    <PageContainer
      title="Hospital Resource Coordination & Capacity Telemetry"
      subtitle="Live multi-resource availability, utilization pressure meters, and automated operational directives."
      badge={<Badge variant="info" dot>Live Telemetry (5s auto-sync)</Badge>}
      actions={
        <Button variant="ghost" size="sm" onClick={() => refetch()} leftIcon={<RotateCcw className="w-3.5 h-3.5" />}>
          Refresh
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Operational Recommendations Banner */}
        <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-sky-950/40 to-slate-900 border border-sky-500/30 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-sky-400 animate-pulse" />
              Automated Operational Directives & Recommendations
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              Updated: {coordination?.last_updated || "Just now"}
            </span>
          </div>

          <div className="space-y-2">
            {coordination?.operational_recommendations?.map((rec, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-200"
              >
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span>{rec}</span>
              </div>
            ))}
          </div>

          <p className="text-[11px] text-slate-500 italic pt-1">
            "{coordination?.disclaimer || "AI decision support only. Final clinical decision must be made by qualified healthcare professionals."}"
          </p>
        </div>

        {/* Resources Grid */}
        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Updating hospital resource telemetry..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {coordination?.resources?.map((res, index) => (
              <Card key={index} hoverable className="p-5 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                        {getResourceIcon(res.resource_type)}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white">{res.name}</h4>
                        <p className="text-[11px] text-slate-400 font-mono">{res.resource_type}</p>
                      </div>
                    </div>
                    {getStatusBadge(res.status)}
                  </div>

                  <div className="space-y-1.5 pt-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Capacity Load</span>
                      <span className="font-bold text-white font-mono">{res.utilization_percentage}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          res.utilization_percentage >= 85
                            ? "bg-rose-500"
                            : res.utilization_percentage >= 60
                            ? "bg-amber-400"
                            : "bg-emerald-400"
                        }`}
                        style={{ width: `${Math.min(100, res.utilization_percentage)}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-300">
                  {res.details}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
};
