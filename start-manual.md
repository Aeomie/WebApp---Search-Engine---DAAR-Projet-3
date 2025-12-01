# Manual Service Startup Guide

If you prefer to start services manually, follow these steps in order:

## 1. Start PostgreSQL Database

### Option A: Using Docker (Recommended)
```powershell
docker run --name postgres-webapp -e POSTGRES_USER=aeon -e POSTGRES_PASSWORD=152346 -e POSTGRES_DB=webapp -p 5332:5432 -d postgres:latest
```

### Option B: Using Local PostgreSQL
Ensure PostgreSQL is running on port 5332 with:
- Database: `webapp`
- Username: `aeon`
- Password: `152346`

## 2. Fetch Books Data (Optional, First Time Only)

```powershell
cd DataFetcher
pip install -r requirements.txt
python bookFetcher.py
cd ..
```

## 3. Start FastAPI Services (3 terminals)

### Terminal 1 - Engine API (Port 8000)
```powershell
cd apis
uvicorn engine_api:app --reload --port 8000
```

### Terminal 2 - Index Service API (Port 8003)
```powershell
cd apis
uvicorn index_service_api:app --reload --port 8003
```

### Terminal 3 - Jaccard API (Port 8005)
```powershell
cd apis
uvicorn jacard_api:app --reload --port 8005
```

## 4. Start Spring Boot Backend (Terminal 4)

```powershell
cd backend
# Using Maven Wrapper (recommended)
.\mvnw.cmd spring-boot:run

# OR using Maven
mvn spring-boot:run
```

## 5. Start React Frontend (Terminal 5)

```powershell
cd frontend
npm install  # First time only
npm run dev
```

## Service URLs

Once all services are running:

- **PostgreSQL**: `localhost:5332`
- **Engine API**: http://localhost:8000
- **Index Service API**: http://localhost:8003
- **Jaccard API**: http://localhost:8005
- **Spring Boot Backend**: http://localhost:8080
- **React Frontend**: http://localhost:5173

## Stopping Services

Press `Ctrl+C` in each terminal to stop the respective service.

To stop PostgreSQL:
```powershell
docker stop postgres-webapp
```
