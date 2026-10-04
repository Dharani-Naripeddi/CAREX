"""
Comprehensive CAREX Full-System Functional Test & Deep Diagnostics Suite
Tests all 8 user personas, all 22 API routers, all clinical and AI workflows,
edge cases, error conditions, role restrictions, and live lifecycles.
"""

import sys
import os
import json
import datetime
import traceback
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import RoleEnum
from app.models.patient import Patient
from app.models.department import Department
from app.models.bed import Bed, BedStatus
from app.models.ward import Ward
from app.models.lab import LabTest
from app.models.pharmacy import Medicine, MedicineBatch
from app.models.billing import BillingItem, BillingCategory
from app.utils.seed import seed_database, DEFAULT_PASSWORD

default_client = TestClient(app)

class TestReporter:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []
        self.module_results = {}

    def log_pass(self, module, test_name):
        self.passed += 1
        if module not in self.module_results:
            self.module_results[module] = {"passed": 0, "failed": 0}
        self.module_results[module]["passed"] += 1
        print(f"  [PASS] {test_name}")

    def log_fail(self, module, test_name, reason):
        self.failed += 1
        if module not in self.module_results:
            self.module_results[module] = {"passed": 0, "failed": 0}
        self.module_results[module]["failed"] += 1
        self.errors.append((module, test_name, reason))
        print(f"  [FAIL] {test_name}: {reason}")

    def summary(self):
        print("\n" + "="*80)
        print("CAREX COMPREHENSIVE FULL-SYSTEM TEST SUMMARY")
        print("="*80)
        for mod, res in self.module_results.items():
            status = "PASS" if res["failed"] == 0 else "FAIL"
            print(f"Module: {mod:<35} | Passed: {res['passed']:<3} | Failed: {res['failed']:<3} | [{status}]")
        print("-"*80)
        print(f"TOTAL TESTS: {self.passed + self.failed} | PASSED: {self.passed} | FAILED: {self.failed}")
        if self.errors:
            print("\nDetailed Errors Found:")
            for mod, name, reason in self.errors:
                print(f" - [{mod}] {name}: {reason}")
        print("="*80 + "\n")
        print(f"DEBUG_CHECK: failed={self.failed}, errors={self.errors}")
        return self.failed == 0

