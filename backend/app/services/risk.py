"""Risk analysis services - transaction risk and fraud detection."""


def analyze_transaction_risk(amount: float, transaction_type: str, description: str, 
                             recipient_new: bool) -> dict:
    """Analyze transaction risk score."""
    risk_score = 0
    reasons = []
    
    # Amount-based risk
    if amount > 100000:
        risk_score += 30
        reasons.append("High-value transaction (>Rs.1,00,000)")
    elif amount > 50000:
        risk_score += 15
        reasons.append("Significant transaction amount")
    
    # New recipient risk
    if recipient_new:
        risk_score += 20
        reasons.append("New/unknown recipient")
    
    # Suspicious keywords in description
    suspicious_keywords = [
        "urgent", "immediately", "wire", "crypto", "bitcoin", 
        "lottery", "prize", "free"
    ]
    
    desc_lower = description.lower()
    found_keywords = [kw for kw in suspicious_keywords if kw in desc_lower]
    
    if found_keywords:
        risk_score += len(found_keywords) * 15
        reasons.append(f"Suspicious keywords: {', '.join(found_keywords)}")
    
    # Transaction type risk
    high_risk_types = ["international_transfer", "wire_transfer"]
    if transaction_type in high_risk_types:
        risk_score += 20
        reasons.append("High-risk transaction type")
    
    # Cap at 100
    risk_score = min(risk_score, 100)
    
    # Recommendation
    if risk_score > 70:
        recommendation = "Block transaction. High fraud probability."
        delay = "24-hour hold recommended"
    elif risk_score > 40:
        recommendation = "Proceed with additional verification."
        delay = "OTP verification recommended"
    else:
        recommendation = "Transaction appears safe."
        delay = "No delay needed"
    
    confidence = min(60 + len(reasons) * 10, 95)
    
    return {
        "risk_score": risk_score,
        "reasons": reasons,
        "recommendation": recommendation,
        "delay": delay,
        "confidence": confidence
    }


def detect_fraud(text: str) -> dict:
    """Detect fraud indicators in text."""
    fraud_keywords = {
        "urgent": 15,
        "lottery": 25,
        "winner": 20,
        "click here": 20,
        "wire transfer": 20,
        "otp": 15,
        "verify account": 20,
        "limited time": 15,
        "free money": 25,
        "congratulations": 10,
        "prize": 20,
        "act now": 15,
        "bank details": 20,
        "password": 25,
        "pin number": 25,
        "suspended": 20,
        "account blocked": 20,
        "inheritance": 20,
        "transfer fee": 20,
        "advance payment": 20,
        "guaranteed return": 20
    }
    
    text_lower = text.lower()
    found_keywords = {}
    total_score = 0
    
    for keyword, weight in fraud_keywords.items():
        if keyword in text_lower:
            found_keywords[keyword] = weight
            total_score += weight
    
    probability = min(total_score, 100)
    
    # Verdict
    if probability > 70:
        verdict = "High Risk"
        recommendation = "Strong fraud indicators detected. Do not respond or share personal information."
    elif probability > 40:
        verdict = "Suspicious"
        recommendation = "Concerning elements found. Verify sender through official channels."
    elif probability > 15:
        verdict = "Low Risk"
        recommendation = "Minor suspicious elements. Exercise normal caution."
    else:
        verdict = "Safe"
        recommendation = "No significant fraud indicators detected."
    
    # Highlight positions
    highlights = []
    for keyword in found_keywords:
        idx = text_lower.find(keyword)
        if idx >= 0:
            highlights.append({
                "keyword": keyword,
                "start": idx,
                "end": idx + len(keyword),
                "weight": found_keywords[keyword]
            })
    
    confidence = min(50 + len(found_keywords) * 10, 95)
    
    return {
        "probability": probability,
        "verdict": verdict,
        "keywords_found": found_keywords,
        "highlights": highlights,
        "recommendation": recommendation,
        "confidence": confidence
    }
