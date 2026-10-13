@echo off
chcp 65001 >nul
echo === Pixiv Downloader 打包脚本 (onedir 模式) ===
echo.

cd /d "%~dp0"

set "VER=v1.0.0"
set "SEVENZIP=C:\Program Files\7-Zip\7z.exe"
if not exist "%SEVENZIP%" set "SEVENZIP=7z"

echo [1/5] 构建前端 ...
cd webui\frontend
call npm run build
if %errorlevel% neq 0 ( echo 前端构建失败! & pause & exit /b 1 )
cd ..\..

echo [2/5] 安装打包工具 ...
call .\venv\Scripts\python.exe -m pip install pyinstaller reportlab --quiet
if %errorlevel% neq 0 ( echo pip 安装失败! & pause & exit /b 1 )

echo [3/5] 生成用户指南 PDF ...
call .\venv\Scripts\python.exe generate_guide.py
if %errorlevel% neq 0 ( echo PDF 生成失败! & pause & exit /b 1 )

echo [4/5] PyInstaller 打包 (onedir, 这一步约 3-5 分钟) ...
call .\venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --distpath packaged --workpath build_tmp build_exe.spec
if %errorlevel% neq 0 ( echo 打包失败! & pause & exit /b 1 )

if exist "packaged\PixivDownloader.exe" del /q "packaged\PixivDownloader.exe"
move /y "packaged\用户指南.pdf" "packaged\PixivDownloader\" >nul

echo [5/5] 生成 7z 与 zip 发行包 ...
if exist "%SEVENZIP%" (
    "%SEVENZIP%" a -t7z -mx=9 "packaged\PixivDownloader-%VER%.7z" ".\packaged\PixivDownloader" >nul
    if %errorlevel% neq 0 ( echo 7z 生成失败! & pause & exit /b 1 )
    "%SEVENZIP%" a -tzip -mx=9 "packaged\PixivDownloader-%VER%.zip" ".\packaged\PixivDownloader" >nul
    if %errorlevel% neq 0 ( echo zip 生成失败! & pause & exit /b 1 )
) else (
    powershell -NoProfile -Command "Compress-Archive -Path 'packaged\PixivDownloader' -DestinationPath 'packaged\PixivDownloader-%VER%.zip' -Force"
    if %errorlevel% neq 0 ( echo zip 生成失败! & pause & exit /b 1 )
    echo 未找到 7-Zip, 已跳过 7z 生成 (请手动安装 7-Zip 或自行压缩)
)

echo.
echo === 打包完成 ===
echo 输出位置: packaged\ 文件夹
echo   - PixivDownloader\                解压即用的程序文件夹 (含 用户指南.pdf)
echo   - PixivDownloader-%VER%.7z        发行包 (7z)
echo   - PixivDownloader-%VER%.zip       发行包 (zip)
echo.
echo 将 7z / zip 上传到 GitHub Releases 即可。
pause
