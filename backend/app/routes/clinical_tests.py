from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
import uuid
from datetime import datetime

from app.models.schemas import (
    InitiateUploadRequest, InitiateUploadResponse,
    RefreshUrlRequest, RefreshUrlResponse,
    CompleteUploadRequest, CompleteUploadResponse,
    UploadStatusResponse,
)
from app.models.enums import UploadStatus
from app.dependencies.auth import get_current_patient, get_current_clinician, TokenPayload, get_current_user
from app.config import settings

router = APIRouter()

# ============ ENDPOINT 1: INITIATE UPLOAD ============

@router.post(
    "/clinical-tests/uploads/initiate",
    response_model=InitiateUploadResponse,
    status_code=201,
)
async def initiate_upload(
    request: InitiateUploadRequest,
    idempotency_key: str = Header(...),
    current_patient: str = Depends(get_current_patient),
):
    """
    POST /api/v1/clinical-tests/uploads/initiate
    Crear sesión de subida e obtener URL firmada de GCS
    """
    
    # TODO: Validaciones
    # - MIME type en whitelist
    # - Size ≤ MAX_CLINICAL_FILE_BYTES
    # - SHA-256 válido
    # - Idempotency-Key + client_upload_id = tupla única
    
    # TODO: Crear registro en MongoDB
    # - clinical_test_id (ULID)
    # - upload_id (ULID)
    # - estado = "initiated"
    
    # TODO: Generar URL firmada V4 de GCS
    # - Ruta: private/clinical-tests/{patient_id}/{clinical_test_id}/original
    # - Expiración: 15 minutos
    # - Content-Type forzado
    
    # Por ahora, mock response
    upload_id = f"ctu_{str(uuid.uuid4())[:8]}"
    clinical_test_id = f"ct_{str(uuid.uuid4())[:8]}"
    
    return InitiateUploadResponse(
        upload_id=upload_id,
        clinical_test_id=clinical_test_id,
        status=UploadStatus.INITIATED,
        upload={
            "method": "PUT",
            "signed_url": "https://storage.googleapis.com/mock-url",
            "required_headers": {"Content-Type": request.mime_type},
            "expires_at": datetime.utcnow().isoformat() + "Z",
        }
    )

# ============ ENDPOINT 2: REFRESH URL ============

@router.post(
    "/clinical-tests/uploads/{upload_id}/refresh-url",
    response_model=RefreshUrlResponse,
)
async def refresh_url(
    upload_id: str,
    request: RefreshUrlRequest,
    idempotency_key: str = Header(...),
    current_patient: str = Depends(get_current_patient),
):
    """
    POST /api/v1/clinical-tests/uploads/{upload_id}/refresh-url
    Reemplazar URL firmada expirada sin duplicar registro
    """
    
    # TODO: Validar sesión existe
    # TODO: Validar SHA-256 coincide con initiate
    # TODO: Generar nueva URL firmada
    # TODO: Rate limit (max 10 refrescos por sesión)
    
    return RefreshUrlResponse(
        upload_id=upload_id,
        status=UploadStatus.INITIATED,
        upload={
            "method": "PUT",
            "signed_url": "https://storage.googleapis.com/mock-url-refreshed",
            "required_headers": {"Content-Type": "application/pdf"},
            "expires_at": datetime.utcnow().isoformat() + "Z",
        }
    )

# ============ ENDPOINT 3: COMPLETE UPLOAD ============

@router.post(
    "/clinical-tests/uploads/{upload_id}/complete",
    response_model=CompleteUploadResponse,
)
async def complete_upload(
    upload_id: str,
    request: CompleteUploadRequest,
    idempotency_key: str = Header(...),
    current_patient: str = Depends(get_current_patient),
):
    """
    POST /api/v1/clinical-tests/uploads/{upload_id}/complete
    Señalar que transferencia terminó. Verificar en GCS y encolar validación
    """
    
    # TODO: Verificar objeto existe en GCS (HEAD)
    # TODO: Validar checksum y tamaño coinciden
    # TODO: Persistir registro en MongoDB (transacción)
    # TODO: Emitir job de escaneo de malware (outbox pattern)
    # TODO: IMPORTANTE: local_file_can_be_deleted SIEMPRE = false
    
    clinical_test_id = "ct_01J8ZC2F41"  # Mock
    
    return CompleteUploadResponse(
        clinical_test_id=clinical_test_id,
        upload_id=upload_id,
        status=UploadStatus.PROCESSING,
        local_file_can_be_deleted=False,
        status_url=f"/api/v1/clinical-tests/uploads/{upload_id}/status",
    )

