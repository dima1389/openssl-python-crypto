import os
import shutil
import subprocess
import hashlib
import json
import yaml
from datetime import datetime

# === CONFIG ===
password = "password"
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
    json_files = []
    yaml_files = []

    for f in files:
        full_path = os.path.join(dirpath, f)
        if os.path.isfile(full_path):
            hash = sha256sum(full_path)
            json_files.append({"file": f, "sha256": hash})
            yaml_files.append({"file": f, "sha256": hash})

    meta_json = {
        "timestamp": timestamp,
        "algorithm": algo,
        "output_folder": dirpath.replace("\\", "\\\\"),
        "generated_files": json_files
    }
    if bits: meta_json["bits"] = bits
    if curve: meta_json["curve"] = curve

    meta_yaml = {
        "timestamp": timestamp,
        "algorithm": algo,
        "output_folder": dirpath.replace("\\", "\\\\"),
        "generated_files": yaml_files
    }
    if bits: meta_yaml["bits"] = bits
    if curve: meta_yaml["curve"] = curve

    with open(os.path.join(dirpath, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_json, f, indent=2)
    with open(os.path.join(dirpath, "meta.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(meta_yaml, f, allow_unicode=True)

# === AES ===
for bits in [128, 192, 256]:
    algo = "AES"
    dirpath = os.path.join(outdir_symmetric, "AES", f"AES{bits}")
    os.makedirs(dirpath, exist_ok=True)
    subprocess.run(["openssl", "rand", "-out", os.path.join(dirpath, "key.bin"), str(bits)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"Generated AES {bits}-bit key -> {dirpath}")
    write_meta(algo, str(bits), "", dirpath, ["key.bin"])

# === RSA ===
for bits in [2048, 3072, 4096]:
    algo = "RSA"
    dirpath = os.path.join(outdir_asymmetric, "RSA", f"RSA{bits}")
    os.makedirs(dirpath, exist_ok=True)
    subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-aes256", "-pass", f"pass:{password}",
                    "-out", os.path.join(dirpath, "private_key.pem"),
                    "-pkeyopt", f"rsa_keygen_bits:{bits}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["openssl", "pkey", "-in", os.path.join(dirpath, "private_key.pem"), "-passin", f"pass:{password}",
                    "-outform", "DER", "-out", os.path.join(dirpath, "private_key.der")], stdout=subprocess.DEVNULL)
    subprocess.run(["openssl", "rsa", "-in", os.path.join(dirpath, "private_key.pem"), "-passin", f"pass:{password}",
                    "-pubout", "-out", os.path.join(dirpath, "public_key.pem")], stdout=subprocess.DEVNULL)
    subprocess.run(["openssl", "rsa", "-in", os.path.join(dirpath, "private_key.pem"), "-passin", f"pass:{password}",
                    "-pubout", "-outform", "DER", "-out", os.path.join(dirpath, "public_key.der")], stdout=subprocess.DEVNULL)
    log(f"Generated RSA {bits}-bit key pair -> {dirpath}")
    write_meta(algo, str(bits), "", dirpath, [
        "private_key.pem", "private_key.der", "public_key.pem", "public_key.der"
    ])

# === EC Curves ===
for curve in ["prime256v1", "secp384r1", "secp521r1", "secp256k1"]:
    algo = "EC"
    dirpath = os.path.join(outdir_asymmetric, "EC-Curves", f"EC_{curve}")
    os.makedirs(dirpath, exist_ok=True)
    private_pem = os.path.join(dirpath, "private_key.pem")
    subprocess.run(
        f'openssl ecparam -name {curve} -genkey -noout | openssl ec -aes256 -passout pass:{password} -out "{private_pem}"',
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["openssl", "ec", "-in", private_pem, "-passin", f"pass:{password}",
                    "-outform", "DER", "-out", os.path.join(dirpath, "private_key.der")], stdout=subprocess.DEVNULL)
    subprocess.run(["openssl", "ec", "-in", private_pem, "-passin", f"pass:{password}",
                    "-pubout", "-out", os.path.join(dirpath, "public_key.pem")], stdout=subprocess.DEVNULL)
    subprocess.run(["openssl", "ec", "-in", private_pem, "-passin", f"pass:{password}",
                    "-pubout", "-outform", "DER", "-out", os.path.join(dirpath, "public_key.der")], stdout=subprocess.DEVNULL)
    log(f"Generated EC {curve} key -> {dirpath}")
    write_meta(algo, "", curve, dirpath, [
        "private_key.pem", "private_key.der", "public_key.pem", "public_key.der"
    ])

# === DSA ===
algo = "DSA"
bits = "2048"
dirpath = os.path.join(outdir_asymmetric, "DSA", "DSA2048")
os.makedirs(dirpath, exist_ok=True)
subprocess.run(["openssl", "dsaparam", "-out", os.path.join(dirpath, "dsaparam.pem"), bits], stdout=subprocess.DEVNULL)
subprocess.run(["openssl", "gendsa", "-aes256", "-passout", f"pass:{password}",
                "-out", os.path.join(dirpath, "private_key.pem"), os.path.join(dirpath, "dsaparam.pem")], stdout=subprocess.DEVNULL)
subprocess.run(["openssl", "dsa", "-in", os.path.join(dirpath, "private_key.pem"), "-passin", f"pass:{password}",
                "-pubout", "-out", os.path.join(dirpath, "public_key.pem")], stdout=subprocess.DEVNULL)
log(f"Generated DSA {bits}-bit key -> {dirpath}")
write_meta(algo, bits, "", dirpath, [
    "dsaparam.pem", "private_key.pem", "public_key.pem"
])

# === EdDSA ===
for algo in ["ED25519", "ED448"]:
    dirpath = os.path.join(outdir_asymmetric, "EdDSA", algo)
    os.makedirs(dirpath, exist_ok=True)
    subprocess.run(["openssl", "genpkey", "-algorithm", algo, "-out", os.path.join(dirpath, "private_key.pem")], stdout=subprocess.DEVNULL)
    subprocess.run(["openssl", "pkey", "-in", os.path.join(dirpath, "private_key.pem"),
                    "-pubout", "-out", os.path.join(dirpath, "public_key.pem")], stdout=subprocess.DEVNULL)
    log(f"Generated {algo} key -> {dirpath}")
    write_meta(algo, "", "", dirpath, [
        "private_key.pem", "public_key.pem"
    ])

log("=== Key Generation Complete ===")
print(f"Keys created successfully. See: {global_log}")
