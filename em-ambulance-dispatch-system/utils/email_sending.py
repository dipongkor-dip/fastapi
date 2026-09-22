import smtplib

from email.message import EmailMessage

from config import settings


def send_email(
    recipient_email: str,
    subject: str,
    body: str,
    attachment=None,
    attachment_name: str | None = None,
):
    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = settings.email_sender
    message["To"] = recipient_email

    message.set_content(body)

    if attachment is not None:
        message.add_attachment(
            attachment,
            maintype="application",
            subtype="pdf",
            filename=attachment_name or "receipt.pdf",
        )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()

        server.login(
            settings.email_sender,
            settings.email_password,
        )

        server.send_message(message)
