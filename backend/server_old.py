from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os, logging, uuid, re, math, json, asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api = APIRouter(prefix="/api")

JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGO = "HS256"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════

class RegisterInput(BaseModel):
    name: str
    email: str
    password: str

class LoginInput(BaseModel):
    email: str
    password: str

class QuizSubmitInput(BaseModel):
    lessonId: str
    answers: List[int]

class PredictionInput(BaseModel):
    stockSymbol: str
    predictedDirection: str

class TaxCompareInput(BaseModel):
    income: float
    deductions_80c: float = 0
    deductions_80d: float = 0
    hra_exemption: float = 0
    other_deductions: float = 0

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

class TransactionCheckInput(BaseModel):
    amount: float
    type: str
    description: str
    recipientNew: bool = False

class FraudDetectInput(BaseModel):
    text: str

class AdvisorQueryInput(BaseModel):
    query: str

class AddAssetInput(BaseModel):
    symbol: str
    quantity: int
    buyPrice: float

class MarkAlertReadInput(BaseModel):
    alertId: str

# ═══════════════════════════════════════════════════════
# WEBSOCKET MANAGERS
# ═══════════════════════════════════════════════════════

class AlertConnectionManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket, user_id: str):
        await ws.accept()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(ws)

    def disconnect(self, ws: WebSocket, user_id: str):
        if user_id in self.connections:
            self.connections[user_id] = [c for c in self.connections[user_id] if c != ws]

    async def send_to_user(self, user_id: str, data: dict):
        for ws in self.connections.get(user_id, []):
            try:
                await ws.send_json(data)
            except:
                pass

    async def broadcast_all(self, data: dict):
        for uid in self.connections:
            await self.send_to_user(uid, data)

class ChatConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections = [c for c in self.connections if c != ws]

    async def broadcast(self, data: dict):
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except:
                pass

alert_mgr = AlertConnectionManager()
chat_mgr = ChatConnectionManager()

# ═══════════════════════════════════════════════════════
# AUTH HELPERS
# ═══════════════════════════════════════════════════════

