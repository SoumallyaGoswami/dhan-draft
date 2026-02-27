"""Risk & Safety module routes."""
from fastapi import APIRouter, Depends

from ..models.schemas import TransactionCheckInput, FraudDetectInput
from ..services.auth import get_current_user
from ..services.risk import analyze_transaction_risk, detect_fraud
from ..utils.responses import success_response

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/transaction")
async def check_transaction_risk(inp: TransactionCheckInput, user=Depends(get_current_user)):
    """Analyze transaction risk."""
    result = analyze_transaction_risk(
        inp.amount,
        inp.type,
        inp.description,
        inp.recipientNew
    )
    
    return success_response(data=result)


@router.post("/fraud")
async def detect_fraud_text(inp: FraudDetectInput, user=Depends(get_current_user)):
    """Detect fraud in text."""
    result = detect_fraud(inp.text)
    
    return success_response(data=result)
