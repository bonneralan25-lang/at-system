"""
Google Geocoding Service
Completes partial addresses (missing zip/city/state) using the Google Geocoding API.
Results are biased to the Houston, TX metro area.
"""
from __future__ import annotations

import re
import logging
import httpx

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def has_zip(address: str) -> bool:
    """Return True if the address string already contains a 5-digit zip code."""
    return bool(re.search(r"\b\d{5}\b", address or ""))


def complete_address(partial: str, api_key: str) -> dict | None:
    """
    Given a partial address (possibly missing zip/city/state), call the Google Geocoding
    API biased to Houston, TX and return the first matching full address.

    Returns:
        {"full_address": "1234 Main St, Houston, TX 77001", "zip_code": "77001"}
    or None if geocoding fails, no result found, or no zip can be resolved.
    """
    if not api_key:
        logger.debug("No GOOGLE_MAPS_API_KEY configured — skipping address autocomplete")
        return None

    if not partial or not partial.strip():
        return None

    # Don't bother if it already has a zip
    if has_zip(partial):
        return None

    # Append Houston hint if the address doesn't already mention it
    query = partial.strip()
    lower = query.lower()
    if "houston" not in lower and ", tx" not in lower and " tx " not in lower:
        query = f"{query}, Houston, TX"

    try:
        resp = httpx.get(
            GEOCODING_URL,
            params={
                "address": query,
                "region": "us",
                "components": "administrative_area:TX|country:US",
                "key": api_key,
            },
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK" or not data.get("results"):
            logger.warning(
                f"Geocoding no results for '{partial}' (queried as '{query}'): "
                f"status={data.get('status')}"
            )
            return None

        result = data["results"][0]
        full_address = result.get("formatted_address", "")

        # Extract zip code from address components
        zip_code = ""
        for comp in result.get("address_components", []):
            if "postal_code" in comp.get("types", []):
                zip_code = comp["long_name"]
                break

        if not zip_code:
            logger.warning(f"Geocoding result has no zip code for '{partial}': {full_address}")
            return None

        logger.info(f"Autocompleted address: '{partial}' → '{full_address}' (zip={zip_code})")
        return {"full_address": full_address, "zip_code": zip_code}

    except httpx.TimeoutException:
        logger.warning(f"Geocoding timeout for '{partial}'")
        return None
    except Exception as e:
        logger.error(f"Geocoding error for '{partial}': {e}")
        return None
