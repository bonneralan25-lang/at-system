from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from supabase import create_client
from datetime import datetime, timezone
from config import get_settings
from models.estimate import EstimateAdjust, EstimateReject
from services.ghl import send_message_to_contact, format_estimate_for_client

router = APIRouter(prefix="/api/estimates", tags=["estimates"])


def get_supabase():
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


@router.get("")
async def list_estimates(
    status: str | None = Query(None),
    service_type: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    sb = get_supabase()
    q = sb.table("estimates").select("*, lead:leads(*)").order("created_at", desc=True).limit(limit)
    if status:
        q = q.eq("status", status)
    if service_type:
        q = q.eq("service_type", service_type)
    res = q.execute()
    return res.data or []


@router.get("/{estimate_id}")
async def get_estimate(estimate_id: str):
    sb = get_supabase()
    res = (
        sb.table("estimates")
        .select("*, lead:leads(*)")
        .eq("id", estimate_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return res.data


@router.post("/{estimate_id}/approve")
async def approve_estimate(estimate_id: str):
    sb = get_supabase()
    res = sb.table("estimates").select("*, lead:leads(*)").eq("id", estimate_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Estimate not found")

    estimate = res.data
    lead = estimate.get("lead") or {}

    now = datetime.now(timezone.utc).isoformat()
    sb.table("estimates").update({
        "status": "approved",
        "approved_at": now,
    }).eq("id", estimate_id).execute()

    sb.table("leads").update({"status": "approved"}).eq("id", estimate["lead_id"]).execute()

    # Send estimate to client via GHL
    contact_id = lead.get("ghl_contact_id")
    if contact_id:
        msg = format_estimate_for_client(estimate, estimate["service_type"])
        sent = send_message_to_contact(contact_id, msg)
        if sent:
            sb.table("leads").update({"status": "sent"}).eq("id", estimate["lead_id"]).execute()

    return {"status": "approved", "estimate_id": estimate_id}


@router.put("/{estimate_id}")
async def adjust_estimate(estimate_id: str, body: EstimateAdjust):
    sb = get_supabase()
    res = sb.table("estimates").select("*").eq("id", estimate_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Estimate not found")

    estimate = res.data
    now = datetime.now(timezone.utc).isoformat()

    update_data = {
        "status": "adjusted",
        "estimate_low": body.estimate_low,
        "estimate_high": body.estimate_high,
        "approved_at": now,
    }
    if body.owner_notes:
        update_data["owner_notes"] = body.owner_notes

    sb.table("estimates").update(update_data).eq("id", estimate_id).execute()
    sb.table("leads").update({"status": "approved"}).eq("id", estimate["lead_id"]).execute()

    # Send adjusted estimate to client
    lead_res = sb.table("leads").select("*").eq("id", estimate["lead_id"]).single().execute()
    lead = lead_res.data or {}
    contact_id = lead.get("ghl_contact_id")
    if contact_id:
        adjusted_estimate = {**estimate, "estimate_low": body.estimate_low, "estimate_high": body.estimate_high}
        msg = format_estimate_for_client(adjusted_estimate, estimate["service_type"])
        sent = send_message_to_contact(contact_id, msg)
        if sent:
            sb.table("leads").update({"status": "sent"}).eq("id", estimate["lead_id"]).execute()

    return {"status": "adjusted", "estimate_id": estimate_id}


@router.post("/{estimate_id}/reject")
async def reject_estimate(estimate_id: str, body: EstimateReject):
    sb = get_supabase()
    res = sb.table("estimates").select("*").eq("id", estimate_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Estimate not found")

    update_data: dict = {"status": "rejected"}
    if body.notes:
        update_data["owner_notes"] = body.notes

    sb.table("estimates").update(update_data).eq("id", estimate_id).execute()
    sb.table("leads").update({"status": "rejected"}).eq("id", res.data["lead_id"]).execute()

    return {"status": "rejected", "estimate_id": estimate_id}