def get_auth_token(client_instance, email, password=DEFAULT_PASSWORD):
    res = client_instance.post("/api/v1/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        return res.json()["access_token"]
    raise Exception(f"Failed to login with {email}: {res.status_code} - {res.text}")

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def run_all_tests(test_client=None):
    c = test_client or default_client
    reporter = TestReporter()

    print("\n[STEP 1] Database Seeding & Health Check...")
    # Health Check
    res = c.get("/api/v1/health/")
    if res.status_code == 200 and res.json().get("status") == "healthy":
        reporter.log_pass("System Health", "GET /api/v1/health/ returns healthy")
    else:
        reporter.log_fail("System Health", "GET /api/v1/health/", f"Status {res.status_code}, body: {res.text}")

    # Root endpoint
    res = c.get("/")
    if res.status_code == 200 and res.json().get("status") == "online":
        reporter.log_pass("System Health", "GET / returns online")
    else:
        reporter.log_fail("System Health", "GET /", f"Status {res.status_code}")

    print("\n[STEP 2] Testing Authentication & All 8 Personas...")
    personas = {
        "SUPER_ADMIN": "superadmin@carex.health",
        "HOSPITAL_ADMIN": "admin@carex.health",
        "DOCTOR": "dr.sharma@carex.health",
        "NURSE": "nurse.sarah@carex.health",
        "RECEPTIONIST": "reception@carex.health",
        "PHARMACIST": "pharmacy@carex.health",
        "LAB_TECHNICIAN": "lab@carex.health",
        "PATIENT": "patient.john@carex.health",
    }
    tokens = {}
    for role_name, email in personas.items():
        try:
            tok = get_auth_token(c, email)
            tokens[role_name] = tok
            reporter.log_pass("Authentication", f"Login successful for {role_name} ({email})")
            
            # Verify /auth/me
            me_res = c.get("/api/v1/auth/me", headers=auth_headers(tok))
            if me_res.status_code == 200 and me_res.json()["email"] == email:
                reporter.log_pass("Authentication", f"GET /auth/me verified for {role_name}")
            else:
                reporter.log_fail("Authentication", f"GET /auth/me for {role_name}", f"Status {me_res.status_code}")
        except Exception as e:
            reporter.log_fail("Authentication", f"Login failed for {role_name}", str(e))

    # Invalid login test
    inv_res = c.post("/api/v1/auth/login", json={"email": "superadmin@carex.health", "password": "WrongPassword123"})
    if inv_res.status_code == 401:
        reporter.log_pass("Authentication", "Invalid password correctly rejected with 401")
    else:
        reporter.log_fail("Authentication", "Invalid password check", f"Expected 401, got {inv_res.status_code}")

    print("\n[STEP 3] Testing RBAC Boundaries & Role Restrictions...")
    # Doctor trying to access users management
    doc_tok = tokens.get("DOCTOR")
    if doc_tok:
        res = c.get("/api/v1/users/", headers=auth_headers(doc_tok))
        if res.status_code == 403:
            reporter.log_pass("RBAC", "Doctor forbidden from GET /users/ (403)")
        else:
            reporter.log_fail("RBAC", "Doctor access to /users/", f"Expected 403, got {res.status_code}")

    # Patient trying to access command center / dashboard admin
    pat_tok = tokens.get("PATIENT")
    if pat_tok:
        res = c.get("/api/v1/dashboard/admin", headers=auth_headers(pat_tok))
        if res.status_code == 403:
            reporter.log_pass("RBAC", "Patient forbidden from GET /dashboard/admin (403)")
        else:
            reporter.log_fail("RBAC", "Patient access to /dashboard/admin", f"Expected 403, got {res.status_code}")

    # Role Dashboard Endpoints
    admin_tok = tokens.get("HOSPITAL_ADMIN")
    for role_key in ["doctor", "nurse", "receptionist", "pharmacist", "lab_technician", "patient", "hospital_admin"]:
        res = c.get(f"/api/v1/dashboard/role/{role_key}", headers=auth_headers(admin_tok))
        if res.status_code == 200:
            reporter.log_pass("Role Dashboards", f"GET /dashboard/role/{role_key} returns 200")
        else:
            reporter.log_fail("Role Dashboards", f"GET /dashboard/role/{role_key}", f"Status {res.status_code}")

    print("\n[STEP 4] Master Patient Index (MPI) Flow...")
    rec_tok = tokens.get("RECEPTIONIST")
    # 1. Create Patient
    unique_suffix = int(datetime.datetime.now().timestamp())
    new_patient_payload = {
        "first_name": "Test",
        "last_name": f"Patient_{unique_suffix}",
        "date_of_birth": "1990-05-15",
        "gender": "Male",
        "blood_group": "B+",
        "contact_number": f"+91 98765{unique_suffix % 100000:05d}",
        "email": f"test.patient.{unique_suffix}@example.com",
        "address": "42 Wellness Way, Sector 5",
        "emergency_contact_name": "Family Contact",
        "emergency_contact_phone": "+91 9876543210",
        "allergies": ["Penicillin", "Sulfa Drugs"],
        "medical_history": ["Mild asthma", "Seasonal rhinitis"],
    }
    create_pat_res = c.post("/api/v1/patients/", json=new_patient_payload, headers=auth_headers(rec_tok))
    created_patient_id = None
    if create_pat_res.status_code == 201:
        created_patient_id = create_pat_res.json()["id"]
        mrn = create_pat_res.json()["mrn"]
        reporter.log_pass("Patient MPI", f"POST /patients/ created patient ID {created_patient_id} (MRN: {mrn})")
    else:
        reporter.log_fail("Patient MPI", "POST /patients/", f"Status {create_pat_res.status_code} - {create_pat_res.text}")

    if created_patient_id:
        # Search patient by name
        s_res = c.get(f"/api/v1/patients/?query=Patient_{unique_suffix}", headers=auth_headers(rec_tok))
        if s_res.status_code == 200 and len(s_res.json()) >= 1:
            reporter.log_pass("Patient MPI", "GET /patients/?query=... correctly matched patient")
        else:
            reporter.log_fail("Patient MPI", "GET /patients/?query=...", f"Status {s_res.status_code}, count: {len(s_res.json()) if s_res.status_code==200 else 0}")

        # Update patient
        upd_res = c.put(f"/api/v1/patients/{created_patient_id}", json={
            "allergies": ["Penicillin", "Sulfa Drugs", "Aspirin"],
            "medical_history": ["Mild asthma", "Seasonal rhinitis", "Hypertension Stage 1"]
        }, headers=auth_headers(rec_tok))
        if upd_res.status_code == 200 and len(upd_res.json()["allergies"]) == 3:
            reporter.log_pass("Patient MPI", f"PUT /patients/{created_patient_id} successfully updated clinical allergies & history")
        else:
            reporter.log_fail("Patient MPI", f"PUT /patients/{created_patient_id}", f"Status {upd_res.status_code}")

    print("\n[STEP 5] Appointments & Scheduling Flow...")
    # Get Doctors & Departments
    deps_res = c.get("/api/v1/departments/", headers=auth_headers(rec_tok))
    dept_id = deps_res.json()[0]["id"] if deps_res.status_code == 200 and deps_res.json() else 1
    docs_res = c.get("/api/v1/doctors/", headers=auth_headers(rec_tok))
    doc_id = docs_res.json()[0]["user_id"] if docs_res.status_code == 200 and docs_res.json() else 3

    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    apt_payload = {
        "patient_id": created_patient_id or 1,
        "doctor_id": doc_id,
        "department_id": dept_id,
        "appointment_date": tomorrow,
        "appointment_time": "10:30",
        "appointment_type": "FIRST_VISIT",
        "reason": "Routine clinical checkup and consultation",
    }
    apt_res = c.post("/api/v1/appointments/", json=apt_payload, headers=auth_headers(rec_tok))
    apt_id = None
    if apt_res.status_code == 201:
        apt_id = apt_res.json()["id"]
        reporter.log_pass("Appointments", f"POST /appointments/ booked appointment ID {apt_id}")
    else:
        reporter.log_fail("Appointments", "POST /appointments/", f"Status {apt_res.status_code} - {apt_res.text}")

    if apt_id:
        # Reschedule
        resched_res = c.put(f"/api/v1/appointments/{apt_id}/reschedule", json={
            "appointment_date": tomorrow,
            "appointment_time": "14:00",
            "notes": "Patient requested afternoon slot"
        }, headers=auth_headers(rec_tok))
        if resched_res.status_code == 200 and resched_res.json()["appointment_time"] == "14:00":
            reporter.log_pass("Appointments", f"PUT /appointments/{apt_id}/reschedule updated time to 14:00")
        else:
            reporter.log_fail("Appointments", f"PUT /appointments/{apt_id}/reschedule", f"Status {resched_res.status_code}")

        # Update status
        st_res = c.put(f"/api/v1/appointments/{apt_id}/status", json={"status": "IN_CONSULTATION"}, headers=auth_headers(rec_tok))
        if st_res.status_code == 200 and st_res.json()["status"] == "IN_CONSULTATION":
            reporter.log_pass("Appointments", f"PUT /appointments/{apt_id}/status set to IN_CONSULTATION")
        else:
            reporter.log_fail("Appointments", f"PUT /appointments/{apt_id}/status", f"Status {st_res.status_code}")

    print("\n[STEP 6] OPD Token Queue Flow...")
    tok_payload = {
        "patient_id": created_patient_id or 1,
        "department_id": dept_id,
        "doctor_id": doc_id,
        "priority": "NORMAL",
    }
    tok_res = c.post("/api/v1/tokens/generate", json=tok_payload, headers=auth_headers(rec_tok))
    token_id = None
    if tok_res.status_code == 201:
        token_id = tok_res.json()["id"]
        t_num = tok_res.json()["token_number"]
        reporter.log_pass("OPD Tokens", f"POST /tokens/generate generated token {t_num} (ID: {token_id})")
    else:
        reporter.log_fail("OPD Tokens", "POST /tokens/generate", f"Status {tok_res.status_code} - {tok_res.text}")

    if token_id:
        # Get queue status
        q_res = c.get(f"/api/v1/tokens/queue?department_id={dept_id}", headers=auth_headers(rec_tok))
        if q_res.status_code == 200:
            reporter.log_pass("OPD Tokens", f"GET /tokens/queue returned total {q_res.json().get('total_tokens_today')} tokens today")
        else:
            reporter.log_fail("OPD Tokens", "GET /tokens/queue", f"Status {q_res.status_code}")

        # Patient live token tracking
        live_res = c.get(f"/api/v1/tokens/patient/{created_patient_id or 1}/status", headers=auth_headers(rec_tok))
        if live_res.status_code == 200 and live_res.json().get("has_active_token") is True:
            reporter.log_pass("OPD Tokens", f"GET /tokens/patient/.../status verified live tracking")
        else:
            reporter.log_fail("OPD Tokens", "GET /tokens/patient/.../status", f"Status {live_res.status_code}")

        # Call token
        call_res = c.put(f"/api/v1/tokens/{token_id}/call", headers=auth_headers(doc_tok))
        if call_res.status_code == 200 and call_res.json()["status"] == "CALLED":
            reporter.log_pass("OPD Tokens", f"PUT /tokens/{token_id}/call called patient into room")
        else:
            reporter.log_fail("OPD Tokens", f"PUT /tokens/{token_id}/call", f"Status {call_res.status_code}")

        # Complete token
        comp_res = c.put(f"/api/v1/tokens/{token_id}/complete", headers=auth_headers(doc_tok))
        if comp_res.status_code == 200 and comp_res.json()["status"] == "COMPLETED":
            reporter.log_pass("OPD Tokens", f"PUT /tokens/{token_id}/complete completed consultation")
        else:
            reporter.log_fail("OPD Tokens", f"PUT /tokens/{token_id}/complete", f"Status {comp_res.status_code}")

    print("\n[STEP 7] Emergency & Triage Flow...")
    emr_payload = {
        "patient_id": created_patient_id or 1,
        "chief_complaint": "Acute crushing chest pain, diaphoresis, radiating to left arm",
        "systolic_bp": 85,
        "diastolic_bp": 55,
        "heart_rate": 138,
        "respiratory_rate": 30,
        "oxygen_saturation": 88.0,
        "temperature": 37.2,
        "gcs_score": 13,
        "pain_score": 9,
        "consciousness_level": "VERBAL",
        "is_trauma": False,
        "notes": "Suspected acute STEMI / cardiogenic shock",
    }
    emr_res = c.post("/api/v1/emergency/", json=emr_payload, headers=auth_headers(tokens.get("NURSE")))
    emr_id = None
    if emr_res.status_code == 201:
        emr_id = emr_res.json()["id"]
        triage = emr_res.json()["triage_level"]
        reporter.log_pass("Emergency Triage", f"POST /emergency/ created case ID {emr_id} with triage level {triage}")
        if triage == "RED":
            reporter.log_pass("Emergency Triage", "Critical hemodynamic instability correctly triaged as RED (Level 1)")
        else:
            reporter.log_fail("Emergency Triage", "Triage Level check", f"Expected RED for unstable vitals, got {triage}")
    else:
        reporter.log_fail("Emergency Triage", "POST /emergency/", f"Status {emr_res.status_code} - {emr_res.text}")

    print("\n[STEP 8] Inpatient Care (IPD) & Bed Census Flow...")
    # Find an available bed
    nurse_tok = tokens.get("NURSE")
    beds_res = c.get("/api/v1/beds/?status=AVAILABLE", headers=auth_headers(nurse_tok))
    avail_beds = beds_res.json() if beds_res.status_code == 200 else []
    target_bed_id = avail_beds[0]["id"] if avail_beds else None

    adm_id = None
    if target_bed_id:
        adm_payload = {
            "patient_id": created_patient_id or 1,
            "bed_id": target_bed_id,
            "attending_doctor_id": doc_id,
            "admission_reason": "Emergency stabilization and monitoring",
            "diagnosis": "Acute Coronary Syndrome",
            "admission_type": "EMERGENCY",
        }
        adm_res = c.post("/api/v1/ipd/admissions", json=adm_payload, headers=auth_headers(nurse_tok))
        if adm_res.status_code == 201:
            adm_id = adm_res.json()["id"]
            reporter.log_pass("IPD & Beds", f"POST /ipd/admissions admitted patient to Bed {target_bed_id} (Admission ID {adm_id})")
        else:
            reporter.log_fail("IPD & Beds", "POST /ipd/admissions", f"Status {adm_res.status_code} - {adm_res.text}")

    if adm_id:
        # Bed Transfer
        other_avail = [b for b in avail_beds if b["id"] != target_bed_id]
        if other_avail:
            new_bed_id = other_avail[0]["id"]
            xfer_res = c.post(f"/api/v1/ipd/admissions/{adm_id}/transfer", json={
                "to_bed_id": new_bed_id,
                "reason": "Transfer to higher observation unit"
            }, headers=auth_headers(nurse_tok))
            if xfer_res.status_code == 200:
                reporter.log_pass("IPD & Beds", f"POST /ipd/admissions/{adm_id}/transfer moved patient to Bed {new_bed_id}")
            else:
                reporter.log_fail("IPD & Beds", f"POST /ipd/admissions/{adm_id}/transfer", f"Status {xfer_res.status_code}")

        # Bed Dashboard Stats
        bed_stats_res = c.get("/api/v1/beds/dashboard", headers=auth_headers(nurse_tok))
        if bed_stats_res.status_code == 200:
            reporter.log_pass("IPD & Beds", f"GET /beds/dashboard returned total beds: {bed_stats_res.json().get('total_beds')}")
        else:
            reporter.log_fail("IPD & Beds", "GET /beds/dashboard", f"Status {bed_stats_res.status_code}")

        # Discharge patient
        dc_res = c.post(f"/api/v1/ipd/admissions/{adm_id}/discharge", json={
            "discharge_condition": "STABLE",
            "discharge_summary": "Hemodynamically stable. Discharged with home medications and follow-up in 1 week.",
            "discharge_medications": [{"name": "Aspirin 75mg", "dosage": "OD", "duration": "30 days"}]
        }, headers=auth_headers(tokens.get("DOCTOR")))
        if dc_res.status_code == 200 and dc_res.json()["status"] == "DISCHARGED":
            reporter.log_pass("IPD & Beds", f"POST /ipd/admissions/{adm_id}/discharge successfully discharged patient")
        else:
            reporter.log_fail("IPD & Beds", f"POST /ipd/admissions/{adm_id}/discharge", f"Status {dc_res.status_code}")

    print("\n[STEP 9] Diagnostic Laboratory & Specimen Flow...")
    lab_tok = tokens.get("LAB_TECHNICIAN")
    tests_res = c.get("/api/v1/lab/tests", headers=auth_headers(lab_tok))
    test_id = tests_res.json()[0]["id"] if tests_res.status_code == 200 and tests_res.json() else 1

    # Create Lab Order
    lab_order_res = c.post("/api/v1/lab/orders", json={
        "patient_id": created_patient_id or 1,
        "test_id": test_id,
        "priority": "STAT",
        "clinical_notes": "Chest pain workup",
        "sample_type": "Whole Blood",
    }, headers=auth_headers(tokens.get("DOCTOR")))
    order_id = None
    if lab_order_res.status_code == 201:
        order_id = lab_order_res.json()["id"]
        reporter.log_pass("Laboratory", f"POST /lab/orders created STAT order ID {order_id}")
    else:
        reporter.log_fail("Laboratory", "POST /lab/orders", f"Status {lab_order_res.status_code} - {lab_order_res.text}")

    if order_id:
        # Collect sample
        col_res = c.post(f"/api/v1/lab/orders/{order_id}/collect-sample", headers=auth_headers(lab_tok))
        if col_res.status_code == 200 and col_res.json()["status"] == "SAMPLE_COLLECTED":
            reporter.log_pass("Laboratory", f"POST /lab/orders/{order_id}/collect-sample accessioned specimen")
        else:
            reporter.log_fail("Laboratory", f"POST /lab/orders/{order_id}/collect-sample", f"Status {col_res.status_code}")

        # Start test
        start_res = c.post(f"/api/v1/lab/orders/{order_id}/start-test", headers=auth_headers(lab_tok))
        if start_res.status_code == 200 and start_res.json()["status"] == "IN_PROGRESS":
            reporter.log_pass("Laboratory", f"POST /lab/orders/{order_id}/start-test placed on analyzer")
        else:
            reporter.log_fail("Laboratory", f"POST /lab/orders/{order_id}/start-test", f"Status {start_res.status_code}")

        # Enter results
        res_entry = c.post(f"/api/v1/lab/orders/{order_id}/results", json={
            "parameters": [
                {"parameter_name": "Troponin I", "measured_value": "1.85", "unit": "ng/mL", "reference_range": "0.00 - 0.04", "flag": "CRITICAL"},
                {"parameter_name": "CK-MB", "measured_value": "45.0", "unit": "U/L", "reference_range": "0.0 - 25.0", "flag": "HIGH"},
            ]
        }, headers=auth_headers(lab_tok))
        if res_entry.status_code == 200 and res_entry.json()["status"] == "RESULTS_ENTERED":
            reporter.log_pass("Laboratory", f"POST /lab/orders/{order_id}/results saved structured parameters with flags")
        else:
            reporter.log_fail("Laboratory", f"POST /lab/orders/{order_id}/results", f"Status {res_entry.status_code} - {res_entry.text}")

        # Verify report
        ver_res = c.post(f"/api/v1/lab/orders/{order_id}/verify?clinical_impression=Elevated+Troponin+I+indicative+of+Myocardial+Infarction&conclusion=Clinical+correlation+with+ECG+recommended", headers=auth_headers(lab_tok))
        if ver_res.status_code == 200 and ver_res.json().get("status") == "VERIFIED":
            reporter.log_pass("Laboratory", f"POST /lab/orders/{order_id}/verify generated verified report {ver_res.json().get('report_number')}")
        else:
            reporter.log_fail("Laboratory", f"POST /lab/orders/{order_id}/verify", f"Status {ver_res.status_code} - {ver_res.text}")

        # Workload summary
        wl_res = c.get("/api/v1/lab/workload-summary", headers=auth_headers(lab_tok))
        if wl_res.status_code == 200:
            reporter.log_pass("Laboratory", f"GET /lab/workload-summary returned telemetry")
        else:
            reporter.log_fail("Laboratory", "GET /lab/workload-summary", f"Status {wl_res.status_code}")

    print("\n[STEP 10] Pharmacy, Prescriptions & Dispensing Flow...")
    pharm_tok = tokens.get("PHARMACIST")
    meds_res = c.get("/api/v1/pharmacy/medicines", headers=auth_headers(pharm_tok))
    med_id = meds_res.json()[0]["id"] if meds_res.status_code == 200 and meds_res.json() else 1

    # Create e-Prescription
    rx_payload = {
        "patient_id": created_patient_id or 1,
        "diagnosis": "Acute Coronary Syndrome & Hypertension",
        "notes": "Administer promptly with water",
        "items": [
            {
                "medicine_id": med_id,
                "dosage": "500mg",
                "frequency": "TDS",
                "duration": "5 days",
                "quantity": 10,
                "instructions": "After food",
            }
        ]
    }
    rx_res = c.post("/api/v1/pharmacy/prescriptions", json=rx_payload, headers=auth_headers(tokens.get("DOCTOR")))
    rx_id = None
    if rx_res.status_code == 201:
        rx_id = rx_res.json()["id"]
        rx_num = rx_res.json()["prescription_number"]
        reporter.log_pass("Pharmacy", f"POST /pharmacy/prescriptions created e-Rx {rx_num} (ID {rx_id})")
    else:
        reporter.log_fail("Pharmacy", "POST /pharmacy/prescriptions", f"Status {rx_res.status_code} - {rx_res.text}")

    if rx_id:
        # Dispense prescription
        med_detail = c.get("/api/v1/pharmacy/medicines", headers=auth_headers(pharm_tok)).json()
        batches = [m["batches"] for m in med_detail if m["id"] == med_id and m.get("batches")]
        batch_id = batches[0][0]["id"] if batches and batches[0] else None

        dispense_payload = {
            "prescription_id": rx_id,
            "remarks": "Dispensed full course to patient attendant",
            "items": [
                {
                    "prescription_item_id": rx_res.json()["items"][0]["id"],
                    "medicine_id": med_id,
                    "batch_id": batch_id,
                    "quantity_dispensed": 10,
                }
            ]
        }
        disp_res = c.post("/api/v1/pharmacy/dispense", json=dispense_payload, headers=auth_headers(pharm_tok))
        if disp_res.status_code == 200:
            reporter.log_pass("Pharmacy", f"POST /pharmacy/dispense atomically dispensed medication and updated inventory")
        else:
            reporter.log_fail("Pharmacy", "POST /pharmacy/dispense", f"Status {disp_res.status_code} - {disp_res.text}")

        # Expiry and Low Stock
        exp_res = c.get("/api/v1/pharmacy/expiry", headers=auth_headers(pharm_tok))
        if exp_res.status_code == 200:
            reporter.log_pass("Pharmacy", f"GET /pharmacy/expiry classified batches ({len(exp_res.json())} batches)")
        else:
            reporter.log_fail("Pharmacy", "GET /pharmacy/expiry", f"Status {exp_res.status_code}")

    print("\n[STEP 11] Billing, Invoicing & Payment Settlement Flow...")
    # Get Billing Items
    bill_items_res = c.get("/api/v1/billing/items", headers=auth_headers(rec_tok))
    bitem_id = bill_items_res.json()[0]["id"] if bill_items_res.status_code == 200 and bill_items_res.json() else None

    # Create Invoice
    inv_payload = {
        "patient_id": created_patient_id or 1,
        "discount_amount": 100.0,
        "notes": "Inpatient and lab services billing",
        "items": [
            {
                "item_name": "Specialist Cardiology Consultation",
                "category": "CONSULTATION",
                "quantity": 1,
                "unit_price": 1000.0,
            },
            {
                "item_name": "Cardiac Troponin I Diagnostic Assay",
                "category": "LAB_TEST",
                "quantity": 1,
                "unit_price": 850.0,
            }
        ]
    }
    inv_res = c.post("/api/v1/billing/invoices", json=inv_payload, headers=auth_headers(rec_tok))
    invoice_id = None
    if inv_res.status_code == 201:
        invoice_id = inv_res.json()["id"]
        inv_num = inv_res.json()["invoice_number"]
        total_amt = inv_res.json()["total_amount"]
        reporter.log_pass("Billing", f"POST /billing/invoices generated invoice {inv_num} (Total: ₹{total_amt})")
    else:
        reporter.log_fail("Billing", "POST /billing/invoices", f"Status {inv_res.status_code} - {inv_res.text}")

    if invoice_id:
        # Record Payment
        pay_res = c.post(f"/api/v1/billing/invoices/{invoice_id}/payments", json={
            "amount": 500.0,
            "payment_method": "UPI",
            "transaction_reference": f"UPI-TEST-{unique_suffix}",
            "notes": "Partial advance settlement",
        }, headers=auth_headers(rec_tok))
        if pay_res.status_code == 201:
            reporter.log_pass("Billing", f"POST /billing/invoices/{invoice_id}/payments recorded partial payment receipt {pay_res.json().get('receipt_number')}")
        else:
            reporter.log_fail("Billing", f"POST /billing/invoices/{invoice_id}/payments", f"Status {pay_res.status_code} - {pay_res.text}")

        # Dashboard stats
        bstats_res = c.get("/api/v1/billing/dashboard-stats", headers=auth_headers(rec_tok))
        if bstats_res.status_code == 200:
            reporter.log_pass("Billing", f"GET /billing/dashboard-stats returned telemetry")
        else:
            reporter.log_fail("Billing", "GET /billing/dashboard-stats", f"Status {bstats_res.status_code}")

    print("\n[STEP 12] AI Decision Support Modules (All 8 Modules)...")
    admin_tok = tokens.get("HOSPITAL_ADMIN")
    
    # 1. Queue prediction
    q_pred = c.post("/api/v1/ai/queue/predict", json={"department_id": dept_id}, headers=auth_headers(admin_tok))
    if q_pred.status_code == 200 and "predicted_wait_minutes" in q_pred.json():
        reporter.log_pass("AI Intelligence", f"AI Module 1 (OPD Queue Wait-Time Forecast): {q_pred.json()['predicted_wait_minutes']} mins (Risk: {q_pred.json()['delay_risk']})")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 1 (Queue Prediction)", f"Status {q_pred.status_code} - {q_pred.text}")

    # 2. Bed forecast
    bed_pred = c.post("/api/v1/ai/beds/predict", json={"ward_id": 1}, headers=auth_headers(admin_tok))
    if bed_pred.status_code == 200 and "forecast_6h_occupancy_pct" in bed_pred.json():
        reporter.log_pass("AI Intelligence", f"AI Module 2 (Bed Capacity Horizon & LOS Risk): 6h={bed_pred.json()['forecast_6h_occupancy_pct']}%")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 2 (Bed Forecast)", f"Status {bed_pred.status_code} - {bed_pred.text}")

    # 3. Pharmacy prediction
    pharm_pred = c.post("/api/v1/ai/pharmacy/predict", json={"medicine_id": med_id, "days_history": 30}, headers=auth_headers(admin_tok))
    if pharm_pred.status_code == 200 and "predicted_stockout_days" in pharm_pred.json():
        reporter.log_pass("AI Intelligence", f"AI Module 3 (Pharmacy Stockout Velocity): Stockout in {pharm_pred.json()['predicted_stockout_days']} days")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 3 (Pharmacy Prediction)", f"Status {pharm_pred.status_code} - {pharm_pred.text}")

    # 4. Emergency Triage AI
    triage_ai = c.post("/api/v1/ai/triage/assess", json={
        "chief_complaint": "Acute severe shortness of breath with cyanosis",
        "systolic_bp": 80,
        "heart_rate": 140,
        "oxygen_saturation": 82,
        "gcs_score": 11,
    }, headers=auth_headers(admin_tok))
    if triage_ai.status_code == 200 and "predicted_triage_level" in triage_ai.json():
        reporter.log_pass("AI Intelligence", f"AI Module 4 (Emergency Triage CDSS): Level {triage_ai.json()['predicted_triage_level']} (ESI {triage_ai.json()['esi_level']})")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 4 (Triage AI)", f"Status {triage_ai.status_code} - {triage_ai.text}")

    # 5. Document AI OCR / NER
    doc_ai = c.post("/api/v1/ai/documents/analyze", json={
        "file_name": "discharge_summary_001.pdf",
        "document_type": "LAB_REPORT",
        "raw_text": "Patient presented with severe chest pain. ECG shows ST elevation in leads II, III, aVF. Troponin I: 2.1 ng/mL. Diagnosed with Inferior STEMI. Prescribed Aspirin 75mg OD and Clopidogrel 75mg OD.",
    }, headers=auth_headers(admin_tok))
    doc_id = None
    if doc_ai.status_code == 200 and "extracted_entities" in doc_ai.json():
        doc_id = doc_ai.json()["id"]
        reporter.log_pass("AI Intelligence", f"AI Module 5 (Medical Document OCR/BioBERT NER): Extracted {len(doc_ai.json()['extracted_entities'])} entities")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 5 (Document AI)", f"Status {doc_ai.status_code} - {doc_ai.text}")

    # Verify document AI
    if doc_id:
        vdoc = c.post(f"/api/v1/ai/documents/{doc_id}/verify", headers=auth_headers(admin_tok))
        if vdoc.status_code == 200 and vdoc.json().get("is_verified") is True:
            reporter.log_pass("AI Intelligence", f"AI Module 5 Sign-off verified document ID {doc_id}")
        else:
            reporter.log_fail("AI Intelligence", f"Document verification ID {doc_id}", f"Status {vdoc.status_code}")

    # 6. Voice-to-Note EHR
    voice_ai = c.post("/api/v1/ai/voice/transcribe", json={
        "audio_text": "Patient is a 54 year old male presenting with worsening dyspnea on exertion and bilateral ankle edema for 3 weeks. Vital signs stable. S3 gallop present. Impression: Congestive Heart Failure NYHA Class III. Plan: Start Furosemide 40mg daily, strict fluid restriction, 2D-Echocardiogram.",
        "patient_id": created_patient_id or 1,
    }, headers=auth_headers(tokens.get("DOCTOR")))
    if voice_ai.status_code == 200 and "soap_note" in voice_ai.json():
        reporter.log_pass("AI Intelligence", f"AI Module 6 (Voice-to-Note Whisper SOAP): Formatted SOAP consultation note")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 6 (Voice EHR)", f"Status {voice_ai.status_code} - {voice_ai.text}")

    # 7. Nursing Shift Handover
    handover_ai = c.post("/api/v1/ai/handover/generate", json={
        "ward_id": 1,
        "shift_name": "MORNING_TO_EVENING",
    }, headers=auth_headers(tokens.get("NURSE")))
    handover_id = None
    if handover_ai.status_code == 200 and "sbar_notes" in handover_ai.json():
        handover_id = handover_ai.json()["id"]
        reporter.log_pass("AI Intelligence", f"AI Module 7 (Nursing Shift Handover SBAR): Generated handover for {handover_ai.json().get('patient_count')} patients")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 7 (Shift Handover)", f"Status {handover_ai.status_code} - {handover_ai.text}")

    if handover_id:
        hap = c.post(f"/api/v1/ai/handover/{handover_id}/approve", json={
            "important_observations": "Bed 4 patient needs evening ECG re-check.",
            "next_shift_checklist": ["Check Bed 4 Troponin repeat at 20:00", "Monitor ICU Bed 2 SpO2 continuous"]
        }, headers=auth_headers(tokens.get("NURSE")))
        if hap.status_code == 200:
            reporter.log_pass("AI Intelligence", f"AI Module 7 Shift Handover Approved successfully")
        else:
            reporter.log_fail("AI Intelligence", f"Handover approval ID {handover_id}", f"Status {hap.status_code}")

    # 8. Operational Anomaly Detector
    anom_ai = c.post("/api/v1/ai/anomalies/detect", json={"domain": "ALL"}, headers=auth_headers(admin_tok))
    if anom_ai.status_code == 200 and "anomalies" in anom_ai.json():
        reporter.log_pass("AI Intelligence", f"AI Module 8 (Operational Flow Anomaly Isolation Forest): Scanned telemetry ({len(anom_ai.json()['anomalies'])} active alerts)")
    else:
        reporter.log_fail("AI Intelligence", "AI Module 8 (Anomaly Detection)", f"Status {anom_ai.status_code} - {anom_ai.text}")

    print("\n[STEP 13] Hospital Brain Flagship Central Intelligence Layer...")
    # Overview
    hb_over = c.get("/api/v1/hospital-brain/overview", headers=auth_headers(admin_tok))
    if hb_over.status_code == 200 and "overall_strain_index" in hb_over.json():
        reporter.log_pass("Hospital Brain", f"GET /hospital-brain/overview returned Strain Index: {hb_over.json()['overall_strain_index']}/100")
    else:
        reporter.log_fail("Hospital Brain", "GET /hospital-brain/overview", f"Status {hb_over.status_code} - {hb_over.text}")

    # Events Feed
    hb_events = c.get("/api/v1/hospital-brain/events", headers=auth_headers(admin_tok))
    if hb_events.status_code == 200:
        events = hb_events.json()
        reporter.log_pass("Hospital Brain", f"GET /hospital-brain/events returned {len(events)} prioritized events")
        if events:
            ev = events[0]
            # Get Granular "Why?" Explainability breakdown
            ev_detail = c.get(f"/api/v1/hospital-brain/events/{ev['id']}", headers=auth_headers(admin_tok))
            if ev_detail.status_code == 200 and "explanation" in ev_detail.json() and "priority" in ev_detail.json():
                reporter.log_pass("Hospital Brain", f"GET /hospital-brain/events/{ev['id']} Transparent Explainability ('Why?' breakdown) verified (Priority: {ev_detail.json()['priority']['score']}/100)")
            else:
                reporter.log_fail("Hospital Brain", f"Explainability for event {ev['id']}", f"Status {ev_detail.status_code}")

            # Acknowledge event
            ack_res = c.post(f"/api/v1/hospital-brain/events/{ev['id']}/acknowledge", headers=auth_headers(admin_tok))
            if ack_res.status_code == 200 and ack_res.json()["status"] == "ACKNOWLEDGED":
                reporter.log_pass("Hospital Brain", f"POST /hospital-brain/events/{ev['id']}/acknowledge transitioned event status")
            else:
                reporter.log_fail("Hospital Brain", f"Acknowledge event {ev['id']}", f"Status {ack_res.status_code}")
    else:
        reporter.log_fail("Hospital Brain", "GET /hospital-brain/events", f"Status {hb_events.status_code}")

    # What-If Capacity Simulation Engine
    sim_res = c.post("/api/v1/hospital-brain/simulation", json={
        "emergency_arrival_delta_pct": 20,
        "icu_occupancy_delta_pct": 10,
        "opd_demand_delta_pct": 30,
        "ward_discharge_rate_delta_pct": -15
    }, headers=auth_headers(admin_tok))
    if sim_res.status_code == 200 and "projected_hospital_status" in sim_res.json():
        reporter.log_pass("Hospital Brain", f"POST /hospital-brain/simulation in-memory What-If model executed (Projected Status: {sim_res.json()['projected_hospital_status']})")
    else:
        reporter.log_fail("Hospital Brain", "POST /hospital-brain/simulation", f"Status {sim_res.status_code} - {sim_res.text}")

    print("\n[STEP 14] SIH Demo Simulator & Longitudinal Patient Journey...")
    # Scenarios list
    demo_scenarios = c.get("/api/v1/demo/scenarios", headers=auth_headers(admin_tok))
    if demo_scenarios.status_code == 200 and len(demo_scenarios.json()) == 7:
        reporter.log_pass("SIH Demo Center", f"GET /demo/scenarios returned all 7 deterministic scenarios")
    else:
        reporter.log_fail("SIH Demo Center", "GET /demo/scenarios", f"Status {demo_scenarios.status_code}")

    # Launch flagship crisis scenario
    launch_res = c.post("/api/v1/demo/launch", json={"scenario_code": "HOSPITAL_CAPACITY_CRISIS"}, headers=auth_headers(admin_tok))
    if launch_res.status_code == 200 and launch_res.json().get("scenario_code") == "HOSPITAL_CAPACITY_CRISIS":
        reporter.log_pass("SIH Demo Center", "POST /demo/launch successfully injected HOSPITAL_CAPACITY_CRISIS telemetry & alerts")
    else:
        reporter.log_fail("SIH Demo Center", "POST /demo/launch", f"Status {launch_res.status_code} - {launch_res.text}")

    # Check Pipeline Progression
    pipe_res = c.get("/api/v1/demo/pipeline-progress", headers=auth_headers(admin_tok))
    if pipe_res.status_code == 200 and len(pipe_res.json().get("steps", [])) >= 6:
        reporter.log_pass("SIH Demo Center", f"GET /demo/pipeline-progress tracked all {len(pipe_res.json()['steps'])} pipeline steps")
    else:
        reporter.log_fail("SIH Demo Center", "GET /demo/pipeline-progress", f"Status {pipe_res.status_code}")

    # Reset demo to baseline
    reset_res = c.post("/api/v1/demo/reset", headers=auth_headers(admin_tok))
    if reset_res.status_code == 200 and reset_res.json().get("status") == "SUCCESS":
        reporter.log_pass("SIH Demo Center", "POST /demo/reset zero-side-effect reset restored baseline")
    else:
        reporter.log_fail("SIH Demo Center", "POST /demo/reset", f"Status {reset_res.status_code} - {reset_res.text}")

    # End-to-End Longitudinal Patient Journey
    journey_res = c.get(f"/api/v1/patients/{created_patient_id or 1}/journey", headers=auth_headers(admin_tok))
    if journey_res.status_code == 200 and "journey_stages" in journey_res.json():
        tl_len = len(journey_res.json()["journey_stages"])
        reporter.log_pass("Patient Journey", f"GET /patients/{created_patient_id or 1}/journey synthesized {tl_len} longitudinal care touchpoints")
    else:
        reporter.log_fail("Patient Journey", f"GET /patients/{created_patient_id or 1}/journey", f"Status {journey_res.status_code} - {journey_res.text}")

    return reporter.summary(), reporter.errors

if __name__ == "__main__":
    success, errors = run_all_tests()
    if not success or errors:
        sys.exit(1)
    else:
        print("\nAll CAREX multi-role workflows and clinical endpoints verified successfully with 0 errors.\n")
        sys.exit(0)
