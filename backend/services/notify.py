"""
Notification service — SMS via Twilio, Email via Resend.
Designed to be extended with APNs push notifications for the future iPhone app.
"""

import logging
from config import get_settings

logger = logging.getLogger(__name__)


def _format_estimate_message(estimate: dict, lead: dict) -> str:
    low = estimate.get("estimate_low", 0)
    high = estimate.get("estimate_high", 0)
    service = estimate.get("service_type", "").replace("_", " ").title()
    address = lead.get("address", "Unknown address")
    estimate_id = estimate.get("id", "")
    settings = get_settings()
    link = f"{settings.frontend_url}/estimates/{estimate_id}"
    return (
        f"New {service} estimate pending your approval.\n"
        f"Address: {address}\n"
        f"Range: ${low:,.0f}–${high:,.0f}\n"
        f"Review: {link}"
    )


def send_sms_to_owner(estimate: dict, lead: dict) -> bool:
    settings = get_settings()
    if not all([settings.twilio_account_sid, settings.twilio_auth_token,
                settings.twilio_from_number, settings.owner_phone]):
        logger.warning("Twilio not configured — skipping SMS")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        message = _format_estimate_message(estimate, lead)
        client.messages.create(
            body=message,
            from_=settings.twilio_from_number,
            to=settings.owner_phone,
        )
        logger.info(f"SMS sent to owner for estimate {estimate.get('id')}")
        return True
    except Exception as e:
        logger.error(f"SMS failed: {e}")
        return False


def send_email_to_owner(estimate: dict, lead: dict) -> bool:
    settings = get_settings()
    if not all([settings.resend_api_key, settings.owner_email]):
        logger.warning("Resend not configured — skipping email")
        return False

    try:
        import resend
        resend.api_key = settings.resend_api_key

        low = estimate.get("estimate_low", 0)
        high = estimate.get("estimate_high", 0)
        service = estimate.get("service_type", "").replace("_", " ").title()
        address = lead.get("address", "Unknown address")
        estimate_id = estimate.get("id", "")
        link = f"{settings.frontend_url}/estimates/{estimate_id}"

        resend.Emails.send({
            "from": f"Dashboard <noreply@{settings.owner_email.split('@')[-1]}>",
            "to": settings.owner_email,
            "subject": f"[Action Required] New {service} Estimate — {address}",
            "html": f"""
            <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
              <h2 style="color:#1d4ed8">New Estimate Pending Approval</h2>
              <table style="width:100%;border-collapse:collapse">
                <tr><td style="padding:8px 0;color:#6b7280">Service</td>
                    <td style="padding:8px 0;font-weight:600">{service}</td></tr>
                <tr><td style="padding:8px 0;color:#6b7280">Address</td>
                    <td style="padding:8px 0;font-weight:600">{address}</td></tr>
                <tr><td style="padding:8px 0;color:#6b7280">Estimate Range</td>
                    <td style="padding:8px 0;font-weight:600;font-size:1.2em">${low:,.0f} – ${high:,.0f}</td></tr>
              </table>
              <a href="{link}" style="display:inline-block;margin-top:20px;padding:12px 24px;
                background:#1d4ed8;color:white;text-decoration:none;border-radius:6px;font-weight:600">
                Review & Approve Estimate
              </a>
            </div>
            """,
        })
        logger.info(f"Email sent to owner for estimate {estimate_id}")
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False


def notify_owner(estimate: dict, lead: dict) -> None:
    """Fire-and-forget: send SMS + email to owner."""
    send_sms_to_owner(estimate, lead)
    send_email_to_owner(estimate, lead)
