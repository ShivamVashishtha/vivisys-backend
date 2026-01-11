# app/fhir_store.py
from __future__ import annotations
from typing import Any, Dict, Tuple
from uuid import uuid4
import asyncio

# key: (resourceType, id) -> resource json
_STORE: Dict[Tuple[str, str], Dict[str, Any]] = {}
_LOCK = asyncio.Lock()

async def create(resource_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    rt = resource_type.strip()
    if not rt:
        raise ValueError("resource_type is required")

    # Create a shallow copy and normalize resourceType
    res = dict(payload or {})
    res["resourceType"] = rt

    # Ensure id
    rid = str(res.get("id") or "").strip()
    if not rid:
        rid = str(uuid4())
        res["id"] = rid

    async with _LOCK:
        _STORE[(rt, rid)] = res

    return res

async def read(resource_type: str, resource_id: str) -> Dict[str, Any] | None:
    rt = resource_type.strip()
    rid = resource_id.strip()
    async with _LOCK:
        return _STORE.get((rt, rid))
