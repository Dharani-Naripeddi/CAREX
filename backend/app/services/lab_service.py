import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

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
from app.models.patient import Patient
from app.models.user import User
from app.models.notification import NotificationType, NotificationPriority
from app.schemas.lab import (
    LabTestCreate,
    LabTestUpdate,
    LabOrderCreate,
    LabResultEntryRequest,
    LabWorkloadSummary,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.core.logging import logger


class LabService:
    @staticmethod
    def get_tests(db: Session, category: Optional[str] = None, active_only: bool = True) -> List[LabTest]:
        query = db.query(LabTest)
        if active_only:
            query = query.filter(LabTest.is_active == True)
        if category:
            query = query.filter(LabTest.category == category)
        return query.order_by(LabTest.name).all()

    @staticmethod
    def get_test_by_id(db: Session, test_id: int) -> LabTest:
        test = db.query(LabTest).filter(LabTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Laboratory test not found.")
        return test

    @staticmethod
    def create_test(db: Session, test_in: LabTestCreate, user_id: int) -> LabTest:
        existing = db.query(LabTest).filter(LabTest.code == test_in.code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Test code '{test_in.code}' already exists.")

        test = LabTest(
            code=test_in.code.upper(),
            name=test_in.name,
            category=test_in.category,
            department_id=test_in.department_id,
            description=test_in.description,
            sample_type=test_in.sample_type,
            normal_range=test_in.normal_range,
            unit=test_in.unit,
            price=test_in.price,
            is_active=test_in.is_active,
            parameters=test_in.parameters,
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        
        AuditService.log(
            db=db,
            user_id=user_id,
            action="LAB_TEST_CATALOGUE_CREATED",
            entity="LAB_TEST",
            entity_id=str(test.id),
            details={"code": test.code, "name": test.name, "price": test.price},
        )
        return test

    @staticmethod
    def get_orders(
        db: Session,
        status_filter: Optional[LabOrderStatus] = None,
        priority_filter: Optional[LabOrderPriority] = None,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LabOrder]:
        query = (
            db.query(LabOrder)
            .options(
                joinedload(LabOrder.patient),
                joinedload(LabOrder.doctor),
                joinedload(LabOrder.test),
                joinedload(LabOrder.result).joinedload(LabResult.parameters),
                joinedload(LabOrder.report),
            )
        )
        if status_filter:
            query = query.filter(LabOrder.status == status_filter)
        if priority_filter:
            query = query.filter(LabOrder.priority == priority_filter)
        if patient_id:
            query = query.filter(LabOrder.patient_id == patient_id)
        if doctor_id:
            query = query.filter(LabOrder.doctor_id == doctor_id)

        return query.order_by(
            (LabOrder.priority == LabOrderPriority.STAT).desc(),
            (LabOrder.priority == LabOrderPriority.URGENT).desc(),
            desc(LabOrder.order_date),
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> LabOrder:
        order = (
            db.query(LabOrder)
            .options(
                joinedload(LabOrder.patient),
                joinedload(LabOrder.doctor),
                joinedload(LabOrder.test),
                joinedload(LabOrder.result).joinedload(LabResult.parameters),
                joinedload(LabOrder.report),
            )
            .filter(LabOrder.id == order_id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")
        return order

    @staticmethod
    def create_order(db: Session, order_in: LabOrderCreate, doctor_id: int) -> LabOrder:
        patient = db.query(Patient).filter(Patient.id == order_in.patient_id).first()
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found.")

        test = db.query(LabTest).filter(LabTest.id == order_in.test_id).first()
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected lab test does not exist.")

        # Generate unique order number
        count = db.query(LabOrder).count() + 1
        order_number = f"LAB-2026-{count:04d}"
        while db.query(LabOrder).filter(LabOrder.order_number == order_number).first():
            count += 1
            order_number = f"LAB-2026-{count:04d}"

        order = LabOrder(
            order_number=order_number,
            patient_id=order_in.patient_id,
            doctor_id=doctor_id,
            test_id=order_in.test_id,
            admission_id=order_in.admission_id,
            emergency_case_id=order_in.emergency_case_id,
            priority=order_in.priority,
            status=LabOrderStatus.PENDING,
            clinical_notes=order_in.clinical_notes,
            sample_type=order_in.sample_type or test.sample_type,
            order_date=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(order)
        db.flush()

        # Notify Lab Technicians
        notif_priority = (
            NotificationPriority.URGENT
            if order_in.priority == LabOrderPriority.STAT
            else NotificationPriority.HIGH
            if order_in.priority == LabOrderPriority.URGENT
            else NotificationPriority.NORMAL
        )
        NotificationService.create_notification(
            db=db,
            role_target="LAB_TECHNICIAN",
            title=f"New Lab Order ({order.priority.value}): {test.name}",
            message=f"Order {order.order_number} placed for {patient.full_name} ({patient.mrn}).",
            type=NotificationType.ALERT if order.priority == LabOrderPriority.STAT else NotificationType.INFO,
            priority=notif_priority,
            related_entity="LAB_ORDER",
            related_entity_id=str(order.id),
        )

        # Audit Log
        AuditService.log(
            db=db,
            user_id=doctor_id,
            action="LAB_ORDER_CREATED",
            entity="LAB_ORDER",
            entity_id=str(order.id),
            details={
                "order_number": order.order_number,
                "test": test.name,
                "priority": order.priority.value,
                "patient": patient.full_name,
            },
        )

        db.commit()
        db.refresh(order)
        return LabService.get_order_by_id(db, order.id)

    @staticmethod
    def mark_sample_collected(db: Session, order_id: int, technician_id: int) -> LabOrder:
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")
        
        if order.status == LabOrderStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot collect sample for cancelled order.")

        order.status = LabOrderStatus.SAMPLE_COLLECTED
        order.sample_collected_at = datetime.datetime.now(datetime.timezone.utc)
        order.collected_by_id = technician_id
        db.commit()
        db.refresh(order)
        return LabService.get_order_by_id(db, order.id)

    @staticmethod
    def start_test(db: Session, order_id: int, technician_id: int) -> LabOrder:
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        order.status = LabOrderStatus.IN_PROGRESS
        order.performed_by_id = technician_id
        db.commit()
        db.refresh(order)
        return LabService.get_order_by_id(db, order.id)

    @staticmethod
    def calculate_parameter_flag(
        numeric_val: Optional[float],
        param_def: Optional[Dict[str, Any]],
    ) -> LabResultFlag:
        """Calculate reference range flags from configured parameter ranges."""
        if numeric_val is None or not param_def:
            return LabResultFlag.NORMAL

        crit_low = param_def.get("critical_low")
        crit_high = param_def.get("critical_high")
        min_val = param_def.get("min_val")
        max_val = param_def.get("max_val")

        if crit_low is not None and numeric_val < crit_low:
            return LabResultFlag.CRITICAL
        if crit_high is not None and numeric_val > crit_high:
            return LabResultFlag.CRITICAL
        if min_val is not None and numeric_val < min_val:
            return LabResultFlag.LOW
        if max_val is not None and numeric_val > max_val:
            return LabResultFlag.HIGH

        return LabResultFlag.NORMAL

    @staticmethod
    def enter_results(db: Session, order_id: int, result_in: LabResultEntryRequest, technician_id: int) -> LabOrder:
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        test = db.query(LabTest).filter(LabTest.id == order.test_id).first()
        params_map = {p.get("name"): p for p in (test.parameters or []) if isinstance(p, dict)}

        # Create or update LabResult
        existing_result = db.query(LabResult).filter(LabResult.order_id == order.id).first()
        if existing_result:
            lab_result = existing_result
            lab_result.result_summary = result_in.result_summary
            lab_result.technician_notes = result_in.technician_notes
            lab_result.technician_id = technician_id
            # Remove old parameter entries
            db.query(LabResultParameter).filter(LabResultParameter.lab_result_id == lab_result.id).delete()
        else:
            lab_result = LabResult(
                order_id=order.id,
                patient_id=order.patient_id,
                technician_id=technician_id,
                result_summary=result_in.result_summary,
                technician_notes=result_in.technician_notes,
            )
            db.add(lab_result)
            db.flush()

        has_abnormal = False
        has_critical = False

        # Add parameter items
        for p_input in result_in.parameters:
            param_config = params_map.get(p_input.parameter_name)
            calculated_flag = p_input.flag or LabService.calculate_parameter_flag(
                numeric_val=p_input.numeric_value,
                param_def=param_config,
            )
            is_crit = (calculated_flag == LabResultFlag.CRITICAL) or p_input.is_critical

            if calculated_flag in [LabResultFlag.LOW, LabResultFlag.HIGH, LabResultFlag.CRITICAL]:
                has_abnormal = True
            if is_crit:
                has_critical = True

            ref_range_str = p_input.reference_range
            if not ref_range_str and param_config:
                min_v = param_config.get("min_val")
                max_v = param_config.get("max_val")
                if min_v is not None and max_v is not None:
                    ref_range_str = f"{min_v} - {max_v}"

            unit_str = p_input.unit or (param_config.get("unit") if param_config else None) or test.unit

            param_obj = LabResultParameter(
                lab_result_id=lab_result.id,
                parameter_name=p_input.parameter_name,
                result_value=p_input.result_value,
                numeric_value=p_input.numeric_value,
                unit=unit_str,
                reference_range=ref_range_str,
                flag=calculated_flag,
                is_critical=is_crit,
            )
            db.add(param_obj)

        lab_result.is_abnormal = has_abnormal
        lab_result.is_critical = has_critical
        order.status = LabOrderStatus.COMPLETED
        order.completed_at = datetime.datetime.now(datetime.timezone.utc)
        order.performed_by_id = technician_id

        AuditService.log(
            db=db,
            user_id=technician_id,
            action="LAB_RESULT_ENTERED",
            entity="LAB_RESULT",
            entity_id=str(lab_result.id),
            details={"order_number": order.order_number, "is_abnormal": has_abnormal, "is_critical": has_critical},
        )

        db.commit()
        db.refresh(order)
        return LabService.get_order_by_id(db, order.id)

    @staticmethod
    def verify_report(
        db: Session,
        order_id: int,
        verified_by_id: int,
        clinical_impression: Optional[str] = None,
        conclusion: Optional[str] = None,
    ) -> LabReport:
        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab order not found.")

        result = db.query(LabResult).filter(LabResult.order_id == order.id).first()
        if not result:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot verify an order without entered results.")

        patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
        test = db.query(LabTest).filter(LabTest.id == order.test_id).first()
        doctor = db.query(User).filter(User.id == order.doctor_id).first()
        verifier = db.query(User).filter(User.id == verified_by_id).first()

        order.status = LabOrderStatus.VERIFIED
        order.verified_at = datetime.datetime.now(datetime.timezone.utc)
        order.verified_by_id = verified_by_id

        # Generate or update report
        existing_report = db.query(LabReport).filter(LabReport.order_id == order.id).first()
        if existing_report:
            report = existing_report
            report.status = LabReportStatus.RELEASED
            report.verified_by_id = verified_by_id
            report.clinical_impression = clinical_impression or report.clinical_impression
            report.conclusion = conclusion or report.conclusion
        else:
            report_count = db.query(LabReport).count() + 1
            report_num = f"RPT-2026-{report_count:04d}"
            while db.query(LabReport).filter(LabReport.report_number == report_num).first():
                report_count += 1
                report_num = f"RPT-2026-{report_count:04d}"
            report = LabReport(
                report_number=report_num,
                order_id=order.id,
                lab_result_id=result.id,
                patient_id=order.patient_id,
                doctor_id=order.doctor_id,
                technician_id=result.technician_id,
                verified_by_id=verified_by_id,
                report_date=datetime.datetime.now(datetime.timezone.utc),
                status=LabReportStatus.RELEASED,
                clinical_impression=clinical_impression or f"Official verified diagnostic report for {test.name}.",
                conclusion=conclusion or ("Abnormal findings flagged. Please correlate clinically." if result.is_abnormal else "All measured parameters within normal physiological reference ranges."),
            )
            db.add(report)

        db.flush()

        # Send Notifications
        # 1. To Ordering Doctor
        NotificationService.create_notification(
            db=db,
            user_id=order.doctor_id,
            title=f"Lab Report Released: {test.name}",
            message=f"Verified diagnostic report #{report.report_number} for {patient.full_name} is ready for review.",
            type=NotificationType.SUCCESS if not result.is_critical else NotificationType.CRITICAL,
            priority=NotificationPriority.URGENT if result.is_critical else NotificationPriority.NORMAL,
            related_entity="LAB_ORDER",
            related_entity_id=str(order.id),
        )

        # 2. To Patient (if patient user account exists)
        if patient.user_id:
            NotificationService.create_notification(
                db=db,
                user_id=patient.user_id,
                title="Your Laboratory Report is Available",
                message=f"The results for your {test.name} test have been released by the laboratory.",
                type=NotificationType.SUCCESS,
                priority=NotificationPriority.NORMAL,
                related_entity="LAB_ORDER",
                related_entity_id=str(order.id),
            )

        AuditService.log(
            db=db,
            user_id=verified_by_id,
            action="LAB_REPORT_VERIFIED",
            entity="LAB_REPORT",
            entity_id=str(report.id),
            details={"report_number": report.report_number, "order_number": order.order_number},
        )

        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_reports(
        db: Session,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[LabReport]:
        query = (
            db.query(LabReport)
            .options(
                joinedload(LabReport.order).joinedload(LabOrder.test),
                joinedload(LabReport.patient),
                joinedload(LabReport.doctor),
                joinedload(LabReport.technician),
                joinedload(LabReport.verified_by),
                joinedload(LabReport.lab_result).joinedload(LabResult.parameters),
            )
            .filter(LabReport.status == LabReportStatus.RELEASED)
        )
        if patient_id:
            query = query.filter(LabReport.patient_id == patient_id)
        if doctor_id:
            query = query.filter(LabReport.doctor_id == doctor_id)

        return query.order_by(desc(LabReport.report_date)).offset(skip).limit(limit).all()

    @staticmethod
    def get_workload_summary(db: Session) -> LabWorkloadSummary:
        total_orders = db.query(LabOrder).count()
        pending = db.query(LabOrder).filter(LabOrder.status == LabOrderStatus.PENDING).count()
        collected = db.query(LabOrder).filter(LabOrder.status == LabOrderStatus.SAMPLE_COLLECTED).count()
        in_progress = db.query(LabOrder).filter(LabOrder.status == LabOrderStatus.IN_PROGRESS).count()
        completed = db.query(LabOrder).filter(LabOrder.status == LabOrderStatus.COMPLETED).count()
        verified = db.query(LabOrder).filter(LabOrder.status == LabOrderStatus.VERIFIED).count()
        urgent = db.query(LabOrder).filter(
            LabOrder.status.in_([LabOrderStatus.PENDING, LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.IN_PROGRESS, LabOrderStatus.COMPLETED]),
            LabOrder.priority.in_([LabOrderPriority.URGENT, LabOrderPriority.STAT]),
        ).count()

        return LabWorkloadSummary(
            pending_count=pending,
            sample_collected_count=collected,
            in_progress_count=in_progress + collected,
            completed_count=completed,
            verified_count=verified,
            urgent_pending_count=urgent,
            today_total_orders=total_orders,
        )
