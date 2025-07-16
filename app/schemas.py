from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int

class TaskOut(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int
    is_done: bool
    created_at: datetime

    class Config:
        orm_mode = True

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    priority: Optional[int] = None
    is_done: Optional[bool] = None






