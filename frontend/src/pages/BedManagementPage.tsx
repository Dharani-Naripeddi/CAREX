import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { bedsApi } from "../services/api";
import { Bed, BedStatus, Ward } from "../types/emergency_ipd";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { useToast } from "../hooks/useToast";
import {
  BedDouble,
  Activity,
  Wind,
  Wrench,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  RotateCcw,
  Building,
  User,
  ShieldAlert,
} from "lucide-react";

export const BedManagementPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [selectedWardId, setSelectedWardId] = useState<number | undefined>(undefined);
  const [selectedStatus, setSelectedStatus] = useState<string>("");

  // Queries
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ["bedDashboardStats"],
    queryFn: bedsApi.getDashboard,
    refetchInterval: 5000,
  });

  const { data: beds, isLoading: bedsLoading, isError, refetch: refetchBeds } = useQuery({
    queryKey: ["beds", selectedWardId, selectedStatus],
    queryFn: () =>
      bedsApi.listBeds({
        ward_id: selectedWardId,
        status: (selectedStatus as BedStatus) || undefined,
      }),
    refetchInterval: 5000,
  });

  // Mutation to update bed status (e.g. Cleaned -> Available)
  const updateBedStatusMutation = useMutation({
    mutationFn: ({ bedId, status }: { bedId: number; status: BedStatus }) =>
      bedsApi.updateStatus(bedId, status),
    onSuccess: (updatedBed) => {
      queryClient.invalidateQueries({ queryKey: ["beds"] });
      queryClient.invalidateQueries({ queryKey: ["bedDashboardStats"] });
      queryClient.invalidateQueries({ queryKey: ["wards"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      success(
        `Bed ${updatedBed.bed_number} Updated`,
        `Status successfully transitioned to ${updatedBed.status}.`
      );
    },
    onError: (err: any) => {
      toastError("Update Failed", err.response?.data?.detail || "Could not update bed status.");
    },
  });

  const getStatusColor = (status: BedStatus) => {
    switch (status) {
      case "AVAILABLE":
        return "border-emerald-500/40 bg-emerald-950/20 text-emerald-400";
      case "OCCUPIED":
        return "border-rose-500/40 bg-rose-950/20 text-rose-400";
      case "RESERVED":
        return "border-amber-500/40 bg-amber-950/20 text-amber-400";
      case "CLEANING":
        return "border-sky-500/40 bg-sky-950/20 text-sky-400";
      case "MAINTENANCE":
        return "border-purple-500/40 bg-purple-950/20 text-purple-400";
    }
  };

  const getStatusBadge = (status: BedStatus) => {
    switch (status) {
      case "AVAILABLE":
        return <Badge variant="success" dot>AVAILABLE</Badge>;
      case "OCCUPIED":
        return <Badge variant="critical" dot>OCCUPIED</Badge>;
      case "RESERVED":
        return <Badge variant="warning">RESERVED</Badge>;
      case "CLEANING":
        return <Badge variant="info">CLEANING</Badge>;
      case "MAINTENANCE":
        return <Badge variant="neutral">MAINTENANCE</Badge>;
    }
  };

  return (
    <PageContainer
      title="Hospital Bed Management & Ward Occupancy Telemetry"
      subtitle="Visual interactive ward floor maps, real-time bed capacity meters, and cleaning/maintenance status management."
      badge={<Badge variant="info" dot>{stats?.total_beds || 0} Total Beds</Badge>}
      actions={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            refetchStats();
            refetchBeds();
          }}
          leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
        >
          Refresh Grid
        </Button>
      }
    >
      <div className="space-y-6">
        {/* KPI Counter Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <Card className="p-3.5 border-slate-800 bg-slate-900/60">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Beds</span>
            <div className="text-xl font-black text-white mt-1">{stats?.total_beds || 0}</div>
            <span className="text-[10px] text-slate-500">Across 7 Wards</span>
          </Card>

          <Card className="p-3.5 border-rose-500/30 bg-rose-950/15">
            <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400">Occupied</span>
            <div className="text-xl font-black text-rose-300 mt-1">{stats?.occupied_beds || 0}</div>
            <span className="text-[10px] text-rose-400/70">{stats?.occupancy_rate || 0}% Occupancy</span>
          </Card>

          <Card className="p-3.5 border-emerald-500/30 bg-emerald-950/15">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Available</span>
            <div className="text-xl font-black text-emerald-300 mt-1">{stats?.available_beds || 0}</div>
            <span className="text-[10px] text-emerald-400/70">Ready for Admission</span>
          </Card>

          <Card className="p-3.5 border-amber-500/30 bg-amber-950/15">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">Reserved</span>
            <div className="text-xl font-black text-amber-300 mt-1">{stats?.reserved_beds || 0}</div>
            <span className="text-[10px] text-amber-400/70">Planned Surgeries</span>
          </Card>

          <Card className="p-3.5 border-sky-500/30 bg-sky-950/15">
            <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400">Cleaning</span>
            <div className="text-xl font-black text-sky-300 mt-1">{stats?.cleaning_beds || 0}</div>
            <span className="text-[10px] text-sky-400/70">Sanitization in Progress</span>
          </Card>

          <Card className="p-3.5 border-purple-500/30 bg-purple-950/15">
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">Maintenance</span>
            <div className="text-xl font-black text-purple-300 mt-1">{stats?.maintenance_beds || 0}</div>
            <span className="text-[10px] text-purple-400/70">Biomedical Engineering</span>
          </Card>
        </div>

        {/* Ward Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <button
            onClick={() => setSelectedWardId(undefined)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-xl whitespace-nowrap transition-all ${
              selectedWardId === undefined
                ? "bg-sky-500 text-white shadow-lg shadow-sky-500/25"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            All Wards ({stats?.total_beds || 0})
          </button>
          {stats?.wards?.map((w) => (
            <button
              key={w.id}
              onClick={() => setSelectedWardId(w.id)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-xl whitespace-nowrap transition-all flex items-center gap-1.5 ${
                selectedWardId === w.id
                  ? "bg-sky-500 text-white shadow-lg shadow-sky-500/25"
                  : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              <span>{w.name}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-md bg-slate-950/80 font-mono font-bold">
                {w.available_beds}/{w.total_beds}
              </span>
            </button>
          ))}
        </div>

        {/* Status Quick Filter Bar */}
        <div className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-semibold">Filter Status:</span>
            {["", "AVAILABLE", "OCCUPIED", "RESERVED", "CLEANING", "MAINTENANCE"].map((st) => (
              <button
                key={st}
                onClick={() => setSelectedStatus(st)}
                className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                  selectedStatus === st
                    ? "bg-slate-800 text-white font-bold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st === "" ? "All Statuses" : st}
              </button>
            ))}
          </div>

          <div className="text-[11px] text-slate-400">
            Showing <strong className="text-white">{beds?.length || 0}</strong> beds
          </div>
        </div>

        {/* Visual Bed Grid Matrix */}
        {bedsLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Rendering Ward Floor Matrix..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetchBeds()} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {beds?.map((bed) => (
              <div
                key={bed.id}
                className={`p-4 rounded-2xl border-2 transition-all hover:scale-[1.01] hover:shadow-xl flex flex-col justify-between ${getStatusColor(
                  bed.status
                )}`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-extrabold text-white tracking-wider">
                      {bed.bed_number}
                    </span>
                    {getStatusBadge(bed.status)}
                  </div>

                  <div className="text-[11px] text-slate-300 font-medium">
                    {bed.ward_name || "General Ward"}
                  </div>

                  {/* Capabilities */}
                  <div className="flex items-center gap-2 pt-1">
                    {bed.has_oxygen_support && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 border border-teal-500/30 flex items-center gap-1 font-mono">
                        <Wind className="w-3 h-3" /> O2
                      </span>
                    )}
                    {bed.has_ventilator && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1 font-mono">
                        <Activity className="w-3 h-3" /> Ventilator
                      </span>
                    )}
                  </div>

                  {/* Occupant if any */}
                  {bed.status === "OCCUPIED" && (
                    <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-0.5 mt-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-white">
                        <User className="w-3.5 h-3.5 text-rose-400" />
                        <span className="truncate">{bed.patient_name || "Patient Admitted"}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        MRN: {bed.patient_mrn || "N/A"}
                      </div>
                    </div>
                  )}
                </div>

                {/* Quick Status Action Buttons */}
                <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-end gap-1.5">
                  {bed.status === "CLEANING" && (
                    <Button
                      variant="glow"
                      size="sm"
                      onClick={() =>
                        updateBedStatusMutation.mutate({ bedId: bed.id, status: "AVAILABLE" })
                      }
                      leftIcon={<Sparkles className="w-3 h-3" />}
                    >
                      Mark Cleaned
                    </Button>
                  )}

                  {bed.status === "MAINTENANCE" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        updateBedStatusMutation.mutate({ bedId: bed.id, status: "AVAILABLE" })
                      }
                      leftIcon={<CheckCircle2 className="w-3 h-3" />}
                    >
                      Ready for Use
                    </Button>
                  )}

                  {bed.status === "AVAILABLE" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        updateBedStatusMutation.mutate({ bedId: bed.id, status: "MAINTENANCE" })
                      }
                      leftIcon={<Wrench className="w-3 h-3 text-slate-400" />}
                    >
                      Service
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
};
