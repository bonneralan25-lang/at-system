"""Public proposal API — no auth required. Used by customer-facing booking page."""
import logging
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from db import get_db
from config import get_settings
from services.ghl import send_message_to_contact
from services.google_calendar import create_calendar_event
from services.notify import send_booking_confirmation_to_customer

router = APIRouter(prefix="/api/proposal", tags=["proposals"])
logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    selected_tier: str
    booked_at: str
    contact_email: str | None = None
    selected_color: str | None = None
    color_mode: str = "gallery"
    hoa_colors: list | None = None
    custom_color: str | None = None


class BookingRequest(BaseModel):
    selected_tier: str          # "essential" | "signature" | "legacy"
    booked_at: str              # ISO datetime string from customer
    contact_email: str | None = None
    selected_color: str | None = None
    color_mode: str = "gallery" # gallery | hoa_only | hoa_approved | custom
    hoa_colors: list | None = None
    custom_color: str | None = None
    stripe_session_id: str | None = None


@router.get("/{token}")
async def get_proposal(token: str):
    """Public endpoint — returns proposal data for the customer booking page."""
    db = get_db()
    result = db.table("proposals").select("*").eq("token", token).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal = result.data
    if proposal["status"] == "booked":
        return {
            "status": "booked",
            "token": token,
            "booked_at": proposal.get("booked_at"),
            "selected_tier": proposal.get("selected_tier"),
        }

    is_preview = proposal["status"] == "preview"

    # Fetch estimate + lead for pricing and customer info
    est_result = db.table("estimates").select("*").eq("id", proposal["estimate_id"]).single().execute()
    if not est_result.data:
        raise HTTPException(status_code=404, detail="Estimate not found")
    estimate = est_result.data

    lead_result = db.table("leads").select("*").eq("id", proposal["lead_id"]).single().execute()
    lead = lead_result.data or {}

    tiers = (estimate.get("inputs") or {}).get("_tiers") or {}

    # Mark as viewed if still in 'sent' state (not for preview)
    if proposal["status"] == "sent":
        db.table("proposals").update({"status": "viewed"}).eq("token", token).execute()

    inputs = estimate.get("inputs") or {}
    return {
        "status": "preview" if is_preview else "viewed",
        "token": token,
        "customer_name": lead.get("contact_name") or "",
        "address": lead.get("address") or "",
        "service_type": estimate.get("service_type", "fence_staining"),
        "previously_stained": inputs.get("previously_stained") or "No",
        "tiers": {
            "essential": float(tiers.get("essential") or 0),
            "signature": float(tiers.get("signature") or 0),
            "legacy":    float(tiers.get("legacy") or 0),
        },
    }


@router.post("/{token}/create-checkout")
async def create_checkout(token: str, body: CheckoutRequest):
    db = get_db()
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payment not configured")

    result = db.table("proposals").select("*").eq("token", token).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if result.data["status"] == "booked":
        raise HTTPException(status_code=409, detail="Already booked")
    if body.selected_tier not in ("essential", "signature", "legacy"):
        raise HTTPException(status_code=400, detail="Invalid tier")
    try:
        datetime.fromisoformat(body.booked_at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booked_at")

    # Store pending booking data
    db.table("proposals").update({
        "pending_booking": {
            "selected_tier": body.selected_tier,
            "booked_at": body.booked_at,
            "contact_email": body.contact_email,
            "selected_color": body.selected_color,
            "color_mode": body.color_mode,
            "hoa_colors": body.hoa_colors,
            "custom_color": body.custom_color,
        }
    }).eq("token", token).execute()

    import stripe as stripe_lib
    stripe_lib.api_key = settings.stripe_secret_key
    session = stripe_lib.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": 5000,
                "product_data": {"name": "Fence Restoration Deposit", "description": "Refundable if we cancel"},
            },
            "quantity": 1,
        }],
        success_url=f"{settings.frontend_url}/proposal/{token}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.frontend_url}/proposal/{token}",
    )
    return {"checkout_url": session.url}


