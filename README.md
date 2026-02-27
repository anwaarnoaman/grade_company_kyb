# Regulatory KYB & Financial Risk Assessment System

This project implements a **Company KYB (Know Your Business) onboarding and financial risk assessment system** using:

- **Frontend:** Next.js  
- **Backend:** FastAPI (Python 3.12)  
- **Database:** PostgreSQL  
- **Storage:** Azure Blob Storage  
- **Secrets Management:** Azure Key Vault  

All services are containerized and orchestrated using **Docker Compose**.

---

## 🚀 Prerequisites

- **Python 3.12** (for backend scripts or local development)  
- **Node.js and npm** (for frontend)  
- **Docker** & **Docker Compose** installed  
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / Mac)  
  - [Install Docker Engine + Compose](https://docs.docker.com/compose/install/) (Linux)  

- **Environment Variables**:

```bash
DATABASE_URL=postgresql://admin:admin@localhost:5432/dfm
DATABASE_URL_ASYNC=postgresql+asyncpg://admin:admin@localhost:5432/dfm
AZURE_STORAGE_BLOB_CONNECTION_STRING=some_value   # provided separately via email. Make sure to also update this value in docker-compose.yml
AZURE_STORAGE_CONTAINER=documents
```

---

## 🗂 Project Structure

```
root/
│
├─ backend/            # FastAPI application
├─ frontend/           # Next.js frontend
├─ docker-compose.yml  # Docker Compose configuration
├─ sample_docs/        # Synthetic KYB documents for testing
├─ README.md
├─ SECURITY.md
├─ Architecture Diagram.png  #Diagram
└─ KYB Assessment.postman_collection.json  # Postman collection for API testing
```

---

## ⚙️ Running the Application

### Using Docker Compose

### (!IMPORTANT) Setup docker compose enviorment variable under api section shared in email 
AZURE_STORAGE_BLOB_CONNECTION_STRING=shared link

**Ubuntu / Linux:**

```bash
sudo docker compose up --build
```

**Windows (PowerShell / CMD):**

```powershell
docker-compose up --build
```

> Backend: `http://localhost:8082`  
> Frontend: `http://localhost:3000`

To stop the services:

```bash
sudo docker compose down   # Linux
docker-compose down         # Windows
```

---

### Local Development (Optional)

1. **Backend:**

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip3 install -e .
# Run migrations first, then start FastAPI
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8082
```

2. **Frontend:**

```bash
cd frontend
# Node.js environment is required
npm install --force
npm run dev
```

Ensure **environment variables** (DB connection, Blob Storage, JWT secret) are set via `.env` file, or as listed above.

---

## 📝 Features

- Bulk **document ingestion** and classification (Trade License, MOA/AOA, Bank Letters, IDs, Financial Statements)  
- **Data extraction & normalization** for company profile, shareholders, UBOs, and financial indicators  
- **Rule-based financial risk scoring** (0–100) with risk bands and risk drivers  
- **Human-in-the-loop review** with Review & Confirm interface  
- **Audit logs** for document uploads, data extraction, risk scoring, and manual edits  
- **Security**: JWT authentication, Azure Key Vault for secrets, masked sensitive data  
- **API Testing:** A Postman collection is included: `KYB Assessment.postman_collection.json`

---

## ⚡ Notes

- All data is **synthetic or publicly available**; no real PII is used.  
- Designed to demonstrate **regulatory awareness, explainability, and auditability**, not production financial use.  
- Docker Compose uses **low-cost local resources** for demonstration purposes.
 
