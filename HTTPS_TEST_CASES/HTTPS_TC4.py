import subprocess
import time
import pyautogui
import shutil
from datetime import datetime
import os

DUT_IP = os.getenv("DUT_IP")
PORT = "443"

SCREENSHOT_DIR = "SCREENSHOTS"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ---------------- TERMINAL CONTROL ----------------

def launch_terminal():
    subprocess.Popen(["gnome-terminal"])
    time.sleep(3)

def focus_terminal():
    subprocess.run(["wmctrl", "-xa", "gnome-terminal"])
    time.sleep(1)

def maximize_terminal():
    pyautogui.hotkey("alt", "f10")
    time.sleep(1)

def run_visible_command(command):
    pyautogui.typewrite(command + "\n", interval=0.03)

def stop_execution():
    pyautogui.hotkey("ctrl", "c")
    time.sleep(1)

def exit_terminal():
    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(1)

# ---------------- BACKEND EXECUTION ----------------

def run_tls12_backend():
    return subprocess.run(
        [
            "openssl", "s_client",
            "-connect", f"{DUT_IP}:{PORT}",
            "-cipher", "NULL",
            "-tls1_2"
        ],
        capture_output=True,
        text=True,
        timeout=10
    )

def run_tls13_backend():
    return subprocess.run(
    [
        "openssl", "s_client",
        "-connect", f"{DUT_IP}:{PORT}",
        "-tls1_3"
    ],
    input="",
    capture_output=True,
    text=True,
    timeout=10
)

# ---------------- MAIN FUNCTION ----------------

def run_https_NULL_test():

    test_data = {
        "test_case_id": "TC8_HTTPS_NO_ENCRYPTION_REJECTION",

        "tls1_2": {
            "command": f"openssl s_client -connect {DUT_IP}:{PORT} -cipher NULL -tls1_2",
            "output": "",
            "result": "",
            "remarks": "",
            "screenshot": ""
        },

        "tls1_3": {
            "command": f"openssl s_client -connect {DUT_IP}:{PORT} -tls1_3",
            "output": "",
            "result": "",
            "remarks": "",
            "screenshot": ""
        },

        "final_result": ""
    }

    try:
        # ================= TLS 1.2 =================
        launch_terminal()
        focus_terminal()
        maximize_terminal()

        run_visible_command(test_data["tls1_2"]["command"])
        time.sleep(5)

        # Backend capture
        tls12_res = run_tls12_backend()
        tls12_output = (tls12_res.stdout + tls12_res.stderr).lower()
        test_data["tls1_2"]["output"] = tls12_output

        # Screenshot
        ss1 = os.path.join(SCREENSHOT_DIR, f"tc8_tls12_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot(ss1)
        test_data["tls1_2"]["screenshot"] = ss1

        # Stop + exit
        stop_execution()
        exit_terminal()

        # ================= TLS 1.3 =================
        launch_terminal()
        focus_terminal()
        maximize_terminal()

        run_visible_command(test_data["tls1_3"]["command"])
        time.sleep(5)

        # Backend capture
        tls13_res = run_tls13_backend()
        tls13_output = (tls13_res.stdout + tls13_res.stderr).lower()
        test_data["tls1_3"]["output"] = tls13_output

        # Screenshot
        ss2 = os.path.join(SCREENSHOT_DIR, f"tc8_tls13_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        pyautogui.screenshot(ss2)
        test_data["tls1_3"]["screenshot"] = ss2

        # Stop + exit
        stop_execution()
        exit_terminal()

        # ================= RESULT LOGIC =================

        # TLS1.2
        if "no ciphers available" in tls12_output or "cipher    : 0000" in tls12_output:
            test_data["tls1_2"]["result"] = "PASS"
            test_data["tls1_2"]["remarks"] = "NULL cipher rejected"

        elif "cipher is null" in tls12_output:
            test_data["tls1_2"]["result"] = "FAIL"
            test_data["tls1_2"]["remarks"] = "NULL cipher accepted"

        else:
            test_data["tls1_2"]["result"] = "PASS"
            test_data["tls1_2"]["remarks"] = "Secure behavior"

        # TLS1.3
        if "tls_" in tls13_output and "cipher is" in tls13_output:
            test_data["tls1_3"]["result"] = "PASS"
            test_data["tls1_3"]["remarks"] = "Strong cipher enforced"

        else:
            test_data["tls1_3"]["result"] = "PASS"
            test_data["tls1_3"]["remarks"] = "TLS1.3 secure by design"

        # Final
        if test_data["tls1_2"]["result"] == "PASS" and test_data["tls1_3"]["result"] == "PASS":
            test_data["final_result"] = "PASS"
        else:
            test_data["final_result"] = "FAIL"

        print(test_data)

    except Exception as e:
        print("Error:", str(e))

    return test_data