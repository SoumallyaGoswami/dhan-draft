"""Learn module routes - lessons, quizzes, tax calculators."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from ..models.schemas import QuizSubmitInput, TaxCompareInput
from ..services.auth import get_current_user
from ..services.tax import calculate_old_regime_tax, calculate_new_regime_tax
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/learn", tags=["learn"])


@router.get("/lessons")
async def get_lessons(user=Depends(get_current_user)):
    """Get all lessons with user's completion status."""
    db = get_db()
    
    lessons = await db.lessons.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    scores = await db.quiz_scores.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    
    # Map best scores by lesson ID
    score_map = {}
    for score in scores:
        lesson_id = score["lessonId"]
        if lesson_id not in score_map or score["score"] > score_map[lesson_id]:
            score_map[lesson_id] = score["score"]
    
    # Attach scores to lessons
    for lesson in lessons:
        lesson["bestScore"] = score_map.get(lesson["id"], None)
        lesson["completed"] = lesson["id"] in score_map
    
    return success_response(data=lessons)


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, user=Depends(get_current_user)):
    """Get specific lesson details."""
    db = get_db()
    
    lesson = await db.lessons.find_one({"id": lesson_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    
    return success_response(data=lesson)


@router.post("/quiz/submit")
async def submit_quiz(inp: QuizSubmitInput, user=Depends(get_current_user)):
    """Submit quiz answers and calculate score."""
    db = get_db()
    
    # Get lesson and quiz
    lesson = await db.lessons.find_one({"id": inp.lessonId}, {"_id": 0})
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    
    quiz = lesson.get("quiz", [])
    
    if len(inp.answers) != len(quiz):
        raise HTTPException(400, f"Expected {len(quiz)} answers, got {len(inp.answers)}")
    
    # Calculate score
    correct_count = sum(1 for i, answer in enumerate(inp.answers) if answer == quiz[i]["correct"])
    score = round(correct_count / len(quiz) * 100)
    
    # Save score record
    record = {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "lessonId": inp.lessonId,
        "lessonTitle": lesson["title"],
        "score": score,
        "correct": correct_count,
        "total": len(quiz),
        "answers": inp.answers,
        "completedAt": datetime.now(timezone.utc).isoformat()
    }
    
    await db.quiz_scores.insert_one(record)
    
    return success_response(
        data={
            "score": score,
            "correct": correct_count,
            "total": len(quiz),
            "answers": [q["correct"] for q in quiz]
        },
        message=f"Quiz completed! Score: {score}%"
    )


@router.get("/quiz/history")
async def get_quiz_history(user=Depends(get_current_user)):
    """Get user's quiz history."""
    db = get_db()
    
    scores = await db.quiz_scores.find(
        {"userId": user["id"]},
        {"_id": 0}
    ).sort("completedAt", -1).to_list(50)
    
    return success_response(data=scores)


@router.post("/tax-compare")
async def compare_tax_regimes(inp: TaxCompareInput, user=Depends(get_current_user)):
    """Compare old vs new tax regime."""
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
        "savings": round(savings),
        "explanation": f"The {'Old' if better == 'old' else 'New'} regime saves you Rs.{savings:,.0f} more."
    })


@router.get("/bank-rates")
async def get_bank_rates(user=Depends(get_current_user)):
    """Get bank interest rates comparison."""
    rates = [
        {
            "type": "Savings Account",
            "rate": "2.5% - 4.0%",
            "minBalance": "Rs.1,000 - Rs.10,000",
            "taxable": "Yes (above Rs.10,000)",
            "liquidity": "High"
        },
        {
            "type": "Fixed Deposit (FD)",
            "rate": "5.0% - 7.5%",
            "minBalance": "Rs.1,000",
            "taxable": "Yes (TDS above Rs.40,000)",
            "liquidity": "Low (penalty on early withdrawal)"
        },
        {
            "type": "Recurring Deposit (RD)",
            "rate": "5.5% - 6.5%",
            "minBalance": "Rs.100/month",
            "taxable": "Yes",
            "liquidity": "Low"
        },
        {
            "type": "Current Account",
            "rate": "0%",
            "minBalance": "Rs.10,000+",
            "taxable": "N/A",
            "liquidity": "High"
        },
        {
            "type": "PPF",
            "rate": "7.1%",
            "minBalance": "Rs.500/year",
            "taxable": "Exempt (EEE)",
            "liquidity": "Low (15-year lock-in)"
        },
        {
            "type": "NPS",
            "rate": "8% - 10% (market-linked)",
            "minBalance": "Rs.500/year",
            "taxable": "Partial (60% exempt at maturity)",
            "liquidity": "Very Low (till 60 years)"
        }
    ]
    
    return success_response(data=rates)
