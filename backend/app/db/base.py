# Import all the models, so that Base has them before being
# imported by Alembic or database initialization scripts
from app.db.base_class import Base  # noqa
from app.models.role import Role, RoleEnum  # noqa
from app.models.department import Department  # noqa
from app.models.user import User  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.patient import Patient  # noqa
from app.models.doctor_profile import DoctorProfile  # noqa
from app.models.nurse_profile import NurseProfile, ShiftEnum  # noqa
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType  # noqa
from app.models.opd_token import OpdToken, TokenStatus, TokenPriority  # noqa
from app.models.ward import Ward  # noqa
from app.models.room import Room, RoomType  # noqa
from app.models.bed import Bed, BedStatus  # noqa
from app.models.admission import Admission, AdmissionStatus, DischargeCondition  # noqa
from app.models.bed_transfer import BedTransfer  # noqa
from app.models.emergency_case import EmergencyCase, TriageLevel, ConsciousnessLevel, EmergencyCaseStatus  # noqa
from app.models.lab import LabTest, LabOrder, LabResult, LabResultParameter, LabReport, LabOrderStatus, LabOrderPriority, LabResultFlag, LabReportStatus  # noqa
from app.models.pharmacy import Medicine, MedicineBatch, PharmacyTransaction, Prescription, PrescriptionItem, Dispensing, DispensingItem, PharmacyTransactionType, PrescriptionStatus, PrescriptionItemStatus  # noqa
from app.models.billing import BillingItem, Invoice, InvoiceItem, Payment, BillingCategory, InvoicePaymentStatus, PaymentMethod  # noqa
from app.models.notification import Notification, NotificationType, NotificationPriority  # noqa
from app.models.ai import AIPrediction, AIAlert, AIFeedback, AIDocumentRecord, AIShiftHandover, ModelProviderType, AIRiskLevel, AIAlertSeverity, AIAlertStatus, AIPredictionType, AIAlertType  # noqa
