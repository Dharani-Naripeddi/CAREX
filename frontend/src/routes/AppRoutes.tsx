import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { AppLayout } from "../components/layout/AppLayout";
import { LoginPage } from "../pages/LoginPage";
import { CommandCenterPage } from "../pages/CommandCenterPage";
import { RoleDashboardPage } from "../pages/RoleDashboardPage";
import { PatientsPage } from "../pages/PatientsPage";
import { AppointmentsPage } from "../pages/AppointmentsPage";
import { DoctorsPage } from "../pages/DoctorsPage";
import { NursesPage } from "../pages/NursesPage";
import { OpdQueuePage } from "../pages/OpdQueuePage";
import { EmergencyPage } from "../pages/EmergencyPage";
import { ResourceCoordinationPage } from "../pages/ResourceCoordinationPage";
import { IpdPage } from "../pages/IpdPage";
import { BedManagementPage } from "../pages/BedManagementPage";
import { LaboratoryPage } from "../pages/LaboratoryPage";
import { PharmacyPage } from "../pages/PharmacyPage";
import { BillingPage } from "../pages/BillingPage";
import { PrescriptionsPage } from "../pages/PrescriptionsPage";
import { AiDashboardPage } from "../pages/AiDashboardPage";
import { OpdQueuePredictionPage } from "../pages/OpdQueuePredictionPage";
import { BedForecastPage } from "../pages/BedForecastPage";
import { PharmacyIntelligencePage } from "../pages/PharmacyIntelligencePage";
import { OperationalAnomaliesPage } from "../pages/OperationalAnomaliesPage";
import { DocumentAiPage } from "../pages/DocumentAiPage";
import { AiShiftHandoverPage } from "../pages/AiShiftHandoverPage";
import { HospitalBrainPage } from "../pages/HospitalBrainPage";
import { DemoPage } from "../pages/DemoPage";
import { PatientJourneyPage } from "../pages/PatientJourneyPage";
import { InnovationPage } from "../pages/InnovationPage";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredRoles?: string[] }> = ({
  children,
  requiredRoles,
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-950">
        <LoadingSpinner size="lg" label="Authenticating session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRoles && user?.role && !requiredRoles.includes(user.role)) {
    return <Navigate to={`/dashboard/${user.role.toLowerCase()}`} replace />;
  }

  return <>{children}</>;
};

export const AppRoutes: React.FC = () => {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public Route */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected Clinical System Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        {/* Default Redirect */}
        <Route
          index
          element={
            user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN" ? (
              <Navigate to="/command-center" replace />
            ) : (
              <Navigate to={`/dashboard/${user?.role?.toLowerCase() || "doctor"}`} replace />
            )
          }
        />

        {/* Command Center (Admin) */}
        <Route
          path="command-center"
          element={
            <ProtectedRoute requiredRoles={["SUPER_ADMIN", "HOSPITAL_ADMIN"]}>
              <CommandCenterPage />
            </ProtectedRoute>
          }
        />

        {/* Phase 7: SIH Demo Mode, Patient Journey, and Innovation Matrix */}
        <Route path="admin/demo" element={<DemoPage />} />
        <Route path="demo" element={<DemoPage />} />
        <Route path="patients/:id/journey" element={<PatientJourneyPage />} />
        <Route path="patient-journey" element={<PatientJourneyPage />} />
        <Route path="admin/innovation" element={<InnovationPage />} />
        <Route path="innovation" element={<InnovationPage />} />

        {/* Phase 6 Hospital Brain Central Intelligence Command Center */}
        <Route path="admin/hospital-brain" element={<HospitalBrainPage />} />
        <Route path="hospital-brain" element={<HospitalBrainPage />} />

        {/* Phase 5 AI Intelligence Layer Modules */}
        <Route path="admin/ai" element={<AiDashboardPage />} />
        <Route path="ai" element={<AiDashboardPage />} />
        <Route path="admin/ai/queue" element={<OpdQueuePredictionPage />} />
        <Route path="admin/ai/bed-forecast" element={<BedForecastPage />} />
        <Route path="admin/ai/pharmacy" element={<PharmacyIntelligencePage />} />
        <Route path="admin/ai/anomalies" element={<OperationalAnomaliesPage />} />
        <Route path="admin/ai/history" element={<AiDashboardPage />} />
        <Route path="ai/documents" element={<DocumentAiPage />} />
        <Route path="ai/handover" element={<AiShiftHandoverPage />} />

        {/* Phase 4 Support Services Modules */}
        <Route path="lab" element={<LaboratoryPage />} />
        <Route path="pharmacy" element={<PharmacyPage />} />
        <Route path="prescriptions" element={<PrescriptionsPage />} />
        <Route path="billing" element={<BillingPage />} />

        {/* Phase 3 Acute Care & Operational Modules */}
        <Route path="emergency" element={<EmergencyPage />} />
        <Route path="resources" element={<ResourceCoordinationPage />} />
        <Route path="ipd" element={<IpdPage />} />
        <Route path="beds" element={<BedManagementPage />} />

        {/* Phase 2 Core HMS Modules */}
        <Route path="patients" element={<PatientsPage />} />
        <Route path="appointments" element={<AppointmentsPage />} />
        <Route path="doctors" element={<DoctorsPage />} />
        <Route path="nurses" element={<NursesPage />} />
        <Route path="opd-queue" element={<OpdQueuePage />} />

        {/* Role Workspaces */}
        <Route path="dashboard/:roleName" element={<RoleDashboardPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
