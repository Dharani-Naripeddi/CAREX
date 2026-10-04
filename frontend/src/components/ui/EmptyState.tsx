import React from "react";
import { FolderOpen } from "lucide-react";
import { Button } from "./Button";
import { clsx } from "clsx";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title = "No records found",
  description = "There are currently no active items or clinical records matching your criteria.",
  actionLabel,
  onAction,
  className,
}) => {
  return (
    <div
      className={clsx(
        "flex flex-col items-center justify-center p-10 text-center rounded-2xl bg-slate-900/40 border border-dashed border-slate-800 my-4",
        className
      )}
    >
      <div className="w-12 h-12 rounded-2xl bg-slate-800/80 flex items-center justify-center text-slate-400 mb-3 border border-slate-700">
        {icon || <FolderOpen className="w-6 h-6 text-slate-400" />}
      </div>
      <h4 className="text-sm font-semibold text-white mb-1">{title}</h4>
      <p className="text-xs text-slate-400 mb-4 max-w-sm">{description}</p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
