@echo off
echo ===== Fixing API Server =====
echo.
echo Step 1: Stopping all containers...
docker-compose -f docker-compose.dev.yml down
echo.
echo Step 2: Starting containers again...
docker-compose -f docker-compose.dev.yml up -d
echo.
echo Step 3: Waiting for services to start...
timeout /t 10
echo.
echo Step 4: Checking container status...
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Step 5: Checking API logs...
docker logs TCGScraper-API-Dev --tail 15
echo.
echo ===== Fix Complete =====
echo The API should now be running on http://localhost:8000
echo Try your CSV upload again!
pause