# ============ ENDPOINT 4: UPLOAD STATUS ============

@router.get(
    "/clinical-tests/uploads/{upload_id}/status",
    response_model=UploadStatusResponse,
)
async def get_upload_status(
    upload_id: str,
    current_patient: str = Depends(get_current_patient),
):
    """
    GET /api/v1/clinical-tests/uploads/{upload_id}/status
    Consultar resultado del procesamiento. Retorna local_file_can_be_deleted SOLO en ready_for_review
    """
    
    # TODO: Leer estado del job de validación/escaneo
    # TODO: Retornar estado de malware_scan y mime_validation
    # TODO: local_file_can_be_deleted = true SOLO si status = ready_for_review
    
    return UploadStatusResponse(
        clinical_test_id="ct_01J8ZC2F41",
        upload_id=upload_id,
        status=UploadStatus.PROCESSING,
        processing={
            "malware_scan": "pending",
            "mime_validation": "pending",
        },
        local_file_can_be_deleted=False,
        error=None,
        completed_at=None,
    )

# ============ ENDPOINTS 5-11 TODO ============

@router.get("/clinical-tests")
async def list_clinical_tests(
    status: Optional[str] = None,
    test_type: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
    current_patient: str = Depends(get_current_patient),
):
    """ENDPOINT #5: GET /api/v1/clinical-tests - Listar resultados de paciente"""
    return {"items": [], "next_cursor": None}

@router.get("/clinical-tests/{clinical_test_id}")
async def get_clinical_test(
    clinical_test_id: str,
    user = Depends(get_current_user),
):
    """ENDPOINT #6: GET /api/v1/clinical-tests/{id} - Obtener un resultado"""
    return {"clinical_test_id": clinical_test_id}

@router.patch("/clinical-tests/{clinical_test_id}")
async def edit_clinical_test(
    clinical_test_id: str,
    current_patient: str = Depends(get_current_patient),
):
    """ENDPOINT #7: PATCH /api/v1/clinical-tests/{id} - Editar metadatos"""
    return {"clinical_test_id": clinical_test_id, "updated_at": datetime.utcnow().isoformat()}

@router.delete("/clinical-tests/{clinical_test_id}")
async def delete_clinical_test(
    clinical_test_id: str,
    current_patient: str = Depends(get_current_patient),
):
    """ENDPOINT #8: DELETE /api/v1/clinical-tests/{id} - Soft delete"""
    return {"clinical_test_id": clinical_test_id, "status": "deleted"}

@router.post("/clinical-tests/{clinical_test_id}/download-url")
async def create_download_url(
    clinical_test_id: str,
    user = Depends(get_current_user),
):
    """ENDPOINT #9: POST /api/v1/clinical-tests/{id}/download-url - URL segura de descarga"""
    return {"url": "https://storage.googleapis.com/mock", "expires_at": datetime.utcnow().isoformat()}

@router.get("/patients/{patient_id}/clinical-tests")
async def list_patient_clinical_tests(
    patient_id: str,
    current_clinician: str = Depends(get_current_clinician),
):
    """ENDPOINT #10: GET /api/v1/patients/{patient_id}/clinical-tests - Listar para clínico"""
    return {"items": [], "next_cursor": None}

@router.patch("/clinical-tests/{clinical_test_id}/review")
async def review_clinical_test(
    clinical_test_id: str,
    current_clinician: str = Depends(get_current_clinician),
):
    """ENDPOINT #11: PATCH /api/v1/clinical-tests/{id}/review - Revisión clínica"""
    return {"clinical_test_id": clinical_test_id, "review": {"status": "reviewed"}}