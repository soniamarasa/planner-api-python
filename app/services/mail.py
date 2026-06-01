from email.message import EmailMessage
import smtplib

from app.core.config import settings


def send_email(email: str, user: str, subject: str, link: str) -> None:
    if not all([settings.host, settings.port_mail, settings.user, settings.password_mail]):
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.user
    message["To"] = email
    message.set_content(link)
    message.add_alternative(
        (
            "<div style='color: black; font-family: Trebuchet MS;'>"
            f"<h2 style='color: #C49877'>Hello, {user}.</h2>"
            "<p>You have requested to reset your password.</p>"
            "<p>Click on the button below to create a new password.</p>"
            f"<a href='{link}'><button style='background-color:#EEBD1E;border:none;color:white;padding:10px 25px;text-align:center;text-decoration:none;display:inline-block;font-size:1.2rem;border-radius:8px;cursor:pointer !important;'>Set Password</button></a>"
            "<p><small>If you haven't requested a password reset, please ignore this email.</small></p>"
            "<h3>Weekly Planner</h3></div>"
        ),
        subtype="html",
    )

    with smtplib.SMTP_SSL(settings.host, settings.port_mail) as server:
        server.login(settings.user, settings.password_mail)
        server.send_message(message)
