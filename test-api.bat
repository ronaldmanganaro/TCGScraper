@echo off
echo Testing API connection...
echo.
curl -X GET http://localhost:8000/health 2>nul
if %errorlevel% equ 0 (
    echo ✅ API is responding!
) else (
    echo ❌ API is not responding
    echo Checking API logs:
    docker logs TCGScraper-API-Dev --tail 10
)
echo.
pause
