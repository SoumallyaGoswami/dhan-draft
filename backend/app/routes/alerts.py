"""Alerts module routes."""
import uuid
import math
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query

from ..models.schemas import MarkAlertReadInput
from ..services.auth import get_current_user
from ..services.market import analyze_sentiment, calculate_impact_score
from ..database import get_db
from ..utils.responses import success_response
from ..websockets.managers import alert_manager

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def get_alerts(
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    """Get alerts with pagination."""
    db = get_db()
    
    skip = (page - 1) * limit
    
    # Get paginated alerts
    alerts = await db.alerts.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get total count
    total = await db.alerts.count_documents({})
    unread = sum(1 for a in alerts if not a.get("is_read"))
    
    return success_response(data={
        "alerts": alerts,
        "unread_count": unread,
        "page": page,
        "total": total,
        "pages": math.ceil(total / limit) if total > 0 else 0
    })


@router.post("/mark-read")
async def mark_alert_read(inp: MarkAlertReadInput, user=Depends(get_current_user)):
    """Mark specific alert as read."""
    db = get_db()
    
    await db.alerts.update_one(
        {"id": inp.alertId},
        {"$set": {"is_read": True}}
    )
    
    return success_response(message="Alert marked as read")


@router.post("/mark-all-read")
async def mark_all_alerts_read(user=Depends(get_current_user)):
    """Mark all alerts as read."""
    db = get_db()
    
    await db.alerts.update_many(
        {"is_read": False},
        {"$set": {"is_read": True}}
    )
    
    return success_response(message="All alerts marked as read")


@router.post("/generate")
async def generate_alerts_from_news(user=Depends(get_current_user)):
    """Generate alerts from high-impact news."""
    db = get_db()
    
    news_items = await db.news.find({}, {"_id": 0}).to_list(50)
    alerts_created = 0
    
    for news_item in news_items:
        impact = calculate_impact_score(news_item)
        
        if impact >= 75:
            # Check if alert already exists
            existing = await db.alerts.find_one({"title": news_item["title"]})
            
            if not existing:
                sentiment = analyze_sentiment(news_item.get("content", ""))
                severity = "High" if impact >= 85 else "Medium"
                
                alert = {
                    "id": str(uuid.uuid4()),
                    "title": news_item.get("title", "Market Alert"),
                    "impact_score": impact,
                    "impacted_sectors": [news_item.get("sector", "General")],
                    "severity": severity,
                    "explanation": f"{sentiment['label']} sentiment detected in {news_item.get('sector', 'market')} sector with {sentiment['confidence']}% confidence.",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "is_read": False
                }
                
                await db.alerts.insert_one(alert)
                
                # Broadcast to all connected users
                broadcast_data = {k: v for k, v in alert.items() if k != "_id"}
                await alert_manager.broadcast_all({"type": "new_alert", "data": broadcast_data})
                
                alerts_created += 1
    
    return success_response(
        data={"alerts_created": alerts_created},
        message=f"Generated {alerts_created} new alerts"
    )
