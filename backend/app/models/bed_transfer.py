from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class BedTransfer(Base):
    __tablename__ = "bed_transfers"

    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id", ondelete="CASCADE"), nullable=False, index=True)
    from_bed_id = Column(Integer, ForeignKey("beds.id", ondelete="RESTRICT"), nullable=False)
    to_bed_id = Column(Integer, ForeignKey("beds.id", ondelete="RESTRICT"), nullable=False)

    transfer_reason = Column(Text, nullable=False)
    transferred_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    transferred_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    admission = relationship("Admission", back_populates="transfers")
    from_bed = relationship("Bed", foreign_keys=[from_bed_id])
    to_bed = relationship("Bed", foreign_keys=[to_bed_id])
    transferred_by = relationship("User", foreign_keys=[transferred_by_id])
