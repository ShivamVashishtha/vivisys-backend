import httpx

async def fetch_fhir_resource(base_url: str, resource_type: str, resource_id: str):
    url = f"{base_url.rstrip('/')}/{resource_type}/{resource_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, headers={"Accept": "application/fhir+json"})

    if r.status_code == 404:
        # return a structured "missing" response instead of raising
        return {
            "resourceType": resource_type,
            "id": resource_id,
            "_error": {
                "status": 404,
                "message": "Resource not found on FHIR server",
                "url": url,
            },
        }

    # for other errors, still raise
    r.raise_for_status()
    return r.json()
