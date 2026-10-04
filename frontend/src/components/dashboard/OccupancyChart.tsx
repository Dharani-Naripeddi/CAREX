import React from "react";
import { DepartmentOccupancy } from "../../types/dashboard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../ui/Card";
import { Building2 } from "lucide-react";
import { clsx } from "clsx";

interface OccupancyChartProps {
  departments: DepartmentOccupancy[];
}

export const OccupancyChart: React.FC<OccupancyChartProps> = ({ departments }) => {
  return (
    <Card className="flex flex-col h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>
            <Building2 className="w-4 h-4 text-emerald-400" />
            Department Bed Occupancy
          </CardTitle>
          <span className="text-[11px] font-medium text-slate-400">Live Census</span>
        </div>
        <CardDescription>
          Real-time bed utilization across specialized hospital wards and acute units.
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-4 pt-2">
        {departments.map((dept) => {
          const isCritical = dept.occupancy_rate >= 90;
          const isWarning = dept.occupancy_rate >= 80 && dept.occupancy_rate < 90;

          return (
            <div key={dept.department} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200">{dept.department}</span>
                <span className="font-mono text-slate-300">
                  <span className="font-bold text-white">{dept.occupied_beds}</span> / {dept.total_beds} beds{" "}
                  <span
                    className={clsx(
                      "font-bold ml-1.5",
                      isCritical ? "text-rose-400" : isWarning ? "text-amber-400" : "text-emerald-400"
                    )}
                  >
                    ({dept.occupancy_rate}%)
                  </span>
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={clsx(
                    "h-full rounded-full transition-all duration-500",
                    isCritical
                      ? "bg-gradient-to-r from-rose-500 to-red-600 shadow-sm shadow-rose-500/50"
                      : isWarning
                      ? "bg-gradient-to-r from-amber-400 to-yellow-500"
                      : "bg-gradient-to-r from-sky-400 to-emerald-400"
                  )}
                  style={{ width: `${Math.min(dept.occupancy_rate, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};
