"""Markets module routes - stocks, predictions, sentiment, heatmap."""
import uuid
import math
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query

from ..models.schemas import PredictionInput
from ..services.auth import get_current_user
from ..services.market import predict_stock_direction, analyze_sentiment
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("/stocks")
async def get_stocks(user=Depends(get_current_user)):
    """Get all stocks (without historical data)."""
    db = get_db()
    
    stocks = await db.stocks.find({}, {"_id": 0, "historicalData": 0}).to_list(50)
    
    return success_response(data=stocks)


@router.get("/stocks/{symbol}")
async def get_stock_detail(symbol: str, user=Depends(get_current_user)):
    """Get stock details with AI prediction."""
    db = get_db()
    
    stock = await db.stocks.find_one({"symbol": symbol.upper()}, {"_id": 0})
    if not stock:
        raise HTTPException(404, "Stock not found")
    
    # Add AI prediction
    historical_data = stock.get("historicalData", [])
    prediction = predict_stock_direction(historical_data)
    stock["aiPrediction"] = prediction
    
    return success_response(data=stock)


@router.post("/predict")
async def submit_prediction(inp: PredictionInput, user=Depends(get_current_user)):
    """Submit user's stock prediction and compare with AI."""
    db = get_db()
    
    # Get stock data
    stock = await db.stocks.find_one({"symbol": inp.stockSymbol.upper()}, {"_id": 0})
    if not stock:
        raise HTTPException(404, "Stock not found")
    
    # Get AI prediction
    historical_data = stock.get("historicalData", [])
    ai_prediction = predict_stock_direction(historical_data)
    
    # Check if user prediction matches AI
    correct = inp.predictedDirection == ai_prediction["direction"]
    
    # Save prediction record
    record = {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "stockSymbol": inp.stockSymbol.upper(),
        "predictedDirection": inp.predictedDirection,
        "aiDirection": ai_prediction["direction"],
        "aiConfidence": ai_prediction["confidence"],
        "correct": correct,
        "explanation": ai_prediction["explanation"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.predictions.insert_one(record)
    
    return success_response(
        data={
            "userPrediction": inp.predictedDirection,
            "aiPrediction": ai_prediction,
            "match": correct,
            "explanation": ai_prediction["explanation"]
        },
        message="Prediction recorded"
    )


@router.get("/predictions")
async def get_user_predictions(
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's predictions with pagination."""
    db = get_db()
    
    skip = (page - 1) * limit
    
    # Get paginated predictions
    predictions = await db.predictions.find(
        {"userId": user["id"]},
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get total count for pagination
    total = await db.predictions.count_documents({"userId": user["id"]})
    
    # Calculate accuracy
    all_predictions = await db.predictions.find({"userId": user["id"]}, {"_id": 0}).to_list(1000)
    correct_count = sum(1 for p in all_predictions if p.get("correct"))
    accuracy = round(correct_count / len(all_predictions) * 100) if all_predictions else 0
    
    return success_response(data={
        "predictions": predictions,
        "accuracy": accuracy,
        "total": total,
        "correct": correct_count,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 0
    })


@router.get("/sentiment")
async def get_sentiment_analysis(user=Depends(get_current_user)):
    """Get sentiment analysis for all news."""
    db = get_db()
    
    news = await db.news.find({}, {"_id": 0}).to_list(50)
    
    # Add sentiment analysis to each news item
    for news_item in news:
        news_item["sentiment_analysis"] = analyze_sentiment(news_item.get("content", ""))
    
    return success_response(data=news)


@router.get("/heatmap")
async def get_market_heatmap(user=Depends(get_current_user)):
    """Get market heatmap by sector."""
    db = get_db()
    
    stocks = await db.stocks.find({}, {"_id": 0}).to_list(50)
    
    heatmap = {}
    
    for stock in stocks:
        sector = stock.get("sector", "Other")
        
        # Calculate price change
        historical_data = stock.get("historicalData", [])
        if len(historical_data) >= 2:
            change = (
                (historical_data[-1]["close"] - historical_data[-2]["close"]) /
                historical_data[-2]["close"] * 100
            )
        else:
            change = stock.get("change", 0)
        
        # Initialize sector if not exists
        if sector not in heatmap:
            heatmap[sector] = {
                "sector": sector,
                "stocks": [],
                "avgChange": 0
            }
        
        heatmap[sector]["stocks"].append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "change": round(change, 2)
        })
    
    # Calculate average change per sector
    for sector_data in heatmap.values():
        changes = [s["change"] for s in sector_data["stocks"]]
        sector_data["avgChange"] = round(sum(changes) / len(changes), 2) if changes else 0
    
    return success_response(data=list(heatmap.values()))
