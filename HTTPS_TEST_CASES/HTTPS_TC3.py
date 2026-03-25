import subprocess
import time
import pyautogui
import os
from datetime import datetime

# ================= CONFIG =================
DUT_IP = os.getenv("DUT_IP")

SCREENSHOT_DIR = "SCREENSHOTS"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
# =========================================


# ---------------- TERMINAL CONTROL ----------------

def launch_terminal():
    subprocess.Popen(["gnome-terminal"])
    time.sleep(4)


def focus_terminal():
    subprocess.run(["wmctrl", "-xa", "gnome-terminal"])
    time.sleep(1)


def maximize_terminal():
    pyautogui.hotkey("alt", "f10")
    time.sleep(1)


def close_terminal():
    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(1)


# ---------------- SCREENSHOT ----------------

def take_screenshot(label):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOT_DIR}/{ts}_{label}.png"
    pyautogui.screenshot(path)
    return path


# ---------------- MAIN FUNCTION ----------------

def run_https_weak_cipher_test(cipher_test_data):

    test_data = {
        "test_case_id": "TC7_HTTPS_WEAK_CIPHER_NEGOTIATION",
        "results": [],
        "screenshots": []
    }

    # Extract weak ciphers
    weak_tls12 = cipher_test_data["details"]["TLSv1.2"]["ciphers"].get("weak", [])
    weak_tls13 = cipher_test_data["details"]["TLSv1.3"]["ciphers"].get("weak", [])

    all_weak_ciphers = [
        ("TLSv1.2", cipher) for cipher in weak_tls12
    ] + [
        ("TLSv1.3", cipher) for cipher in weak_tls13
    ]

    # =====================================================
    # TEST WEAK TLS CIPHER SUITES
    # =====================================================

    for tls_version, cipher in all_weak_ciphers:

        if tls_version == "TLSv1.2":
            cmd = f"echo | openssl s_client -connect {DUT_IP}:443 -tls1_2 -cipher {cipher} 2>&1 | grep -Ei 'Cipher is|handshake failure|no shared cipher|no cipher match'"
        else:
            cmd = f"echo | openssl s_client -connect {DUT_IP}:443 -tls1_3 -ciphersuites {cipher} 2>&1 | grep -Ei 'Cipher is|handshake failure|no shared cipher|no cipher match'"

        # -------- TERMINAL (FOR SCREENSHOT ONLY) --------
        launch_terminal()
        focus_terminal()
        maximize_terminal()

        pyautogui.typewrite(cmd + "\n", interval=0.03)

        time.sleep(5)

        screenshot = take_screenshot(f"https_tc7_weak_{cipher}")

        close_terminal()

        # -------- BACKEND EXECUTION (SAFE) --------
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5   # 🔥 prevents hanging
            )
            output = (result.stdout + result.stderr).strip().lower()

        except subprocess.TimeoutExpired as e:
            output = (e.stdout or "") + (e.stderr or "")
            output = output.strip().lower()

        # -------- NEGOTIATION DETECTION --------
        if not output:
            negotiated = False

        elif "cipher is (none)" in output:
            negotiated = False

        elif "handshake failure" in output or "no shared cipher" in output:
            negotiated = False

        elif "cipher is" in output:
            negotiated = True

        else:
            negotiated = False

        # -------- STORE RESULT --------
        test_data["results"].append({
            "tls_version": tls_version,
            "cipher": cipher,
            "command": cmd,
            "negotiated": negotiated,
            "terminal_output": output
        })

        test_data["screenshots"].append(screenshot)

        # 🚨 FAIL FAST (SSH STYLE)
        if negotiated:
            return test_data

    return test_data