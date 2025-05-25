@echo off
setlocal EnableDelayedExpansion

:: Generic Docker Application Runner
:: Stops, removes, builds, and runs a Docker container, then checks application status
:: Logs output to run_docker_app.log
:: Date: May 25, 2025, 11:56 PM IST

:: Redirect output to log file and console
echo Starting Docker application setup... > run_docker_app.log
echo Starting Docker application setup...

:: Define variables (customize as needed)
set CONTAINER_NAME=smartquiz-app
set IMAGE_NAME=smartquiz-app:latest
set PORT_MAPPING=8000:8000
set VOLUME_MAPPING=E:/smart-quiz/data:/data
set HEALTH_URL=http://127.0.0.1:8000/health
set DOCKERFILE_PATH=.
set TIMEOUT=30
set LOG_FILE=run_docker_app.log

:: Check if Docker is installed and running
echo Checking Docker installation... | tee -a %LOG_FILE%
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker is not installed or not accessible. Please install Docker Desktop and ensure it is running. | tee -a %LOG_FILE%
    pause
    exit /b 1
)
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker daemon is not running. Please start Docker Desktop. | tee -a %LOG_FILE%
    pause
    exit /b 1
)

:: Stop existing container (if running)
echo Stopping existing container '%CONTAINER_NAME%'... | tee -a %LOG_FILE%
docker stop %CONTAINER_NAME% >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Container '%CONTAINER_NAME%' stopped successfully. | tee -a %LOG_FILE%
) else (
    echo No running container '%CONTAINER_NAME%' found or error stopping container. | tee -a %LOG_FILE%
)

:: Remove existing container (if exists)
echo Removing existing container '%CONTAINER_NAME%'... | tee -a %LOG_FILE%
docker rm %CONTAINER_NAME% >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Container '%CONTAINER_NAME%' removed successfully. | tee -a %LOG_FILE%
) else (
    echo No container '%CONTAINER_NAME%' found or error removing container. | tee -a %LOG_FILE%
)

:: Build Docker image
echo Building Docker image '%IMAGE_NAME%'... | tee -a %LOG_FILE%
docker build -t %IMAGE_NAME% %DOCKERFILE_PATH%
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to build Docker image. Check Dockerfile and project files. | tee -a %LOG_FILE%
    pause
    exit /b 1
)
echo Docker image '%IMAGE_NAME%' built successfully. | tee -a %LOG_FILE%

:: Run Docker container
echo Starting container '%CONTAINER_NAME%'... | tee -a %LOG_FILE%
if defined VOLUME_MAPPING (
    docker run -d --name %CONTAINER_NAME% -p %PORT_MAPPING% -v %VOLUME_MAPPING% %IMAGE_NAME%
) else (
    docker run -d --name %CONTAINER_NAME% -p %PORT_MAPPING% %IMAGE_NAME%
)
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to start container. Check Docker configuration and port '%PORT_MAPPING%'. | tee -a %LOG_FILE%
    pause
    exit /b 1
)
echo Container '%CONTAINER_NAME%' started successfully. | tee -a %LOG_FILE%

:: Wait for application to start
echo Waiting for application to start (%TIMEOUT% seconds)... | tee -a %LOG_FILE%
timeout /t %TIMEOUT% /nobreak >nul

:: Check if application is running
echo Checking application health at %HEALTH_URL%... | tee -a %LOG_FILE%
curl -s -o health_response.json -w "%%{http_code}" %HEALTH_URL% > http_status.txt 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Curl command failed. Ensure curl is installed and %HEALTH_URL% is accessible. | tee -a %LOG_FILE%
    echo Possible issues: | tee -a %LOG_FILE%
    echo - Curl not installed (run: curl --version). | tee -a %LOG_FILE%
    echo - Network issue or application not started. | tee -a %LOG_FILE%
    echo Check container logs: docker logs %CONTAINER_NAME% | tee -a %LOG_FILE%
    if exist health_response.json (
        echo Health response: | tee -a %LOG_FILE%
        type health_response.json | tee -a %LOG_FILE%
    )
    goto :cleanup
)

:: Read HTTP status
set HTTP_STATUS=0
if exist http_status.txt (
    for /f %%i in (http_status.txt) do set HTTP_STATUS=%%i
)

:: Check health status
if "!HTTP_STATUS!"=="200" (
    echo SUCCESS: Application is running and healthy. | tee -a %LOG_FILE%
    if exist health_response.json (
        echo Health response: | tee -a %LOG_FILE%
        type health_response.json | tee -a %LOG_FILE%
    ) else (
        echo WARNING: Health response file not found. | tee -a %LOG_FILE%
    )
) else (
    echo ERROR: Application is not responding (HTTP !HTTP_STATUS!). | tee -a %LOG_FILE%
    if exist health_response.json (
        echo Health response: | tee -a %LOG_FILE%
        type health_response.json | tee -a %LOG_FILE%
    ) else (
        echo WARNING: Health response file not found. | tee -a %LOG_FILE%
    )
    echo Possible issues: | tee -a %LOG_FILE%
    echo - Application failed to start (check container logs: docker logs %CONTAINER_NAME%). | tee -a %LOG_FILE%
    echo - Port 8000 is in use (check with: netstat -ano | findstr :8000). | tee -a %LOG_FILE%
    echo - Health endpoint %HEALTH_URL% is incorrect for this application. | tee -a %LOG_FILE%
)

:cleanup
:: Clean up temporary files
if exist http_status.txt del http_status.txt
if exist health_response.json del health_response.json

echo. | tee -a %LOG_FILE%
echo Setup complete. Access the API at %HEALTH_URL%/docs | tee -a %LOG_FILE%
echo To stop the container, run: docker stop %CONTAINER_NAME% | tee -a %LOG_FILE%
echo Log file: %LOG_FILE% | tee -a %LOG_FILE%
pause