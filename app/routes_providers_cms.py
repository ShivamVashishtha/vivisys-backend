from fastapi import APIRouter, Depends, Query
import httpx

from .deps import get_current_user  # IMPORTANT: use deps (not routes_auth)

router = APIRouter(prefix="/providers/cms", tags=["providers"])

CMS_NPI_URL = "https://npiregistry.cms.hhs.gov/api/"

@router.get("/search")
async def search_providers_cms(
    first_name: str | None = Query(default=None),
    last_name: str | None = Query(default=None),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    postal_code: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    skip: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
):
    params = {
        "version": "2.1",
        "enumeration_type": "NPI-1",
        "limit": limit,
        "skip": skip,
    }
    if first_name: params["first_name"] = first_name
    if last_name: params["last_name"] = last_name
    if city: params["city"] = city
    if state: params["state"] = state
    if postal_code: params["postal_code"] = postal_code

    async with httpx.AsyncClient(timeout=12.0) as client:
        r = await client.get(CMS_NPI_URL, params=params)
        r.raise_for_status()
        data = r.json()

    results = []
    for item in data.get("results", []) or []:
        basic = item.get("basic", {}) or {}
        tax = item.get("taxonomies", []) or []
        addresses = item.get("addresses", []) or []

        loc = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), None) or \
              next((a for a in addresses if a.get("address_purpose") == "MAILING"), None) or {}

        name = " ".join([basic.get("first_name") or "", basic.get("middle_name") or "", basic.get("last_name") or ""]).strip()
        cred = basic.get("credential")
        if cred:
            name = f"{name}, {cred}"

        primary_tax = next((t for t in tax if t.get("primary")), None) or (tax[0] if tax else {})

        results.append({
            "npi": item.get("number"),
            "name": name or basic.get("name") or "—",
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
            "taxonomy": {
                "code": primary_tax.get("code"),
                "desc": primary_tax.get("desc"),
                "primary": primary_tax.get("primary", False),
            },
            "raw": item,
        })

    return {
        "source": "cms_npi_registry",
        "query": params,
        "result_count": data.get("result_count", len(results)),
        "results": results,
    }
