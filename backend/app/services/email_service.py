import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from jinja2 import Environment, BaseLoader
import re

from app.core.config import settings


class EmailService:
    """Handles SMTP email sending with tracking pixel injection and link wrapping."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from_name: Optional[str] = None,
        smtp_use_tls: bool = True,
    ) -> None:
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.smtp_username = smtp_username or settings.SMTP_USERNAME
        self.smtp_password = smtp_password or settings.SMTP_PASSWORD
        self.smtp_from_name = smtp_from_name or settings.SMTP_FROM_NAME
        self.smtp_use_tls = smtp_use_tls

    def _inject_tracking_pixel(self, html_body: str, tracking_id: str) -> str:
        """Inject a 1x1 tracking pixel at the end of the email body."""
        pixel_url = f"{settings.BASE_URL}/api/v1/tracking/open/{tracking_id}"
        pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />'
        if "</body>" in html_body:
            return html_body.replace("</body>", f"{pixel}</body>")
        return html_body + pixel

    def _wrap_links(self, html_body: str, email_id: str) -> str:
        """Replace all href links with tracked redirect links."""
        def replace_link(match: re.Match) -> str:
            original_url = match.group(1)
            if "/track/" in original_url or "tracking" in original_url:
                return match.group(0)
            import urllib.parse
            encoded_url = urllib.parse.quote(original_url, safe="")
            tracked_url = f"{settings.BASE_URL}/api/v1/tracking/click/{email_id}?url={encoded_url}"
            return f'href="{tracked_url}"'

        return re.sub(r'href="([^"]+)"', replace_link, html_body)

    def _text_to_html(self, text: str) -> str:
        """Convert plain text email body to basic HTML."""
        html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        paragraphs = html.split("\n\n")
        html_parts = []
        for para in paragraphs:
            if para.strip():
                lines = para.replace("\n", "<br>")
                html_parts.append(f"<p>{lines}</p>")
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
         font-size: 15px; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
  p {{ margin: 0 0 16px 0; }}
  a {{ color: #2563eb; }}
</style>
</head>
<body>
{"".join(html_parts)}
</body>
</html>"""

    def render_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        """Render a Jinja2 template string with variables."""
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        return template.render(**variables)

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
        tracking_id: Optional[str] = None,
        email_id: Optional[str] = None,
        resume_path: Optional[str] = None,
        cc: Optional[list[str]] = None,
    ) -> bool:
        """Send an email via SMTP with optional tracking and resume attachment."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.smtp_from_name} <{self.smtp_username}>"
        msg["To"] = f"{to_name} <{to_email}>"
        if cc:
            msg["Cc"] = ", ".join(cc)

        # Convert body to HTML
        html_body = self._text_to_html(body)

        # Inject tracking
        if tracking_id:
            html_body = self._inject_tracking_pixel(html_body, tracking_id)
        if email_id:
            html_body = self._wrap_links(html_body, email_id)

        # Attach parts
        text_part = MIMEText(body, "plain", "utf-8")
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(text_part)
        msg.attach(html_part)

        # Attach resume if provided
        if resume_path:
            resume_file = Path(resume_path)
            if resume_file.exists():
                with open(resume_file, "rb") as f:
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=resume_file.name,
                )
                msg.attach(attachment)
            else:
                logger.warning(f"Resume file not found: {resume_path}")

        try:
            context = ssl.create_default_context()
            if self.smtp_use_tls:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.smtp_username, [to_email], msg.as_string())
            else:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.smtp_username, [to_email], msg.as_string())
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending to {to_email}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            raise


def get_email_service(user=None) -> EmailService:
    """Factory function to get EmailService, optionally with user-specific SMTP settings."""
    if user and user.smtp_host:
        return EmailService(
            smtp_host=user.smtp_host,
            smtp_port=user.smtp_port,
            smtp_username=user.smtp_username,
            smtp_password=user.smtp_password,
            smtp_from_name=user.smtp_from_name or user.full_name,
            smtp_use_tls=user.smtp_use_tls,
        )
    return EmailService()
