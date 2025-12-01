# WebApp Search Engine - Setup Guide

Complete setup guide for the WebApp Search Engine project.

## 📋 Prerequisites

Before starting, ensure you have the following installed:

- **Git Bash** (Windows only) - Included with [Git for Windows](https://git-scm.com/downloads)
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Java 21** - [Download](https://adoptium.net/)
- **Maven** (optional, project includes Maven Wrapper)
- **Docker Desktop** (for PostgreSQL database) - [Download](https://www.docker.com/products/docker-desktop/)

**Windows Users:** All commands should be run in Git Bash, not PowerShell or CMD.

## 🚀 Quick Start

### One-Time Setup

Run the setup script to install all dependencies and build the project:

```bash
chmod +x setup.sh
./setup.sh
```

**Note:** On Windows, use Git Bash to run these scripts.

This script will:
1. ✓ Check all prerequisites (Python, Node.js, Java, etc.)
2. ✓ Set up PostgreSQL database (via Docker)
3. ✓ Install Python dependencies for DataFetcher and APIs
4. ✓ Install Node.js dependencies for Frontend
5. ✓ Build the Spring Boot backend with Maven

### Start All Services

After setup is complete, start all services with:

```bash
chmod +x start-all.sh
./start-all.sh
```

This will start all services:
- Engine API (Port 8000)
- Index Service API (Port 8003)
- Jaccard API (Port 8005)
- Spring Boot Backend (Port 8080)
- React Frontend (Port 5173)

**Note:** On Windows with Git Bash, services open in separate command windows. On Linux/Mac, they run in background with logs in the `logs/` directory.

### Stop All Services

To stop all running services:

```bash
./stop-all.sh
```

## 📂 Project Structure

```
WebApp---Search-Engine---DAAR-Projet-3/
│
├── setup.sh                   # One-time setup script
├── start-all.sh               # Start all services
├── stop-all.sh                # Stop all services
├── start-manual.md            # Manual startup instructions
│
├── DataFetcher/               # Book data fetching utility
│   ├── bookFetcher.py
│   └── requirements.txt
│
├── apis/                      # FastAPI services
│   ├── engine_api.py          # Port 8000
│   ├── index_service_api.py   # Port 8003
│   ├── jacard_api.py          # Port 8005
│   ├── requirements.txt
│   └── search_algorithms/
│
├── backend/                   # Spring Boot application
│   ├── pom.xml
│   ├── mvnw.cmd               # Maven Wrapper
│   └── src/
│
├── frontend/                  # React application
│   ├── package.json
│   └── src/
│
└── books_data/                # Books and indexes
    ├── catalog.json
    └── books/
```

## 🔧 Configuration

### Database Configuration

The project uses PostgreSQL with the following settings:

- **Host**: `localhost`
- **Port**: `5332`
- **Database**: `webapp`
- **Username**: `aeon`
- **Password**: `152346`

These settings are configured in:
- `backend/src/main/resources/application.properties`

### API Endpoints Configuration

The backend communicates with the following API services:

| Service | Endpoint |
|---------|----------|
| Build Index | http://localhost:8003/indexAPI/build |
| Index Status | http://localhost:8003/indexAPI/status |
| Generate Words | http://localhost:8000/engine/generateWords |
| Jaccard Build | http://localhost:8005/jacardAPI/build |
| Jaccard PageRank | http://localhost:8005/jacardAPI/run_pagerank |
| Jaccard Load | http://localhost:8005/jacardAPI/load |
| Jaccard Status | http://localhost:8005/jacardAPI/status |
| Similarity Score | http://localhost:8005/jacardAPI/similar/ |
| PageRank Score | http://localhost:8005/jacardAPI/pagerank |

## 📚 Fetching Books Data

To populate the `books_data` directory with book files:

```powershell
cd DataFetcher
python bookFetcher.py
cd ..
```

This is optional but recommended for a fully functional search engine.

## 🔍 Manual Service Management

If you prefer to start services manually or need more control, see the detailed manual startup guide:

**[View Manual Startup Guide](start-manual.md)**

## 🛠️ Development Workflow

### Frontend Development
```powershell
cd frontend
npm run dev
```
The frontend supports hot-reload (HMR) for instant updates.

### Backend Development
```powershell
cd backend
.\mvnw.cmd spring-boot:run
```
Spring Boot DevTools provides automatic restart on code changes.

### API Development
```powershell
cd apis
uvicorn engine_api:app --reload --port 8000
```
Uvicorn's `--reload` flag enables auto-reload on file changes.

## 🔍 Troubleshooting

### Port Already in Use

If you get a "port already in use" error:

1. Check what's using the port:
```powershell
netstat -ano | findstr ":8000"  # Replace with the port number
```

2. Stop the process:
```powershell
.\stop-all.ps1
```

### PostgreSQL Connection Failed

1. Ensure PostgreSQL container is running:
```powershell
docker ps | findstr postgres-webapp
```

2. If not running, start it:
```powershell
docker start postgres-webapp
```

3. Or create a new container:
```powershell
docker run --name postgres-webapp -e POSTGRES_USER=aeon -e POSTGRES_PASSWORD=152346 -e POSTGRES_DB=webapp -p 5332:5432 -d postgres:latest
```

### Python Package Issues

Reinstall dependencies:
```powershell
cd apis
pip install -r requirements.txt --force-reinstall
```

### Node.js Package Issues

Clear cache and reinstall:
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Maven Build Issues

Clean and rebuild:
```powershell
cd backend
.\mvnw.cmd clean install -U
```

## 📊 Service Health Checks

### Check if PostgreSQL is ready
```powershell
docker exec postgres-webapp pg_isready -U aeon
```

### Check API status
```powershell
# Engine API
curl http://localhost:8000

# Index Service API
curl http://localhost:8003

# Jaccard API
curl http://localhost:8005
```

### Check Backend
```powershell
curl http://localhost:8080/actuator/health
# Or just check if it's responding
curl http://localhost:8080
```

### Check Frontend
Open http://localhost:5173 in your browser

## 🔄 Updating Dependencies

### Python Dependencies
```powershell
cd apis
pip install -r requirements.txt --upgrade
```

### Node.js Dependencies
```powershell
cd frontend
npm update
```

### Java Dependencies
```powershell
cd backend
.\mvnw.cmd clean install -U
```

## 📝 Common Commands Reference

| Task | Command |
|------|---------|
| Initial Setup | `.\setup.ps1` |
| Start All Services | `.\start-all.ps1` |
| Stop All Services | `.\stop-all.ps1` |
| View PostgreSQL Logs | `docker logs postgres-webapp` |
| Access PostgreSQL | `docker exec -it postgres-webapp psql -U aeon -d webapp` |
| Build Backend | `cd backend; .\mvnw.cmd clean install` |
| Test Backend | `cd backend; .\mvnw.cmd test` |

## 🆘 Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the [Manual Startup Guide](start-manual.md)
3. Ensure all prerequisites are properly installed
4. Check service logs in their respective terminal windows

## 📖 Additional Resources

- **Spring Boot Documentation**: https://spring.io/projects/spring-boot
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React + Vite Documentation**: https://vitejs.dev/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

## 🎯 Next Steps

After setup:

1. ✅ Run `./setup.sh` (first time only)
2. ✅ Run `./start-all.sh` to start all services
3. ✅ Open http://localhost:5173 in your browser
4. ✅ Start developing!

**Windows Users:** Use Git Bash to run these scripts. They work on Windows, Linux, and Mac.

Happy coding! 🚀
