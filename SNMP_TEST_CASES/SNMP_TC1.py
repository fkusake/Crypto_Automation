import subprocess
import time
import pyautogui
import os
from datetime import datetime

DUT_IP = os.getenv("DUT_IP")

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

def run_snmp_backend(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=20
        )
        return result.stdout.strip()
    except Exception as e:
        return str(e)

# ---------------- VALIDATION ----------------

def check_snmp_success(output):
    return bool(output.strip())

# ---------------- MAIN FUNCTION ----------------

def run_snmp_tc1():

    snmp_test_data = {
        "test_case_id": "TC1_SNMP_VERSION_CHECK",

        "user_input_v1": "",
        "terminal_output_v1": "",
        "v1_screenshot": "",

        "user_input_v2c": "",
        "terminal_output_v2c": "",
        "v2c_screenshot": "",

        "validation_details": {
            "v1_success": False,
            "v2c_success": False
        },

        "final_result": ""
    }

    try:
        launch_terminal()
        focus_terminal()
        maximize_terminal()

        # ---------------- SNMPv1 ----------------

        cmd_v1 = f"snmpwalk -v1 -c public {DUT_IP} | grep -E 'STRING|INTEGER|OID|iso' | head -n 3"

        snmp_test_data["user_input_v1"] = cmd_v1

        run_visible_command(cmd_v1)

        time.sleep(5)

        v1_output = run_snmp_backend(cmd_v1)

        snmp_test_data["terminal_output_v1"] = (
            v1_output if v1_output else "No response (secure)"
        )

        # Screenshot
        v1_screenshot_name = f"snmp_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        v1_screenshot_path = os.path.join(SCREENSHOT_DIR, v1_screenshot_name)

        pyautogui.screenshot(v1_screenshot_path)
        snmp_test_data["v1_screenshot"] = v1_screenshot_path

        print(v1_screenshot_path)

        # Validation
        snmp_test_data["validation_details"]["v1_success"] = check_snmp_success(v1_output)

        # ---------------- CLEAR TERMINAL ----------------

        run_visible_command("clear")
        time.sleep(1)

        # ---------------- SNMPv2c ----------------

        cmd_v2 = f"snmpwalk -v2c -c public {DUT_IP} | grep -E 'STRING|INTEGER|OID|iso' | head -n 3"

        snmp_test_data["user_input_v2c"] = cmd_v2

        run_visible_command(cmd_v2)

        time.sleep(5)

        v2_output = run_snmp_backend(cmd_v2)

        snmp_test_data["terminal_output_v2c"] = (
            v2_output if v2_output else "No response (secure)"
        )

        # Screenshot
        v2_screenshot_name = f"snmp_v2c_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        v2_screenshot_path = os.path.join(SCREENSHOT_DIR, v2_screenshot_name)

        pyautogui.screenshot(v2_screenshot_path)
        snmp_test_data["v2c_screenshot"] = v2_screenshot_path

        print(v2_screenshot_path)

        # Validation
        snmp_test_data["validation_details"]["v2c_success"] = check_snmp_success(v2_output)

        # ---------------- FINAL RESULT ----------------

        v1_success = snmp_test_data["validation_details"]["v1_success"]
        v2_success = snmp_test_data["validation_details"]["v2c_success"]

        if v1_success or v2_success:
            snmp_test_data["final_result"] = "FAIL"
        else:
            snmp_test_data["final_result"] = "PASS"

    finally:
        exit_terminal()
        return snmp_test_data


