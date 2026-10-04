import React, { HTMLAttributes } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  glow?: "none" | "sky" | "emerald" | "rose" | "purple";
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  glow = "none",
  hoverable = false,
  ...props
}) => {
  const glowStyles = {
    none: "",
    sky: "border-sky-500/30 shadow-lg shadow-sky-950/40",
    emerald: "border-emerald-500/30 shadow-lg shadow-emerald-950/40",
    rose: "border-rose-500/30 shadow-lg shadow-rose-950/40",
    purple: "border-purple-500/30 shadow-lg shadow-purple-950/40",
  };

  return (
    <div
      className={twMerge(
        clsx(
          "rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-md transition-all duration-300 text-slate-100 overflow-hidden",
          glowStyles[glow],
          hoverable && "hover:border-slate-700 hover:bg-slate-900/90 hover:shadow-xl hover:-translate-y-0.5",
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => (
  <div className={twMerge(clsx("p-5 pb-3 flex flex-col space-y-1.5", className))} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className,
  ...props
}) => (
  <h3
    className={twMerge(
      clsx("text-base font-semibold tracking-tight text-white flex items-center gap-2", className)
    )}
    {...props}
  >
    {children}
  </h3>
);

export const CardDescription: React.FC<HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className,
  ...props
}) => (
  <p className={twMerge(clsx("text-xs text-slate-400 font-normal leading-relaxed", className))} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => (
  <div className={twMerge(clsx("p-5 pt-0", className))} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => (
  <div
    className={twMerge(
      clsx("p-5 pt-3 border-t border-slate-800/80 flex items-center justify-between", className)
    )}
    {...props}
  >
    {children}
  </div>
);
