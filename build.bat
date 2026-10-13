@echo off
chcp 65001 >nul
echo === Pixiv Downloader 打包脚本 ===
echo.

cd /d "%~dp0"

echo [1/4] 构建前端 ...
cd webui\frontend
call npm run build
if %errorlevel% neq 0 ( echo 前端构建失败! & pause & exit /b 1 )
cd ..\..

echo [2/4] 安装打包工具 ...
call .\venv\Scripts\python.exe -m pip install pyinstaller reportlab --quiet
if %errorlevel% neq 0 ( echo pip 安装失败! & pause & exit /b 1 )

echo [3/4] 生成用户指南 PDF ...
call .\venv\Scripts\python.exe generate_guide.py
if %errorlevel% neq 0 ( echo PDF 生成失败! & pause & exit /b 1 )

echo [4/4] PyInstaller 圧縮 (这一步约 3-5 分钟) ...
call .\venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath packaged --workpath build_tmp build_exe.spec
if %errorlevel% neq 0 ( echo 圧縮失敗! & pause & exit /b 1 )

echo.
echo === 圧縮完成 ===
echo 输出位置: packaged\ 文件夹
echo   - PixivDownloader.exe
echo   - 用户指南.pdf
echo.
echo 将 packaged\ 下所有文件发送给用户即可。
echo 用户首次运行后会自动在其目录下创建 config\、downloads\ 等文件夹。
pause
