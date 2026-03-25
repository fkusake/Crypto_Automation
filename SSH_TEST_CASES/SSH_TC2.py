


import subprocess
import time
import pyautogui
import os
import re
from datetime import datetime

# ================= CONFIG =================
INTERFACE = os.getenv("INTERFACE")
DUT_IP = os.getenv("DUT_IP")
USER = os.getenv("DUT_USER")
DUT_PASSWORD = os.getenv("DUT_PASSWORD")

SCREENSHOT_DIR = "SCREENSHOTS"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

PCAP_DIR = "PCAP_FILES"
os.makedirs(PCAP_DIR, exist_ok=True)
# =========================================


# ---------------- DYNAMIC SSH ----------------

def detect_error_type(output):
    if "no matching host key type" in output:
        return "host_key"
    elif "no matching key exchange method" in output:
        return "kex"
    elif "no matching cipher" in output:
        return "cipher"
    elif "no matching MAC" in output:
        return "mac"
    return None


def extract_offered_algorithms(output):
    match = re.search(r"Their offer:\s*(.*)", output)
    if match:
        return [a.strip() for a in match.group(1).split(",")]
    return []


def build_dynamic_ssh_command(user, ip, output):

    error_type = detect_error_type(output)
    algos = extract_offered_algorithms(output)

    if not algos:
        return f"ssh {user}@{ip}"

    algo_str = ",".join(algos)

    cmd = "ssh "

    if error_type == "host_key":
        cmd += f"-o HostKeyAlgorithms=+{algo_str} "
        cmd += f"-o PubkeyAcceptedAlgorithms=+{algo_str} "

    elif error_type == "kex":
        cmd += f"-o KexAlgorithms=+{algo_str} "

    elif error_type == "cipher":
        cmd += f"-o Ciphers=+{algo_str} "

    elif error_type == "mac":
        cmd += f"-o MACs=+{algo_str} "

    return cmd + f"{user}@{ip}"


# ---------------- TERMINAL CONTROL ----------------

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


# ---------------- USER INPUT ----------------

def get_user_choice():

    print("\nChoose an option:")
    print("1) Enter SSH command manually")
    print("2) Use auto-generated command")

    choice = input("Enter choice (1/2): ").strip()

    if choice == "1":
        return input("Enter SSH command: ").strip()

    return None


# ---------------- DEMO SSH LOOP (UNCHANGED) ----------------

def run_visible_ssh_loop(user, ip):

    ssh_command = f"ssh {user}@{ip}"

    while True:

        output = ""

        # ✅ ONLY backend detection condition
        if ssh_command == f"ssh {user}@{ip}":
            try:
                import shlex

                cmd = ["sshpass", "-p", DUT_PASSWORD] + shlex.split(ssh_command)

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                output = (result.stdout + result.stderr)

            except subprocess.TimeoutExpired:
                output = ""

        # ✅ ALWAYS execute GUI SSH (important)
        subprocess.Popen([
            "gnome-terminal",
            "--title=SSH_CLIENT",
            "--"
        ])
        time.sleep(2)

        focus_window_by_title("SSH_CLIENT")
        maximize_terminal()

        pyautogui.typewrite(f"{ssh_command}\n", interval=0.05)
        time.sleep(3)

        pyautogui.typewrite(DUT_PASSWORD + "\n", interval=0.05)
        time.sleep(5)

        # ✅ SUCCESS conditions
        if ssh_command != f"ssh {user}@{ip}":
            print("✅ SSH Successful")
            pyautogui.typewrite("exit\n", interval=0.05)
            time.sleep(1)
            pyautogui.typewrite("exit\n", interval=0.05)
            time.sleep(1)
            return ssh_command, output

        if "Unable to negotiate" not in output:
            print("✅ SSH Successful")
            pyautogui.typewrite("exit\n", interval=0.05)
            time.sleep(1)
            pyautogui.typewrite("exit\n", interval=0.05)
            time.sleep(1)
            return ssh_command, output

        # ❌ FAIL
        print("❌ SSH Failed")

        pyautogui.typewrite("exit\n", interval=0.05)
        time.sleep(1)

        user_cmd = get_user_choice()

        if user_cmd:
            ssh_command = user_cmd
        else:
            ssh_command = build_dynamic_ssh_command(user, ip, output)

        print(f"Retrying with: {ssh_command}")


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

    time.sleep(8)


