import React from "react";
import { FileQuestion, Home } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/Button";

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-6 bg-[#080e1e] text-slate-100 text-center">
      <div className="w-16 h-16 rounded-3xl bg-slate-800 text-slate-400 flex items-center justify-center mb-6 ring-8 ring-slate-800/50">
        <FileQuestion className="w-8 h-8" />
      </div>

      <h1 className="text-3xl font-extrabold text-white mb-2">404 • Page Not Found</h1>
      <p className="text-sm text-slate-400 max-w-md mb-6 leading-relaxed">
        The requested clinical module or patient route does not exist in this CAREX installation.
      </p>

      <Link to="/dashboard">
        <Button variant="glow" size="md" leftIcon={<Home className="w-4 h-4" />}>
          Back to Dashboard
        </Button>
      </Link>
    </div>
  );
};
