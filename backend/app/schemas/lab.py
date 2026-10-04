import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict
from app.models.lab import (
    LabOrderStatus,
    LabOrderPriority,
    LabResultFlag,
    LabReportStatus,
)


# Lab Test Schemas
class LabTestParameterDef(BaseModel):
    name: str
    unit: Optional[str] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None
    text_range: Optional[str] = None


class LabTestBase(BaseModel):
    code: str
    name: str
    category: str = "Hematology"
    description: Optional[str] = None
    sample_type: str = "Whole Blood (EDTA)"
    normal_range: Optional[str] = None
    unit: Optional[str] = None
    price: float = 0.0
    is_active: bool = True
    parameters: List[Dict[str, Any]] = []


class LabTestCreate(LabTestBase):
    department_id: Optional[int] = None


class LabTestUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    sample_type: Optional[str] = None
    normal_range: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    parameters: Optional[List[Dict[str, Any]]] = None


class LabTestResponse(LabTestBase):
    id: int
    department_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Lab Result Parameter Schemas
class LabResultParameterInput(BaseModel):
    parameter_name: str
    result_value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[LabResultFlag] = None
    is_critical: Optional[bool] = False


class LabResultParameterResponse(BaseModel):
    id: int
    parameter_name: str
    result_value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: LabResultFlag
    is_critical: bool

    model_config = ConfigDict(from_attributes=True)


# Lab Result Schemas
class LabResultEntryRequest(BaseModel):
    result_summary: Optional[str] = None
    technician_notes: Optional[str] = None
    parameters: List[LabResultParameterInput]
    is_abnormal: Optional[bool] = False
    is_critical: Optional[bool] = False


class LabResultResponse(BaseModel):
    id: int
    order_id: int
    patient_id: int
    technician_id: int
    technician_name: Optional[str] = None
    result_summary: Optional[str] = None
    technician_notes: Optional[str] = None
    is_abnormal: bool
    is_critical: bool
    created_at: datetime.datetime
    parameters: List[LabResultParameterResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Lab Report Schemas
class LabReportResponse(BaseModel):
    id: int
    report_number: str
    order_id: int
    lab_result_id: int
    patient_id: int
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    doctor_id: int
    doctor_name: Optional[str] = None
    technician_id: int
    technician_name: Optional[str] = None
    verified_by_id: Optional[int] = None
    verified_by_name: Optional[str] = None
    report_date: datetime.datetime
    status: LabReportStatus
    test_name: Optional[str] = None
    test_code: Optional[str] = None
    sample_type: Optional[str] = None
    clinical_impression: Optional[str] = None
    conclusion: Optional[str] = None
    print_html: Optional[str] = None
    parameters: List[LabResultParameterResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Lab Order Schemas
class LabOrderCreate(BaseModel):
    patient_id: int
    test_id: int
    priority: LabOrderPriority = LabOrderPriority.NORMAL
    clinical_notes: Optional[str] = None
    sample_type: Optional[str] = None
    admission_id: Optional[int] = None
    emergency_case_id: Optional[int] = None


class LabOrderResponse(BaseModel):
    id: int
    order_number: str
    patient_id: int
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    
    doctor_id: int
    doctor_name: Optional[str] = None
    
    test_id: int
    test_name: Optional[str] = None
    test_code: Optional[str] = None
    test_category: Optional[str] = None
    test_price: Optional[float] = None
    
    admission_id: Optional[int] = None
    emergency_case_id: Optional[int] = None
    
    priority: LabOrderPriority
    status: LabOrderStatus
    
    clinical_notes: Optional[str] = None
    sample_type: Optional[str] = None
    
    order_date: datetime.datetime
    sample_collected_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    verified_at: Optional[datetime.datetime] = None
    
    result: Optional[LabResultResponse] = None
    report_id: Optional[int] = None
    report_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LabWorkloadSummary(BaseModel):
    pending_count: int = 0
    sample_collected_count: int = 0
    in_progress_count: int = 0
    completed_count: int = 0
    verified_count: int = 0
    urgent_pending_count: int = 0
    today_total_orders: int = 0
