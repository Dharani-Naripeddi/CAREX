import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopNavbar } from "./TopNavbar";

export const AppLayout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      {/* Top Navigation */}
      <TopNavbar />

      <div className="flex flex-1 pt-16">
        {/* Collapsible Left Sidebar */}
        <Sidebar
          collapsed={isSidebarCollapsed}
          onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        />

        {/* Dynamic Main Workspace Content */}
        <main
          className={`flex-1 transition-all duration-300 ${
            isSidebarCollapsed ? "pl-20" : "pl-64"
          } p-6 max-w-full overflow-x-hidden`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};
