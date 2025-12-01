@echo off
echo ========================================
echo Testing Deployment HTTP Scenario
echo ========================================
echo.
echo This will start an HTTP server (not HTTPS)
echo to simulate deployment environment where
echo getUserMedia fails due to non-secure context.
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python test_deployment_scenario.py

