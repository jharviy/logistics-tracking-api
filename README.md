# 📦 LogiTrack API

A backend REST API for managing shipment logs across logistics hubs — built with **FastAPI**, **PostgreSQL**, and **JWT authentication**. Deployed on Railway with a live PostgreSQL database on Neon.

---

## 🌐 Live Demo

| Link | Description |
|------|-------------|
| 👉 **[Interactive Demo](https://logistics-tracking-api-production.up.railway.app/)** | Try the full flow — register, login, and submit shipments |
| 📄 **[API Documentation](https://logistics-tracking-api-production.up.railway.app/docs)** | Explore and test all endpoints via Swagger UI |

> No installation required. Everything runs in your browser.

---

## ✨ What It Does

LogiTrack lets logistics hub operators register, log in, and record incoming shipments. Each shipment log captures the tracking number, SKU, package count, and weight — and automatically associates it with the operator's assigned hub.

**Core features:**
- User registration with hub assignment
- JWT-based login and authentication
- Shipment log submission (auth-protected)
- Live database viewer for registered users and shipment records

---

## 🚀 Try It Yourself (No Setup Needed)

### Option A — Interactive Demo Page
Visit **[the demo page](https://logistics-tracking-api-production.up.railway.app/)** and follow the 3-step flow:

1. **Register(Optional)** — Fill in the form (defaults are pre-filled) and click *Create Account*
2. **Login** — Switch to the Login tab. You can authorize using your newly created user profile, or use the default system credentials:
   * **Username:** `admin`
   * **Password:** `password123`
3. **Post Log** — Switch to the Post Log tab and click *Submit Shipment Log*

Watch your entry appear live in the database viewer on the right.

---

### Option B — Swagger UI (For Technical Users)

Visit **[/docs](https://logistics-tracking-api-production.up.railway.app/docs)** and follow the numbered endpoints:

**Step 1** — `POST /register` → Click **Try it out** → **Execute** (defaults are pre-filled)

**Step 2** — Click the **🔒 Authorize** button → enter your username and password → **Authorize**

**Step 3** — `POST /logs` → Click **Try it out** → fill in shipment details → **Execute**

**Step 4** — `GET /tracking_database` → **Try it out** → **Execute** to see all records

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python) |
| Database | PostgreSQL (Neon.tech) |
| ORM | SQLAlchemy |
| Auth | JWT (PyJWT + bcrypt) |
| Deployment | Railway |
| Containerization | Docker |

---

## 📁 Project Structure

```
logistics-tracking-api/
├── logitrack_api.py      # Main application — all routes, models, and logic
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container build instructions
├── static/               #
│   ├── demo.html         # DEMO UI
├── .env.example          # Environment variable template
└── README.md
```
---

## 📬 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/register` | ❌ | Create a new user account |
| `POST` | `/login` | ❌ | Log in and receive a JWT token |
| `POST` | `/logs` | ✅ | Submit a shipment log |
| `GET` | `/tracking_database` | ✅ | View all shipment records |
| `GET` | `/users_database` | ❌ | View all registered users (demo) |
| `GET` | `/` | ❌ | Interactive demo page |
| `GET` | `/docs` | ❌ | Swagger UI documentation |

---

## 👨‍💻 Author

**jharviy** — [GitHub](https://github.com/jharviy)

Built as a portfolio project to demonstrate backend API development with Python.
