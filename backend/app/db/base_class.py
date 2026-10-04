import datetime
from typing import Any
from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy import Column, DateTime, Integer


@as_declarative()
class Base:
    id: Any
    __name__: str

    # Automatically generate __tablename__ from class name in lowercase
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
