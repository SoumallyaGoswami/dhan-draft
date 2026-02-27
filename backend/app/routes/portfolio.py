"""Portfolio & Tax module routes."""
import uuid
from fastapi import APIRouter, HTTPException, Depends

from ..models.schemas import TaxCompareInput, CapitalGainsInput, FDTaxInput, AddAssetInput
from ..services.auth import get_current_user
from ..services.tax import (
    calculate_old_regime_tax,
    calculate_new_regime_tax,
    calculate_capital_gains_tax,
    calculate_fd_tax
)
from ..services.financial import calculate_financial_health
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/assets")
async def get_assets(user=Depends(get_current_user)):
    """Get user's portfolio assets."""
    db = get_db()
    
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    
    return success_response(data=assets)


@router.get("/summary")
async def get_portfolio_summary(user=Depends(get_current_user)):
    """Get comprehensive portfolio summary."""
    db = get_db()
    
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    
    if not assets:
        return success_response(data={
            "totalValue": 0,
            "totalCost": 0,
            "totalGain": 0,
            "gainPct": 0,
            "allocation": [],
            "sectorDiversification": [],
            "volatility": "N/A",
            "assets": []
        })
    
    # Calculate totals
    total_value = sum(a["quantity"] * a["currentPrice"] for a in assets)
    total_cost = sum(a["quantity"] * a["buyPrice"] for a in assets)
    total_gain = total_value - total_cost
    gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0
    
    # Allocation by type
    types = {}
    for asset in assets:
        asset_type = asset.get("type", "equity")
        value = asset["quantity"] * asset["currentPrice"]
        types[asset_type] = types.get(asset_type, 0) + value
    
    allocation = [
        {"name": k, "value": round(v), "percentage": round(v/total_value*100, 1)}
        for k, v in types.items()
    ]
    
    # Sector diversification
    sectors = {}
    for asset in assets:
        sector = asset.get("sector", "Other")
        value = asset["quantity"] * asset["currentPrice"]
        sectors[sector] = sectors.get(sector, 0) + value
    
    sector_div = [
        {"name": k, "value": round(v), "percentage": round(v/total_value*100, 1)}
        for k, v in sectors.items()
    ]
    
    # Volatility indicator
    equity_ratio = types.get("equity", 0) / total_value if total_value > 0 else 0
    if equity_ratio > 0.7:
        volatility = "High"
    elif equity_ratio > 0.4:
        volatility = "Moderate"
    else:
        volatility = "Low"
    
    # Per-asset details
    asset_details = []
    for asset in assets:
        current_value = asset["quantity"] * asset["currentPrice"]
        cost_basis = asset["quantity"] * asset["buyPrice"]
        gain = current_value - cost_basis
        gain_pct_asset = (gain / cost_basis * 100) if cost_basis > 0 else 0
        
        detail = {k: v for k, v in asset.items() if k != "userId"}
        detail.update({
            "currentValue": round(current_value),
            "costBasis": round(cost_basis),
            "gain": round(gain),
            "gainPct": round(gain_pct_asset, 2)
        })
        asset_details.append(detail)
    
    return success_response(data={
        "totalValue": round(total_value),
        "totalCost": round(total_cost),
        "totalGain": round(total_gain),
        "gainPct": round(gain_pct, 2),
        "allocation": allocation,
        "sectorDiversification": sector_div,
        "volatility": volatility,
        "assets": asset_details
    })


@router.post("/add-asset")
async def add_asset(inp: AddAssetInput, user=Depends(get_current_user)):
    """Add new asset to portfolio."""
    db = get_db()
    
    # Validate stock exists
    stock = await db.stocks.find_one(
        {"symbol": inp.symbol.upper()},
        {"_id": 0, "historicalData": 0}
    )
    
    if not stock:
        raise HTTPException(404, "Stock not found in our dataset")
    
    if inp.quantity <= 0:
        raise HTTPException(400, "Quantity must be positive")
    
    if inp.buyPrice <= 0:
        raise HTTPException(400, "Buy price must be positive")
    
    # Create asset
    asset = {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "name": stock["name"],
        "symbol": stock["symbol"],
        "type": "equity",
        "sector": stock.get("sector", "Other"),
        "quantity": inp.quantity,
        "buyPrice": inp.buyPrice,
        "currentPrice": stock["currentPrice"]
    }
    
    await db.assets.insert_one(asset)
    
    # Recalculate financial health
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    health = calculate_financial_health(assets)
    
    # Update user's health score
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"financialHealthScore": health["score"]}}
    )
    
    return success_response(
        data={
            "asset": {k: v for k, v in asset.items() if k != "_id"},
            "updatedHealth": health
        },
        message=f"Added {inp.quantity} shares of {stock['symbol']}"
    )


@router.post("/tax/compare")
async def compare_tax(inp: TaxCompareInput, user=Depends(get_current_user)):
    """Compare tax regimes."""
    old_regime = calculate_old_regime_tax(
        inp.income,
        inp.deductions_80c,
        inp.deductions_80d,
        inp.hra_exemption,
        inp.other_deductions
    )
    
    new_regime = calculate_new_regime_tax(inp.income)
    
    better = "old" if old_regime["total"] < new_regime["total"] else "new"
    savings = abs(old_regime["total"] - new_regime["total"])
    
    return success_response(data={
        "old_regime": old_regime,
        "new_regime": new_regime,
        "recommended": better,
        "savings": round(savings)
    })


@router.post("/tax/capital-gains")
async def calculate_capital_gains(inp: CapitalGainsInput, user=Depends(get_current_user)):
    """Calculate capital gains tax."""
    result = calculate_capital_gains_tax(
        inp.buyPrice,
        inp.sellPrice,
        inp.quantity,
        inp.holdingMonths,
        inp.assetType
    )
    
    return success_response(data=result)


@router.post("/tax/fd")
async def calculate_fd_tax_impact(inp: FDTaxInput, user=Depends(get_current_user)):
    """Calculate FD tax impact."""
    result = calculate_fd_tax(inp.principal, inp.rate, inp.years, inp.taxBracket)
    
    return success_response(data=result)
