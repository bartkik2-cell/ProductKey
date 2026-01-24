from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import SENDGRID_API_KEY


def send_email(to_email: str, from_email: str, subject: str, html: str):
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)
