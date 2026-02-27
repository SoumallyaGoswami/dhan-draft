# 🚀 DHAN-DRAFT

AI-powered financial decision intelligence platform built for modern investors.

> Built with ❤️ using FastAPI, React, MongoDB Atlas & deployed on Render + Vercel.

---

## 🌍 Live Demo

- 🔗 Frontend: https://your-frontend-url.vercel.app
- 🔗 Backend API: https://dhan-draft-1.onrender.com
- 📄 API Docs: https://dhan-draft-1.onrender.com/docs

---

## 🧠 What is DHAN-DRAFT?

DHAN-DRAFT is an AI-powered financial assistant designed to:

- 📊 Analyze market data
- 🧮 Evaluate portfolio risk
- 🤖 Provide AI-driven training & insights
- 🔐 Securely manage user accounts
- 📈 Deliver intelligent financial recommendations

---

## 🏗️ Tech Stack

### 🖥️ Frontend
- React (Create React App)
- Tailwind / Custom UI
- Recharts (Data Visualization)
- Axios / Fetch API

### ⚙️ Backend
- FastAPI
- Uvicorn
- Motor (Async MongoDB)
- PyJWT (Authentication)
- Passlib + Bcrypt (Password Hashing)

### 🗄️ Database
- MongoDB Atlas (Cloud Hosted)

### ☁️ Deployment
- Frontend → Vercel
- Backend → Render
- Database → MongoDB Atlas

---

## 📂 Project Structure
dhan-draft/
│
├── frontend/          # React frontend
│
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   ├── utils/
│   │   └── database.py
│   └── server.py
│
└── README.md
---

## ⚙️ Local Development Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/SoumallyaGoswami/dhan-draft.git
cd dhan-draft

2️⃣ Backend Setup
cd backend

python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
Create .env file:
MONGO_URL=your_mongodb_connection_string
SECRET_KEY=your_secret_key
Run server:
uvicorn server:app --reload
Backend runs on:
http://localhost:8000

3️⃣ Frontend Setup
cd frontend
yarn install
yarn start
Create .env inside frontend:
REACT_APP_BACKEND_URL=http://localhost:8000

Frontend runs on:
http://localhost:3000

🔐 Environment Variables

Backend (.env)
MONGO_URL=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=

Frontend (.env)
REACT_APP_BACKEND_URL=

🧪 API Endpoints
GET
/
API status
GET
/health
Health check
POST
/auth/login
Login user
POST
/auth/register
Register user
POST
/ai/trainer
AI trainer endpoint

Full interactive docs available at:
/docs

🚀 Deployment Architecture
User
   ↓
Vercel (Frontend)
   ↓
Render (FastAPI Backend)
   ↓
MongoDB Atlas

🛡️ Security
	•	Passwords hashed with bcrypt
	•	JWT-based authentication
	•	Environment variables protected in deployment
	•	MongoDB Atlas IP whitelist configured

⸻

📌 Future Improvements
	•	Real AI integration (OpenAI / Custom model)
	•	Portfolio optimization engine
	•	Market live data integration
	•	Role-based user access
	•	Advanced analytics dashboard

⸻

👨‍💻 Team

Built by:
	•	Soumallya Goswami
	•	Team DHAN-DRAFT

⸻

📜 License

MIT License

⸻

⭐ If You Like This Project

Give it a ⭐ on GitHub!
---

# 🔥 Optional: Want It To Look Even More Pro?

I can:

- Add badges (Deploy status, License, Build passing)
- Add screenshots section
- Add architecture diagram
- Add hackathon badge
- Add animated GIF preview

---

Tell me:

Is this for:
- Hackathon submission?
- Portfolio project?
- Production startup?

I’ll tailor it next-level accordingly. 🚀
