@echo off
setlocal
title FFmpeg Otomatik Kurulumu (Guvenli Surum)

:: 1. YONETICI IZNI KONTROLU
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [HATA] Lutfen bu dosyayi Yonetici Olarak Calistirin!
    pause
    exit /b
)
echo [BILGI] Yonetici haklari algilandi. Kurulum basliyor...

:: 2. KURULUM DIZINI AYARLARI
set "INSTALL_DIR=C:\ffmpeg"
set "ZIP_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "TEMP_ZIP=%TEMP%\ffmpeg_setup.zip"
set "TEMP_DIR=%TEMP%\ffmpeg_temp"

echo.
echo ---------------------------------------------------
echo FFmpeg indiriliyor...
echo ---------------------------------------------------

:: 3. POWERSHELL ILE GUVENLI TLS 1.2 DESTEKLI INDIRME
powershell -Command ^
 "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
 "; Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%TEMP_ZIP%' -UseBasicParsing" 

if not exist "%TEMP_ZIP%" (
    echo [HATA] Indirme basarisiz oldu. Internet baglantisini kontrol edin.
    pause
    exit /b
)

echo.
echo ---------------------------------------------------
echo Arsiv aciliyor...
echo ---------------------------------------------------

:: TEMP dizinlerini temizle
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
powershell -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP_DIR%' -Force"

if not exist "%TEMP_DIR%" (
    echo [HATA] Arsiv acilirken bir hata olustu.
    pause
    exit /b
)

:: 4. BIN klasorunu otomatik tespit et
echo [BILGI] Bin klasoru araniyor...

for /f "delims=" %%F in ('powershell -NoLogo -NoProfile -Command ^
    "(Get-ChildItem -Path '%TEMP_DIR%' -Recurse -Directory | Where-Object { Test-Path ($_.FullName + '\bin') } | Select-Object -First 1).FullName"') do (
    set "FFROOT=%%F"
)

if "%FFROOT%"=="" (
    echo [HATA] BIN klasoru bulunamadi. Zip yapisi degismis olabilir.
    pause
    exit /b
)

echo [BILGI] Bulunan FFmpeg klasoru:
echo %FFROOT%
echo.

:: 5. ESKI KURULUMU TEMIZLE VE YENI KLASOR OLUSTUR
if exist "%INSTALL_DIR%" (
    echo [BILGI] Diger kurulum temizleniyor...
    rd /s /q "%INSTALL_DIR%"
)
mkdir "%INSTALL_DIR%\bin"

echo.
echo ---------------------------------------------------
echo Dosyalar kopyalaniyor...
echo ---------------------------------------------------

:: Robocopy ile guvenli kopyalama
robocopy "%FFROOT%\bin" "%INSTALL_DIR%\bin" /E >nul
if %errorLevel% GEQ 8 (
    echo [HATA] Dosyalar kopyalanirken hata olustu.
    exit /b
)

:: LICENSE + README (varsa)
if exist "%FFROOT%\LICENSE" copy "%FFROOT%\LICENSE" "%INSTALL_DIR%" >nul
if exist "%FFROOT%\README.txt" copy "%FFROOT%\README.txt" "%INSTALL_DIR%" >nul

echo [BASARILI] FFmpeg dosyalari yerlestirildi.

:: 6. PATH'E EKLEME — SETX YOK, SISTEMI BOZMAZ
echo.
echo ---------------------------------------------------
echo Sistem yoluna (PATH) ekleniyor...
echo ---------------------------------------------------

powershell -Command ^
    "$old = [Environment]::GetEnvironmentVariable('Path','Machine'); if ($old.ToLower() -notlike '*c:\ffmpeg\bin*') { [Environment]::SetEnvironmentVariable('Path', $old + ';C:\ffmpeg\bin', 'Machine'); Write-Host '[BASARILI] PATH guncellendi.' } else { Write-Host '[BILGI] Zaten PATH icinde.' }"

:: 7. TEMIZLIK
del "%TEMP_ZIP%" >nul 2>&1
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"

echo.
echo ===================================================
echo KURULUM TAMAMLANDI!
echo Yeni PATH icin tum terminal pencerelerini kapatip
echo tekrar acmaniz gerekiyor.
echo ===================================================
timeout /t 5 >nul
exit /b
