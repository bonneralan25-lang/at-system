"""
GoHighLevel API v2 client.
Handles fetching contact info and sending messages back to leads.
"""
from __future__ import annotations

import httpx
import logging
from config import get_settings

logger = logging.getLogger(__name__)
GHL_BASE = "https://services.leadconnectorhq.com"


def _headers() -> dict:
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.ghl_api_key}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }


def get_contacts(location_id: str, max_contacts: int = 500) -> list[dict]:
    """
    Fetch existing contacts from a GHL location (paginated, up to max_contacts).
    Used for the one-time sync of historical leads.
    """
    all_contacts: list[dict] = []
    limit = 100
    skip = 0

    while len(all_contacts) < max_contacts:
        try:
            r = httpx.get(
                f"{GHL_BASE}/contacts/",
                headers=_headers(),
                params={"locationId": location_id, "limit": limit, "skip": skip},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            contacts = data.get("contacts", [])
            all_contacts.extend(contacts)
            if len(contacts) < limit:
                break
            skip += limit
        except Exception as e:
            logger.error(f"GHL get_contacts failed (skip={skip}): {e}")
            break

    return all_contacts


def get_contact(contact_id: str) -> dict | None:
    try:
        r = httpx.get(f"{GHL_BASE}/contacts/{contact_id}", headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json().get("contact")
    except Exception as e:
        logger.error(f"GHL get_contact failed: {e}")
        return None


def send_message_to_contact(contact_id: str, message: str) -> bool:
    """Send an SMS/email message to a contact via GHL."""
    settings = get_settings()
    try:
        payload = {
            "type": "SMS",
            "contactId": contact_id,
            "message": message,
            "locationId": settings.ghl_location_id,
        }
        r = httpx.post(f"{GHL_BASE}/conversations/messages", headers=_headers(),
                       json=payload, timeout=10)
        r.raise_for_status()
        logger.info(f"GHL message sent to contact {contact_id}")
        return True
    except Exception as e:
        logger.error(f"GHL send_message failed: {e}")
        return False


def format_estimate_for_client(estimate: dict, service_type: str) -> str:
    """Format the approved estimate as an SMS to send to the lead via GHL."""
    low = estimate.get("estimate_low", 0)
    high = estimate.get("estimate_high", 0)
    service = "Fence Restoration" if service_type == "fence_staining" else "Pressure Washing"
    return (
        f"Hi! Thanks for reaching out about your {service} project. "
        f"Based on the details you shared, our estimate is "
        f"${low:,.0f}–${high:,.0f}. "
        f"This is a preliminary range — our team will be in touch shortly to confirm the details "
        f"and send your full proposal. Any questions? Reply here anytime!"
    )


def parse_webhook_payload(payload: dict) -> dict:
    """
    Normalize a GHL webhook payload into our standard lead format.

    GHL sends contact custom fields in the `customFields` array as:
      [{"key": "fence_height", "value": "6ft standard"}, ...]

    Field keys match the snake_case names created in GHL:
      service_timeline, fence_height, fence_age, previously_stained,
      additional_services, additional_notes
    """
    raw_custom = payload.get("customFields", []) or payload.get("customData", {})

    if isinstance(raw_custom, list):
        fields = {
            f.get("key", f.get("id", "")): f.get("value", f.get("fieldValue", ""))
            for f in raw_custom
            if f.get("key") or f.get("id")
        }
    elif isinstance(raw_custom, dict):
        fields = raw_custom
    else:
        fields = {}

    # Map GHL field keys → our internal form_data keys
    form_data: dict = {
        "service_timeline":    fields.get("service_timeline", ""),
        "fence_height":        fields.get("fence_height", ""),
        "fence_age":           fields.get("fence_age", ""),
        "previously_stained":  fields.get("previously_stained", ""),
        "additional_services": fields.get("additional_services", ""),
        "additional_notes":    fields.get("additional_notes", ""),
    }
    form_data = {k: v for k, v in form_data.items() if v and str(v).strip()}

    # Service type detection
    tags = payload.get("tags", []) or []
    service_raw = (
        payload.get("serviceType", "")
        or payload.get("service_type", "")
        or fields.get("service_type", "")
        or " ".join(tags)
    ).lower()

    service_type = (
        "pressure_washing"
        if ("pressure" in service_raw or "wash" in service_raw)
        else "fence_staining"
    )

    # Build address + extract zip code
    address_parts = [
        payload.get("address1", ""),
        payload.get("city", ""),
        payload.get("state", ""),
        payload.get("postalCode", ""),
    ]
    address = " ".join(p for p in address_parts if p).strip()
    zip_code = str(payload.get("postalCode", "") or "").strip()[:5]

    first = payload.get("firstName", "") or payload.get("first_name", "")
    last  = payload.get("lastName", "")  or payload.get("last_name", "")

    return {
        "ghl_contact_id": payload.get("contactId", payload.get("id", "")),
        "service_type":   service_type,
        "address":        address,
        "zip_code":       zip_code,
        "contact_name":   f"{first} {last}".strip(),
        "contact_phone":  payload.get("phone", ""),
        "contact_email":  payload.get("email", ""),
        "form_data":      form_data,
        "raw_payload":    payload,
    }
