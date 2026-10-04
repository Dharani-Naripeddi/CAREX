import React from "react";
import { Loader2 } from "lucide-react";
import { clsx } from "clsx";

export interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg" | "xl";
  label?: string;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "md",
  label,
  className,
}) => {
  const sizes = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8",
    xl: "w-12 h-12",
  };

  return (
    <div className={clsx("flex flex-col items-center justify-center p-6 gap-3", className)}>
      <Loader2 className={clsx("animate-spin text-sky-400", sizes[size])} />
      {label && <p className="text-xs font-medium text-slate-400 animate-pulse">{label}</p>}
    </div>
  );
};

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, ...props }) => (
  <div
    className={clsx("animate-pulse rounded-lg bg-slate-800/80", className)}
    {...props}
  />
);
