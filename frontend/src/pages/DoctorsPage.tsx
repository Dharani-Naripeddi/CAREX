import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { doctorsApi, departmentsApi } from "../services/api";
import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Modal } from "../components/ui/Modal";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { useToast } from "../hooks/useToast";
import {
  Clock,
  MapPin,
  Award,
  Building,
  Filter,
  Mic,
  UserPlus,
  Stethoscope,
  Sparkles,
} from "lucide-react";
import { VoiceNoteAssistantModal } from "../components/ai/VoiceNoteAssistantModal";

export const DoctorsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [isAddDoctorOpen, setIsAddDoctorOpen] = useState(false);

  // New Doctor Form State
  const [docName, setDocName] = useState("");
  const [docEmail, setDocEmail] = useState("");
  const [docPhone, setDocPhone] = useState("+1-555-0199");
  const [docDeptId, setDocDeptId] = useState<number | undefined>(undefined);
  const [docSpecialization, setDocSpecialization] = useState("");
  const [docQualification, setDocQualification] = useState("MBBS, MD");
  const [docExp, setDocExp] = useState(8);
  const [docFee, setDocFee] = useState(100.0);
  const [docRoom, setDocRoom] = useState("OPD Suite 201");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: doctors, isLoading, isError, refetch } = useQuery({
    queryKey: ["doctors", selectedDept],
    queryFn: () =>
      doctorsApi.list({
        department_id: selectedDept ? Number(selectedDept) : undefined,
      }),
  });

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.list,
  });

  const toggleAvailabilityMutation = useMutation({
    mutationFn: ({ userId, isAvailable }: { userId: number; isAvailable: boolean }) =>
      doctorsApi.update(userId, { is_available: isAvailable }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctors"] });
      success("Status Updated", "Doctor availability schedule updated.");
    },
    onError: (err: any) => {
      toastError("Update Failed", err.response?.data?.detail || "Could not update availability.");
    },
  });

  const handleAddDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    const targetDept = docDeptId || departments?.[0]?.id;
    if (!targetDept) {
      toastError("Error", "Please select a department.");
      return;
    }
    if (!docName.trim() || !docEmail.trim() || !docSpecialization.trim()) {
      toastError("Validation Error", "Please fill in doctor name, email, and specialization.");
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await doctorsApi.create({
        full_name: docName.trim(),
        email: docEmail.trim().toLowerCase(),
        phone: docPhone.trim(),
        department_id: targetDept,
        specialization: docSpecialization.trim(),
        qualification: docQualification.trim(),
        experience_years: Number(docExp),
        consultation_fee: Number(docFee),
        room_number: docRoom.trim(),
        availability_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        available_from: "09:00",
        available_to: "17:00",
      });

      queryClient.invalidateQueries({ queryKey: ["doctors"] });
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      success("Doctor Registered", `${created.full_name} added to ${created.department_name || "Department"}.`);
      setIsAddDoctorOpen(false);

      // Reset
      setDocName("");
      setDocEmail("");
      setDocSpecialization("");
    } catch (err: any) {
      toastError("Registration Failed", err.response?.data?.detail || "Could not register doctor.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageContainer
      title="Attending Medical Staff & Physicians"
      subtitle="Doctor profiles, clinical specializations, consultation schedules, and availability."
      badge={<Badge variant="info" dot>{doctors?.length || 0} Attending Doctors</Badge>}
      actions={
        <div className="flex items-center gap-2">
          <Button
            variant="glow"
            size="sm"
            onClick={() => {
              setIsAddDoctorOpen(true);
              if (departments && departments.length > 0) {
                setDocDeptId(departments[0].id);
              }
            }}
            leftIcon={<UserPlus className="w-4 h-4" />}
          >
            Register New Physician
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Department Filter & Voice Dictation Action */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-bold text-slate-300">Department:</span>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Clinical Specialties ({doctors?.length || 0})</option>
              {departments?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setVoiceModalOpen(true)}
            className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium flex items-center gap-1.5 shadow-md shadow-indigo-950/40 transition-colors"
          >
            <Mic className="w-3.5 h-3.5" /> AI Voice Dictation Assistant
          </button>
        </div>

        <VoiceNoteAssistantModal
          isOpen={voiceModalOpen}
          onClose={() => setVoiceModalOpen(false)}
          onNoteApproved={(note) => {
            success("Clinical Draft Saved", `Structured note recorded for ${note.chief_complaint}`);
          }}
        />

        {/* Doctor Cards Grid */}
        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Loading physician directory..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : doctors && doctors.length === 0 ? (
          <EmptyState
            title="No physicians found"
            description="No doctors match the selected clinical specialty filter."
            actionLabel="Register Physician"
            onAction={() => setIsAddDoctorOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {doctors?.map((doc) => (
              <Card key={doc.id} hoverable className="flex flex-col justify-between">
                <div>
                  <CardHeader className="flex flex-row items-start justify-between pb-3">
                    <div className="flex items-center gap-3">
                      <img
                        src={
                          doc.avatar_url ||
                          "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80"
                        }
                        alt={doc.full_name}
                        className="w-12 h-12 rounded-2xl object-cover border-2 border-sky-500/30"
                      />
                      <div>
                        <CardTitle className="text-sm font-bold text-white leading-tight">
                          {doc.full_name}
                        </CardTitle>
                        <p className="text-[11px] text-sky-400 font-semibold">{doc.specialization}</p>
                      </div>
                    </div>
                    {doc.is_available ? (
                      <Badge variant="success" dot>Available</Badge>
                    ) : (
                      <Badge variant="neutral">Off Duty</Badge>
                    )}
                  </CardHeader>

                  <CardContent className="space-y-2.5 pt-0 text-xs text-slate-300">
                    <div className="flex items-center gap-2 text-slate-400">
                      <Award className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                      <span className="truncate">{doc.qualification}</span>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400">
                      <Building className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span>{doc.department_name || "General Medicine"}</span>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400">
                      <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                      <span>{doc.room_number || "OPD Consultation Wing"}</span>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span>
                        {doc.available_from} - {doc.available_to} ({doc.availability_days?.length || 5} days/week)
                      </span>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px]">
                      <span className="text-slate-500">Consultation Fee</span>
                      <span className="font-bold text-white font-mono">${doc.consultation_fee.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </div>

                <div className="p-4 pt-0">
                  <Button
                    variant={doc.is_available ? "outline" : "glow"}
                    size="sm"
                    className="w-full"
                    onClick={() =>
                      toggleAvailabilityMutation.mutate({
                        userId: doc.user_id,
                        isAvailable: !doc.is_available,
                      })
                    }
                  >
                    {doc.is_available ? "Set as Off Duty" : "Mark as On Duty"}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Dynamic Register Doctor Modal */}
      <Modal
        isOpen={isAddDoctorOpen}
        onClose={() => setIsAddDoctorOpen(false)}
        title="Register Attending Physician"
        description="Add a new doctor to the hospital clinical staff roster with departmental assignment."
        maxWidth="lg"
      >
        <form onSubmit={handleAddDoctor} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Doctor Full Name *"
              placeholder="e.g. Dr. Priya Patel, MD"
              value={docName}
              onChange={(e) => setDocName(e.target.value)}
              required
            />
            <Input
              label="Email Address *"
              type="email"
              placeholder="e.g. dr.patel@carex.health"
              value={docEmail}
              onChange={(e) => setDocEmail(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Clinical Department *"
              options={
                departments?.map((d) => ({
                  value: d.id,
                  label: d.name,
                })) || []
              }
              value={docDeptId || departments?.[0]?.id}
              onChange={(e) => setDocDeptId(Number(e.target.value))}
            />
            <Input
              label="Specialization *"
              placeholder="e.g. Emergency & Trauma Resuscitation"
              value={docSpecialization}
              onChange={(e) => setDocSpecialization(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Qualification *"
              placeholder="e.g. MBBS, MD, FACEP"
              value={docQualification}
              onChange={(e) => setDocQualification(e.target.value)}
              required
            />
            <Input
              label="Experience (Years)"
              type="number"
              value={docExp}
              onChange={(e) => setDocExp(Number(e.target.value))}
            />
            <Input
              label="Consultation Fee ($)"
              type="number"
              step="0.01"
              value={docFee}
              onChange={(e) => setDocFee(Number(e.target.value))}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Room / Clinic Suite"
              placeholder="e.g. Trauma Bay 1 / OPD Suite 204"
              value={docRoom}
              onChange={(e) => setDocRoom(e.target.value)}
            />
            <Input
              label="Contact Phone"
              placeholder="e.g. +1-555-0108"
              value={docPhone}
              onChange={(e) => setDocPhone(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button type="button" variant="ghost" size="sm" onClick={() => setIsAddDoctorOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="glow"
              size="sm"
              isLoading={isSubmitting}
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Add Physician to Roster
            </Button>
          </div>
        </form>
      </Modal>
    </PageContainer>
  );
};

