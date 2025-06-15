@echo off
setlocal enabledelayedexpansion

REM === Configuration ===
set "password=password"
set "global_log=keys\keygen.log"
set "outdir_symmetric=keys\symmetric-encryption"
set "outdir_asymmetric=keys\asymmetric-encryption"

REM === Initialization ===
mkdir "%outdir_symmetric%\AES"
mkdir "%outdir_asymmetric%\RSA"
mkdir "%outdir_asymmetric%\EC-Curves"
mkdir "%outdir_asymmetric%\DSA"
mkdir "%outdir_asymmetric%\EdDSA"
if exist "%global_log%" del "%global_log%"

call :log "=== Key Generation Started ==="

REM === AES (Symmetric) ===
for %%s in (128 192 256) do (
    set "dir=%outdir_symmetric%\AES\AES%%s"
    mkdir "!dir!"
    call :log "Generating AES %%s-bit key -> !dir!"
    echo [LOG] AES %%s-bit > "!dir!\log.txt"
    openssl rand -out "!dir!\key.bin" %%s >> "!dir!\log.txt" 2>&1
    call :log "AES %%s-bit key generation DONE"
)

REM === RSA (Asymmetric) ===
for %%s in (2048 3072 4096) do (
    set "dir=%outdir_asymmetric%\RSA\RSA%%s"
    mkdir "!dir!"
    call :log "Generating RSA %%s-bit key -> !dir!"
    echo [LOG] RSA %%s-bit > "!dir!\log.txt"
    openssl genpkey -algorithm RSA -aes256 -pass pass:%password% -out "!dir!\private_key.pem" -pkeyopt rsa_keygen_bits:%%s >> "!dir!\log.txt" 2>&1
    openssl pkey -in "!dir!\private_key.pem" -passin pass:%password% -outform DER -out "!dir!\private_key.der" >> "!dir!\log.txt" 2>&1
    openssl rsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1
    openssl rsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -outform DER -out "!dir!\public_key.der" >> "!dir!\log.txt" 2>&1
    call :log "RSA %%s-bit key generation DONE"
)

REM === EC Curves (Asymmetric) ===
for %%c in (prime256v1 secp384r1 secp521r1 secp256k1) do (
    set "dir=%outdir_asymmetric%\EC-Curves\EC_%%c"
    mkdir "!dir!"
    call :log "Generating EC key with curve %%c -> !dir!"
    echo [LOG] EC %%c > "!dir!\log.txt"
    openssl ecparam -name %%c -genkey -noout | openssl ec -aes256 -passout pass:%password% -out "!dir!\private_key.pem" >> "!dir!\log.txt" 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -outform DER -out "!dir!\private_key.der" >> "!dir!\log.txt" 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -pubout -outform DER -out "!dir!\public_key.der" >> "!dir!\log.txt" 2>&1
    call :log "EC %%c key generation DONE"
)

REM === DSA (Asymmetric) ===
set "dir=%outdir_asymmetric%\DSA\DSA2048"
mkdir "!dir!"
call :log "Generating DSA 2048-bit key -> !dir!"
echo [LOG] DSA 2048-bit > "!dir!\log.txt"
openssl dsaparam -out "!dir!\dsaparam.pem" 2048 >> "!dir!\log.txt" 2>&1
openssl gendsa -aes256 -passout pass:%password% -out "!dir!\private_key.pem" "!dir!\dsaparam.pem" >> "!dir!\log.txt" 2>&1
openssl dsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1
call :log "DSA 2048-bit key generation DONE"

REM === EdDSA (Asymmetric) ===
for %%a in (ED25519 ED448) do (
    set "dir=%outdir_asymmetric%\EdDSA\%%a"
    mkdir "!dir!"
    call :log "Generating %%a key -> !dir!"
    echo [LOG] %%a > "!dir!\log.txt"
    openssl genpkey -algorithm %%a -out "!dir!\private_key.pem" >> "!dir!\log.txt" 2>&1
    openssl pkey -in "!dir!\private_key.pem" -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1
    call :log "%%a key generation DONE"
)

call :log "=== Key Generation Complete ==="
echo All keys generated. See log: %global_log%
pause
exit /b

REM === Logging function ===
:log
setlocal
set "msg=%~1"
for /f "tokens=1-3 delims=:.," %%a in ("%time%") do (
    set "timestamp=%date% %%a:%%b:%%c"
)
echo [%timestamp%] %msg% >> "%global_log%"
endlocal
exit /b
