import subprocess
import time
import pyautogui
import os
import re
from datetime import datetime

# ================= CONFIG =================
INTERFACE = os.getenv("INTERFACE")
DUT_IP = os.getenv("DUT_IP")


SCREENSHOT_DIR = "SCREENSHOTS"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

PCAP_DIR = "PCAP_FILES"
os.makedirs(PCAP_DIR, exist_ok=True)
# =========================================


# ---------------- TERMINAL CONTROL ----------------

def launch_terminal():
    subprocess.Popen(["gnome-terminal"])
    time.sleep(4)


def focus_window_by_title(title):
    subprocess.run(["wmctrl", "-a", title])
    time.sleep(1)


def maximize_terminal():
    pyautogui.hotkey("alt", "f10")
    time.sleep(1)


def close_terminal():
    pyautogui.hotkey("ctrl", "c")
    time.sleep(1)

    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(0.5)


# ---------------- PHASE 1: TLS INPUT / OUTPUT ----------------

def capture_tls_terminal_output(ip):

    result = subprocess.run(
        ["openssl", "s_client", "-connect", f"{ip}:443"],
        capture_output=True,
        text=True,
        input=""
    )

    return result.stdout.strip()


# ---------------- WIRESHARK ----------------

def launch_wireshark():

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    global PCAP_FILE
    PCAP_FILE = f"full_capture_{ts}.pcap"

    subprocess.Popen([
        "wireshark",
        "-i", INTERFACE,
        "-k",
        "-w", PCAP_FILE
    ])

    print(f"Wireshark capture started → {PCAP_FILE}")

    time.sleep(8)


def focus_wireshark():
    subprocess.run(["wmctrl", "-xa", "wireshark"])
    time.sleep(1)


def apply_tls_filter():
    pyautogui.hotkey("ctrl", "/")
    time.sleep(1)
    pyautogui.typewrite("tls", interval=0.05)
    pyautogui.press("enter")
    time.sleep(2)


# ---------------- WIRESHARK PACKET NAVIGATION ----------------

def select_packet1():
    pyautogui.press("tab")
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "home")
    time.sleep(0.3)

    for _ in range(1):
        pyautogui.press("down")
        time.sleep(0.25)
    
    pyautogui.press("tab")
    time.sleep(0.3)

    for _ in range(4):
        pyautogui.press("down")
        time.sleep(0.25)

    pyautogui.press("right")
    time.sleep(0.3)

    for _ in range(1):
        pyautogui.press("down")
        time.sleep(0.25)
    
    pyautogui.press("right")
    time.sleep(0.3)

    for _ in range(4):
        pyautogui.press("down")
        time.sleep(0.25)

    pyautogui.press("right")
    time.sleep(0.3)
    
    for _ in range(7):
        pyautogui.press("down")
        time.sleep(0.25)


# ---------------- SCREENSHOT ----------------

def take_screenshot(label):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOT_DIR}/{ts}_{label}.png"
    pyautogui.screenshot(path)
    return path


# ---------------- CLI PACKET CAPTURE ----------------

def open_capture_terminal():

    subprocess.Popen([
        "gnome-terminal",
        "--title=TLS_CAPTURE",
        "--"
    ])
    time.sleep(2)

    focus_window_by_title("TLS_CAPTURE")
    maximize_terminal()

    pyautogui.typewrite(
        f'tshark -i {INTERFACE} '
        f'-f "tcp port 443" '
        f'-Y "tls" '
        f'-T fields '
        f'-e frame.number '
        f'-e _ws.col.Info '
        f'-e tls.handshake.ciphersuite\n',
        interval=0
    )

    print("TLS capture terminal started and listening...")
    time.sleep(4)


# ---------------- TLS CLIENT TERMINAL ----------------

def open_tls_terminal():

    subprocess.Popen([
        "gnome-terminal",
        "--title=TLS_CLIENT",
        "--"
    ])
    time.sleep(2)

    focus_window_by_title("TLS_CLIENT")
    maximize_terminal()

    pyautogui.typewrite(
        f"openssl s_client -connect {DUT_IP}:443\n",
        interval=0.05
    )

    time.sleep(6)

    pyautogui.hotkey("ctrl", "c")
    time.sleep(1)

    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(1)

    print("TLS session completed.")


# ---------------- PHASE 3: TLS CRYPTO EXTRACTION ----------------

def extract_tls_crypto(ip):

    result = subprocess.run(
        ["openssl", "s_client", "-connect", f"{ip}:443"],
        capture_output=True,
        text=True,
        input=""
    )

    data = result.stdout

    protocol = "Not Found"
    cipher = "Not Found"

    # Extract from line: "New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384"
    match = re.search(r"New,\s*(TLSv[0-9.]+),\s*Cipher is\s*([A-Z0-9_\-]+)", data)

    if match:
        protocol = match.group(1)
        cipher = match.group(2)

    return {
        "protocol": protocol,
        "cipher": cipher
    }


# ---------------- VALIDATION ----------------

def contains_weak(value, weak_list):
    if not value or value == "Not Found":
        return True
    v = value.lower()
    return any(w in v for w in weak_list)


WEAK_TLS = ["des","3des","rc4","null","export"]


def tls_validate(crypto):

    results = {}

    results["protocol"] = "PASS" if crypto.get("protocol") in ["TLSv1.2","TLSv1.3"] else "FAIL"
    results["cipher"] = "FAIL" if contains_weak(crypto.get("cipher"), WEAK_TLS) else "PASS"

    final_result = "PASS" if all(v == "PASS" for v in results.values()) else "FAIL"

    return results, final_result


# ---------------- MAIN FUNCTION ----------------

def run_tls_verification():

    tls_test_data = {
        "test_case_id": "TC2_PROTECT_DATA_INFO_TRANSFER_USING_HTTPS",
        "user_input": f"openssl s_client -connect {DUT_IP}:443",
        "terminal_output": "",
        "crypto_details": {},
        "nist_validation": {},
        "final_result": "",
        "screenshots": [],
        "pcap_file": ""
    }

    # ========= PHASE 1 =========
    tls_output = capture_tls_terminal_output(DUT_IP)
    tls_test_data["terminal_output"] = tls_output

    # ========= PHASE 2 =========
    launch_wireshark()
    focus_wireshark()
    apply_tls_filter()

    open_capture_terminal()
    open_tls_terminal()

    focus_window_by_title("TLS_CAPTURE")

    tls_test_data["screenshots"].append(
        take_screenshot("cli_tls_capture")
    )

    close_terminal()

    focus_wireshark()

    select_packet1()

    tls_test_data["screenshots"].append(
        take_screenshot("tls_server_hello_packet")
    )

    # ========= PHASE 3 =========
    crypto = extract_tls_crypto(DUT_IP)
    validation, overall_result = tls_validate(crypto)

    tls_test_data["crypto_details"] = crypto
    tls_test_data["nist_validation"] = validation
    tls_test_data["final_result"] = overall_result

    TLS_ONLY_PCAP = os.path.join(
    PCAP_DIR,
    PCAP_FILE.replace("full_capture", "tls_only_capture")
    )

    subprocess.run([
        "tshark",
        "-r", PCAP_FILE,
        "-Y", "tls",
        "-w", TLS_ONLY_PCAP
    ])

    os.remove(PCAP_FILE)

    tls_test_data["pcap_file"] = TLS_ONLY_PCAP

    subprocess.run(["pkill", "-f", "wireshark"])

    return tls_test_data