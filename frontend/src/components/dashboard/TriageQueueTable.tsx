import React from "react";
import { TriagePatient } from "../../types/dashboard";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../ui/Table";
import { Badge } from "../ui/Badge";
import { AlertTriangle, Clock, UserCheck } from "lucide-react";

interface TriageQueueTableProps {
  patients: TriagePatient[];
}

export const TriageQueueTable: React.FC<TriageQueueTableProps> = ({ patients }) => {
  const getPriorityBadge = (priority: TriagePatient["priority"]) => {
    switch (priority) {
      case "P1_CRITICAL":
        return <Badge variant="critical" dot>P1 • Critical</Badge>;
      case "P2_URGENT":
        return <Badge variant="warning" dot>P2 • Urgent</Badge>;
      case "P3_NON_URGENT":
        return <Badge variant="info" dot>P3 • Standard</Badge>;
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          Active Emergency Triage Queue
        </h4>
        <span className="text-xs text-slate-400">{patients.length} Active Patients</span>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Patient ID & Name</TableHead>
            <TableHead>Demographics</TableHead>
            <TableHead>Chief Complaint</TableHead>
            <TableHead>Triage Severity</TableHead>
            <TableHead>Wait Time</TableHead>
            <TableHead>Assigned Care Team</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {patients.map((p) => (
            <TableRow key={p.id}>
              <TableCell>
                <div className="font-bold text-white text-xs">{p.patient_name}</div>
                <div className="text-[10px] text-slate-400 font-mono">{p.id}</div>
              </TableCell>
              <TableCell className="text-xs text-slate-300">
                {p.age}y • {p.gender}
              </TableCell>
              <TableCell className="text-xs text-slate-200 font-medium max-w-xs truncate">
                {p.chief_complaint}
              </TableCell>
              <TableCell>{getPriorityBadge(p.priority)}</TableCell>
              <TableCell>
                <span className="inline-flex items-center gap-1 text-xs font-mono text-amber-300">
                  <Clock className="w-3 h-3" />
                  {p.wait_time_minutes}m
                </span>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-1.5 text-xs text-sky-400 font-medium">
                  <UserCheck className="w-3.5 h-3.5" />
                  <span>{p.assigned_doctor || "Triage Waiting Room"}</span>
                </div>
                <div className="text-[10px] text-slate-400">{p.department}</div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
