# 🚀 Quick Start Guide - DHAN-DRAFT Local Development

## Prerequisites Check

```bash
# Check Node.js (need 18+)
node --version

# Check Python (need 3.9+)
python --version

# Check MongoDB is installed
mongod --version

# Check yarn (or use npm)
yarn --version
```

---

## Step 1: Start MongoDB

```bash
# Option A: If MongoDB is already running as a service
# Nothing to do, skip to Step 2

# Option B: Start MongoDB manually
mongod --dbpath ~/data/db

# Option C: Using Homebrew (Mac)
brew services start mongodb-community

# Option D: Using systemctl (Linux)
sudo systemctl start mongod
```

**Verify MongoDB is running:**
```bash
# Should connect successfully
mongo --eval "db.runCommand({ connectionStatus: 1 })"
```

---

## Step 2: Install Dependencies

### Backend
```bash
cd backend
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
yarn install
# OR if you prefer npm:
npm install
```

---

## Step 3: Configure Environment (Optional)

The app works with sensible defaults. Only configure if needed:

### Backend (optional)
```bash
cd backend
cat > .env <<'EOF'
MONGO_URL=mongodb://localhost:27017/
DB_NAME=dhan_draft_db
CORS_ORIGINS=*
JWT_SECRET=your-secret-key-change-in-production
EOF
```

### Frontend (optional)
```bash
cd frontend
cat > .env <<'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
```

---

## Step 4: Start the Application

### Terminal 1 - Backend

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Connecting to MongoDB...
INFO:     Creating database indexes...
INFO:     ✓ All indexes created successfully
INFO:     Seeding demo data...
INFO:     ✅ Seed data created successfully!
INFO:     Application startup complete.
```

### Terminal 2 - Frontend

```bash
cd frontend
yarn start
# OR
npm start
```

**Expected output:**
```
Starting the development server...

Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
To create a production build, use yarn build.
```

---

## Step 5: Access the Application

### Open in Browser

- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://localhost:8001/docs
- **Backend Health:** http://localhost:8001/health

### Login with Demo Account

```
Email: demo@dhandraft.com
Password: Demo123!
```

---

## 🎯 One-Line Startup (After Setup)

Once you have dependencies installed and MongoDB running:

```bash
# Terminal 1: Backend
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend && yarn start
```

---

## 🐛 Common Issues & Solutions

### Port 3000 Already in Use

```bash
# Kill the process
lsof -ti:3000 | xargs kill -9

# Or use a different port
PORT=3001 yarn start
```

### Port 8001 Already in Use

```bash
# Kill the process
lsof -ti:8001 | xargs kill -9

# Or use a different port
uvicorn server:app --host 0.0.0.0 --port 8002 --reload
# Then update frontend/.env to match
```

### MongoDB Connection Error

```
pymongo.errors.ServerSelectionTimeoutError
```

**Solution:** Make sure MongoDB is running
```bash
# Check if MongoDB is running
ps aux | grep mongod

# Start MongoDB if not running
mongod --dbpath ~/data/db
```

### Module Not Found Error (Backend)

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:** Install requirements
```bash
cd backend
pip install -r requirements.txt
```

### Module Not Found Error (Frontend)

```
Cannot find module 'react'
```

**Solution:** Install dependencies
```bash
cd frontend
rm -rf node_modules
yarn install
```

### Database Seed Data Already Exists

```
INFO: Seed data already exists, skipping...
```

**This is normal!** The app only seeds data once. To reset:
```bash
# Connect to MongoDB
mongo

# Drop database
use dhan_draft_db
db.dropDatabase()

# Restart backend - will re-seed
```

---

## 📊 Verify Everything is Working

### 1. Backend Health Check

```bash
curl http://localhost:8001/health
```

**Expected:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "architecture": "modular"
}
```

### 2. Test Login API

```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@dhandraft.com",
    "password": "Demo123!"
  }'
```

**Expected:**
```json
{
  "success": true,
  "data": {
    "token": "eyJ...",
    "user": {
      "id": "...",
      "name": "Arjun Mehta",
      "email": "demo@dhandraft.com"
    }
  },
  "message": "Login successful"
}
```

### 3. Frontend Accessibility

Visit http://localhost:3000 - should see login page

---

## 🎓 Development Workflow

### Making Changes

**Backend changes:**
- Edit files in `/backend/app/`
- Server auto-reloads (thanks to `--reload` flag)
- Check terminal for errors

**Frontend changes:**
- Edit files in `/frontend/src/`
- Page auto-refreshes (hot reload)
- Check browser console for errors

### Viewing Logs

**Backend logs:**
```bash
# Server logs appear in the terminal where uvicorn is running
# Look for INFO, WARNING, ERROR messages
```

**Frontend logs:**
```bash
# Webpack logs in terminal
# Runtime logs in browser console (F12)
```

### Database Inspection

```bash
# Connect to MongoDB
mongo

# Switch to app database
use dhan_draft_db

# List collections
show collections

# View users
db.users.find().pretty()

# View stocks
db.stocks.find().pretty()
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

## 🏗️ Production Build

### Frontend
```bash
cd frontend
yarn build
# Creates optimized build in /frontend/build/
```

### Backend
```bash
# No build needed for backend
# Just make sure requirements.txt is up to date
pip freeze > requirements.txt
```

---

## 📚 API Documentation

Once running, explore the interactive API docs:

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

You can test all API endpoints directly from the Swagger UI!

---

## 🛑 Stopping the Application

```bash
# In each terminal, press:
Ctrl + C

# Or if running in background:
pkill -f "uvicorn"
pkill -f "react-scripts"
```

---

## 🔄 Restart After Changes

**No restart needed for:**
- React component changes (auto hot-reload)
- Backend route changes (auto reload with --reload flag)
- CSS/Tailwind changes (auto refresh)

**Restart required for:**
- New npm packages: `Ctrl+C` → `yarn install` → `yarn start`
- New pip packages: `Ctrl+C` → `pip install package` → restart uvicorn
- .env changes: Restart both frontend and backend

---

## ✅ Success Indicators

You'll know everything is working when:

1. ✅ Backend terminal shows "Application startup complete"
2. ✅ Frontend terminal shows "Compiled successfully!"
3. ✅ Browser opens to http://localhost:3000
4. ✅ Login page appears with clean design
5. ✅ Can login with demo@dhandraft.com / Demo123!
6. ✅ Dashboard shows with financial data
7. ✅ No errors in browser console (F12)
8. ✅ No errors in backend terminal

---

## 🎉 You're Ready!

The application is now running locally with:
- ✅ No Emergent dependencies
- ✅ Standard React + FastAPI setup
- ✅ Clean, debuggable code
- ✅ All features working

Enjoy developing! 🚀

---

## 📖 Additional Resources

- **Full Setup Guide:** `/app/README_LOCAL_SETUP.md`
- **Change Summary:** `/app/REFACTORING_LOCAL_SUMMARY.md`
- **Verification:** `/app/VERIFICATION_CHECKLIST.md`
- **Backend Architecture:** `/app/backend/REFACTORING_SUMMARY.md`

---

**Need Help?**
1. Check the Troubleshooting section above
2. Review backend terminal logs
3. Check browser console (F12)
4. Verify MongoDB is running
5. Ensure ports 3000 and 8001 are free

---

**Version:** 2.0.0 (Clean Local Setup)  
**Last Updated:** February 2026
