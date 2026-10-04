import datetime
import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    date_of_birth: datetime.date
    gender: str
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    allergies: List[str] = []
    current_medications: List[str] = []
    medical_history: List[str] = []

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            return None
        v = v.strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Please provide a valid email address.")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} is required.")
        v = v.strip()
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} must contain alphabets only.")
        if len(v) < 2:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} must be at least 2 characters.")
        if len(v) > 50:
            raise ValueError(f"{info.field_name.replace('_', ' ').title()} must not exceed 50 characters.")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: datetime.date):
        if v > datetime.date.today():
            raise ValueError("Date of birth cannot be in the future.")
        if v < datetime.date(1900, 1, 1):
            raise ValueError("Please provide a valid date of birth (after 1900).")
        return v

    @field_validator("emergency_contact_name")
    @classmethod
    def validate_emergency_name(cls, v: Optional[str]):
        if not v or not v.strip():
            return None
        v = v.strip()
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Emergency contact name must contain alphabets only.")
        if len(v) < 2:
            raise ValueError("Emergency contact name must be at least 2 characters.")
        if len(v) > 50:
            raise ValueError("Emergency contact name must not exceed 50 characters.")
        return v

    @field_validator("emergency_contact_relation")
    @classmethod
    def validate_emergency_relation(cls, v: Optional[str]):
        if not v or not v.strip():
            return None
        v = v.strip()
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Emergency contact relation must contain alphabets only.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Mobile number is required.")
        v = v.strip()
        if not re.match(r"^\d{10}$", v):
            raise ValueError("Mobile number must be numbers only and exactly 10 digits.")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]):
        if not v or not v.strip():
            return None
        v = v.strip()
        if not re.match(r"^\d{10}$", v):
            raise ValueError("Emergency contact phone must be numbers only and exactly 10 digits.")
        return v


class PatientCreate(PatientBase):
    user_id: Optional[int] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime.date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    medical_history: Optional[List[str]] = None

    @field_validator("email", mode="before")
    @classmethod
    def clean_email_update(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            return None
        v = v.strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Please provide a valid email address.")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_update(cls, v: Optional[str], info):
        if v is not None:
            v = v.strip()
            if not v or not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError(f"{info.field_name.replace('_', ' ').title()} must contain alphabets only.")
            if len(v) < 2:
                raise ValueError(f"{info.field_name.replace('_', ' ').title()} must be at least 2 characters.")
            if len(v) > 50:
                raise ValueError(f"{info.field_name.replace('_', ' ').title()} must not exceed 50 characters.")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob_update(cls, v: Optional[datetime.date]):
        if v is not None:
            if v > datetime.date.today():
                raise ValueError("Date of birth cannot be in the future.")
            if v < datetime.date(1900, 1, 1):
                raise ValueError("Please provide a valid date of birth (after 1900).")
        return v

    @field_validator("emergency_contact_name")
    @classmethod
    def validate_emergency_name_update(cls, v: Optional[str]):
        if v is not None and v.strip():
            v = v.strip()
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError("Emergency contact name must contain alphabets only.")
            if len(v) < 2:
                raise ValueError("Emergency contact name must be at least 2 characters.")
            if len(v) > 50:
                raise ValueError("Emergency contact name must not exceed 50 characters.")
        return v

    @field_validator("emergency_contact_relation")
    @classmethod
    def validate_emergency_relation_update(cls, v: Optional[str]):
        if v is not None and v.strip():
            v = v.strip()
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError("Emergency contact relation must contain alphabets only.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone_update(cls, v: Optional[str]):
        if v is not None and v.strip():
            v = v.strip()
            if not re.match(r"^\d{10}$", v):
                raise ValueError("Mobile number must be numbers only and exactly 10 digits.")
            return v
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone_update(cls, v: Optional[str]):
        if v is not None and v.strip():
            v = v.strip()
            if not re.match(r"^\d{10}$", v):
                raise ValueError("Emergency contact phone must be numbers only and exactly 10 digits.")
            return v
        return v


class PatientResponse(PatientBase):
    id: int
    mrn: str
    full_name: str
    age: int
    user_id: Optional[int] = None
    registered_by_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

