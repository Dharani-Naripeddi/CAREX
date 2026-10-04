from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)

    specialization = Column(String(150), nullable=False, index=True)  # e.g. "Interventional Cardiology"
    qualification = Column(String(150), nullable=False)  # e.g. "MBBS, MD, DM (Cardio)"
    experience_years = Column(Integer, default=5, nullable=False)
    consultation_fee = Column(Float, default=75.0, nullable=False)
    room_number = Column(String(50), nullable=True)  # e.g. "OPD Block B, Suite 204"

    # Schedule and Availability
    availability_days = Column(JSON, default=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], nullable=False)
    available_from = Column(String(10), default="09:00", nullable=False)  # "09:00"
    available_to = Column(String(10), default="17:00", nullable=False)  # "17:00"
    is_available = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", backref="doctor_profile")
    department = relationship("Department", backref="doctors")
