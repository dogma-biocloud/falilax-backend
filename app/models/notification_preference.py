from __future__ import annotations

from sqlalchemy import Integer, String, Boolean, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class NotificationPreference(Base):
    """
    User control to prevent panic/spam:
    - user chooses channels
    - user chooses minimum tier to notify
    """
    __tablename__ = "notification_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    min_tier: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'orange'"))  # notify only orange/red by default

    created_at: Mapped[str] = mapped_column(server_default=text("now()"))