def R(data=None, message="Success", success=True):
    return {"success": success, "data": data, "message": message}

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_pw(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def make_token(uid: str, email: str) -> str:
    return jwt.encode({"uid": uid, "email": email, "exp": datetime.now(timezone.utc) + timedelta(days=7)}, JWT_SECRET, algorithm=JWT_ALGO)

async def current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        p = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGO])
        user = await db.users.find_one({"id": p["uid"]}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ═══════════════════════════════════════════════════════
# SERVICES
# ═══════════════════════════════════════════════════════

def svc_financial_health(assets):
    if not assets:
        return {"score": 45, "confidence": 60, "explanation": "Add assets to your portfolio for a personalized health score."}
    tv = sum(a["quantity"] * a["currentPrice"] for a in assets)
    tc = sum(a["quantity"] * a["buyPrice"] for a in assets)
    if tv == 0:
        return {"score": 30, "confidence": 50, "explanation": "Portfolio has no current value."}
    sectors = {}
    for a in assets:
        s = a.get("sector", "Other")
        sectors[s] = sectors.get(s, 0) + a["quantity"] * a["currentPrice"]
    mc = max(sectors.values()) / tv
    ns = len(sectors)
    div_score = min(ns / 5, 1) * (1 - mc + 0.5) * 25
    div_score = max(0, min(25, div_score))
    ret_pct = ((tv - tc) / tc * 100) if tc > 0 else 0
    ret_score = min(max(ret_pct / 20, 0), 1) * 25
    types = set(a.get("type", "equity") for a in assets)
    type_score = min(len(types) / 3, 1) * 25
    hlth = 15
    if ret_pct > 10: hlth = 25
    elif ret_pct > 5: hlth = 20
    elif ret_pct > 0: hlth = 17
    elif ret_pct < -10: hlth = 5
    total = int(max(0, min(100, div_score + ret_score + type_score + hlth)))
    conf = min(70 + ns * 5 + len(assets) * 2, 95)
    expl = []
    if mc > 0.5: expl.append(f"High sector concentration ({mc*100:.0f}%).")
    if ret_pct < 0: expl.append(f"Portfolio is down {abs(ret_pct):.1f}%.")
    if ns < 3: expl.append("Diversify across more sectors.")
    if ret_pct > 10: expl.append(f"Strong returns of {ret_pct:.1f}%.")
    if not expl: expl.append("Portfolio is well-balanced.")
    return {"score": total, "confidence": conf, "explanation": " ".join(expl)}

def svc_risk_personality(assets):
    if not assets:
        return {"personality": "Undetermined", "confidence": 30, "explanation": "Add assets to determine risk personality."}
    tv = sum(a["quantity"] * a["currentPrice"] for a in assets)
    if tv == 0:
        return {"personality": "Undetermined", "confidence": 30, "explanation": "Portfolio empty."}
    eq = sum(a["quantity"] * a["currentPrice"] for a in assets if a.get("type") == "equity")
    r = eq / tv
    if r > 0.8: return {"personality": "Aggressive", "confidence": 88, "explanation": "Heavy equity allocation signals high risk tolerance."}
    if r > 0.6: return {"personality": "Growth", "confidence": 85, "explanation": "Equity-tilted portfolio with growth focus."}
    if r > 0.4: return {"personality": "Moderate", "confidence": 85, "explanation": "Balanced equity-debt allocation."}
    return {"personality": "Conservative", "confidence": 85, "explanation": "Preference for stable, low-risk instruments."}

def svc_old_regime(income, d80c=0, d80d=0, hra=0, other=0):
    td = min(d80c, 150000) + min(d80d, 25000) + hra + other + 50000
    taxable = max(income - td, 0)
    tax, r = 0, taxable
    if r > 1000000: tax += (r - 1000000) * 0.30; r = 1000000
    if r > 500000: tax += (r - 500000) * 0.20; r = 500000
    if r > 250000: tax += (r - 250000) * 0.05
    cess = tax * 0.04
    return {"taxable_income": round(max(income - td, 0)), "tax": round(tax), "cess": round(cess), "total": round(tax + cess), "effective_rate": round((tax + cess) / income * 100, 2) if income > 0 else 0, "deductions": round(td)}

def svc_new_regime(income):
    sd = 75000
    taxable = max(income - sd, 0)
    tax, rem = 0, taxable
    for amt, rate in [(300000, 0), (300000, 0.05), (300000, 0.10), (300000, 0.15), (300000, 0.20), (float('inf'), 0.30)]:
        if rem <= 0: break
        c = min(rem, amt); tax += c * rate; rem -= c
    if taxable <= 1200000: tax = 0
    cess = tax * 0.04
    return {"taxable_income": round(taxable), "tax": round(tax), "cess": round(cess), "total": round(tax + cess), "effective_rate": round((tax + cess) / income * 100, 2) if income > 0 else 0, "deductions": sd}

def svc_capital_gains(bp, sp, qty, months, atype="equity"):
    gain = (sp - bp) * qty
    gpct = ((sp - bp) / bp * 100) if bp > 0 else 0
    if atype == "equity":
        if months >= 12: tg = max(gain - 125000, 0); tax = tg * 0.125; tt = "LTCG"
        else: tax = max(gain, 0) * 0.20; tt = "STCG"
    else:
        if months >= 24: tax = max(gain, 0) * 0.20; tt = "LTCG"
        else: tax = max(gain, 0) * 0.30; tt = "STCG"
    return {"gain": round(gain), "gain_pct": round(gpct, 2), "tax_type": tt, "tax": round(max(tax, 0)), "net_gain": round(gain - max(tax, 0)), "explanation": f"{tt} of Rs.{round(max(tax, 0)):,} on {atype} held {months} months."}

def svc_fd_tax(principal, rate, years, bracket):
    ipy = principal * rate / 100
    ti = ipy * years; tpy = ipy * bracket / 100; tt = tpy * years
    ptr = ti - tt; er = (ptr / (principal * years)) * 100 if years > 0 else 0
    return {"total_interest": round(ti), "tax_per_year": round(tpy), "total_tax": round(tt), "post_tax_return": round(ptr), "effective_rate": round(er, 2), "explanation": f"At {bracket}% bracket, effective FD rate: {er:.2f}% (pre-tax: {rate}%)."}

def svc_gen_history(base, days=90):
    data, p = [], base
    for i in range(days):
        sv = (i * 7 + 13) % 100
        cp = (sv - 50) / 500
        p *= (1 + cp)
        o, c = round(p * (1 - abs(cp) * 0.3), 2), round(p, 2)
        h, l = round(max(o, c) * 1.012, 2), round(min(o, c) * 0.988, 2)
        d = (datetime.now(timezone.utc) - timedelta(days=days - i)).strftime("%Y-%m-%d")
        data.append({"date": d, "open": o, "high": h, "low": l, "close": c, "volume": 1000000 + sv * 50000})
    return data

def svc_ai_prediction(hist):
    if len(hist) < 5:
        return {"direction": "neutral", "confidence": 50, "explanation": "Insufficient data for analysis."}
    rc = [d["close"] for d in hist[-10:]]
    s5 = sum(rc[-5:]) / 5
    s10 = sum(rc) / len(rc)
    m = (rc[-1] - rc[0]) / rc[0] * 100
    if s5 > s10 and m > 0: d, conf = "up", min(60 + abs(m) * 5, 92)
    elif s5 < s10 and m < 0: d, conf = "down", min(60 + abs(m) * 5, 92)
    else: d, conf = "neutral", 50
    return {"direction": d, "confidence": round(conf), "explanation": f"SMA5 ({s5:.2f}) vs SMA10 ({s10:.2f}). Momentum: {m:.2f}%."}

def svc_sentiment(text):
    pos = ["growth", "profit", "surge", "rally", "bullish", "strong", "gain", "rise", "positive", "record", "high"]
    neg = ["fall", "crash", "bearish", "loss", "decline", "drop", "weak", "risk", "negative", "sell", "low"]
    w = text.lower().split()
    pc = sum(1 for x in w if any(p in x for p in pos))
    nc = sum(1 for x in w if any(n in x for n in neg))
    t = pc + nc
    if t == 0: return {"score": 0.5, "label": "Neutral", "confidence": 40}
    s = pc / t
    lb = "Bullish" if s > 0.6 else ("Bearish" if s < 0.4 else "Neutral")
    return {"score": round(s, 2), "label": lb, "confidence": min(50 + t * 10, 95)}

def svc_tx_risk(amount, ttype, desc, new_recip):
    rs, reasons = 0, []
    if amount > 100000: rs += 30; reasons.append("High-value transaction (>Rs.1,00,000)")
    elif amount > 50000: rs += 15; reasons.append("Significant transaction amount")
    if new_recip: rs += 20; reasons.append("New/unknown recipient")
    suspicious = ["urgent", "immediately", "wire", "crypto", "bitcoin", "lottery", "prize", "free"]
    dl = desc.lower()
    found = [w for w in suspicious if w in dl]
    if found: rs += len(found) * 15; reasons.append(f"Suspicious keywords: {', '.join(found)}")
    if ttype in ["international_transfer", "wire_transfer"]: rs += 20; reasons.append("High-risk transaction type")
    rs = min(rs, 100)
    if rs > 70: rec, delay = "Block transaction. High fraud probability.", "24-hour hold recommended"
    elif rs > 40: rec, delay = "Proceed with additional verification.", "OTP verification recommended"
    else: rec, delay = "Transaction appears safe.", "No delay needed"
    return {"risk_score": rs, "reasons": reasons, "recommendation": rec, "delay": delay, "confidence": min(60 + len(reasons) * 10, 95)}

def svc_fraud(text):
    kw = {"urgent": 15, "lottery": 25, "winner": 20, "click here": 20, "wire transfer": 20, "otp": 15, "verify account": 20, "limited time": 15, "free money": 25, "congratulations": 10, "prize": 20, "act now": 15, "bank details": 20, "password": 25, "pin number": 25, "suspended": 20, "account blocked": 20, "inheritance": 20, "transfer fee": 20, "advance payment": 20, "guaranteed return": 20}
    tl = text.lower()
    found, ts = {}, 0
    for k, w in kw.items():
        if k in tl: found[k] = w; ts += w
    prob = min(ts, 100)
    if prob > 70: v, rec = "High Risk", "Strong fraud indicators detected. Do not respond or share personal information."
    elif prob > 40: v, rec = "Suspicious", "Concerning elements found. Verify sender through official channels."
    elif prob > 15: v, rec = "Low Risk", "Minor suspicious elements. Exercise normal caution."
    else: v, rec = "Safe", "No significant fraud indicators detected."
    highlights = []
    for k in found:
        idx = tl.find(k)
        if idx >= 0: highlights.append({"keyword": k, "start": idx, "end": idx + len(k), "weight": found[k]})
    return {"probability": prob, "verdict": v, "keywords_found": found, "highlights": highlights, "recommendation": rec, "confidence": min(50 + len(found) * 10, 95)}

def svc_advice(assets, user):
    if not assets:
        return {"strategy": "Start building your portfolio with a diversified mix of equity and fixed income.", "tax_suggestion": "Consider ELSS for Section 80C benefits (up to Rs.1.5L deduction).", "risk_alert": "No portfolio detected. Begin with low-risk instruments like PPF or FDs.", "sector_warning": "N/A", "explanation": "Without a portfolio, the advisor recommends starting with a balanced approach based on your risk tolerance."}
    tv = sum(a["quantity"] * a["currentPrice"] for a in assets)
    sectors, types = {}, {}
    for a in assets:
        v = a["quantity"] * a["currentPrice"]
        sectors[a.get("sector", "Other")] = sectors.get(a.get("sector", "Other"), 0) + v
        types[a.get("type", "equity")] = types.get(a.get("type", "equity"), 0) + v
    er = types.get("equity", 0) / tv if tv > 0 else 0
    strats = []
    if er > 0.8: strats.append("Portfolio is heavily equity-weighted. Consider adding fixed income (bonds, FDs) to reduce volatility.")
    elif er < 0.3: strats.append("Low equity exposure may limit growth. Consider adding blue-chip stocks for long-term wealth creation.")
    else: strats.append("Good equity-debt balance. Consider quarterly rebalancing to maintain target allocation.")
    sw = []
    for s, v in sectors.items():
        pct = v / tv * 100
        if pct > 40: sw.append(f"High concentration ({pct:.0f}%) in {s}. Diversify to reduce sector-specific risk.")
    if not sw: sw.append("Sector diversification looks healthy across your portfolio.")
    rp = svc_risk_personality(assets)
    ts = "Consider ELSS funds for 80C benefit with equity exposure." if rp["personality"] in ["Aggressive", "Growth"] else "PPF and NSC offer guaranteed returns with tax benefits for conservative investors."
    gains = sum((a["currentPrice"] - a["buyPrice"]) * a["quantity"] for a in assets)
    ra = []
    if gains < 0: ra.append(f"Portfolio showing unrealized loss of Rs.{abs(gains):,.0f}. Review underperforming holdings.")
    hvs = ["Technology", "Pharma"]
    ve = sum(sectors.get(s, 0) for s in hvs) / tv * 100 if tv > 0 else 0
    if ve > 30: ra.append(f"High exposure ({ve:.0f}%) to volatile sectors (Tech, Pharma).")
    if not ra: ra.append("No significant risk alerts at this time.")
    return {"strategy": " ".join(strats), "tax_suggestion": ts, "risk_alert": " ".join(ra), "sector_warning": " ".join(sw), "explanation": f"Analysis based on Rs.{tv:,.0f} portfolio across {len(sectors)} sectors with {er*100:.0f}% equity allocation. Risk profile: {rp['personality']}."}

def svc_impact_score(news_item):
    """Calculate impact score from news sentiment."""
    sent = svc_sentiment(news_item.get("content", ""))
    score_raw = abs(sent["score"] - 0.5) * 200
    word_count = len(news_item.get("content", "").split())
    boost = min(word_count / 20, 1) * 10
    impact = min(round(score_raw + boost), 100)
    return impact

async def svc_create_alert(news_item, impact_score):
    """Create alert from high-impact news."""
    sent = svc_sentiment(news_item.get("content", ""))
    severity = "High" if impact_score >= 85 else "Medium"
    alert = {
        "id": str(uuid.uuid4()),
        "title": news_item.get("title", "Market Alert"),
        "impact_score": impact_score,
        "impacted_sectors": [news_item.get("sector", "General")],
        "severity": severity,
        "explanation": f"{sent['label']} sentiment detected in {news_item.get('sector', 'market')} sector with {sent['confidence']}% confidence.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_read": False,
    }
    await db.alerts.insert_one(alert)
    broadcast = {k: v for k, v in alert.items() if k != "_id"}
    await alert_mgr.broadcast_all({"type": "new_alert", "data": broadcast})
    return alert

# ═══════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════

@api.post("/auth/register")
async def register(inp: RegisterInput):
    if await db.users.find_one({"email": inp.email}):
        raise HTTPException(400, "Email already registered")
    uid = str(uuid.uuid4())
    user = {"id": uid, "name": inp.name, "email": inp.email, "password": hash_pw(inp.password), "riskPersonality": "Undetermined", "financialHealthScore": 0, "createdAt": datetime.now(timezone.utc).isoformat()}
    await db.users.insert_one(user)
    token = make_token(uid, inp.email)
    return R({"token": token, "user": {"id": uid, "name": inp.name, "email": inp.email}}, "Registration successful")

@api.post("/auth/login")
async def login(inp: LoginInput):
    user = await db.users.find_one({"email": inp.email}, {"_id": 0})
    if not user or not verify_pw(inp.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")
    token = make_token(user["id"], user["email"])
    return R({"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}, "Login successful")

@api.get("/auth/me")
async def me(user=Depends(current_user)):
    return R(user, "User profile")

# ═══════════════════════════════════════════════════════
# OVERVIEW ROUTES
# ═══════════════════════════════════════════════════════

@api.get("/overview/summary")
async def overview_summary(user=Depends(current_user)):
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    health = svc_financial_health(assets)
    risk = svc_risk_personality(assets)
    # Portfolio allocation
    alloc = {}
    tv = sum(a["quantity"] * a["currentPrice"] for a in assets) if assets else 0
    for a in assets:
        t = a.get("type", "equity")
        alloc[t] = alloc.get(t, 0) + a["quantity"] * a["currentPrice"]
    allocation = [{"name": k, "value": round(v), "percentage": round(v/tv*100, 1)} for k, v in alloc.items()] if tv > 0 else []
    # Prediction accuracy
    preds = await db.predictions.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    correct = sum(1 for p in preds if p.get("correct"))
    pred_accuracy = round(correct / len(preds) * 100) if preds else 0
    # Tax optimization (heuristic based on asset types)
    tax_score = 65
    if any(a.get("type") == "fixed_deposit" for a in assets): tax_score += 10
    if any(a.get("type") == "equity" for a in assets): tax_score += 10
    if len(set(a.get("type") for a in assets)) >= 3: tax_score += 15
    tax_score = min(tax_score, 100)
    # Scam awareness
    scam_score = 85
    # Sector sentiment
    news = await db.news.find({}, {"_id": 0}).to_list(50)
    sector_sentiments = {}
    for n in news:
        s = n.get("sector", "Other")
        sent = svc_sentiment(n.get("content", ""))
        if s not in sector_sentiments:
            sector_sentiments[s] = []
        sector_sentiments[s].append(sent["score"])
    sentiment_strip = [{"sector": k, "score": round(sum(v)/len(v), 2), "label": "Bullish" if sum(v)/len(v) > 0.6 else ("Bearish" if sum(v)/len(v) < 0.4 else "Neutral")} for k, v in sector_sentiments.items()]
    # AI insight
    last_advice = await db.chat_history.find_one({"userId": user["id"]}, {"_id": 0}, sort=[("timestamp", -1)])
    ai_insight = last_advice["response"]["strategy"] if last_advice and "response" in last_advice else "Complete your portfolio setup to receive personalized AI insights."
    return R({
        "financialHealth": health,
        "riskPersonality": risk,
        "portfolioAllocation": allocation,
        "totalValue": round(tv),
        "predictionAccuracy": pred_accuracy,
        "taxOptimization": {"score": tax_score, "explanation": "Based on asset type diversity and tax-efficient instruments."},
        "scamAwareness": {"score": scam_score, "explanation": "Stay vigilant against online financial scams."},
        "aiInsight": ai_insight,
        "sectorSentiment": sentiment_strip
    })

# ═══════════════════════════════════════════════════════
# LEARN ROUTES
# ═══════════════════════════════════════════════════════

@api.get("/learn/lessons")
async def get_lessons(user=Depends(current_user)):
    lessons = await db.lessons.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    scores = await db.quiz_scores.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    score_map = {}
    for s in scores:
        lid = s["lessonId"]
        if lid not in score_map or s["score"] > score_map[lid]:
            score_map[lid] = s["score"]
    for l in lessons:
        l["bestScore"] = score_map.get(l["id"], None)
        l["completed"] = l["id"] in score_map
    return R(lessons)

@api.get("/learn/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, user=Depends(current_user)):
    lesson = await db.lessons.find_one({"id": lesson_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    return R(lesson)

@api.post("/learn/quiz/submit")
async def submit_quiz(inp: QuizSubmitInput, user=Depends(current_user)):
    lesson = await db.lessons.find_one({"id": inp.lessonId}, {"_id": 0})
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    quiz = lesson.get("quiz", [])
    if len(inp.answers) != len(quiz):
        raise HTTPException(400, f"Expected {len(quiz)} answers, got {len(inp.answers)}")
    correct = sum(1 for i, a in enumerate(inp.answers) if a == quiz[i]["correct"])
    score = round(correct / len(quiz) * 100)
    record = {"id": str(uuid.uuid4()), "userId": user["id"], "lessonId": inp.lessonId, "lessonTitle": lesson["title"], "score": score, "correct": correct, "total": len(quiz), "answers": inp.answers, "completedAt": datetime.now(timezone.utc).isoformat()}
    await db.quiz_scores.insert_one(record)
    return R({"score": score, "correct": correct, "total": len(quiz), "answers": [q["correct"] for q in quiz]}, f"Quiz completed! Score: {score}%")

@api.get("/learn/quiz/history")
async def quiz_history(user=Depends(current_user)):
    scores = await db.quiz_scores.find({"userId": user["id"]}, {"_id": 0}).sort("completedAt", -1).to_list(50)
    return R(scores)

@api.post("/learn/tax-compare")
async def tax_compare(inp: TaxCompareInput, user=Depends(current_user)):
    old = svc_old_regime(inp.income, inp.deductions_80c, inp.deductions_80d, inp.hra_exemption, inp.other_deductions)
    new = svc_new_regime(inp.income)
    better = "old" if old["total"] < new["total"] else "new"
    savings = abs(old["total"] - new["total"])
    return R({"old_regime": old, "new_regime": new, "recommended": better, "savings": round(savings), "explanation": f"The {'Old' if better == 'old' else 'New'} regime saves you Rs.{savings:,.0f} more."})

@api.get("/learn/bank-rates")
async def bank_rates(user=Depends(current_user)):
    rates = [
        {"type": "Savings Account", "rate": "2.5% - 4.0%", "minBalance": "Rs.1,000 - Rs.10,000", "taxable": "Yes (above Rs.10,000)", "liquidity": "High"},
        {"type": "Fixed Deposit (FD)", "rate": "5.0% - 7.5%", "minBalance": "Rs.1,000", "taxable": "Yes (TDS above Rs.40,000)", "liquidity": "Low (penalty on early withdrawal)"},
        {"type": "Recurring Deposit (RD)", "rate": "5.5% - 6.5%", "minBalance": "Rs.100/month", "taxable": "Yes", "liquidity": "Low"},
        {"type": "Current Account", "rate": "0%", "minBalance": "Rs.10,000+", "taxable": "N/A", "liquidity": "High"},
        {"type": "PPF", "rate": "7.1%", "minBalance": "Rs.500/year", "taxable": "Exempt (EEE)", "liquidity": "Low (15-year lock-in)"},
        {"type": "NPS", "rate": "8% - 10% (market-linked)", "minBalance": "Rs.500/year", "taxable": "Partial (60% exempt at maturity)", "liquidity": "Very Low (till 60 years)"},
    ]
    return R(rates)

# ═══════════════════════════════════════════════════════
# MARKETS ROUTES
# ═══════════════════════════════════════════════════════

@api.get("/markets/stocks")
async def get_stocks(user=Depends(current_user)):
    stocks = await db.stocks.find({}, {"_id": 0, "historicalData": 0}).to_list(50)
    return R(stocks)

@api.get("/markets/stocks/{symbol}")
async def get_stock(symbol: str, user=Depends(current_user)):
    stock = await db.stocks.find_one({"symbol": symbol.upper()}, {"_id": 0})
    if not stock:
        raise HTTPException(404, "Stock not found")
    hist = stock.get("historicalData", [])
    prediction = svc_ai_prediction(hist)
    stock["aiPrediction"] = prediction
    return R(stock)

@api.post("/markets/predict")
async def predict_stock(inp: PredictionInput, user=Depends(current_user)):
    stock = await db.stocks.find_one({"symbol": inp.stockSymbol.upper()}, {"_id": 0})
    if not stock:
        raise HTTPException(404, "Stock not found")
    hist = stock.get("historicalData", [])
    ai_pred = svc_ai_prediction(hist)
    correct = inp.predictedDirection == ai_pred["direction"]
    record = {"id": str(uuid.uuid4()), "userId": user["id"], "stockSymbol": inp.stockSymbol.upper(), "predictedDirection": inp.predictedDirection, "aiDirection": ai_pred["direction"], "aiConfidence": ai_pred["confidence"], "correct": correct, "explanation": ai_pred["explanation"], "timestamp": datetime.now(timezone.utc).isoformat()}
    await db.predictions.insert_one(record)
    return R({"userPrediction": inp.predictedDirection, "aiPrediction": ai_pred, "match": correct, "explanation": ai_pred["explanation"]}, "Prediction recorded")

@api.get("/markets/predictions")
async def get_predictions(user=Depends(current_user)):
    preds = await db.predictions.find({"userId": user["id"]}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    correct = sum(1 for p in preds if p.get("correct"))
    accuracy = round(correct / len(preds) * 100) if preds else 0
    return R({"predictions": preds, "accuracy": accuracy, "total": len(preds), "correct": correct})

@api.get("/markets/sentiment")
async def get_sentiment(user=Depends(current_user)):
    news = await db.news.find({}, {"_id": 0}).to_list(50)
    for n in news:
        n["sentiment_analysis"] = svc_sentiment(n.get("content", ""))
    return R(news)

@api.get("/markets/heatmap")
async def get_heatmap(user=Depends(current_user)):
    stocks = await db.stocks.find({}, {"_id": 0}).to_list(50)
    heatmap = {}
    for s in stocks:
        sector = s.get("sector", "Other")
        hist = s.get("historicalData", [])
        if len(hist) >= 2:
            change = (hist[-1]["close"] - hist[-2]["close"]) / hist[-2]["close"] * 100
        else:
            change = s.get("change", 0)
        if sector not in heatmap:
            heatmap[sector] = {"sector": sector, "stocks": [], "avgChange": 0}
        heatmap[sector]["stocks"].append({"symbol": s["symbol"], "name": s["name"], "change": round(change, 2)})
    for k in heatmap:
        changes = [st["change"] for st in heatmap[k]["stocks"]]
        heatmap[k]["avgChange"] = round(sum(changes) / len(changes), 2) if changes else 0
    return R(list(heatmap.values()))

# ═══════════════════════════════════════════════════════
# PORTFOLIO ROUTES
# ═══════════════════════════════════════════════════════

@api.get("/portfolio/assets")
async def get_assets(user=Depends(current_user)):
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    return R(assets)

@api.get("/portfolio/summary")
async def portfolio_summary(user=Depends(current_user)):
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    if not assets:
        return R({"totalValue": 0, "totalCost": 0, "totalGain": 0, "gainPct": 0, "allocation": [], "sectorDiversification": [], "volatility": "N/A"})
    tv = sum(a["quantity"] * a["currentPrice"] for a in assets)
    tc = sum(a["quantity"] * a["buyPrice"] for a in assets)
    tg = tv - tc
    gpct = (tg / tc * 100) if tc > 0 else 0
    # Allocation by type
    types = {}
    for a in assets:
        t = a.get("type", "equity")
        types[t] = types.get(t, 0) + a["quantity"] * a["currentPrice"]
    allocation = [{"name": k, "value": round(v), "percentage": round(v/tv*100, 1)} for k, v in types.items()]
    # Sector diversification
    sectors = {}
    for a in assets:
        s = a.get("sector", "Other")
        sectors[s] = sectors.get(s, 0) + a["quantity"] * a["currentPrice"]
    sector_div = [{"name": k, "value": round(v), "percentage": round(v/tv*100, 1)} for k, v in sectors.items()]
    # Volatility indicator
    eq_ratio = types.get("equity", 0) / tv if tv > 0 else 0
    if eq_ratio > 0.7: vol = "High"
    elif eq_ratio > 0.4: vol = "Moderate"
    else: vol = "Low"
    # Per-asset details
    details = []
    for a in assets:
        v = a["quantity"] * a["currentPrice"]
        c = a["quantity"] * a["buyPrice"]
        g = v - c
        gp = (g / c * 100) if c > 0 else 0
        details.append({**{k: a[k] for k in a if k != "userId"}, "currentValue": round(v), "costBasis": round(c), "gain": round(g), "gainPct": round(gp, 2)})
    return R({"totalValue": round(tv), "totalCost": round(tc), "totalGain": round(tg), "gainPct": round(gpct, 2), "allocation": allocation, "sectorDiversification": sector_div, "volatility": vol, "assets": details})

@api.post("/portfolio/tax/compare")
async def portfolio_tax_compare(inp: TaxCompareInput, user=Depends(current_user)):
    old = svc_old_regime(inp.income, inp.deductions_80c, inp.deductions_80d, inp.hra_exemption, inp.other_deductions)
    new = svc_new_regime(inp.income)
    better = "old" if old["total"] < new["total"] else "new"
    savings = abs(old["total"] - new["total"])
    return R({"old_regime": old, "new_regime": new, "recommended": better, "savings": round(savings)})

@api.post("/portfolio/tax/capital-gains")
async def portfolio_capital_gains(inp: CapitalGainsInput, user=Depends(current_user)):
    result = svc_capital_gains(inp.buyPrice, inp.sellPrice, inp.quantity, inp.holdingMonths, inp.assetType)
    return R(result)

@api.post("/portfolio/tax/fd")
async def portfolio_fd_tax(inp: FDTaxInput, user=Depends(current_user)):
    result = svc_fd_tax(inp.principal, inp.rate, inp.years, inp.taxBracket)
    return R(result)

# ═══════════════════════════════════════════════════════
# RISK ROUTES
# ═══════════════════════════════════════════════════════

@api.post("/risk/transaction")
async def check_transaction(inp: TransactionCheckInput, user=Depends(current_user)):
    result = svc_tx_risk(inp.amount, inp.type, inp.description, inp.recipientNew)
    return R(result)

@api.post("/risk/fraud")
async def detect_fraud(inp: FraudDetectInput, user=Depends(current_user)):
    result = svc_fraud(inp.text)
    return R(result)

# ═══════════════════════════════════════════════════════
# AI ADVISOR ROUTES
# ═══════════════════════════════════════════════════════

@api.post("/advisor/analyze")
async def advisor_analyze(inp: AdvisorQueryInput, user=Depends(current_user)):
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    advice = svc_advice(assets, user)
    record = {"id": str(uuid.uuid4()), "userId": user["id"], "query": inp.query, "response": advice, "timestamp": datetime.now(timezone.utc).isoformat()}
    await db.chat_history.insert_one(record)
    return R(advice)

@api.get("/advisor/history")
async def advisor_history(user=Depends(current_user)):
    history = await db.chat_history.find({"userId": user["id"]}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    return R(history)

# ═══════════════════════════════════════════════════════
# ALERT ROUTES
# ═══════════════════════════════════════════════════════

@api.get("/alerts")
async def get_alerts(user=Depends(current_user)):
    alerts = await db.alerts.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    unread = sum(1 for a in alerts if not a.get("is_read"))
    return R({"alerts": alerts, "unread_count": unread})

@api.post("/alerts/mark-read")
async def mark_alert_read(inp: MarkAlertReadInput, user=Depends(current_user)):
    await db.alerts.update_one({"id": inp.alertId}, {"$set": {"is_read": True}})
    return R(None, "Alert marked as read")

@api.post("/alerts/mark-all-read")
async def mark_all_alerts_read(user=Depends(current_user)):
    await db.alerts.update_many({"is_read": False}, {"$set": {"is_read": True}})
    return R(None, "All alerts marked as read")

@api.post("/alerts/generate")
async def trigger_alert_generation(user=Depends(current_user)):
    """Generate alerts from news with high impact scores."""
    news = await db.news.find({}, {"_id": 0}).to_list(50)
    created = 0
    for n in news:
        impact = svc_impact_score(n)
        if impact >= 75:
            existing = await db.alerts.find_one({"title": n["title"]})
            if not existing:
                await svc_create_alert(n, impact)
                created += 1
    return R({"alerts_created": created}, f"Generated {created} new alerts")

# ═══════════════════════════════════════════════════════
# COMMUNITY CHAT ROUTES
# ═══════════════════════════════════════════════════════

@api.get("/community/messages")
async def get_community_messages(user=Depends(current_user)):
    messages = await db.community_chat.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    return R(list(reversed(messages)))

# ═══════════════════════════════════════════════════════
# ADD ASSET ROUTE
# ═══════════════════════════════════════════════════════

@api.post("/portfolio/add-asset")
async def add_asset(inp: AddAssetInput, user=Depends(current_user)):
    stock = await db.stocks.find_one({"symbol": inp.symbol.upper()}, {"_id": 0, "historicalData": 0})
    if not stock:
        raise HTTPException(404, "Stock not found in our dataset")
    if inp.quantity <= 0:
        raise HTTPException(400, "Quantity must be positive")
    if inp.buyPrice <= 0:
        raise HTTPException(400, "Buy price must be positive")
    asset = {
        "id": str(uuid.uuid4()),
        "userId": user["id"],
        "name": stock["name"],
        "symbol": stock["symbol"],
        "type": "equity",
        "sector": stock.get("sector", "Other"),
        "quantity": inp.quantity,
        "buyPrice": inp.buyPrice,
        "currentPrice": stock["currentPrice"],
    }
    await db.assets.insert_one(asset)
    assets = await db.assets.find({"userId": user["id"]}, {"_id": 0}).to_list(100)
    health = svc_financial_health(assets)
    await db.users.update_one({"id": user["id"]}, {"$set": {"financialHealthScore": health["score"]}})
    return R({
        "asset": {k: v for k, v in asset.items() if k != "_id"},
        "updatedHealth": health
    }, f"Added {inp.quantity} shares of {stock['symbol']}")

# ═══════════════════════════════════════════════════════
# SEED DATA
# ═══════════════════════════════════════════════════════

async def seed_data():
    existing = await db.users.find_one({"email": "demo@dhandraft.com"})
    if existing:
        logger.info("Seed data already exists, skipping")
        return

    logger.info("Seeding demo data...")
    uid = str(uuid.uuid4())

    # Demo user
    await db.users.insert_one({
        "id": uid, "name": "Arjun Mehta", "email": "demo@dhandraft.com",
        "password": hash_pw("Demo123!"), "riskPersonality": "Moderate",
        "financialHealthScore": 72, "createdAt": datetime.now(timezone.utc).isoformat()
    })

    # Stocks
    stock_data = [
        {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy", "currentPrice": 2450.75, "change": 1.2, "marketCap": "16.5L Cr"},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "Technology", "currentPrice": 3890.50, "change": -0.5, "marketCap": "14.2L Cr"},
        {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking", "currentPrice": 1650.25, "change": 0.8, "marketCap": "12.4L Cr"},
        {"symbol": "INFY", "name": "Infosys", "sector": "Technology", "currentPrice": 1520.00, "change": -1.1, "marketCap": "6.3L Cr"},
        {"symbol": "ITC", "name": "ITC Limited", "sector": "FMCG", "currentPrice": 465.30, "change": 0.3, "marketCap": "5.8L Cr"},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom", "currentPrice": 1680.00, "change": 2.1, "marketCap": "9.4L Cr"},
        {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking", "currentPrice": 780.50, "change": -0.3, "marketCap": "7.0L Cr"},
        {"symbol": "SUNPHARMA", "name": "Sun Pharma", "sector": "Pharma", "currentPrice": 1820.00, "change": 1.5, "marketCap": "4.4L Cr"},
    ]
    for s in stock_data:
        s["id"] = str(uuid.uuid4())
        s["historicalData"] = svc_gen_history(s["currentPrice"])
    await db.stocks.insert_many(stock_data)

    # Assets for demo user
    assets = [
        {"id": str(uuid.uuid4()), "userId": uid, "name": "Reliance Industries", "symbol": "RELIANCE", "type": "equity", "sector": "Energy", "quantity": 20, "buyPrice": 2300, "currentPrice": 2450.75},
        {"id": str(uuid.uuid4()), "userId": uid, "name": "HDFC Bank", "symbol": "HDFCBANK", "type": "equity", "sector": "Banking", "quantity": 30, "buyPrice": 1550, "currentPrice": 1650.25},
        {"id": str(uuid.uuid4()), "userId": uid, "name": "TCS", "symbol": "TCS", "type": "equity", "sector": "Technology", "quantity": 10, "buyPrice": 3700, "currentPrice": 3890.50},
        {"id": str(uuid.uuid4()), "userId": uid, "name": "SBI Fixed Deposit", "symbol": "SBIFD", "type": "fixed_deposit", "sector": "Banking", "quantity": 1, "buyPrice": 200000, "currentPrice": 214000},
        {"id": str(uuid.uuid4()), "userId": uid, "name": "Gold ETF", "symbol": "GOLDBEES", "type": "gold", "sector": "Commodities", "quantity": 50, "buyPrice": 4800, "currentPrice": 5200},
    ]
    await db.assets.insert_many(assets)

    # Lessons
    lessons = [
        {"id": str(uuid.uuid4()), "title": "Introduction to Stock Market", "description": "Learn how the stock market works and why companies list their shares.", "category": "basics", "difficulty": "beginner", "order": 1,
         "content": "The stock market is a marketplace where shares of publicly listed companies are bought and sold. When you buy a share, you own a small part of that company. Stock prices fluctuate based on supply and demand, company performance, and market sentiment. Key concepts include: BSE and NSE are India's primary exchanges. SEBI regulates the market. Investors can trade through demat accounts. Stock indices like Sensex and Nifty track overall market performance.",
         "quiz": [
             {"question": "What is a stock?", "options": ["A type of bond", "Ownership share in a company", "A government loan", "An insurance product"], "correct": 1},
             {"question": "What does IPO stand for?", "options": ["Initial Public Offering", "Internal Price Option", "Instant Profit Order", "Investment Portfolio Optimization"], "correct": 0},
             {"question": "Who regulates the Indian stock market?", "options": ["RBI", "SEBI", "IRDA", "PFRDA"], "correct": 1},
             {"question": "Which is an Indian stock exchange?", "options": ["NASDAQ", "NYSE", "BSE", "LSE"], "correct": 2}
         ]},
        {"id": str(uuid.uuid4()), "title": "Understanding Mutual Funds", "description": "Explore how mutual funds pool money and diversify investments.", "category": "investing", "difficulty": "beginner", "order": 2,
         "content": "Mutual funds pool money from many investors to invest in stocks, bonds, or other securities. A fund manager makes investment decisions. Types include: Equity funds invest in stocks. Debt funds invest in bonds. Hybrid funds mix both. ELSS funds offer tax benefits under Section 80C. SIP (Systematic Investment Plan) allows regular small investments. NAV (Net Asset Value) represents the per-unit value of the fund.",
         "quiz": [
             {"question": "What is a mutual fund?", "options": ["A single stock", "Pooled investment vehicle", "Bank deposit", "Insurance policy"], "correct": 1},
             {"question": "What is SIP?", "options": ["Single Investment Plan", "Systematic Investment Plan", "Stock Index Price", "Savings Interest Plan"], "correct": 1},
             {"question": "Which fund type offers 80C tax benefit?", "options": ["Liquid Fund", "ELSS", "Debt Fund", "Index Fund"], "correct": 1},
             {"question": "What does NAV represent?", "options": ["Total fund value", "Per-unit fund value", "Annual returns", "Fund manager fee"], "correct": 1}
         ]},
        {"id": str(uuid.uuid4()), "title": "Risk Management Essentials", "description": "Learn to assess and manage investment risks effectively.", "category": "risk", "difficulty": "intermediate", "order": 3,
         "content": "Investment risk is the probability of losing money. Key risk types: Market risk affects all investments due to economic changes. Credit risk is the chance a borrower defaults. Liquidity risk means difficulty selling an investment. Inflation risk erodes purchasing power. Diversification across asset classes reduces overall portfolio risk. Risk tolerance depends on age, income, goals, and temperament. The risk-return tradeoff means higher potential returns come with higher risk.",
         "quiz": [
             {"question": "What is diversification?", "options": ["Buying one stock", "Spreading investments across assets", "Timing the market", "Short selling"], "correct": 1},
             {"question": "What is market risk?", "options": ["Risk of a single company", "Risk affecting all investments", "Currency risk only", "Inflation only"], "correct": 1},
             {"question": "Higher returns generally mean:", "options": ["Lower risk", "Higher risk", "No risk", "Guaranteed profits"], "correct": 1},
             {"question": "What reduces portfolio risk?", "options": ["Concentration", "Leverage", "Diversification", "Day trading"], "correct": 2}
         ]},
        {"id": str(uuid.uuid4()), "title": "Tax Planning for Investors", "description": "Master tax-saving strategies for your investments.", "category": "tax", "difficulty": "intermediate", "order": 4,
         "content": "India has two tax regimes: Old and New. Old regime allows deductions like 80C (up to Rs.1.5L), 80D (health insurance), and HRA. New regime has lower rates but fewer deductions. Key tax concepts: LTCG on equity above Rs.1.25L is taxed at 12.5%. STCG on equity is taxed at 20%. FD interest is fully taxable. ELSS provides 80C benefit with 3-year lock-in. Tax-loss harvesting offsets gains with losses.",
         "quiz": [
             {"question": "Maximum 80C deduction limit?", "options": ["Rs.1,00,000", "Rs.1,50,000", "Rs.2,00,000", "Rs.2,50,000"], "correct": 1},
             {"question": "LTCG tax rate on equity?", "options": ["10%", "12.5%", "15%", "20%"], "correct": 1},
             {"question": "ELSS lock-in period?", "options": ["1 year", "3 years", "5 years", "No lock-in"], "correct": 1},
             {"question": "Which regime has lower rates but fewer deductions?", "options": ["Old Regime", "New Regime", "Both same", "Neither"], "correct": 1}
         ]},
        {"id": str(uuid.uuid4()), "title": "Portfolio Diversification Strategy", "description": "Build a well-balanced portfolio across asset classes.", "category": "strategy", "difficulty": "advanced", "order": 5,
         "content": "A well-diversified portfolio spreads risk across asset classes. Asset allocation strategies: Conservative (30% equity, 50% debt, 20% gold). Moderate (50% equity, 30% debt, 20% alternatives). Aggressive (70% equity, 20% debt, 10% alternatives). Rebalancing quarterly maintains target allocation. Sector diversification avoids concentration risk. Geographic diversification includes international funds. Age-based rule: Equity % = 100 minus your age.",
         "quiz": [
             {"question": "Conservative portfolio has most allocation in?", "options": ["Equity", "Debt", "Gold", "Real Estate"], "correct": 1},
             {"question": "How often should you rebalance?", "options": ["Daily", "Weekly", "Quarterly", "Never"], "correct": 2},
             {"question": "Age-based equity rule: Equity % =", "options": ["Age", "100 - Age", "Age x 2", "50% always"], "correct": 1},
             {"question": "Sector diversification helps with:", "options": ["Higher returns guaranteed", "Reducing concentration risk", "Tax savings", "Lower fees"], "correct": 1}
         ]},
    ]
    await db.lessons.insert_many(lessons)

    # News
    news = [
        {"id": str(uuid.uuid4()), "title": "Reliance Energy Division Reports Strong Growth", "content": "Reliance Industries energy division shows strong profit growth driven by robust demand and strategic expansion in green energy initiatives.", "sector": "Energy", "date": "2024-01-15"},
        {"id": str(uuid.uuid4()), "title": "IT Sector Faces Global Headwinds", "content": "Indian IT companies facing decline and weakness due to global economic slowdown and reduced client spending in key markets.", "sector": "Technology", "date": "2024-01-14"},
        {"id": str(uuid.uuid4()), "title": "Banking Sector Maintains Stability", "content": "Banks maintain steady positive performance with strong loan growth despite RBI rate adjustments and regulatory changes.", "sector": "Banking", "date": "2024-01-13"},
        {"id": str(uuid.uuid4()), "title": "FMCG Rural Recovery Continues", "content": "FMCG sector reports positive growth and strong rally driven by rural demand surge and volume recovery across categories.", "sector": "FMCG", "date": "2024-01-12"},
        {"id": str(uuid.uuid4()), "title": "Pharma Exports Face Challenges", "content": "Pharmaceutical companies dealing with risk of regulatory decline in export markets affecting revenue growth.", "sector": "Pharma", "date": "2024-01-11"},
        {"id": str(uuid.uuid4()), "title": "Telecom Sector Record Growth", "content": "India telecom companies report record data consumption growth and strong subscriber gain with positive revenue trends.", "sector": "Telecom", "date": "2024-01-10"},
    ]
    await db.news.insert_many(news)

    # Generate alerts from high-impact news
    for n in news:
        impact = svc_impact_score(n)
        if impact >= 75:
            sent = svc_sentiment(n.get("content", ""))
            severity = "High" if impact >= 85 else "Medium"
            await db.alerts.insert_one({
                "id": str(uuid.uuid4()),
                "title": n["title"],
                "impact_score": impact,
                "impacted_sectors": [n.get("sector", "General")],
                "severity": severity,
                "explanation": f"{sent['label']} sentiment in {n.get('sector', 'market')} sector. Confidence: {sent['confidence']}%.",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False,
            })

    # Seed community messages
    community_msgs = [
        {"id": str(uuid.uuid4()), "userId": uid, "username": "Arjun Mehta", "message": "Has anyone looked at Reliance's energy division results? Impressive numbers!", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()},
        {"id": str(uuid.uuid4()), "userId": str(uuid.uuid4()), "username": "Priya Sharma", "message": "IT sector seems weak this quarter. TCS and Infy both under pressure.", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()},
        {"id": str(uuid.uuid4()), "userId": str(uuid.uuid4()), "username": "Rahul Verma", "message": "Banking sector is holding steady. HDFC Bank looks solid for long term.", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()},
        {"id": str(uuid.uuid4()), "userId": str(uuid.uuid4()), "username": "Sneha Patel", "message": "Anyone investing in pharma? Sun Pharma has been doing well.", "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()},
    ]
    await db.community_chat.insert_many(community_msgs)

    logger.info("Seed data created successfully!")

# ═══════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════

app.include_router(api)

# ═══════════════════════════════════════════════════════
# WEBSOCKET ENDPOINTS (on app, not router)
# ═══════════════════════════════════════════════════════

async def ws_auth(websocket: WebSocket):
    """Authenticate WebSocket via query param token."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return None
    try:
        p = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user = await db.users.find_one({"id": p["uid"]}, {"_id": 0, "password": 0})
        if not user:
            await websocket.close(code=4001)
            return None
        return user
    except Exception:
        await websocket.close(code=4001)
        return None

@app.websocket("/api/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    user = await ws_auth(websocket)
    if not user:
        return
    await alert_mgr.connect(websocket, user["id"])
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_mgr.disconnect(websocket, user["id"])

@app.websocket("/api/ws/chat")
async def ws_chat(websocket: WebSocket):
    user = await ws_auth(websocket)
    if not user:
        return
    await chat_mgr.connect(websocket)
    try:
        recent = await db.community_chat.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
        await websocket.send_json({"type": "history", "data": list(reversed(recent))})
        last_msg_time = {}
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg = data.get("message", "").strip()
            if not msg or len(msg) > 500:
                continue
            now = datetime.now(timezone.utc)
            uid = user["id"]
            if uid in last_msg_time and (now - last_msg_time[uid]).total_seconds() < 2:
                await websocket.send_json({"type": "error", "data": "Rate limited. Wait 2 seconds."})
                continue
            last_msg_time[uid] = now
            record = {
                "id": str(uuid.uuid4()),
                "userId": uid,
                "username": user["name"],
                "message": msg,
                "timestamp": now.isoformat()
            }
            await db.community_chat.insert_one({**record})
            await chat_mgr.broadcast({"type": "message", "data": record})
    except WebSocketDisconnect:
        chat_mgr.disconnect(websocket)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await seed_data()

@app.on_event("shutdown")
async def shutdown():
    client.close()
