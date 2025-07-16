import json
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime
from datetime import datetime, date


class Base(DeclarativeBase):
    pass

class Tasks(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(30))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, unique=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        # date = self.created_at.date()
        dict1 = {"title": self.title,
                "description": self.description,
                "priority": self.priority,
                "is_done": self.is_done,
                "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")}
        return f'{dict1}'
        # return f"{date}"
# 'created_at': datetime.date(2025, 5, 1)