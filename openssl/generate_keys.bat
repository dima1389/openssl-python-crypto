@echo off
setlocal enabledelayedexpansion

REM === CONFIG ===
set "password=password"
set "outdir=keys"
set "global_log=%outdir%\keygen.log"
set "outdir_symmetric=%outdir%\symmetric-encryption"
set "outdir_asymmetric=%outdir%\asymmetric-encryption"

REM === CLEANUP ===
if exist "%outdir%" (
    rmdir /s /q "%outdir%"
)

REM === INIT FOLDERS ===
mkdir "%outdir_symmetric%\AES"
mkdir "%outdir_asymmetric%\RSA"
mkdir "%outdir_asymmetric%\EC-Curves"
mkdir "%outdir_asymmetric%\DSA"
mkdir "%outdir_asymmetric%\EdDSA"

call :log "=== Key Generation Started ==="

REM === AES ===
for %%s in (128 192 256) do (
    set "algo=AES"
    set "bits=%%s"
    set "dir=%outdir_symmetric%\AES\AES%%s"
    mkdir "!dir!"
    openssl rand -out "!dir!\key.bin" %%s >nul 2>&1
    call :log "Generated AES %%s-bit key -> !dir!"
    call :write_meta "!algo!" "!bits!" "" "!dir!" "key.bin"
)

REM === RSA ===
for %%s in (2048 3072 4096) do (
    set "algo=RSA"
    set "bits=%%s"
    set "dir=%outdir_asymmetric%\RSA\RSA%%s"
    mkdir "!dir!"
    openssl genpkey -algorithm RSA -aes256 -pass pass:%password% -out "!dir!\private_key.pem" -pkeyopt rsa_keygen_bits:%%s >nul 2>&1
    openssl pkey -in "!dir!\private_key.pem" -passin pass:%password% -outform DER -out "!dir!\private_key.der" >nul 2>&1
    openssl rsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >nul 2>&1
    openssl rsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -outform DER -out "!dir!\public_key.der" >nul 2>&1
    call :log "Generated RSA %%s-bit key pair -> !dir!"
    call :write_meta "!algo!" "!bits!" "" "!dir!" "private_key.pem,private_key.der,public_key.pem,public_key.der"
)

REM === EC Curves ===
for %%c in (prime256v1 secp384r1 secp521r1 secp256k1) do (
    set "algo=EC"
    set "curve=%%c"
    set "dir=%outdir_asymmetric%\EC-Curves\EC_%%c"
    mkdir "!dir!"
    openssl ecparam -name %%c -genkey -noout | openssl ec -aes256 -passout pass:%password% -out "!dir!\private_key.pem" >nul 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -outform DER -out "!dir!\private_key.der" >nul 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >nul 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -pubout -outform DER -out "!dir!\public_key.der" >nul 2>&1
    call :log "Generated EC %%c key -> !dir!"
    call :write_meta "!algo!" "" "!curve!" "!dir!" "private_key.pem,private_key.der,public_key.pem,public_key.der"
)

REM === DSA ===
set "algo=DSA"
set "bits=2048"
set "dir=%outdir_asymmetric%\DSA\DSA2048"
mkdir "!dir!"
openssl dsaparam -out "!dir!\dsaparam.pem" 2048 >nul 2>&1
openssl gendsa -aes256 -passout pass:%password% -out "!dir!\private_key.pem" "!dir!\dsaparam.pem" >nul 2>&1
openssl dsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >nul 2>&1
call :log "Generated DSA 2048-bit key -> !dir!"
call :write_meta "!algo!" "!bits!" "" "!dir!" "dsaparam.pem,private_key.pem,public_key.pem"

REM === EdDSA ===
for %%a in (ED25519 ED448) do (
    set "algo=%%a"
    set "dir=%outdir_asymmetric%\EdDSA\%%a"
    mkdir "!dir!"
    openssl genpkey -algorithm %%a -out "!dir!\private_key.pem" >nul 2>&1
    openssl pkey -in "!dir!\private_key.pem" -pubout -out "!dir!\public_key.pem" >nul 2>&1
    call :log "Generated %%a key -> !dir!"
    call :write_meta "!algo!" "" "" "!dir!" "private_key.pem,public_key.pem"
)

call :log "=== Key Generation Complete ==="
echo Keys created successfully. See: %global_log%
pause
exit /b

REM === LOG FUNCTION ===
:log
setlocal
set "msg=%~1"
for /f "tokens=1-3 delims=:.," %%a in ("%time%") do (
    set "timestamp=%date% %%a:%%b:%%c"
)
echo [%timestamp%] %msg% >> "%global_log%"
endlocal
exit /b

REM === META WRITER FUNCTION ===
:write_meta
setlocal
set "algo=%~1"
set "bits=%~2"
set "curve=%~3"
set "dir=%~4"
set "files=%~5"

for /f "tokens=1-3 delims=:.," %%a in ("%time%") do (
    set "tstamp=%date% %%a:%%b:%%c"
)

set "json_files="
set "yaml_files="
for %%f in (%files%) do (
    set "file=%%f"
    for /f %%h in ('certutil -hashfile "!dir!\%%f" SHA256 ^| find /i /v "sha256"') do (
        set "hash=%%h"
        set "json_files=!json_files!  {\n    \"file\": \"%%f\",\n    \"sha256\": \"!hash!\"\n  },\n"
        set "yaml_files=!yaml_files!- file: %%f\n  sha256: !hash!\n"
    )
)

REM Strip trailing comma
set "json_files=!json_files:~0,-2!"

REM Write meta.json
(
    echo {
    echo   "timestamp": "!tstamp!",
    echo   "algorithm": "!algo!",
    if defined bits echo   "bits": "!bits!",
    if defined curve echo   "curve": "!curve!",
    echo   "output_folder": "!dir:\=\\!",
    echo   "generated_files": [
    echo !json_files!
    echo   ]
    echo }
) > "!dir!\meta.json"

REM Write meta.yaml
(
    echo timestamp: "!tstamp!"
    echo algorithm: "!algo!"
    if defined bits echo bits: "!bits!"
    if defined curve echo curve: "!curve!"
    echo output_folder: "!dir:\=\\!"
    echo generated_files:
    echo !yaml_files!
) > "!dir!\meta.yaml"

endlocal
exit /b
