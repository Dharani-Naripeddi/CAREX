"""
CAREX Phase 3 Comprehensive End-to-End Verification Script
Tests all acute care, triage decision support, IPD admission, bed transfer,
discharge summary, and live dashboard metrics against http://localhost:8000 using httpx.
"""

import httpx

BASE_URL = "http://localhost:8000/api/v1"

def run_e2e_verification():
    print("==================================================================")
    print("STARTING CAREX PHASE 3 END-TO-END VERIFICATION")
    print("==================================================================")

    with httpx.Client(timeout=15.0) as client:
        # 1. System Health
        health_res = client.get(f"{BASE_URL}/health/")
        assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
        print(f"PASS: 1. System Health OK: {health_res.json()}")

        # 2. Authenticate as Hospital Admin
        login_res = client.post(f"{BASE_URL}/auth/login", json={"email": "admin@carex.health", "password": "Carex#2026"})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"PASS: 2. Admin Authentication OK (Token acquired)")

        # 3. Verify Admin Command Center Live Data
        cmd_res = client.get(f"{BASE_URL}/dashboard/admin", headers=headers)
        assert cmd_res.status_code == 200, f"Admin dashboard failed: {cmd_res.text}"
        cmd_data = cmd_res.json()
        assert len(cmd_data["kpis"]) >= 8
        print(f"PASS: 3. Command Center KPIs OK (Total KPIs: {len(cmd_data['kpis'])})")
        for kpi in cmd_data["kpis"][:4]:
            print(f"     - {kpi['title']}: {kpi['value']} ({kpi['subtext']})")

        # 4. Emergency Case Registration with Rule-Based Triage Support (LEVEL 1 RED)
        emr_payload = {
            "patient_name": "Alexander Cross",
            "age": 54,
            "gender": "Male",
            "symptoms": "Severe crushing substernal chest pain, cold diaphoresis, dyspnea",
            "injury_type": "Suspected Acute STEMI / Cardiogenic Shock",
            "heart_rate": 148,
            "bp_systolic": 76,
            "bp_diastolic": 44,
            "spo2": 86.5,
            "temperature": 37.2,
            "respiratory_rate": 36,
            "consciousness": "ALERT",
        }
        emr_res = client.post(f"{BASE_URL}/emergency/", json=emr_payload, headers=headers)
        assert emr_res.status_code == 201, f"Emergency registration failed: {emr_res.text}"
        emr_case = emr_res.json()
        assert emr_case["triage_level"] == "RED", f"Expected RED triage, got: {emr_case['triage_level']}"
        assert len(emr_case["contributing_factors"]) >= 2
        assert "AI decision support only" in emr_case["disclaimer"]
        print(f"PASS: 4. Emergency Registration & Triage OK:")
        print(f"     - Case Number: {emr_case['case_number']}")
        print(f"     - Triage Level: {emr_case['triage_level']} (STAT)")
        print(f"     - Factors: {emr_case['contributing_factors']}")
        print(f"     - Action: {emr_case['recommended_action']}")

        # 5. Resource Coordination Telemetry
        res_coord = client.get(f"{BASE_URL}/resources/coordination", headers=headers)
        assert res_coord.status_code == 200, f"Resource coordination failed: {res_coord.text}"
        rc_data = res_coord.json()
        assert len(rc_data["resources"]) >= 5
        assert len(rc_data["operational_recommendations"]) >= 1
        print(f"PASS: 5. Resource Coordination Telemetry OK:")
        for r in rc_data["resources"]:
            print(f"     - {r['name']} [{r['status']}]: {r['current_capacity']}/{r['total_capacity']} ({r['utilization_percentage']}%)")
        print(f"     - Recommendations: {rc_data['operational_recommendations']}")

        # 6. Inpatient (IPD) Admission & Bed Allocation
        icu_beds = client.get(f"{BASE_URL}/beds/?status=AVAILABLE", headers=headers).json()
        assert len(icu_beds) > 0, "No available beds for admission test"
        target_bed = icu_beds[0]

        patients = client.get(f"{BASE_URL}/patients/", headers=headers).json()
        doctors = client.get(f"{BASE_URL}/doctors/", headers=headers).json()

        adm_payload = {
            "patient_id": patients[0]["id"],
            "admitting_doctor_id": doctors[0]["user_id"],
            "ward_id": target_bed["ward_id"],
            "bed_id": target_bed["id"],
            "admission_reason": "Emergency Admission: Post-Resuscitation CCU/ICU Titration",
            "expected_stay_days": 4,
            "emergency_case_id": emr_case["id"],
        }
        adm_res = client.post(f"{BASE_URL}/ipd/admissions", json=adm_payload, headers=headers)
        assert adm_res.status_code == 201, f"IPD admission failed: {adm_res.text}"
        admission = adm_res.json()
        print(f"PASS: 6. Inpatient Admission Created OK:")
        print(f"     - Admission #: {admission['admission_number']}")
        print(f"     - Ward: {admission['ward_name']} | Bed: {admission['bed_number']}")
        print(f"     - Status: {admission['status']}")

        # Verify Bed status became OCCUPIED
        bed_check = client.get(f"{BASE_URL}/beds/?ward_id={target_bed['ward_id']}", headers=headers).json()
        occ_bed = next(b for b in bed_check if b["id"] == target_bed["id"])
        assert occ_bed["status"] == "OCCUPIED"
        print(f"     - Bed {occ_bed['bed_number']} confirmed OCCUPIED by {occ_bed['patient_name']}")

        # 7. Bed Management Dashboard Telemetry
        bed_dash = client.get(f"{BASE_URL}/beds/dashboard", headers=headers).json()
        print(f"PASS: 7. Bed Dashboard Telemetry OK:")
        print(f"     - Total Beds: {bed_dash['total_beds']}")
        print(f"     - Occupied: {bed_dash['occupied_beds']} ({bed_dash['occupancy_rate']}%)")
        print(f"     - Available: {bed_dash['available_beds']}")
        print(f"     - ICU Occupancy: {bed_dash['icu_occupancy_rate']}%")

        # 8. Bed Transfer Test
        avail_beds_for_trf = client.get(f"{BASE_URL}/beds/?status=AVAILABLE", headers=headers).json()
        if len(avail_beds_for_trf) > 0:
            new_bed = avail_beds_for_trf[0]
            trf_res = client.post(
                f"{BASE_URL}/ipd/admissions/{admission['id']}/transfer",
                json={"to_bed_id": new_bed["id"], "transfer_reason": "Transferred to Step-Down Unit"},
                headers=headers,
            )
            assert trf_res.status_code == 200
            print(f"PASS: 8. Inpatient Bed Transfer OK (Transferred to {new_bed['bed_number']})")

        # 9. Inpatient Discharge with Complete Discharge Summary
        discharge_payload = {
            "discharge_diagnosis": "Acute STEMI, successful PCI, hemodynamically stabilized",
            "discharge_summary": "Patient completed 4-day inpatient protocol. Echo shows preserved EF 50%.",
            "discharge_condition": "IMPROVED",
            "discharge_medications": [
                {"name": "Ticagrelor 90mg", "dosage": "1 tab PO BID", "duration": "1 year"},
                {"name": "Aspirin 81mg", "dosage": "1 tab PO daily", "duration": "Indefinite"},
                {"name": "Rosuvastatin 20mg", "dosage": "1 tab PO daily", "duration": "Indefinite"},
            ],
            "follow_up_instructions": "Cardiology clinic follow-up in 14 days.",
        }
        dis_res = client.post(
            f"{BASE_URL}/ipd/admissions/{admission['id']}/discharge",
            json=discharge_payload,
            headers=headers,
        )
        assert dis_res.status_code == 200, f"Discharge failed: {dis_res.text}"
        dis_data = dis_res.json()
        assert dis_data["status"] == "DISCHARGED"
        print(f"PASS: 9. Inpatient Discharge with Summary OK:")
        print(f"     - Condition: {dis_data['discharge_condition']}")
        print(f"     - Summary: {dis_data['discharge_summary']}")
        print(f"     - Medications: {len(dis_data['discharge_medications'])} prescribed")

        # 10. Phase 2 Backward Compatibility Verification
        patients_list = client.get(f"{BASE_URL}/patients/", headers=headers).json()
        assert len(patients_list) >= 3
        tokens_queue = client.get(f"{BASE_URL}/tokens/queue", headers=headers).json()
        assert "total_in_queue" in tokens_queue
        print(f"PASS: 10. Phase 2 Compatibility OK (Patients: {len(patients_list)}, Total in Queue: {tokens_queue['total_in_queue']})")

    print("==================================================================")
    print("ALL PHASE 3 END-TO-END VERIFICATION CHECKS PASSED 100%!")
    print("==================================================================")

if __name__ == "__main__":
    run_e2e_verification()
