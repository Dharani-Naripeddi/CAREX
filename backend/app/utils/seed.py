"""
CAREX Database Seeder (Phase 1, Phase 2, Phase 3 & Phase 4)

Initializes default roles, departments, demo users, doctor/nurse profiles,
patient MPI records, appointments, OPD tokens, clinical wards, rooms, beds,
emergency cases with rule-based triage outputs, IPD admissions,
Laboratory catalogue, test orders, structured results, released reports,
Pharmacy medicines catalogue, batch inventories, stock transactions, prescriptions, dispensations,
Billing service items, patient invoices, payments, and multi-role notifications.
"""

import sys
import os
import datetime
import random

# Add backend directory to sys.path if run directly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.role import Role, RoleEnum
from app.models.department import Department
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.models.doctor_profile import DoctorProfile
from app.models.nurse_profile import NurseProfile, ShiftEnum
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.opd_token import OpdToken, TokenStatus, TokenPriority
from app.models.ward import Ward
from app.models.room import Room, RoomType
from app.models.bed import Bed, BedStatus
from app.models.admission import Admission, AdmissionStatus, DischargeCondition
from app.models.emergency_case import EmergencyCase, TriageLevel, ConsciousnessLevel, EmergencyCaseStatus

# Phase 4 Models
from app.models.lab import (
    LabTest,
    LabOrder,
    LabResult,
    LabResultParameter,
    LabReport,
    LabOrderStatus,
    LabOrderPriority,
    LabResultFlag,
    LabReportStatus,
)
from app.models.pharmacy import (
    Medicine,
    MedicineBatch,
    PharmacyTransaction,
    Prescription,
    PrescriptionItem,
    Dispensing,
    DispensingItem,
    PharmacyTransactionType,
    PrescriptionStatus,
    PrescriptionItemStatus,
)
from app.models.billing import (
    BillingItem,
    Invoice,
    InvoiceItem,
    Payment,
    BillingCategory,
    InvoicePaymentStatus,
    PaymentMethod,
)
from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
)
from app.models.ai import (
    AIPrediction,
    AIAlert,
    AIFeedback,
    AIDocumentRecord,
    AIShiftHandover,
    ModelProviderType,
    AIRiskLevel,
    AIAlertSeverity,
    AIAlertStatus,
    AIPredictionType,
    AIAlertType,
)
from app.core.security import get_password_hash
from app.core.logging import logger
from app.services.triage_service import TriageService
from app.services.lab_service import LabService

DEFAULT_PASSWORD = "Carex#2026"


