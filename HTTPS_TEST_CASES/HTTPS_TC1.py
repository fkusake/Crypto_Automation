

import subprocess
import time
import pyautogui
import shutil
from datetime import datetime
import os

DUT_IP = os.getenv("DUT_IP")



# ---------------- WEAK CRYPTO DEFINITIONS ----------------

WEAK_ENCRYPTION = [
    "des",
    "3des",
    "rc4",
    "arcfour",
    "blowfish",
    "cast128",
    "idea",
    "null",
    "none",
    "export",
]

WEAK_MAC = [
    "md5",
    "hmac-md5",
    "sha1",
    "hmac-sha1",
]

WEAK_KEX = [
    "rsa",
    "dh_anon",
]

# ---------------- TERMINAL ----------------

def launch_terminal():
    subprocess.Popen(["gnome-terminal"])
    time.sleep(3)

def focus_terminal():
    subprocess.run(["wmctrl", "-xa", "gnome-terminal"])
    time.sleep(1)

def maximize_terminal():
    pyautogui.hotkey("alt", "f10")
    time.sleep(1)

def run_visible_nmap(command):
    pyautogui.typewrite(command + "\n", interval=0.03)

# ---------------- BACKEND ----------------

def run_nmap_backend():

    if not shutil.which("nmap"):
        return None

    result = subprocess.run(
        ["nmap", "--script", "ssl-enum-ciphers", "-p", "443", DUT_IP],
        capture_output=True,
        text=True
    )

    return result.stdout


# ---------------- UTILITY ----------------

def unique_list(values):
    return list(sorted(set(values)))



# ---- Convert function to SSL format ------

def convert_to_openssl_cipher(cipher):

    cipher = cipher.upper()

    # TLS1.3 fix
    if cipher.startswith("TLS_AKE_WITH_"):
        return cipher.replace("TLS_AKE_WITH_", "TLS_")

    # Remove TLS_
    if cipher.startswith("TLS_"):
        cipher = cipher[4:]

    # Replace WITH
    cipher = cipher.replace("_WITH_", "-")

    parts = cipher.split("_")

    i = 0
    while i < len(parts):
        if parts[i] == "AES" and i + 2 < len(parts):
            combined = f"AES{parts[i+1]}"
            parts.pop(i+1)
            parts[i] = combined
        i += 1

    result = "-".join(parts)

    # 🔥 FINAL FIX
    result = result.replace("AES-128", "AES128").replace("AES-256", "AES256")

    # 🔥 ADD THIS LINE
    result = result.replace("-CHACHA20-POLY1305-SHA256", "-CHACHA20-POLY1305")

    return result

# ---------------- TLS VERSION PARSER (UPDATED) ----------------

def parse_tls_versions(output):

    tls_data = {
        "TLSv1.2": {"ciphers": []},
        "TLSv1.3": {"ciphers": []}
    }

    current_version = None

    for line in output.splitlines():

        line = line.strip()

        if "TLSv1.2:" in line:
            current_version = "TLSv1.2"
            continue

        if "TLSv1.3:" in line:
            current_version = "TLSv1.3"
            continue

        if "TLS_" in line and current_version:

            raw_cipher = line.replace("|", "").strip().split(" ")[0]

            cipher = convert_to_openssl_cipher(raw_cipher)

            tls_data[current_version]["ciphers"].append(cipher)

    # Remove duplicates
    for version in tls_data:
        tls_data[version]["ciphers"] = unique_list(
            tls_data[version]["ciphers"]
        )

    return tls_data

# ---------------- CLASSIFICATION (UPDATED) ----------------

def classify_tls_ciphers(cipher_list):

    strong = []
    weak = []

    for cipher in cipher_list:

        if (
            any(w in cipher for w in WEAK_ENCRYPTION)
            or any(w in cipher for w in WEAK_MAC)
            or any(w in cipher for w in WEAK_KEX)
        ):
            weak.append(cipher)
        else:
            strong.append(cipher)

    return strong, weak


# ---------------- MAIN FUNCTION ----------------

def run_httpsCipher_detection():

    cipher_test_data = {
        "test_case_id": "TC1_HTTPS_CRYPTO_HARDENING",
        "user_input": f"nmap --script ssl-enum-ciphers -p 443 {DUT_IP}",
        "terminal_output": "",
        "result": "",
        "details": {
            "TLSv1.2": {},
            "TLSv1.3": {},
        },
        "screenshot": ""
    }

    # -------- TERMINAL --------
    launch_terminal()
    focus_terminal()
    maximize_terminal()

    run_visible_nmap(cipher_test_data["user_input"])

    time.sleep(6)

    # -------- BACKEND --------
    output = run_nmap_backend()

    cipher_test_data["terminal_output"] = output

    if not output:
        cipher_test_data["result"] = "FAIL"
        return cipher_test_data


    # -------- PARSE TLS OUTPUT --------
    tls_data = parse_tls_versions(output)


    # -------- CLASSIFY (CIPHER SUITE LEVEL) --------

    strong_12, weak_12 = classify_tls_ciphers(
        tls_data["TLSv1.2"]["ciphers"]
    )

    strong_13, weak_13 = classify_tls_ciphers(
        tls_data["TLSv1.3"]["ciphers"]
    )


    # -------- STORE RESULTS --------

    cipher_test_data["details"]["TLSv1.2"] = {
        "ciphers": {
            "strong": strong_12,
            "weak": weak_12
        }
    }

    cipher_test_data["details"]["TLSv1.3"] = {
        "ciphers": {
            "strong": strong_13,
            "weak": weak_13
        }
    }


    # -------- FINAL RESULT --------

    cipher_test_data["result"] = (
        "FAIL"
        if (weak_12 or weak_13)
        else "PASS"
    )


    # -------- SCREENSHOT --------

    screenshot_name = f"cipher_terminal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    screenshot_path = os.path.join("SCREENSHOTS", screenshot_name)

    pyautogui.screenshot(screenshot_path)

    cipher_test_data["screenshot"] = screenshot_path


    # -------- CLOSE TERMINAL --------

    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(1)


    print(cipher_test_data)

    return cipher_test_data