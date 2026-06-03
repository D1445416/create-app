@echo off
title TransitGO - 台中大眾運輸交通整合系統
echo ===================================================================
echo  正在啟動 TransitGO - 台中大眾運輸交通整合系統...
echo ===================================================================
echo.

:: 檢查 .venv 是否存在
if not exist ".venv" (
    echo [錯誤] 找不到 .venv 虛擬環境資料夾！
    echo 正在嘗試自動建立虛擬環境與安裝依賴...
    python -m venv .venv
    if errorlevel 1 (
        echo [錯誤] 無法建立 .venv，請確認系統已安裝 Python 3。
        pause
        exit /b
    )
)

:: 啟用虛擬環境並安裝依賴
echo [資訊] 正在啟用 .venv 虛擬環境...
call .venv\Scripts\activate

echo [資訊] 正在檢查與安裝依賴套件...
pip install -r requirements.txt

:: 初始化資料庫
echo [資訊] 正在初始化資料庫 (如果資料庫檔案不存在)...
python -c "from app.models import init_db; init_db()"
if errorlevel 1 (
    echo [警告] 資料庫初始化失敗，可能資料庫已存在或有其他錯誤。
)

:: 啟動 Flask 伺服器
echo.
echo ===================================================================
echo  伺服器即將啟動！請在瀏覽器中打開：
echo  http://127.0.0.1:5000
echo  若要停止伺服器，請按 Ctrl + C。
echo ===================================================================
echo.

python app.py
pause
