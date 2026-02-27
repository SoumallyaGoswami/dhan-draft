"""Overview route - dashboard summary."""
from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..services.financial import calculate_financial_health, calculate_risk_personality
from ..services.market import analyze_sentiment
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/overview", tags=["overview"])


@router.get("/summary")
async def get_overview_summary(user=Depends(get_current_user)):
    """Get comprehensive overview summary for dashboard."""
    db = get_db()
    
    # Get user's assets
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    
    # Calculate financial health and risk
    health = calculate_financial_health(assets)
    risk = calculate_risk_personality(assets)
    
    # Portfolio allocation by type
    allocation = {}
    total_value = sum(a["quantity"] * a["currentPrice"] for a in assets) if assets else 0
    
    for asset in assets:
        asset_type = asset.get("type", "equity")
        value = asset["quantity"] * asset["currentPrice"]
        allocation[asset_type] = allocation.get(asset_type, 0) + value
    
    allocation_list = [
        {
            "name": k,
            "value": round(v),
            "percentage": round(v/total_value*100, 1)
        }
        for k, v in allocation.items()
    ] if total_value > 0 else []
    
    # Prediction accuracy
    predictions = await db.predictions.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    correct_predictions = sum(1 for p in predictions if p.get("correct"))
    prediction_accuracy = round(correct_predictions / len(predictions) * 100) if predictions else 0
    
    # Tax optimization score (heuristic)
    tax_score = 65
    if any(a.get("type") == "fixed_deposit" for a in assets):
        tax_score += 10
    if any(a.get("type") == "equity" for a in assets):
        tax_score += 10
    if len(set(a.get("type") for a in assets)) >= 3:
        tax_score += 15
    tax_score = min(tax_score, 100)
    
    # Scam awareness score
    scam_score = 85
    
    # Sector sentiment analysis
    news = await db.news.find({}, {"_id": 0}).to_list(50)
    sector_sentiments = {}
    
    for news_item in news:
        sector = news_item.get("sector", "Other")
        sentiment = analyze_sentiment(news_item.get("content", ""))
        
        if sector not in sector_sentiments:
            sector_sentiments[sector] = []
        sector_sentiments[sector].append(sentiment["score"])
    
    sentiment_strip = [
        {
            "sector": sector,
            "score": round(sum(scores)/len(scores), 2),
            "label": "Bullish" if sum(scores)/len(scores) > 0.6 else ("Bearish" if sum(scores)/len(scores) < 0.4 else "Neutral")
        }
        for sector, scores in sector_sentiments.items()
    ]
    
    # AI insight from last advice
    last_advice = await db.chat_history.find_one(
        {"userId": user["id"]},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    ai_insight = (
        last_advice["response"]["strategy"]
        if last_advice and "response" in last_advice
        else "Complete your portfolio setup to receive personalized AI insights."
    )
    
    return success_response(data={
        "financialHealth": health,
        "riskPersonality": risk,
        "portfolioAllocation": allocation_list,
        "totalValue": round(total_value),
        "predictionAccuracy": prediction_accuracy,
        "taxOptimization": {
            "score": tax_score,
            "explanation": "Based on asset type diversity and tax-efficient instruments."
        },
        "scamAwareness": {
            "score": scam_score,
            "explanation": "Stay vigilant against online financial scams."
        },
        "aiInsight": ai_insight,
        "sectorSentiment": sentiment_strip
    })
