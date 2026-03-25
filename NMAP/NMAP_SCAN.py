
        
import subprocess
import time
import pyautogui
import shutil
from datetime import datetime
import os

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

def run_nmap_tcp_backend():

    if not shutil.which("nmap"):
        return None

    result = subprocess.run(
        [
            "nmap",
            "-p22,80,443",
            "-Pn",
            "-n",
            "--open",
            DUT_IP
        ],
        capture_output=True,
        text=True
    )

    return result.stdout


def run_nmap_udp_backend():

    if not shutil.which("nmap"):
        return None

    result = subprocess.run(
        [
            "sudo",
            "nmap",
            "-sU",
            "-p161",
            "-Pn",
            "-n",
            DUT_IP
        ],
        capture_output=True,
        text=True
    )

    return result.stdout


# ---------------- MAIN FUNCTION ----------------

def run_nmap_scan():

    scan_data = {
        "test_case_id": "TC_DUT_CONFIGURATION_NMAP_SCAN",

        "user_input_tcp_ports": f"nmap -p22,80,443 -Pn -n --open {DUT_IP}",
        "terminal_output_tcp_ports": "",

        "user_input_udp_ports": f"sudo nmap -sU -p161 -Pn -n {DUT_IP}",
        "terminal_output_udp_ports": "",

        "tcp_screenshot": "",
        "udp_screenshot": "",

        "SSH": False,
        "HTTP": False,
        "HTTPS": False,
        "SNMP": False
    }

    try:

        launch_terminal()
        focus_terminal()
        maximize_terminal()

        # ---------------- TCP SCAN ----------------

        run_visible_command(scan_data["user_input_tcp_ports"])

        time.sleep(3)

        tcp_output = run_nmap_tcp_backend()

        scan_data["terminal_output_tcp_ports"] = (
            tcp_output if tcp_output else "No output captured"
        )

        if tcp_output:

            out = tcp_output.lower()

            if "22/tcp" in out and "open" in out and "ssh" in out:
                scan_data["SSH"] = True

            if "80/tcp" in out and "open" in out and "http" in out:
                scan_data["HTTP"] = True

            if "443/tcp" in out and "open" in out and "https" in out:
                scan_data["HTTPS"] = True

        # -------- TCP Screenshot --------

        tcp_screenshot_name = f"nmap_tcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        tcp_screenshot_path = os.path.join(SCREENSHOT_DIR, tcp_screenshot_name)

        pyautogui.screenshot(tcp_screenshot_path)

        scan_data["tcp_screenshot"] = tcp_screenshot_path

        print(tcp_screenshot_path)

        # -------- CLEAR TERMINAL --------

        run_visible_command("clear")

        time.sleep(1)

        # ---------------- UDP SCAN (SNMP) ----------------

        run_visible_command(scan_data["user_input_udp_ports"])

        time.sleep(5)

        udp_output = run_nmap_udp_backend()

        scan_data["terminal_output_udp_ports"] = (
            udp_output if udp_output else "No output captured"
        )

        if udp_output:

            out = udp_output.lower()

            if "161/udp" in out and "open" in out and "snmp" in out:
                scan_data["SNMP"] = True

        # -------- UDP Screenshot --------

        udp_screenshot_name = f"nmap_udp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        udp_screenshot_path = os.path.join(SCREENSHOT_DIR, udp_screenshot_name)

        pyautogui.screenshot(udp_screenshot_path)

        scan_data["udp_screenshot"] = udp_screenshot_path

        print(udp_screenshot_path)

    finally:

        exit_terminal()

        return scan_data