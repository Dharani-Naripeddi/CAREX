import React, { HTMLAttributes, TableHTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export const Table: React.FC<TableHTMLAttributes<HTMLTableElement>> = ({
  className,
  ...props
}) => (
  <div className="relative w-full overflow-auto rounded-xl border border-slate-800 bg-slate-900/50">
    <table className={twMerge(clsx("w-full caption-bottom text-sm text-left", className))} {...props} />
  </div>
);

export const TableHeader: React.FC<HTMLAttributes<HTMLTableSectionElement>> = ({
  className,
  ...props
}) => (
  <thead
    className={twMerge(
      clsx("bg-slate-900/90 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800", className)
    )}
    {...props}
  />
);

export const TableBody: React.FC<HTMLAttributes<HTMLTableSectionElement>> = ({
  className,
  ...props
}) => (
  <tbody className={twMerge(clsx("divide-y divide-slate-800/60", className))} {...props} />
);

export const TableRow: React.FC<HTMLAttributes<HTMLTableRowElement>> = ({
  className,
  ...props
}) => (
  <tr
    className={twMerge(
      clsx(
        "transition-colors hover:bg-slate-800/40 data-[state=selected]:bg-slate-800",
        className
      )
    )}
    {...props}
  />
);

export const TableHead: React.FC<ThHTMLAttributes<HTMLTableCellElement>> = ({
  className,
  ...props
}) => (
  <th
    className={twMerge(
      clsx("h-11 px-4 text-left align-middle font-medium text-slate-400 select-none", className)
    )}
    {...props}
  />
);

export const TableCell: React.FC<TdHTMLAttributes<HTMLTableCellElement>> = ({
  className,
  ...props
}) => (
  <td
    className={twMerge(clsx("p-4 align-middle text-slate-200", className))}
    {...props}
  />
);
