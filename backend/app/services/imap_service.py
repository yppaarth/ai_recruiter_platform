from typing import List, Dict, Optional
from datetime import datetime, timezone
from loguru import logger
from app.core.config import settings

try:
    from imap_tools import MailBox, AND
    IMAP_AVAILABLE = True
except ImportError:
    IMAP_AVAILABLE = False
    logger.warning("imap-tools not available, reply detection disabled")


class IMAPService:
    """Detect email replies via IMAP."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = True,
    ) -> None:
        self.host = host or settings.IMAP_HOST
        self.port = port or settings.IMAP_PORT
        self.username = username or settings.IMAP_USERNAME
        self.password = password or settings.IMAP_PASSWORD
        self.use_ssl = use_ssl

    def fetch_replies(
        self,
        since_date: Optional[datetime] = None,
        folder: str = "INBOX",
    ) -> List[Dict]:
        """Fetch emails from inbox and return reply candidates."""
        if not IMAP_AVAILABLE:
            logger.warning("IMAP tools not available")
            return []

        if not self.username or not self.password:
            logger.warning("IMAP credentials not configured")
            return []

        replies = []
        try:
            with MailBox(self.host).login(self.username, self.password, initial_folder=folder) as mailbox:
                criteria = AND(seen=False)
                if since_date:
                    criteria = AND(date_gte=since_date.date(), seen=False)

                for msg in mailbox.fetch(criteria, mark_seen=False):
                    reply = {
                        "message_id": msg.uid,
                        "from_email": msg.from_,
                        "subject": msg.subject or "",
                        "body_preview": (msg.text or msg.html or "")[:500],
                        "received_at": msg.date or datetime.now(timezone.utc),
                    }
                    replies.append(reply)

        except Exception as e:
            logger.error(f"IMAP fetch error: {e}")

        return replies


imap_service = IMAPService()
