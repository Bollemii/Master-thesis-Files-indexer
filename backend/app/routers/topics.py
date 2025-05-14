from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas import TopicsList
from app.models import User
from app.utils.security import get_current_user
from app.database.topics import get_all_topics

router = APIRouter()

@router.get("/topics", response_model=TopicsList, status_code=200, tags=["topics"])
async def get_topics(_: User = Depends(get_current_user),):
    """
    Get a list of topics.
    """
    try:
        topics = get_all_topics()

        return {"items": topics}
    except Exception as e:
        print(f"Error 500 - Listing topics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
