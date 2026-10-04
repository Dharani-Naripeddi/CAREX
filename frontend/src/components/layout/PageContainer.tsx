import React from "react";
import { clsx } from "clsx";

export interface PageContainerProps {
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  title,
  subtitle,
  badge,
  actions,
  children,
  className,
}) => {
  return (
    <div className={clsx("p-6 max-w-[1600px] mx-auto w-full space-y-6 animate-in fade-in duration-300", className)}>
      {(title || actions) && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/60">
          <div>
            <div className="flex items-center gap-3">
              {title && <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">{title}</h1>}
              {badge}
            </div>
            {subtitle && <p className="text-xs sm:text-sm text-slate-400 mt-1">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2.5 shrink-0">{actions}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
