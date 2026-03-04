from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
from supabase import create_client
from config import get_settings
from datetime import datetime, timezone

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_supabase():
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


class PricingUpdate(BaseModel):
    service_type: str
    config: dict[str, Any]


@router.get("/pricing")
async def get_pricing():
    sb = get_supabase()
    res = sb.table("pricing_config").select("*").execute()
    return res.data or []


@router.put("/pricing")
async def update_pricing(body: PricingUpdate):
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    existing = (
        sb.table("pricing_config")
        .select("id")
        .eq("service_type", body.service_type)
        .execute()
    )

    if existing.data:
        sb.table("pricing_config").update({
            "config": body.config,
            "updated_at": now,
        }).eq("service_type", body.service_type).execute()
    else:
        sb.table("pricing_config").insert({
            "service_type": body.service_type,
            "config": body.config,
            "updated_at": now,
        }).execute()

    return {"status": "saved", "service_type": body.service_type}


@router.get("/stats")
async def get_stats():
    """Dashboard KPI stats."""
    from datetime import timedelta
    sb = get_supabase()
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    pending = sb.table("estimates").select("id", count="exact").eq("status", "pending").execute()
    leads_week = sb.table("leads").select("id", count="exact").gte("created_at", week_ago).execute()
    approved_month = (
        sb.table("estimates")
        .select("id,estimate_low", count="exact")
        .in_("status", ["approved", "adjusted"])
        .gte("approved_at", month_start)
        .execute()
    )

    revenue = sum(r.get("estimate_low", 0) for r in (approved_month.data or []))

    return {
        "pending_estimates": pending.count or 0,
        "leads_this_week": leads_week.count or 0,
        "approved_this_month": approved_month.count or 0,
        "revenue_estimate_this_month": revenue,
    }
