from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Ward(Base):
    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # e.g. "Intensive Care Unit (ICU)"
    code = Column(String(20), nullable=False, unique=True, index=True)  # e.g. "ICU", "CCU", "TRAUMA", "SURGERY"
    description = Column(String(255), nullable=True)
    floor = Column(String(20), nullable=False, default="Floor 2")
    wing = Column(String(20), nullable=False, default="Wing A")
    total_beds = Column(Integer, nullable=False, default=10)
    is_active = Column(Boolean, default=True, nullable=False)

    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    department = relationship("Department", backref="wards")
    rooms = relationship("Room", back_populates="ward", cascade="all, delete-orphan")
    beds = relationship("Bed", back_populates="ward", cascade="all, delete-orphan")
