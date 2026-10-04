import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { UserProfile, RoleEnum } from "../types/auth";
import { authApi } from "../services/api";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<UserProfile>;
  logout: () => Promise<void>;
  hasRole: (roles: RoleEnum | RoleEnum[]) => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: boolean;
  isDoctor: boolean;
  isNurse: boolean;
  isPatient: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_USERS_MAP: Record<string, UserProfile> = {
  "superadmin@carex.health": {
    id: 1,
    email: "superadmin@carex.health",
    full_name: "Devin Reynolds (Super Admin)",
    role: "SUPER_ADMIN",
    role_display_name: "Super Administrator",
    permissions: ["*"],
    department_name: "Executive Leadership",
    avatar_url: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
  "admin@carex.health": {
    id: 2,
    email: "admin@carex.health",
    full_name: "Dr. Eleanor Vance (Hospital Admin)",
    role: "HOSPITAL_ADMIN",
    role_display_name: "Hospital Administrator",
    permissions: ["hospital:read", "hospital:write", "users:read", "users:write", "departments:read", "departments:write", "dashboard:admin", "audit:read"],
    department_name: "General Outpatient Medicine",
    avatar_url: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
  "dr.sharma@carex.health": {
    id: 3,
    email: "dr.sharma@carex.health",
    full_name: "Dr. Rajesh Sharma, MD",
    role: "DOCTOR",
    role_display_name: "Attending Physician / Doctor",
    permissions: ["patients:read", "patients:write", "labs:order", "prescriptions:write"],
    department_name: "Cardiology & Vascular",
    avatar_url: "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
  "nurse.sarah@carex.health": {
    id: 4,
    email: "nurse.sarah@carex.health",
    full_name: "Sarah Jenkins, RN",
    role: "NURSE",
    role_display_name: "Registered Nurse",
    permissions: ["patients:read", "vitals:write"],
    department_name: "Emergency & Trauma",
    avatar_url: "https://images.unsplash.com/photo-1594824813501-489e5a8f5f84?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
  "reception@carex.health": {
    id: 5,
    email: "reception@carex.health",
    full_name: "Carlos Gomez",
    role: "RECEPTIONIST",
    role_display_name: "Front Desk & Receptionist",
    permissions: ["patients:register", "billing:write"],
    department_name: "General Outpatient Medicine",
    avatar_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
  "pharmacy@carex.health": {
    id: 6,
    email: "pharmacy@carex.health",
    full_name: "David Kim, PharmD",
    role: "PHARMACIST",
    role_display_name: "Clinical Pharmacist",
    permissions: ["prescriptions:dispense", "inventory:write"],
    department_name: "Pharmacy & Therapeutics",
    avatar_url: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
  "lab@carex.health": {
    id: 7,
    email: "lab@carex.health",
    full_name: "Amanda Foster, MLS",
    role: "LAB_TECHNICIAN",
    role_display_name: "Medical Laboratory Technician",
    permissions: ["labs:report", "labs:verify"],
    department_name: "Pathology & Diagnostic Labs",
    avatar_url: "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
  "patient.john@carex.health": {
    id: 8,
    email: "patient.john@carex.health",
    full_name: "Johnathan Doe",
    role: "PATIENT",
    role_display_name: "Patient / Family Member",
    permissions: ["patient_portal:read"],
    department_name: null,
    avatar_url: "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&auto=format&fit=crop&q=80",
    is_active: true,
  },
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore session from localStorage on startup
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem("carex_token");
      const storedUser = localStorage.getItem("carex_user");

      if (storedToken && storedUser) {
        try {
          setToken(storedToken);
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);

          // Only validate against backend if not a demo-token
          if (!storedToken.startsWith("demo-token-")) {
            try {
              const freshProfile = await authApi.getMe();
              setUser(freshProfile);
              localStorage.setItem("carex_user", JSON.stringify(freshProfile));
            } catch {
              // Token might be expired or backend offline - keep parsedUser if offline
            }
          }
        } catch {
          localStorage.removeItem("carex_token");
          localStorage.removeItem("carex_user");
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<UserProfile> => {
    setIsLoading(true);
    const cleanEmail = email.toLowerCase().trim();
    try {
      let userProfile: UserProfile;
      let accessToken: string;

      try {
        const response = await authApi.login(cleanEmail, password);
        userProfile = response.user;
        accessToken = response.access_token;
      } catch (err: any) {
        const isNetworkError = !err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error");
        if (isNetworkError && DEMO_USERS_MAP[cleanEmail]) {
          // Graceful demo fallback when backend is temporarily offline
          userProfile = DEMO_USERS_MAP[cleanEmail];
          accessToken = `demo-token-${userProfile.role.toLowerCase()}-${Date.now()}`;
        } else {
          throw err;
        }
      }

      localStorage.setItem("carex_token", accessToken);
      localStorage.setItem("carex_user", JSON.stringify(userProfile));
      setToken(accessToken);
      setUser(userProfile);
      return userProfile;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      setToken(null);
      setIsLoading(false);
    }
  }, []);

  const hasRole = useCallback(
    (roles: RoleEnum | RoleEnum[]): boolean => {
      if (!user) return false;
      // Super admin has global bypass permissions
      if (user.role === "SUPER_ADMIN") return true;

      const allowedRoles = Array.isArray(roles) ? roles : [roles];
      return allowedRoles.includes(user.role);
    },
    [user]
  );

  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!user) return false;
      if (user.role === "SUPER_ADMIN" || user.permissions.includes("*")) return true;
      return user.permissions.includes(permission);
    },
    [user]
  );

  const isAdmin = user?.role === "SUPER_ADMIN" || user?.role === "HOSPITAL_ADMIN";
  const isDoctor = user?.role === "DOCTOR";
  const isNurse = user?.role === "NURSE";
  const isPatient = user?.role === "PATIENT";

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        hasRole,
        hasPermission,
        isAdmin,
        isDoctor,
        isNurse,
        isPatient,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
