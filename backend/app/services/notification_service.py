"""SMTP delivery for real human-support handoffs and AI case report emails.

All SMTP values come from deployment configuration. A missing mail provider is
reported as `not_configured`; it never becomes a fake successful notification.
"""
import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Literal, Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

DeliveryStatus = Literal["sent", "not_configured", "failed"]


def _send_message_sync(message: EmailMessage) -> None:
    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=ssl.create_default_context(), timeout=15) as client:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
            client.send_message(message)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as client:
        client.ehlo()
        if settings.SMTP_USE_TLS:
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
        client.send_message(message)


def _send_mime_sync(msg: MIMEMultipart) -> None:
    """Send a MIME multipart message (for HTML emails)."""
    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=ssl.create_default_context(), timeout=15) as client:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
            client.sendmail(msg["From"], msg["To"], msg.as_string())
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as client:
        client.ehlo()
        if settings.SMTP_USE_TLS:
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
        client.sendmail(msg["From"], msg["To"], msg.as_string())


async def send_handoff_email(subject: str, body: str) -> DeliveryStatus:
    """Notify the configured human-support inbox of a handoff."""
    if not settings.smtp_configured:
        return "not_configured"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME or settings.APP_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = settings.SUPPORT_HANDOFF_EMAIL
    message.set_content(body)
    try:
        await asyncio.to_thread(_send_message_sync, message)
        logger.info("Human handoff email sent", recipient=settings.SUPPORT_HANDOFF_EMAIL)
        return "sent"
    except Exception as exc:
        logger.error("Human handoff email failed", error=str(exc))
        return "failed"


async def send_case_report_email(
    case_id: str,
    report: Dict[str, Any],
    evidence_urls: List[str],
    case_data: Dict[str, Any],
    approve_url: str,
    reject_url: str,
) -> DeliveryStatus:
    """
    Send a rich HTML forensic report email for an analysed case.

    Includes:
    - AI-generated recommendation and confidence
    - Per-image analysis summaries
    - Evidence image thumbnails (linked)
    - One-click Approve / Reject action buttons
    - Full case metadata
    """
    if not settings.smtp_configured:
        logger.warning(
            "SMTP not configured — skipping case report email",
            case_id=case_id,
            tip="Set SMTP_HOST, SMTP_FROM_EMAIL, SUPPORT_HANDOFF_EMAIL in .env",
        )
        return "not_configured"

    subject = _build_subject(case_id, report)
    html_body = _build_html_report(
        case_id=case_id,
        report=report,
        evidence_urls=evidence_urls,
        case_data=case_data,
        approve_url=approve_url,
        reject_url=reject_url,
    )
    plain_body = _build_plain_text(case_id, report, approve_url, reject_url)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME or settings.APP_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = settings.SUPPORT_HANDOFF_EMAIL
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        await asyncio.to_thread(_send_mime_sync, msg)
        logger.info("Case report email sent", case_id=case_id, recipient=settings.SUPPORT_HANDOFF_EMAIL)
        return "sent"
    except Exception as exc:
        logger.error("Case report email failed", case_id=case_id, error=str(exc))
        return "failed"


# ─────────────────────────────────────────────────────────────────────────────
#  EMAIL CONTENT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_subject(case_id: str, report: Dict[str, Any]) -> str:
    rec = report.get("overall_recommendation", "ESCALATE")
    conf = report.get("confidence", 0)
    emoji = {"APPROVE": "✅", "REJECT": "🚫", "ESCALATE": "⚠️"}.get(rec, "🔍")
    return f"{emoji} ArgusCX Evidence Report — {case_id} — AI recommends {rec} ({conf:.0%} confidence)"


def _build_plain_text(
    case_id: str,
    report: Dict[str, Any],
    approve_url: str,
    reject_url: str,
) -> str:
    rec = report.get("overall_recommendation", "ESCALATE")
    conf = report.get("confidence", 0)
    summary = report.get("summary", "No summary available.")
    findings = "\n".join(f"  • {f}" for f in report.get("key_findings", []))

    return f"""ArgusCX — AI Evidence Analysis Report
Case: {case_id}

AI RECOMMENDATION: {rec} (Confidence: {conf:.0%})

Summary:
{summary}

Key Findings:
{findings or "  No specific findings recorded."}

--- ACTION REQUIRED ---
Approve this case:  {approve_url}
Reject this case:   {reject_url}

This report was generated automatically by ArgusCX Vision Analysis.
"""


