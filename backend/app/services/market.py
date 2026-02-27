"""Market analysis services - predictions, sentiment, heatmap."""
from datetime import datetime, timezone, timedelta


def generate_stock_history(base_price: float, days: int = 90) -> list:
    """Generate pseudo-random historical stock data."""
    data = []
    price = base_price
    
    for i in range(days):
        # Deterministic pseudo-random value
        seed_value = (i * 7 + 13) % 100
        change_pct = (seed_value - 50) / 500  # -10% to +10%
        
        price *= (1 + change_pct)
        
        open_price = round(price * (1 - abs(change_pct) * 0.3), 2)
        close_price = round(price, 2)
        high_price = round(max(open_price, close_price) * 1.012, 2)
        low_price = round(min(open_price, close_price) * 0.988, 2)
        
        date = (datetime.now(timezone.utc) - timedelta(days=days - i)).strftime("%Y-%m-%d")
        volume = 1000000 + seed_value * 50000
        
        data.append({
            "date": date,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        })
    
    return data


def predict_stock_direction(historical_data: list) -> dict:
    """Predict stock direction using SMA-based analysis."""
    if len(historical_data) < 5:
        return {
            "direction": "neutral",
            "confidence": 50,
            "explanation": "Insufficient data for analysis."
        }
    
    # Get recent closing prices
    recent_closes = [d["close"] for d in historical_data[-10:]]
    
    # Calculate simple moving averages
    sma5 = sum(recent_closes[-5:]) / 5
    sma10 = sum(recent_closes) / len(recent_closes)
    
    # Calculate momentum
    momentum = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] * 100
    
    # Determine direction and confidence
    if sma5 > sma10 and momentum > 0:
        direction = "up"
        confidence = min(60 + abs(momentum) * 5, 92)
    elif sma5 < sma10 and momentum < 0:
        direction = "down"
        confidence = min(60 + abs(momentum) * 5, 92)
    else:
        direction = "neutral"
        confidence = 50
    
    return {
        "direction": direction,
        "confidence": round(confidence),
        "explanation": f"SMA5 ({sma5:.2f}) vs SMA10 ({sma10:.2f}). Momentum: {momentum:.2f}%."
    }


def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of text using keyword matching."""
    positive_keywords = [
        "growth", "profit", "surge", "rally", "bullish", "strong", 
        "gain", "rise", "positive", "record", "high"
    ]
    negative_keywords = [
        "fall", "crash", "bearish", "loss", "decline", "drop", 
        "weak", "risk", "negative", "sell", "low"
    ]
    
    words = text.lower().split()
    
    positive_count = sum(1 for word in words if any(kw in word for kw in positive_keywords))
    negative_count = sum(1 for word in words if any(kw in word for kw in negative_keywords))
    
    total_count = positive_count + negative_count
    
    if total_count == 0:
        return {
            "score": 0.5,
            "label": "Neutral",
            "confidence": 40
        }
    
    sentiment_score = positive_count / total_count
    
    if sentiment_score > 0.6:
        label = "Bullish"
    elif sentiment_score < 0.4:
        label = "Bearish"
    else:
        label = "Neutral"
    
    confidence = min(50 + total_count * 10, 95)
    
    return {
        "score": round(sentiment_score, 2),
        "label": label,
        "confidence": confidence
    }


def calculate_impact_score(news_item: dict) -> int:
    """Calculate impact score from news sentiment."""
    sentiment = analyze_sentiment(news_item.get("content", ""))
    score_raw = abs(sentiment["score"] - 0.5) * 200
    
    word_count = len(news_item.get("content", "").split())
    boost = min(word_count / 20, 1) * 10
    
    impact = min(round(score_raw + boost), 100)
    return impact
