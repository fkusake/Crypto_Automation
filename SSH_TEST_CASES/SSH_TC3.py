import subprocess
import time
import pyautogui
import os
from datetime import datetime
import shlex

# ================= CONFIG =================
DUT_IP = os.getenv("DUT_IP")
USER = os.getenv("DUT_USER")
DUT_PASSWORD = os.getenv("DUT_PASSWORD")

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


# ---------------- NEGOTIATION DETECTION ----------------



def check_negotiation(command, algo):

    # 🔥 prepend sshpass to full command string
    full_cmd = f"sshpass -p '{DUT_PASSWORD}' {command}"

    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    output = (result.stdout + result.stderr).lower()

    # 🔍 negotiation logic
    if "no matching" in output or "bad ssh2" in output:
        return False, output

    if algo.lower() in output:
        return True, output

    return False, output

# ------------------- BASE COMMAND BUILDER-----------------

def build_tc3_command(base_cmd, option, value):
    base = base_cmd.replace("ssh ", "").strip()

    if option == "MACs":
        return (
            f"ssh -vv -o BatchMode=no {base} "
            f"-o Ciphers=aes128-ctr "
            f"-o {option}={value} exit 2>&1 | grep 'debug1: kex:'"
        )

    # ✅ Default for others
    return (
        f"ssh -vv -o BatchMode=no {base} "
        f"-o {option}={value} exit 2>&1 | grep 'debug1: kex:'"
    )


# ---------------- MAIN FUNCTION ----------------

def run_ssh_weak_cipher_test(cipher_test_data,ssh_data):

    test_data = {
        "test_case_id": "TC_SSH_WEAK_NEGOTIATION",
        "results": [],
        "screenshots": []
    }

    weak_ciphers = cipher_test_data["details"]["encryption"].get("weak", [])
    weak_macs = cipher_test_data["details"]["mac"].get("weak", [])
    weak_kex = cipher_test_data["details"]["kex"].get("weak", [])
    weak_host = cipher_test_data["details"]["host_key"].get("weak", [])

    base_Command = ssh_data["basecommand"]


    # =====================================================
    # TEST WEAK CIPHERS
    # =====================================================

    for cipher in weak_ciphers:

        cmd = cmd = build_tc3_command(base_Command, "Ciphers", cipher)

        launch_terminal()
        focus_terminal()
        maximize_terminal()

        pyautogui.typewrite(cmd + "\n", interval=0.03)

        time.sleep(3)

        pyautogui.typewrite(DUT_PASSWORD + "\n", interval=0.05)

        time.sleep(6)

        screenshot = take_screenshot(f"weak_cipher_{cipher}")

        close_terminal()

        negotiated, terminal_output = check_negotiation(cmd, cipher)

        test_data["results"].append({
         "type": "cipher",
         "algorithm": cipher,
         "command": cmd,
         "negotiated": negotiated,
          "terminal_output": terminal_output
        })

        test_data["screenshots"].append(screenshot)

        if negotiated:
            return test_data


    # =====================================================
    # TEST WEAK MAC
    # =====================================================

    for mac in weak_macs:

        cmd = build_tc3_command(base_Command, "MACs", mac)

        launch_terminal()
        focus_terminal()
        maximize_terminal()

        pyautogui.typewrite(cmd + "\n", interval=0.03)

        time.sleep(3)

        pyautogui.typewrite(DUT_PASSWORD + "\n", interval=0.05)

        time.sleep(6)

        screenshot = take_screenshot(f"weak_mac_{mac}")

        close_terminal()

        negotiated, terminal_output = check_negotiation(cmd, mac)

        test_data["results"].append({
            "type": "mac",
            "algorithm": mac,
            "command": cmd,
            "negotiated": negotiated,
            "terminal_output": terminal_output
        })

        test_data["screenshots"].append(screenshot)

        if negotiated:
            return test_data


    # =====================================================
    # TEST WEAK KEX
    # =====================================================

    for kex in weak_kex:

        cmd = build_tc3_command(base_Command, "KexAlgorithms", kex)

        launch_terminal()
        focus_terminal()
        maximize_terminal()

        pyautogui.typewrite(cmd + "\n", interval=0.03)

        time.sleep(3)

        pyautogui.typewrite(DUT_PASSWORD + "\n", interval=0.05)

        time.sleep(6)

        screenshot = take_screenshot(f"weak_kex_{kex}")

        close_terminal()

        negotiated, terminal_output = check_negotiation(cmd, kex)

        test_data["results"].append({
            "type": "kex",
            "algorithm": kex,
            "command": cmd,
            "negotiated": negotiated,
            "terminal_output": terminal_output
        })

        test_data["screenshots"].append(screenshot)

        if negotiated:
            return test_data


    # =====================================================
    # TEST WEAK HOST KEY
    # =====================================================

    for host in weak_host:

        cmd = build_tc3_command(base_Command, "HostKeyAlgorithms", host)

        launch_terminal()
        focus_terminal()
        maximize_terminal()

        pyautogui.typewrite(cmd + "\n", interval=0.03)

        time.sleep(3)

        pyautogui.typewrite(DUT_PASSWORD + "\n", interval=0.05)

        time.sleep(6)

        screenshot = take_screenshot(f"weak_hostkey_{host}")

        close_terminal()

        negotiated, terminal_output = check_negotiation(cmd, host)

        test_data["results"].append({
            "type": "host_key",
            "algorithm": host,
            "command": cmd,
            "negotiated": negotiated,
            "terminal_output": terminal_output
        })

        test_data["screenshots"].append(screenshot)

        if negotiated:
            return test_data


    return test_data


# -------- OPTIONAL RUN --------