import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_

from app.models.billing import (
    BillingItem,
    Invoice,
    InvoiceItem,
    Payment,
    BillingCategory,
    InvoicePaymentStatus,
    PaymentMethod,
)
from app.models.patient import Patient
from app.models.user import User
from app.models.admission import Admission, AdmissionStatus
from app.models.room import Room
from app.models.lab import LabOrder, LabOrderStatus
from app.models.pharmacy import Dispensing
from app.models.notification import NotificationType, NotificationPriority
from app.schemas.billing import (
    BillingItemCreate,
    InvoiceCreate,
    PaymentCreate,
    AdmissionDischargeBillingSummary,
    BillingDashboardStats,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.core.logging import logger


class BillingService:
    @staticmethod
    def get_billing_items(db: Session, category: Optional[BillingCategory] = None, active_only: bool = True) -> List[BillingItem]:
        query = db.query(BillingItem)
        if active_only:
            query = query.filter(BillingItem.is_active == True)
        if category:
            query = query.filter(BillingItem.category == category)
        return query.order_by(BillingItem.name).all()

    @staticmethod
    def create_billing_item(db: Session, item_in: BillingItemCreate, user_id: int) -> BillingItem:
        existing = db.query(BillingItem).filter(BillingItem.code == item_in.code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Billing item code '{item_in.code}' already exists.")

        item = BillingItem(
            code=item_in.code.upper(),
            name=item_in.name,
            category=item_in.category,
            unit_price=item_in.unit_price,
            tax_percent=item_in.tax_percent,
            description=item_in.description,
            is_active=item_in.is_active,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def create_invoice(db: Session, invoice_in: InvoiceCreate, user_id: int) -> Invoice:
        patient = db.query(Patient).filter(Patient.id == invoice_in.patient_id).first()
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

        # Duplicate check for reference_type / reference_id
        for itm in invoice_in.items:
            if itm.reference_type and itm.reference_id:
                existing_item = (
                    db.query(InvoiceItem)
                    .join(Invoice)
                    .filter(
                        InvoiceItem.reference_type == itm.reference_type,
                        InvoiceItem.reference_id == str(itm.reference_id),
                        Invoice.payment_status != InvoicePaymentStatus.CANCELLED,
                    )
                    .first()
                )
                if existing_item:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"This {itm.reference_type.lower()} (#{itm.reference_id}) has already been billed in Invoice #{existing_item.invoice.invoice_number}.",
                    )

        inv_count = db.query(Invoice).count() + 1
        inv_number = f"INV-2026-{inv_count:04d}"

        invoice = Invoice(
            invoice_number=inv_number,
            patient_id=invoice_in.patient_id,
            appointment_id=invoice_in.appointment_id,
            admission_id=invoice_in.admission_id,
            emergency_case_id=invoice_in.emergency_case_id,
            date=datetime.date.today(),
            due_date=invoice_in.due_date or (datetime.date.today() + datetime.timedelta(days=14)),
            notes=invoice_in.notes,
            created_by_id=user_id,
            payment_status=InvoicePaymentStatus.UNPAID,
            paid_amount=0.0,
        )
        db.add(invoice)
        db.flush()

        subtotal = 0.0
        total_discount = 0.0
        total_tax = 0.0

        for itm_input in invoice_in.items:
            line_subtotal = itm_input.quantity * itm_input.unit_price
            discount_val = itm_input.discount
            tax_val = (line_subtotal - discount_val) * (itm_input.tax_percent / 100.0) if itm_input.tax_percent else 0.0
            line_total = (line_subtotal - discount_val) + tax_val

            subtotal += line_subtotal
            total_discount += discount_val
            total_tax += tax_val

            item_obj = InvoiceItem(
                invoice_id=invoice.id,
                billing_item_id=itm_input.billing_item_id,
                description=itm_input.description,
                category=itm_input.category,
                quantity=itm_input.quantity,
                unit_price=itm_input.unit_price,
                discount=itm_input.discount,
                tax_percent=itm_input.tax_percent,
                total_price=line_total,
                reference_type=itm_input.reference_type,
                reference_id=str(itm_input.reference_id) if itm_input.reference_id else None,
            )
            db.add(item_obj)

        invoice.subtotal = subtotal
        invoice.discount_amount = total_discount
        invoice.tax_amount = total_tax
        invoice.total_amount = (subtotal - total_discount) + total_tax
        invoice.balance_amount = invoice.total_amount

        # Send Patient Notification
        if patient.user_id:
            NotificationService.create_notification(
                db=db,
                user_id=patient.user_id,
                title=f"New Invoice Generated: {invoice.invoice_number}",
                message=f"An invoice of ${invoice.total_amount:.2f} has been generated for your recent hospital services.",
                type=NotificationType.INFO,
                priority=NotificationPriority.NORMAL,
                related_entity="INVOICE",
                related_entity_id=str(invoice.id),
            )

        AuditService.log(
            db=db,
            user_id=user_id,
            action="INVOICE_CREATED",
            entity="INVOICE",
            entity_id=str(invoice.id),
            details={"invoice_number": invoice.invoice_number, "total_amount": invoice.total_amount, "patient": patient.full_name},
        )

        db.commit()
        db.refresh(invoice)
        return BillingService.get_invoice_by_id(db, invoice.id)

    @staticmethod
    def get_invoices(
        db: Session,
        status_filter: Optional[InvoicePaymentStatus] = None,
        patient_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        query = (
            db.query(Invoice)
            .options(
                joinedload(Invoice.patient),
                joinedload(Invoice.created_by),
                joinedload(Invoice.items).joinedload(InvoiceItem.billing_item),
                joinedload(Invoice.payments).joinedload(Payment.recorded_by),
            )
        )
        if status_filter:
            query = query.filter(Invoice.payment_status == status_filter)
        if patient_id:
            query = query.filter(Invoice.patient_id == patient_id)

        invoices = query.order_by(desc(Invoice.created_at)).offset(skip).limit(limit).all()
        for inv in invoices:
            if inv.patient:
                inv.patient_name = inv.patient.full_name
                inv.patient_mrn = inv.patient.mrn
                inv.patient_phone = inv.patient.phone
                inv.patient_email = inv.patient.email
                inv.patient_address = inv.patient.address
            if inv.created_by:
                inv.created_by_name = inv.created_by.full_name
        return invoices

    @staticmethod
    def get_invoice_by_id(db: Session, invoice_id: int) -> Invoice:
        inv = (
            db.query(Invoice)
            .options(
                joinedload(Invoice.patient),
                joinedload(Invoice.created_by),
                joinedload(Invoice.items).joinedload(InvoiceItem.billing_item),
                joinedload(Invoice.payments).joinedload(Payment.recorded_by),
            )
            .filter(Invoice.id == invoice_id)
            .first()
        )
        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

        if inv.patient:
            inv.patient_name = inv.patient.full_name
            inv.patient_mrn = inv.patient.mrn
            inv.patient_phone = inv.patient.phone
            inv.patient_email = inv.patient.email
            inv.patient_address = inv.patient.address
        if inv.created_by:
            inv.created_by_name = inv.created_by.full_name
        return inv

    @staticmethod
    def record_payment(db: Session, invoice_id: int, payment_in: PaymentCreate, user_id: int) -> Payment:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

        if invoice.payment_status == InvoicePaymentStatus.PAID:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invoice is already fully paid.")

        if payment_in.amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount must be greater than zero.")

        if payment_in.amount > invoice.balance_amount + 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount (${payment_in.amount:.2f}) exceeds outstanding invoice balance (${invoice.balance_amount:.2f}).",
            )

        pay_count = db.query(Payment).count() + 1
        payment = Payment(
            payment_number=f"PAY-2026-{pay_count:04d}",
            invoice_id=invoice.id,
            patient_id=invoice.patient_id,
            amount=payment_in.amount,
            payment_method=payment_in.payment_method,
            reference_number=payment_in.reference_number,
            notes=payment_in.notes,
            payment_date=datetime.datetime.now(datetime.timezone.utc),
            recorded_by_id=user_id,
        )
        db.add(payment)
        db.flush()

        invoice.paid_amount += payment.amount
        invoice.balance_amount = max(0.0, invoice.total_amount - invoice.paid_amount)

        if invoice.balance_amount <= 0.01:
            invoice.payment_status = InvoicePaymentStatus.PAID
            invoice.balance_amount = 0.0
        else:
            invoice.payment_status = InvoicePaymentStatus.PARTIALLY_PAID

        patient = db.query(Patient).filter(Patient.id == invoice.patient_id).first()

        # Send Patient Notification
        if patient and patient.user_id:
            NotificationService.create_notification(
                db=db,
                user_id=patient.user_id,
                title="Payment Received",
                message=f"Payment of ${payment.amount:.2f} recorded for Invoice {invoice.invoice_number}. Remaining balance: ${invoice.balance_amount:.2f}.",
                type=NotificationType.SUCCESS,
                priority=NotificationPriority.NORMAL,
                related_entity="INVOICE",
                related_entity_id=str(invoice.id),
            )

        AuditService.log(
            db=db,
            user_id=user_id,
            action="PAYMENT_RECORDED",
            entity="PAYMENT",
            entity_id=str(payment.id),
            details={
                "payment_number": payment.payment_number,
                "invoice_number": invoice.invoice_number,
                "amount": payment.amount,
                "method": payment.payment_method.value,
            },
        )

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def calculate_admission_billing_summary(db: Session, admission_id: int) -> AdmissionDischargeBillingSummary:
        admission = (
            db.query(Admission)
            .options(
                joinedload(Admission.patient),
                joinedload(Admission.bed).joinedload(Bed.room),
                joinedload(Admission.ward),
            )
            .filter(Admission.id == admission_id)
            .first()
        )
        if not admission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission not found.")

        # Calculate stay days
        start_date = admission.admission_date
        end_date = admission.discharge_date or datetime.datetime.now(datetime.timezone.utc)
        stay_days = max(1, (end_date.date() - start_date.date()).days)

        room_rate = 150.0
        if admission.bed and admission.bed.room and admission.bed.room.daily_rate:
            room_rate = admission.bed.room.daily_rate
        elif admission.ward and admission.ward.code in ["ICU", "CCU"]:
            room_rate = 350.0

        room_charges = stay_days * room_rate

        # Completed lab orders during admission
        lab_orders = (
            db.query(LabOrder)
            .options(joinedload(LabOrder.test))
            .filter(LabOrder.admission_id == admission.id, LabOrder.status != LabOrderStatus.CANCELLED)
            .all()
        )
        lab_charges = sum(o.test.price for o in lab_orders if o.test)

        # Dispensings for this patient during stay
        dispensings = db.query(Dispensing).filter(Dispensing.patient_id == admission.patient_id).all()
        disp_charges = sum(d.total_amount for d in dispensings)

        procedure_charges = 0.0
        other_charges = 50.0  # Admission processing fee

        subtotal = room_charges + lab_charges + disp_charges + procedure_charges + other_charges
        tax = subtotal * 0.05  # 5% healthcare tax
        total = subtotal + tax

        # Check existing invoices
        existing_invoices = db.query(Invoice).filter(Invoice.admission_id == admission.id).all()
        unpaid = sum(i.balance_amount for i in existing_invoices)

        return AdmissionDischargeBillingSummary(
            admission_id=admission.id,
            admission_number=admission.admission_number,
            patient_id=admission.patient_id,
            patient_name=admission.patient.full_name if admission.patient else "Patient",
            stay_days=stay_days,
            daily_room_rate=room_rate,
            room_charges_total=room_charges,
            lab_charges_total=lab_charges,
            pharmacy_charges_total=disp_charges,
            procedure_charges_total=procedure_charges,
            other_charges_total=other_charges,
            estimated_subtotal=subtotal,
            estimated_tax=tax,
            estimated_total=total,
            existing_invoices_count=len(existing_invoices),
            unpaid_balance=unpaid,
        )

    @staticmethod
    def get_dashboard_stats(db: Session) -> BillingDashboardStats:
        today = datetime.date.today()
        month_start = today.replace(day=1)

        today_payments = db.query(Payment).filter(func.date(Payment.payment_date) == today).all()
        today_rev = sum(p.amount for p in today_payments)

        month_payments = db.query(Payment).filter(func.date(Payment.payment_date) >= month_start).all()
        month_rev = sum(p.amount for p in month_payments)

        unpaid_invoices = (
            db.query(Invoice)
            .filter(Invoice.payment_status.in_([InvoicePaymentStatus.UNPAID, InvoicePaymentStatus.PARTIALLY_PAID]))
            .all()
        )
        total_unpaid = sum(i.balance_amount for i in unpaid_invoices)

        today_invoices = db.query(Invoice).filter(Invoice.date == today).count()

        return BillingDashboardStats(
            today_revenue=today_rev,
            month_revenue=month_rev,
            outstanding_bills_count=len(unpaid_invoices),
            total_unpaid_amount=total_unpaid,
            today_invoices_count=today_invoices,
            today_payments_count=len(today_payments),
        )
