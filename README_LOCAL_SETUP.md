# DHAN-DRAFT - Local Development Setup

## 🎯 Overview

This is a clean, production-ready version of DHAN-DRAFT that runs in any standard local development environment **without any internal Emergent plugins or dependencies**.

All visual editing metadata, Babel transformations, and runtime dependencies have been removed for maximum compatibility and simplicity.

---

## 📋 Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.9+
- **MongoDB** 4.4+ (running locally on port 27017)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
yarn install
# OR
npm install
```

### 2. Configure Environment

The app works with safe defaults. For custom configuration:

**Backend** (`backend/.env`):
```env
MONGO_URL=mongodb://localhost:27017/
DB_NAME=dhan_draft_db
CORS_ORIGINS=*
JWT_SECRET=your-secret-key-here
```

**Frontend** (`frontend/.env`):
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 3. Start MongoDB

```bash
# If MongoDB is not running:
mongod --dbpath /path/to/data/db
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
# OR
npm start
```

### 5. Access the App

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

### 6. Demo Credentials

- **Email:** demo@dhandraft.com
- **Password:** Demo123!

---

## 🗂️ Project Structure

```
dhan-draft/
├── backend/                    # FastAPI backend
│   ├── app/                   # Modular application code
│   │   ├── config.py         # Environment configuration
│   │   ├── database.py       # MongoDB + indexes
│   │   ├── main.py           # FastAPI app
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # Business logic (6 services)
│   │   ├── routes/           # API endpoints (9 routers)
│   │   ├── websockets/       # Real-time handlers
│   │   └── utils/            # Helpers & seed data
│   ├── server.py             # Entry point (imports from app/)
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment variables
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   │   └── ui/          # Shadcn UI components (45+)
│   │   ├── pages/           # Page components (8 pages)
│   │   ├── context/         # React context (Auth)
│   │   ├── hooks/           # Custom hooks
│   │   └── lib/             # Utilities & API client
│   ├── public/              # Static assets
│   ├── package.json         # Dependencies
│   ├── craco.config.js      # Build configuration
│   └── .env                 # Environment variables
│
└── README_LOCAL_SETUP.md    # This file
```

---

## 🔧 What Was Removed

To make this a standard local development setup, the following Emergent-specific components were removed:

### Removed Babel Plugins
- ❌ `plugins/visual-edits/babel-metadata-plugin.js` (2,160 lines)
- ❌ `plugins/visual-edits/dev-server-setup.js` (34KB)
- ❌ `plugins/health-check/webpack-health-plugin.js`
- ❌ `plugins/health-check/health-endpoints.js`

### Removed Metadata Attributes
All JSX elements previously had these attributes (now removed):
- ❌ `x-file-name`
- ❌ `x-line-number`
- ❌ `x-id`
- ❌ `x-component`
- ❌ `x-dynamic`
- ❌ `x-source-*` (type, var, file, line, path, editable)
- ❌ `x-array-*` (var, file, line, item-param)
- ❌ `x-excluded`
- ❌ `data-ve-dynamic`

### Simplified Configuration
- ✅ Clean `craco.config.js` (no custom Babel plugins)
- ✅ Standard React tooling only
- ✅ No AST traversal or file system scanning
- ✅ No Emergent runtime dependencies

---

## 📦 Package.json Changes

**Before** (with Emergent plugins):
```json
{
  "scripts": {
    "start": "craco start",  // With visual-edits plugins
    "build": "craco build"
  }
}
```

**After** (clean setup):
```json
{
  "scripts": {
    "start": "craco start",  // Standard React only
    "build": "craco build"
  }
}
```

No dependencies changed - only internal plugins removed.

---

## 🐛 Troubleshooting

### MongoDB Connection Error
```
Error: connect ECONNREFUSED 127.0.0.1:27017
```
**Solution:** Make sure MongoDB is running:
```bash
mongod --dbpath /path/to/data
```

### Port Already in Use
```
Error: Port 3000 is already in use
```
**Solution:** Kill the process or use a different port:
```bash
# Kill existing process
lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 yarn start
```

### Backend Environment Variables
```
KeyError: 'MONGO_URL'
```
**Solution:** The app now uses safe defaults. Create `.env` file if needed:
```bash
cd backend
cat > .env <<EOF
MONGO_URL=mongodb://localhost:27017/
DB_NAME=dhan_draft_db
EOF
```

### CORS Errors
```
Access to XMLHttpRequest blocked by CORS policy
```
**Solution:** Make sure backend `.env` has:
```env
CORS_ORIGINS=http://localhost:3000
```
Or use `*` for development:
```env
CORS_ORIGINS=*
```

---

## 🧪 Running Tests

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
yarn test
# OR
npm test
```

