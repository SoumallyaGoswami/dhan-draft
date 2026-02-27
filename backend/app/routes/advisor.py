"""AI Advisor module routes."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from ..models.schemas import AdvisorQueryInput
from ..services.auth import get_current_user
from ..services.advisor import generate_advice
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/analyze")
async def analyze_portfolio(inp: AdvisorQueryInput, user=Depends(get_current_user)):
    """Get AI advisor analysis."""
    db = get_db()
    
    # Get user's assets
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    
    # Generate advice
    advice = generate_advice(assets, user)
    
    # Save to chat history
    record = {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "query": inp.query,
        "response": advice,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_history.insert_one(record)
    
    return success_response(data=advice)


@router.get("/history")
async def get_advisor_history(user=Depends(get_current_user)):
    """Get AI advisor conversation history."""
    db = get_db()
    
    history = await db.chat_history.find(
        {"userId": user["id"]},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(50)
    
    return success_response(data=history)
