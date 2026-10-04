from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.logging import logger


class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        entity: str,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Create an audit log record for compliance."""
        try:
            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                entity=entity,
                entity_id=str(entity_id) if entity_id else None,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            logger.info(f"Audit: [{action}] on {entity}:{entity_id} by user {user_id}")
            return audit_entry
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to write audit log: {e}")
            raise e
