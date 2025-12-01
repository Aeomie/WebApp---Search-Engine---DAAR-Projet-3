#!/bin/bash

# Bash Setup Script for WebApp Search Engine
echo "========================================"
echo "  WebApp Search Engine - Setup Script  "
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
echo ""

# Track if there are any errors
ERRORS=0

# Check Python
if command_exists python3 || command_exists python; then
    if command_exists python3; then
        PYTHON_CMD=python3
    else
        PYTHON_CMD=python
    fi
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python not found. Please install Python 3.11+${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check pip
if command_exists pip3 || command_exists pip; then
    if command_exists pip3; then
        PIP_CMD=pip3
    else
        PIP_CMD=pip
    fi
    echo -e "${GREEN}✓ pip found${NC}"
else
    echo -e "${RED}✗ pip not found. Please install pip${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js found: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not found. Please install Node.js 18+${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm found: v$NPM_VERSION${NC}"
else
    echo -e "${RED}✗ npm not found. Please install npm${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check Java
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}✓ Java found: $JAVA_VERSION${NC}"
else
    echo -e "${RED}✗ Java not found. Please install Java 21+${NC}"
    ERRORS=$((ERRORS + 1))
fi

# If there are errors, show summary and wait
if [ $ERRORS -gt 0 ]; then
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  Found $ERRORS missing prerequisite(s)${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Please install the missing prerequisites and run this script again.${NC}"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Maven
if command_exists mvn; then
    MAVEN_VERSION=$(mvn --version | head -n 1)
    echo -e "${GREEN}✓ Maven found: $MAVEN_VERSION${NC}"
    MVN_CMD=mvn
else
    echo -e "${YELLOW}⚠ Maven not found. Will use Maven Wrapper (mvnw)${NC}"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        MVN_CMD="./mvnw.cmd"
    else
        MVN_CMD="./mvnw"
    fi
fi

# Check Docker
if command_exists docker; then
    echo -e "${GREEN}✓ Docker found${NC}"
else
    echo -e "${YELLOW}⚠ Docker not found. You'll need to set up PostgreSQL manually${NC}"
fi

echo ""
echo "========================================"
echo "  Setting Up Database                  "
echo "========================================"
echo ""

echo -e "${YELLOW}Please ensure PostgreSQL is running on localhost:5332${NC}"
echo "Database: webapp"
echo "Username: aeon"
echo "Password: 152346"
echo ""
echo -e "${CYAN}If you're using Docker for PostgreSQL, run:${NC}"
echo "  docker run --name postgres-webapp -e POSTGRES_USER=aeon -e POSTGRES_PASSWORD=152346 -e POSTGRES_DB=webapp -p 5332:5432 -d postgres:latest"
echo ""

if command_exists docker; then
    read -p "Do you want to set up PostgreSQL with Docker now? (Y/N): " setupDb
    if [[ "$setupDb" == "Y" || "$setupDb" == "y" ]]; then
        echo -e "${YELLOW}Setting up PostgreSQL container...${NC}"
        
        # Stop and remove ALL existing PostgreSQL containers that might be using port 5332
        echo -e "${YELLOW}Stopping and removing existing PostgreSQL containers...${NC}"
        docker ps -a --filter "ancestor=postgres" --format "{{.Names}}" | while read container; do
            echo "  Stopping $container..."
            docker stop "$container" 2>/dev/null
            docker rm "$container" 2>/dev/null
        done
        
        # Also explicitly stop postgres-webapp if it exists
        docker stop postgres-webapp 2>/dev/null
        docker rm postgres-webapp 2>/dev/null
        
        # Start new container
        echo -e "${YELLOW}Starting new PostgreSQL container...${NC}"
        if docker run --name postgres-webapp \
            -e POSTGRES_USER=aeon \
            -e POSTGRES_PASSWORD=152346 \
            -e POSTGRES_DB=webapp \
            -p 5332:5432 \
            -d postgres:latest; then
            
            echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
            sleep 5
            echo -e "${GREEN}✓ PostgreSQL container started successfully${NC}"
        else
            echo -e "${RED}✗ Failed to start PostgreSQL container${NC}"
            echo -e "${YELLOW}Please ensure port 5332 is not in use or start PostgreSQL manually${NC}"
        fi
    fi
fi

echo ""
echo "========================================"
echo "  Installing Python Dependencies       "
echo "========================================"
echo ""

# Install DataFetcher dependencies
echo -e "${YELLOW}Installing DataFetcher dependencies...${NC}"
cd DataFetcher
if $PIP_CMD install -r requirements.txt --quiet; then
    echo -e "${GREEN}✓ DataFetcher dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install DataFetcher dependencies${NC}"
    echo -e "${YELLOW}Check the error above and try again${NC}"
    cd ..
    read -p "Press Enter to exit..."
    exit 1
fi
cd ..

# Install APIs dependencies
echo -e "${YELLOW}Installing APIs dependencies...${NC}"
cd apis
if $PIP_CMD install -r requirements.txt --quiet; then
    echo -e "${GREEN}✓ APIs dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install APIs dependencies${NC}"
    echo -e "${YELLOW}Check the error above and try again${NC}"
    cd ..
    read -p "Press Enter to exit..."
    exit 1
fi
cd ..

echo ""
echo "========================================"
echo "  Installing Frontend Dependencies     "
echo "========================================"
echo ""

echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
if npm install; then
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install frontend dependencies${NC}"
    echo -e "${YELLOW}Check the error above and try again${NC}"
    cd ..
    read -p "Press Enter to exit..."
    exit 1
fi
cd ..

echo ""
echo "========================================"
echo "  Building Backend (Maven)             "
echo "========================================"
echo ""

echo -e "${YELLOW}Building Spring Boot backend...${NC}"
cd backend
if [[ "$MVN_CMD" == "./mvnw" ]]; then
    chmod +x mvnw
fi
if $MVN_CMD clean install -DskipTests; then
    echo -e "${GREEN}✓ Backend built successfully${NC}"
else
    echo -e "${RED}✗ Failed to build backend${NC}"
    echo -e "${YELLOW}Check the error above and try again${NC}"
    cd ..
    read -p "Press Enter to exit..."
    exit 1
fi
cd ..

echo ""
echo "========================================"
echo -e "${GREEN}  Setup Complete!                      ${NC}"
echo "========================================"
echo ""

echo -e "${CYAN}Next steps:${NC}"
echo "1. To fetch books data (optional):"
echo "   cd DataFetcher"
echo "   $PYTHON_CMD bookFetcher.py"
echo "   cd .."
echo ""
echo "2. To start all services:"
echo "   ./start-all.sh"
echo ""
echo "Or start services manually (see start-manual.md)"
echo ""
read -p "Press Enter to continue..."
