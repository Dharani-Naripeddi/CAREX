import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(50), unique=True, index=True, nullable=False)  # Medical Record Number, e.g. CRX-2026-0001
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)  # Male, Female, Other
    blood_group = Column(String(10), nullable=True)  # A+, A-, B+, B-, AB+, AB-, O+, O-
    address = Column(Text, nullable=True)

    # Emergency Contact
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)

    # Clinical Baseline Lists (Stored as JSON Arrays)
    allergies = Column(JSON, default=list, nullable=False)  # e.g. ["Penicillin", "Latex", "Peanuts"]
    current_medications = Column(JSON, default=list, nullable=False)  # e.g. ["Atorvastatin 20mg OD", "Metformin 500mg BD"]
    medical_history = Column(JSON, default=list, nullable=False)  # e.g. ["Type 2 Diabetes (2020)", "Hypertension (2018)"]

    # Account Linkages
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    registered_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    registered_by = relationship("User", foreign_keys=[registered_by_id])
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    tokens = relationship("OpdToken", back_populates="patient", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        today = datetime.date.today()
        if not self.date_of_birth:
            return 0
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
