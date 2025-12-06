@echo off
echo Generating self-signed SSL certificate for movefuze.com (68.183.88.5)
echo.

REM Create ssl directory if it doesn't exist
if not exist ssl mkdir ssl

REM Check if OpenSSL is available
where openssl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: OpenSSL is not installed or not in PATH
    echo.
    echo Please install OpenSSL:
    echo 1. Download from: https://slproweb.com/products/Win32OpenSSL.html
    echo 2. Or use Git Bash (includes OpenSSL)
    echo 3. Or use WSL (Windows Subsystem for Linux)
    echo.
    pause
    exit /b 1
)

REM Generate private key
openssl genrsa -out ssl\key.pem 2048

REM Generate certificate signing request
openssl req -new -key ssl\key.pem -out ssl\cert.csr -subj "/CN=movefuze.com" -addext "subjectAltName=DNS:movefuze.com,DNS:www.movefuze.com,IP:68.183.88.5"

REM Generate self-signed certificate
openssl x509 -req -days 365 -in ssl\cert.csr -signkey ssl\key.pem -out ssl\cert.pem -extensions v3_req -extfile ssl\extfile.conf

REM Create extfile.conf for certificate extensions
(
echo [v3_req]
echo subjectAltName=DNS:movefuze.com,DNS:www.movefuze.com,IP:68.183.88.5
) > ssl\extfile.conf

openssl x509 -req -days 365 -in ssl\cert.csr -signkey ssl\key.pem -out ssl\cert.pem -extensions v3_req -extfile ssl\extfile.conf

REM Clean up
del ssl\cert.csr
del ssl\extfile.conf

echo.
echo SSL certificate generated successfully!
echo    Certificate: ssl\cert.pem
echo    Private Key: ssl\key.pem
echo.
echo Note: This is a self-signed certificate.
echo Browsers will show a security warning that you need to accept.
echo.
pause

