import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { appointmentsApi, patientsApi, doctorsApi, departmentsApi, tokensApi } from "../services/api";
import { Appointment, AppointmentStatus, AppointmentType, PatientCreatePayload } from "../types/clinical";
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
import { useAuth } from "../hooks/useAuth";
import {
  Calendar,
  CalendarPlus,
  Clock,
  UserCheck,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Ticket,
  Filter,
  User,
  Building,
  AlertCircle,
  Search,
  UserPlus,
  FileSpreadsheet,
  Stethoscope,
  Phone,
  Mail,
  HeartPulse,
  Sparkles,
  Check,
} from "lucide-react";

export const AppointmentsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { success, error: toastError } = useToast();

  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<string>("");

  // Modals
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [reschedulingAppt, setReschedulingAppt] = useState<Appointment | null>(null);
  const [cancellingAppt, setCancellingAppt] = useState<Appointment | null>(null);

  // Booking Modal Mode: "NEW_PATIENT" (fill details) vs "EXISTING_PATIENT" (search MPI)
  const [bookingMode, setBookingMode] = useState<"NEW_PATIENT" | "EXISTING_PATIENT">("NEW_PATIENT");

  // Dynamic Patient Form State (Patient direct intake)
  const [patientFirstName, setPatientFirstName] = useState("");
  const [patientLastName, setPatientLastName] = useState("");
  const [patientPhone, setPatientPhone] = useState("");
  const [patientEmail, setPatientEmail] = useState("");
  const [patientDob, setPatientDob] = useState("1995-06-15");
  const [patientGender, setPatientGender] = useState("Male");
  const [patientBloodGroup, setPatientBloodGroup] = useState("O+");
  const [patientAddress, setPatientAddress] = useState("");
  const [emergencyName, setEmergencyName] = useState("");
  const [emergencyPhone, setEmergencyPhone] = useState("");

  // Existing Patient Selector State
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatientId, setSelectedPatientId] = useState<number | undefined>(undefined);

  // Clinical & Scheduling State
  const [bookDoctorId, setBookDoctorId] = useState<number | undefined>(undefined);
  const [bookDeptId, setBookDeptId] = useState<number | undefined>(undefined);
  const [bookDate, setBookDate] = useState(new Date().toISOString().split("T")[0]);
  const [bookTime, setBookTime] = useState("10:30");
  const [bookType, setBookType] = useState<AppointmentType>("OPD");
  const [bookComplaint, setBookComplaint] = useState("");
  const [autoIssueToken, setAutoIssueToken] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reschedule Form
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [rescheduleNotes, setRescheduleNotes] = useState("");

  // Cancel Form
  const [cancelReason, setCancelReason] = useState("");

  // Quick Doctor Modal state in booking flow
  const [isQuickAddDocOpen, setIsQuickAddDocOpen] = useState(false);
  const [quickDocName, setQuickDocName] = useState("");
  const [quickDocEmail, setQuickDocEmail] = useState("");
  const [quickDocSpec, setQuickDocSpec] = useState("");
  const [quickDocFee, setQuickDocFee] = useState(100);
  const [quickDocRoom, setQuickDocRoom] = useState("OPD Suite 201");
  const [isRegisteringDoc, setIsRegisteringDoc] = useState(false);

  // Queries
  const { data: appointments, isLoading, isError, refetch } = useQuery({
    queryKey: ["appointments", activeTab, selectedDoctorId, selectedDate],
    queryFn: () =>
      appointmentsApi.list({
        status: activeTab === "ALL" ? undefined : (activeTab as AppointmentStatus),
        doctor_id: selectedDoctorId ? Number(selectedDoctorId) : undefined,
        date: selectedDate || undefined,
      }),
  });

  const { data: patients } = useQuery({
    queryKey: ["patients"],
    queryFn: () => patientsApi.list(),
  });

  const { data: doctors } = useQuery({
    queryKey: ["doctors"],
    queryFn: () => doctorsApi.list(),
  });

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.list,
  });

  // Filter doctors by selected department dynamically
  const filteredDoctors = (doctors || []).filter((doc) => {
    if (!bookDeptId) return true;
    return doc.department_id === bookDeptId;
  });

  // Filter existing patients in search mode
  const filteredPatients = (patients || []).filter((p) => {
    if (!patientSearch.trim()) return true;
    const query = patientSearch.toLowerCase();
    return (
      p.full_name?.toLowerCase().includes(query) ||
      p.mrn?.toLowerCase().includes(query) ||
      p.phone?.toLowerCase().includes(query) ||
      p.email?.toLowerCase().includes(query)
    );
  });

  // When bookDeptId changes, ensure bookDoctorId is valid
  useEffect(() => {
    if (bookDeptId) {
      if (filteredDoctors.length > 0) {
        const isDocInDept = filteredDoctors.some((d) => d.user_id === bookDoctorId);
        if (!isDocInDept) {
          setBookDoctorId(filteredDoctors[0].user_id);
        }
      } else if (doctors && doctors.length > 0 && !bookDoctorId) {
        setBookDoctorId(doctors[0].user_id);
      }
    }
  }, [bookDeptId, filteredDoctors, bookDoctorId, doctors]);

  // Quick Register Doctor on the fly
  const handleQuickAddDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookDeptId) {
      toastError("Error", "Please select a department first.");
      return;
    }
    if (!quickDocName.trim() || !quickDocEmail.trim()) {
      toastError("Validation Error", "Please fill in physician name and email.");
      return;
    }

    setIsRegisteringDoc(true);
    try {
      const selectedDeptObj = departments?.find((d) => d.id === bookDeptId);
      const spec = quickDocSpec.trim() || `${selectedDeptObj?.name || "Clinical"} Specialist`;

      const newDoc = await doctorsApi.create({
        full_name: quickDocName.trim(),
        email: quickDocEmail.trim().toLowerCase(),
        phone: "+1-555-0199",
        department_id: bookDeptId,
        specialization: spec,
        qualification: "MBBS, MD",
        experience_years: 8,
        consultation_fee: Number(quickDocFee),
        room_number: quickDocRoom.trim(),
        availability_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        available_from: "09:00",
        available_to: "17:00",
      });

      await queryClient.invalidateQueries({ queryKey: ["doctors"] });
      setBookDoctorId(newDoc.user_id);
      success("Doctor Added & Assigned", `${newDoc.full_name} registered and assigned to booking.`);
      setIsQuickAddDocOpen(false);

      // Reset
      setQuickDocName("");
      setQuickDocEmail("");
      setQuickDocSpec("");
    } catch (err: any) {
      toastError("Registration Failed", err.response?.data?.detail || "Could not register doctor.");
    } finally {
      setIsRegisteringDoc(false);
    }
  };

  // Handle open book modal with clean defaults
  const openBookModal = () => {
    setIsBookModalOpen(true);
    const defaultDept = departments?.[0]?.id;
    setBookDeptId(defaultDept);
    const docsInDept = (doctors || []).filter((d) => !defaultDept || d.department_id === defaultDept);
    setBookDoctorId(docsInDept?.[0]?.user_id || doctors?.[0]?.user_id);

    // If user is a patient, pre-fill with their details if possible
    if (user?.role === "PATIENT") {
      const matchedPatient = patients?.find((p) => p.user_id === user.id || p.email === user.email);
      if (matchedPatient) {
        setSelectedPatientId(matchedPatient.id);
        setBookingMode("EXISTING_PATIENT");
      }
    } else {
      if (patients && patients.length > 0) {
        setSelectedPatientId(patients[0].id);
      }
    }
  };

  // Mutations
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status, options }: { id: number; status: AppointmentStatus; options?: any }) =>
      appointmentsApi.updateStatus(id, status, options),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["tokens"] });
      success("Status Updated", `Appointment updated to ${variables.status}.`);
    },
    onError: (err: any) => {
      toastError("Update Failed", err.response?.data?.detail || "Could not update status.");
    },
  });

  const rescheduleMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => appointmentsApi.reschedule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      setReschedulingAppt(null);
      success("Appointment Rescheduled", "Date and time updated successfully.");
    },
    onError: (err: any) => {
      toastError("Reschedule Failed", err.response?.data?.detail || "Could not reschedule.");
    },
  });

  const generateTokenMutation = useMutation({
    mutationFn: tokensApi.generate,
    onSuccess: (tok) => {
      queryClient.invalidateQueries({ queryKey: ["tokens"] });
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      success("OPD Token Issued", `Token ${tok.token_code} generated. Estimated wait: ~${tok.estimated_wait_minutes} mins.`);
    },
    onError: (err: any) => {
      toastError("Token Failed", err.response?.data?.detail || "Could not issue token.");
    },
  });

  // Dynamic Unified Appointment Form Submission
  const handleBookingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookDeptId || !bookDoctorId) {
      toastError("Missing Fields", "Please select a department and attending doctor.");
      return;
    }

    setIsSubmitting(true);
    try {
      let targetPatientId = selectedPatientId;
      let patientDisplayName = "";

      if (bookingMode === "NEW_PATIENT") {
        const fName = patientFirstName.trim();
        const lName = patientLastName.trim();
        const phone = patientPhone.trim();
        const emName = emergencyName.trim();
        const emPhone = emergencyPhone.trim();

        if (!fName || !/^[a-zA-Z\s\-']{2,50}$/.test(fName)) {
          toastError("Validation Error", "Patient First Name must contain alphabets only (2-50 characters).");
          setIsSubmitting(false);
          return;
        }
        if (!lName || !/^[a-zA-Z\s\-']{2,50}$/.test(lName)) {
          toastError("Validation Error", "Patient Last Name must contain alphabets only (2-50 characters).");
          setIsSubmitting(false);
          return;
        }
        if (!/^\d{10}$/.test(phone)) {
          toastError("Validation Error", "Patient Mobile Number must be numbers only and exactly 10 digits.");
          setIsSubmitting(false);
          return;
        }
        if (emName && !/^[a-zA-Z\s\-']{2,50}$/.test(emName)) {
          toastError("Validation Error", "Emergency contact name must contain alphabets only (2-50 characters).");
          setIsSubmitting(false);
          return;
        }
        if (emPhone && !/^\d{10}$/.test(emPhone)) {
          toastError("Validation Error", "Emergency contact phone must be numbers only and exactly 10 digits.");
          setIsSubmitting(false);
          return;
        }

        // 1. Create Patient dynamically
        const newPatientPayload: PatientCreatePayload = {
          first_name: fName,
          last_name: lName,
          phone: phone,
          email: patientEmail.trim() || undefined,
          date_of_birth: patientDob,
          gender: patientGender,
          blood_group: patientBloodGroup,
          address: patientAddress.trim() || undefined,
          emergency_contact_name: emName || undefined,
          emergency_contact_phone: emPhone || undefined,
          emergency_contact_relation: emName ? "Contact" : undefined,
          allergies: [],
          current_medications: [],
          medical_history: [],
        };

        const createdPatient = await patientsApi.create(newPatientPayload);
        targetPatientId = createdPatient.id;
        patientDisplayName = `${createdPatient.full_name} (${createdPatient.mrn})`;
      } else {
        const found = patients?.find((p) => p.id === selectedPatientId);
        patientDisplayName = found ? `${found.full_name} (${found.mrn})` : `Patient #${selectedPatientId}`;
      }

      if (!targetPatientId) {
        toastError("Error", "No patient selected.");
        setIsSubmitting(false);
        return;
      }

      // 2. Create Appointment
      const createdAppt = await appointmentsApi.create({
        patient_id: targetPatientId,
        doctor_id: bookDoctorId,
        department_id: bookDeptId,
        appointment_date: bookDate,
        appointment_time: bookTime,
        type: bookType,
        chief_complaint: bookComplaint || "General Outpatient Consultation",
      });

      // 3. Optionally Issue OPD Live Queue Token
      if (autoIssueToken) {
        try {
          await tokensApi.generate({
            patient_id: targetPatientId,
            department_id: bookDeptId,
            doctor_id: bookDoctorId,
            appointment_id: createdAppt.id,
            priority: "NORMAL",
          });
        } catch (tokErr) {
          console.warn("Auto-token generation error:", tokErr);
        }
      }

      // Invalidate all query caches
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["tokens"] });
      queryClient.invalidateQueries({ queryKey: ["roleDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });

      success(
        "Appointment Confirmed!",
        `Booking #${createdAppt.appointment_number} scheduled for ${patientDisplayName} on ${bookDate} at ${bookTime}.`
      );

      setIsBookModalOpen(false);

      // Reset form
      setPatientFirstName("");
      setPatientLastName("");
      setPatientPhone("");
      setPatientEmail("");
      setPatientAddress("");
      setEmergencyName("");
      setEmergencyPhone("");
      setBookComplaint("");
    } catch (err: any) {
      toastError("Booking Failed", err.response?.data?.detail || "Could not schedule appointment.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: AppointmentStatus) => {
    switch (status) {
      case "SCHEDULED":
        return <Badge variant="info">Scheduled</Badge>;
      case "CHECKED_IN":
        return <Badge variant="warning" dot>Checked In</Badge>;
      case "WAITING":
        return <Badge variant="warning" dot>In Waiting Queue</Badge>;
      case "IN_CONSULTATION":
        return <Badge variant="critical" dot>In Consultation</Badge>;
      case "COMPLETED":
        return <Badge variant="success" dot>Completed</Badge>;
      case "CANCELLED":
        return <Badge variant="neutral">Cancelled</Badge>;
      case "NO_SHOW":
        return <Badge variant="neutral">No Show</Badge>;
    }
  };

  const statusTabs = [
    { key: "ALL", label: "All Appointments" },
    { key: "SCHEDULED", label: "Scheduled" },
    { key: "CHECKED_IN", label: "Checked In" },
    { key: "WAITING", label: "Waiting Queue" },
    { key: "IN_CONSULTATION", label: "In Consultation" },
    { key: "COMPLETED", label: "Completed" },
    { key: "CANCELLED", label: "Cancelled" },
  ];

  const quickComplaintPresets = [
    "Routine OPD Health Checkup",
    "Persistent Headache & Migraine",
    "Chest Discomfort & Palpitations",
    "Joint Pain & Mobility Assessment",
    "Seasonal Flu, Cough & Fever",
    "Blood Pressure & Sugar Review",
  ];

  const quickTimeSlots = ["09:00", "09:30", "10:30", "11:30", "14:00", "15:30", "16:30", "17:30"];

  const selectedPatientObj = patients?.find((p) => p.id === selectedPatientId);

  return (
    <PageContainer
      title="Appointment Scheduling & Clinical Roster"
      subtitle="Comprehensive outpatient appointments, check-in queue, and consultation lifecycle."
      badge={<Badge variant="info" dot>{appointments?.length || 0} Total</Badge>}
      actions={
        <Button
          variant="glow"
          size="sm"
          onClick={openBookModal}
          leftIcon={<CalendarPlus className="w-4 h-4" />}
        >
          Book New Appointment
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-slate-800">
          {statusTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-xl transition-all whitespace-nowrap ${
                activeTab === tab.key
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Doctor & Date Filter Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 p-3.5 rounded-2xl bg-slate-900/70 border border-slate-800 backdrop-blur-md">
          <div className="flex-1 flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-bold text-slate-300">Filter By:</span>
          </div>

          <select
            value={selectedDoctorId}
            onChange={(e) => setSelectedDoctorId(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">All Attending Doctors</option>
            {doctors?.map((doc) => (
              <option key={doc.user_id} value={doc.user_id}>
                {doc.full_name} ({doc.specialization})
              </option>
            ))}
          </select>

          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />

          {(selectedDoctorId || selectedDate || activeTab !== "ALL") && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedDoctorId("");
                setSelectedDate("");
                setActiveTab("ALL");
              }}
              leftIcon={<RotateCcw className="w-3 h-3" />}
            >
              Reset
            </Button>
          )}
        </div>

        {/* Appointments Table */}
        {isLoading ? (
          <div className="py-20">
            <LoadingSpinner size="lg" label="Loading appointment schedule..." />
          </div>
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : appointments && appointments.length === 0 ? (
          <EmptyState
            title="No appointments found"
            description="No scheduled or historical appointments match the current filter."
            actionLabel="Schedule Appointment"
            onAction={openBookModal}
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Appt #</TableHead>
                <TableHead>Patient & MRN</TableHead>
                <TableHead>Attending Doctor</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Date & Time</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {appointments?.map((appt) => (
                <TableRow key={appt.id}>
                  <TableCell className="font-mono text-xs text-sky-400 font-bold">
                    {appt.appointment_number}
                  </TableCell>
                  <TableCell>
                    <div className="font-bold text-white text-xs">{appt.patient_name}</div>
                    <div className="text-[10px] text-slate-400">
                      {appt.patient_mrn} {appt.patient_phone ? `• ${appt.patient_phone}` : ""}
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-slate-300">
                    <div className="font-semibold text-white">{appt.doctor_name}</div>
                    <div className="text-[10px] text-slate-400">{appt.doctor_specialization || "Physician"}</div>
                  </TableCell>
                  <TableCell className="text-xs text-slate-300">
                    {appt.department_name}
                  </TableCell>
                  <TableCell className="text-xs text-slate-300">
                    <div className="font-medium text-white">{appt.appointment_date}</div>
                    <div className="text-[11px] text-sky-400 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {appt.appointment_time}
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(appt.status)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {/* Action buttons based on status */}
                      {appt.status === "SCHEDULED" && (
                        <>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() =>
                              updateStatusMutation.mutate({ id: appt.id, status: "CHECKED_IN" })
                            }
                            title="Check In Patient"
                            leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                          >
                            Check-In
                          </Button>
                          <Button
                            variant="glow"
                            size="sm"
                            onClick={() =>
                              generateTokenMutation.mutate({
                                patient_id: appt.patient_id,
                                department_id: appt.department_id,
                                doctor_id: appt.doctor_id,
                                appointment_id: appt.id,
                                priority: "NORMAL",
                              })
                            }
                            title="Issue OPD Token"
                            leftIcon={<Ticket className="w-3.5 h-3.5" />}
                          >
                            Token
                          </Button>
                        </>
                      )}

                      {(appt.status === "CHECKED_IN" || appt.status === "WAITING") && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() =>
                            updateStatusMutation.mutate({
                              id: appt.id,
                              status: "IN_CONSULTATION",
                              options: { notes: "Doctor started clinical consultation." },
                            })
                          }
                          title="Call into Consultation Room"
                        >
                          Start Consult
                        </Button>
                      )}

                      {appt.status === "IN_CONSULTATION" && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() =>
                            updateStatusMutation.mutate({
                              id: appt.id,
                              status: "COMPLETED",
                              options: { notes: "Consultation completed, prescription provided." },
                            })
                          }
                          title="Complete Consultation"
                          leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                        >
                          Complete
                        </Button>
                      )}

                      {/* Reschedule / Cancel */}
                      {appt.status !== "COMPLETED" && appt.status !== "CANCELLED" && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setReschedulingAppt(appt);
                              setNewDate(appt.appointment_date);
                              setNewTime(appt.appointment_time);
                            }}
                            title="Reschedule"
                          >
                            Reschedule
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setCancellingAppt(appt);
                              setCancelReason("");
                            }}
                            className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                            title="Cancel Appointment"
                          >
                            Cancel
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Dynamic Schedule Clinical Appointment Modal */}
      <Modal
        isOpen={isBookModalOpen}
        onClose={() => setIsBookModalOpen(false)}
        title="Schedule Clinical Appointment"
        description="Book outpatient consultations, register patient details dynamically, and issue real-time queue tokens."
        maxWidth="2xl"
      >
        <form onSubmit={handleBookingSubmit} className="space-y-4 pt-2">
          {/* Mode Switcher Tabs */}
          <div className="p-1 rounded-xl bg-slate-950 border border-slate-800 grid grid-cols-2 gap-1">
            <button
              type="button"
              onClick={() => setBookingMode("NEW_PATIENT")}
              className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                bookingMode === "NEW_PATIENT"
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <UserPlus className="w-4 h-4" />
              <span>Patient Direct Intake (Fill Details)</span>
            </button>
            <button
              type="button"
              onClick={() => setBookingMode("EXISTING_PATIENT")}
              className={`py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                bookingMode === "EXISTING_PATIENT"
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/25"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Search className="w-4 h-4" />
              <span>Search Registered Patients ({patients?.length || 0})</span>
            </button>
          </div>

          {/* MODE 1: DYNAMIC PATIENT INTAKE FORM */}
          {bookingMode === "NEW_PATIENT" && (
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-400">
                  <User className="w-4 h-4" />
                  <span>1. Patient Demographics & Contact</span>
                </div>
                <span className="text-[10px] text-slate-500 font-medium">Auto-generates CRX MRN in Master Patient Index</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input
                  label="First Name (Alphabets only) *"
                  placeholder="e.g. Johnathan"
                  value={patientFirstName}
                  maxLength={50}
                  pattern="^[A-Za-z\s\-']{2,50}$"
                  title="First name must contain alphabets only (min 2 characters)"
                  onChange={(e) => setPatientFirstName(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                  required
                />
                <Input
                  label="Last Name (Alphabets only) *"
                  placeholder="e.g. Watson"
                  value={patientLastName}
                  maxLength={50}
                  pattern="^[A-Za-z\s\-']{2,50}$"
                  title="Last name must contain alphabets only (min 2 characters)"
                  onChange={(e) => setPatientLastName(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Input
                  label="Mobile Number (10 digits) *"
                  placeholder="e.g. 9876543210"
                  inputMode="numeric"
                  type="tel"
                  maxLength={10}
                  pattern="[0-9]{10}"
                  title="Mobile number must be numbers only and exactly 10 digits"
                  value={patientPhone}
                  helperText={patientPhone ? `${patientPhone.length}/10 digits ${patientPhone.length === 10 ? "✓" : ""}` : "Numbers only, 10 digits"}
                  onChange={(e) => setPatientPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                  required
                />
                <Input
                  label="Email Address (Optional)"
                  type="email"
                  placeholder="e.g. patient@carex.health"
                  value={patientEmail}
                  onChange={(e) => setPatientEmail(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <Input
                  label="Date of Birth *"
                  type="date"
                  value={patientDob}
                  max={new Date().toISOString().split("T")[0]}
                  min="1900-01-01"
                  onChange={(e) => setPatientDob(e.target.value)}
                  required
                />
                <Select
                  label="Gender *"
                  options={[
                    { value: "Male", label: "Male" },
                    { value: "Female", label: "Female" },
                    { value: "Other", label: "Other" },
                  ]}
                  value={patientGender}
                  onChange={(e) => setPatientGender(e.target.value)}
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
                  value={patientBloodGroup}
                  onChange={(e) => setPatientBloodGroup(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <Input
                  label="Residential Address (Optional)"
                  placeholder="e.g. 742 Evergreen Terrace"
                  value={patientAddress}
                  maxLength={200}
                  onChange={(e) => setPatientAddress(e.target.value)}
                />
                <Input
                  label="Emergency Contact Name"
                  placeholder="e.g. Sarah Watson"
                  value={emergencyName}
                  maxLength={50}
                  pattern="^[A-Za-z\s\-']+$"
                  title="Contact name must contain alphabets only"
                  onChange={(e) => setEmergencyName(e.target.value.replace(/[^a-zA-Z\s\-']/g, ""))}
                />
                <Input
                  label="Emergency Phone (10 digits)"
                  placeholder="e.g. 9876543210"
                  inputMode="numeric"
                  type="tel"
                  maxLength={10}
                  pattern="[0-9]{10}"
                  title="Emergency phone must be numbers only and exactly 10 digits"
                  value={emergencyPhone}
                  helperText={emergencyPhone ? `${emergencyPhone.length}/10 digits ${emergencyPhone.length === 10 ? "✓" : ""}` : undefined}
                  onChange={(e) => setEmergencyPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                />
              </div>
            </div>
          )}

          {/* MODE 2: SEARCH REGISTERED PATIENTS */}
          {bookingMode === "EXISTING_PATIENT" && (
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-400">
                  <UserCheck className="w-4 h-4" />
                  <span>1. Select Registered Patient</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  Showing {filteredPatients.length} of {patients?.length || 0} registered patients
                </span>
              </div>

              {/* Patient Search Input */}
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter by Patient Name, MRN (CRX-...), or Phone..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              {/* Select Dropdown */}
              <div>
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
                  size={filteredPatients.length > 3 ? 3 : 2}
                  required
                >
                  {filteredPatients.map((p) => (
                    <option key={p.id} value={p.id} className="py-1 px-2">
                      {p.full_name} • MRN: {p.mrn} • Phone: {p.phone} ({p.gender}, {p.age}y, {p.blood_group || "N/A"})
                    </option>
                  ))}
                  {filteredPatients.length === 0 && (
                    <option disabled value="">
                      No registered patients match your search. Switch to "Patient Direct Intake" tab to register.
                    </option>
                  )}
                </select>
              </div>

              {/* Selected Patient Preview Card */}
              {selectedPatientObj && (
                <div className="p-3 rounded-xl bg-sky-950/20 border border-sky-500/30 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-sky-500/20 text-sky-400 font-bold flex items-center justify-center text-sm">
                      {selectedPatientObj.first_name[0]}
                      {selectedPatientObj.last_name[0]}
                    </div>
                    <div>
                      <div className="font-bold text-white flex items-center gap-2">
                        <span>{selectedPatientObj.full_name}</span>
                        <Badge variant="info">{selectedPatientObj.mrn}</Badge>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {selectedPatientObj.gender} • {selectedPatientObj.age} yrs • Blood: {selectedPatientObj.blood_group || "Unknown"} • {selectedPatientObj.phone}
                      </div>
                    </div>
                  </div>
                  {selectedPatientObj.allergies && selectedPatientObj.allergies.length > 0 && (
                    <Badge variant="critical">Allergies: {selectedPatientObj.allergies.join(", ")}</Badge>
                  )}
                </div>
              )}
            </div>
          )}

          {/* SECTION 2: CLINICAL DIRECTIVE & SCHEDULING */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                <Stethoscope className="w-4 h-4" />
                <span>2. Department, Doctor & Slot</span>
              </div>
              <span className="text-[10px] text-slate-500">Doctors filtered by chosen specialty</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Clinical Department *
                </label>
                <select
                  value={bookDeptId}
                  onChange={(e) => setBookDeptId(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                >
                  {departments?.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Attending Doctor *
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      const selDept = departments?.find((d) => d.id === bookDeptId);
                      setQuickDocSpec(selDept ? `${selDept.name} Specialist` : "");
                      setIsQuickAddDocOpen(true);
                    }}
                    className="text-[10px] text-sky-400 hover:text-sky-300 flex items-center gap-1 font-semibold hover:underline"
                  >
                    <UserPlus className="w-3 h-3" />
                    + Add Doctor
                  </button>
                </div>
                <select
                  value={bookDoctorId}
                  onChange={(e) => setBookDoctorId(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                >
                  {filteredDoctors.length > 0 ? (
                    filteredDoctors.map((doc) => (
                      <option key={doc.user_id} value={doc.user_id}>
                        {doc.full_name} • {doc.specialization} (${doc.consultation_fee})
                      </option>
                    ))
                  ) : (
                    <>
                      <option disabled value="">
                        -- No doctor assigned to this department yet --
                      </option>
                      {doctors?.map((doc) => (
                        <option key={doc.user_id} value={doc.user_id}>
                          [Covering / On-Call] {doc.full_name} ({doc.department_name || "General Medicine"})
                        </option>
                      ))}
                    </>
                  )}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Input
                label="Appointment Date *"
                type="date"
                value={bookDate}
                onChange={(e) => setBookDate(e.target.value)}
                required
              />
              <Input
                label="Appointment Time *"
                type="time"
                value={bookTime}
                onChange={(e) => setBookTime(e.target.value)}
                required
              />
              <Select
                label="Consultation Type"
                options={[
                  { value: "OPD", label: "OPD Consultation" },
                  { value: "EMERGENCY", label: "Emergency Walk-in" },
                  { value: "FOLLOW_UP", label: "Follow-up Visit" },
                  { value: "ROUTINE_CHECKUP", label: "Routine Health Checkup" },
                ]}
                value={bookType}
                onChange={(e) => setBookType(e.target.value as AppointmentType)}
              />
            </div>

            {/* Quick Time Slot Pills */}
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-slate-400">Quick Slot Presets:</span>
              <div className="flex flex-wrap gap-1.5">
                {quickTimeSlots.map((slot) => (
                  <button
                    key={slot}
                    type="button"
                    onClick={() => setBookTime(slot)}
                    className={`px-2.5 py-1 text-[11px] font-mono rounded-lg border transition-all ${
                      bookTime === slot
                        ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 font-bold"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                    }`}
                  >
                    {slot}
                  </button>
                ))}
              </div>
            </div>

            {/* Chief Complaint Input & Quick Presets */}
            <div className="space-y-1.5 pt-1">
              <Input
                label="Chief Complaint / Clinical Directive *"
                placeholder="e.g. Chest tightness on exertion, review cardiac telemetry"
                value={bookComplaint}
                onChange={(e) => setBookComplaint(e.target.value)}
                required
              />
              <div className="flex flex-wrap gap-1.5 pt-0.5">
                {quickComplaintPresets.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setBookComplaint(preset)}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-slate-400 hover:text-sky-300 hover:border-sky-500/40 transition-all"
                  >
                    + {preset}
                  </button>
                ))}
              </div>
            </div>

            {/* Auto-Issue Token Option */}
            <label className="flex items-center gap-2.5 pt-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoIssueToken}
                onChange={(e) => setAutoIssueToken(e.target.checked)}
                className="w-4 h-4 rounded text-sky-500 bg-slate-950 border-slate-800 focus:ring-sky-500"
              />
              <span className="text-xs text-slate-300 flex items-center gap-1.5">
                <Ticket className="w-3.5 h-3.5 text-amber-400" />
                <strong>Automatically Issue OPD Live Queue Token</strong> upon booking
              </span>
            </label>
          </div>

          {/* Modal Footer Actions */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-800">
            <span className="text-[11px] text-slate-500">
              {bookingMode === "NEW_PATIENT" ? "✨ Registers patient & schedules visit" : "⚡ Links to existing patient MRN"}
            </span>
            <div className="flex items-center gap-2.5">
              <Button type="button" variant="ghost" size="sm" onClick={() => setIsBookModalOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="glow"
                size="sm"
                isLoading={isSubmitting}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                Confirm Appointment Booking
              </Button>
            </div>
          </div>
        </form>
      </Modal>

      {/* Reschedule Modal */}
      {reschedulingAppt && (
        <Modal
          isOpen={!!reschedulingAppt}
          onClose={() => setReschedulingAppt(null)}
          title={`Reschedule Appointment #${reschedulingAppt.appointment_number}`}
          description={`Patient: ${reschedulingAppt.patient_name} • Dr. ${reschedulingAppt.doctor_name}`}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              rescheduleMutation.mutate({
                id: reschedulingAppt.id,
                data: {
                  appointment_date: newDate,
                  appointment_time: newTime,
                  notes: rescheduleNotes,
                },
              });
            }}
            className="space-y-4 pt-2"
          >
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="New Date *"
                type="date"
                value={newDate}
                onChange={(e) => setNewDate(e.target.value)}
                required
              />
              <Input
                label="New Time *"
                type="time"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                required
              />
            </div>

            <Input
              label="Rescheduling Reason / Notes"
              placeholder="e.g. Patient requested morning slot change"
              value={rescheduleNotes}
              onChange={(e) => setRescheduleNotes(e.target.value)}
            />

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setReschedulingAppt(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="glow" size="sm" isLoading={rescheduleMutation.isPending}>
                Save Reschedule
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Cancel Appointment Modal */}
      {cancellingAppt && (
        <Modal
          isOpen={!!cancellingAppt}
          onClose={() => setCancellingAppt(null)}
          title={`Cancel Appointment #${cancellingAppt.appointment_number}`}
          description={`Revokes appointment for ${cancellingAppt.patient_name}.`}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateStatusMutation.mutate({
                id: cancellingAppt.id,
                status: "CANCELLED",
                options: { cancellation_reason: cancelReason },
              });
              setCancellingAppt(null);
            }}
            className="space-y-4 pt-2"
          >
            <Input
              label="Cancellation Reason *"
              placeholder="e.g. Patient called to cancel, schedule conflict"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              required
            />

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setCancellingAppt(null)}>
                Keep Appointment
              </Button>
              <Button type="submit" variant="destructive" size="sm">
                Confirm Cancellation
              </Button>
            </div>
          </form>
        </Modal>
      )}
      {/* Quick Add Doctor Modal Dialog in Booking Flow */}
      {isQuickAddDocOpen && (
        <Modal
          isOpen={isQuickAddDocOpen}
          onClose={() => setIsQuickAddDocOpen(false)}
          title="Quick Register Physician"
          description={`Add a specialist doctor to ${
            departments?.find((d) => d.id === bookDeptId)?.name || "selected department"
          }.`}
          maxWidth="md"
        >
          <form onSubmit={handleQuickAddDoctor} className="space-y-3.5 pt-2">
            <Input
              label="Doctor Full Name *"
              placeholder="e.g. Dr. Priya Patel, MD"
              value={quickDocName}
              onChange={(e) => setQuickDocName(e.target.value)}
              required
            />
            <Input
              label="Doctor Email *"
              type="email"
              placeholder="e.g. dr.patel@carex.health"
              value={quickDocEmail}
              onChange={(e) => setQuickDocEmail(e.target.value)}
              required
            />
            <Input
              label="Specialization *"
              placeholder="e.g. Emergency & Trauma Resuscitation"
              value={quickDocSpec}
              onChange={(e) => setQuickDocSpec(e.target.value)}
              required
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Consultation Fee ($)"
                type="number"
                step="0.01"
                value={quickDocFee}
                onChange={(e) => setQuickDocFee(Number(e.target.value))}
              />
              <Input
                label="Room / Clinic Suite"
                placeholder="e.g. Trauma Bay 1"
                value={quickDocRoom}
                onChange={(e) => setQuickDocRoom(e.target.value)}
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setIsQuickAddDocOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="glow"
                size="sm"
                isLoading={isRegisteringDoc}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                Save & Assign Doctor
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </PageContainer>
  );
};

