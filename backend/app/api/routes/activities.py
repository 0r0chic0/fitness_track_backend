import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Activity, ActivityCreate, ActivityPublic, ActivitiesPublic, ActivityUpdate, Message

router = APIRouter(prefix="/activities", tags=["activities"])

@router.get("/", response_model=ActivitiesPublic)
def read_activities(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Activity)
        count = session.exec(count_statement).one()
        statement = select(Activity).offset(skip).limit(limit)
        activities = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Activity)
            .where(Activity.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Activity)
            .where(Activity.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        activities = session.exec(statement).all()

    return ActivitiesPublic(data=activities, count=count)


@router.get("/{id}", response_model=ActivityPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get activity by ID.
    """
    activity = session.get(Activity, id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not current_user.is_superuser and (activity.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return activity


@router.post("/", response_model=ActivityPublic)
def create_activity(
    *, session: SessionDep, current_user: CurrentUser, activity_in: ActivityCreate
) -> Any:
    """
    Create new item.
    """
    activity = Activity.model_validate(activity_in, update={"owner_id": current_user.id})
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


@router.put("/{id}", response_model=ActivityPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    activity_in: ActivityUpdate,
) -> Any:
    """
    Update an item.
    """
    activity = session.get(Activity, id)
    if not activity:
        raise HTTPException(status_code=404, detail="activity not found")
    if not current_user.is_superuser and (activity.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = activity_in.model_dump(exclude_unset=True)
    activity.sqlmodel_update(update_dict)
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    activity = session.get(Activity, id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not current_user.is_superuser and (activity.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(activity)
    session.commit()
    return Message(message="Activity deleted successfully")
