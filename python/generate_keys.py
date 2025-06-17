import os
import shutil
import hashlib
import json
import yaml
from datetime import datetime
from secrets import token_bytes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, ed448
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# === CONFIG ===
password = b"password"
outdir = "keys"
global_log = os.path.join(outdir, "keygen.log")
outdir_symmetric = os.path.join(outdir, "symmetric-encryption")
outdir_asymmetric = os.path.join(outdir, "asymmetric-encryption")

# === CLEANUP ===
if os.path.exists(outdir):
    shutil.rmtree(outdir)

# === INIT FOLDERS ===
os.makedirs(os.path.join(outdir_symmetric, "AES"), exist_ok=True)
for name in ["RSA", "EC-Curves", "DSA", "EdDSA"]:
    os.makedirs(os.path.join(outdir_asymmetric, name), exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime("%a %d.%m.%Y. %H:%M:%S")
    with open(global_log, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def sha256sum(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def write_meta(algo, bits, curve, dirpath, files):
    timestamp = datetime.now().strftime("%a %d.%m.%Y. %H:%M:%S")
    filelist = [{"file": f, "sha256": sha256sum(os.path.join(dirpath, f))} for f in files]
    meta = {
        "timestamp": timestamp,
        "algorithm": algo,
        "output_folder": dirpath.replace("\\", "\\\\"),
        "generated_files": filelist
    }
    if bits: meta["bits"] = bits
    if curve: meta["curve"] = curve

    with open(os.path.join(dirpath, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    with open(os.path.join(dirpath, "meta.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(meta, f, allow_unicode=True)

# === AES ===
for bits in [128, 192, 256]:
    algo = "AES"
    dirpath = os.path.join(outdir_symmetric, "AES", f"AES{bits}")
    os.makedirs(dirpath, exist_ok=True)
    key = token_bytes(bits // 8)
    with open(os.path.join(dirpath, "key.bin"), "wb") as f:
        f.write(key)
    log(f"Generated AES {bits}-bit key -> {dirpath}")
    write_meta(algo, str(bits), "", dirpath, ["key.bin"])

# === RSA ===
for bits in [2048, 3072, 4096]:
    algo = "RSA"
    dirpath = os.path.join(outdir_asymmetric, "RSA", f"RSA{bits}")
    os.makedirs(dirpath, exist_ok=True)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password)
    )
    private_der = private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password)
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(os.path.join(dirpath, "private_key.pem"), "wb") as f: f.write(private_pem)
    with open(os.path.join(dirpath, "private_key.der"), "wb") as f: f.write(private_der)
    with open(os.path.join(dirpath, "public_key.pem"), "wb") as f: f.write(public_pem)
    with open(os.path.join(dirpath, "public_key.der"), "wb") as f: f.write(public_der)

    log(f"Generated RSA {bits}-bit key pair -> {dirpath}")
    write_meta(algo, str(bits), "", dirpath, [
        "private_key.pem", "private_key.der", "public_key.pem", "public_key.der"
    ])

# === EC Curves ===
curve_map = {
    "prime256v1": ec.SECP256R1(),
    "secp384r1": ec.SECP384R1(),
    "secp521r1": ec.SECP521R1(),
    "secp256k1": ec.SECP256K1()
}
for name, curve in curve_map.items():
    algo = "EC"
    dirpath = os.path.join(outdir_asymmetric, "EC-Curves", f"EC_{name}")
    os.makedirs(dirpath, exist_ok=True)
    private_key = ec.generate_private_key(curve)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password)
    )
    private_der = private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password)
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(os.path.join(dirpath, "private_key.pem"), "wb") as f: f.write(private_pem)
    with open(os.path.join(dirpath, "private_key.der"), "wb") as f: f.write(private_der)
    with open(os.path.join(dirpath, "public_key.pem"), "wb") as f: f.write(public_pem)
    with open(os.path.join(dirpath, "public_key.der"), "wb") as f: f.write(public_der)
    log(f"Generated EC {name} key -> {dirpath}")
    write_meta(algo, "", name, dirpath, [
        "private_key.pem", "private_key.der", "public_key.pem", "public_key.der"
    ])

# === EdDSA ===
eddsa_algos = {
    "ED25519": ed25519.Ed25519PrivateKey,
    "ED448": ed448.Ed448PrivateKey
}
for name, cls in eddsa_algos.items():
    algo = name
    dirpath = os.path.join(outdir_asymmetric, "EdDSA", name)
    os.makedirs(dirpath, exist_ok=True)
    private_key = cls.generate()
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(os.path.join(dirpath, "private_key.pem"), "wb") as f: f.write(private_pem)
    with open(os.path.join(dirpath, "public_key.pem"), "wb") as f: f.write(public_pem)
    log(f"Generated {name} key -> {dirpath}")
    write_meta(algo, "", "", dirpath, [
        "private_key.pem", "public_key.pem"
    ])

log("=== Key Generation Complete ===")
print(f"Keys created successfully. See: {global_log}")