def focus_wireshark():
    subprocess.run(["wmctrl", "-xa", "wireshark"])
    time.sleep(1)


def apply_ssh_filter():
    pyautogui.hotkey("ctrl", "/")
    time.sleep(1)
    pyautogui.typewrite("ssh", interval=0.05)
    pyautogui.press("enter")
    time.sleep(2)


# ---------------- WIRESHARK NAVIGATION ----------------

def select_packet1():
    pyautogui.press("tab")
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "home")
    time.sleep(0.3)
    for _ in range(3):
        pyautogui.press("down")
        time.sleep(0.25)


def select_packet2():
    pyautogui.hotkey("shift", "tab")
    time.sleep(0.3)
    for _ in range(4):
        pyautogui.press("down")
        time.sleep(0.25)
    pyautogui.press("tab")
    time.sleep(0.4)
    for _ in range(5):
        pyautogui.press("down")
        time.sleep(0.2)


def expand_ssh_protocol():
    pyautogui.press("tab")
    time.sleep(0.4)
    for _ in range(6):
        pyautogui.press("down")
        time.sleep(0.2)
    pyautogui.press("right")
    time.sleep(0.4)


def expand_ssh_version_2():
    pyautogui.press("down")
    time.sleep(0.2)
    pyautogui.press("right")
    time.sleep(0.4)
    for _ in range(3):
        pyautogui.press("down")
        time.sleep(0.2)


# ---------------- CLI CAPTURE ----------------

def open_capture_terminal():

    subprocess.Popen([
        "gnome-terminal",
        "--title=SSH_CAPTURE",
        "--"
    ])
    time.sleep(2)

    focus_window_by_title("SSH_CAPTURE")
    maximize_terminal()

    pyautogui.typewrite(
        f'tshark -i {INTERFACE} '
        f'-f "tcp port 22" '
        f'-Y "ssh.message_code == 20" '
        f'-T fields '
        f'-e frame.number '
        f'-e _ws.col.Info '
        f'-e ssh.kex_algorithms\n',
        interval=0
    )

    time.sleep(4)


# ---------------- SCREENSHOT ----------------

def take_screenshot(label):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOT_DIR}/{ts}_{label}.png"
    pyautogui.screenshot(path)
    return path


# ---------------- PHASE 3: SSH CRYPTO EXTRACTION ----------------

def extract_ssh_crypto(ssh_command,password):

    cmd = ssh_command.split()

    # insert -vv after ssh
    cmd.insert(1, "-vv")
    cmd.append("exit")

    full_cmd = ["sshpass", "-p", password] + cmd

    result = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True
    )

    data = result.stderr

    def grab(pattern, default="Not Found"):
        m = re.search(pattern, data, re.MULTILINE)
        return m.group(1).strip() if m else default

    return {
        "protocol": grab(r"Remote protocol version ([0-9.]+)"),
        "cipher": grab(r"server->client cipher: ([^\s]+)"),
        "kex": grab(r"kex: algorithm: ([^\s]+)"),
        "host_key": grab(r"host key algorithm: ([^\s]+)")
    }

# ---------------- VALIDATION ----------------

def contains_weak(value, weak_list):
    if not value or value == "Not Found":
        return True
    v = value.lower()
    return any(w in v for w in weak_list)


WEAK_ENCRYPTION = ["des","3des","rc4","arcfour","blowfish","cast128","idea","null","none","export"]
WEAK_KEX = ["diffie-hellman-group1","diffie-hellman-group14-sha1","group-exchange-sha1"]
WEAK_HOST_KEY = ["ssh-dss","rsa1024","rsa512"]


