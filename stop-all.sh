#!/bin/bash

# Bash Script to Stop All Services
echo "========================================"
echo "  Stopping All Services                 "
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

# Function to kill process on port
kill_port() {
    local port=$1
    local service=$2
    
    echo -e "${YELLOW}Stopping $service on port $port...${NC}"
    
    if $IS_WINDOWS; then
        # Windows
        for pid in $(netstat -ano | grep ":$port" | awk '{print $5}' | sort -u); do
            if [ ! -z "$pid" ] && [ "$pid" != "0" ]; then
                taskkill //PID $pid //F 2>/dev/null
            fi
        done
    else
        # Linux/Mac
        local pid=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            kill -9 $pid 2>/dev/null
            echo -e "${GREEN}✓ $service stopped${NC}"
        else
            echo -e "  $service not running"
        fi
    fi
}

# Stop services by port
kill_port 8000 "Engine API"
kill_port 8003 "Index Service API"
kill_port 8005 "Jaccard API"
kill_port 8080 "Spring Boot Backend"
kill_port 5173 "React Frontend"

# Stop services by PID files (Linux/Mac)
if ! $IS_WINDOWS && [ -d "logs" ]; then
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            if [ ! -z "$pid" ]; then
                kill -9 $pid 2>/dev/null
            fi
            rm "$pidfile"
        fi
    done
fi

echo ""
echo -e "${YELLOW}Stopping PostgreSQL container...${NC}"
if command -v docker >/dev/null 2>&1; then
    if docker stop postgres-webapp 2>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL stopped${NC}"
    else
        echo -e "  PostgreSQL not running"
    fi
else
    echo -e "  Docker not found"
fi

echo ""
echo "========================================"
echo -e "${GREEN}  All Services Stopped                 ${NC}"
echo "========================================"
echo ""

if $IS_WINDOWS; then
    echo -e "${YELLOW}Note: Service terminal windows are still open.${NC}"
    echo -e "${YELLOW}Please close them manually or they will show errors.${NC}"
    echo ""
fi

read -p "Press Enter to exit..."
