"""Seed demo data for application."""
import uuid
import logging
from datetime import datetime, timezone, timedelta

from ..database import get_db
from ..services.auth import hash_password
from ..services.market import generate_stock_history, analyze_sentiment, calculate_impact_score

logger = logging.getLogger(__name__)


async def seed_demo_data():
    """Seed database with demo data if not already present."""
    db = get_db()
    
    # Check if data already exists
    existing_user = await db.users.find_one({"email": "demo@dhandraft.com"})
    if existing_user:
        logger.info("Seed data already exists, skipping...")
        return
    
    logger.info("Seeding demo data...")
    
    demo_user_id = str(uuid.uuid4())
    
    # Demo user
    await db.users.insert_one({
        "id": demo_user_id,
        "name": "Arjun Mehta",
        "email": "demo@dhandraft.com",
        "password": hash_password("Demo123!"),
        "riskPersonality": "Moderate",
        "financialHealthScore": 72,
        "createdAt": datetime.now(timezone.utc).isoformat()
    })
    
    # Stock data with historical prices
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
    
    for stock in stock_data:
        stock["id"] = str(uuid.uuid4())
        stock["historicalData"] = generate_stock_history(stock["currentPrice"])
    
    await db.stocks.insert_many(stock_data)
    
    # Demo user's portfolio assets
    assets = [
        {"id": str(uuid.uuid4()), "userId": demo_user_id, "name": "Reliance Industries", "symbol": "RELIANCE", "type": "equity", "sector": "Energy", "quantity": 20, "buyPrice": 2300, "currentPrice": 2450.75},
        {"id": str(uuid.uuid4()), "userId": demo_user_id, "name": "HDFC Bank", "symbol": "HDFCBANK", "type": "equity", "sector": "Banking", "quantity": 30, "buyPrice": 1550, "currentPrice": 1650.25},
        {"id": str(uuid.uuid4()), "userId": demo_user_id, "name": "TCS", "symbol": "TCS", "type": "equity", "sector": "Technology", "quantity": 10, "buyPrice": 3700, "currentPrice": 3890.50},
        {"id": str(uuid.uuid4()), "userId": demo_user_id, "name": "SBI Fixed Deposit", "symbol": "SBIFD", "type": "fixed_deposit", "sector": "Banking", "quantity": 1, "buyPrice": 200000, "currentPrice": 214000},
        {"id": str(uuid.uuid4()), "userId": demo_user_id, "name": "Gold ETF", "symbol": "GOLDBEES", "type": "gold", "sector": "Commodities", "quantity": 50, "buyPrice": 4800, "currentPrice": 5200},
    ]
    
    await db.assets.insert_many(assets)
    
    # Educational lessons with quizzes
    lessons = [
        {
            "id": str(uuid.uuid4()),
            "title": "Introduction to Stock Market",
            "description": "Learn how the stock market works and why companies list their shares.",
            "category": "basics",
            "difficulty": "beginner",
            "order": 1,
            "content": "The stock market is a marketplace where shares of publicly listed companies are bought and sold. When you buy a share, you own a small part of that company. Stock prices fluctuate based on supply and demand, company performance, and market sentiment. Key concepts include: BSE and NSE are India's primary exchanges. SEBI regulates the market. Investors can trade through demat accounts. Stock indices like Sensex and Nifty track overall market performance.",
            "quiz": [
                {"question": "What is a stock?", "options": ["A type of bond", "Ownership share in a company", "A government loan", "An insurance product"], "correct": 1},
                {"question": "What does IPO stand for?", "options": ["Initial Public Offering", "Internal Price Option", "Instant Profit Order", "Investment Portfolio Optimization"], "correct": 0},
                {"question": "Who regulates the Indian stock market?", "options": ["RBI", "SEBI", "IRDA", "PFRDA"], "correct": 1},
                {"question": "Which is an Indian stock exchange?", "options": ["NASDAQ", "NYSE", "BSE", "LSE"], "correct": 2}
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Understanding Mutual Funds",
            "description": "Explore how mutual funds pool money and diversify investments.",
            "category": "investing",
            "difficulty": "beginner",
            "order": 2,
            "content": "Mutual funds pool money from many investors to invest in stocks, bonds, or other securities. A fund manager makes investment decisions. Types include: Equity funds invest in stocks. Debt funds invest in bonds. Hybrid funds mix both. ELSS funds offer tax benefits under Section 80C. SIP (Systematic Investment Plan) allows regular small investments. NAV (Net Asset Value) represents the per-unit value of the fund.",
            "quiz": [
                {"question": "What is a mutual fund?", "options": ["A single stock", "Pooled investment vehicle", "Bank deposit", "Insurance policy"], "correct": 1},
                {"question": "What is SIP?", "options": ["Single Investment Plan", "Systematic Investment Plan", "Stock Index Price", "Savings Interest Plan"], "correct": 1},
                {"question": "Which fund type offers 80C tax benefit?", "options": ["Liquid Fund", "ELSS", "Debt Fund", "Index Fund"], "correct": 1},
                {"question": "What does NAV represent?", "options": ["Total fund value", "Per-unit fund value", "Annual returns", "Fund manager fee"], "correct": 1}
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Risk Management Essentials",
            "description": "Learn to assess and manage investment risks effectively.",
            "category": "risk",
            "difficulty": "intermediate",
            "order": 3,
            "content": "Investment risk is the probability of losing money. Key risk types: Market risk affects all investments due to economic changes. Credit risk is the chance a borrower defaults. Liquidity risk means difficulty selling an investment. Inflation risk erodes purchasing power. Diversification across asset classes reduces overall portfolio risk. Risk tolerance depends on age, income, goals, and temperament. The risk-return tradeoff means higher potential returns come with higher risk.",
            "quiz": [
                {"question": "What is diversification?", "options": ["Buying one stock", "Spreading investments across assets", "Timing the market", "Short selling"], "correct": 1},
                {"question": "What is market risk?", "options": ["Risk of a single company", "Risk affecting all investments", "Currency risk only", "Inflation only"], "correct": 1},
                {"question": "Higher returns generally mean:", "options": ["Lower risk", "Higher risk", "No risk", "Guaranteed profits"], "correct": 1},
                {"question": "What reduces portfolio risk?", "options": ["Concentration", "Leverage", "Diversification", "Day trading"], "correct": 2}
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Tax Planning for Investors",
            "description": "Master tax-saving strategies for your investments.",
            "category": "tax",
            "difficulty": "intermediate",
            "order": 4,
            "content": "India has two tax regimes: Old and New. Old regime allows deductions like 80C (up to Rs.1.5L), 80D (health insurance), and HRA. New regime has lower rates but fewer deductions. Key tax concepts: LTCG on equity above Rs.1.25L is taxed at 12.5%. STCG on equity is taxed at 20%. FD interest is fully taxable. ELSS provides 80C benefit with 3-year lock-in. Tax-loss harvesting offsets gains with losses.",
            "quiz": [
                {"question": "Maximum 80C deduction limit?", "options": ["Rs.1,00,000", "Rs.1,50,000", "Rs.2,00,000", "Rs.2,50,000"], "correct": 1},
                {"question": "LTCG tax rate on equity?", "options": ["10%", "12.5%", "15%", "20%"], "correct": 1},
                {"question": "ELSS lock-in period?", "options": ["1 year", "3 years", "5 years", "No lock-in"], "correct": 1},
                {"question": "Which regime has lower rates but fewer deductions?", "options": ["Old Regime", "New Regime", "Both same", "Neither"], "correct": 1}
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Portfolio Diversification Strategy",
            "description": "Build a well-balanced portfolio across asset classes.",
            "category": "strategy",
            "difficulty": "advanced",
            "order": 5,
            "content": "A well-diversified portfolio spreads risk across asset classes. Asset allocation strategies: Conservative (30% equity, 50% debt, 20% gold). Moderate (50% equity, 30% debt, 20% alternatives). Aggressive (70% equity, 20% debt, 10% alternatives). Rebalancing quarterly maintains target allocation. Sector diversification avoids concentration risk. Geographic diversification includes international funds. Age-based rule: Equity % = 100 minus your age.",
            "quiz": [
                {"question": "Conservative portfolio has most allocation in?", "options": ["Equity", "Debt", "Gold", "Real Estate"], "correct": 1},
                {"question": "How often should you rebalance?", "options": ["Daily", "Weekly", "Quarterly", "Never"], "correct": 2},
                {"question": "Age-based equity rule: Equity % =", "options": ["Age", "100 - Age", "Age x 2", "50% always"], "correct": 1},
                {"question": "Sector diversification helps with:", "options": ["Higher returns guaranteed", "Reducing concentration risk", "Tax savings", "Lower fees"], "correct": 1}
            ]
        }
    ]
    
    await db.lessons.insert_many(lessons)
    
    # News articles
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
    for news_item in news:
        impact = calculate_impact_score(news_item)
        if impact >= 75:
            sentiment = analyze_sentiment(news_item.get("content", ""))
            severity = "High" if impact >= 85 else "Medium"
            
            await db.alerts.insert_one({
                "id": str(uuid.uuid4()),
                "title": news_item["title"],
                "impact_score": impact,
                "impacted_sectors": [news_item.get("sector", "General")],
                "severity": severity,
                "explanation": f"{sentiment['label']} sentiment in {news_item.get('sector', 'market')} sector. Confidence: {sentiment['confidence']}%.",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False
            })
    
    # Community chat messages
    community_messages = [
        {"id": str(uuid.uuid4()), "userId": demo_user_id, "username": "Arjun Mehta", "message": "Has anyone looked at Reliance's energy division results? Impressive numbers!", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()},
        {"id": str(uuid.uuid4()), "userId": str(uuid.uuid4()), "username": "Priya Sharma", "message": "IT sector seems weak this quarter. TCS and Infy both under pressure.", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()},
        {"id": str(uuid.uuid4()), "userId": str(uuid.uuid4()), "username": "Rahul Verma", "message": "Banking sector is holding steady. HDFC Bank looks solid for long term.", "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()},
        {"id": str(uuid.uuid4()), "userId": str(uuid.uuid4()), "username": "Sneha Patel", "message": "Anyone investing in pharma? Sun Pharma has been doing well.", "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()},
    ]
    
    await db.community_chat.insert_many(community_messages)
    
    logger.info("✅ Seed data created successfully!")
