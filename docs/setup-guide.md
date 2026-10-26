# DealForge AI — Local Setup and Installation Guide

## 1. System Requirements

- **Operating System:** Linux, macOS, or Windows 10/11
- **Python:** 3.11.x (tested on Python 3.11.9)
- **Node.js:** v18+ or v22+ (tested on Node v22.23.2, npm 10.9.1)
- **Database:** MySQL 8.0+ or MySQL 8.4+ (listening on `127.0.0.1:3306`)
- **Docker & Docker Compose (Optional):** For containerized service orchestration

---

## 2. Environment Configuration

1. Copy the example configuration template:
   ```bash
   cp .env.example .env
   ```

2. Configure environment variables in `.env`:
   ```ini
   APP_NAME="DealForge AI"
   APP_ENV="development"
   DEBUG=True
   HOST="127.0.0.1"
   PORT=8000
   DEMO_MODE=True

   # MySQL Database Connection
   DB_HOST="127.0.0.1"
   DB_PORT=3306
   DB_USER="root"
   DB_PASSWORD="your_mysql_password"
   DB_NAME="dealforge_db"
   DB_ECHO=False

   # Security & Authentication
   JWT_SECRET="dealforge_enterprise_secret_key_change_in_production_2026"
   JWT_ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=1440

   # Inter-Agent Protocol (A2A) URLs
   A2A_VENDOR_RESEARCH_URL="http://127.0.0.1:8000/a2a/vendor-research"
   A2A_PROCUREMENT_ANALYSIS_URL="http://127.0.0.1:8000/a2a/procurement-analysis"
   A2A_NEGOTIATION_URL="http://127.0.0.1:8000/a2a/negotiation"
   A2A_APPROVAL_REPLANNING_URL="http://127.0.0.1:8000/a2a/approval-replanning"
   ```

---

## 3. Python Backend Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run database migrations via Alembic:
   ```bash
   alembic upgrade head
   ```

3. Seed demonstration catalog data into MySQL:
   ```bash
   python -m app.db.seed
   ```
   *Seeds 11 synthetic vendors, 17 certifications, 4 procurement policies, 10 products, 14 catalog listings, 3 default roles, and 3 authorized demo users.*

---

## 4. Frontend Application Setup (React 18 + TypeScript + Tailwind)

1. Navigate to `frontend-app/`:
   ```bash
   cd frontend-app
   npm install
   ```

2. Build production assets:
   ```bash
   npm run build
   ```
   *Outputs bundle to `frontend-app/dist`, which FastAPI automatically serves from root `/`.*

---

## 5. Running the Application

### Option A: Standard Local Execution

Start the unified FastAPI server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Web Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API Documentation (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative API Documentation (ReDoc): [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Option B: Docker Compose Execution

```bash
docker-compose up --build -d
```

---

## 6. Pre-Seeded Demonstration Users

| Persona | Email | Password | Role | Permissions |
|---|---|---|---|---|
| Rajesh Sharma | `manager@dealforge.ai` | `Manager@123` | Procurement Manager | Request submission, catalog tracking, standard approvals |
| Priya Venkatesh | `finance@dealforge.ai` | `Finance@123` | Finance Reviewer | High-value authorization, budget overrun exceptions |
| System Admin | `admin@dealforge.ai` | `Admin@123` | Administrator | System-wide audit inspection, policy adjustments |
