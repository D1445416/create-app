@echo off
chcp 65001 > nul
echo ===================================================
echo   台中大眾運輸交通整合APP - 啟動腳本
echo ===================================================
echo.
echo [1/3] 正在檢查 Python 環境...

:: 檢查是否有 python 或是 py 命令
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [錯誤] 找不到 Python！請確保已安裝 Python 並將其加入系統 PATH 中。
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo [2/3] 正在安裝/檢查必要套件 (Flask, Requests 等)...
%PYTHON_CMD% -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [警告] 套件安裝可能未完全成功，嘗試直接執行應用程式...
)

echo [3/3] 正在啟動 Flask 後端服務並開啟瀏覽器...
:: 在背景稍微延遲後自動開啟瀏覽器
start "" "http://127.0.0.1:5000"

echo ---------------------------------------------------
echo   服務正在執行中！請勿關閉此視窗。
echo   您可以點選瀏覽器或直接輸入 http://127.0.0.1:5000 進行訪問。
echo   要停止運行，請在此視窗按下 Ctrl + C 或直接關閉此視窗。
echo ---------------------------------------------------
echo.

:: 啟動 Flask 應用
%PYTHON_CMD% app.py

pause
