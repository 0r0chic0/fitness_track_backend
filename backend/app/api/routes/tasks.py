from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", tags=["tasks"])
def read_all():
    return [{"id": 1, "title": "First Task"}]
