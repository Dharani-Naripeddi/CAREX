from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.ai import ModelProviderType, AIRiskLevel
from app.ai.base import StandardAIExplanation


class PharmacyPredictionRequest(BaseModel):
    medicine_id: Optional[int] = None
    days_history: int = 30


class ConsumptionTrendPoint(BaseModel):
    date_label: str
    units_dispensed: int
    daily_average: float
    stock_level_at_end_of_day: int


class MedicineDepletionForecast(BaseModel):
    medicine_id: int
    medicine_code: str
    medicine_name: str
    category: str
    current_stock: int
    reorder_level: int
    max_stock_level: int
    
    avg_daily_consumption: float
    estimated_days_remaining: float
    predicted_depletion_date: Optional[date] = None
    recommended_reorder_quantity: int
    
    risk_level: AIRiskLevel
    expiry_risk_category: Optional[str] = None
    confidence: Optional[float] = None
    model_provider_type: ModelProviderType
    
    explanation: StandardAIExplanation
    recommended_action: str


class PharmacyPredictionResponse(BaseModel):
    total_medicines_analyzed: int
    critical_depletion_count: int
    high_depletion_count: int
    total_stock_value: float
    
    top_depletion_risks: List[MedicineDepletionForecast] = Field(default_factory=list)
    selected_medicine_forecast: Optional[MedicineDepletionForecast] = None
    consumption_trend_chart: List[ConsumptionTrendPoint] = Field(default_factory=list)
    
    overall_risk_level: AIRiskLevel
    model_provider_type: ModelProviderType
    model_version: str
    alert_triggered: bool = False
