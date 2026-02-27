"""AI advisor services - rule-based strategy engine."""
from .financial import calculate_risk_personality


def generate_advice(assets: list, user: dict) -> dict:
    """Generate personalized financial advice based on portfolio."""
    if not assets:
        return {
            "strategy": "Start building your portfolio with a diversified mix of equity and fixed income.",
            "tax_suggestion": "Consider ELSS for Section 80C benefits (up to Rs.1.5L deduction).",
            "risk_alert": "No portfolio detected. Begin with low-risk instruments like PPF or FDs.",
            "sector_warning": "N/A",
            "explanation": "Without a portfolio, the advisor recommends starting with a balanced approach based on your risk tolerance."
        }
    
    total_value = sum(a["quantity"] * a["currentPrice"] for a in assets)
    
    # Calculate sector and type allocations
    sectors = {}
    types = {}
    
    for asset in assets:
        value = asset["quantity"] * asset["currentPrice"]
        
        sector = asset.get("sector", "Other")
        sectors[sector] = sectors.get(sector, 0) + value
        
        asset_type = asset.get("type", "equity")
        types[asset_type] = types.get(asset_type, 0) + value
    
    equity_ratio = types.get("equity", 0) / total_value if total_value > 0 else 0
    
    # Generate strategy recommendations
    strategies = []
    if equity_ratio > 0.8:
        strategies.append(
            "Portfolio is heavily equity-weighted. Consider adding fixed income (bonds, FDs) to reduce volatility."
        )
    elif equity_ratio < 0.3:
        strategies.append(
            "Low equity exposure may limit growth. Consider adding blue-chip stocks for long-term wealth creation."
        )
    else:
        strategies.append(
            "Good equity-debt balance. Consider quarterly rebalancing to maintain target allocation."
        )
    
    # Sector warnings
    sector_warnings = []
    for sector, value in sectors.items():
        pct = value / total_value * 100
        if pct > 40:
            sector_warnings.append(
                f"High concentration ({pct:.0f}%) in {sector}. Diversify to reduce sector-specific risk."
            )
    
    if not sector_warnings:
        sector_warnings.append("Sector diversification looks healthy across your portfolio.")
    
    # Tax suggestions
    risk_profile = calculate_risk_personality(assets)
    if risk_profile["personality"] in ["Aggressive", "Growth"]:
        tax_suggestion = "Consider ELSS funds for 80C benefit with equity exposure."
    else:
        tax_suggestion = "PPF and NSC offer guaranteed returns with tax benefits for conservative investors."
    
    # Risk alerts
    risk_alerts = []
    total_gains = sum((a["currentPrice"] - a["buyPrice"]) * a["quantity"] for a in assets)
    
    if total_gains < 0:
        risk_alerts.append(
            f"Portfolio showing unrealized loss of Rs.{abs(total_gains):,.0f}. Review underperforming holdings."
        )
    
    # High volatility sectors
    volatile_sectors = ["Technology", "Pharma"]
    volatile_exposure = sum(sectors.get(s, 0) for s in volatile_sectors) / total_value * 100 if total_value > 0 else 0
    
    if volatile_exposure > 30:
        risk_alerts.append(
            f"High exposure ({volatile_exposure:.0f}%) to volatile sectors (Tech, Pharma)."
        )
    
    if not risk_alerts:
        risk_alerts.append("No significant risk alerts at this time.")
    
    # Generate explanation
    explanation = (
        f"Analysis based on Rs.{total_value:,.0f} portfolio across {len(sectors)} sectors "
        f"with {equity_ratio*100:.0f}% equity allocation. "
        f"Risk profile: {risk_profile['personality']}."
    )
    
    return {
        "strategy": " ".join(strategies),
        "tax_suggestion": tax_suggestion,
        "risk_alert": " ".join(risk_alerts),
        "sector_warning": " ".join(sector_warnings),
        "explanation": explanation
    }
