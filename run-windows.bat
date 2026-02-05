@echo off
echo ============================================
echo    KONTABIL - Iniciando sem Docker
echo ============================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.10+ de https://python.org
    pause
    exit /b 1
)

REM Verifica Node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado!
    echo Instale Node.js 18+ de https://nodejs.org
    pause
    exit /b 1
)

REM Configura variaveis de ambiente
set DATABASE_URL=sqlite:///./kontabil.db
set SECRET_KEY=dev-secret-key-change-in-production-12345678901234567890
set ENCRYPTION_KEY=dev-encryption-key-32-chars-ok!!
set JWT_ALGORITHM=HS256
set ACCESS_TOKEN_EXPIRE_MINUTES=60
set ANTHROPIC_API_KEY=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

echo [1/4] Instalando dependencias do backend...
cd backend
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias Python
    pause
    exit /b 1
)

echo [2/4] Instalando dependencias do frontend...
cd ..\frontend
call npm install --silent
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias Node
    pause
    exit /b 1
)

echo [3/4] Iniciando backend na porta 8000...
cd ..\backend
start "Kontabil Backend" cmd /c "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

echo [4/4] Iniciando frontend na porta 5173...
cd ..\frontend
start "Kontabil Frontend" cmd /c "npm run dev"

echo.
echo ============================================
echo    SISTEMA INICIADO!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Para parar: feche as janelas do terminal
echo.
pause