def seed_database(db: Session):
    logger.info("Starting CAREX database initialization and seeding (Phases 1-4)...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # 1. Seed Roles
    roles_data = [
        {"name": RoleEnum.SUPER_ADMIN, "display_name": "Super Administrator", "description": "Global enterprise system control.", "permissions": ["*"]},
        {"name": RoleEnum.HOSPITAL_ADMIN, "display_name": "Hospital Administrator", "description": "Hospital operational oversight.", "permissions": ["*"]},
        {"name": RoleEnum.DOCTOR, "display_name": "Attending Physician / Doctor", "description": "Clinical care.", "permissions": ["patients:read", "patients:write", "labs:order", "prescriptions:write"]},
        {"name": RoleEnum.NURSE, "display_name": "Registered Nurse", "description": "Inpatient care.", "permissions": ["patients:read", "vitals:write"]},
        {"name": RoleEnum.RECEPTIONIST, "display_name": "Front Desk & Receptionist", "description": "Intake & booking.", "permissions": ["patients:register", "billing:write"]},
        {"name": RoleEnum.PHARMACIST, "display_name": "Clinical Pharmacist", "description": "Pharmacy dispensing & inventory.", "permissions": ["prescriptions:dispense", "inventory:write"]},
        {"name": RoleEnum.LAB_TECHNICIAN, "display_name": "Medical Laboratory Technician", "description": "Lab diagnostic tests.", "permissions": ["labs:report", "labs:verify"]},
        {"name": RoleEnum.PATIENT, "display_name": "Patient / Family Member", "description": "Personal health portal.", "permissions": ["patient_portal:read"]},
    ]

    roles_map = {}
    for r_info in roles_data:
        role = db.query(Role).filter(Role.name == r_info["name"]).first()
        if not role:
            role = Role(
                name=r_info["name"],
                display_name=r_info["display_name"],
                description=r_info["description"],
                permissions=r_info["permissions"],
            )
            db.add(role)
            db.commit()
            db.refresh(role)
        roles_map[r_info["name"]] = role

    # 2. Seed Departments
    departments_data = [
        {"name": "Emergency & Trauma", "code": "EMERGENCY", "description": "24/7 Level 1 Trauma Resuscitation Unit."},
        {"name": "Cardiology & Vascular", "code": "CARDIOLOGY", "description": "Interventional cardiology and CCU."},
        {"name": "Pediatrics & Neonatology", "code": "PEDIATRICS", "description": "Pediatric general care and NICU."},
        {"name": "Orthopedics & Joint Replacement", "code": "ORTHOPEDICS", "description": "Trauma surgery and arthroscopy."},
        {"name": "Pathology & Diagnostic Labs", "code": "PATHOLOGY", "description": "Clinical chemistry, hematology, and serology."},
        {"name": "Pharmacy & Therapeutics", "code": "PHARMACY", "description": "Central hospital pharmacy & sterile dispensing."},
        {"name": "Radiology & Diagnostic Imaging", "code": "RADIOLOGY", "description": "MRI, CT, ultrasound suites."},
        {"name": "General Outpatient Medicine", "code": "GEN_MED", "description": "Primary care consultations."},
    ]

    departments_map = {}
    for d_info in departments_data:
        dept = db.query(Department).filter(Department.code == d_info["code"]).first()
        if not dept:
            dept = Department(
                name=d_info["name"],
                code=d_info["code"],
                description=d_info["description"],
                is_active=True,
            )
            db.add(dept)
            db.commit()
            db.refresh(dept)
        departments_map[d_info["code"]] = dept

    # 3. Seed Demo Users
    hashed_pwd = get_password_hash(DEFAULT_PASSWORD)

    users_data = [
        {"email": "superadmin@carex.health", "full_name": "Devin Reynolds (Super Admin)", "role": RoleEnum.SUPER_ADMIN, "department": None, "phone": "+1-555-0100", "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"},
        {"email": "admin@carex.health", "full_name": "Dr. Eleanor Vance (Hospital Admin)", "role": RoleEnum.HOSPITAL_ADMIN, "department": "GEN_MED", "phone": "+1-555-0101", "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.sharma@carex.health", "full_name": "Dr. Rajesh Sharma, MD", "role": RoleEnum.DOCTOR, "department": "CARDIOLOGY", "phone": "+1-555-0102", "avatar_url": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.patel@carex.health", "full_name": "Dr. Priya Patel, MD", "role": RoleEnum.DOCTOR, "department": "EMERGENCY", "phone": "+1-555-0108", "avatar_url": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.lin@carex.health", "full_name": "Dr. Maya Lin, MD", "role": RoleEnum.DOCTOR, "department": "PEDIATRICS", "phone": "+1-555-0109", "avatar_url": "https://images.unsplash.com/photo-1594824813501-489e5a8f5f84?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.reed@carex.health", "full_name": "Dr. Alexander Reed, MD", "role": RoleEnum.DOCTOR, "department": "ORTHOPEDICS", "phone": "+1-555-0110", "avatar_url": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.thorne@carex.health", "full_name": "Dr. Aris Thorne, MD", "role": RoleEnum.DOCTOR, "department": "PATHOLOGY", "phone": "+1-555-0111", "avatar_url": "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.vance.pharm@carex.health", "full_name": "Dr. Marcus Vance, PharmD", "role": RoleEnum.DOCTOR, "department": "PHARMACY", "phone": "+1-555-0112", "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.wu@carex.health", "full_name": "Dr. Samantha Wu, MD", "role": RoleEnum.DOCTOR, "department": "RADIOLOGY", "phone": "+1-555-0113", "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80"},
        {"email": "dr.mehta@carex.health", "full_name": "Dr. Arjun Mehta, MD", "role": RoleEnum.DOCTOR, "department": "GEN_MED", "phone": "+1-555-0114", "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80"},
        {"email": "nurse.sarah@carex.health", "full_name": "Sarah Jenkins, RN", "role": RoleEnum.NURSE, "department": "EMERGENCY", "phone": "+1-555-0103", "avatar_url": "https://images.unsplash.com/photo-1594824813501-489e5a8f5f84?w=150&auto=format&fit=crop&q=80"},
        {"email": "reception@carex.health", "full_name": "Carlos Gomez", "role": RoleEnum.RECEPTIONIST, "department": "GEN_MED", "phone": "+1-555-0104", "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80"},
        {"email": "pharmacy@carex.health", "full_name": "David Kim, PharmD", "role": RoleEnum.PHARMACIST, "department": "PHARMACY", "phone": "+1-555-0105", "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80"},
        {"email": "lab@carex.health", "full_name": "Amanda Foster, MLS", "role": RoleEnum.LAB_TECHNICIAN, "department": "PATHOLOGY", "phone": "+1-555-0106", "avatar_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80"},
        {"email": "patient.john@carex.health", "full_name": "Johnathan Doe", "role": RoleEnum.PATIENT, "department": None, "phone": "+1-555-0107", "avatar_url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&auto=format&fit=crop&q=80"},
    ]

    users_map = {}
    for u_info in users_data:
        user = db.query(User).filter(User.email == u_info["email"]).first()
        dept_id = departments_map[u_info["department"]].id if u_info["department"] and u_info["department"] in departments_map else None
        role_id = roles_map[u_info["role"]].id

        if not user:
            user = User(
                email=u_info["email"],
                hashed_password=hashed_pwd,
                full_name=u_info["full_name"],
                phone=u_info["phone"],
                avatar_url=u_info["avatar_url"],
                role_id=role_id,
                department_id=dept_id,
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        users_map[u_info["email"]] = user

    # 4. Doctor Profiles for All Clinical Specialties
    doctors_seed_list = [
        {
            "email": "dr.sharma@carex.health",
            "dept_code": "CARDIOLOGY",
            "specialization": "Interventional & Clinical Cardiology",
            "qualification": "MBBS, MD, DM (Cardiology), FACC",
            "experience_years": 14,
            "consultation_fee": 120.0,
            "room_number": "OPD Block B, Suite 204",
        },
        {
            "email": "dr.patel@carex.health",
            "dept_code": "EMERGENCY",
            "specialization": "Emergency Medicine & Acute Trauma Resuscitation",
            "qualification": "MBBS, MD (Emergency Medicine), FACEP",
            "experience_years": 11,
            "consultation_fee": 110.0,
            "room_number": "Trauma Resuscitation Bay 1",
        },
        {
            "email": "dr.lin@carex.health",
            "dept_code": "PEDIATRICS",
            "specialization": "Pediatric Critical Care & Neonatology",
            "qualification": "MBBS, MD (Pediatrics), FAAP",
            "experience_years": 9,
            "consultation_fee": 95.0,
            "room_number": "Pediatric Pavilion Suite 102",
        },
        {
            "email": "dr.reed@carex.health",
            "dept_code": "ORTHOPEDICS",
            "specialization": "Orthopedic Surgery & Joint Reconstruction",
            "qualification": "MBBS, MS (Orthopedics), FAAOS",
            "experience_years": 16,
            "consultation_fee": 135.0,
            "room_number": "Ortho Surgical Wing Suite 305",
        },
        {
            "email": "dr.thorne@carex.health",
            "dept_code": "PATHOLOGY",
            "specialization": "Clinical Pathology & Molecular Diagnostics",
            "qualification": "MBBS, MD (Pathology), FCAP",
            "experience_years": 12,
            "consultation_fee": 85.0,
            "room_number": "Diagnostics Tower Suite 108",
        },
        {
            "email": "dr.vance.pharm@carex.health",
            "dept_code": "PHARMACY",
            "specialization": "Clinical Pharmacotherapy & Toxicology",
            "qualification": "PharmD, BCPS, Clinical Pharmacology",
            "experience_years": 8,
            "consultation_fee": 65.0,
            "room_number": "Pharmacy Consultation Suite 101",
        },
        {
            "email": "dr.wu@carex.health",
            "dept_code": "RADIOLOGY",
            "specialization": "Diagnostic Imaging & Interventional Radiology",
            "qualification": "MBBS, MD (Radiodiagnosis)",
            "experience_years": 10,
            "consultation_fee": 115.0,
            "room_number": "Imaging Wing Suite 201",
        },
        {
            "email": "dr.mehta@carex.health",
            "dept_code": "GEN_MED",
            "specialization": "Internal Medicine & Preventive Primary Care",
            "qualification": "MBBS, MD (General Medicine)",
            "experience_years": 13,
            "consultation_fee": 75.0,
            "room_number": "General OPD Suite 101",
        },
    ]

    for d_seed in doctors_seed_list:
        doc_u = users_map.get(d_seed["email"])
        if doc_u and d_seed["dept_code"] in departments_map:
            doc_p = db.query(DoctorProfile).filter(DoctorProfile.user_id == doc_u.id).first()
            if not doc_p:
                doc_p = DoctorProfile(
                    user_id=doc_u.id,
                    department_id=departments_map[d_seed["dept_code"]].id,
                    specialization=d_seed["specialization"],
                    qualification=d_seed["qualification"],
                    experience_years=d_seed["experience_years"],
                    consultation_fee=d_seed["consultation_fee"],
                    room_number=d_seed["room_number"],
                    availability_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    available_from="09:00",
                    available_to="17:00",
                    is_available=True,
                )
                db.add(doc_p)
                db.commit()

    doc_user = users_map.get("dr.sharma@carex.health")

    # 5. Nurse Profile
    nurse_user = users_map.get("nurse.sarah@carex.health")
    if nurse_user:
        nurse_prof = db.query(NurseProfile).filter(NurseProfile.user_id == nurse_user.id).first()
        if not nurse_prof:
            nurse_prof = NurseProfile(
                user_id=nurse_user.id,
                department_id=departments_map["EMERGENCY"].id,
                qualification="BSN, RN, Certified Emergency Nurse (CEN)",
                shift=ShiftEnum.MORNING,
                ward_assigned="Emergency Trauma Bay 1 & Ward 4B",
                is_on_duty=True,
            )
            db.add(nurse_prof)
            db.commit()

    # 6. Seed Patients (MPI)
    patient_user = users_map.get("patient.john@carex.health")
    patient_records = [
        {
            "mrn": "CRX-2026-0001",
            "first_name": "Johnathan",
            "last_name": "Doe",
            "email": "patient.john@carex.health",
            "phone": "+1-555-0107",
            "date_of_birth": datetime.date(1982, 5, 14),
            "gender": "Male",
            "blood_group": "O+",
            "address": "742 Evergreen Terrace, Springfield, OR",
            "emergency_contact_name": "Mary Doe",
            "emergency_contact_phone": "+1-555-0199",
            "emergency_contact_relation": "Spouse",
            "allergies": ["Penicillin", "Sulfa Drugs"],
            "current_medications": ["Atorvastatin 20mg OD", "Aspirin 81mg OD"],
            "medical_history": ["Hyperlipidemia (2021)", "Mild Hypertension"],
            "user_id": patient_user.id if patient_user else None,
        },
        {
            "mrn": "CRX-2026-0002",
            "first_name": "Elena",
            "last_name": "Rostova",
            "email": "elena.r@example.com",
            "phone": "+1-555-0244",
            "date_of_birth": datetime.date(1990, 8, 22),
            "gender": "Female",
            "blood_group": "A+",
            "address": "1204 Pine Valley Rd, Seattle, WA",
            "emergency_contact_name": "Dmitri Rostov",
            "emergency_contact_phone": "+1-555-0245",
            "emergency_contact_relation": "Brother",
            "allergies": ["Latex"],
            "current_medications": ["Ibuprofen 400mg PRN"],
            "medical_history": ["Knee Arthroscopy (2022)"],
            "user_id": None,
        },
        {
            "mrn": "CRX-2026-0003",
            "first_name": "Michael",
            "last_name": "Sterling",
            "email": "m.sterling@example.com",
            "phone": "+1-555-0388",
            "date_of_birth": datetime.date(1968, 11, 3),
            "gender": "Male",
            "blood_group": "B+",
            "address": "402 Grand Avenue, Chicago, IL",
            "emergency_contact_name": "Sarah Sterling",
            "emergency_contact_phone": "+1-555-0389",
            "emergency_contact_relation": "Wife",
            "allergies": ["Shellfish", "NSAIDs"],
            "current_medications": ["Metoprolol 50mg BD", "Lisinopril 10mg OD"],
            "medical_history": ["Coronary Artery Disease", "Type 2 Diabetes"],
            "user_id": None,
        },
        {
            "mrn": "CRX-2026-0004",
            "first_name": "Sophia",
            "last_name": "Chen",
            "email": "sophia.chen@example.com",
            "phone": "+1-555-0455",
            "date_of_birth": datetime.date(1995, 2, 18),
            "gender": "Female",
            "blood_group": "AB+",
            "address": "88 Horizon Blvd, San Francisco, CA",
            "emergency_contact_name": "Ken Chen",
            "emergency_contact_phone": "+1-555-0456",
            "emergency_contact_relation": "Father",
            "allergies": ["None"],
            "current_medications": ["Levothyroxine 50mcg OD"],
            "medical_history": ["Hypothyroidism (2023)"],
            "user_id": None,
        },
        {
            "mrn": "CRX-2026-0005",
            "first_name": "Robert",
            "last_name": "Taylor",
            "email": "r.taylor@example.com",
            "phone": "+1-555-0577",
            "date_of_birth": datetime.date(1955, 9, 30),
            "gender": "Male",
            "blood_group": "O-",
            "address": "512 Oakwood Dr, Austin, TX",
            "emergency_contact_name": "Grace Taylor",
            "emergency_contact_phone": "+1-555-0578",
            "emergency_contact_relation": "Daughter",
            "allergies": ["Ciprofloxacin"],
            "current_medications": ["Amlodipine 5mg OD", "Metformin 1000mg BD"],
            "medical_history": ["Hypertension", "Diabetic Nephropathy Stage 2"],
            "user_id": None,
        },
    ]

    patients_map = {}
    for p_info in patient_records:
        pat = db.query(Patient).filter(Patient.mrn == p_info["mrn"]).first()
        if not pat:
            pat = Patient(
                mrn=p_info["mrn"],
                first_name=p_info["first_name"],
                last_name=p_info["last_name"],
                email=p_info["email"],
                phone=p_info["phone"],
                date_of_birth=p_info["date_of_birth"],
                gender=p_info["gender"],
                blood_group=p_info["blood_group"],
                address=p_info["address"],
                emergency_contact_name=p_info["emergency_contact_name"],
                emergency_contact_phone=p_info["emergency_contact_phone"],
                emergency_contact_relation=p_info["emergency_contact_relation"],
                allergies=p_info["allergies"],
                current_medications=p_info["current_medications"],
                medical_history=p_info["medical_history"],
                user_id=p_info["user_id"],
                registered_by_id=users_map["reception@carex.health"].id if "reception@carex.health" in users_map else None,
            )
            db.add(pat)
            db.commit()
            db.refresh(pat)
        patients_map[p_info["mrn"]] = pat

    # 7. Seed Wards, Rooms, Beds (Phase 3)
    wards_data = [
        {"code": "ICU", "name": "Intensive Care Unit (ICU)", "floor": "Floor 3", "wing": "Wing A", "total": 6},
        {"code": "CCU", "name": "Coronary Care Unit (CCU)", "floor": "Floor 3", "wing": "Wing B", "total": 6},
        {"code": "TRAUMA", "name": "Emergency Trauma Resuscitation", "floor": "Floor 1", "wing": "Wing Ground", "total": 6},
        {"code": "GEN_SURG", "name": "General Surgery Ward", "floor": "Floor 4", "wing": "Wing C", "total": 8},
        {"code": "PEDIATRICS", "name": "Pediatrics Inpatient Ward", "floor": "Floor 2", "wing": "Wing D", "total": 6},
        {"code": "ORTHOPEDICS", "name": "Orthopedics Inpatient Ward", "floor": "Floor 4", "wing": "Wing B", "total": 6},
        {"code": "MATERNITY", "name": "Maternity & OB/GYN Ward", "floor": "Floor 2", "wing": "Wing A", "total": 6},
    ]

    wards_map = {}
    for w_info in wards_data:
        ward = db.query(Ward).filter(Ward.code == w_info["code"]).first()
        if not ward:
            ward = Ward(
                code=w_info["code"],
                name=w_info["name"],
                floor=w_info["floor"],
                wing=w_info["wing"],
                total_beds=w_info["total"],
                is_active=True,
            )
            db.add(ward)
            db.commit()
            db.refresh(ward)
        wards_map[w_info["code"]] = ward

        room = db.query(Room).filter(Room.ward_id == ward.id).first()
        if not room:
            room = Room(
                room_number=f"{ward.code}-101",
                ward_id=ward.id,
                room_type=RoomType.ICU if ward.code in ["ICU", "CCU", "TRAUMA"] else RoomType.GENERAL_WARD,
                has_oxygen_support=True,
                daily_rate=350.0 if ward.code in ["ICU", "CCU"] else 150.0,
            )
            db.add(room)
            db.commit()
            db.refresh(room)

        existing_beds = db.query(Bed).filter(Bed.ward_id == ward.id).count()
        if existing_beds == 0:
            for b_idx in range(1, w_info["total"] + 1):
                bed_num = f"{w_info['code']}-{b_idx:02d}"
                init_status = BedStatus.AVAILABLE
                if b_idx == 1 and w_info["code"] in ["ICU", "CCU", "GEN_SURG"]:
                    init_status = BedStatus.OCCUPIED
                elif b_idx == 2 and w_info["code"] == "TRAUMA":
                    init_status = BedStatus.CLEANING

                bed = Bed(
                    bed_number=bed_num,
                    ward_id=ward.id,
                    room_id=room.id,
                    status=init_status,
                    has_oxygen_support=True,
                    has_ventilator=(w_info["code"] in ["ICU", "TRAUMA"]),
                )
                db.add(bed)
                db.commit()

    # 8. Seed Emergency Cases
    if db.query(EmergencyCase).count() == 0:
        now_time = datetime.datetime.now(datetime.timezone.utc)
        er_samples = [
            {
                "num": "EMR-2026-0001",
                "pat_name": "Michael Sterling",
                "age": 58,
                "gender": "Male",
                "symptoms": "Severe substernal crushing chest pain, diaphoresis, shortness of breath",
                "injury": "Suspected Acute STEMI / Coronary Event",
                "hr": 144,
                "sys": 82,
                "dia": 54,
                "spo2": 88.5,
                "temp": 37.2,
                "rr": 32,
                "conscious": ConsciousnessLevel.ALERT,
            },
            {
                "num": "EMR-2026-0002",
                "pat_name": "Elena Rostova",
                "age": 34,
                "gender": "Female",
                "symptoms": "High-speed motorcycle collision, deformed right lower extremity, intense pain",
                "injury": "Severe Compound Femur Fracture, active bleeding",
                "hr": 126,
                "sys": 105,
                "dia": 68,
                "spo2": 95.0,
                "temp": 36.8,
                "rr": 26,
                "conscious": ConsciousnessLevel.VOICE,
            },
        ]
        for s in er_samples:
            eval_res = TriageService.evaluate_triage(
                heart_rate=s["hr"],
                bp_systolic=s["sys"],
                bp_diastolic=s["dia"],
                spo2=s["spo2"],
                temperature=s["temp"],
                respiratory_rate=s["rr"],
                consciousness=s["conscious"],
                injury_type=s["injury"],
                symptoms=s["symptoms"],
            )
            ec = EmergencyCase(
                case_number=s["num"],
                patient_name=s["pat_name"],
                age=s["age"],
                gender=s["gender"],
                arrival_time=now_time - datetime.timedelta(minutes=15),
                symptoms=s["symptoms"],
                injury_type=s["injury"],
                heart_rate=s["hr"],
                bp_systolic=s["sys"],
                bp_diastolic=s["dia"],
                spo2=s["spo2"],
                temperature=s["temp"],
                respiratory_rate=s["rr"],
                consciousness=s["conscious"],
                triage_level=eval_res.triage_level,
                contributing_factors=eval_res.contributing_factors,
                recommended_action=eval_res.recommended_action,
                status=EmergencyCaseStatus.TRIAGED,
                doctor_id=doc_user.id if doc_user else None,
                nurse_id=nurse_user.id if nurse_user else None,
            )
            db.add(ec)
            db.commit()

    # 9. Seed Active Admission
    if db.query(Admission).count() == 0 and doc_user:
        ccu_bed = db.query(Bed).filter(Bed.bed_number == "CCU-01").first()
        if ccu_bed:
            adm = Admission(
                admission_number="ADM-2026-0001",
                patient_id=patients_map["CRX-2026-0001"].id,
                admitting_doctor_id=doc_user.id,
                ward_id=ccu_bed.ward_id,
                bed_id=ccu_bed.id,
                admission_date=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2),
                admission_reason="Post-percutaneous coronary intervention (PCI) monitoring and titration",
                expected_stay_days=3,
                status=AdmissionStatus.ADMITTED,
            )
            db.add(adm)
            db.flush()
            ccu_bed.status = BedStatus.OCCUPIED
            ccu_bed.current_admission_id = adm.id
            db.commit()

    # ==========================================
    # PHASE 4: 10. SEED LABORATORY CATALOGUE & TESTS
    # ==========================================
    lab_tests_data = [
        {
            "code": "CBC",
            "name": "Complete Blood Count (CBC with Differential)",
            "category": "Hematology",
            "sample_type": "Whole Blood (EDTA)",
            "price": 35.0,
            "description": "Full analysis of red blood cells, white blood cells, platelets, and automated differential.",
            "parameters": [
                {"name": "Hemoglobin (Hb)", "unit": "g/dL", "min_val": 13.5, "max_val": 17.5, "critical_low": 7.0, "critical_high": 20.0},
                {"name": "Total Leukocyte Count (WBC)", "unit": "10^3/uL", "min_val": 4.5, "max_val": 11.0, "critical_low": 2.0, "critical_high": 30.0},
                {"name": "Platelet Count", "unit": "10^3/uL", "min_val": 150.0, "max_val": 450.0, "critical_low": 50.0, "critical_high": 1000.0},
                {"name": "Hematocrit (PCV)", "unit": "%", "min_val": 40.0, "max_val": 52.0, "critical_low": 20.0, "critical_high": 60.0},
                {"name": "Neutrophils", "unit": "%", "min_val": 40.0, "max_val": 75.0},
                {"name": "Lymphocytes", "unit": "%", "min_val": 20.0, "max_val": 45.0},
            ],
        },
        {
            "code": "TROP_I",
            "name": "High-Sensitivity Cardiac Troponin I (hs-cTnI)",
            "category": "Cardiac Markers",
            "sample_type": "Serum (SST)",
            "price": 65.0,
            "description": "STAT diagnostic marker for myocardial infarction and acute coronary syndrome.",
            "parameters": [
                {"name": "Cardiac Troponin I", "unit": "ng/mL", "min_val": 0.0, "max_val": 0.04, "critical_high": 0.10},
            ],
        },
        {
            "code": "GLU_F",
            "name": "Fasting Plasma Glucose (FBS)",
            "category": "Biochemistry",
            "sample_type": "Fluoride Plasma",
            "price": 20.0,
            "description": "Fasting blood sugar estimation for diabetes screening and glycemic control.",
            "parameters": [
                {"name": "Fasting Glucose", "unit": "mg/dL", "min_val": 70.0, "max_val": 99.0, "critical_low": 50.0, "critical_high": 350.0},
            ],
        },
        {
            "code": "HBA1C",
            "name": "Glycated Hemoglobin (HbA1c)",
            "category": "Biochemistry",
            "sample_type": "Whole Blood (EDTA)",
            "price": 45.0,
            "description": "3-month average glycemic index assessment.",
            "parameters": [
                {"name": "HbA1c", "unit": "%", "min_val": 4.0, "max_val": 5.6, "critical_high": 12.0},
            ],
        },
        {
            "code": "LIPID_PANEL",
            "name": "Comprehensive Lipid Profile",
            "category": "Biochemistry",
            "sample_type": "Serum (SST)",
            "price": 55.0,
            "description": "Total cholesterol, triglycerides, HDL, LDL, and VLDL assessment.",
            "parameters": [
                {"name": "Total Cholesterol", "unit": "mg/dL", "min_val": 125.0, "max_val": 200.0, "critical_high": 300.0},
                {"name": "Triglycerides", "unit": "mg/dL", "min_val": 50.0, "max_val": 150.0, "critical_high": 500.0},
                {"name": "HDL Cholesterol (Good)", "unit": "mg/dL", "min_val": 40.0, "max_val": 60.0},
                {"name": "LDL Cholesterol (Calculated)", "unit": "mg/dL", "min_val": 50.0, "max_val": 100.0, "critical_high": 190.0},
            ],
        },
        {
            "code": "LFT",
            "name": "Liver Function Tests (LFT)",
            "category": "Biochemistry",
            "sample_type": "Serum (SST)",
            "price": 60.0,
            "description": "Hepatic enzyme panel: Bilirubin, SGOT/AST, SGPT/ALT, Alkaline Phosphatase, Total Protein, Albumin.",
            "parameters": [
                {"name": "Total Bilirubin", "unit": "mg/dL", "min_val": 0.2, "max_val": 1.2, "critical_high": 15.0},
                {"name": "Direct Bilirubin", "unit": "mg/dL", "min_val": 0.0, "max_val": 0.3},
                {"name": "SGOT / AST", "unit": "U/L", "min_val": 10.0, "max_val": 40.0, "critical_high": 500.0},
                {"name": "SGPT / ALT", "unit": "U/L", "min_val": 7.0, "max_val": 56.0, "critical_high": 500.0},
                {"name": "Alkaline Phosphatase (ALP)", "unit": "U/L", "min_val": 44.0, "max_val": 147.0},
                {"name": "Serum Albumin", "unit": "g/dL", "min_val": 3.5, "max_val": 5.0, "critical_low": 2.0},
            ],
        },
        {
            "code": "KFT",
            "name": "Kidney Function Tests (KFT / RFT)",
            "category": "Biochemistry",
            "sample_type": "Serum (SST)",
            "price": 50.0,
            "description": "Renal panel: Urea, BUN, Creatinine, Uric Acid, eGFR.",
            "parameters": [
                {"name": "Serum Creatinine", "unit": "mg/dL", "min_val": 0.7, "max_val": 1.3, "critical_high": 5.0},
                {"name": "Blood Urea Nitrogen (BUN)", "unit": "mg/dL", "min_val": 7.0, "max_val": 20.0, "critical_high": 100.0},
                {"name": "Serum Uric Acid", "unit": "mg/dL", "min_val": 3.5, "max_val": 7.2},
                {"name": "Estimated GFR", "unit": "mL/min/1.73m2", "min_val": 90.0, "max_val": 120.0, "critical_low": 15.0},
            ],
        },
        {
            "code": "ELECTROLYTES",
            "name": "Serum Electrolytes Panel (Na+, K+, Cl-)",
            "category": "Biochemistry",
            "sample_type": "Serum (SST)",
            "price": 40.0,
            "description": "Electrolyte and fluid balance assessment.",
            "parameters": [
                {"name": "Sodium (Na+)", "unit": "mmol/L", "min_val": 135.0, "max_val": 145.0, "critical_low": 120.0, "critical_high": 160.0},
                {"name": "Potassium (K+)", "unit": "mmol/L", "min_val": 3.5, "max_val": 5.1, "critical_low": 2.8, "critical_high": 6.5},
                {"name": "Chloride (Cl-)", "unit": "mmol/L", "min_val": 96.0, "max_val": 106.0},
            ],
        },
        {
            "code": "THYROID",
            "name": "Thyroid Profile (Total T3, T4, TSH)",
            "category": "Endocrinology",
            "sample_type": "Serum (SST)",
            "price": 60.0,
            "description": "Thyroid hormone function panel.",
            "parameters": [
                {"name": "TSH (Ultrasensitive)", "unit": "uIU/mL", "min_val": 0.4, "max_val": 4.5, "critical_high": 30.0},
                {"name": "Total T3", "unit": "ng/dL", "min_val": 80.0, "max_val": 200.0},
                {"name": "Total T4", "unit": "ug/dL", "min_val": 5.0, "max_val": 12.0},
            ],
        },
        {
            "code": "URINE_RE",
            "name": "Urine Routine & Microscopic Examination",
            "category": "Urinalysis",
            "sample_type": "Midstream Clean Catch Urine",
            "price": 25.0,
            "description": "Physical, chemical, and microscopic examination of urine sample.",
            "parameters": [
                {"name": "Urine Specific Gravity", "unit": "", "min_val": 1.005, "max_val": 1.030},
                {"name": "pH", "unit": "", "min_val": 5.0, "max_val": 7.5},
                {"name": "Protein / Albumin", "unit": "", "min_val": 0.0, "max_val": 0.0, "text_range": "Negative"},
                {"name": "Glucose", "unit": "", "min_val": 0.0, "max_val": 0.0, "text_range": "Negative"},
                {"name": "Pus Cells (WBC)", "unit": "/HPF", "min_val": 0.0, "max_val": 5.0, "critical_high": 50.0},
                {"name": "RBCs", "unit": "/HPF", "min_val": 0.0, "max_val": 2.0, "critical_high": 25.0},
            ],
        },
        {
            "code": "COAG_PT",
            "name": "Prothrombin Time & INR (PT/INR)",
            "category": "Hematology",
            "sample_type": "Sodium Citrate Blood",
            "price": 30.0,
            "description": "Extrinsic coagulation pathway and oral anticoagulant monitoring.",
            "parameters": [
                {"name": "Prothrombin Time (Patient)", "unit": "seconds", "min_val": 11.0, "max_val": 14.5, "critical_high": 30.0},
                {"name": "INR", "unit": "ratio", "min_val": 0.9, "max_val": 1.2, "critical_high": 4.5},
            ],
        },
        {
            "code": "ABG",
            "name": "Arterial Blood Gas (ABG)",
            "category": "Critical Care",
            "sample_type": "Heparinized Arterial Blood",
            "price": 75.0,
            "description": "STAT oxygenation, ventilation, and acid-base status for critical emergencies.",
            "parameters": [
                {"name": "pH", "unit": "", "min_val": 7.35, "max_val": 7.45, "critical_low": 7.15, "critical_high": 7.60},
                {"name": "PaCO2", "unit": "mmHg", "min_val": 35.0, "max_val": 45.0, "critical_low": 20.0, "critical_high": 70.0},
                {"name": "PaO2", "unit": "mmHg", "min_val": 80.0, "max_val": 100.0, "critical_low": 50.0},
                {"name": "HCO3- (Bicarbonate)", "unit": "mmol/L", "min_val": 22.0, "max_val": 26.0, "critical_low": 10.0, "critical_high": 40.0},
                {"name": "Oxygen Saturation (SaO2)", "unit": "%", "min_val": 95.0, "max_val": 100.0, "critical_low": 85.0},
            ],
        },
        {
            "code": "CRP_QUANT",
            "name": "C-Reactive Protein (Quantitative CRP)",
            "category": "Serology & Immunology",
            "sample_type": "Serum (SST)",
            "price": 35.0,
            "description": "Systemic inflammatory acute phase reactant marker.",
            "parameters": [
                {"name": "C-Reactive Protein", "unit": "mg/L", "min_val": 0.0, "max_val": 5.0, "critical_high": 100.0},
            ],
        },
        {
            "code": "D_DIMER",
            "name": "D-Dimer Quantitative Assay",
            "category": "Hematology",
            "sample_type": "Citrated Plasma",
            "price": 60.0,
            "description": "Fibrin degradation product assessment for DVT and pulmonary embolism rule-out.",
            "parameters": [
                {"name": "D-Dimer", "unit": "ng/mL FEU", "min_val": 0.0, "max_val": 500.0, "critical_high": 2000.0},
            ],
        },
        {
            "code": "VIT_D3",
            "name": "Vitamin D 25-Hydroxy (Total D2 + D3)",
            "category": "Endocrinology",
            "sample_type": "Serum (SST)",
            "price": 55.0,
            "description": "Serum 25-hydroxyvitamin D measurement for bone and metabolic health.",
            "parameters": [
                {"name": "25-OH Vitamin D Total", "unit": "ng/mL", "min_val": 30.0, "max_val": 100.0, "critical_low": 10.0},
            ],
        },
        {
            "code": "FERRITIN",
            "name": "Serum Ferritin Level",
            "category": "Hematology",
            "sample_type": "Serum (SST)",
            "price": 40.0,
            "description": "Total body iron storage and inflammatory marker.",
            "parameters": [
                {"name": "Ferritin", "unit": "ng/mL", "min_val": 20.0, "max_val": 250.0, "critical_low": 10.0, "critical_high": 1000.0},
            ],
        },
        {
            "code": "COVID_PCR",
            "name": "SARS-CoV-2 (COVID-19) RT-PCR",
            "category": "Molecular Diagnostics",
            "sample_type": "Nasopharyngeal Swab in VTM",
            "price": 50.0,
            "description": "Real-time RT-PCR qualitative detection of viral RNA.",
            "parameters": [
                {"name": "SARS-CoV-2 Viral RNA", "unit": "", "min_val": 0.0, "max_val": 0.0, "text_range": "Not Detected / Negative"},
            ],
        },
        {
            "code": "DENGUE_NS1",
            "name": "Dengue Duo Panel (NS1 Antigen + IgM/IgG Antibodies)",
            "category": "Serology & Immunology",
            "sample_type": "Serum (SST)",
            "price": 45.0,
            "description": "Rapid immunochromatographic assay for acute dengue viremia.",
            "parameters": [
                {"name": "Dengue NS1 Antigen", "unit": "", "min_val": 0.0, "max_val": 0.0, "text_range": "Negative"},
                {"name": "Dengue IgM Antibody", "unit": "", "min_val": 0.0, "max_val": 0.0, "text_range": "Negative"},
                {"name": "Dengue IgG Antibody", "unit": "", "min_val": 0.0, "max_val": 0.0, "text_range": "Negative"},
            ],
        },
        {
            "code": "BLOOD_CULTURE",
            "name": "Automated Blood Culture & Sensitivity (Aerobic)",
            "category": "Microbiology",
            "sample_type": "Whole Blood in BACTEC Bottle",
            "price": 80.0,
            "description": "Continuous automated monitoring for bacteremia and sepsis pathogens.",
            "parameters": [
                {"name": "Growth after 5 Days", "unit": "", "min_val": 0.0, "max_val": 0.0, "text_range": "No Growth (Sterile)"},
            ],
        },
        {
            "code": "SERUM_CALCIUM",
            "name": "Serum Total & Ionized Calcium",
            "category": "Biochemistry",
            "sample_type": "Serum (SST)",
            "price": 25.0,
            "description": "Bone metabolism, neuromuscular excitability, and parathyroid screening.",
            "parameters": [
                {"name": "Total Serum Calcium", "unit": "mg/dL", "min_val": 8.5, "max_val": 10.2, "critical_low": 6.5, "critical_high": 13.0},
            ],
        },
    ]

    lab_tests_map = {}
    pathology_dept = departments_map.get("PATHOLOGY")
    for t_info in lab_tests_data:
        test = db.query(LabTest).filter(LabTest.code == t_info["code"]).first()
        if not test:
            test = LabTest(
                code=t_info["code"],
                name=t_info["name"],
                category=t_info["category"],
                department_id=pathology_dept.id if pathology_dept else None,
                description=t_info["description"],
                sample_type=t_info["sample_type"],
                price=t_info["price"],
                is_active=True,
                parameters=t_info["parameters"],
            )
            db.add(test)
            db.commit()
            db.refresh(test)
        lab_tests_map[t_info["code"]] = test

    # Seed 100+ Lab Orders with intentional demo scenarios
    lab_tech_user = users_map.get("lab@carex.health")
    if db.query(LabOrder).count() == 0 and doc_user and lab_tech_user:
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        patient_list = list(patients_map.values())
        test_keys = list(lab_tests_map.keys())

        # Intentional Scenario 3: STAT Troponin I for Michael Sterling (Emergency)
        emr_case = db.query(EmergencyCase).filter(EmergencyCase.case_number == "EMR-2026-0001").first()
        stat_order = LabOrder(
            order_number="LAB-2026-0001",
            patient_id=patients_map["CRX-2026-0003"].id,
            doctor_id=doc_user.id,
            test_id=lab_tests_map["TROP_I"].id,
            emergency_case_id=emr_case.id if emr_case else None,
            priority=LabOrderPriority.STAT,
            status=LabOrderStatus.IN_PROGRESS,
            clinical_notes="Acute crushing chest pain with ST changes. STAT hs-cTnI required immediately.",
            sample_type="Serum (SST)",
            order_date=now_dt - datetime.timedelta(minutes=20),
            sample_collected_at=now_dt - datetime.timedelta(minutes=10),
            collected_by_id=nurse_user.id if nurse_user else lab_tech_user.id,
            performed_by_id=lab_tech_user.id,
        )
        db.add(stat_order)

        # Intentional Scenario 5: Completed & Verified CBC with flagged WBC & Hb for Elena Rostova
        elena_pat = patients_map["CRX-2026-0002"]
        cbc_order = LabOrder(
            order_number="LAB-2026-0002",
            patient_id=elena_pat.id,
            doctor_id=doc_user.id,
            test_id=lab_tests_map["CBC"].id,
            priority=LabOrderPriority.URGENT,
            status=LabOrderStatus.VERIFIED,
            clinical_notes="Pre-operative trauma assessment following fracture reduction.",
            sample_type="Whole Blood (EDTA)",
            order_date=now_dt - datetime.timedelta(hours=4),
            sample_collected_at=now_dt - datetime.timedelta(hours=3, minutes=30),
            completed_at=now_dt - datetime.timedelta(hours=2),
            verified_at=now_dt - datetime.timedelta(hours=1),
            collected_by_id=lab_tech_user.id,
            performed_by_id=lab_tech_user.id,
            verified_by_id=doc_user.id,
        )
        db.add(cbc_order)
        db.flush()

        cbc_res = LabResult(
            order_id=cbc_order.id,
            patient_id=elena_pat.id,
            technician_id=lab_tech_user.id,
            result_summary="Elevated white blood cell count indicative of acute inflammatory response post-trauma; mild microcytic anemia.",
            technician_notes="Specimen analyzed on Sysmex XN-1000 automated analyzer. Internal QC valid.",
            is_abnormal=True,
            is_critical=False,
            created_at=now_dt - datetime.timedelta(hours=2),
        )
        db.add(cbc_res)
        db.flush()

        # Add CBC parameters with flags
        cbc_params = [
            {"name": "Hemoglobin (Hb)", "val": "10.4", "num": 10.4, "unit": "g/dL", "ref": "13.5 - 17.5", "flag": LabResultFlag.LOW},
            {"name": "Total Leukocyte Count (WBC)", "val": "13.8", "num": 13.8, "unit": "10^3/uL", "ref": "4.5 - 11.0", "flag": LabResultFlag.HIGH},
            {"name": "Platelet Count", "val": "280.0", "num": 280.0, "unit": "10^3/uL", "ref": "150.0 - 450.0", "flag": LabResultFlag.NORMAL},
            {"name": "Hematocrit (PCV)", "val": "32.1", "num": 32.1, "unit": "%", "ref": "40.0 - 52.0", "flag": LabResultFlag.LOW},
            {"name": "Neutrophils", "val": "82.0", "num": 82.0, "unit": "%", "ref": "40.0 - 75.0", "flag": LabResultFlag.HIGH},
            {"name": "Lymphocytes", "val": "14.0", "num": 14.0, "unit": "%", "ref": "20.0 - 45.0", "flag": LabResultFlag.LOW},
        ]
        for cp in cbc_params:
            db.add(LabResultParameter(
                lab_result_id=cbc_res.id,
                parameter_name=cp["name"],
                result_value=cp["val"],
                numeric_value=cp["num"],
                unit=cp["unit"],
                reference_range=cp["ref"],
                flag=cp["flag"],
                is_critical=False,
            ))

        # Verified Report
        cbc_report = LabReport(
            report_number="RPT-2026-0001",
            order_id=cbc_order.id,
            lab_result_id=cbc_res.id,
            patient_id=elena_pat.id,
            doctor_id=doc_user.id,
            technician_id=lab_tech_user.id,
            verified_by_id=doc_user.id,
            report_date=now_dt - datetime.timedelta(hours=1),
            status=LabReportStatus.RELEASED,
            clinical_impression="Neutrophilic leukocytosis consistent with traumatic tissue injury; mild normocytic anemia.",
            conclusion="Results verified and released to attending clinical team.",
        )
        db.add(cbc_report)

        # Seed additional orders to exceed 100+ total orders
        order_idx = 3
        statuses = [LabOrderStatus.VERIFIED, LabOrderStatus.COMPLETED, LabOrderStatus.IN_PROGRESS, LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.PENDING]
        priorities = [LabOrderPriority.NORMAL, LabOrderPriority.NORMAL, LabOrderPriority.URGENT, LabOrderPriority.STAT]

        for i in range(3, 108):
            pat = random.choice(patient_list)
            t_key = random.choice(test_keys)
            test_obj = lab_tests_map[t_key]
            ord_status = random.choice(statuses)
            ord_prio = random.choice(priorities)
            time_offset = datetime.timedelta(days=random.randint(0, 14), hours=random.randint(0, 23), minutes=random.randint(0, 59))

            ord_obj = LabOrder(
                order_number=f"LAB-2026-{i:04d}",
                patient_id=pat.id,
                doctor_id=doc_user.id,
                test_id=test_obj.id,
                priority=ord_prio,
                status=ord_status,
                clinical_notes=f"Routine diagnostic evaluation for {test_obj.name}.",
                sample_type=test_obj.sample_type,
                order_date=now_dt - time_offset,
                sample_collected_at=(now_dt - time_offset + datetime.timedelta(minutes=30)) if ord_status != LabOrderStatus.PENDING else None,
                completed_at=(now_dt - time_offset + datetime.timedelta(hours=2)) if ord_status in [LabOrderStatus.COMPLETED, LabOrderStatus.VERIFIED] else None,
                verified_at=(now_dt - time_offset + datetime.timedelta(hours=3)) if ord_status == LabOrderStatus.VERIFIED else None,
                collected_by_id=lab_tech_user.id if ord_status != LabOrderStatus.PENDING else None,
                performed_by_id=lab_tech_user.id if ord_status in [LabOrderStatus.IN_PROGRESS, LabOrderStatus.COMPLETED, LabOrderStatus.VERIFIED] else None,
                verified_by_id=doc_user.id if ord_status == LabOrderStatus.VERIFIED else None,
            )
            db.add(ord_obj)
            db.flush()

            if ord_status in [LabOrderStatus.COMPLETED, LabOrderStatus.VERIFIED]:
                res_obj = LabResult(
                    order_id=ord_obj.id,
                    patient_id=pat.id,
                    technician_id=lab_tech_user.id,
                    result_summary=f"Automated analysis completed for {test_obj.name}.",
                    technician_notes="All calibrations within +/- 2 SD.",
                    is_abnormal=False,
                    is_critical=False,
                    created_at=now_dt - time_offset + datetime.timedelta(hours=2),
                )
                db.add(res_obj)
                db.flush()

                # Add parameter values
                for p_def in (test_obj.parameters or []):
                    min_v = p_def.get("min_val", 10.0)
                    max_v = p_def.get("max_val", 20.0)
                    if min_v is not None and max_v is not None:
                        val_num = round(random.uniform(min_v, max_v), 2)
                        val_str = str(val_num)
                    else:
                        val_str = p_def.get("text_range", "Normal")
                        val_num = None

                    db.add(LabResultParameter(
                        lab_result_id=res_obj.id,
                        parameter_name=p_def.get("name", "Parameter"),
                        result_value=val_str,
                        numeric_value=val_num,
                        unit=p_def.get("unit"),
                        reference_range=f"{min_v} - {max_v}" if min_v and max_v else p_def.get("text_range"),
                        flag=LabResultFlag.NORMAL,
                        is_critical=False,
                    ))

                if ord_status == LabOrderStatus.VERIFIED:
                    db.add(LabReport(
                        report_number=f"RPT-2026-{i:04d}",
                        order_id=ord_obj.id,
                        lab_result_id=res_obj.id,
                        patient_id=pat.id,
                        doctor_id=doc_user.id,
                        technician_id=lab_tech_user.id,
                        verified_by_id=doc_user.id,
                        report_date=now_dt - time_offset + datetime.timedelta(hours=3),
                        status=LabReportStatus.RELEASED,
                        clinical_impression="Report verified and electronically authorized.",
                        conclusion="Normal diagnostic findings.",
                    ))

        db.commit()

    # ==========================================
    # PHASE 4: 11. SEED PHARMACY MEDICINES & BATCHES
    # ==========================================
    medicines_data = [
        # Cardiovascular
        {"code": "MED-001", "name": "Atorvastatin 20mg", "generic_name": "Atorvastatin Calcium", "category": "Cardiovascular", "unit": "Tablets", "reorder": 40, "max": 400, "price": 1.20, "mfg": "Pfizer / Viatris"},
        {"code": "MED-002", "name": "Aspirin 81mg (E.C.)", "generic_name": "Acetylsalicylic Acid", "category": "Cardiovascular", "unit": "Tablets", "reorder": 50, "max": 500, "price": 0.40, "mfg": "Bayer"},
        {"code": "MED-003", "name": "Clopidogrel 75mg", "generic_name": "Clopidogrel Bisulfate", "category": "Cardiovascular", "unit": "Tablets", "reorder": 30, "max": 300, "price": 1.80, "mfg": "Sanofi"},
        {"code": "MED-004", "name": "Metoprolol Succinate 50mg (ER)", "generic_name": "Metoprolol Succinate", "category": "Cardiovascular", "unit": "Tablets", "reorder": 40, "max": 350, "price": 1.10, "mfg": "AstraZeneca"},
        {"code": "MED-005", "name": "Lisinopril 10mg", "generic_name": "Lisinopril Dihydrate", "category": "Cardiovascular", "unit": "Tablets", "reorder": 35, "max": 300, "price": 0.65, "mfg": "Novartis"},
        {"code": "MED-006", "name": "Amlodipine Besylate 5mg", "generic_name": "Amlodipine Besylate", "category": "Cardiovascular", "unit": "Tablets", "reorder": 45, "max": 400, "price": 0.50, "mfg": "Pfizer"},
        {"code": "MED-007", "name": "Nitroglycerin 0.4mg Sublingual", "generic_name": "Glyceryl Trinitrate", "category": "Cardiovascular", "unit": "Tablets", "reorder": 20, "max": 150, "price": 2.50, "mfg": "Sun Pharma"},
        {"code": "MED-008", "name": "Heparin Sodium 5,000 IU/mL", "generic_name": "Heparin Sodium Injection", "category": "Cardiovascular", "unit": "Vials", "reorder": 25, "max": 200, "price": 18.00, "mfg": "Fresenius Kabi"},

        # Antibiotics & Anti-Infectives
        {"code": "MED-009", "name": "Azithromycin 500mg", "generic_name": "Azithromycin Dihydrate", "category": "Antibiotics", "unit": "Tablets", "reorder": 30, "max": 250, "price": 2.80, "mfg": "Cipla"},  # Scenario 1: Low stock
        {"code": "MED-010", "name": "Amoxicillin-Clavulanate 625mg", "generic_name": "Amoxicillin + Clavulanic Acid", "category": "Antibiotics", "unit": "Tablets", "reorder": 40, "max": 300, "price": 3.20, "mfg": "GSK"},  # Scenario 2: Expiring in 5 days
        {"code": "MED-011", "name": "Ceftriaxone 1g IV Injection", "generic_name": "Ceftriaxone Sodium", "category": "Antibiotics", "unit": "Vials", "reorder": 30, "max": 300, "price": 8.50, "mfg": "Roche"},
        {"code": "MED-012", "name": "Ciprofloxacin 500mg", "generic_name": "Ciprofloxacin HCl", "category": "Antibiotics", "unit": "Tablets", "reorder": 35, "max": 300, "price": 1.40, "mfg": "Bayer"},
        {"code": "MED-013", "name": "Levofloxacin 500mg", "generic_name": "Levofloxacin Hemihydrate", "category": "Antibiotics", "unit": "Tablets", "reorder": 25, "max": 200, "price": 2.10, "mfg": "Sanofi"},
        {"code": "MED-014", "name": "Meropenem 1g IV", "generic_name": "Meropenem Trihydrate", "category": "Antibiotics", "unit": "Vials", "reorder": 15, "max": 100, "price": 32.00, "mfg": "AstraZeneca"},
        {"code": "MED-015", "name": "Vancomycin 500mg IV", "generic_name": "Vancomycin Hydrochloride", "category": "Antibiotics", "unit": "Vials", "reorder": 15, "max": 120, "price": 24.00, "mfg": "Eli Lilly"},

        # Analgesics & Anti-Inflammatory
        {"code": "MED-016", "name": "Paracetamol 650mg (Acetaminophen)", "generic_name": "Paracetamol", "category": "Analgesics", "unit": "Tablets", "reorder": 100, "max": 1000, "price": 0.25, "mfg": "GSK"},
        {"code": "MED-017", "name": "Ibuprofen 400mg", "generic_name": "Ibuprofen", "category": "Analgesics", "unit": "Tablets", "reorder": 50, "max": 500, "price": 0.45, "mfg": "Abbott"},
        {"code": "MED-018", "name": "Tramadol 50mg Capsule", "generic_name": "Tramadol Hydrochloride", "category": "Analgesics", "unit": "Capsules", "reorder": 25, "max": 200, "price": 1.75, "mfg": "Grünenthal"},
        {"code": "MED-019", "name": "Morphine Sulfate 10mg/mL IV", "generic_name": "Morphine Sulfate", "category": "Analgesics", "unit": "Ampoules", "reorder": 15, "max": 100, "price": 9.50, "mfg": "Hikma"},
        {"code": "MED-020", "name": "Diclofenac Sodium 50mg", "generic_name": "Diclofenac Sodium", "category": "Analgesics", "unit": "Tablets", "reorder": 40, "max": 400, "price": 0.60, "mfg": "Novartis"},

        # Antidiabetics & Endocrine
        {"code": "MED-021", "name": "Metformin 500mg (XR)", "generic_name": "Metformin Hydrochloride", "category": "Antidiabetic", "unit": "Tablets", "reorder": 60, "max": 600, "price": 0.35, "mfg": "Merck"},
        {"code": "MED-022", "name": "Human Insulin Regular 100 IU/mL", "generic_name": "Regular Recombinant Insulin", "category": "Antidiabetic", "unit": "Vials", "reorder": 20, "max": 150, "price": 16.50, "mfg": "Novo Nordisk"},
        {"code": "MED-023", "name": "Insulin Glargine 100 U/mL (Lantus)", "generic_name": "Insulin Glargine", "category": "Antidiabetic", "unit": "Pens", "reorder": 15, "max": 100, "price": 38.00, "mfg": "Sanofi"},
        {"code": "MED-024", "name": "Glimepiride 2mg", "generic_name": "Glimepiride", "category": "Antidiabetic", "unit": "Tablets", "reorder": 30, "max": 300, "price": 0.80, "mfg": "Sanofi"},
        {"code": "MED-025", "name": "Levothyroxine 50mcg", "generic_name": "Levothyroxine Sodium", "category": "Endocrine", "unit": "Tablets", "reorder": 40, "max": 400, "price": 0.50, "mfg": "Abbott"},

        # Gastrointestinal
        {"code": "MED-026", "name": "Pantoprazole 40mg (E.C.)", "generic_name": "Pantoprazole Sodium", "category": "Gastrointestinal", "unit": "Tablets", "reorder": 60, "max": 600, "price": 0.90, "mfg": "Takeda"},
        {"code": "MED-027", "name": "Ondansetron 4mg Oral Dissolving", "generic_name": "Ondansetron HCl", "category": "Gastrointestinal", "unit": "Tablets", "reorder": 30, "max": 300, "price": 1.25, "mfg": "GSK"},
        {"code": "MED-028", "name": "Omeprazole 20mg Capsule", "generic_name": "Omeprazole", "category": "Gastrointestinal", "unit": "Capsules", "reorder": 50, "max": 500, "price": 0.70, "mfg": "AstraZeneca"},
        {"code": "MED-029", "name": "Loperamide 2mg", "generic_name": "Loperamide Hydrochloride", "category": "Gastrointestinal", "unit": "Capsules", "reorder": 20, "max": 200, "price": 0.40, "mfg": "Johnson & Johnson"},

        # Respiratory & Antiallergic
        {"code": "MED-030", "name": "Salbutamol Inhaler 100mcg/puff", "generic_name": "Albuterol / Salbutamol", "category": "Respiratory", "unit": "Inhalers", "reorder": 20, "max": 150, "price": 12.00, "mfg": "GSK"},
        {"code": "MED-031", "name": "Budesonide 0.5mg Respules", "generic_name": "Budesonide Inhalation", "category": "Respiratory", "unit": "Ampoules", "reorder": 30, "max": 250, "price": 3.50, "mfg": "AstraZeneca"},
        {"code": "MED-032", "name": "Montelukast 10mg", "generic_name": "Montelukast Sodium", "category": "Respiratory", "unit": "Tablets", "reorder": 30, "max": 300, "price": 1.10, "mfg": "MSD"},
        {"code": "MED-033", "name": "Cetirizine 10mg", "generic_name": "Cetirizine Hydrochloride", "category": "Antiallergic", "unit": "Tablets", "reorder": 50, "max": 500, "price": 0.30, "mfg": "UCB"},

        # Critical Care, Emergency & IV Fluids
        {"code": "MED-034", "name": "Normal Saline 0.9% 500mL IV", "generic_name": "Sodium Chloride 0.9%", "category": "IV Fluids", "unit": "Bags", "reorder": 80, "max": 800, "price": 3.00, "mfg": "Baxter"},
        {"code": "MED-035", "name": "Ringer's Lactate 500mL IV", "generic_name": "Compound Sodium Lactate", "category": "IV Fluids", "unit": "Bags", "reorder": 60, "max": 600, "price": 3.50, "mfg": "B. Braun"},
        {"code": "MED-036", "name": "Dextrose 5% in Water 500mL IV", "generic_name": "D5W IV Infusion", "category": "IV Fluids", "unit": "Bags", "reorder": 40, "max": 400, "price": 3.20, "mfg": "Baxter"},
        {"code": "MED-037", "name": "Epinephrine (Adrenaline) 1mg/mL", "generic_name": "Epinephrine Auto-inject/Ampoule", "category": "Critical Care", "unit": "Ampoules", "reorder": 20, "max": 150, "price": 7.50, "mfg": "Mylan"},
        {"code": "MED-038", "name": "Atropine Sulfate 0.6mg/mL", "generic_name": "Atropine Sulfate Injection", "category": "Critical Care", "unit": "Ampoules", "reorder": 20, "max": 150, "price": 4.00, "mfg": "Akorn"},
        {"code": "MED-039", "name": "Furosemide 20mg/2mL IV (Lasix)", "generic_name": "Furosemide Injection", "category": "Critical Care", "unit": "Ampoules", "reorder": 30, "max": 250, "price": 2.20, "mfg": "Sanofi"},
        {"code": "MED-040", "name": "Midazolam 5mg/mL IV", "generic_name": "Midazolam Hydrochloride", "category": "Critical Care", "unit": "Ampoules", "reorder": 15, "max": 100, "price": 8.00, "mfg": "Roche"},
        {"code": "MED-041", "name": "Propofol 1% 20mL (Diprivan)", "generic_name": "Propofol Emulsion", "category": "Critical Care", "unit": "Vials", "reorder": 15, "max": 100, "price": 18.50, "mfg": "Fresenius"},
        {"code": "MED-042", "name": "Dexamethasone 4mg/mL IV", "generic_name": "Dexamethasone Sodium Phosphate", "category": "Critical Care", "unit": "Vials", "reorder": 30, "max": 250, "price": 3.00, "mfg": "Merck"},
        {"code": "MED-043", "name": "Potassium Chloride 20 mEq/10mL", "generic_name": "KCl Concentrated Infusion", "category": "Critical Care", "unit": "Ampoules", "reorder": 25, "max": 200, "price": 4.50, "mfg": "Baxter"},
        {"code": "MED-044", "name": "Hydrocortisone 100mg IV", "generic_name": "Hydrocortisone Sodium Succinate", "category": "Critical Care", "unit": "Vials", "reorder": 20, "max": 150, "price": 6.00, "mfg": "Pfizer"},
        {"code": "MED-045", "name": "Dopamine HCl 200mg/5mL IV", "generic_name": "Dopamine Inotrope", "category": "Critical Care", "unit": "Ampoules", "reorder": 15, "max": 100, "price": 11.00, "mfg": "Hospira"},
        {"code": "MED-046", "name": "Noradrenaline 4mg/2mL (Levophed)", "generic_name": "Norepinephrine Bitartrate", "category": "Critical Care", "unit": "Ampoules", "reorder": 15, "max": 100, "price": 16.00, "mfg": "Pfizer"},
        {"code": "MED-047", "name": "Amiodarone 150mg/3mL IV", "generic_name": "Amiodarone Hydrochloride", "category": "Cardiovascular", "unit": "Ampoules", "reorder": 15, "max": 100, "price": 9.00, "mfg": "Sanofi"},
        {"code": "MED-048", "name": "Warfarin Sodium 5mg", "generic_name": "Warfarin Sodium", "category": "Cardiovascular", "unit": "Tablets", "reorder": 25, "max": 200, "price": 0.85, "mfg": "Bristol Myers Squibb"},
        {"code": "MED-049", "name": "Multivitamin & Zinc Drops 30mL", "generic_name": "Therapeutic Multivitamin", "category": "Nutrition", "unit": "Bottles", "reorder": 20, "max": 150, "price": 6.50, "mfg": "Abbott"},
        {"code": "MED-050", "name": "Calcium Carbonate + Vit D3", "generic_name": "Calcium 500mg + D3 400IU", "category": "Nutrition", "unit": "Tablets", "reorder": 40, "max": 400, "price": 0.45, "mfg": "GSK"},
    ]

    medicines_map = {}
    for m_info in medicines_data:
        med = db.query(Medicine).filter(Medicine.code == m_info["code"]).first()
        if not med:
            med = Medicine(
                code=m_info["code"],
                name=m_info["name"],
                generic_name=m_info["generic_name"],
                category=m_info["category"],
                unit=m_info["unit"],
                reorder_level=m_info["reorder"],
                max_stock_level=m_info["max"],
                unit_price=m_info["price"],
                manufacturer=m_info["mfg"],
                is_active=True,
            )
            db.add(med)
            db.commit()
            db.refresh(med)
        medicines_map[m_info["code"]] = med

    # Seed Medicine Batches with intentional demo scenarios
    pharm_user = users_map.get("pharmacy@carex.health")
    if db.query(MedicineBatch).count() == 0 and pharm_user:
        today_date = datetime.date.today()

        # Demo Scenario 1: Low Stock Medicine: Azithromycin 500mg (8 units, reorder level 30)
        azithro = medicines_map["MED-009"]
        b_az = MedicineBatch(
            medicine_id=azithro.id,
            batch_number="BATCH-AZI-2026",
            quantity=8,  # LOW STOCK
            initial_quantity=100,
            purchase_price=1.80,
            selling_price=2.80,
            manufacturing_date=today_date - datetime.timedelta(days=120),
            expiry_date=today_date + datetime.timedelta(days=200),
            supplier="Cipla Healthcare Logistics",
            storage_location="Shelf B-04 (Antibiotics)",
            is_active=True,
        )
        db.add(b_az)

        # Demo Scenario 2: Expiring Medicine: Amoxicillin-Clavulanate 625mg (Batch expiring in 5 days)
        amox = medicines_map["MED-010"]
        b_amox_exp = MedicineBatch(
            medicine_id=amox.id,
            batch_number="BATCH-AMX-EXP5D",
            quantity=24,
            initial_quantity=150,
            purchase_price=2.00,
            selling_price=3.20,
            manufacturing_date=today_date - datetime.timedelta(days=500),
            expiry_date=today_date + datetime.timedelta(days=5),  # EXPIRING WITHIN 7 DAYS
            supplier="GSK Pharma Distribution",
            storage_location="Shelf B-02 (Near Expiry Bin)",
            is_active=True,
        )
        b_amox_fresh = MedicineBatch(
            medicine_id=amox.id,
            batch_number="BATCH-AMX-2027",
            quantity=180,
            initial_quantity=200,
            purchase_price=2.00,
            selling_price=3.20,
            manufacturing_date=today_date - datetime.timedelta(days=30),
            expiry_date=today_date + datetime.timedelta(days=450),
            supplier="GSK Pharma Distribution",
            storage_location="Shelf B-03 (Antibiotics)",
            is_active=True,
        )
        db.add(b_amox_exp)
        db.add(b_amox_fresh)

        # Seed realistic batches for remaining medicines
        batch_counter = 1
        for med_code, med_obj in medicines_map.items():
            if med_code in ["MED-009", "MED-010"]:
                continue

            # Batch 1 (Standard Active)
            qty1 = random.randint(80, 220)
            exp_days1 = random.randint(180, 550)
            b1 = MedicineBatch(
                medicine_id=med_obj.id,
                batch_number=f"BATCH-{med_code[-3:]}-{batch_counter:02d}A",
                quantity=qty1,
                initial_quantity=qty1 + 30,
                purchase_price=round(med_obj.unit_price * 0.65, 2),
                selling_price=med_obj.unit_price,
                manufacturing_date=today_date - datetime.timedelta(days=90),
                expiry_date=today_date + datetime.timedelta(days=exp_days1),
                supplier="Apex MedSupply Global",
                storage_location=f"Aisle {random.randint(1, 4)}-Bay {random.randint(1, 8)}",
                is_active=True,
            )
            db.add(b1)
            batch_counter += 1

            # Some meds get second batch (expiring in 25 days or expired)
            if med_code in ["MED-016", "MED-026", "MED-034"]:
                b_exp = MedicineBatch(
                    medicine_id=med_obj.id,
                    batch_number=f"BATCH-{med_code[-3:]}-{batch_counter:02d}E",
                    quantity=random.randint(10, 25),
                    initial_quantity=100,
                    purchase_price=round(med_obj.unit_price * 0.65, 2),
                    selling_price=med_obj.unit_price,
                    manufacturing_date=today_date - datetime.timedelta(days=400),
                    expiry_date=today_date + datetime.timedelta(days=22),  # EXPIRING WITHIN 30 DAYS
                    supplier="Apex MedSupply Global",
                    storage_location="Clearance Bin C-1",
                    is_active=True,
                )
                db.add(b_exp)

        db.commit()

        # Seed Pharmacy Stock Purchase Transactions
        all_batches = db.query(MedicineBatch).all()
        for idx, b in enumerate(all_batches[:20]):
            txn = PharmacyTransaction(
                transaction_number=f"TXN-2026-{idx+1:04d}",
                medicine_id=b.medicine_id,
                batch_id=b.id,
                transaction_type=PharmacyTransactionType.PURCHASE,
                quantity=b.initial_quantity,
                unit_price=b.purchase_price,
                total_amount=b.initial_quantity * b.purchase_price,
                reference_type="PURCHASE_ORDER",
                reference_id=f"PO-2026-{idx+100}",
                notes=f"Stock procurement receipt for batch {b.batch_number}.",
                performed_by_id=pharm_user.id,
                created_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=random.randint(5, 30)),
            )
            db.add(txn)
        db.commit()

    # ==========================================
    # PHASE 4: 12. SEED PRESCRIPTIONS & DISPENSINGS
    # ==========================================
    if db.query(Prescription).count() == 0 and doc_user and pharm_user:
        john_pat = patients_map["CRX-2026-0001"]
        adm_john = db.query(Admission).filter(Admission.patient_id == john_pat.id).first()
        now_dt = datetime.datetime.now(datetime.timezone.utc)

        # Demo Scenario 6: Dispensed Prescription for Johnathan Doe (Post-PCI discharge)
        rx1 = Prescription(
            prescription_number="RX-2026-0001",
            patient_id=john_pat.id,
            doctor_id=doc_user.id,
            admission_id=adm_john.id if adm_john else None,
            diagnosis="Post-Percutaneous Coronary Intervention (PCI) Secondary Prevention",
            notes="Take Atorvastatin at bedtime. Take Aspirin with food. Report any unusual bleeding immediately.",
            status=PrescriptionStatus.DISPENSED,
            created_at=now_dt - datetime.timedelta(days=1),
        )
        db.add(rx1)
        db.flush()

        # Items
        atorva = medicines_map["MED-001"]
        aspirin = medicines_map["MED-002"]
        rx1_item1 = PrescriptionItem(
            prescription_id=rx1.id,
            medicine_id=atorva.id,
            dosage="20mg",
            frequency="1-0-0-1 (At bedtime)",
            duration="30 days",
            quantity_prescribed=30,
            quantity_dispensed=30,
            instructions="Take at bedtime with water.",
            status=PrescriptionItemStatus.DISPENSED,
        )
        rx1_item2 = PrescriptionItem(
            prescription_id=rx1.id,
            medicine_id=aspirin.id,
            dosage="81mg",
            frequency="1-0-0-0 (Morning with meal)",
            duration="30 days",
            quantity_prescribed=30,
            quantity_dispensed=30,
            instructions="Take after breakfast.",
            status=PrescriptionItemStatus.DISPENSED,
        )
        db.add(rx1_item1)
        db.add(rx1_item2)
        db.flush()

        # Dispensing Record
        b_atorva = db.query(MedicineBatch).filter(MedicineBatch.medicine_id == atorva.id).first()
        b_aspirin = db.query(MedicineBatch).filter(MedicineBatch.medicine_id == aspirin.id).first()

        dsp1 = Dispensing(
            dispensing_number="DSP-2026-0001",
            prescription_id=rx1.id,
            patient_id=john_pat.id,
            pharmacist_id=pharm_user.id,
            total_amount=(30 * atorva.unit_price) + (30 * aspirin.unit_price),
            notes="Dispensed with patient counseling on antiplatelet compliance.",
            created_at=now_dt - datetime.timedelta(hours=18),
        )
        db.add(dsp1)
        db.flush()

        if b_atorva:
            db.add(DispensingItem(
                dispensing_id=dsp1.id,
                prescription_item_id=rx1_item1.id,
                medicine_id=atorva.id,
                batch_id=b_atorva.id,
                quantity_dispensed=30,
                unit_price=atorva.unit_price,
                total_price=30 * atorva.unit_price,
            ))
            # Dispense Transaction
            db.add(PharmacyTransaction(
                transaction_number="TXN-2026-0050",
                medicine_id=atorva.id,
                batch_id=b_atorva.id,
                transaction_type=PharmacyTransactionType.DISPENSE,
                quantity=-30,
                unit_price=atorva.unit_price,
                total_amount=30 * atorva.unit_price,
                reference_type="DISPENSE",
                reference_id=dsp1.dispensing_number,
                notes=f"Dispensed for Rx {rx1.prescription_number} (Patient: {john_pat.full_name})",
                performed_by_id=pharm_user.id,
                created_at=now_dt - datetime.timedelta(hours=18),
            ))

        if b_aspirin:
            db.add(DispensingItem(
                dispensing_id=dsp1.id,
                prescription_item_id=rx1_item2.id,
                medicine_id=aspirin.id,
                batch_id=b_aspirin.id,
                quantity_dispensed=30,
                unit_price=aspirin.unit_price,
                total_price=30 * aspirin.unit_price,
            ))
            # Dispense Transaction
            db.add(PharmacyTransaction(
                transaction_number="TXN-2026-0051",
                medicine_id=aspirin.id,
                batch_id=b_aspirin.id,
                transaction_type=PharmacyTransactionType.DISPENSE,
                quantity=-30,
                unit_price=aspirin.unit_price,
                total_amount=30 * aspirin.unit_price,
                reference_type="DISPENSE",
                reference_id=dsp1.dispensing_number,
                notes=f"Dispensed for Rx {rx1.prescription_number} (Patient: {john_pat.full_name})",
                performed_by_id=pharm_user.id,
                created_at=now_dt - datetime.timedelta(hours=18),
            ))

        # Seed Pending Prescription for Elena Rostova
        elena_pat = patients_map["CRX-2026-0002"]
        rx2 = Prescription(
            prescription_number="RX-2026-0002",
            patient_id=elena_pat.id,
            doctor_id=doc_user.id,
            diagnosis="Right Femur Fracture Reduction - Post-Op Analgesia & Antibiotic Prophylaxis",
            notes="Take with plenty of water.",
            status=PrescriptionStatus.PENDING,
            created_at=now_dt - datetime.timedelta(hours=2),
        )
        db.add(rx2)
        db.flush()

        amox_med = medicines_map["MED-010"]
        ibu_med = medicines_map["MED-017"]
        panto_med = medicines_map["MED-026"]

        db.add(PrescriptionItem(
            prescription_id=rx2.id,
            medicine_id=amox_med.id,
            dosage="625mg",
            frequency="1-0-1 (Twice daily after food)",
            duration="5 days",
            quantity_prescribed=10,
            quantity_dispensed=0,
            instructions="Complete full 5-day course.",
            status=PrescriptionItemStatus.PENDING,
        ))
        db.add(PrescriptionItem(
            prescription_id=rx2.id,
            medicine_id=ibu_med.id,
            dosage="400mg",
            frequency="1-0-1 (As needed for acute pain)",
            duration="7 days",
            quantity_prescribed=14,
            quantity_dispensed=0,
            instructions="Take strictly after meals.",
            status=PrescriptionItemStatus.PENDING,
        ))
        db.add(PrescriptionItem(
            prescription_id=rx2.id,
            medicine_id=panto_med.id,
            dosage="40mg",
            frequency="1-0-0 (30 mins before breakfast)",
            duration="7 days",
            quantity_prescribed=7,
            quantity_dispensed=0,
            instructions="Gastric mucosal protection.",
            status=PrescriptionItemStatus.PENDING,
        ))

        db.commit()

    # ==========================================
    # PHASE 4: 13. SEED BILLING ITEMS, INVOICES & PAYMENTS
    # ==========================================
    billing_items_data = [
        {"code": "SRV-CONSULT-GEN", "name": "General Outpatient Consultation", "category": BillingCategory.CONSULTATION, "price": 50.0, "tax": 0.0},
        {"code": "SRV-CONSULT-SPEC", "name": "Specialist / Cardiologist Consultation", "category": BillingCategory.CONSULTATION, "price": 120.0, "tax": 0.0},
        {"code": "SRV-CONSULT-EMR", "name": "Emergency Trauma Level 1 Evaluation", "category": BillingCategory.CONSULTATION, "price": 180.0, "tax": 0.0},
        {"code": "SRV-ROOM-ICU", "name": "Intensive Care Unit (ICU) Daily Charge", "category": BillingCategory.ROOM, "price": 350.0, "tax": 5.0},
        {"code": "SRV-ROOM-CCU", "name": "Coronary Care Unit (CCU) Daily Charge", "category": BillingCategory.ROOM, "price": 350.0, "tax": 5.0},
        {"code": "SRV-ROOM-GEN", "name": "General Ward Bed Daily Charge", "category": BillingCategory.ROOM, "price": 150.0, "tax": 5.0},
        {"code": "SRV-PROC-ECG", "name": "12-Lead Electrocardiogram (ECG)", "category": BillingCategory.PROCEDURE, "price": 45.0, "tax": 0.0},
        {"code": "SRV-PROC-ECHO", "name": "2D Echocardiography with Doppler", "category": BillingCategory.PROCEDURE, "price": 150.0, "tax": 0.0},
        {"code": "SRV-PROC-CAST", "name": "Orthopedic Splinting & Cast Application", "category": BillingCategory.PROCEDURE, "price": 95.0, "tax": 0.0},
        {"code": "SRV-PROC-SUTURE", "name": "Minor Wound Debridement & Suturing", "category": BillingCategory.PROCEDURE, "price": 75.0, "tax": 0.0},
        {"code": "SRV-NURSING-CARE", "name": "Daily Inpatient Nursing & MAR Monitoring", "category": BillingCategory.OTHER, "price": 40.0, "tax": 0.0},
    ]

    billing_items_map = {}
    for b_info in billing_items_data:
        item = db.query(BillingItem).filter(BillingItem.code == b_info["code"]).first()
        if not item:
            item = BillingItem(
                code=b_info["code"],
                name=b_info["name"],
                category=b_info["category"],
                unit_price=b_info["price"],
                tax_percent=b_info["tax"],
                is_active=True,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
        billing_items_map[b_info["code"]] = item

    # Seed Demo Scenario 4: Outstanding Inpatient Bill for Johnathan Doe
    reception_user = users_map.get("reception@carex.health")
    if db.query(Invoice).count() == 0 and reception_user:
        john_pat = patients_map["CRX-2026-0001"]
        adm_john = db.query(Admission).filter(Admission.patient_id == john_pat.id).first()
        now_date = datetime.date.today()

        inv1 = Invoice(
            invoice_number="INV-2026-0001",
            patient_id=john_pat.id,
            admission_id=adm_john.id if adm_john else None,
            date=now_date - datetime.timedelta(days=1),
            due_date=now_date + datetime.timedelta(days=14),
            subtotal=918.0,
            discount_amount=50.0,
            tax_amount=35.0,
            total_amount=903.0,
            paid_amount=300.0,
            balance_amount=603.0,  # OUTSTANDING BALANCE
            payment_status=InvoicePaymentStatus.PARTIALLY_PAID,
            notes="Interim inpatient hospital billing for CCU stay, telemetry, and initial diagnostic panel.",
            created_by_id=reception_user.id,
        )
        db.add(inv1)
        db.flush()

        # Add invoice items
        db.add(InvoiceItem(
            invoice_id=inv1.id,
            description="Coronary Care Unit (CCU) Room Charges (2 Days)",
            category=BillingCategory.ROOM,
            quantity=2.0,
            unit_price=350.0,
            discount=0.0,
            tax_percent=5.0,
            total_price=735.0,
            reference_type="ADMISSION_ROOM",
            reference_id=str(adm_john.id) if adm_john else "1",
        ))
        db.add(InvoiceItem(
            invoice_id=inv1.id,
            description="Specialist / Cardiologist Consultation",
            category=BillingCategory.CONSULTATION,
            quantity=1.0,
            unit_price=120.0,
            discount=0.0,
            tax_percent=0.0,
            total_price=120.0,
            reference_type="CONSULTATION",
            reference_id="DR-SHARMA",
        ))
        db.add(InvoiceItem(
            invoice_id=inv1.id,
            description="12-Lead Electrocardiogram (ECG)",
            category=BillingCategory.PROCEDURE,
            quantity=1.0,
            unit_price=45.0,
            discount=0.0,
            tax_percent=0.0,
            total_price=45.0,
            reference_type="PROCEDURE",
            reference_id="ECG-01",
        ))
        db.add(InvoiceItem(
            invoice_id=inv1.id,
            description="Prescription Medications (Atorvastatin 20mg & Aspirin 81mg)",
            category=BillingCategory.MEDICINE,
            quantity=1.0,
            unit_price=48.0,
            discount=50.0,  # Hospital wellness courtesy discount
            tax_percent=0.0,
            total_price=48.0,
            reference_type="DISPENSING",
            reference_id="DSP-2026-0001",
        ))

        # Initial partial payment
        pay1 = Payment(
            payment_number="PAY-2026-0001",
            invoice_id=inv1.id,
            patient_id=john_pat.id,
            amount=300.0,
            payment_method=PaymentMethod.CARD,
            reference_number="TXN-VISA-9824",
            notes="Admission deposit paid via Visa Debit Card.",
            payment_date=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
            recorded_by_id=reception_user.id,
        )
        db.add(pay1)

        # Seed Paid Outpatient Invoice for Elena Rostova
        elena_pat = patients_map["CRX-2026-0002"]
        inv2 = Invoice(
            invoice_number="INV-2026-0002",
            patient_id=elena_pat.id,
            date=now_date,
            due_date=now_date + datetime.timedelta(days=7),
            subtotal=210.0,
            discount_amount=0.0,
            tax_amount=0.0,
            total_amount=210.0,
            paid_amount=210.0,
            balance_amount=0.0,
            payment_status=InvoicePaymentStatus.PAID,
            notes="OPD visit, Complete Blood Count diagnostic lab, and minor orthopedic splinting.",
            created_by_id=reception_user.id,
        )
        db.add(inv2)
        db.flush()

        db.add(InvoiceItem(
            invoice_id=inv2.id,
            description="General Outpatient Consultation",
            category=BillingCategory.CONSULTATION,
            quantity=1.0,
            unit_price=80.0,
            discount=0.0,
            tax_percent=0.0,
            total_price=80.0,
        ))
        db.add(InvoiceItem(
            invoice_id=inv2.id,
            description="Complete Blood Count (CBC with Differential)",
            category=BillingCategory.LAB,
            quantity=1.0,
            unit_price=35.0,
            discount=0.0,
            tax_percent=0.0,
            total_price=35.0,
            reference_type="LAB_ORDER",
            reference_id="LAB-2026-0002",
        ))
        db.add(InvoiceItem(
            invoice_id=inv2.id,
            description="Orthopedic Splinting & Cast Application",
            category=BillingCategory.PROCEDURE,
            quantity=1.0,
            unit_price=95.0,
            discount=0.0,
            tax_percent=0.0,
            total_price=95.0,
        ))

        pay2 = Payment(
            payment_number="PAY-2026-0002",
            invoice_id=inv2.id,
            patient_id=elena_pat.id,
            amount=210.0,
            payment_method=PaymentMethod.UPI,
            reference_number="UPI-REF-847291039",
            notes="Settled in full via UPI QR code at cashier desk.",
            payment_date=datetime.datetime.now(datetime.timezone.utc),
            recorded_by_id=reception_user.id,
        )
        db.add(pay2)

        db.commit()

    # ==========================================
    # PHASE 4: 14. SEED MULTI-ROLE NOTIFICATIONS
    # ==========================================
    if db.query(Notification).count() == 0:
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        notifications_data = [
            # Doctor Notifications
            {
                "user_id": users_map["dr.sharma@carex.health"].id,
                "role_target": "DOCTOR",
                "type": NotificationType.SUCCESS,
                "priority": NotificationPriority.NORMAL,
                "title": "Lab Report Released: CBC (Elena Rostova)",
                "message": "Verified diagnostic report #RPT-2026-0001 is ready. WBC 13.8 x10^3/uL flagged high.",
                "entity": "LAB_ORDER",
                "entity_id": "2",
                "time_offset": datetime.timedelta(minutes=45),
            },
            {
                "user_id": users_map["dr.sharma@carex.health"].id,
                "role_target": "DOCTOR",
                "type": NotificationType.ALERT,
                "priority": NotificationPriority.URGENT,
                "title": "STAT Emergency Arrival: Michael Sterling (STEMI)",
                "message": "Patient arrived in Trauma Bay 1 with severe chest pain (SpO2 88%). STAT Troponin ordered.",
                "entity": "EMERGENCY",
                "entity_id": "1",
                "time_offset": datetime.timedelta(minutes=15),
            },
            # Pharmacist Notifications
            {
                "user_id": users_map["pharmacy@carex.health"].id,
                "role_target": "PHARMACIST",
                "type": NotificationType.WARNING,
                "priority": NotificationPriority.HIGH,
                "title": "LOW STOCK ALERT: Azithromycin 500mg",
                "message": "Remaining stock is 8 Tablets (Reorder level is 30). Suggested reorder: 242 Tablets.",
                "entity": "INVENTORY",
                "entity_id": str(medicines_map["MED-009"].id),
                "time_offset": datetime.timedelta(hours=1),
            },
            {
                "user_id": users_map["pharmacy@carex.health"].id,
                "role_target": "PHARMACIST",
                "type": NotificationType.WARNING,
                "priority": NotificationPriority.NORMAL,
                "title": "Batch Expiry Warning: Amoxicillin-Clav 625mg",
                "message": "Batch #BATCH-AMX-EXP5D (24 units) will expire in 5 days. Prioritize FEFO dispensing.",
                "entity": "INVENTORY",
                "entity_id": str(medicines_map["MED-010"].id),
                "time_offset": datetime.timedelta(hours=2),
            },
            {
                "user_id": users_map["pharmacy@carex.health"].id,
                "role_target": "PHARMACIST",
                "type": NotificationType.INFO,
                "priority": NotificationPriority.NORMAL,
                "title": "New Prescription #RX-2026-0002 (Elena Rostova)",
                "message": "Prescription with 3 items received from Dr. Rajesh Sharma. Ready for dispensing.",
                "entity": "PRESCRIPTION",
                "entity_id": "2",
                "time_offset": datetime.timedelta(minutes=30),
            },
            # Lab Tech Notifications
            {
                "user_id": users_map["lab@carex.health"].id,
                "role_target": "LAB_TECHNICIAN",
                "type": NotificationType.ALERT,
                "priority": NotificationPriority.URGENT,
                "title": "STAT Lab Order: Cardiac Troponin I",
                "message": "Order #LAB-2026-0001 for Michael Sterling (Emergency Trauma Bay). STAT priority.",
                "entity": "LAB_ORDER",
                "entity_id": "1",
                "time_offset": datetime.timedelta(minutes=20),
            },
            # Patient Notifications
            {
                "user_id": users_map["patient.john@carex.health"].id,
                "role_target": "PATIENT",
                "type": NotificationType.SUCCESS,
                "priority": NotificationPriority.NORMAL,
                "title": "Medications Dispensed by Central Pharmacy",
                "message": "Your prescription #RX-2026-0001 (Atorvastatin & Aspirin) has been dispensed.",
                "entity": "PRESCRIPTION",
                "entity_id": "1",
                "time_offset": datetime.timedelta(hours=18),
            },
            {
                "user_id": users_map["patient.john@carex.health"].id,
                "role_target": "PATIENT",
                "type": NotificationType.INFO,
                "priority": NotificationPriority.NORMAL,
                "title": "Invoice Generated: #INV-2026-0001",
                "message": "Inpatient stay invoice of $903.00 has been generated. Outstanding balance: $603.00.",
                "entity": "INVOICE",
                "entity_id": "1",
                "time_offset": datetime.timedelta(hours=18),
            },
            # Hospital Admin Notifications
            {
                "user_id": users_map["admin@carex.health"].id,
                "role_target": "HOSPITAL_ADMIN",
                "type": NotificationType.WARNING,
                "priority": NotificationPriority.HIGH,
                "title": "ICU Ward Occupancy Threshold Exceeded",
                "message": "ICU bed occupancy is currently at 91.6% (Only 2 available beds remaining).",
                "entity": "ADMISSION",
                "entity_id": "1",
                "time_offset": datetime.timedelta(hours=3),
            },
            {
                "user_id": users_map["admin@carex.health"].id,
                "role_target": "HOSPITAL_ADMIN",
                "type": NotificationType.INFO,
                "priority": NotificationPriority.NORMAL,
                "title": "Daily Revenue Milestone: $510.00 Collected",
                "message": "Total payments processed across Cash, Card, and UPI channels today.",
                "entity": "INVOICE",
                "entity_id": "2",
                "time_offset": datetime.timedelta(hours=1),
            },
        ]

        for n_info in notifications_data:
            notif = Notification(
                user_id=n_info["user_id"],
                role_target=n_info["role_target"],
                type=n_info["type"],
                priority=n_info["priority"],
                title=n_info["title"],
                message=n_info["message"],
                related_entity=n_info["entity"],
                related_entity_id=n_info["entity_id"],
                is_read=False,
                created_at=now_dt - n_info["time_offset"],
            )
            db.add(notif)

        # -------------------------------------------------------------
        # PHASE 5: AI INTELLIGENCE LAYER SEED DATA
        # -------------------------------------------------------------
        logger.info("Seeding Phase 5 AI Predictions, Operational Alerts, Document Records & Shift Handovers...")

        # 1. Seed Initial AI Predictions
        ai_predictions_data = [
            AIPrediction(
                prediction_type=AIPredictionType.QUEUE_WAIT_TIME,
                entity_type="DEPARTMENT",
                entity_id="1",  # Cardiology
                prediction_value={"estimated_wait_minutes": 31.0, "normal_estimate_minutes": 18.0, "waiting_count": 12, "delay_minutes": 13.0},
                risk_level=AIRiskLevel.MEDIUM,
                confidence=0.89,
                model_name="carex-opd-queue-engine",
                model_version="v1.2.0-rf-queue",
                model_provider_type=ModelProviderType.STATISTICAL_MODEL,
                explanation={
                    "summary": "Projected wait time is 31 mins for 12 waiting patient(s) (Baseline: 18 mins, Delay: +13 mins).",
                    "reasons": [
                        "Computed across 38 historical consultation sessions (mean: 15.2 mins).",
                        "Recent consultation duration (18.6m) is 22% longer than historical baseline.",
                        "Moderate wait time elongation observed.",
                    ],
                    "recommended_action": "Monitor consultation pace. Pre-stage vital checks at nursing triage station.",
                },
                recommended_action="Review queue pacing and assign floating clinical support if wait exceeds 35 mins.",
                input_features={"waiting_count": 12, "department_id": 1, "sample_size": 38},
                generated_at=now_dt - datetime.timedelta(minutes=15),
            ),
            AIPrediction(
                prediction_type=AIPredictionType.BED_OCCUPANCY,
                entity_type="HOSPITAL_BEDS",
                entity_id="ALL",
                prediction_value={"current_occupancy_percent": 82.5, "projected_6h": 87.0, "projected_12h": 91.0, "projected_24h": 94.0, "occupied_beds": 33, "total_beds": 40},
                risk_level=AIRiskLevel.HIGH,
                confidence=0.91,
                model_name="carex-bed-capacity-engine",
                model_version="v1.4.0-capacity-markov",
                model_provider_type=ModelProviderType.STATISTICAL_MODEL,
                explanation={
                    "summary": "Projected 24-hour bed capacity risk is HIGH (Current: 82.5%, 24h Forecast: 94.0%).",
                    "reasons": [
                        "Current hospital-wide bed occupancy is 82.5% (33/40 beds occupied).",
                        "24-hour occupancy forecast reaches 94.0%, exceeding high-risk threshold (85%).",
                        "Admission velocity (6.8/day) outpaces discharge rate (3.4/day).",
                    ],
                    "recommended_action": "Initiate Bed Management Protocol: Review discharge-ready patients in step-down wards.",
                },
                recommended_action="Review upcoming admissions and expected discharges. Hold elective admissions.",
                input_features={"total_beds": 40, "occupied_beds": 33, "active_admissions": 14},
                generated_at=now_dt - datetime.timedelta(minutes=25),
            ),
            AIPrediction(
                prediction_type=AIPredictionType.PHARMACY_DEPLETION,
                entity_type="MEDICINE",
                entity_id="1",  # Azithromycin
                prediction_value={"medicine_id": 1, "current_stock": 8, "reorder_level": 30, "days_remaining": 1.4, "reorder_qty": 72},
                risk_level=AIRiskLevel.CRITICAL,
                confidence=0.94,
                model_name="carex-pharmacy-fefo-engine",
                model_version="v1.3.0-fefo-velocity",
                model_provider_type=ModelProviderType.STATISTICAL_MODEL,
                explanation={
                    "summary": "Azithromycin 500mg: 8 units in stock (1.4 days remaining). Risk is CRITICAL.",
                    "reasons": [
                        "Average daily dispensing velocity is 5.7 units/day (based on 172 units across 30 days).",
                        "Critical depletion risk: Only 8 units remain (1.4 days of operational supply).",
                        "Current stock has fallen below mandatory safety threshold (30 units).",
                    ],
                    "recommended_action": "Issue PO for 72 units of Azithromycin 500mg immediately.",
                },
                recommended_action="Execute automated purchase requisition PO-PHARM-2026-088 for 72 units.",
                input_features={"current_stock": 8, "reorder_level": 30, "max_stock": 80},
                generated_at=now_dt - datetime.timedelta(minutes=40),
            ),
        ]

        for p in ai_predictions_data:
            db.add(p)

        # 2. Seed Initial AI Alerts
        ai_alerts_data = [
            AIAlert(
                alert_type=AIAlertType.PHARMACY_DEPLETION,
                severity=AIAlertSeverity.CRITICAL,
                title="Pharmacy Stock Depletion Risk: Azithromycin 500mg",
                description="Azithromycin 500mg (8 units) has 1.4 days remaining at current dispensing velocity. Suggested reorder: 72 units.",
                reason=[
                    "Prescription dispensing volume surged +80% over past 48 hours.",
                    "Remaining batch inventory (8 units) is below 30% of mandatory safety buffer.",
                    "Suggested automated replenishment: 72 units to achieve target max stock.",
                ],
                recommended_action="Execute automated purchase requisition PO-PHARM-2026-088 for 72 units of Azithromycin 500mg.",
                related_entity="PHARMACY_MEDICINE",
                related_entity_id="1",
                status=AIAlertStatus.ACTIVE,
                created_at=now_dt - datetime.timedelta(minutes=35),
            ),
            AIAlert(
                alert_type=AIAlertType.BED_CAPACITY_RISK,
                severity=AIAlertSeverity.HIGH,
                title="High Bed Capacity Risk (94% Occupancy Projected) — Hospital Wide",
                description="Bed occupancy is projected to reach 94.0% within 24 hours. High admission velocity outpaces expected discharge turnover.",
                reason=[
                    "Current hospital-wide bed occupancy is 82.5% (33/40 beds occupied).",
                    "24-hour occupancy forecast reaches 94.0%, exceeding high-risk threshold (85%).",
                    "Critical care & telemetry wards operating at near saturation limit.",
                ],
                recommended_action="Initiate Bed Management Protocol: Review discharge-ready patients in step-down wards, hold elective admissions, and mobilize surge capacity beds.",
                related_entity="BED_MANAGEMENT",
                related_entity_id="ALL",
                status=AIAlertStatus.ACTIVE,
                created_at=now_dt - datetime.timedelta(minutes=20),
            ),
            AIAlert(
                alert_type=AIAlertType.OPD_DELAY,
                severity=AIAlertSeverity.WARNING,
                title="OPD Queue Delay Detected — Outpatient Clinic",
                description="Estimated wait time (31 mins) exceeds normal SLA by 13 mins for 12 waiting patients.",
                reason=[
                    "Average consultation duration elongated due to complex patient reviews.",
                    "Recent consultation duration (18.6m) is 22% longer than historical baseline.",
                ],
                recommended_action="Monitor consultation pace. Pre-stage vital checks at nursing triage station.",
                related_entity="OPD_DEPARTMENT",
                related_entity_id="1",
                status=AIAlertStatus.ACKNOWLEDGED,
                created_at=now_dt - datetime.timedelta(hours=1),
                acknowledged_at=now_dt - datetime.timedelta(minutes=45),
                acknowledged_by_id=users_map["admin@carex.health"].id,
            ),
        ]

        for a in ai_alerts_data:
            db.add(a)

        # 3. Seed Sample Medical Document Record
        sample_doc = AIDocumentRecord(
            file_name="elena_rostova_pathology_cbc.pdf",
            file_type="PDF",
            patient_id=patients_map["CRX-2026-0002"].id,
            uploaded_by_id=users_map["dr.sharma@carex.health"].id,
            document_type="LABORATORY_REPORT",
            raw_text="CAREX DIAGNOSTIC PATHOLOGY REPORT\nPatient: Elena Rostova (CRX-2026-0002)\nHemoglobin: 10.4 g/dL (Reference: 12.0 - 17.5)\nTotal Leukocyte Count (WBC): 13.8 10^3/uL (Reference: 4.5 - 11.0)\nPlatelet Count: 285 10^3/uL (Reference: 150 - 450)\nFasting Blood Glucose: 92 mg/dL (Reference: 70 - 100)\nSerum Creatinine: 0.8 mg/dL (Reference: 0.6 - 1.2)",
            extracted_data=[
                {"parameter_name": "Hemoglobin (Hb)", "result_value": "10.4", "numeric_value": 10.4, "unit": "g/dL", "reference_range": "12.0 - 17.5", "flag": "LOW", "is_abnormal": True},
                {"parameter_name": "Total Leukocyte Count (WBC)", "result_value": "13.8", "numeric_value": 13.8, "unit": "10^3/uL", "reference_range": "4.5 - 11.0", "flag": "HIGH", "is_abnormal": True},
                {"parameter_name": "Platelet Count", "result_value": "285", "numeric_value": 285.0, "unit": "10^3/uL", "reference_range": "150 - 450", "flag": "NORMAL", "is_abnormal": False},
                {"parameter_name": "Fasting Blood Glucose", "result_value": "92", "numeric_value": 92.0, "unit": "mg/dL", "reference_range": "70 - 100", "flag": "NORMAL", "is_abnormal": False},
                {"parameter_name": "Serum Creatinine", "result_value": "0.8", "numeric_value": 0.8, "unit": "mg/dL", "reference_range": "0.6 - 1.2", "flag": "NORMAL", "is_abnormal": False},
            ],
            ai_summary="Extracted 5 laboratory parameter(s). Identified 2 out-of-range observation(s): Hemoglobin (10.4 g/dL) is below reference range (12.0 - 17.5 g/dL). Total Leukocyte Count (13.8 10^3/uL) is elevated above reference threshold (4.5 - 11.0 10^3/uL).",
            confidence=0.92,
            is_verified=True,
            verified_by_id=users_map["dr.sharma@carex.health"].id,
            verified_at=now_dt - datetime.timedelta(hours=2),
            created_at=now_dt - datetime.timedelta(hours=3),
        )
        db.add(sample_doc)

        # 4. Seed Sample Nursing Shift Handover
        sample_handover = AIShiftHandover(
            ward_id=1,  # CCU Ward
            shift_name="MORNING",
            from_nurse_id=users_map["nurse.sarah@carex.health"].id,
            to_nurse_id=users_map["nurse.sarah@carex.health"].id,
            patient_summaries=[
                {
                    "admission_id": 1,
                    "admission_number": "ADM-2026-0001",
                    "patient_id": patients_map["CRX-2026-0001"].id,
                    "patient_name": "Johnathan Doe",
                    "patient_mrn": "CRX-2026-0001",
                    "bed_number": "CCU-01",
                    "ward_name": "Coronary Care Unit (CCU)",
                    "priority": "HIGH",
                    "current_status": "Continuous Acute Telemetry Monitoring",
                    "latest_vitals": {"BP": "108/68 mmHg", "Heart Rate": "98 bpm", "SpO2": "94% (4L O2)", "Temperature": "36.8°C"},
                    "pending_investigations": ["High-Sensitivity Troponin-I (STAT)"],
                    "active_medications": ["Atorvastatin 40mg (1-0-0)", "Aspirin 75mg (1-0-0)"],
                    "key_tasks": ["Hourly vital parameter charting", "Follow-up pending STAT hs-cTnI report", "Administer scheduled evening cardiac medications"],
                    "important_observations": "Patient stable post-PCI stent deployment. Continuous telemetry active. No recurring substernal chest discomfort reported.",
                }
            ],
            important_observations="Shift handover compiled for MORNING shift. Total active inpatients: 1 (1 high acuity / telemetry). All pending investigations and scheduled medication passes documented for incoming nursing team.",
            next_shift_checklist=[
                "Perform bedside handover and patient identification for active admitted patients in CCU.",
                "Verify IV line patency, infusion pump rates, and telemetry lead contact.",
                "Review and acknowledge 1 high-priority clinical care monitoring profile.",
                "Complete end-of-shift controlled medication reconciliation in central ward storage.",
            ],
            ai_notes="Automated nursing shift intelligence generated from electronic medical records, active bed telemetry, and pending diagnostic worklists. Nurse verification required before final sign-off.",
            status="APPROVED",
            approved_by_id=users_map["nurse.sarah@carex.health"].id,
            approved_at=now_dt - datetime.timedelta(hours=1),
            created_at=now_dt - datetime.timedelta(hours=2),
        )
        db.add(sample_handover)

        # 5. Seed Sample AI Feedback
        sample_feedback = AIFeedback(
            user_id=users_map["dr.sharma@carex.health"].id,
            rating="USEFUL",
            notes="Accurate queue delay prediction during morning cardiology rush. Pre-staging vitals at triage saved 10 mins per patient.",
            created_at=now_dt - datetime.timedelta(minutes=30),
        )
        db.add(sample_feedback)

        db.commit()

    logger.info("CAREX Database seeding completed successfully with all Phase 1, 2, 3, 4, & 5 AI Intelligence Layer!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