def _build_html_report(
    case_id: str,
    report: Dict[str, Any],
    evidence_urls: List[str],
    case_data: Dict[str, Any],
    approve_url: str,
    reject_url: str,
) -> str:
    rec = report.get("overall_recommendation", "ESCALATE")
    conf = report.get("confidence", 0)
    summary = report.get("summary", "")
    findings = report.get("key_findings", [])
    per_image = report.get("per_image", [])

    rec_color = {"APPROVE": "#10b981", "REJECT": "#ef4444", "ESCALATE": "#f59e0b"}.get(rec, "#6b7280")
    rec_bg = {"APPROVE": "#d1fae5", "REJECT": "#fee2e2", "ESCALATE": "#fef3c7"}.get(rec, "#f3f4f6")
    rec_icon = {"APPROVE": "✅", "REJECT": "🚫", "ESCALATE": "⚠️"}.get(rec, "🔍")

    session_data = case_data.get("session", {}) or {}
    order_id = session_data.get("order_id") or case_data.get("order_id") or "N/A"
    customer = session_data.get("customer_ref") or "N/A"
    category = session_data.get("category") or "N/A"
    return_reason = session_data.get("return_reason") or "N/A"
    claim_text = session_data.get("claim_text") or "N/A"
    image_count = report.get("image_count", len(evidence_urls))

    # Build per-image cards
    image_cards_html = ""
    for img in per_image:
        img_url = img.get("url", "")
        img_rec = img.get("overall_recommendation", "ESCALATE")
        img_conf = float(img.get("confidence", 0))
        img_summary = img.get("summary", "")
        img_color = {"APPROVE": "#10b981", "REJECT": "#ef4444", "ESCALATE": "#f59e0b"}.get(img_rec, "#6b7280")
        img_icon = {"APPROVE": "✅", "REJECT": "🚫", "ESCALATE": "⚠️"}.get(img_rec, "🔍")

        # Condition / fraud sub-findings
        condition = img.get("product_condition", {})
        fraud = img.get("fraud_indicators", {})
        authenticity = img.get("authenticity", {})
        claim_cons = img.get("claim_consistency", {})

        sub_rows = []
        if condition:
            sub_rows.append(f"<tr><td style='padding:4px 8px;color:#6b7280;font-size:12px;'>Damage detected</td><td style='padding:4px 8px;font-size:12px;'>{'Yes ⚠️' if condition.get('damage_detected') else 'No ✅'}</td></tr>")
        if authenticity:
            sub_rows.append(f"<tr><td style='padding:4px 8px;color:#6b7280;font-size:12px;'>Serial visible</td><td style='padding:4px 8px;font-size:12px;'>{'Yes ✅' if authenticity.get('serial_visible') else 'No ⚠️'}</td></tr>")
        if claim_cons:
            sub_rows.append(f"<tr><td style='padding:4px 8px;color:#6b7280;font-size:12px;'>Claim consistent</td><td style='padding:4px 8px;font-size:12px;'>{'Yes ✅' if claim_cons.get('consistent') else 'No 🚫'}</td></tr>")
        if fraud:
            sub_rows.append(f"<tr><td style='padding:4px 8px;color:#6b7280;font-size:12px;'>Fraud indicators</td><td style='padding:4px 8px;font-size:12px;'>{'Yes 🚫' if any([fraud.get('ai_generated_likely'), fraud.get('staging_signs'), fraud.get('image_manipulation_detected')]) else 'None ✅'}</td></tr>")

        img_thumb = f'<img src="{img_url}" alt="Evidence" style="width:100%;max-height:200px;object-fit:cover;border-radius:8px;display:block;" />' if img_url else '<div style="width:100%;height:100px;background:#f3f4f6;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#9ca3af;font-size:12px;">No image</div>'

        image_cards_html += f"""
        <div style="border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:16px;">
          <div style="display:flex;align-items:stretch;">
            <div style="width:180px;min-width:180px;background:#f9fafb;">
              <a href="{img_url}" target="_blank">{img_thumb}</a>
            </div>
            <div style="flex:1;padding:16px;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-size:13px;color:#6b7280;">Image {img.get('index', '?')}</span>
                <span style="background:{rec_bg if img_rec == rec else '#f3f4f6'};color:{img_color};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;">{img_icon} {img_rec} ({img_conf:.0%})</span>
              </div>
              <p style="font-size:13px;color:#374151;line-height:1.5;margin:0 0 10px 0;">{img_summary}</p>
              <table style="border-collapse:collapse;width:100%;">
                {"".join(sub_rows)}
              </table>
            </div>
          </div>
        </div>
        """

    # Build findings list
    findings_html = ""
    for f in findings:
        findings_html += f'<li style="margin-bottom:6px;color:#374151;font-size:14px;">{f}</li>'
    if not findings_html:
        findings_html = '<li style="color:#9ca3af;font-size:14px;">No specific findings recorded.</li>'

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ArgusCX Evidence Report — {case_id}</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#f3f4f6;">
  <div style="max-width:700px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#4338ca 100%);padding:32px 40px;">
      <div style="font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;">🔍 ArgusCX</div>
      <div style="font-size:14px;color:rgba(255,255,255,0.7);margin-top:4px;">AI Evidence Forensic Report</div>
      <div style="margin-top:16px;font-size:13px;color:rgba(255,255,255,0.6);font-family:monospace;">Case ID: {case_id}</div>
    </div>

    <div style="padding:32px 40px;">

      <!-- AI Recommendation Banner -->
      <div style="background:{rec_bg};border:2px solid {rec_color}30;border-radius:12px;padding:20px 24px;margin-bottom:28px;text-align:center;">
        <div style="font-size:36px;margin-bottom:8px;">{rec_icon}</div>
        <div style="font-size:22px;font-weight:700;color:{rec_color};">AI RECOMMENDS: {rec}</div>
        <div style="font-size:14px;color:#6b7280;margin-top:4px;">Confidence: <strong style="color:{rec_color};">{conf:.0%}</strong> · {image_count} image(s) analysed</div>
        <p style="font-size:14px;color:#374151;line-height:1.6;margin:12px 0 0 0;">{summary}</p>
      </div>

      <!-- Case Metadata -->
      <div style="background:#f9fafb;border-radius:12px;padding:20px 24px;margin-bottom:28px;">
        <div style="font-size:12px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;">Case Details</div>
        <table style="width:100%;border-collapse:collapse;">
          <tr>
            <td style="padding:6px 0;color:#6b7280;font-size:13px;width:140px;">Order ID</td>
            <td style="padding:6px 0;color:#111827;font-size:13px;font-weight:500;">{order_id}</td>
            <td style="padding:6px 0;color:#6b7280;font-size:13px;width:140px;">Customer</td>
            <td style="padding:6px 0;color:#111827;font-size:13px;font-weight:500;">{customer}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6b7280;font-size:13px;">Category</td>
            <td style="padding:6px 0;color:#111827;font-size:13px;font-weight:500;">{category}</td>
            <td style="padding:6px 0;color:#6b7280;font-size:13px;">Return Reason</td>
            <td style="padding:6px 0;color:#111827;font-size:13px;font-weight:500;">{return_reason}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6b7280;font-size:13px;vertical-align:top;">Claim Text</td>
            <td colspan="3" style="padding:6px 0;color:#111827;font-size:13px;font-style:italic;">"{claim_text}"</td>
          </tr>
        </table>
      </div>

      <!-- Key Findings -->
      <div style="margin-bottom:28px;">
        <div style="font-size:16px;font-weight:600;color:#111827;margin-bottom:12px;">🔎 Key Findings</div>
        <ul style="margin:0;padding-left:20px;">
          {findings_html}
        </ul>
      </div>

      <!-- Per-Image Analysis -->
      {f'<div style="margin-bottom:28px;"><div style="font-size:16px;font-weight:600;color:#111827;margin-bottom:16px;">📸 Evidence Analysis ({image_count} image(s))</div>{image_cards_html}</div>' if image_cards_html else ''}

      <!-- Action Buttons -->
      <div style="background:#f9fafb;border-radius:12px;padding:24px;margin-bottom:16px;text-align:center;">
        <div style="font-size:15px;font-weight:600;color:#111827;margin-bottom:6px;">⚡ Take Action</div>
        <p style="font-size:13px;color:#6b7280;margin:0 0 20px 0;">Review the analysis above and make your decision. This action will be logged.</p>
        <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;">
          <a href="{approve_url}"
             style="display:inline-block;padding:14px 36px;background:#10b981;color:#fff;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;letter-spacing:0.01em;">
            ✅ Approve Case
          </a>
          <a href="{reject_url}"
             style="display:inline-block;padding:14px 36px;background:#ef4444;color:#fff;text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;letter-spacing:0.01em;">
            🚫 Reject Case
          </a>
        </div>
      </div>

      <p style="font-size:11px;color:#d1d5db;text-align:center;margin:0;">
        Secured by ArgusCX · This email was generated automatically · Action links are single-use
      </p>
    </div>
  </div>
</body>
</html>"""
