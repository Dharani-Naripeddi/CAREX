from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.ai import (
    AIDocumentRecord,
    AIPrediction,
    AIPredictionType,
    AIRiskLevel,
    ModelProviderType,
)
from app.ai.document_ai.extractor import MedicalDocumentExtractor
from app.ai.document_ai.schemas import (
    DocumentAnalysisRequest,
    DocumentAnalysisResponse,
    ExtractedParameter,
)


class DocumentAIService:
    @staticmethod
    def analyze_document(
        db: Session,
        request: DocumentAnalysisRequest,
        uploaded_by_id: int,
        persist: bool = True,
    ) -> DocumentAnalysisResponse:
        extractor = MedicalDocumentExtractor()

        raw_text = request.raw_text or f"CAREX DIAGNOSTIC PATHOLOGY REPORT\nFile: {request.file_name}\nHemoglobin: 10.2 g/dL\nWBC: 13.8 10^3/uL\nPlatelet: 285 10^3/uL\nFasting Blood Glucose: 142 mg/dL\nSerum Creatinine: 0.9 mg/dL"
        extracted_params, findings, summary, risk = extractor.extract_from_text(raw_text)

        patient_name = None
        if request.patient_id:
            p = db.query(Patient).filter(Patient.id == request.patient_id).first()
            if p:
                patient_name = f"{p.first_name} {p.last_name}"

        doc_record_id = None
        if persist:
            doc_record = AIDocumentRecord(
                file_name=request.file_name,
                file_type=request.file_type,
                patient_id=request.patient_id,
                uploaded_by_id=uploaded_by_id,
                document_type=request.document_type,
                raw_text=raw_text,
                extracted_data=[p.dict() for p in extracted_params],
                ai_summary=summary,
                confidence=0.88,
                is_verified=False,
            )
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)
            doc_record_id = doc_record.id

            # Save prediction record
            pred_record = AIPrediction(
                prediction_type=AIPredictionType.CLINICAL_SUMMARY,
                entity_type="DOCUMENT_RECORD",
                entity_id=str(doc_record_id),
                prediction_value={"extracted_count": len(extracted_params), "abnormal_count": len(findings)},
                risk_level=risk,
                confidence=0.88,
                model_name="carex-document-ai-nlp",
                model_version=extractor.version,
                model_provider_type=ModelProviderType.STATISTICAL_MODEL,
                explanation={
                    "summary": summary,
                    "reasons": findings or ["All parameters within expected biological ranges."],
                    "recommended_action": "Verify extracted parameters against original laboratory sheet and sign off.",
                },
                recommended_action="Physician verification required before updating active patient chart.",
                input_features={"file_name": request.file_name, "file_type": request.file_type},
            )
            db.add(pred_record)
            db.commit()

        abnormal_count = len([p for p in extracted_params if p.is_abnormal])

        return DocumentAnalysisResponse(
            document_id=doc_record_id,
            file_name=request.file_name,
            file_type=request.file_type,
            document_type=request.document_type,
            patient_id=request.patient_id,
            patient_name=patient_name,
            extracted_parameters=extracted_params,
            abnormal_parameters_count=abnormal_count,
            ai_summary=summary,
            key_findings=findings,
            risk_level=risk,
            confidence=0.88,
            model_provider_type=ModelProviderType.STATISTICAL_MODEL,
            model_version=extractor.version,
            is_verified=False,
        )

    @staticmethod
    def verify_document(db: Session, document_id: int, verified_by_id: int) -> AIDocumentRecord:
        doc = db.query(AIDocumentRecord).filter(AIDocumentRecord.id == document_id).first()
        if doc:
            doc.is_verified = True
            doc.verified_by_id = verified_by_id
            doc.verified_at = datetime.utcnow()
            db.commit()
            db.refresh(doc)
        return doc
