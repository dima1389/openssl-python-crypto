@echo off
setlocal enabledelayedexpansion

set "outdir=keys"
set "password=changeme123"
mkdir %outdir%

REM === AES ===
for %%s in (128 192 256) do (
    set "dir=%outdir%\AES%%s"
    mkdir "!dir!"
    echo [LOG] Generating AES %%s-bit key > "!dir!\log.txt"
    openssl rand -out "!dir!\key.bin" %%s >> "!dir!\log.txt" 2>&1
)

REM === RSA ===
for %%s in (2048 3072 4096) do (
    set "dir=%outdir%\RSA%%s"
    mkdir "!dir!"
    echo [LOG] Generating RSA %%s-bit key pair > "!dir!\log.txt"
    openssl genpkey -algorithm RSA -aes256 -pass pass:%password% -out "!dir!\private_key.pem" -pkeyopt rsa_keygen_bits:%%s >> "!dir!\log.txt" 2>&1
    openssl pkey -in "!dir!\private_key.pem" -passin pass:%password% -outform DER -out "!dir!\private_key.der" >> "!dir!\log.txt" 2>&1
    openssl rsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1
    openssl rsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -outform DER -out "!dir!\public_key.der" >> "!dir!\log.txt" 2>&1
)

REM === EC Curves ===
for %%c in (prime256v1 secp384r1 secp521r1 secp256k1) do (
    set "dir=%outdir%\EC_%%c"
    mkdir "!dir!"
    echo [LOG] Generating EC key with curve %%c > "!dir!\log.txt"
    openssl ecparam -name %%c -genkey -noout | openssl ec -aes256 -passout pass:%password% -out "!dir!\private_key.pem" >> "!dir!\log.txt" 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -outform DER -out "!dir!\private_key.der" >> "!dir!\log.txt" 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1
    openssl ec -in "!dir!\private_key.pem" -passin pass:%password% -pubout -outform DER -out "!dir!\public_key.der" >> "!dir!\log.txt" 2>&1
)

REM === DSA ===
set "dir=%outdir%\DSA2048"
mkdir "!dir!"
echo [LOG] Generating DSA 2048-bit key pair > "!dir!\log.txt"
openssl dsaparam -out "!dir!\dsaparam.pem" 2048 >> "!dir!\log.txt" 2>&1
openssl gendsa -aes256 -passout pass:%password% -out "!dir!\private_key.pem" "!dir!\dsaparam.pem" >> "!dir!\log.txt" 2>&1
openssl dsa -in "!dir!\private_key.pem" -passin pass:%password% -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1

REM === EdDSA ===
for %%a in (ED25519 ED448) do (
    set "dir=%outdir%\%%a"
    mkdir "!dir!"
    echo [LOG] Generating %%a key pair > "!dir!\log.txt"
    openssl genpkey -algorithm %%a -out "!dir!\private_key.pem" >> "!dir!\log.txt" 2>&1
    openssl pkey -in "!dir!\private_key.pem" -pubout -out "!dir!\public_key.pem" >> "!dir!\log.txt" 2>&1
)

echo All keys generated. Check each folder for log.txt and output files.
pause
