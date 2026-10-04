import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { RoleEnum } from "../types/auth";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

interface ProtectedRouteProps {
  children: React.ReactElement;
  allowedRoles?: RoleEnum[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
}) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-[#080e1e]">
        <LoadingSpinner size="lg" label="Verifying clinical credentials..." />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If specific roles are required, verify user role or super admin bypass
  if (allowedRoles && allowedRoles.length > 0) {
    if (user.role !== "SUPER_ADMIN" && !allowedRoles.includes(user.role)) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return children;
};
