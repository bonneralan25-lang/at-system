"""
GHL Contact Sync — imports existing GHL contacts as leads.
POST /api/sync/ghl
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks

from config import get_settings
from services.ghl import get_contacts, parse_webhook_payload
from api.webhooks import get_supabase, get_pricing_config, process_lead

router = APIRouter()
logger = logging.getLogger(__name__)

# Custom fields that indicate the contact came from our fence/pressure wash form
FORM_FIELD_KEYS = {
    "fence_height", "fence_age", "previously_stained",
    "service_timeline", "additional_services", "additional_notes",
    "surface_type", "square_footage",
}


@router.post("/api/sync/ghl")
async def sync_ghl_contacts(background_tasks: BackgroundTasks):
    """
    Pull existing GHL contacts and import them as leads.
    - Skips contacts with no fence/pressure wash form fields (irrelevant contacts)
    - Skips contacts already in the DB (deduped by ghl_contact_id)
    - Queues estimate calculation for each newly imported lead
    """
    settings = get_settings()
    sb = get_supabase()

    # Fetch existing contact IDs to avoid duplicates
    existing_res = sb.table("leads").select("ghl_contact_id").execute()
    existing_ids = {r["ghl_contact_id"] for r in (existing_res.data or [])}

    # Pull contacts from GHL
    contacts = get_contacts(settings.ghl_location_id)
    logger.info(f"GHL sync: fetched {len(contacts)} contacts")

    imported = 0
    skipped_duplicate = 0
    skipped_no_fields = 0
    errors = 0

    for contact in contacts:
        contact_id = contact.get("id", "")

        if not contact_id:
            continue

        if contact_id in existing_ids:
            skipped_duplicate += 1
            continue

        # Normalize using the same parser as the webhook
        lead_data = parse_webhook_payload(contact)

        # Only import contacts who have at least one form field filled in
        if not lead_data["form_data"]:
            skipped_no_fields += 1
            continue

        lead_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        lead_row = {
            "id":             lead_id,
            "ghl_contact_id": contact_id,
            "service_type":   lead_data["service_type"],
            "status":         "new",
            "address":        lead_data["address"],
            "form_data":      lead_data["form_data"],
            "created_at":     now,
        }

        try:
            sb.table("leads").insert(lead_row).execute()
            background_tasks.add_task(process_lead, lead_id, lead_data)
            existing_ids.add(contact_id)
            imported += 1
            logger.info(f"Synced contact {contact_id} → lead {lead_id}")
        except Exception as e:
            logger.error(f"Failed to import contact {contact_id}: {e}")
            errors += 1

    return {
        "status":             "done",
        "total_fetched":      len(contacts),
        "imported":           imported,
        "skipped_duplicate":  skipped_duplicate,
        "skipped_no_fields":  skipped_no_fields,
        "errors":             errors,
    }


@router.get("/api/sync/ghl/preview")
async def preview_ghl_contacts():
    """
    Preview what would be synced — returns contact count without importing.
    Useful for checking the API connection before doing a full sync.
    """
    settings = get_settings()
    contacts = get_contacts(settings.ghl_location_id, max_contacts=100)

    with_fields = sum(
        1 for c in contacts
        if parse_webhook_payload(c)["form_data"]
    )

    return {
        "status":            "ok",
        "total_contacts":    len(contacts),
        "with_form_fields":  with_fields,
        "sample_names": [
            f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
            for c in contacts[:5]
        ],
    }
