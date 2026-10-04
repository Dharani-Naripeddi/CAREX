import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { nursesApi, departmentsApi } from "../services/api";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { useToast } from "../hooks/useToast";
import {
  MapPin,
  Building,
  Filter,
} from "lucide-react";

export const NursesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const [selectedDept, setSelectedDept] = useState<string>("");

  const { data: nurses, isLoading, isError, refetch } = useQuery({
    queryKey: ["nurses", selectedDept],
    queryFn: () =>
      nursesApi.list({
        department_id: selectedDept ? Number(selectedDept) : undefined,
      }),
  });

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.list,
  });

  const toggleDutyMutation = useMutation({
    mutationFn: ({ userId, isOnDuty }: { userId: number; isOnDuty: boolean }) =>
      nursesApi.update(userId, { is_on_duty: isOnDuty }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nurses"] });
      success("Duty Status Updated", "Nursing staff duty schedule updated.");
    },
    onError: (err: any) => {
      toastError("Update Failed", err.response?.data?.detail || "Could not update nurse duty.");
    },
  });

  const getShiftBadge = (shift: string) => {
    switch (shift) {
      case "MORNING":
        return <Badge variant="info">Morning (07:00 - 15:00)</Badge>;
      case "EVENING":
        return <Badge variant="warning">Evening (15:00 - 23:00)</Badge>;
      case "NIGHT":
        return <Badge variant="critical">Night (23:00 - 07:00)</Badge>;
      default:
        return <Badge variant="neutral">Rotating Shift</Badge>;
    }
  };

  return (
    <PageContainer
      title="Nursing Station & Inpatient Ward Rosters"
      subtitle="Registered nurses, clinical ward assignments, active shift schedules, and duty status."
      badge={<Badge variant="info" dot>{nurses?.length || 0} Nursing Staff</Badge>}
    >
      <div className="space-y-4">
        {/* Department Filter */}
        <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-bold text-slate-300">Department:</span>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Nursing Units</option>
              {departments?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Nurses Grid */}
        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Loading nursing roster..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : nurses && nurses.length === 0 ? (
          <EmptyState
            title="No nursing staff found"
            description="No nurses match the selected department filter."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {nurses?.map((n) => (
              <Card key={n.id} hoverable className="flex flex-col justify-between">
                <div>
                  <CardHeader className="flex flex-row items-start justify-between pb-3">
                    <div className="flex items-center gap-3">
                      <img
                        src={
                          n.avatar_url ||
                          "https://images.unsplash.com/photo-1594824813501-489e5a8f5f84?w=150&auto=format&fit=crop&q=80"
                        }
                        alt={n.full_name}
                        className="w-12 h-12 rounded-2xl object-cover border-2 border-emerald-500/30"
                      />
                      <div>
                        <CardTitle className="text-sm font-bold text-white leading-tight">
                          {n.full_name}
                        </CardTitle>
                        <p className="text-[11px] text-emerald-400 font-semibold">{n.qualification}</p>
                      </div>
                    </div>
                    {n.is_on_duty ? (
                      <Badge variant="success" dot>On Duty</Badge>
                    ) : (
                      <Badge variant="neutral">Off Duty</Badge>
                    )}
                  </CardHeader>

                  <CardContent className="space-y-2.5 pt-0 text-xs text-slate-300">
                    <div className="flex items-center gap-2 text-slate-400">
                      <Building className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span>{n.department_name || "Emergency & Trauma"}</span>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400">
                      <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                      <span>{n.ward_assigned || "General Inpatient Ward"}</span>
                    </div>

                    <div className="pt-2 border-t border-slate-800">
                      <span className="text-slate-500 block mb-1">Shift Schedule:</span>
                      {getShiftBadge(n.shift)}
                    </div>
                  </CardContent>
                </div>

                <div className="p-4 pt-0">
                  <Button
                    variant={n.is_on_duty ? "outline" : "glow"}
                    size="sm"
                    className="w-full"
                    onClick={() =>
                      toggleDutyMutation.mutate({
                        userId: n.user_id,
                        isOnDuty: !n.is_on_duty,
                      })
                    }
                  >
                    {n.is_on_duty ? "Mark Shift Completed (Off Duty)" : "Check In to Shift (On Duty)"}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
};
