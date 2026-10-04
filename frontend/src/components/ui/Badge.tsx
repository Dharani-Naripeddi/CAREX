import React, { HTMLAttributes } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "success"
    | "warning"
    | "critical"
    | "info"
    | "neutral"
    | "purple"
    | "outline";
  size?: "sm" | "md";
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  className,
  variant = "neutral",
  size = "sm",
  dot = false,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center font-medium rounded-full transition-colors select-none";

  const variants = {
    success:
      "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30",
    warning:
      "bg-amber-500/10 text-amber-300 border border-amber-500/30",
    critical:
      "bg-rose-500/10 text-rose-400 border border-rose-500/30",
    info:
      "bg-sky-500/10 text-sky-400 border border-sky-500/30",
    purple:
      "bg-purple-500/10 text-purple-400 border border-purple-500/30",
    neutral:
      "bg-slate-800 text-slate-300 border border-slate-700",
    outline:
      "bg-transparent text-slate-300 border border-slate-700",
  };

  const dotColors = {
    success: "bg-emerald-400",
    warning: "bg-amber-400",
    critical: "bg-rose-400 animate-pulse",
    info: "bg-sky-400",
    purple: "bg-purple-400",
    neutral: "bg-slate-400",
    outline: "bg-slate-400",
  };

  const sizes = {
    sm: "text-[11px] px-2 py-0.5 gap-1.5",
    md: "text-xs px-2.5 py-1 gap-2",
  };

  return (
    <span
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      {...props}
    >
      {dot && <span className={clsx("w-1.5 h-1.5 rounded-full shrink-0", dotColors[variant])} />}
      {children}
    </span>
  );
};
