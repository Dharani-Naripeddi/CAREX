import pytest
import datetime
from fastapi.testclient import TestClient
from app.models.patient import Patient
from app.models.lab import LabTest, LabOrder, LabOrderStatus, LabOrderPriority, LabResultFlag
from app.models.pharmacy import Medicine, MedicineBatch, Prescription, PrescriptionStatus
from app.models.billing import BillingItem, Invoice, InvoicePaymentStatus, PaymentMethod
from app.models.notification import Notification


def get_token_for(client, email: str, password: str = "Carex#2026") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def test_lab_catalogue_and_order_lifecycle(client: TestClient, db):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")
    lab_tech_token = get_token_for(client, "lab@carex.health")

    # 1. Fetch Lab Test catalogue
    resp = client.get("/api/v1/lab/tests", headers={"Authorization": f"Bearer {lab_tech_token}"})
    assert resp.status_code == 200
    tests = resp.json()
    assert len(tests) >= 1
    cbc_test = next((t for t in tests if t["code"] == "CBC"), tests[0])

    # 2. Get a patient
    patient = db.query(Patient).first()
    assert patient is not None

    # 3. Doctor orders CBC test
    order_payload = {
        "patient_id": patient.id,
        "test_id": cbc_test["id"],
        "priority": "STAT",
        "clinical_notes": "Stat acute trauma evaluation",
    }
    resp = client.post("/api/v1/lab/orders", json=order_payload, headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code in [200, 201]
    order_data = resp.json()
    assert order_data["priority"] == "STAT"
    assert order_data["status"] == "PENDING"
    order_id = order_data["id"]

    # 4. Lab Tech collects specimen
    resp = client.post(f"/api/v1/lab/orders/{order_id}/collect-sample", headers={"Authorization": f"Bearer {lab_tech_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "SAMPLE_COLLECTED"

    # 5. Lab Tech starts analyzer test
    resp = client.post(f"/api/v1/lab/orders/{order_id}/start-test", headers={"Authorization": f"Bearer {lab_tech_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"

    # 6. Enter Results with flagged parameters
    results_payload = {
        "result_summary": "Marked neutrophilia with mild normocytic anemia.",
        "technician_notes": "Analyzed on Sysmex automated analyzer.",
        "parameters": [
            {
                "parameter_name": "Hemoglobin (Hb)",
                "result_value": "9.8",
                "numeric_value": 9.8,
                "unit": "g/dL",
                "reference_range": "13.5 - 17.5",
                "flag": "LOW",
                "is_critical": False,
            },
            {
                "parameter_name": "Total Leukocyte Count (WBC)",
                "result_value": "18.5",
                "numeric_value": 18.5,
                "unit": "10^3/uL",
                "reference_range": "4.5 - 11.0",
                "flag": "HIGH",
                "is_critical": False,
            },
        ],
    }
    resp = client.post(f"/api/v1/lab/orders/{order_id}/results", json=results_payload, headers={"Authorization": f"Bearer {lab_tech_token}"})
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "COMPLETED"
    assert res_data["result"] is not None
    assert res_data["result"]["is_abnormal"] is True
    assert len(res_data["result"]["parameters"]) == 2

    # 7. Doctor verifies and releases report
    resp = client.post(f"/api/v1/lab/orders/{order_id}/verify", headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    report_data = resp.json()
    assert report_data["status"] == "RELEASED"
    assert report_data["order_id"] == order_id


def test_pharmacy_inventory_expiry_and_low_stock(client: TestClient, db):
    pharmacist_token = get_token_for(client, "pharmacy@carex.health")

    # 1. Fetch medicines
    resp = client.get("/api/v1/pharmacy/medicines", headers={"Authorization": f"Bearer {pharmacist_token}"})
    assert resp.status_code == 200
    meds = resp.json()
    assert len(meds) >= 1

    # 2. Check Expiry Analysis
    resp = client.get("/api/v1/pharmacy/expiry", headers={"Authorization": f"Bearer {pharmacist_token}"})
    assert resp.status_code == 200
    expiry_list = resp.json()
    assert isinstance(expiry_list, list)

    # 3. Check Low Stock Alerts
    resp = client.get("/api/v1/pharmacy/low-stock", headers={"Authorization": f"Bearer {pharmacist_token}"})
    assert resp.status_code == 200
    low_stock_list = resp.json()
    assert isinstance(low_stock_list, list)

    # 4. Check Pharmacy Dashboard Stats
    resp = client.get("/api/v1/pharmacy/dashboard-stats", headers={"Authorization": f"Bearer {pharmacist_token}"})
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_medicines" in stats
    assert "total_stock_units" in stats


def test_prescription_and_atomic_dispense(client: TestClient, db):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")
    pharmacist_token = get_token_for(client, "pharmacy@carex.health")

    patient = db.query(Patient).first()
    assert patient is not None

    # Find a medicine with active batch
    batch = db.query(MedicineBatch).filter(MedicineBatch.quantity >= 10, MedicineBatch.is_active == True).first()
    assert batch is not None
    med_id = batch.medicine_id
    initial_batch_qty = batch.quantity

    # 1. Doctor creates prescription
    rx_payload = {
        "patient_id": patient.id,
        "diagnosis": "Hypertension titration",
        "notes": "Take in morning with food",
        "items": [
            {
                "medicine_id": med_id,
                "dosage": "10mg",
                "frequency": "1-0-0",
                "duration": "5 days",
                "quantity_prescribed": 5,
                "instructions": "Take after breakfast",
            }
        ],
    }
    resp = client.post("/api/v1/pharmacy/prescriptions", json=rx_payload, headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code in [200, 201]
    rx_data = resp.json()
    assert rx_data["status"] == "PENDING"
    rx_id = rx_data["id"]
    rx_item_id = rx_data["items"][0]["id"]

    # 2. Pharmacist dispenses from batch
    dispense_payload = {
        "prescription_id": rx_id,
        "items": [
            {
                "prescription_item_id": rx_item_id,
                "batch_id": batch.id,
                "quantity": 5,
            }
        ],
        "notes": "Dispensed with adherence instructions",
    }
    resp = client.post("/api/v1/pharmacy/dispense", json=dispense_payload, headers={"Authorization": f"Bearer {pharmacist_token}"})
    assert resp.status_code in [200, 201]
    dsp_data = resp.json()
    assert dsp_data["prescription_id"] == rx_id

    # Verify inventory was decremented atomically
    db.refresh(batch)
    assert batch.quantity == initial_batch_qty - 5


def test_billing_invoice_and_payment(client: TestClient, db):
    receptionist_token = get_token_for(client, "reception@carex.health")

    patient = db.query(Patient).first()
    assert patient is not None

    # 1. Get billing items
    resp = client.get("/api/v1/billing/items", headers={"Authorization": f"Bearer {receptionist_token}"})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1

    # 2. Create invoice
    inv_payload = {
        "patient_id": patient.id,
        "notes": "Outpatient diagnostic & consultation package",
        "items": [
            {
                "description": "General Outpatient Consultation",
                "category": "CONSULTATION",
                "quantity": 1,
                "unit_price": 60.0,
                "discount": 0.0,
                "tax_percent": 0.0,
            },
            {
                "description": "Complete Blood Count",
                "category": "LAB",
                "quantity": 1,
                "unit_price": 40.0,
                "discount": 0.0,
                "tax_percent": 5.0,
            },
        ],
    }
    resp = client.post("/api/v1/billing/invoices", json=inv_payload, headers={"Authorization": f"Bearer {receptionist_token}"})
    assert resp.status_code in [200, 201]
    inv_data = resp.json()
    assert inv_data["total_amount"] == 102.0  # 60 + 40 + (40 * 0.05)
    assert inv_data["payment_status"] == "UNPAID"
    inv_id = inv_data["id"]

    # 3. Record payment
    pay_payload = {
        "amount": 102.0,
        "payment_method": "CARD",
        "reference_number": "TXN-TEST-1234",
        "notes": "Full settlement via card",
    }
    resp = client.post(f"/api/v1/billing/invoices/{inv_id}/payments", json=pay_payload, headers={"Authorization": f"Bearer {receptionist_token}"})
    assert resp.status_code in [200, 201]
    pay_data = resp.json()
    assert pay_data["amount"] == 102.0

    # Verify invoice status is PAID
    resp = client.get(f"/api/v1/billing/invoices/{inv_id}", headers={"Authorization": f"Bearer {receptionist_token}"})
    assert resp.status_code == 200
    updated_inv = resp.json()
    assert updated_inv["payment_status"] == "PAID"
    assert updated_inv["balance_amount"] == 0.0


def test_notifications_unread_and_mark_read(client: TestClient, db):
    doctor_token = get_token_for(client, "dr.sharma@carex.health")

    # 1. Fetch unread count
    resp = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    count_data = resp.json()
    assert "unread_count" in count_data

    # 2. List notifications
    resp = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    notifs = resp.json()
    assert isinstance(notifs, list)

    if len(notifs) > 0:
        first_id = notifs[0]["id"]
        # Mark as read
        resp = client.post(f"/api/v1/notifications/{first_id}/read", headers={"Authorization": f"Bearer {doctor_token}"})
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    # 3. Mark all read
    resp = client.post("/api/v1/notifications/read-all", headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
