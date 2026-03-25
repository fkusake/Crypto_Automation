import subprocess
import time
import pyautogui
import shutil
from datetime import datetime
import os

DUT_IP = os.getenv("DUT_IP")
USER = os.getenv("DUT_USER")


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

def exit_terminal():
    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(1)

# ---------------- BACKEND EXECUTION ----------------

def run_none_cipher_backend():

    if not shutil.which("ssh"):
        return None

    result = subprocess.run(
        [
            "ssh",
            "-o", "Ciphers=none",
            "-o", "StrictHostKeyChecking=no",
            f"{USER}@{DUT_IP}",
            "exit"
        ],
        capture_output=True,
        text=True,
        timeout=10
    )

    return result

# ---------------- MAIN FUNCTION ----------------

def run_ssh_none_cipher_test(cipher_data):

    test_data = {
        "test_case_id": "TC4_SSH_NONE_CIPHER",

        "user_input": f"ssh -o Ciphers=none {USER}@{DUT_IP}",
        "terminal_output": "",

        "screenshot": "",

        "result": "",
        "remarks": "",
        "None_cipher_exist":False
    }

    try:

        launch_terminal()
        focus_terminal()
        maximize_terminal()

        # -------- RUN COMMAND VISIBLY --------

        run_visible_command(test_data["user_input"])

        time.sleep(5)

        # -------- BACKEND EXECUTION --------

        backend_result = run_none_cipher_backend()

        if backend_result:

            output = (backend_result.stdout + backend_result.stderr).lower()
            test_data["terminal_output"] = output

# Extract encryption algorithms from TC1 data
        encryption_algos = cipher_data["details"]["encryption"]["strong"] + cipher_data["details"]["encryption"]["weak"]

# -------- CASE 1: Server supports NONE cipher (CRITICAL FAIL) --------
        if "none" in [algo.lower() for algo in encryption_algos]:

            test_data["result"] = "FAIL"
            test_data["None_cipher_exist"] = True
            test_data["remarks"] = (
            "DUT supports 'none' cipher in encryption algorithms (critical security issue)"
        )

# -------- CASE 2: Client blocks NONE cipher --------
        elif "bad ssh2 cipher spec" in output:

         test_data["result"] = "PASS"
         test_data["remarks"] = (
         "SSH client blocks 'none' cipher and DUT does not advertise it"
         )

# -------- CASE 3: Server rejects NONE cipher --------
        if "no matching cipher" in output or "connection closed" in output:

         test_data["result"] = "PASS"
         test_data["remarks"] = (
        "DUT rejected None cipher negotiation (expected behavior)"
         )

# -------- CASE 4: Connection succeeds --------
        elif backend_result.returncode == 0:

         test_data["result"] = "FAIL"
         test_data["remarks"] = (
         "Connection succeeded using None cipher (critical vulnerability)"
        )

# -------- CASE 5: Default safe -------- 
        else:

         test_data["result"] = "PASS"
         test_data["remarks"] = (
         "None cipher not supported or usable"
        )

        # -------- SCREENSHOT --------

        screenshot_name = f"tc4_none_cipher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_name)

        pyautogui.screenshot(screenshot_path)

        test_data["screenshot"] = screenshot_path

        print(screenshot_path)

    finally:

        exit_terminal()

        print(test_data)
        return test_data