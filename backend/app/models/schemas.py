"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field
from typing import List, Optional


# ═══════════════════════════════════════════════════════
# AUTH MODELS
# ═══════════════════════════════════════════════════════

class RegisterInput(BaseModel):
    name: str
    email: str
    password: str


class LoginInput(BaseModel):
    email: str
    password: str


# ═══════════════════════════════════════════════════════
# LEARN MODELS
# ═══════════════════════════════════════════════════════

class QuizSubmitInput(BaseModel):
    lessonId: str
    answers: List[int]


class TaxCompareInput(BaseModel):
    income: float
    deductions_80c: float = 0
    deductions_80d: float = 0
    hra_exemption: float = 0
    other_deductions: float = 0


# ═══════════════════════════════════════════════════════
# MARKET MODELS
# ═══════════════════════════════════════════════════════

class PredictionInput(BaseModel):
    stockSymbol: str
    predictedDirection: str


# ═══════════════════════════════════════════════════════
# PORTFOLIO MODELS
# ═══════════════════════════════════════════════════════

class CapitalGainsInput(BaseModel):
    buyPrice: float
    sellPrice: float
    quantity: int
    holdingMonths: int
    assetType: str = "equity"


class FDTaxInput(BaseModel):
    principal: float
    rate: float
    years: int
    taxBracket: float


class AddAssetInput(BaseModel):
    symbol: str
    quantity: int
    buyPrice: float


# ═══════════════════════════════════════════════════════
# RISK MODELS
# ═══════════════════════════════════════════════════════

class TransactionCheckInput(BaseModel):
    amount: float
    type: str
    description: str
    recipientNew: bool = False


class FraudDetectInput(BaseModel):
    text: str


# ═══════════════════════════════════════════════════════
# ADVISOR MODELS
# ═══════════════════════════════════════════════════════

class AdvisorQueryInput(BaseModel):
    query: str


# ═══════════════════════════════════════════════════════
# ALERT MODELS
# ═══════════════════════════════════════════════════════

class MarkAlertReadInput(BaseModel):
    alertId: str
