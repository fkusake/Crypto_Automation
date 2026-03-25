import subprocess
import time
import pyautogui
import os
from datetime import datetime

# ================= CONFIG =================
INTERFACE = os.getenv("INTERFACE")
DUT_IP = os.getenv("DUT_IP")

SCREENSHOT_DIR = "SCREENSHOTS"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# =========================================


# ---------------- TERMINAL CONTROL ----------------

def open_terminal(title):
    subprocess.Popen(["gnome-terminal", "--title", title])
    time.sleep(3)


def focus_window(title):
    subprocess.run(["wmctrl", "-xa", title])
    time.sleep(1)


def maximize():
    pyautogui.hotkey("alt", "f10")
    time.sleep(1)


def close_terminal():
    pyautogui.hotkey("ctrl", "c")
    time.sleep(1)
    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(1)


# ---------------- WIRESHARK ----------------

def launch_wireshark():
    subprocess.Popen([
        "wireshark",
        "-i", INTERFACE,
        "-k"
    ])
    time.sleep(8)


def focus_wireshark():
    subprocess.run(["wmctrl", "-xa", "wireshark"])
    time.sleep(1)


def apply_snmp_filter():
    pyautogui.hotkey("ctrl", "/")
    time.sleep(1)
    pyautogui.typewrite("snmp", interval=0.05)
    pyautogui.press("enter")
    time.sleep(2)


def close_wireshark():
    subprocess.run(["pkill", "-f", "wireshark"])
    time.sleep(2)


# ---------------- SCREENSHOT ----------------

def take_screenshot(label):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOT_DIR}/{ts}_{label}.png"
    pyautogui.screenshot(path)
    return path


# ---------------- BACKEND ----------------

def run_backend(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def check_success(output):
    return bool(output.strip())


# ---------------- WIRESHARK NAVIGATION ----------------

def select_snmp_packet():
    pyautogui.press("tab")
    time.sleep(0.3)

    pyautogui.hotkey("ctrl", "home")
    time.sleep(0.3)

    for _ in range(10):   # go to packet ~10
        pyautogui.press("down")
        time.sleep(0.2)

    pyautogui.press("tab")
    time.sleep(0.3)

    for _ in range(5):
        pyautogui.press("down")
        time.sleep(0.2)

    pyautogui.press("right")
    time.sleep(0.3)

    for _ in range(2):
        pyautogui.press("down")
        time.sleep(0.2)

    pyautogui.press("right")
    time.sleep(0.3)

    for _ in range(3):
        pyautogui.press("down")
        time.sleep(0.2)
        
    pyautogui.press("right")
    time.sleep(0.3)


# ---------------- SINGLE PHASE ----------------

def run_snmp_phase(mode):

    data = {
        "command": "",
        "output": "",
        "terminal_screenshot": "",
        "wireshark_screenshot": "",
        "success": False
    }

    # Launch Wireshark
    launch_wireshark()
    focus_wireshark()
    apply_snmp_filter()

    # Open terminal
    open_terminal("SNMP_TEST")
    focus_window("SNMP_TEST")
    maximize()

    # Commands
    if mode == "authPriv":
        cmd = f"snmpwalk -v3 -u snmpuser -l authPriv -a SHA -A AuthPass123 -x AES -X PrivPass123 {DUT_IP} | head -n 3"
    elif mode == "authNoPriv":
        cmd = f"snmpwalk -v3 -u snmpuser -l authNoPriv -a SHA -A AuthPass123 {DUT_IP} | head -n 3"
    else:
        cmd = f"snmpwalk -v3 -u snmpuser -l noAuthNoPriv {DUT_IP} | head -n 3"

    data["command"] = cmd

    # Run visible
    pyautogui.typewrite(cmd + "\n", interval=0.03)
    time.sleep(5)

    # Backend capture
    output = run_backend(cmd)
    data["output"] = output if output else "No response"
    data["success"] = check_success(output)

    # Terminal screenshot
    data["terminal_screenshot"] = take_screenshot(f"{mode}_terminal")

    # Close terminal
    close_terminal()

    # Wireshark validation
    focus_wireshark()
    select_snmp_packet()

    data["wireshark_screenshot"] = take_screenshot(f"{mode}_wireshark")

    # Close Wireshark
    close_wireshark()

    return data


# ---------------- MAIN FUNCTION ----------------

def run_snmp_tc2():

    result = {
        "test_case_id": "TC2_SNMP_SECURE_COMMUNICATION",

        "authPriv": {},
        "authNoPriv": {},
        "noAuthNoPriv": {},

        "final_result": ""
    }

    # Run phases
    result["authPriv"] = run_snmp_phase("authPriv")
    result["authNoPriv"] = run_snmp_phase("authNoPriv")
    result["noAuthNoPriv"] = run_snmp_phase("noAuthNoPriv")

    # Validation logic
    authPriv_ok = result["authPriv"]["success"]
    authNoPriv_ok = result["authNoPriv"]["success"]
    noAuth_ok = result["noAuthNoPriv"]["success"]

    if not authPriv_ok:
        result["final_result"] = "FAIL"

    elif authNoPriv_ok or noAuth_ok:
        result["final_result"] = "FAIL"

    else:
        result["final_result"] = "PASS"

    return result
