import logging

import aiosmtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> None:
    if not settings.EMAIL_ENABLED:
        logger.info("EMAIL (dev mode) To: %s | Subject: %s | Body: %s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        start_tls=True,
    )


async def send_prospect_confirmation(email: str, first_name: str) -> None:
    await send_email(
        to=email,
        subject="We received your inquiry",
        body=(
            f"Hi {first_name},\n\n"
            "Thank you for your interest in our legal services. "
            "An attorney will review your submission and reach out shortly.\n\n"
            "Best regards,\nThe Legal Team"
        ),
    )


async def send_attorney_notification(
    first_name: str, last_name: str, email: str
) -> None:
    await send_email(
        to=settings.ATTORNEY_EMAIL,
        subject=f"New lead: {first_name} {last_name}",
        body=(
            f"A new lead has been submitted:\n\n"
            f"Name: {first_name} {last_name}\n"
            f"Email: {email}\n\n"
            "Please log in to the dashboard to review."
        ),
    )
