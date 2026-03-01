"""Markets module routes - stocks, predictions, sentiment, heatmap."""
import uuid
import math
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query

from ..config import settings
from ..models.schemas import PredictionInput
from ..services.auth import get_current_user
from ..services.market import predict_stock_direction, analyze_sentiment
from ..services.alpha_vantage import (
    get_quote,
    get_time_series_daily,
    get_metadata_by_symbol,
    get_alpha_metadata_by_symbol,
    get_metadata_for_alpha,
)
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/markets", tags=["markets"])


def _fallback_historical_from_quote(current_price: float, previous_close: float) -> list:
    """Build minimal 2-point series from quote so chart always has data when time series API fails (e.g. rate limit)."""
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)
    return [
        {"date": yesterday.strftime("%Y-%m-%d"), "open": previous_close, "high": previous_close, "low": previous_close, "close": previous_close, "volume": 0},
        {"date": today.strftime("%Y-%m-%d"), "open": previous_close, "high": current_price, "low": previous_close, "close": current_price, "volume": 0},
    ]


async def _stocks_from_alpha():
    """Build stock list from Alpha Vantage quotes (US symbols for reliable real-time data)."""
    stocks = []
    for meta in get_metadata_for_alpha():
        quote = await get_quote(meta["alpha_symbol"])
        if quote is None:
            stocks.append({
                "symbol": meta["symbol"],
                "name": meta["name"],
                "sector": meta["sector"],
                "marketCap": meta["marketCap"],
                "currentPrice": 0,
                "change": 0,
                "currency": "USD",
            })
            continue
        stocks.append({
            "symbol": meta["symbol"],
            "name": meta["name"],
            "sector": meta["sector"],
            "marketCap": meta["marketCap"],
            "currentPrice": quote["currentPrice"],
            "change": quote["change"],
            "currency": "USD",
        })
    return stocks


@router.get("/stocks")
async def get_stocks(user=Depends(get_current_user)):
    """Get all stocks (without historical data). Uses Alpha Vantage if API key is set; falls back to DB on failure."""
    db = get_db()
    if settings.ALPHA_VANTAGE_API_KEY:
        stocks = await _stocks_from_alpha()
        # If Alpha returned no real prices (all 0), fall back to DB so the app still loads
        if stocks and any(s.get("currentPrice") for s in stocks):
            return success_response(data=stocks)
        stocks_db = await db.stocks.find({}, {"_id": 0, "historicalData": 0}).to_list(50)
        if stocks_db:
            return success_response(data=stocks_db)
        # Alpha failed and DB empty - return whatever we got (placeholders with 0)
        return success_response(data=stocks)
    stocks = await db.stocks.find({}, {"_id": 0, "historicalData": 0}).to_list(50)
    return success_response(data=stocks)


@router.get("/stocks/{symbol}")
async def get_stock_detail(symbol: str, user=Depends(get_current_user)):
    """Get stock details with AI prediction. Uses Alpha Vantage if API key is set."""
    sym_upper = symbol.upper()
    db = get_db()
    if settings.ALPHA_VANTAGE_API_KEY:
        meta = get_alpha_metadata_by_symbol(sym_upper)
        if meta:
            quote = await get_quote(meta["alpha_symbol"])
            historical = await get_time_series_daily(meta["alpha_symbol"])
            if quote is not None or historical:
                current_price = quote["currentPrice"] if quote else (historical[-1]["close"] if historical else 0)
                change = quote["change"] if quote else 0
                prev_close = quote["previousClose"] if quote else (historical[-2]["close"] if len(historical) >= 2 else current_price)
                if not quote and len(historical) >= 2:
                    prev_close = historical[-2]["close"]
                    current_price = historical[-1]["close"]
                    change = round((current_price - prev_close) / prev_close * 100, 2)
                # When time series is empty (e.g. rate limit), use quote to build a minimal chart so graph always shows
                if not historical and quote:
                    historical = _fallback_historical_from_quote(current_price, prev_close)
                stock = {
                    "symbol": meta["symbol"],
                    "name": meta["name"],
                    "sector": meta["sector"],
                    "marketCap": meta["marketCap"],
                    "currentPrice": current_price,
                    "change": change,
                    "historicalData": historical,
                    "currency": "USD",
                }
                stock["aiPrediction"] = predict_stock_direction(historical)
                return success_response(data=stock)
        # Alpha failed or symbol not in metadata: fall back to DB
    stock = await db.stocks.find_one({"symbol": sym_upper}, {"_id": 0})
    if not stock:
        raise HTTPException(404, "Stock not found")
    historical_data = stock.get("historicalData", [])
    stock["aiPrediction"] = predict_stock_direction(historical_data)
    return success_response(data=stock)


@router.post("/predict")
async def submit_prediction(inp: PredictionInput, user=Depends(get_current_user)):
    """Submit user's stock prediction and compare with AI."""
    db = get_db()
    sym_upper = inp.stockSymbol.upper()
    historical_data = []
    if settings.ALPHA_VANTAGE_API_KEY:
        meta = get_alpha_metadata_by_symbol(sym_upper)
        if not meta:
            raise HTTPException(404, "Stock not found")
        historical_data = await get_time_series_daily(meta["alpha_symbol"])
    else:
        stock = await db.stocks.find_one({"symbol": sym_upper}, {"_id": 0})
        if not stock:
            raise HTTPException(404, "Stock not found")
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
    """Get market heatmap by sector. Uses Alpha Vantage when API key is set; falls back to DB on failure."""
    db = get_db()
    if settings.ALPHA_VANTAGE_API_KEY:
        stocks = await _stocks_from_alpha()
        if not stocks or not any(s.get("currentPrice") for s in stocks):
            stocks = await db.stocks.find({}, {"_id": 0}).to_list(50)
    else:
        stocks = await db.stocks.find({}, {"_id": 0}).to_list(50)
    heatmap = {}
    for stock in stocks:
        sector = stock.get("sector", "Other")
        change = stock.get("change", 0)
        if sector not in heatmap:
            heatmap[sector] = {"sector": sector, "stocks": [], "avgChange": 0}
        heatmap[sector]["stocks"].append({
            "symbol": stock["symbol"],
            "name": stock.get("name", stock["symbol"]),
            "change": round(change, 2),
        })
    for sector_data in heatmap.values():
        changes = [s["change"] for s in sector_data["stocks"]]
        sector_data["avgChange"] = round(sum(changes) / len(changes), 2) if changes else 0
    return success_response(data=list(heatmap.values()))
