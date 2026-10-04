import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { patientsApi, appointmentsApi, tokensApi, departmentsApi, doctorsApi } from "../services/api";
import { Patient, PatientCreatePayload } from "../types/clinical";
import { PageContainer } from "../components/layout/PageContainer";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/Table";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { Badge } from "../components/ui/Badge";
import { Modal } from "../components/ui/Modal";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { useToast } from "../hooks/useToast";
import {
  Users,
  UserPlus,
  Search,
  Filter,
  CalendarPlus,
  Ticket,
  Eye,
  Edit2,
  AlertTriangle,
  Pill,
  HeartPulse,
  Phone,
  Mail,
  MapPin,
  Clock,
  Shield,
  FileText,
} from "lucide-react";

export const PatientsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGender, setSelectedGender] = useState("");
  const [selectedBloodGroup, setSelectedBloodGroup] = useState("");

  // Modals state
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [viewingPatient, setViewingPatient] = useState<Patient | null>(null);
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const [bookingForPatient, setBookingForPatient] = useState<Patient | null>(null);
  const [tokenForPatient, setTokenForPatient] = useState<Patient | null>(null);

  // Form State for Registration
  const [formData, setFormData] = useState<PatientCreatePayload>({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    date_of_birth: "1990-01-01",
    gender: "Male",
    blood_group: "O+",
    address: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    emergency_contact_relation: "Spouse",
    allergies: [],
    current_medications: [],
    medical_history: [],
  });

  const [allergyInput, setAllergyInput] = useState("");
  const [medInput, setMedInput] = useState("");
  const [historyInput, setHistoryInput] = useState("");

  // Booking & Token form state
  const [selectedDocId, setSelectedDocId] = useState<number | undefined>(undefined);
  const [selectedDeptId, setSelectedDeptId] = useState<number | undefined>(undefined);
  const [apptDate, setApptDate] = useState(new Date().toISOString().split("T")[0]);
  const [apptTime, setApptTime] = useState("10:30");
  const [chiefComplaint, setChiefComplaint] = useState("");

  // Data Queries
  const { data: patients, isLoading, isError, refetch } = useQuery({
    queryKey: ["patients", searchQuery, selectedGender, selectedBloodGroup],
    queryFn: () =>
      patientsApi.list({
        query: searchQuery || undefined,
        gender: selectedGender || undefined,
        blood_group: selectedBloodGroup || undefined,
      }),
  });

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.list,
  });

  const { data: doctors } = useQuery({
    queryKey: ["doctors"],
    queryFn: () => doctorsApi.list(),
  });

  // Mutations
  const createPatientMutation = useMutation({
    mutationFn: patientsApi.create,
    onSuccess: (newPatient) => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setIsRegisterOpen(false);
      success("Patient Registered", `${newPatient.full_name} (${newPatient.mrn}) created successfully.`);
      // Reset form
      setFormData({
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        date_of_birth: "1990-01-01",
        gender: "Male",
        blood_group: "O+",
        address: "",
        emergency_contact_name: "",
        emergency_contact_phone: "",
        emergency_contact_relation: "Spouse",
        allergies: [],
        current_medications: [],
        medical_history: [],
      });
    },
    onError: (err: any) => {
      toastError("Registration Failed", err.response?.data?.detail || "Could not register patient.");
    },
  });

  const updatePatientMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => patientsApi.update(id, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      setEditingPatient(null);
      setViewingPatient(updated);
      success("Patient Updated", `${updated.full_name} profile updated successfully.`);
    },
    onError: (err: any) => {
      toastError("Update Failed", err.response?.data?.detail || "Could not update patient.");
    },
  });

  const createAppointmentMutation = useMutation({
    mutationFn: appointmentsApi.create,
    onSuccess: (appt) => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setBookingForPatient(null);
      success("Appointment Scheduled", `Booking #${appt.appointment_number} confirmed for ${apptDate}.`);
    },
    onError: (err: any) => {
      toastError("Booking Failed", err.response?.data?.detail || "Could not book appointment.");
    },
  });

  const generateTokenMutation = useMutation({
    mutationFn: tokensApi.generate,
    onSuccess: (tok) => {
      queryClient.invalidateQueries({ queryKey: ["tokens"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setTokenForPatient(null);
      success("Token Generated", `OPD Token ${tok.token_code} issued. Estimated wait: ~${tok.estimated_wait_minutes} mins.`);
    },
    onError: (err: any) => {
      toastError("Token Generation Failed", err.response?.data?.detail || "Could not issue token.");
    },
  });

  const handleAddAllergy = () => {
    if (allergyInput.trim()) {
      setFormData((prev) => ({ ...prev, allergies: [...(prev.allergies || []), allergyInput.trim()] }));
      setAllergyInput("");
    }
  };

  const handleAddMed = () => {
    if (medInput.trim()) {
      setFormData((prev) => ({ ...prev, current_medications: [...(prev.current_medications || []), medInput.trim()] }));
      setMedInput("");
    }
  };

  const handleAddHistory = () => {
    if (historyInput.trim()) {
      setFormData((prev) => ({ ...prev, medical_history: [...(prev.medical_history || []), historyInput.trim()] }));
      setHistoryInput("");
    }
  };

  return (
    <PageContainer
      title="Master Patient Directory (MPI)"
      subtitle="Centralized patient records, allergies, clinical history, and admissions intake."
      badge={<Badge variant="info" dot>{patients?.length || 0} Registered</Badge>}
      actions={
        <Button
          variant="glow"
          size="sm"
          onClick={() => setIsRegisterOpen(true)}
          leftIcon={<UserPlus className="w-4 h-4" />}
        >
          Register New Patient
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 p-4 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-md">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Patient Name, MRN (CRX-...), Phone, Email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedGender}
              onChange={(e) => setSelectedGender(e.target.value)}
              className="px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Genders</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>

            <select
              value={selectedBloodGroup}
              onChange={(e) => setSelectedBloodGroup(e.target.value)}
              className="px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Blood Groups</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
            </select>
          </div>
        </div>

        {/* Patient Table View */}
        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Loading Master Patient Directory..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : patients && patients.length === 0 ? (
          <EmptyState
            title="No matching patient records found"
            description="Try adjusting your search criteria or register a new patient."
            actionLabel="Register Patient"
            onAction={() => setIsRegisterOpen(true)}
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>MRN & Patient Name</TableHead>
                <TableHead>Demographics</TableHead>
                <TableHead>Contact & Phone</TableHead>
                <TableHead>Documented Allergies</TableHead>
                <TableHead>Emergency Contact</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {patients?.map((p) => (
                <TableRow key={p.id}>
                  <TableCell>
                    <div className="font-bold text-white text-xs">{p.full_name}</div>
                    <div className="text-[10px] text-sky-400 font-mono font-semibold">{p.mrn}</div>
                  </TableCell>
                  <TableCell className="text-xs text-slate-300">
                    <div>{p.age}y • {p.gender}</div>
                    {p.blood_group && (
                      <span className="inline-block text-[10px] font-bold px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 mt-0.5">
                        {p.blood_group}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-xs text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <Phone className="w-3 h-3 text-slate-400" />
                      <span>{p.phone}</span>
                    </div>
                    {p.email && (
                      <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-0.5">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span className="truncate max-w-[140px]">{p.email}</span>
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    {p.allergies && p.allergies.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {p.allergies.map((alg, i) => (
                          <span
                            key={i}
                            className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center gap-1"
                          >
                            <AlertTriangle className="w-2.5 h-2.5" />
                            {alg}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-500">NKDA (None)</span>
                    )}
                  </TableCell>
                  <TableCell className="text-xs text-slate-300">
                    {p.emergency_contact_name ? (
                      <div>
                        <p className="font-semibold text-white">{p.emergency_contact_name}</p>
                        <p className="text-[10px] text-slate-400">{p.emergency_contact_phone} ({p.emergency_contact_relation})</p>
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-500">Not recorded</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setViewingPatient(p)}
                        title="View Full Profile"
                        leftIcon={<Eye className="w-3.5 h-3.5" />}
                      >
                        Profile
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setBookingForPatient(p);
                          setSelectedDeptId(departments?.[0]?.id);
                          setSelectedDocId(doctors?.[0]?.user_id);
                        }}
                        title="Book Appointment"
                        leftIcon={<CalendarPlus className="w-3.5 h-3.5" />}
                      >
                        Book
                      </Button>
                      <Button
                        variant="glow"
                        size="sm"
                        onClick={() => {
                          setTokenForPatient(p);
                          setSelectedDeptId(departments?.[0]?.id);
                        }}
                        title="Issue OPD Queue Token"
                        leftIcon={<Ticket className="w-3.5 h-3.5" />}
                      >
                        Token
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Registration Modal Dialog */}
      <Modal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        title="Register New Patient Record"
        description="Creates a Master Patient Index (MPI) record with medical history and allergies."
        maxWidth="xl"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const fName = formData.first_name.trim();
            const lName = formData.last_name.trim();
            const phone = formData.phone.trim();
            const emName = formData.emergency_contact_name?.trim();
            const emPhone = formData.emergency_contact_phone?.trim();
            const emRel = formData.emergency_contact_relation?.trim();

            if (!fName || !/^[a-zA-Z\s\-']{2,50}$/.test(fName)) {
              toastError("Validation Error", "First Name must contain alphabets only (2-50 characters).");
              return;
            }
            if (!lName || !/^[a-zA-Z\s\-']{2,50}$/.test(lName)) {
              toastError("Validation Error", "Last Name must contain alphabets only (2-50 characters).");
              return;
            }
            if (!/^\d{10}$/.test(phone)) {
              toastError("Validation Error", "Mobile number must be numbers only and exactly 10 digits.");
              return;
            }
            if (emName && !/^[a-zA-Z\s\-']{2,50}$/.test(emName)) {
              toastError("Validation Error", "Emergency contact name must contain alphabets only (2-50 characters).");
              return;
            }
            if (emPhone && !/^\d{10}$/.test(emPhone)) {
              toastError("Validation Error", "Emergency contact phone must be numbers only and exactly 10 digits.");
              return;
            }
            if (emRel && !/^[a-zA-Z\s\-']+$/.test(emRel)) {
              toastError("Validation Error", "Emergency contact relation must contain alphabets only.");
              return;
            }

            createPatientMutation.mutate({
              ...formData,
              first_name: fName,
              last_name: lName,
              phone: phone,
              emergency_contact_name: emName || undefined,
              emergency_contact_phone: emPhone || undefined,
              emergency_contact_relation: emRel || undefined,
            });
          }}
          className="space-y-4 max-h-[75vh] overflow-y-auto pr-1"
        >
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name (Alphabets only) *"
              placeholder="e.g. Eleanor"
              value={formData.first_name}
              maxLength={50}
              pattern="^[A-Za-z\s\-']{2,50}$"
              title="First name must contain alphabets only (min 2 characters)"
              onChange={(e) =>
                setFormData({
                  ...formData,
                  first_name: e.target.value.replace(/[^a-zA-Z\s\-']/g, ""),
                })
              }
              required
            />
            <Input
              label="Last Name (Alphabets only) *"
              placeholder="e.g. Vance"
              value={formData.last_name}
              maxLength={50}
              pattern="^[A-Za-z\s\-']{2,50}$"
              title="Last name must contain alphabets only (min 2 characters)"
              onChange={(e) =>
                setFormData({
                  ...formData,
                  last_name: e.target.value.replace(/[^a-zA-Z\s\-']/g, ""),
                })
              }
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Date of Birth *"
              type="date"
              value={formData.date_of_birth}
              max={new Date().toISOString().split("T")[0]}
              min="1900-01-01"
              onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
              required
            />
            <Select
              label="Gender *"
              options={[
                { value: "Male", label: "Male" },
                { value: "Female", label: "Female" },
                { value: "Other", label: "Other" },
              ]}
              value={formData.gender}
              onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
            />
            <Select
              label="Blood Group"
              options={[
                { value: "O+", label: "O+" },
                { value: "O-", label: "O-" },
                { value: "A+", label: "A+" },
                { value: "A-", label: "A-" },
                { value: "B+", label: "B+" },
                { value: "B-", label: "B-" },
                { value: "AB+", label: "AB+" },
                { value: "AB-", label: "AB-" },
              ]}
              value={formData.blood_group || "O+"}
              onChange={(e) => setFormData({ ...formData, blood_group: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Mobile Number (10 digits) *"
              placeholder="e.g. 9876543210"
              inputMode="numeric"
              type="tel"
              maxLength={10}
              pattern="[0-9]{10}"
              title="Mobile number must be numbers only and exactly 10 digits"
              value={formData.phone}
              helperText={formData.phone ? `${formData.phone.length}/10 digits ${formData.phone.length === 10 ? "✓" : ""}` : "Numbers only, 10 digits"}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  phone: e.target.value.replace(/\D/g, "").slice(0, 10),
                })
              }
              required
            />
            <Input
              label="Email Address"
              type="email"
              placeholder="eleanor.vance@example.com"
              value={formData.email || ""}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <Input
            label="Residential Address"
            placeholder="e.g. 104 Willow Creek Parkway, Boston, MA"
            value={formData.address || ""}
            maxLength={200}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
          />

          {/* Emergency Contact */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Phone className="w-3.5 h-3.5 text-sky-400" />
              Emergency Contact Information
            </h4>
            <div className="grid grid-cols-3 gap-2.5">
              <Input
                label="Contact Name (Alphabets)"
                placeholder="e.g. Thomas Vance"
                value={formData.emergency_contact_name || ""}
                maxLength={50}
                pattern="^[A-Za-z\s\-']+$"
                title="Contact name must contain alphabets only"
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    emergency_contact_name: e.target.value.replace(/[^a-zA-Z\s\-']/g, ""),
                  })
                }
              />
              <Input
                label="Contact Phone (10 digits)"
                placeholder="e.g. 9876543210"
                inputMode="numeric"
                type="tel"
                maxLength={10}
                pattern="[0-9]{10}"
                title="Emergency phone must be numbers only and exactly 10 digits"
                value={formData.emergency_contact_phone || ""}
                helperText={formData.emergency_contact_phone ? `${formData.emergency_contact_phone.length}/10 digits ${formData.emergency_contact_phone.length === 10 ? "✓" : ""}` : undefined}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    emergency_contact_phone: e.target.value.replace(/\D/g, "").slice(0, 10),
                  })
                }
              />
              <Input
                label="Relation (Alphabets)"
                placeholder="e.g. Spouse / Father"
                value={formData.emergency_contact_relation || ""}
                maxLength={30}
                pattern="^[A-Za-z\s\-']+$"
                title="Relation must contain alphabets only"
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    emergency_contact_relation: e.target.value.replace(/[^a-zA-Z\s\-']/g, ""),
                  })
                }
              />
            </div>
          </div>

          {/* Allergies Builder */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Known Drug / Food Allergies
            </label>
            <div className="flex gap-2">
              <Input
                placeholder="Type allergy (e.g. Penicillin, Latex, Peanuts) and press Add"
                value={allergyInput}
                onChange={(e) => setAllergyInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddAllergy();
                  }
                }}
              />
              <Button type="button" variant="outline" size="sm" onClick={handleAddAllergy}>
                Add
              </Button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {formData.allergies?.map((alg, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1.5"
                >
                  <AlertTriangle className="w-3 h-3 text-rose-400" />
                  {alg}
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        allergies: formData.allergies?.filter((_, i) => i !== idx),
                      })
                    }
                    className="hover:text-white"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Current Medications & Medical History */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Current Medications
              </label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g. Atorvastatin 20mg"
                  value={medInput}
                  onChange={(e) => setMedInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddMed();
                    }
                  }}
                />
                <Button type="button" variant="outline" size="sm" onClick={handleAddMed}>
                  Add
                </Button>
              </div>
              <div className="space-y-1">
                {formData.current_medications?.map((m, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200"
                  >
                    <span>{m}</span>
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          current_medications: formData.current_medications?.filter((_, i) => i !== idx),
                        })
                      }
                      className="text-slate-400 hover:text-rose-400"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Medical History
              </label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g. Type 2 Diabetes"
                  value={historyInput}
                  onChange={(e) => setHistoryInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddHistory();
                    }
                  }}
                />
                <Button type="button" variant="outline" size="sm" onClick={handleAddHistory}>
                  Add
                </Button>
              </div>
              <div className="space-y-1">
                {formData.medical_history?.map((h, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200"
                  >
                    <span>{h}</span>
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          medical_history: formData.medical_history?.filter((_, i) => i !== idx),
                        })
                      }
                      className="text-slate-400 hover:text-rose-400"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button type="button" variant="ghost" size="sm" onClick={() => setIsRegisterOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="glow" size="sm" isLoading={createPatientMutation.isPending}>
              Register Patient in MPI
            </Button>
          </div>
        </form>
      </Modal>

      {/* View Clinical Profile Modal */}
      {viewingPatient && (
        <Modal
          isOpen={!!viewingPatient}
          onClose={() => setViewingPatient(null)}
          title={`Clinical Profile • ${viewingPatient.full_name}`}
          description={`MRN: ${viewingPatient.mrn} • Registered on ${new Date(viewingPatient.created_at).toLocaleDateString()}`}
          maxWidth="lg"
        >
          <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
            {/* Header badge strip */}
            <div className="flex flex-wrap items-center gap-2 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
              <Badge variant="info">{viewingPatient.gender}</Badge>
              <Badge variant="neutral">{viewingPatient.age} years old</Badge>
              <Badge variant="critical">Blood Group: {viewingPatient.blood_group || "Unknown"}</Badge>
              <span className="text-slate-400 ml-auto">DOB: {viewingPatient.date_of_birth}</span>
            </div>

            {/* Allergies Highlight Box */}
            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                Documented Allergies
              </h4>
              {viewingPatient.allergies && viewingPatient.allergies.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {viewingPatient.allergies.map((alg, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40"
                    >
                      {alg}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No known drug allergies (NKDA) recorded.</p>
              )}
            </div>

            {/* Medications and History Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2">
                  <Pill className="w-3.5 h-3.5" />
                  Active Medications
                </h4>
                {viewingPatient.current_medications && viewingPatient.current_medications.length > 0 ? (
                  <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                    {viewingPatient.current_medications.map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500">No active medications.</p>
                )}
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                  <HeartPulse className="w-3.5 h-3.5" />
                  Past Medical History
                </h4>
                {viewingPatient.medical_history && viewingPatient.medical_history.length > 0 ? (
                  <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                    {viewingPatient.medical_history.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500">No significant medical history.</p>
                )}
              </div>
            </div>

            {/* Emergency Contact & Contact */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Contact & Emergency Information
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
                <div>
                  <span className="text-slate-500 block">Phone:</span>
                  <span className="font-semibold text-white">{viewingPatient.phone}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Email:</span>
                  <span className="font-semibold text-white">{viewingPatient.email || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Emergency Contact:</span>
                  <span className="font-semibold text-white">
                    {viewingPatient.emergency_contact_name || "N/A"} ({viewingPatient.emergency_contact_relation || "N/A"})
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Emergency Phone:</span>
                  <span className="font-semibold text-white">{viewingPatient.emergency_contact_phone || "N/A"}</span>
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const pat = viewingPatient;
                  setViewingPatient(null);
                  setBookingForPatient(pat);
                }}
                leftIcon={<CalendarPlus className="w-3.5 h-3.5" />}
              >
                Schedule Appointment
              </Button>
              <Button
                variant="glow"
                size="sm"
                onClick={() => {
                  const pat = viewingPatient;
                  setViewingPatient(null);
                  setTokenForPatient(pat);
                }}
                leftIcon={<Ticket className="w-3.5 h-3.5" />}
              >
                Generate OPD Token
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Book Appointment Modal Dialog */}
      {bookingForPatient && (
        <Modal
          isOpen={!!bookingForPatient}
          onClose={() => setBookingForPatient(null)}
          title={`Book Appointment • ${bookingForPatient.full_name}`}
          description={`MRN: ${bookingForPatient.mrn}`}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (selectedDeptId && selectedDocId) {
                createAppointmentMutation.mutate({
                  patient_id: bookingForPatient.id,
                  doctor_id: selectedDocId,
                  department_id: selectedDeptId,
                  appointment_date: apptDate,
                  appointment_time: apptTime,
                  type: "OPD",
                  chief_complaint: chiefComplaint,
                });
              }
            }}
            className="space-y-4 pt-2"
          >
            <Select
              label="Clinical Department *"
              options={
                departments?.map((d) => ({
                  value: d.id,
                  label: d.name,
                })) || []
              }
              value={selectedDeptId}
              onChange={(e) => setSelectedDeptId(Number(e.target.value))}
            />

            <Select
              label="Attending Doctor *"
              options={
                (doctors || [])
                  .filter((doc) => !selectedDeptId || doc.department_id === selectedDeptId)
                  .map((doc) => ({
                    value: doc.user_id,
                    label: `${doc.full_name} (${doc.specialization})`,
                  })) || []
              }
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(Number(e.target.value))}
            />

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Appointment Date *"
                type="date"
                value={apptDate}
                onChange={(e) => setApptDate(e.target.value)}
                required
              />
              <Input
                label="Time Slot *"
                type="time"
                value={apptTime}
                onChange={(e) => setApptTime(e.target.value)}
                required
              />
            </div>

            <Input
              label="Chief Complaint / Reason for Visit *"
              placeholder="e.g. Persistent headache, elevated BP check"
              value={chiefComplaint}
              onChange={(e) => setChiefComplaint(e.target.value)}
              required
            />

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setBookingForPatient(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="glow" size="sm" isLoading={createAppointmentMutation.isPending}>
                Confirm Appointment
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Generate OPD Token Modal Dialog */}
      {tokenForPatient && (
        <Modal
          isOpen={!!tokenForPatient}
          onClose={() => setTokenForPatient(null)}
          title={`Generate OPD Token • ${tokenForPatient.full_name}`}
          description={`MRN: ${tokenForPatient.mrn} • Issues daily sequential queue code`}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (selectedDeptId) {
                generateTokenMutation.mutate({
                  patient_id: tokenForPatient.id,
                  department_id: selectedDeptId,
                  doctor_id: selectedDocId,
                  priority: "NORMAL",
                });
              }
            }}
            className="space-y-4 pt-2"
          >
            <Select
              label="Clinical Department *"
              options={
                departments?.map((d) => ({
                  value: d.id,
                  label: d.name,
                })) || []
              }
              value={selectedDeptId}
              onChange={(e) => setSelectedDeptId(Number(e.target.value))}
            />

            <Select
              label="Assigned Doctor (Optional)"
              options={[
                { value: "", label: "Next Available Doctor" },
                ...(doctors?.map((doc) => ({
                  value: doc.user_id,
                  label: `${doc.full_name} (${doc.specialization})`,
                })) || []),
              ]}
              value={selectedDocId || ""}
              onChange={(e) => setSelectedDocId(e.target.value ? Number(e.target.value) : undefined)}
            />

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300">
              <p className="font-semibold text-sky-400">Automatic Queue Calculation</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Token code will be generated based on department code and daily counter.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setTokenForPatient(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="glow" size="sm" isLoading={generateTokenMutation.isPending}>
                Issue OPD Token
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </PageContainer>
  );
};
