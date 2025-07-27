from typing import Annotated

# from app.app import app
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.models import Tasks
from app.db import get_async_session

# from sqlmodel import Session, Depends, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, Query, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from datetime import datetime


router = APIRouter()


# SessionDep = Annotated[Session, Depends(get_async_session)]

@router.post("/tasks/", response_model=TaskOut)
async def create_task(task: TaskCreate, session: AsyncSession = Depends(get_async_session)):
    db_task = Tasks(**task.dict())
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task


@router.get("/tasks/", response_model=list[TaskOut])
async def get_tasks(
        session: AsyncSession = Depends(get_async_session),
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
):

    result = await session.execute(
        select(Tasks).order_by(Tasks.priority.asc()).offset(offset).limit(limit)
    )
    tasks = result.scalars().all()


    return tasks

@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id, session: AsyncSession = Depends(get_async_session)):
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
async def delete_task(task_id, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Tasks).filter(Tasks.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await session.delete(task)
    await session.commit()
    return {"ok": True}

@router.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id, task_new: TaskUpdate, session: AsyncSession = Depends(get_async_session)):
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
    return task

@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_async_session)):

    #Total
    result_total = await session.execute(
        select(Tasks)
    )
    tasks_total = result_total.scalars().all()

    #Completed
    result_completed = await session.execute(
        select(Tasks).filter(Tasks.is_done == True)
    )
    tasks_completed = result_completed.scalars().all()

    #Pending
    result_pending = await session.execute(
        select(Tasks).filter(Tasks.is_done == False)
    )
    tasks_pending = result_pending.scalars().all()

    return {
        "total": len(tasks_total),
        "complete": len(tasks_completed),
        "pending": len(tasks_pending)
    }









