@echo off
echo Restarting API server...
docker restart TCGScraper-API-Dev
echo Waiting for API to start...
timeout /t 5
echo Checking API status...
docker logs TCGScraper-API-Dev --tail 10
echo.
echo API restart complete. Check logs above for any errors.
pause