---

## 📚 API Documentation

Once the backend is running, visit:

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **Health Check:** http://localhost:8001/health

### API Endpoints

**Authentication:**
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login user
- GET `/api/auth/me` - Get current user

**Overview:**
- GET `/api/overview/summary` - Dashboard summary

**Learn:**
- GET `/api/learn/lessons` - Get all lessons
- GET `/api/learn/lessons/{id}` - Get lesson details
- POST `/api/learn/quiz/submit` - Submit quiz
- GET `/api/learn/quiz/history` - Quiz history
- POST `/api/learn/tax-compare` - Compare tax regimes
- GET `/api/learn/bank-rates` - Bank interest rates

**Markets:**
- GET `/api/markets/stocks` - List stocks
- GET `/api/markets/stocks/{symbol}` - Stock details
- POST `/api/markets/predict` - Submit prediction
- GET `/api/markets/predictions` - User predictions (paginated)
- GET `/api/markets/sentiment` - Sentiment analysis
- GET `/api/markets/heatmap` - Market heatmap

**Portfolio:**
- GET `/api/portfolio/assets` - User assets
- GET `/api/portfolio/summary` - Portfolio summary
- POST `/api/portfolio/add-asset` - Add asset
- POST `/api/portfolio/tax/compare` - Tax comparison
- POST `/api/portfolio/tax/capital-gains` - Capital gains tax
- POST `/api/portfolio/tax/fd` - FD tax calculation

**Risk & Safety:**
- POST `/api/risk/transaction` - Transaction risk analysis
- POST `/api/risk/fraud` - Fraud detection

**AI Advisor:**
- POST `/api/advisor/analyze` - Get AI advice
- GET `/api/advisor/history` - Advisor history

**Alerts:**
- GET `/api/alerts` - Get alerts (paginated)
- POST `/api/alerts/mark-read` - Mark alert read
- POST `/api/alerts/mark-all-read` - Mark all read
- POST `/api/alerts/generate` - Generate alerts

**Community:**
- GET `/api/community/messages` - Community messages

**WebSocket:**
- WS `/api/ws/alerts` - Real-time alerts
- WS `/api/ws/chat` - Community chat

---

## 🌍 Production Deployment

### Environment Variables (Production)

**Backend:**
```env
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/
DB_NAME=dhan_draft_prod
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET=<strong-random-secret>
```

**Frontend:**
```env
REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

### Build Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001

# Frontend
cd frontend
yarn build
# Serve the 'build' folder with nginx or any static server
```

---

## 🔑 Key Features

### Backend
- ✅ Modular FastAPI architecture (31 files, 2,380 lines)
- ✅ MongoDB with 15 performance indexes
- ✅ JWT authentication with bcrypt
- ✅ WebSocket support for real-time features
- ✅ Pagination for high-volume endpoints
- ✅ TTL indexes for auto-cleanup
- ✅ Comprehensive API documentation (Swagger/ReDoc)

### Frontend
- ✅ React 19 with modern hooks
- ✅ Tailwind CSS + 45+ Shadcn UI components
- ✅ React Router v7 for navigation
- ✅ Axios for API calls with interceptors
- ✅ Context API for authentication
- ✅ Recharts for data visualization
- ✅ WebSocket integration for real-time updates

### Features
- 📊 Financial health scoring
- 🎯 Risk personality assessment
- 📈 Stock market predictions (SMA-based)
- 💰 Tax calculators (3 types)
- 🛡️ Transaction risk analysis
- 🚨 Fraud detection with keyword highlighting
- 🤖 AI advisor with rule-based strategies
- 📢 Real-time alerts and notifications
- 💬 Community chat

---

## 📝 Development Notes

### No Visual Editing Dependencies
This version is completely independent of any visual editing runtime. All code is standard React and FastAPI.

### Clean Babel Configuration
The Babel configuration is minimal and standard. No custom AST transformations or metadata injection.

### Standard Tooling
- Uses Create React App (via craco for path aliases)
- Standard FastAPI with uvicorn
- No custom build pipelines or transformations

### Environment Safety
The backend gracefully handles missing environment variables with safe defaults and clear warning messages.

---

## 🤝 Contributing

This is a clean, standalone version of the application. Contributions should maintain:
- Standard React patterns (no custom Babel plugins)
- Clean FastAPI architecture
- No external runtime dependencies
- Clear error messages and logging

---

## 📄 License

[Your License Here]

---

## 🆘 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Review backend logs: Check console output from uvicorn
3. Review frontend logs: Check browser console (F12)
4. Verify MongoDB is running and accessible

---

**Version:** 2.0.0 (Clean Local Setup)  
**Last Updated:** February 2026
