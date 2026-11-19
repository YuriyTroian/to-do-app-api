from typing import Annotated, Optional
from uuid import UUID

# from app.app import app
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.models import Tasks
from app.db import get_async_session

# from sqlmodel import Session, Depends, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, Query, Depends, APIRouter, Header
from fastapi.responses import JSONResponse
from app import idempotency
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from datetime import datetime
import json
from fastapi import Response
from app.cache import cache_get, cache_set, cache_invalidate, cache_stats

router = APIRouter()


# SessionDep = Annotated[Session, Depends(get_async_session)]

@router.post("/tasks/", response_model=TaskOut)
async def create_task(
        task: TaskCreate,
        session: AsyncSession = Depends(get_async_session),
        idempotency_key: Optional[str] = Header(default=None),
):
    fp = None
    if idempotency_key:
        fp = idempotency.fingerprint(task.model_dump())
        replay = await idempotency.begin(idempotency_key, fp)
        if replay is not None:
            return replay  # повторний запит: збережена відповідь, у базу не пишемо

    try:
        db_task = Tasks(**task.dict())
        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)
        await cache_invalidate()
    except Exception:
        if idempotency_key:
            await idempotency.abort(idempotency_key)  # дозволяємо клієнту повторити
        raise

    if idempotency_key:
        body = TaskOut.model_validate(db_task, from_attributes=True).model_dump(mode="json")
        await idempotency.complete(idempotency_key, fp, body, 200)
        return JSONResponse(content=body)
    return db_task


@router.get("/tasks/", response_model=list[TaskOut])
async def get_tasks(
        session: AsyncSession = Depends(get_async_session),
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
):
    cached, key = await cache_get(offset, limit)
    if cached is not None:
        return Response(content=cached, media_type="application/json")

    result = await session.execute(
        select(Tasks).order_by(Tasks.priority.asc()).offset(offset).limit(limit)
    )
    tasks = result.scalars().all()

    payload = json.dumps([
        TaskOut.model_validate(t, from_attributes=True).model_dump(mode="json")
        for t in tasks
    ])
    await cache_set(key, payload)
    return Response(content=payload, media_type="application/json")

@router.get("/cache/stats")
async def get_cache_stats():
    return await cache_stats()

@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: UUID, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Tasks).filter(Tasks.id == task_id)
    )
    task = result.scalars().first()
    # task = session.query(Tasks).filter(Tasks.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
#
@router.delete("/tasks/{task_id}")
async def delete_task(task_id: UUID, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Tasks).filter(Tasks.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await session.delete(task)
    await session.commit()
    await cache_invalidate()
    return {"ok": True}

@router.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: UUID, task_new: TaskUpdate, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Tasks).filter(Tasks.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = task_new.dict(exclude_unset=True)
    for key, value in task_data.items():
        if key == "description":
            if value == "string":
                continue
        if key == "priority":
            if value == 0:
                continue

        setattr(task, key, value)



    # for key, value in task_new.dict().items():
    #     setattr(task, key, value) if value else None

    # task = Tasks(**task_new.dict())
    # session.add(task)


    await session.commit()
    await session.refresh(task)
    await cache_invalidate()
    return task

@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_async_session)):
    # Один агрегатний запит: рахує сама база, у Python повертається один рядок,
    # тож вартість не залежить від кількості записів.
    result = await session.execute(
        select(
            func.count(Tasks.id),
            func.count(Tasks.id).filter(Tasks.is_done.is_(True)),
            func.count(Tasks.id).filter(Tasks.is_done.is_(False)),
        )
    )
    total, complete, pending = result.one()

    return {
        "total": total,
        "complete": complete,
        "pending": pending
    }









