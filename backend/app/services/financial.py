"""Financial health and risk analysis services."""


def calculate_financial_health(assets: list) -> dict:
    """Calculate financial health score based on portfolio."""
    if not assets:
        return {
            "score": 45,
            "confidence": 60,
            "explanation": "Add assets to your portfolio for a personalized health score."
        }
    
    total_value = sum(a["quantity"] * a["currentPrice"] for a in assets)
    total_cost = sum(a["quantity"] * a["buyPrice"] for a in assets)
    
    if total_value == 0:
        return {
            "score": 30,
            "confidence": 50,
            "explanation": "Portfolio has no current value."
        }
    
    # Calculate sector concentration
    sectors = {}
    for asset in assets:
        sector = asset.get("sector", "Other")
        sectors[sector] = sectors.get(sector, 0) + asset["quantity"] * asset["currentPrice"]
    
    max_concentration = max(sectors.values()) / total_value
    num_sectors = len(sectors)
    
    # Diversification score (0-25 points)
    div_score = min(num_sectors / 5, 1) * (1 - max_concentration + 0.5) * 25
    div_score = max(0, min(25, div_score))
    
    # Returns score (0-25 points)
    return_pct = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
    ret_score = min(max(return_pct / 20, 0), 1) * 25
    
    # Asset type diversity score (0-25 points)
    types = set(a.get("type", "equity") for a in assets)
    type_score = min(len(types) / 3, 1) * 25
    
    # Health score based on returns (0-25 points)
    if return_pct > 10:
        health_score = 25
    elif return_pct > 5:
        health_score = 20
    elif return_pct > 0:
        health_score = 17
    elif return_pct < -10:
        health_score = 5
    else:
        health_score = 15
    
    total_score = int(max(0, min(100, div_score + ret_score + type_score + health_score)))
    confidence = min(70 + num_sectors * 5 + len(assets) * 2, 95)
    
    # Generate explanation
    explanations = []
    if max_concentration > 0.5:
        explanations.append(f"High sector concentration ({max_concentration*100:.0f}%).")
    if return_pct < 0:
        explanations.append(f"Portfolio is down {abs(return_pct):.1f}%.")
    if num_sectors < 3:
        explanations.append("Diversify across more sectors.")
    if return_pct > 10:
        explanations.append(f"Strong returns of {return_pct:.1f}%.")
    if not explanations:
        explanations.append("Portfolio is well-balanced.")
    
    return {
        "score": total_score,
        "confidence": confidence,
        "explanation": " ".join(explanations)
    }


def calculate_risk_personality(assets: list) -> dict:
    """Calculate risk personality based on equity allocation."""
    if not assets:
        return {
            "personality": "Undetermined",
            "confidence": 30,
            "explanation": "Add assets to determine risk personality."
        }
    
    total_value = sum(a["quantity"] * a["currentPrice"] for a in assets)
    
    if total_value == 0:
        return {
            "personality": "Undetermined",
            "confidence": 30,
            "explanation": "Portfolio empty."
        }
    
    equity_value = sum(
        a["quantity"] * a["currentPrice"] 
        for a in assets 
        if a.get("type") == "equity"
    )
    
    equity_ratio = equity_value / total_value
    
    if equity_ratio > 0.8:
        return {
            "personality": "Aggressive",
            "confidence": 88,
            "explanation": "Heavy equity allocation signals high risk tolerance."
        }
    elif equity_ratio > 0.6:
        return {
            "personality": "Growth",
            "confidence": 85,
            "explanation": "Equity-tilted portfolio with growth focus."
        }
    elif equity_ratio > 0.4:
        return {
            "personality": "Moderate",
            "confidence": 85,
            "explanation": "Balanced equity-debt allocation."
        }
    else:
        return {
            "personality": "Conservative",
            "confidence": 85,
            "explanation": "Preference for stable, low-risk instruments."
        }
