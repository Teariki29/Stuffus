@echo off
setlocal
title Optimiseur de stuff Dofus - lanceur

REM ============================================================
REM   Lance l'optimiseur de stuff Dofus en local.
REM   Premier lancement : cree le venv, installe les deps,
REM   telecharge et prepare les donnees. Ensuite : demarrage direct.
REM ============================================================

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "VENV_PY=%BACKEND%\.venv\Scripts\python.exe"

echo ==========================================
echo   Optimiseur de stuff Dofus
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Python introuvable dans le PATH. Installez Python 3.12+ puis reessayez.
  pause
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Node.js introuvable dans le PATH. Installez Node 18+ puis reessayez.
  pause
  exit /b 1
)

REM --- backend : environnement Python + dependances ---
if not exist "%VENV_PY%" (
  echo [setup] Creation de l'environnement Python...
  python -m venv "%BACKEND%\.venv"
  if errorlevel 1 goto :error
  echo [setup] Installation des dependances backend ^(1-2 min^)...
  "%VENV_PY%" -m pip install --upgrade pip
  "%VENV_PY%" -m pip install ortools fastapi "uvicorn[standard]" "pydantic>=2" httpx pytest ruff
  if errorlevel 1 goto :error
)

REM --- donnees : ingestion + normalisation au premier lancement ---
if not exist "%BACKEND%\data\items.sqlite" (
  echo [setup] Telechargement et preparation des donnees ^(premier lancement^)...
  pushd "%BACKEND%"
  "%VENV_PY%" -m app.data.ingest
  if errorlevel 1 ( popd & goto :error )
  "%VENV_PY%" -m app.data.normalize
  if errorlevel 1 ( popd & goto :error )
  popd
)

REM --- frontend : dependances npm ---
if not exist "%FRONTEND%\node_modules" (
  echo [setup] Installation des dependances frontend...
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 ( popd & goto :error )
  popd
)

echo.
echo [run] Backend  -^> http://127.0.0.1:8000
start "Dofus Optimizer - Backend" /d "%BACKEND%" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

echo [run] Frontend -^> http://localhost:5173
start "Dofus Optimizer - Frontend" /d "%FRONTEND%" cmd /k "npm run dev"

echo.
echo [run] Ouverture du navigateur dans quelques secondes...
timeout /t 6 /nobreak >nul
start "" http://localhost:5173

echo.
echo Application lancee.
echo Fermez les fenetres "Backend" et "Frontend" pour l'arreter.
echo.
exit /b 0

:error
echo.
echo [ERREUR] Le lancement a echoue. Lisez les messages ci-dessus.
pause
exit /b 1
