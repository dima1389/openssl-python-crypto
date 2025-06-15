@echo off
setlocal enabledelayedexpansion

REM List of algorithms
set "algos=AES RSA EC"

REM Root output directory
set "outdir=keys"
mkdir %outdir%

REM AES key generation (128, 192, 256-bit)
for %%s in (128 192 256) do (
    set "algo=AES%%s"
    set "dir=%outdir%\!algo!"
    mkdir "!dir!"
    openssl rand -out "!dir!\key.bin" %%s
)

REM RSA key generation (2048 and 4096-bit)
for %%s in (2048 4096) do (
    set "algo=RSA%%s"
    set "dir=%outdir%\!algo!"
    mkdir "!dir!"
    openssl genpkey -algorithm RSA -out "!dir!\private_key.pem" -pkeyopt rsa_keygen_bits:%%s
    openssl rsa -in "!dir!\private_key.pem" -pubout -out "!dir!\public_key.pem"
)

REM EC key generation using prime256v1 and secp384r1 curves
for %%c in (prime256v1 secp384r1) do (
    set "algo=EC_%%c"
    set "dir=%outdir%\!algo!"
    mkdir "!dir!"
    openssl ecparam -name %%c -genkey -noout -out "!dir!\private_key.pem"
    openssl ec -in "!dir!\private_key.pem" -pubout -out "!dir!\public_key.pem"
)

echo Done.
pause
