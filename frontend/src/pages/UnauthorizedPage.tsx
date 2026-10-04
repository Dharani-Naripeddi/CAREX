import React from "react";
import { ShieldAlert, ArrowLeft, Home } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button } from "../components/ui/Button";

export const UnauthorizedPage: React.FC = () => {
  const { user } = useAuth();

  const getDashboardPath = () => {
    if (!user) return "/login";
    if (user.role === "SUPER_ADMIN" || user.role === "HOSPITAL_ADMIN") return "/dashboard";
    return `/workspace/${user.role.toLowerCase()}`;
  };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-6 bg-[#080e1e] text-slate-100 text-center">
      <div className="w-16 h-16 rounded-3xl bg-rose-500/20 text-rose-400 flex items-center justify-center mb-6 ring-8 ring-rose-500/10">
        <ShieldAlert className="w-8 h-8" />
      </div>

      <h1 className="text-3xl font-extrabold text-white mb-2">403 • Restricted Clinical Zone</h1>
      <p className="text-sm text-slate-400 max-w-md mb-6 leading-relaxed">
        Your current role (<span className="text-sky-400 font-semibold">{user?.role_display_name || user?.role || "Guest"}</span>) does not possess the requisite RBAC security clearances to access this department or module.
      </p>

      <div className="flex items-center gap-3">
        <Link to={getDashboardPath()}>
          <Button variant="glow" size="md" leftIcon={<Home className="w-4 h-4" />}>
            Return to My Workspace
          </Button>
        </Link>
        <Link to="/login">
          <Button variant="outline" size="md" leftIcon={<ArrowLeft className="w-4 h-4" />}>
            Sign In with Different Role
          </Button>
        </Link>
      </div>
    </div>
  );
};
