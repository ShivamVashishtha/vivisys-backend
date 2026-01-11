from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
import httpx

router = APIRouter(prefix="/hospitals", tags=["hospitals"])

CMS_NPI_BASE = "https://npiregistry.cms.hhs.gov/api/"
CMS_API_VERSION = "2.1"


def _pick_practice_location(addresses: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    # NPPES returns multiple addresses; we prefer "practice" if present.
    # If not found, fall back to first.
    if not addresses:
        return None
    for a in addresses:
        if (a.get("address_purpose") or "").lower() == "location":
            return a
    return addresses[0]


def _normalize_org_result(r: Dict[str, Any]) -> Dict[str, Any]:
    basic = r.get("basic") or {}
    addresses = r.get("addresses") or []
    loc = _pick_practice_location(addresses) or {}

    name = (
        basic.get("organization_name")
        or basic.get("name")
        or basic.get("authorized_official_organization_name")
        or "Unknown"
    )

    return {
        "npi": r.get("number"),
        "name": name,
        "enumeration_type": r.get("enumeration_type"),
        "status": basic.get("status"),
        "last_updated": basic.get("last_updated"),
        "address": {
            "line1": loc.get("address_1"),
            "line2": loc.get("address_2"),
            "city": loc.get("city"),
            "state": loc.get("state"),
            "postal_code": loc.get("postal_code"),
            "country_code": loc.get("country_code"),
            "telephone_number": loc.get("telephone_number"),
        },
        "taxonomies": r.get("taxonomies") or [],
        "raw": r,  # optional: keep full record for debugging; remove if you prefer
    }


@router.get("/cms/search")
async def search_hospitals_cms(
    name: str = Query(..., min_length=2, description="Organization (hospital) name, e.g. 'Northwestern'"),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None, min_length=2, max_length=2),
    postal_code: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=200, description="Max 200 per CMS API"),
    skip: int = Query(0, ge=0, le=1000, description="Max 1000 per CMS API"),
) -> Dict[str, Any]:
    """
    Search organizations (NPI-2) from the CMS NPPES NPI Registry API.
    """
    params: Dict[str, Any] = {
        "version": CMS_API_VERSION,
        "enumeration_type": "NPI-2",
        "organization_name": name,
        "limit": limit,
        "skip": skip,
    }
    if city:
        params["city"] = city
    if state:
        params["state"] = state
    if postal_code:
        params["postal_code"] = postal_code

    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(CMS_NPI_BASE, params=params)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"CMS NPI Registry request failed: {str(e)}")

    data = resp.json()
    results = data.get("results") or []
    normalized = [_normalize_org_result(x) for x in results]

    return {
        "source": "cms_npi_registry",
        "query": params,
        "result_count": data.get("result_count", len(normalized)),
        "results": normalized,
    }
