# app/routes_fhir.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any, Dict

from .fhir_store import create as store_create, read as store_read

router = APIRouter(prefix="/fhir", tags=["fhir"])

@router.post("/{resource_type}")
async def create_resource(resource_type: str, payload: Dict[str, Any]):
    """
    Minimal mock FHIR create endpoint.
    Accepts POST /fhir/Immunization (etc) and returns a created resource with an id.
    """
    # be lenient: allow missing resourceType, but if present it must match
    incoming_rt = (payload or {}).get("resourceType")
    if incoming_rt and str(incoming_rt) != resource_type:
        raise HTTPException(
            status_code=400,
            detail=f"resourceType mismatch: body has {incoming_rt}, URL has {resource_type}",
        )

    try:
        created = await store_create(resource_type, payload or {})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return created

@router.get("/{resource_type}/{resource_id}")
async def get_resource(resource_type: str, resource_id: str):
    res = await store_read(resource_type, resource_id)
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")
    return res