def nist_validate(crypto):

    results = {}

    results["protocol"] = "PASS" if crypto.get("protocol") == "2.0" else "FAIL"
    results["encryption"] = "FAIL" if contains_weak(crypto.get("cipher"), WEAK_ENCRYPTION) else "PASS"
    results["kex"] = "FAIL" if contains_weak(crypto.get("kex"), WEAK_KEX) else "PASS"
    results["host_key"] = "FAIL" if contains_weak(crypto.get("host_key"), WEAK_HOST_KEY) else "PASS"

    final_result = "PASS" if all(v == "PASS" for v in results.values()) else "FAIL"

    return results, final_result


# ---------------- MAIN ----------------

def run_ssh_verification():

    ssh_test_data = {
        "test_case_id": "TC2_SSH_SECURE_COMMUNICATION",
        "user_input": "",
        "terminal_output": "",
        "crypto_details": {},
        "nist_validation": {},
        "final_result": "",
        "screenshots": [],
        "pcap_file": "",
        "basecommand":""
    }

    # -------- DEMO PHASE --------
    ssh_command, ssh_output = run_visible_ssh_loop(USER, DUT_IP)

    ssh_test_data["user_input"] = ssh_command
    ssh_test_data["basecommand"] = ssh_command
    ssh_test_data["terminal_output"] = ssh_output

    # -------- REAL CAPTURE PHASE --------
    launch_wireshark()
    focus_wireshark()
    apply_ssh_filter()

    open_capture_terminal()

    # ---- Run REAL SSH ----
    subprocess.Popen([
        "gnome-terminal",
        "--title=SSH_CLIENT",
        "--"
    ])
    time.sleep(2)

    focus_window_by_title("SSH_CLIENT")
    maximize_terminal()

    pyautogui.typewrite(f"{ssh_command}\n", interval=0.05)
    time.sleep(3)
    pyautogui.typewrite(DUT_PASSWORD + "\n", interval=0.05)

    # 🔥 IMPORTANT WAIT (capture packets)
    time.sleep(8)

    # Close SSH
    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(2)
    pyautogui.typewrite("exit\n", interval=0.05)
    time.sleep(2)

    # -------- CLI Screenshot --------
    focus_window_by_title("SSH_CAPTURE")
    ssh_test_data["screenshots"].append(
        take_screenshot("cli_packet_capture")
    )

    close_terminal()

    # -------- WIRESHARK NAVIGATION --------
    focus_wireshark()

    select_packet1()
    expand_ssh_protocol()
    expand_ssh_version_2()

    ssh_test_data["screenshots"].append(
        take_screenshot("ssh_key_exchange_version_2")
    )

    select_packet2()

    ssh_test_data["screenshots"].append(
        take_screenshot("ssh_encrypted_packet")
    )

     # ========= PHASE 3 =========
    crypto = extract_ssh_crypto(ssh_command,DUT_PASSWORD)
    validation, overall_result = nist_validate(crypto)

    ssh_test_data["crypto_details"] = crypto
    ssh_test_data["nist_validation"] = validation
    ssh_test_data["final_result"] = overall_result

    # -------- PCAP PROCESS --------
    SSH_ONLY_PCAP = os.path.join(
        PCAP_DIR,
        PCAP_FILE.replace("full_capture", "ssh_only_capture")
    )

    subprocess.run([
        "tshark",
        "-r", PCAP_FILE,
        "-Y", "ssh",
        "-w", SSH_ONLY_PCAP
    ])

    os.remove(PCAP_FILE)

    ssh_test_data["pcap_file"] = SSH_ONLY_PCAP

    subprocess.run(["pkill", "-f", "wireshark"])

    return ssh_test_data


if __name__ == "__main__":
    run_ssh_verification()