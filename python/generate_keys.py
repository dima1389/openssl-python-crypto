import os
import shutil
import hashlib
import json
import yaml
import platform
import getpass
from datetime import datetime
from pathlib import Path
from secrets import token_bytes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, ed448
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# === CONFIGURATION ===
PASSWORD = os.environ.get("KEY_PASSWORD", "default_password").encode()
OUTDIR = Path("keys")
LOGFILE = OUTDIR / "keygen.log"
OUTDIR_SYM = OUTDIR / "symmetric-encryption"
OUTDIR_ASYM = OUTDIR / "asymmetric-encryption"

# === UTILITY FUNCTIONS ===
def log(message):
    timestamp = datetime.now().strftime("%a %d.%m.%Y. %H:%M:%S")
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def sha256sum(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def write_meta(algo, bits, curve, dirpath, files):
    timestamp = datetime.now().strftime("%a %d.%m.%Y. %H:%M:%S")
    filelist = [{"file": str(f.name), "sha256": sha256sum(f)} for f in files]
    meta = {
        "timestamp": timestamp,
        "algorithm": algo,
        "output_folder": str(dirpath),
        "generated_files": filelist,
        "user": getpass.getuser(),
        "host": platform.node(),
        "python_version": platform.python_version()
    }
    if bits: meta["bits"] = bits
    if curve: meta["curve"] = curve

    with open(dirpath / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    with open(dirpath / "meta.yaml", "w", encoding="utf-8") as f:
        yaml.dump(meta, f, allow_unicode=True)

    with open(dirpath / "key_info.txt", "w", encoding="utf-8") as f:
        f.write(f"{algo} key generated on {timestamp}\n")

# === GENERATORS ===
def generate_aes_keys():
    for bits in [128, 192, 256]:
        dirpath = OUTDIR_SYM / "AES" / f"AES{bits}"
        dirpath.mkdir(parents=True, exist_ok=True)
        key = token_bytes(bits // 8)
        key_file = dirpath / "key.bin"
        with open(key_file, "wb") as f:
            f.write(key)
        log(f"Generated AES {bits}-bit key -> {dirpath}")
        write_meta("AES", str(bits), None, dirpath, [key_file])

def generate_rsa_keys():
    for bits in [2048, 3072, 4096]:
        dirpath = OUTDIR_ASYM / "RSA" / f"RSA{bits}"
        dirpath.mkdir(parents=True, exist_ok=True)
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
        files = []
        for fmt in ["pem", "der"]:
            enc = serialization.Encoding.PEM if fmt == "pem" else serialization.Encoding.DER
            priv = dirpath / f"private_key.{fmt}"
            pub = dirpath / f"public_key.{fmt}"
            with open(priv, "wb") as f:
                f.write(private_key.private_bytes(enc, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(PASSWORD)))
            with open(pub, "wb") as f:
                f.write(private_key.public_key().public_bytes(enc, serialization.PublicFormat.SubjectPublicKeyInfo))
            files += [priv, pub]
        log(f"Generated RSA {bits}-bit key pair -> {dirpath}")
        write_meta("RSA", str(bits), None, dirpath, files)

def generate_ec_keys():
    curves = {
        "prime256v1": ec.SECP256R1(),
        "secp384r1": ec.SECP384R1(),
        "secp521r1": ec.SECP521R1(),
        "secp256k1": ec.SECP256K1()
    }
    for name, curve in curves.items():
        dirpath = OUTDIR_ASYM / "EC-Curves" / f"EC_{name}"
        dirpath.mkdir(parents=True, exist_ok=True)
        private_key = ec.generate_private_key(curve)
        files = []
        for fmt in ["pem", "der"]:
            enc = serialization.Encoding.PEM if fmt == "pem" else serialization.Encoding.DER
            priv = dirpath / f"private_key.{fmt}"
            pub = dirpath / f"public_key.{fmt}"
            with open(priv, "wb") as f:
                f.write(private_key.private_bytes(enc, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(PASSWORD)))
            with open(pub, "wb") as f:
                f.write(private_key.public_key().public_bytes(enc, serialization.PublicFormat.SubjectPublicKeyInfo))
            files += [priv, pub]
        log(f"Generated EC {name} key -> {dirpath}")
        write_meta("EC", None, name, dirpath, files)

def generate_eddsa_keys():
    algos = {
        "ED25519": ed25519.Ed25519PrivateKey,
        "ED448": ed448.Ed448PrivateKey
    }
    for name, cls in algos.items():
        dirpath = OUTDIR_ASYM / "EdDSA" / name
        dirpath.mkdir(parents=True, exist_ok=True)
        private_key = cls.generate()
        priv_file = dirpath / "private_key.pem"
        pub_file = dirpath / "public_key.pem"
        with open(priv_file, "wb") as f:
            f.write(private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        with open(pub_file, "wb") as f:
            f.write(private_key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        log(f"Generated {name} key -> {dirpath}")
        write_meta(name, None, None, dirpath, [priv_file, pub_file])

# === MAIN EXECUTION ===
def main():
    if OUTDIR.exists():
        log(f"WARNING: Removing existing directory {OUTDIR}")
        shutil.rmtree(OUTDIR)
    OUTDIR_SYM.mkdir(parents=True, exist_ok=True)
    for name in ["RSA", "EC-Curves", "DSA", "EdDSA"]:
        (OUTDIR_ASYM / name).mkdir(parents=True, exist_ok=True)

    generate_aes_keys()
    generate_rsa_keys()
    generate_ec_keys()
    generate_eddsa_keys()

    log("=== Key Generation Complete ===")
    print(f"Keys created successfully. See log: {LOGFILE}")

if __name__ == "__main__":
    main()
