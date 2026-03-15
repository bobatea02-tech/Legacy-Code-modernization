@echo off
echo ========================================
echo TypeScript Configuration Verification
echo ========================================
echo.

cd frontend

echo [1/4] Checking TypeScript compilation...
call npx tsc --noEmit
if %errorlevel% equ 0 (
    echo [OK] No TypeScript errors
) else (
    echo [FAIL] TypeScript errors found
    exit /b 1
)
echo.

echo [2/4] Checking build...
call npm run build > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Build successful
) else (
    echo [FAIL] Build failed
    exit /b 1
)
echo.

echo [3/4] Checking configuration files...
if exist "tsconfig.json" (
    echo [OK] tsconfig.json exists
) else (
    echo [FAIL] tsconfig.json missing
    exit /b 1
)

if exist "tsconfig.app.json" (
    echo [OK] tsconfig.app.json exists
) else (
    echo [FAIL] tsconfig.app.json missing
    exit /b 1
)

if exist "tsconfig.node.json" (
    echo [OK] tsconfig.node.json exists
) else (
    echo [FAIL] tsconfig.node.json missing
    exit /b 1
)
echo.

echo [4/4] Checking type definitions...
if exist "src\vite-env.d.ts" (
    echo [OK] vite-env.d.ts exists
) else (
    echo [FAIL] vite-env.d.ts missing
    exit /b 1
)
echo.

echo ========================================
echo ALL CHECKS PASSED!
echo ========================================
echo.
echo The TypeScript configuration is correct.
echo.
echo If you still see errors in VS Code:
echo 1. Press Ctrl+Shift+P
echo 2. Type: TypeScript: Restart TS Server
echo 3. Press Enter
echo.
echo See RELOAD_VSCODE_INSTRUCTIONS.md for details.
echo.

pause
