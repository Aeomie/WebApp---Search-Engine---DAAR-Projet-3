#!/bin/bash

# Bash Script to Start All Services
echo "========================================"
echo "  Starting All Services                 "
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

# Function to start a service in background
start_service() {
    local title=$1
    local command=$2
    local path=$3
    local port=$4
    
    echo -e "${YELLOW}Starting $title...${NC}"
    
    if $IS_WINDOWS; then
        # For Windows, use PowerShell to start new cmd window
        WIN_PATH="$(cd "$path" && pwd -W)"
        powershell.exe -Command "Start-Process cmd.exe -ArgumentList '/k', 'cd /d \"$WIN_PATH\" && title $title && echo ======================================== && echo   $title && echo ======================================== && echo. && $command'" &
        sleep 1
        echo -e "${GREEN}✓ $title started in new window${NC}"
    else
        # For Linux/Mac, run in background with nohup
        cd "$path"
        nohup bash -c "$command" > "../logs/${title}.log" 2>&1 &
        echo $! > "../logs/${title}.pid"
        echo -e "${GREEN}✓ $title started (PID: $(cat ../logs/${title}.pid))${NC}"
        cd - > /dev/null
    fi
    
    sleep 1
}

# Create logs directory for non-Windows systems
if ! $IS_WINDOWS; then
    mkdir -p logs
fi

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
if command -v docker >/dev/null 2>&1; then
    if docker ps --filter "name=postgres-webapp" --format "{{.Names}}" | grep -q "postgres-webapp"; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    else
        echo -e "${YELLOW}Starting PostgreSQL...${NC}"
        if docker start postgres-webapp 2>/dev/null; then
            sleep 3
            echo -e "${GREEN}✓ PostgreSQL started${NC}"
        else
            if docker run --name postgres-webapp \
                -e POSTGRES_USER=aeon \
                -e POSTGRES_PASSWORD=152346 \
                -e POSTGRES_DB=webapp \
                -p 5332:5432 \
                -d postgres:latest; then
                sleep 3
                echo -e "${GREEN}✓ PostgreSQL started${NC}"
            else
                echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
                echo -e "${YELLOW}Please start PostgreSQL manually on port 5332${NC}"
                read -p "Press Enter to continue anyway or Ctrl+C to exit..."
            fi
        fi
    fi
else
    echo -e "${YELLOW}⚠ Docker not found. Please ensure PostgreSQL is running on port 5332${NC}"
    read -p "Press Enter to continue or Ctrl+C to exit..."
fi

echo ""

# Detect Python and uvicorn commands
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# Optional: Ask if user wants to fetch books first
echo -e "${CYAN}Do you want to fetch book data first? (recommended for first run) (Y/N):${NC}"
read -p "" fetchBooks
if [[ "$fetchBooks" == "Y" || "$fetchBooks" == "y" ]]; then
    echo -e "${YELLOW}Fetching books data...${NC}"
    
    if $IS_WINDOWS; then
        # Open in new window on Windows using PowerShell
        WIN_PATH="$(cd DataFetcher && pwd -W)"
        powershell.exe -Command "Start-Process cmd.exe -ArgumentList '/k', 'cd /d \"$WIN_PATH\" && echo ======================================== && echo   Fetching Books Data && echo ======================================== && echo. && python bookFetcher.py && echo. && echo ======================================== && echo   Fetch Complete! && echo ======================================== && pause'" &
        echo -e "${GREEN}✓ Book fetcher started in new window${NC}"
        echo -e "${YELLOW}Waiting for fetch to complete (check the new window)...${NC}"
        read -p "Press Enter when book fetching is complete to continue..."
    else
        # Run directly on Linux/Mac
        cd DataFetcher
        if $PYTHON_CMD bookFetcher.py; then
            echo -e "${GREEN}✓ Books fetched successfully${NC}"
        else
            echo -e "${YELLOW}⚠ Failed to fetch books (continuing anyway)${NC}"
        fi
        cd ..
    fi
    
    echo ""
fi

# Start Engine API (port 8000)
start_service "Engine API (Port 8000)" "uvicorn engine_api:app --reload --port 8000" "apis" 8000

# Start Index Service API (port 8003)
start_service "Index Service API (Port 8003)" "uvicorn index_service_api:app --reload --port 8003" "apis" 8003

# Start Jaccard API (port 8005)
start_service "Jaccard API (Port 8005)" "uvicorn jacard_api:app --reload --port 8005" "apis" 8005

# Start Backend (port 8080)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    MVN_CMD="mvnw.cmd"
else
    MVN_CMD="./mvnw"
fi
start_service "Spring Boot Backend (Port 8080)" "$MVN_CMD spring-boot:run" "backend" 8080

# Start Frontend (port 5173)
start_service "React Frontend (Port 5173)" "npm run dev" "frontend" 5173

echo ""
echo "========================================"
echo -e "${GREEN}  All Services Started!                ${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}Services are running at:${NC}"
echo "  📊 PostgreSQL Database:    localhost:5332"
echo "  🔧 Engine API:             http://localhost:8000"
echo "  📇 Index Service API:      http://localhost:8003"
echo "  📈 Jaccard API:            http://localhost:8005"
echo "  ⚙️  Spring Boot Backend:   http://localhost:8080"
echo "  🌐 React Frontend:         http://localhost:5173"
echo ""
echo -e "${CYAN}API Documentation:${NC}"
echo "  Engine API Docs:           http://localhost:8000/docs"
echo "  Index Service API Docs:    http://localhost:8003/docs"
echo "  Jaccard API Docs:          http://localhost:8005/docs"
echo ""

if $IS_WINDOWS; then
    echo -e "${YELLOW}Each service is running in its own window.${NC}"
    echo -e "${YELLOW}Close individual windows to stop specific services.${NC}"
else
    echo -e "${YELLOW}Services are running in the background.${NC}"
    echo -e "${YELLOW}Check logs in the 'logs' directory.${NC}"
    echo -e "${YELLOW}PIDs saved in logs/*.pid files.${NC}"
fi

echo -e "${YELLOW}Run ./stop-all.sh to stop all services.${NC}"
echo ""
read -p "Press Enter to continue..."