@router.post("/{token}/book")
async def book_proposal(token: str, body: BookingRequest):
    """Customer submits their tier choice + date. Creates calendar event, notifies Alan."""
    db = get_db()
    settings = get_settings()

    result = db.table("proposals").select("*").eq("token", token).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal = result.data
    if proposal["status"] == "booked":
        raise HTTPException(status_code=409, detail="This proposal has already been booked")

    # If coming from Stripe redirect, verify payment and load pending booking data
    if body.stripe_session_id:
        settings_inner = get_settings()
        if not settings_inner.stripe_secret_key:
            raise HTTPException(status_code=503, detail="Payment not configured")
        import stripe as stripe_lib
        stripe_lib.api_key = settings_inner.stripe_secret_key
        try:
            session = stripe_lib.checkout.Session.retrieve(body.stripe_session_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not verify payment: {e}")
        if session.payment_status != "paid":
            raise HTTPException(status_code=400, detail="Payment not completed")
        # Load pending booking from DB
        pending_result = db.table("proposals").select("pending_booking").eq("token", token).single().execute()
        pending = (pending_result.data or {}).get("pending_booking") or {}
        body.selected_tier = pending.get("selected_tier") or body.selected_tier
        body.booked_at = pending.get("booked_at") or body.booked_at
        body.contact_email = pending.get("contact_email")
        body.selected_color = pending.get("selected_color")
        body.color_mode = pending.get("color_mode", "gallery")
        body.hoa_colors = pending.get("hoa_colors")
        body.custom_color = pending.get("custom_color")

    if body.selected_tier not in ("essential", "signature", "legacy"):
        raise HTTPException(status_code=400, detail="Invalid tier")

    # Parse booked_at
    try:
        booked_dt = datetime.fromisoformat(body.booked_at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booked_at datetime")

    # Fetch lead + estimate for context
    lead_result = db.table("leads").select("*").eq("id", proposal["lead_id"]).single().execute()
    lead = lead_result.data or {}
    est_result = db.table("estimates").select("*").eq("id", proposal["estimate_id"]).single().execute()
    estimate = est_result.data or {}
    tiers = (estimate.get("inputs") or {}).get("_tiers") or {}

    customer_name = lead.get("contact_name") or "Customer"
    address = lead.get("address") or ""
    tier_label = body.selected_tier.capitalize()
    tier_price = tiers.get(body.selected_tier, 0)
    date_str = booked_dt.strftime("%A, %B %-d at %-I:%M %p")

    # Build color display string for calendar/SMS
    color_display = ""
    if body.color_mode == "gallery" and body.selected_color:
        color_display = body.selected_color
    elif body.color_mode == "hoa_only" and body.hoa_colors:
        color_display = f"HOA multi-select: {', '.join(str(c) for c in body.hoa_colors)}"
    elif body.color_mode == "hoa_approved":
        color_display = f"HOA Approved: {body.custom_color or 'TBD'}"
    elif body.color_mode == "custom":
        color_display = f"Custom: {body.custom_color or 'TBD'}"

    # Create Google Calendar event
    summary = f"Fence Staining — {customer_name} ({tier_label})"
    description = (
        f"Customer: {customer_name}\n"
        f"Address: {address}\n"
        f"Package: {tier_label} — ${tier_price:,.2f}\n"
        f"Color: {color_display or 'Not specified'}\n"
        f"Phone: {lead.get('contact_phone') or 'N/A'}\n"
        f"Booked via proposal link"
    )
    calendar_event_id = create_calendar_event(
        summary=summary,
        description=description,
        location=address,
        start_dt=booked_dt,
        duration_hours=4,
        credentials_json=settings.google_calendar_credentials_json,
        calendar_id=settings.google_calendar_id,
    )

    # Notify Alan via GHL SMS
    if settings.owner_ghl_contact_id:
        alan_msg = (
            f"📅 New Booking!\n"
            f"Customer: {customer_name}\n"
            f"Package: {tier_label} (${tier_price:,.0f})\n"
            f"Color: {color_display or 'Not specified'}\n"
            f"Date: {date_str}\n"
            f"Address: {address}"
        )
        sent = send_message_to_contact(settings.owner_ghl_contact_id, alan_msg)
        if not sent:
            logger.warning("Failed to send booking notification to Alan via GHL")
    else:
        logger.warning("OWNER_GHL_CONTACT_ID not set — Alan not notified")

    # Send booking confirmation to customer
    if body.contact_email:
        send_booking_confirmation_to_customer(
            to_email=body.contact_email,
            customer_name=customer_name,
            tier_label=tier_label,
            tier_price=tier_price,
            color_display=color_display or "Not specified",
            date_str=date_str,
            address=address,
        )

    # Update proposal row
    db.table("proposals").update({
        "status": "booked",
        "selected_tier": body.selected_tier,
        "booked_at": booked_dt.isoformat(),
        "calendar_event_id": calendar_event_id,
        "selected_color": body.selected_color,
        "color_mode": body.color_mode,
        "hoa_colors": body.hoa_colors,
        "custom_color": body.custom_color,
        "stripe_session_id": body.stripe_session_id,
        "deposit_paid": bool(body.stripe_session_id),
    }).eq("token", token).execute()

    logger.info(f"Proposal {token} booked: {tier_label} on {date_str} for {customer_name}")

    return {"status": "booked", "booked_at": booked_dt.isoformat(), "selected_tier": body.selected_tier}
