from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from supabase import create_client
from config import get_settings

router = APIRouter(prefix="/api/leads", tags=["leads"])


def get_supabase():
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


@router.get("")
async def list_leads(
    service_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    sb = get_supabase()
    q = sb.table("leads").select("*").order("created_at", desc=True).limit(limit)
    if service_type:
        q = q.eq("service_type", service_type)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    return res.data or []


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    sb = get_supabase()
    res = sb.table("leads").select("*").eq("id", lead_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead = res.data

    est_res = (
        sb.table("estimates")
        .select("*")
        .eq("lead_id", lead_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if est_res.data:
        lead["estimate"] = est_res.data[0]

    return lead
