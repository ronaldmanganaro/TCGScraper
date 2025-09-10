@echo off
echo Checking Docker container status...
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Checking API logs...
docker logs TCGScraper-API-Dev --tail 20
pause
