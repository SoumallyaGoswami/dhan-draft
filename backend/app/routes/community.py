"""Community chat module routes."""
from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/messages")
async def get_community_messages(user=Depends(get_current_user)):
    """Get recent community chat messages."""
    db = get_db()
    
    messages = await db.community_chat.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    # Reverse to show oldest first
    return success_response(data=list(reversed(messages)))
