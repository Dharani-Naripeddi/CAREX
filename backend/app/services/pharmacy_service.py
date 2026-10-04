import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_

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
from app.models.patient import Patient
from app.models.user import User
from app.models.notification import NotificationType, NotificationPriority
from app.schemas.pharmacy import (
    MedicineCreate,
    MedicineUpdate,
    MedicineBatchCreate,
    PrescriptionCreate,
    DispensePayload,
    ExpiryClassificationItem,
    LowStockAlertItem,
    PharmacyDashboardStats,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.core.logging import logger


class PharmacyService:
    @staticmethod
    def get_medicines(
        db: Session,
        category: Optional[str] = None,
        query_str: Optional[str] = None,
        low_stock_only: bool = False,
        active_only: bool = True,
    ) -> List[Medicine]:
        query = db.query(Medicine).options(joinedload(Medicine.batches))
        if active_only:
            query = query.filter(Medicine.is_active == True)
        if category:
            query = query.filter(Medicine.category == category)
        if query_str:
            term = f"%{query_str}%"
            query = query.filter(
                (Medicine.name.ilike(term)) | (Medicine.generic_name.ilike(term)) | (Medicine.code.ilike(term))
            )
        
        medicines = query.order_by(Medicine.name).all()

        results = []
        for m in medicines:
            total_stock = sum(b.quantity for b in m.batches if b.is_active and b.expiry_date >= datetime.date.today())
            m.total_stock = total_stock
            m.batches_count = len(m.batches)
            m.is_low_stock = total_stock <= m.reorder_level
            m.suggested_reorder_qty = max(0, m.max_stock_level - total_stock) if m.is_low_stock else 0

            # Attach expiry status and risk to each batch
            today = datetime.date.today()
            for b in m.batches:
                days = (b.expiry_date - today).days
                b.days_to_expiry = days
                if days < 0:
                    b.expiry_status = "EXPIRED"
                    b.risk_level = "HIGH"
                elif days <= 7:
                    b.expiry_status = "EXPIRING_7_DAYS"
                    b.risk_level = "HIGH"
                elif days <= 30:
                    b.expiry_status = "EXPIRING_30_DAYS"
                    b.risk_level = "MEDIUM"
                elif days <= 90:
                    b.expiry_status = "EXPIRING_90_DAYS"
                    b.risk_level = "LOW"
                else:
                    b.expiry_status = "VALID"
                    b.risk_level = "LOW"

            if not low_stock_only or m.is_low_stock:
                results.append(m)

        return results

    @staticmethod
    def get_medicine_by_id(db: Session, medicine_id: int) -> Medicine:
        med = db.query(Medicine).options(joinedload(Medicine.batches)).filter(Medicine.id == medicine_id).first()
        if not med:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")
        total_stock = sum(b.quantity for b in med.batches if b.is_active and b.expiry_date >= datetime.date.today())
        med.total_stock = total_stock
        med.is_low_stock = total_stock <= med.reorder_level
        med.suggested_reorder_qty = max(0, med.max_stock_level - total_stock)
        return med

    @staticmethod
    def create_medicine(db: Session, med_in: MedicineCreate, user_id: int) -> Medicine:
        existing = db.query(Medicine).filter(Medicine.code == med_in.code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Medicine code '{med_in.code}' already exists.")

        med = Medicine(
            code=med_in.code.upper(),
            name=med_in.name,
            generic_name=med_in.generic_name,
            category=med_in.category,
            manufacturer=med_in.manufacturer,
            unit=med_in.unit,
            reorder_level=med_in.reorder_level,
            max_stock_level=med_in.max_stock_level,
            unit_price=med_in.unit_price,
            is_active=med_in.is_active,
        )
        db.add(med)
        db.commit()
        db.refresh(med)

        AuditService.log(
            db=db,
            user_id=user_id,
            action="MEDICINE_CATALOGUE_CREATED",
            entity="MEDICINE",
            entity_id=str(med.id),
            details={"name": med.name, "code": med.code, "unit_price": med.unit_price},
        )
        return med

    @staticmethod
    def add_batch(db: Session, batch_in: MedicineBatchCreate, user_id: int) -> MedicineBatch:
        med = db.query(Medicine).filter(Medicine.id == batch_in.medicine_id).first()
        if not med:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

        batch = MedicineBatch(
            medicine_id=batch_in.medicine_id,
            batch_number=batch_in.batch_number,
            quantity=batch_in.quantity,
            initial_quantity=batch_in.quantity,
            purchase_price=batch_in.purchase_price,
            selling_price=batch_in.selling_price or med.unit_price,
            manufacturing_date=batch_in.manufacturing_date,
            expiry_date=batch_in.expiry_date,
            supplier=batch_in.supplier,
            storage_location=batch_in.storage_location,
            is_active=True,
        )
        db.add(batch)
        db.flush()

        # Create PURCHASE Transaction record
        txn_count = db.query(PharmacyTransaction).count() + 1
        txn = PharmacyTransaction(
            transaction_number=f"TXN-2026-{txn_count:04d}",
            medicine_id=med.id,
            batch_id=batch.id,
            transaction_type=PharmacyTransactionType.PURCHASE,
            quantity=batch.quantity,
            unit_price=batch.purchase_price,
            total_amount=batch.quantity * batch.purchase_price,
            reference_type="PURCHASE_BATCH",
            reference_id=batch.batch_number,
            notes=f"Initial batch stock intake from {batch.supplier or 'Supplier'}.",
            performed_by_id=user_id,
        )
        db.add(txn)

        AuditService.log(
            db=db,
            user_id=user_id,
            action="BATCH_CREATED",
            entity="MEDICINE_BATCH",
            entity_id=str(batch.id),
            details={"batch_number": batch.batch_number, "quantity": batch.quantity, "medicine": med.name},
        )

        db.commit()
        db.refresh(batch)
        return batch

    @staticmethod
    def get_expiry_classification(db: Session) -> List[ExpiryClassificationItem]:
        today = datetime.date.today()
        batches = (
            db.query(MedicineBatch)
            .options(joinedload(MedicineBatch.medicine))
            .filter(MedicineBatch.is_active == True, MedicineBatch.quantity > 0)
            .order_by(MedicineBatch.expiry_date.asc())
            .all()
        )

        items = []
        for b in batches:
            days = (b.expiry_date - today).days
            if days < 0:
                cat = "EXPIRED"
                risk = "HIGH"
            elif days <= 7:
                cat = "EXPIRING_WITHIN_7_DAYS"
                risk = "HIGH"
            elif days <= 30:
                cat = "EXPIRING_WITHIN_30_DAYS"
                risk = "MEDIUM"
            elif days <= 90:
                cat = "EXPIRING_WITHIN_90_DAYS"
                risk = "LOW"
            else:
                continue

            items.append(
                ExpiryClassificationItem(
                    medicine_id=b.medicine.id,
                    medicine_name=b.medicine.name,
                    medicine_code=b.medicine.code,
                    batch_id=b.id,
                    batch_number=b.batch_number,
                    quantity=b.quantity,
                    expiry_date=b.expiry_date,
                    days_remaining=days,
                    category=cat,
                    risk_level=risk,
                )
            )

        return items

    @staticmethod
    def get_low_stock_alerts(db: Session) -> List[LowStockAlertItem]:
        today = datetime.date.today()
        meds = db.query(Medicine).options(joinedload(Medicine.batches)).filter(Medicine.is_active == True).all()

        alerts = []
        for m in meds:
            total_stock = sum(b.quantity for b in m.batches if b.is_active and b.expiry_date >= today)
            if total_stock <= m.reorder_level:
                suggested = max(0, m.max_stock_level - total_stock)
                alerts.append(
                    LowStockAlertItem(
                        medicine_id=m.id,
                        medicine_name=m.name,
                        medicine_code=m.code,
                        category=m.category,
                        current_stock=total_stock,
                        reorder_level=m.reorder_level,
                        max_stock_level=m.max_stock_level,
                        suggested_reorder_qty=suggested,
                        unit=m.unit,
                    )
                )

        return sorted(alerts, key=lambda x: x.current_stock)

    @staticmethod
    def get_transactions(
        db: Session,
        medicine_id: Optional[int] = None,
        transaction_type: Optional[PharmacyTransactionType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PharmacyTransaction]:
        query = (
            db.query(PharmacyTransaction)
            .options(
                joinedload(PharmacyTransaction.medicine),
                joinedload(PharmacyTransaction.batch),
                joinedload(PharmacyTransaction.performed_by),
            )
        )
        if medicine_id:
            query = query.filter(PharmacyTransaction.medicine_id == medicine_id)
        if transaction_type:
            query = query.filter(PharmacyTransaction.transaction_type == transaction_type)

        return query.order_by(desc(PharmacyTransaction.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def create_prescription(db: Session, rx_in: PrescriptionCreate, doctor_id: int) -> Prescription:
        patient = db.query(Patient).filter(Patient.id == rx_in.patient_id).first()
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

        if not rx_in.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prescription must contain at least one medication.")

        rx_count = db.query(Prescription).count() + 1
        rx_number = f"RX-2026-{rx_count:04d}"

        prescription = Prescription(
            prescription_number=rx_number,
            patient_id=rx_in.patient_id,
            doctor_id=doctor_id,
            appointment_id=rx_in.appointment_id,
            admission_id=rx_in.admission_id,
            emergency_case_id=rx_in.emergency_case_id,
            diagnosis=rx_in.diagnosis,
            notes=rx_in.notes,
            status=PrescriptionStatus.PENDING,
        )
        db.add(prescription)
        db.flush()

        for item_in in rx_in.items:
            med = db.query(Medicine).filter(Medicine.id == item_in.medicine_id).first()
            if not med:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Medicine ID {item_in.medicine_id} not found.")

            p_item = PrescriptionItem(
                prescription_id=prescription.id,
                medicine_id=item_in.medicine_id,
                dosage=item_in.dosage,
                frequency=item_in.frequency,
                duration=item_in.duration,
                quantity_prescribed=item_in.quantity_prescribed,
                quantity_dispensed=0,
                instructions=item_in.instructions,
                status=PrescriptionItemStatus.PENDING,
            )
            db.add(p_item)

        # Notify Pharmacists
        NotificationService.create_notification(
            db=db,
            role_target="PHARMACIST",
            title=f"New Prescription {prescription.prescription_number}",
            message=f"Prescription ordered for {patient.full_name} ({len(rx_in.items)} medications). Ready for dispensing.",
            type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            related_entity="PRESCRIPTION",
            related_entity_id=str(prescription.id),
        )

        db.commit()
        db.refresh(prescription)
        return PharmacyService.get_prescription_by_id(db, prescription.id)

    @staticmethod
    def get_prescriptions(
        db: Session,
        status_filter: Optional[PrescriptionStatus] = None,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Prescription]:
        query = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient),
                joinedload(Prescription.doctor),
                joinedload(Prescription.items).joinedload(PrescriptionItem.medicine),
            )
        )
        if status_filter:
            query = query.filter(Prescription.status == status_filter)
        if patient_id:
            query = query.filter(Prescription.patient_id == patient_id)
        if doctor_id:
            query = query.filter(Prescription.doctor_id == doctor_id)

        today = datetime.date.today()
        prescriptions = query.order_by(desc(Prescription.created_at)).offset(skip).limit(limit).all()
        
        # Attach available stock to items for UI display
        for p in prescriptions:
            for item in p.items:
                if item.medicine:
                    total_stock = sum(
                        b.quantity for b in item.medicine.batches if b.is_active and b.expiry_date >= today
                    )
                    item.available_stock = total_stock
                    item.unit_price = item.medicine.unit_price
        return prescriptions

    @staticmethod
    def get_prescription_by_id(db: Session, prescription_id: int) -> Prescription:
        rx = (
            db.query(Prescription)
            .options(
                joinedload(Prescription.patient),
                joinedload(Prescription.doctor),
                joinedload(Prescription.items).joinedload(PrescriptionItem.medicine),
            )
            .filter(Prescription.id == prescription_id)
            .first()
        )
        if not rx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found.")

        today = datetime.date.today()
        for item in rx.items:
            if item.medicine:
                total_stock = sum(b.quantity for b in item.medicine.batches if b.is_active and b.expiry_date >= today)
                item.available_stock = total_stock
                item.unit_price = item.medicine.unit_price
        return rx

    @staticmethod
    def dispense_prescription(
        db: Session,
        dispense_in: DispensePayload,
        pharmacist_id: int,
    ) -> Dispensing:
        """
        Execute atomic dispensing transaction:
        1. Validate stock and expiry
        2. Deduct inventory from selected batches
        3. Record immutable PharmacyTransaction records
        4. Update prescription items and prescription status
        5. Notify patient
        """
        prescription = db.query(Prescription).filter(Prescription.id == dispense_in.prescription_id).first()
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found.")

        if prescription.status == PrescriptionStatus.DISPENSED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This prescription has already been fully dispensed.")

        patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
        today = datetime.date.today()

        # Create Dispensing Header
        dsp_count = db.query(Dispensing).count() + 1
        dispensing = Dispensing(
            dispensing_number=f"DSP-2026-{dsp_count:04d}",
            prescription_id=prescription.id,
            patient_id=prescription.patient_id,
            pharmacist_id=pharmacist_id,
            notes=dispense_in.notes,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(dispensing)
        db.flush()

        total_amount = 0.0

        for item_payload in dispense_in.items:
            p_item = db.query(PrescriptionItem).filter(PrescriptionItem.id == item_payload.prescription_item_id).first()
            if not p_item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prescription item #{item_payload.prescription_item_id} not found.")

            batch = db.query(MedicineBatch).filter(MedicineBatch.id == item_payload.batch_id).first()
            if not batch:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch #{item_payload.batch_id} not found.")

            # Validation checks
            if not batch.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Batch '{batch.batch_number}' is marked inactive.")

            if batch.expiry_date < today:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Batch '{batch.batch_number}' expired on {batch.expiry_date} and cannot be dispensed.")

            if batch.quantity < item_payload.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {p_item.medicine.name}. Only {batch.quantity} units available in Batch {batch.batch_number}.",
                )

            # Deduct stock
            batch.quantity -= item_payload.quantity

            # Update prescription item
            p_item.quantity_dispensed += item_payload.quantity
            if p_item.quantity_dispensed >= p_item.quantity_prescribed:
                p_item.status = PrescriptionItemStatus.DISPENSED
            else:
                p_item.status = PrescriptionItemStatus.PARTIALLY_DISPENSED

            unit_price = batch.selling_price or p_item.medicine.unit_price
            line_total = item_payload.quantity * unit_price
            total_amount += line_total

            # Create DispensingItem
            dsp_item = DispensingItem(
                dispensing_id=dispensing.id,
                prescription_item_id=p_item.id,
                medicine_id=p_item.medicine_id,
                batch_id=batch.id,
                quantity_dispensed=item_payload.quantity,
                unit_price=unit_price,
                total_price=line_total,
            )
            db.add(dsp_item)

            # Create Pharmacy Transaction Record
            txn_count = db.query(PharmacyTransaction).count() + 1
            txn = PharmacyTransaction(
                transaction_number=f"TXN-2026-{txn_count:04d}",
                medicine_id=p_item.medicine_id,
                batch_id=batch.id,
                transaction_type=PharmacyTransactionType.DISPENSE,
                quantity=-item_payload.quantity,
                unit_price=unit_price,
                total_amount=line_total,
                reference_type="DISPENSE",
                reference_id=dispensing.dispensing_number,
                notes=f"Dispensed for Prescription {prescription.prescription_number} (Patient: {patient.full_name})",
                performed_by_id=pharmacist_id,
            )
            db.add(txn)

            # Check for low stock trigger
            remaining_med_stock = sum(b.quantity for b in p_item.medicine.batches if b.is_active and b.expiry_date >= today)
            if remaining_med_stock <= p_item.medicine.reorder_level:
                NotificationService.create_notification(
                    db=db,
                    role_target="PHARMACIST",
                    title=f"LOW STOCK ALERT: {p_item.medicine.name}",
                    message=f"Current stock has dropped to {remaining_med_stock} {p_item.medicine.unit} (Reorder level: {p_item.medicine.reorder_level}).",
                    type=NotificationType.WARNING,
                    priority=NotificationPriority.HIGH,
                    related_entity="INVENTORY",
                    related_entity_id=str(p_item.medicine.id),
                )

        dispensing.total_amount = total_amount

        # Update prescription overall status
        all_items = db.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == prescription.id).all()
        if all(i.status == PrescriptionItemStatus.DISPENSED for i in all_items):
            prescription.status = PrescriptionStatus.DISPENSED
        else:
            prescription.status = PrescriptionStatus.PARTIALLY_DISPENSED

        # Patient notification
        if patient.user_id:
            NotificationService.create_notification(
                db=db,
                user_id=patient.user_id,
                title="Prescription Dispensed",
                message=f"Your medication order for prescription {prescription.prescription_number} has been dispensed by Central Pharmacy.",
                type=NotificationType.SUCCESS,
                priority=NotificationPriority.NORMAL,
                related_entity="PRESCRIPTION",
                related_entity_id=str(prescription.id),
            )

        AuditService.log(
            db=db,
            user_id=pharmacist_id,
            action="MEDICINE_DISPENSED",
            entity="DISPENSING",
            entity_id=str(dispensing.id),
            details={
                "dispensing_number": dispensing.dispensing_number,
                "prescription_number": prescription.prescription_number,
                "total_amount": total_amount,
            },
        )

        db.commit()
        db.refresh(dispensing)
        return dispensing

    @staticmethod
    def get_dashboard_stats(db: Session) -> PharmacyDashboardStats:
        today = datetime.date.today()
        total_meds = db.query(Medicine).filter(Medicine.is_active == True).count()
        total_units = (
            db.query(func.coalesce(func.sum(MedicineBatch.quantity), 0))
            .filter(MedicineBatch.is_active == True, MedicineBatch.expiry_date >= today)
            .scalar()
        )

        low_stock_count = len(PharmacyService.get_low_stock_alerts(db))
        exp_items = PharmacyService.get_expiry_classification(db)
        expired_count = sum(1 for e in exp_items if e.category == "EXPIRED")
        expiring_soon = sum(1 for e in exp_items if e.category in ["EXPIRING_WITHIN_7_DAYS", "EXPIRING_WITHIN_30_DAYS"])

        today_dispensings = db.query(Dispensing).filter(func.date(Dispensing.created_at) == today).all()
        today_dispensed_count = len(today_dispensings)
        today_dispensed_amount = sum(d.total_amount for d in today_dispensings)

        return PharmacyDashboardStats(
            total_medicines=total_meds,
            total_stock_units=int(total_units),
            low_stock_count=low_stock_count,
            expiring_soon_count=expiring_soon,
            expired_count=expired_count,
            today_dispensed_count=today_dispensed_count,
            today_dispensed_amount=today_dispensed_amount,
        )
