@echo off
setlocal EnableDelayedExpansion
title FFmpeg Otomatik Kurulumu (Native Surum)

Wmic.exe /Namespace:\\root\default Path SystemRestore Call CreateRestorePoint "FFmpeg Kurulum Oncesi", 100, 7 >nul 2>&1

:: 1. YONETICI IZNI KONTROLU
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [HATA] Lutfen bu dosyayi Yonetici Olarak Calistirin!
    pause
    exit /b
)

:: 2. DEGISKENLER
set "INSTALL_DIR=C:\ffmpeg"
set "ZIP_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "TEMP_ZIP=%TEMP%\ffmpeg_setup.zip"
set "TEMP_DIR=%TEMP%\ffmpeg_temp"

echo.
echo [1/5] FFmpeg indiriliyor (curl ile)...
:: --ssl-no-revoke sertifika kontrol hatalarini onler, -L yönlendirmeleri takip eder
curl -L -o "%TEMP_ZIP%" "%ZIP_URL%" --ssl-no-revoke

if not exist "%TEMP_ZIP%" (
    echo [HATA] Indirme basarisiz.
    pause
    exit /b
)

echo.
echo [2/5] Arsiv aciliyor (tar ile)...
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
:: Windows tar komutu zip dosyalarini destekler
tar -xf "%TEMP_ZIP%" -C "%TEMP_DIR%"

:: 3. BIN KLASORU TESPITI
echo.
echo [3/5] Bin klasoru tespit ediliyor...
set "FFROOT="
for /d /r "%TEMP_DIR%" %%d in (bin) do (
    if exist "%%d\ffmpeg.exe" (
        set "FFROOT=%%~dpd"
    )
)

if "!FFROOT!"=="" (
    echo [HATA] FFmpeg klasor yapisi bulunamadi.
    pause
    exit /b
)
:: Sonundaki ters slash'i temizle
if "!FFROOT:~-1!"=="\" set "FFROOT=!FFROOT:~0,-1!"

:: 4. KURULUM
echo.
echo [4/5] Dosyalar %INSTALL_DIR% konumuna tasiniyor...

if exist "%INSTALL_DIR%" rd /s /q "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%"
mkdir "%INSTALL_DIR%\bin"

:: Sadece gerekli dosyalari al
robocopy "!FFROOT!\bin" "%INSTALL_DIR%\bin" /E /NFL /NDL >nul
if exist "!FFROOT!\LICENSE" copy "!FFROOT!\LICENSE" "%INSTALL_DIR%" >nul
if exist "!FFROOT!\README.txt" copy "!FFROOT!\README.txt" "%INSTALL_DIR%" >nul

:: 5. PATH AYARI (Powershell Kullanimi Zorunlu - Ancak optimize edildi)
echo.
echo [5/5] PATH guncelleniyor...

:: PATH islemini ayri bir scope'ta yapip batch icine gomulu komut karmasasini azalttik
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$p=[Environment]::GetEnvironmentVariable('Path','Machine'); if($p -notlike '*C:\ffmpeg\bin*'){$n=$p+';C:\ffmpeg\bin';[Environment]::SetEnvironmentVariable('Path',$n,'Machine');Write-Host 'PATH eklendi.'}else{Write-Host 'Zaten ekli.'}"

:: TEMIZLIK
del "%TEMP_ZIP%" >nul 2>&1
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"

echo.
echo KURULUM BASARIYLA TAMAMLANDI!
timeout /t 5 >nul
