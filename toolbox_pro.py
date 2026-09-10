#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import string
from webbrain import WebBrain  # auto-added
from aibrain import AIBrain  # auto-added v4
from cortex import Cortex  # auto-added v5

def _looks_question(t):
    """v5.1 aggressive web trigger: does this message look like a real question?"""
    tl = (t or "").strip().lower()
    if not tl or tl.startswith("/"):
        return False
    if tl.endswith("?") or "\u061f" in tl:
        return True
    return bool(re.search(r"\b(what|who|why|how|when|where|which|explain|tell me|meaning|definition|best|difference|compare|tutorial|guide)\b", tl))

import os, sys, re, json, math, time, socket, subprocess, threading, shutil
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
except ImportError:
    print("tkinter not found"); sys.exit(1)

if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":0"
_SUDO_U = os.environ.get("SUDO_USER")
if _SUDO_U and not os.environ.get("XAUTHORITY"):
    os.environ["XAUTHORITY"] = "/home/%s/.Xauthority" % _SUDO_U
LOG_FILE = os.path.expanduser("~/.toolbox_pro.log")

THEMES = {
"dark":   {"bg":"#0a0e1a","bg2":"#0d1322","card":"#131a2e","border":"#232c4a","text":"#e8ecff","dim":"#8a93b5","accent":"#7aa2f7","accent2":"#b388ff","moon":"#ffe9a0","green":"#7ee2a8","red":"#ff6b81"},
"light":  {"bg":"#f2f4fb","bg2":"#ffffff","card":"#e8ebf7","border":"#c9cfe6","text":"#1a2033","dim":"#5a6280","accent":"#3b6fd4","accent2":"#7c4dcc","moon":"#b8860b","green":"#1d8a4e","red":"#c2334d"},
"calm":   {"bg":"#0e1a16","bg2":"#12211c","card":"#16281f","border":"#274434","text":"#dff2e6","dim":"#7fa392","accent":"#6fd3a5","accent2":"#a5d6b8","moon":"#e8f5c8","green":"#7ee2a8","red":"#ff8f8f"},
"deep":   {"bg":"#05070f","bg2":"#080b16","card":"#0c1120","border":"#1a2340","text":"#d5dcf5","dim":"#6b7495","accent":"#5b8cff","accent2":"#8f7bd8","moon":"#cfd8ff","green":"#5fd39a","red":"#e05c74"},
"vampire":{"bg":"#140608","bg2":"#1a080b","card":"#220a0f","border":"#3d1420","text":"#ffdfe3","dim":"#a06a72","accent":"#ff4d6d","accent2":"#c9184a","moon":"#ffb3c1","green":"#7ee2a8","red":"#ff2e4d"},
"forest": {"bg":"#06120a","bg2":"#081a0e","card":"#0c2413","border":"#1a3d22","text":"#d8f5dd","dim":"#6fa07a","accent":"#52d67a","accent2":"#a3e635","moon":"#f0ffd8","green":"#7ee2a8","red":"#ff6b81"},
"ocean":  {"bg":"#04121e","bg2":"#061a2a","card":"#0a2336","border":"#143a52","text":"#d9f0ff","dim":"#6f93ab","accent":"#38bdf8","accent2":"#22d3ee","moon":"#a5f3fc","green":"#7ee2a8","red":"#ff6b81"},
"golden": {"bg":"#171004","bg2":"#1f1606","card":"#291d08","border":"#4a3610","text":"#ffefc9","dim":"#a8925f","accent":"#f5b942","accent2":"#ffd166","moon":"#fff3b0","green":"#7ee2a8","red":"#ff6b81"},
"icy":    {"bg":"#0a1620","bg2":"#0d1d2a","card":"#122836","border":"#234a5e","text":"#e0f7ff","dim":"#7ba3b5","accent":"#7dd3fc","accent2":"#e0f2fe","moon":"#ffffff","green":"#7ee2a8","red":"#ff6b81"},
"purple": {"bg":"#12061f","bg2":"#170828","card":"#1f0b33","border":"#37165c","text":"#f0e3ff","dim":"#9a7bb5","accent":"#c084fc","accent2":"#e879f9","moon":"#f5d0fe","green":"#7ee2a8","red":"#ff6b81"}}
THEME_EN = {"dark":"Dark","light":"Light","calm":"Calm","deep":"Deep","vampire":"Vampire","forest":"Night Forest","ocean":"Ocean","golden":"Golden","icy":"Icy","purple":"Purple Night"}

SETTINGS_FILE = os.path.expanduser("~/.toolbox_pro_settings.json")

def log(msg, level="INFO"):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("[%s] [%s] %s\n" % (datetime.now().strftime('%H:%M:%S'), level, msg))
    except Exception:
        pass

def run_cmd(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -2, str(e)


def get_iface():
    base = "/sys/class/net"
    fallback = None
    if os.path.isdir(base):
        for d in os.listdir(base):
            if d == "lo":
                continue
            if os.path.isdir(os.path.join(base, d, "wireless")):
                return d
            if fallback is None:
                fallback = d
    return fallback

def get_subnet_info():
    iface = get_iface()
    if not iface:
        return None, None, None
    _, out = run_cmd(["ip", "-4", "addr", "show", iface], 10)
    m = re.search(r"inet\s+([\d./]+)", out)
    m2 = re.search(r"inet\s+([\d.]+)", out)
    _, route = run_cmd(["ip", "route"], 10)
    m3 = re.search(r"default\s+via\s+([\d.]+)", route)
    return (m.group(1) if m else None, m2.group(1) if m2 else None, m3.group(1) if m3 else None)

def _digits_en(s):
    fa_d = "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9"
    ar_d = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
    en_d = "0123456789"
    r = str(s)
    for i in range(10):
        r = r.replace(fa_d[i], en_d[i]).replace(ar_d[i], en_d[i])
    return r


class AsyncCommandRunner:
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, tag="default"):
        self.tag = tag
        self.process = None
        self.stop_flag = False
        self.running = False

    @classmethod
    def get(cls, tag="default"):
        with cls._lock:
            if tag not in cls._instances:
                cls._instances[tag] = cls(tag)
            return cls._instances[tag]

    def run(self, cmd, output_callback, timeout=0):
        if self.running:
            return False
        self.stop_flag = False
        self.running = True

        def worker():
            try:
                import select
                m_fd, s_fd = __import__('pty').openpty()
                args = ["bash", "-c", cmd] if isinstance(cmd, str) else cmd
                self.process = subprocess.Popen(
                    args, stdout=s_fd, stderr=s_fd, stdin=s_fd,
                    start_new_session=True)
                try:
                    os.close(s_fd)
                except Exception:
                    pass
                if timeout > 0:
                    def tk():
                        time.sleep(timeout)
                        if not self.stop_flag and self.process and self.process.poll() is None:
                            self.stop()
                    threading.Thread(target=tk, daemon=True).start()
                last_line = None
                dup = 0
                while True:
                    if self.stop_flag:
                        self._kill()
                        break
                    try:
                        r, _, _ = select.select([m_fd], [], [], 0.2)
                    except Exception:
                        break
                    if not r:
                        if self.process and self.process.poll() is not None:
                            break
                        continue
                    try:
                        data = os.read(m_fd, 4096)
                    except OSError:
                        break
                    if not data:
                        break
                    text = data.decode('utf-8', 'replace')
                    text = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)
                    text = re.sub(r'\x1b[()][0-9A-Za-z]', '', text)
                    text = text.replace('\r', '\n')
                    for line in text.split('\n'):
                        s = line.strip()
                        if not s:
                            continue
                        if s == last_line:
                            dup += 1
                            if dup > 3:
                                continue
                        else:
                            last_line = s
                            dup = 0
                        output_callback(s)
                try:
                    os.close(m_fd)
                except Exception:
                    pass
                if self.process:
                    self.process.wait()
                    rc = self.process.returncode
                    msg = "\n[Exit code: %d]" % rc
                    if self.stop_flag:
                        msg += " (stopped)"
                    output_callback(msg)
            except Exception as e:
                output_callback("Error: %s" % e)
            finally:
                self.running = False
                self.process = None

        threading.Thread(target=worker, daemon=True).start()
        return True

    def stop(self):
        self.stop_flag = True
        self._kill()

    def _kill(self):
        if self.process is not None:
            try:
                os.killpg(os.getpgid(self.process.pid), 15)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

TTH = {
    "bg": "#0a0e1a",
    "bg2": "#0f1626",
    "card": "#141d30",
    "border": "#1e2d45",
    "text": "#c8d6e5",
    "dim": "#5a6b82",
    "moon": "#ffe9a0",
    "accent": "#64b5f6",
    "accent2": "#b388ff",
    "green": "#81c784",
    "red": "#e57373",
    "font": ("Segoe UI", 12),
    "font_b": ("Segoe UI", 13, "bold"),
    "font_h": ("Segoe UI", 20, "bold"),
    "font_s": ("Segoe UI", 10)}
TH = TTH

_CTTH = {

"en": {
"desc_ipgeox": "IP & domain geolocation info",
"desc_phone": "SIM operator & province lookup",
"desc_passcheck": "Password strength analysis",
"desc_passforge": "Secure random password generator",
"desc_wordlist": "Custom wordlist builder",
"desc_hostscan": "Find network devices (3 methods)",
"desc_nmap": "Port scan & service detection",
"desc_sysmon": "Live CPU/RAM/network monitor",
"desc_settings": "Appearance, sound, performance & privacy",
"desc_forge": "Build your own custom tool",
"back": "Back", "run": "Run", "stop": "Stop",
"save": "Save", "search": "Search", "history": "History",
"local_ip": "My Local IP", "public_ip": "My Public IP",
"net_phones": "Network Devices",
"appearance": "Appearance & Theme",
"sound": "Sound",
"performance": "Performance & Network",
"data": "Data & Backup",
"about": "About",
"language": "Language",
"apply_lang": "Apply & Restart",
"new_tool": "New Tool", "manage": "Manage",
"edit": "Edit", "delete": "Delete",
"cancel": "Cancel", "confirm": "Confirm",
"add_step": "Step", "add_var": "Variable",
"build": "Build",
"b_info": "Info", "b_sec": "Security",
"b_net": "Network", "b_sys": "System",
"my_tools": "My Custom Tools",
"no_tools": "No tools yet."}}

_DESC = {

"en": {
"desc_ipgeox": "Locate IP or website",
"desc_phone": "Number analysis",
"desc_passcheck": "Password strength, 8 criteria",
"desc_passforge": "Generate strong passwords",
"desc_wordlist": "Generate wordlists",
"desc_hostscan": "Discover network devices",
"desc_nmap": "Port and service scan",
"desc_sysmon": "Live system info",
"desc_settings": "Advanced app settings",
"desc_forge": "Personal tool workshop"}}

I18N = {}
for _lg, _d in _CTTH.items():
    for _k, _v in _d.items():
        I18N.setdefault(_k, {})[_lg] = _v

for _lg, _d in _DESC.items():
    for _k, _v in _d.items():
        I18N.setdefault(_k, {})[_lg] = _v

I18N.setdefault("desc_webtools", { "en": "Web security headers"})
I18N.setdefault("desc_packx", { "en": "Package installer"})
I18N.setdefault("desc_helpbook", { "en": "Tools guide book"})
I18N.setdefault("desc_wifi", { "en": "WiFi security testing"})
I18N.setdefault("desc_webpentest", { "en": "Web pentest"})
I18N.setdefault("desc_brute", { "en": "Hash cracking"})
I18N.setdefault("desc_osint", { "en": "Username/domain OSINT"})
I18N.setdefault("desc_exploit", { "en": "CVE & exploit finder"})

EEEXTRA_TR = {
"Good night": "Good night",
"Good morning": "Good morning",
"Good afternoon": "Good afternoon",
"Saved (theme/font needs restart)": "Saved (theme/font needs restart)",
"Search history cleared": "Search history cleared",
"Exported": "Exported",
"Restored, restarting...": "Restored, restarting...",
"Reset done, restarting...": "Reset done, restarting...",
"Private IP, Local analysis": "Private IP, Local analysis",
"This is a local network IP, not geolocatable": "This is a local network IP, not geolocatable",
"Status: online": "Status: online",
"Status: offline": "Status: offline",
"Uptime:": "Uptime:",
"Total disk:": "Total disk:",
"Used:": "Used:",
"Free:": "Free:",
"Internal execution error": "Internal execution error",


"Very strong": "Very strong",
"Strong": "Strong",
"Medium": "Medium",
"Weak": "Weak",


"Security Headers Analysis": "Security Headers Analysis",
"No steps saved": "No steps saved",
"Stopped": "Stopped",
"All steps completed": "All steps completed"}



TOOL_HELP = {
"dashboard": {
  "en": "Home screen. Click a tool card to open it; '< Back' returns here; the help button at the bottom of each page opens its full guide."},
  "ipgeox": {
  "en": "Enter an IP or domain to see geolocation, ISP and owner info. Accuracy is city-level."},
  "phoneinfo": {
  "en": "Detects Iranian mobile operator and province from the number prefix."},
  "passcheck": {
  "en": "Scores password strength locally against security criteria; nothing is sent anywhere."},
  "passforge": {
  "en": "Generates strong random passwords with chosen length and charset."},
  "wordlist": {
  "en": "Builds custom wordlists (base words + prefixes/suffixes + number ranges) for password testing."},
  "hostscan": {
  "en": "Discovers devices on your LAN via arp-scan / nmap / ping sweep."},
  "nmapx": {
  "en": "Scans open ports and services of a target. Only on networks you own or have permission for."},
  "sysmon": {
  "en": "Live CPU/RAM/network monitor with top processes."},
  "packx": {
  "en": "Automatically installs packages by detecting the system package manager (apt/pacman/dnf/apk). Just enter a tool name and press Install."},
  "wifiattack": {
  "en": "Full Wi-Fi audit flow: monitor mode, AP scan, client scan, targeted or broadcast deauth, stop. Only on your own network."},
  "webpentest": {
  "en": "Basic web security checks: headers, TLS, tech, common paths. Only on your own sites."},
  "bruteforce": {
  "en": "Password testing with a wordlist against SSH/FTP/web forms. Only with permission."},
  "osint": {
  "en": "Advanced OSINT: username (28 platforms + GitHub), domain (DNS/WHOIS/SSL/subs/reverse-IP), IP (geo/ISP/ports), email (Gravatar/MX/disposable). Public sources only."},
  "exploitfinder": {
  "en": "Finds published CVEs/exploits for a service version. Awareness only."},
  "webtools": {
  "en": "Small quick web utilities (headers, DNS, ping...)."},
  "custom": {
  "en": "Turn any shell command into a tool card; {target} is replaced by your input."},
  "custom_edit": {
  "en": "Edit or delete your custom tools."},
  "settings": {
  "en": "Language, theme, sound, performance and privacy settings."},
  "hashid": {
  "en": "Detects hash type and cracks via best available tool (hashcat, john, built-in engine) with rockyou."},
  "exif": {
  "en": "Shows and scrubs file metadata (camera, GPS...). Install exiftool for full support."},
  "subfind": {
  "en": "Discovers subdomains via an editable wordlist, live results with IPs, wildcard detection. Fully local."},
  "ncat": {
  "en": "Simple GUI for nc/ncat: connect or listen, live send/receive. Install ncat via Packages card if needed."}}

TOOL_HELP["airgeddon"] = { "en": "GUI front-end for the real airgeddon; live menus answered via the input box; external terminal button for fullscreen. Only on your own network or with permission."}


GB_KB = [
{"id":"wifiattack","n":"WiFi Security Testing","p":"wifiattack","cat":"Network","risk":"dangerous","icon":"\U0001f4e1",
 "k":["wifi","wireless","wlan","monitor","deauth","airodump","aireplay","handshake","bssid","router","\u0648\u0627\u06cc\u0641\u0627\u06cc","\u0648\u0627\u06cc \u0641\u0627\u06cc","\u0645\u0648\u062f\u0645","\u0631\u0648\u062a\u0631","\u0642\u0637\u0639","disconnect","kick","drop"],
 "al":["wifi password","monitor mode","handshake capture","my wifi password","hack my own wifi"],
 "qs":["how do i test my own wifi","which tool attacks wifi","how do i test my own wifi password","which tool can disconnect a wifi","how do i disconnect a wifi","which tool kicks clients off wifi"],
 "d":"Full Wi-Fi audit: monitor mode, AP scan, client scan, deauth test, stop.",
 "s":["Set interface (wlan0) and press Monitor ON (root + aircrack-ng needed)","Scan APs (15s) and pick your BSSID; channel fills automatically","Optional: Scan clients (20s), put a client MAC in CLIENT","Deauth test on YOUR network to force handshake traffic","Stop anytime; take the capture to Hash ID with a wordlist"],
 "r":"root/sudo, aircrack-ng, monitor-mode Wi-Fi adapter","rel":["airgeddon","wordlist","hashid"],"aw":1},
{"id":"airgeddon","n":"Airgeddon","p":"airgeddon","cat":"Network","risk":"dangerous","icon":"\U0001f4e1",
 "k":["airgeddon","evil","twin","pmkid","wps"],
 "al":["airgeddon menu","evil twin"],"qs":["how do i run airgeddon"],
 "d":"Front-end for the airgeddon suite: handshake, PMKID, evil twin, WPS flows in guided menus.",
 "s":["Press Install if not installed","Start - an external terminal opens","Follow its numbered menus in that terminal"],
 "r":"root, airgeddon, compatible adapter","rel":["wifiattack"],"aw":1},
{"id":"nmapx","n":"Nmap Port Scanner","p":"nmap","cat":"Network","risk":"sensitive","icon":"\U0001f6f0",
 "k":["nmap","port","ports","service","stealth","\u067e\u0648\u0631\u062a","\u0627\u0633\u06a9\u0646"],
 "al":["port scan","open ports","scan ports"],"qs":["which tool scans ports","how do i scan open ports"],
 "d":"Scans open ports/services with 5 profiles: Fast, Aggressive, Vulnerability, All ports, Stealth SYN.",
 "s":["Enter target IP or domain","Choose a scan mode","Run; Stop cancels; extra args in Settings"],
 "r":"nmap (Packages card)","rel":["hostscan","webpentest","exploitfinder"]},
{"id":"hostscan","n":"Host Scanner","p":"hostscan","cat":"Network","risk":"safe","icon":"\U0001f5a5",
 "k":["lan","arp","ping","devices","network","\u0634\u0628\u06a9\u0647","\u062f\u0633\u062a\u06af\u0627\u0647"],
 "al":["who is on my network","find devices"],"qs":["how do i see devices on my lan"],
 "d":"Discovers live LAN devices via ARP + ping sweep + nmap with names and MACs.",
 "s":["Press Unified Host Scan","Read IP / name / MAC table"],"rel":["nmapx","ipgeox"]},
{"id":"webpentest","n":"Web Pentest","p":"webpentest","cat":"Web","risk":"sensitive","icon":"\U0001f578",
 "k":["web","site","website","pentest","tls","certificate","\u0633\u0627\u06cc\u062a","\u0648\u0628"],
 "al":["test my website","web security check"],"qs":["how do i pentest my own site"],
 "d":"Non-destructive web checks: DNS, common ports, TLS cert, admin/robots paths.",
 "s":["Enter your own site URL","Press Run and review the report"],"rel":["webtools","subfind"]},
{"id":"webtools","n":"Web Tools","p":"webtools","cat":"Web","risk":"safe","icon":"\U0001f310",
 "k":["headers","cms","robots","technology","wordpress"],
 "al":["security headers","cms detect"],"qs":["how do i see http headers"],
 "d":"Quick web utilities: headers, server tech, CMS detection, robots.txt.",
 "s":["Enter URL","Run or robots button"],"rel":["webpentest"]},
{"id":"hashid","n":"Hash Identifier & Cracker","p":"hashid","cat":"Security","risk":"dangerous","icon":"\U0001f9ec",
 "k":["hash","md5","sha1","sha256","sha512","ntlm","bcrypt","hashcat","john","\u0647\u0634","\u06a9\u0631\u06a9"],
 "al":["crack hash","identify hash","what hash is this"],"qs":["how do i crack a hash","which tool uses hashcat"],
 "d":"Detects hash type then cracks via hashcat / john / built-in engine with rockyou.",
 "s":["Paste the hash","Press Analyze & Crack","Auto-detects type, tries common words, then rockyou via hashcat/john/built-in"],
 "r":"optional hashcat or john; rockyou auto-handled","rel":["wordlist","bruteforce"],"aw":1},
{"id":"bruteforce","n":"Brute Force / Offline Crack","p":"bruteforce","cat":"Security","risk":"dangerous","icon":"\U0001f513",
 "k":["brute","bruteforce","dictionary","offline","\u062d\u0645\u0644\u0647"],
 "al":["brute force","dictionary attack"],"qs":["how do i brute force a hash"],
 "d":"Offline wordlist / digit-range cracking against md5/sha1/sha256/sha512.",
 "s":["Paste hash, choose type","Give a wordlist file (empty = digits 0000-9999)","Run / Stop"],
 "rel":["hashid","wordlist"],"aw":1},
{"id":"wordlist","n":"Wordlist Builder","p":"wordlist","cat":"Security","risk":"safe","icon":"\U0001f4dd",
 "k":["wordlist","dictionary","prefix","suffix","\u0644\u06cc\u0633\u062a","\u06a9\u0644\u0645\u0627\u062a"],
 "al":["build wordlist","make dictionary"],"qs":["how do i build a wordlist"],
 "d":"Builds custom wordlists: base words + prefixes/suffixes + digit ranges, exportable.",
 "s":["Fill base words / prefixes / suffixes / digit range","Generate to preview","Save to file; feed it to Hash ID or Brute Force"],
 "rel":["hashid","bruteforce"]},
{"id":"passforge","n":"Password Forge","p":"passforge","cat":"Security","risk":"safe","icon":"\U0001f6e1",
 "k":["generate","password","passphrase","random","\u0631\u0645\u0632","\u067e\u0633\u0648\u0631\u062f"],
 "al":["generate password","strong password"],"qs":["how do i generate a strong password"],
 "d":"Generates secure random passwords or passphrases with entropy rating.",
 "s":["Set length/count and charsets or Phrase mode","Generate; Copy Last copies newest"],"rel":["passcheck"]},
{"id":"passcheck","n":"Pass Check","p":"passcheck","cat":"Security","risk":"safe","icon":"\U0001f511",
 "k":["strength","entropy","check","\u0642\u062f\u0631\u062a"],
 "al":["password strength","is my password strong"],"qs":["how do i check password strength"],
 "d":"Scores a password locally: length, entropy, GPU crack-time estimate. Nothing leaves your machine.",
 "s":["Type the password","Press Check"],"rel":["passforge"]},
{"id":"osint","n":"Advanced OSINT","p":"osint","cat":"Info","risk":"sensitive","icon":"\U0001f575",
 "k":["osint","username","domain","email","gravatar","sherlock","\u06a9\u0627\u0631\u0628\u0631","\u0627\u06cc\u0645\u06cc\u0644","\u062f\u0627\u0645\u0646\u0647"],
 "al":["username hunt","domain osint","email osint"],"qs":["how do i investigate a username","which tool does osint on a domain"],
 "d":"OSINT suite: username (21+ platforms), domain (DNS/WHOIS/SSL/CT subs), IP (geo/RDAP/ports), email (Gravatar/MX).",
 "s":["Enter target (username / domain / IP / email)","Press the matching mode button","Watch verified live results; Stop cancels"],
 "rel":["subfind","ipgeox"]},
{"id":"subfind","n":"Subdomain Finder","p":"subfind","cat":"Network","risk":"safe","icon":"\U0001f310",
 "k":["subdomain","sub","dns","\u0632\u06cc\u0631\u062f\u0627\u0645\u0646\u0647"],
 "al":["find subdomains"],"qs":["how do i find subdomains"],
 "d":"Finds subdomains via an editable wordlist with wildcard detection, fully local DNS.",
 "s":["Enter the domain","Edit wordlist if needed","Start / Stop"],"rel":["osint","webpentest"]},
{"id":"exploitfinder","n":"Exploit Finder","p":"exploitfinder","cat":"Security","risk":"sensitive","icon":"\U0001f4a3",
 "k":["exploit","cve","vulnerability","nvd","\u0622\u0633\u06cc\u0628"],
 "al":["search cve","find exploit"],"qs":["how do i find cves for a service"],
 "d":"Searches the official NVD database for CVEs by keyword (product/version).",
 "s":["Type product + version","Press Search; review CVE list + Exploit-DB link"],
 "rel":["nmapx","webpentest"]},
{"id":"ipgeox","n":"IP Geolocation","p":"ipgeox","cat":"Info","risk":"safe","icon":"\U0001f30d",
 "k":["ip","geo","location","country","isp","map","\u0622\u06cc \u067e\u06cc","\u0645\u0648\u0642\u0639\u06cc\u062a"],
 "al":["where is this ip","ip location"],"qs":["how do i find the location of an ip"],
 "d":"Geolocates IP/domain: country, city, ISP, org, coords + map; private IPs analyzed locally.",
 "s":["Type IP/domain or use My Local / My Public IP","Search; Open Map opens the browser"],"rel":["osint","hostscan"]},
{"id":"phoneinfo","n":"Phone Info","p":"phoneinfo","cat":"Info","risk":"safe","icon":"\U0001f4f1",
 "k":["phone","mobile","operator","sim","\u0634\u0645\u0627\u0631\u0647","\u0645\u0648\u0628\u0627\u06cc\u0644","\u0627\u067e\u0631\u0627\u062a\u0648\u0631"],
 "al":["sim operator"],"qs":["which tool checks a phone number"],
 "d":"Analyzes Iranian mobile numbers: operator, SIM generation, issue years, prepaid/postpaid.",
 "s":["Enter number like 09123456789","Press Analyze"],"rel":["osint"]},
{"id":"exif","n":"Metadata Inspector","p":"exif","cat":"Info","risk":"safe","icon":"\U0001f4f7",
 "k":["exif","metadata","gps","photo","image","\u0645\u062a\u0627\u062f\u0627\u062a\u0627","\u0639\u06a9\u0633"],
 "al":["photo metadata","gps in photo"],"qs":["how do i remove gps from a photo"],
 "d":"Shows and scrubs file metadata (device, GPS, dates); backup kept as *_original.",
 "s":["Browse or type a file path","Show to inspect; Scrub to remove metadata"],
 "r":"exiftool for full support (Packages card)","rel":[]},
{"id":"ncat","n":"Netcat Interface","p":"ncat","cat":"Network","risk":"sensitive","icon":"\U0001f50c",
 "k":["netcat","ncat","nc","listen","connect","shell","socket"],
 "al":["netcat listen","reverse shell gui"],"qs":["how do i use netcat"],
 "d":"GUI for nc/ncat: connect or listen on a port with live send/receive.",
 "s":["Choose Connect or Listen; set host and port","Start; type and Send; Stop closes"],
 "r":"nc or ncat (Packages card)","rel":[]},
{"id":"packx","n":"Package Installer","p":"packx","cat":"System","risk":"safe","icon":"\U0001f4e6",
 "k":["install","package","apt","pacman","dnf","apk","\u0646\u0635\u0628","\u067e\u06a9\u06cc\u062c"],
 "al":["install tool","missing command"],"qs":["how do i install nmap","a command is missing what do i do"],
 "d":"Auto-detects package manager (apt/pacman/dnf/apk) and installs; sudo via opened terminal.",
 "s":["Type package names space-separated","Press Install; enter sudo password if asked"],"rel":[]},
{"id":"sysmon","n":"System Monitor","p":"sysmon","cat":"System","risk":"safe","icon":"\U0001f4ca",
 "k":["cpu","ram","memory","disk","uptime","system","\u0633\u06cc\u0633\u062a\u0645"],
 "al":["cpu usage","monitor system"],"qs":["how do i see cpu and ram"],
 "d":"Live CPU load, RAM, disk, uptime, IP/gateway; optional 5s auto-refresh.",
 "s":["Press Refresh or enable Auto (5s)"],"rel":["hostscan"]},
{"id":"settings","n":"Settings","p":"settings","cat":"System","risk":"safe","icon":"\u2699",
 "k":["settings","theme","opacity","proxy","privacy","font","title","\u062a\u0646\u0638\u06cc\u0645\u0627\u062a","\u062a\u0645"],
 "al":["change theme","dark mode"],"qs":["how do i change the theme","where is proxy setting"],
 "d":"10 themes, font size, opacity, title, always-on-top, private mode, sound, proxy, nmap args - live apply.",
 "s":["Change what you want","Press Save Changes - applies instantly"],"rel":[]},
{"id":"forge","n":"Forge (Custom Tools)","p":"forge","cat":"System","risk":"safe","icon":"\U0001f527",
 "k":["forge","custom","build","own","\u0627\u0628\u0632\u0627\u0631","\u0634\u062e\u0635\u06cc"],
 "al":["make my own tool","custom tool"],"qs":["how do i create my own tool","what is forge"],
 "d":"Turns shell commands into reusable tool cards with ${variables}, steps, timeouts, sudo.",
 "s":["+ New Tool and name it","Define variables name=value","Add steps using ${var}","Save; Run from Forge list; use Guide / Insert / Check buttons"],
 "rel":["packx"]},
{"id":"guidebot","n":"Toolbox AI (me)","p":"guidebot","cat":"Info","risk":"safe","icon":"\U0001f916",
 "k":["guide","bot","assistant","ai","help","\u0631\u0627\u0647\u0646\u0645\u0627","\u0631\u0628\u0627\u062a"],
 "al":["guide bot","ask the bot"],"qs":["what can you do","who are you"],
 "d":"Web-enabled assistant of this app (live web search, full explanations, image search, learning memory): routes questions to the right tool with steps, prerequisites and warnings - EN/FA, zero internet.",
 "s":["Type a question and Send","/tools lists all, /help commands, /clear wipes chat"],"rel":["forge","settings","websearch","imagesearch"]},
{"id":"websearch","n":"Web Search","p":"guidebot","cat":"Info","risk":"safe","icon":"\U0001f310",
 "k":["web","search","google","internet","duckduckgo","online","deep","wiki","news","/web","\u0633\u0631\u0686","\u062c\u0633\u062a\u062c\u0648","\u06af\u0648\u06af\u0644","\u0627\u06cc\u0646\u062a\u0631\u0646\u062a"],
 "al":["web search","search the web","google search","answer from web"],
 "qs":["how do i search the web","how does web search work","can you search google"],
 "d":"Online web search: /web <question>; modes wiki / news / deep; auto CVE->NVD lookup; confidence score; SQLite memory (30-day expiry).",
 "s":["Open the Toolbox AI page","Type /web <question> - or ask anything unmatched and web fallback triggers automatically","Modes: /web wiki <topic> | /web news <topic> | /web deep <question>","Wait 5-15s while pages are read","Answer shows confidence, summary, numbered sentences and source URLs"],
 "r":"internet; pip packages ddgs, requests, beautifulsoup4","rel":["imagesearch","guidebot"]},
{"id":"imagesearch","n":"Image Search","p":"guidebot","cat":"Info","risk":"safe","icon":"\U0001f5bc",
 "k":["image","img","picture","photo","download image","logo","/img","\u062a\u0635\u0648\u06cc\u0631","\u0639\u06a9\u0633"],
 "al":["image search","download image","find pictures"],
 "qs":["how do i search images","how do i download a picture"],
 "d":"Downloads images for a query into ~/.toolbox_pro_images/ with auto format detection (JPG/PNG/GIF/WEBP).",
 "s":["Open the Toolbox AI page","Type /img <query>","Images download and save locally","Each result shows title, saved file path and source URL"],
 "r":"internet; pip package ddgs","rel":["websearch"]}]

GB_DANGER = [
 (r"(ddos|denial of service|botnet|flood attack)", None),
 (r"(malware|virus|ransomware|trojan|worm|keylogger|spyware|rootkit)", None),
 (r"(phishing|fake login|credential harvest|clone site)", None),
 (r"(carding|credit card|cvv|bank account|skimmer)", None),
 (r"(bomb|weapon|explosive|gun)", None),
 (r"(wifi|wireless|wpa|wpa2|handshake|deauth|router|modem).{0,40}(hack|crack|break|attack|password|passwd)|(hack|crack|break|attack).{0,40}(wifi|wireless|wpa|router|modem)|(\u0647\u06a9|\u0646\u0641\u0648\u0630|\u06a9\u0631\u06a9).{0,20}(\u0648\u0627\u06cc\u0641\u0627\u06cc|\u0648\u0627\u06cc \u0641\u0627\u06cc|\u0645\u0648\u062f\u0645|\u0631\u0648\u062a\u0631)", "wifiattack"),
 (r"(hash|md5|sha1|sha256|sha512|ntlm|bcrypt).{0,30}(crack|break|reverse)|(crack|break|reverse).{0,30}(hash|md5|password)|(\u06a9\u0631\u06a9).{0,15}(\u0647\u0634|\u0631\u0645\u0632)", "hashid"),
 (r"(brute ?force|dictionary attack|wordlist attack)", "bruteforce"),
 (r"(exploit|cve|vulnerability).{0,30}(find|search|use)|(find|search).{0,20}(exploit|cve)", "exploitfinder"),
 (r"(sniff|intercept|capture).{0,30}(traffic|packet|network|handshake)", "wifiattack"),
 (r"(port|network|host|target).{0,20}(scan|recon|enumerat)|(scan|recon).{0,20}(port|network|host)", "nmapx"),
 (r"(osint|stalk|track|investigate|dox).{0,30}(person|username|email|phone|someone|girl|boy)", "osint"), (r"(disconnect|cut|kick|drop|\u0642\u0637\u0639).{0,20}(wifi|wireless|wlan|\u0648\u0627\u06cc\u0641\u0627\u06cc|\u0648\u0627\u06cc \u0641\u0627\u06cc|\u0645\u0648\u062f\u0645|router|modem)|(wifi|wireless|wlan|\u0648\u0627\u06cc\u0641\u0627\u06cc|\u0648\u0627\u06cc \u0641\u0627\u06cc).{0,20}(disconnect|cut|kick|drop|\u0642\u0637\u0639)", "wifiattack")]

GB_NO = ("NOT in Toolbox Pro.\nThis toolbox ships ONLY defensive and authorized-audit utilities:\nscanning your own networks, public-source OSINT, password/hash testing on\nYOUR OWN data, Wi-Fi audit on YOUR OWN network.\nI cannot guide anything outside that scope.")

class GBEngine:
    EN_STOP = set("the a an is are am was were how do does did i you me my we us to for of in on with and or please tell about what which where can could should would there here it its this that be been have has had not no yes so if then than too very just need want get got make made use using tool tools app program way know learn show give me".split())
    FA_STOP = set("\u0686\u0647 \u06a9\u062f\u0648\u0645 \u06a9\u062c\u0627 \u0686\u0637\u0648\u0631 \u0686\u06af\u0648\u0646\u0647 \u0686\u0631\u0627 \u0622\u06cc\u0627 \u0645\u0646 \u062a\u0648 \u0634\u0645\u0627 \u0628\u0647 \u0627\u0632 \u062f\u0631 \u0628\u0627 \u0648 \u06cc\u0627 \u06a9\u0647 \u0627\u0633\u062a \u0647\u0633\u062a \u0631\u0648 \u0631\u0627 \u0628\u0631\u0627\u06cc \u0628\u0627\u06cc\u062f \u0628\u0631\u0645 \u0628\u0631\u0647 \u0645\u06cc\u0634\u0647 \u0645\u06cc \u06a9\u0646\u0645 \u06a9\u0646\u0647".split())
    TR = str.maketrans("\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669", "01234567890123456789")
    INT = [("needs", r"(need|require|install|prerequisit|dependenc|\u0646\u06cc\u0627\u0632|\u067e\u06cc\u0634|\u0646\u0635\u0628)"),
           ("warn", r"(danger|risk|safe|legal|law|permission|warn|\u062e\u0637\u0631|\u0645\u062c\u0648\u0632|\u0642\u0627\u0646\u0648\u0646)"),
           ("trouble", r"(not working|error|fail|bug|problem|fix|crash|\u062e\u0637\u0627|\u0645\u0634\u06a9\u0644|\u062e\u0631\u0627\u0628|\u06a9\u0627\u0631 \u0646\u0645\u06cc)"),
           ("where", r"(which|where|what tool|find|locate|\u06a9\u062f\u0648\u0645|\u06a9\u062c\u0627)"),
           ("howto", r"(how|step|guide|use|usage|tutorial|start|work|\u0686\u0637\u0648\u0631|\u0686\u06af\u0648\u0646\u0647|\u0645\u0631\u0627\u062d\u0644|\u0622\u0645\u0648\u0632\u0634)")]
    def __init__(self):
        self.last = None
    def norm(self, s):
        s = str(s).lower().translate(self.TR)
        s = s.replace("\u064a", "\u06cc").replace("\u0643", "\u06a9").replace("\u200c", "")
        return re.sub(r"[^0-9a-z\u0600-\u06ff]+", " ", s).strip()
    def intent(self, low):
        for nm, pat in self.INT:
            if re.search(pat, low):
                return nm
        return "general"
    def score(self, e, toks, nq, dl):
        s = 0.0
        for t in toks:
            for k in e["k"]:
                if t == k:
                    s += 3.0
                elif len(k) > 3 and len(t) > 3 and (t.startswith(k) or k.startswith(t)):
                    s += 1.8
        for ph in e.get("al", []):
            if ph in nq:
                s += 3.0
            else:
                r = dl.SequenceMatcher(None, nq, ph).ratio()
                if r > 0.75:
                    s += 2.5 * r
        for qq in e.get("qs", []):
            r = dl.SequenceMatcher(None, nq, self.norm(qq)).ratio()
            if r > 0.70:
                s += 3.0 * r
        return s
    def byid(self, tid):
        for e in GB_KB:
            if e["id"] == tid:
                return e
        return None
    def block(self, e, it):
        L = ["%s %s   [%s | risk: %s]" % (e.get("icon", ""), e["n"], e.get("cat", ""), e.get("risk", "safe")),
             "Path: Dashboard > %s" % e["n"], e["d"]]
        if it in ("howto", "where", "general", "trouble") and e.get("s"):
            L.append("Steps:")
            L += ["  %d. %s" % (i, x) for i, x in enumerate(e["s"], 1)]
        if it in ("needs", "howto", "general", "trouble") and e.get("r"):
            L.append("Requires: " + e["r"])
        if it == "trouble":
            L += ["Troubleshooting:", "  1. Install 'Requires' via the Packages card.",
                  "  2. Run the app with sudo if the tool needs root.",
                  "  3. Open the page and press its Tool Guide button."]
        if e.get("risk") == "dangerous" or e.get("aw"):
            L.append("LEGAL: only on networks/systems/data you OWN or have WRITTEN permission for.")
        elif e.get("risk") == "sensitive":
            L.append("Use only on targets you are authorized to assess.")
        return L
GB_AI_CUSTOM = os.path.expanduser("~/.toolbox_ai_custom.json")
GB_AI_WEIGHTS = os.path.expanduser("~/.toolbox_ai_weights.json")
GB_SYN = [("\u067e\u0633\u0648\u0631\u062f", "password"), ("\u06af\u0630\u0631\u0648\u0627\u0698\u0647", "password"),
 ("\u0646\u0627\u0645 \u06a9\u0627\u0631\u0628\u0631\u06cc", "username"), ("\u0632\u06cc\u0631 \u062f\u0627\u0645\u0646\u0647", "subdomain"),
 ("\u0627\u0633\u06a9\u0646\u0631", "scan"), ("\u0645\u062a\u0627 \u062f\u0627\u062a\u0627", "metadata"),
 ("wi fi", "wifi"), ("\u0648\u0627\u06cc \u0641\u0627\u06cc", "\u0648\u0627\u06cc\u0641\u0627\u06cc")]
GB_PLANS = [
 (r"(wifi|wireless|\u0648\u0627\u06cc\u0641\u0627\u06cc).{0,30}(audit|full|complete)|(audit|test|check).{0,20}(wifi|wireless|\u0648\u0627\u06cc\u0641\u0627\u06cc)", ["wifiattack","wordlist","hashid"], "Full Wi-Fi security audit"),
 (r"(network|lan|net).{0,30}(audit|scan|map|recon)|(audit|map|recon).{0,20}(network|lan)|\u0634\u0628\u06a9\u0647.{0,15}\u0627\u0633\u06a9\u0646", ["hostscan","nmapx","exploitfinder"], "Full network reconnaissance"),
 (r"(web|site|website|\u0633\u0627\u06cc\u062a).{0,30}(audit|pentest|test|full)|(audit|pentest).{0,20}(web|site)", ["subfind","webpentest","webtools","exploitfinder"], "Full web application audit"),
 (r"(person|someone|target|individual|\u0634\u062e\u0635).{0,30}(osint|investigate|profile|recon|\u062a\u062d\u0642\u06cc\u0642)|osint.{0,20}(person|someone)", ["osint","ipgeox","phoneinfo"], "OSINT profile (public data only)"),
 (r"(password|pass|\u0631\u0645\u0632).{0,30}(security|policy|audit|check)|(security|audit).{0,20}(password)", ["passcheck","passforge"], "Password security review"),
 (r"(hash|\u0647\u0634).{0,30}(workflow|pipeline|process|full)|(workflow|pipeline).{0,20}(hash|crack)", ["hashid","wordlist","bruteforce"], "Hash cracking workflow")]



GB_GUIDE_TEXT_FULL = """
TOOLBOX AI - COMPLETE TOOL GUIDE (v5.3)
========================================================

[1] OVERVIEW
  Toolbox AI is the built-in, WEB-ENABLED assistant of Toolbox Pro.
  It is NOT offline-only: everyday questions are answered from the
  live web. It combines:
    - an internal knowledge base of every tool in this app (usable
      without internet as a fallback),
    - a LIVE web engine (Google-first) that returns long, complete
      explanations built from full paragraphs of real pages,
    - a learning memory that stores answered questions locally,
    - an offline page archive that keeps working without internet,
    - an image search that downloads pictures to a local folder.
  All output is ENGLISH ONLY. Persian/Arabic text found inside web
  pages is filtered out before display.

[2] ANSWER PIPELINE (exact order of processing)
  1. Safety filter (always first, cannot be disabled)
  2. Slash commands (/web, /img, /brief, ...)
  3. WEB-FIRST mode, if enabled (/webfirst on)
  4. Learned memory (instant, offline, fuzzy match 90%+)
  5. Internal knowledge base (score threshold 4.5)
  6. Live web search - triggered when the KB score is below 4.5 OR
     the message looks like a real question (what/how/why/.../?)
  7. Offline archive fallback when the web returns nothing

[3] WEB SEARCH - EXACT QUERY + FULL EXPLANATION
  - Your query is sent to the search engine EXACTLY as you typed it.
    No rewriting, no synonym expansion, no extra parallel queries.
  - Engine chain with automatic fallback:
    Google -> DuckDuckGo -> Brave -> Mojeek
  - FULL explanation mode (default for /web and for auto fallback):
      * reads up to 8 result pages concurrently
      * keeps FULL paragraphs (80-4000 characters each)
      * returns up to 15 paragraphs, up to ~20,000 characters total
      * grouped by source; each block shows the page title and URL
      * ends with a Sources list
  - Expected time: 10-30 seconds. A brief UI freeze is normal.
  - Modes:
      /web wiki <topic>    Wikipedia only (fast, encyclopedic)
      /web news <topic>    latest news
      /web deep <question> 8 pages, always fresh, bypasses cache
  - A CVE ID inside the query also fetches the official NVD
    description and shows it with a shield marker.

[4] CORTEX INTELLIGENCE LAYER
  - Intent detection: definition / howto / compare / why / list /
    news / yesno / general - printed as an "Intent:" header line.
  - Multi-part questions ("what is X and how to Y") are split and
    answered part by part.
  - How-to answers get an extra numbered "Detected steps" section.
  - Source authority badges per domain:
      nist.gov / cisa.gov 2.0 | owasp.org 1.8 | wikipedia.org 1.6
      .gov / .edu 1.5 | github / stackoverflow 1.2-1.3
      medium 0.8 | quora 0.7
    HIGH >= 1.4, MEDIUM >= 1.0, otherwise LOW.
  - Every answer ends with "Try next" suggestions; /related repeats
    the last suggestion set. /topic shows the tracked topic.
  - /stats shows counters: questions, web hits, web misses,
    memory hits, current topic, learned entries, archive size.

[5] COMMAND REFERENCE
  WEB
    /web <question>      full explanation with your exact query
    /search <question>   alias of /web
    /web wiki <topic>    Wikipedia only
    /web news <topic>    latest news
    /web deep <question> deep fresh search (8 pages, no cache)
    /brief <question>    one-line fast answer
    /steps <question>    forced step-by-step how-to mode
    /webfirst on|off     send EVERY question to the web first
    /offline <question>  search the local archive only (no internet)
    /archive             archive statistics (pages, size, path)
    /summarize <url>     extractive summary of any web page
  IMAGES
    /img <query>         download up to 6 images
    /image <query>       alias of /img
    Files are saved to: ~/.toolbox_pro_images/
  MEMORY & LEARNING
    /memory              list learned knowledge entries
    /forgetall           wipe learned knowledge
    /clearmem            wipe learned knowledge + web answer cache
    /resetmem            alias of /clearmem
  INTERNAL KNOWLEDGE BASE (works offline)
    /help  /tools  /cats  /risk  /find <task>  /plan <goal>
    compare A vs B  |  compare all  |  /why  |  /next
    /teach q | a  |  /good  |  /bad  |  /hist  |  /clear

[6] MEMORY, DATA FILES & RESET
  ~/.toolbox_pro_aibrain.json   conversation (20) + learned Q&A (300)
  ~/.toolbox_pro_webcache.db    web answer cache (30-day expiry)
  ~/.toolbox_pro_archive.db     offline page archive (auto-filled)
  ~/.toolbox_pro_cortex.json    counters, topic, webfirst flag
  ~/.toolbox_pro_images/        downloaded images
  ~/.toolbox_ai_custom.json     your /teach entries
  ~/.toolbox_ai_weights.json    /good /bad ranking weights
  To start completely fresh: run /clearmem, then delete the files
  above if needed. The archive refills automatically as you search.

[7] SAFETY FILTER (PERMANENT)
  Runs before every other step, including web search. Actionable
  requests to create malware, viruses, ransomware, weapons, or to
  attack systems without authorization are refused and never reach
  the internet. This filter is a fixed part of the product and cannot
  be switched off by any command or setting. Analytical, historical
  and defensive questions about the same topics (how X works, how to
  detect / remove / defend against X) are fully allowed and receive
  complete web answers.

[8] LEGAL WARNING
  Use all tools and searches only on systems and networks you own or
  have explicit written authorization to test. Web content comes from
  third-party sites - always verify critical information against the
  cited source URLs.

[9] EXAMPLES
  /web what is the sun
  /web how does a reverse shell work and how to detect it
  /web deep history of cryptography
  /brief what is dns
  /steps how to harden an ssh server
  /img network topology diagram
  /summarize https://en.wikipedia.org/wiki/Sun
  /offline sql injection
  /webfirst on

[10] TROUBLESHOOTING
  - "No web result found." -> no internet, all engines blocked, or
    only non-English pages matched. Retry with /web deep <question>.
  - A 10-30 second freeze during /web is normal (pages are read).
  - Answers repeating old cached text -> run /clearmem.
  - Missing packages:
      pip install --break-system-packages ddgs requests beautifulsoup4
  - Proxy: HTTP_PROXY / HTTPS_PROXY environment variables are used
    automatically when set.
"""

TOOL_HELP["guidebot"] = {"en": GB_GUIDE_TEXT_FULL}  # FULL English guide (v5.3)


class ToolboxAI(GBEngine):
    def __init__(self):
        GBEngine.__init__(self)
        try: self.custom = json.load(open(GB_AI_CUSTOM, encoding="utf-8"))
        except Exception: self.custom = []
        try: self.weights = json.load(open(GB_AI_WEIGHTS, encoding="utf-8"))
        except Exception: self.weights = {}
        self.hist = []
        self.wiz = None
        self.last_e = None
        self.last_toks = []
        self.last_nq = ""
        self.web = WebBrain()  # auto-added
        self.brain = AIBrain()  # auto-added v4
        self.cortex = Cortex(self.web, self.brain)  # auto-added v5
        self.webfirst = bool(self.cortex.st.get('webfirst', False))  # v5.1
    def _save(self):
        try: json.dump(self.custom, open(GB_AI_CUSTOM, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception: pass
        try: json.dump(self.weights, open(GB_AI_WEIGHTS, "w", encoding="utf-8"))
        except Exception: pass
    def norm(self, s):
        s = str(s).lower()
        for a, b in GB_SYN:
            s = s.replace(a, b)
        return GBEngine.norm(self, s)
    def score(self, e, toks, nq, dl):
        s = GBEngine.score(self, e, toks, nq, dl) + self.weights.get(e["id"], 0.0)
        nm = e["n"].lower()
        for w in nm.replace("(", " ").replace(")", " ").replace("/", " ").split():
            if len(w) > 3 and w in nq:
                s += 2.0
        return s
    def _matched(self, e, toks, nq):
        m = []
        for t in toks:
            for k in e["k"]:
                if t == k or (len(k) > 3 and len(t) > 3 and (t.startswith(k) or k.startswith(t))):
                    m.append(k)
        for ph in e.get("al", []):
            if ph in nq:
                m.append(ph)
        return sorted(set(m))
    def _plan(self, nl):
        for pat, ids, label in GB_PLANS:
            if re.search(pat, nl):
                L = ["WORKFLOW PLAN: %s" % label, ""]
                pages = []
                for n, tid in enumerate(ids, 1):
                    e = self.byid(tid)
                    if not e:
                        continue
                    pages.append((e["p"], e["n"]))
                    L.append("Phase %d: %s %s" % (n, e.get("icon", ""), e["n"]))
                    L.append("   why: %s" % e["d"])
                    if e.get("s"):
                        L.append("   first step: %s" % e["s"][0])
                L.append("")
                L.append("Run phases in order; green buttons jump to each tool.")
                return {"kind": "plan", "head": "Planner", "text": "\n".join(L), "pages": pages}
        return None
    def _name_hits(self, nq, dl):
        out = []
        for e in GB_KB:
            s = 0.0
            nm = self.norm(e["n"])
            if nm in nq:
                s = 6.0
            else:
                words = [w for w in nm.split() if len(w) > 3]
                for w in words:
                    if w in nq:
                        s += 2.5
                for w in nq.split():
                    if len(w) > 4:
                        for x in words + [e["id"]]:
                            if len(x) > 3 and dl.SequenceMatcher(None, w, x).ratio() > 0.85:
                                s += 2.0
                                break
            if s > 0:
                out.append((s, e))
        out.sort(key=lambda x: -x[0])
        return out
    def _cmp_side(self, e):
        rels = [x["n"] for x in (self.byid(r) for r in e.get("rel", [])) if x]
        return ["%s %s" % (e.get("icon", ""), e["n"]),
                "  category : %s" % e.get("cat", "-"),
                "  risk     : %s" % e.get("risk", "safe"),
                "  does     : %s" % e["d"],
                "  needs    : %s" % (e.get("r") or "nothing extra"),
                "  steps    : %d" % len(e.get("s", [])),
                "  combines : %s" % (", ".join(rels) or "-")]
    def _verdict(self, a, b):
        V = ["VERDICT:"]
        rk = {"safe": 0, "sensitive": 1, "dangerous": 2}
        if rk.get(a.get("risk"), 0) != rk.get(b.get("risk"), 0):
            V.append("  - risk differs: %s is %s, %s is %s." % (a["n"], a.get("risk"), b["n"], b.get("risk")))
        if bool(a.get("r")) != bool(b.get("r")):
            easy = b["n"] if a.get("r") else a["n"]
            V.append("  - %s is easier to start (no extra requirements)." % easy)
        if a.get("cat") == b.get("cat"):
            V.append("  - same category (%s): pick by task, or combine them." % a.get("cat"))
        else:
            V.append("  - different categories (%s vs %s): they usually complement each other." % (a.get("cat"), b.get("cat")))
        if b["id"] in a.get("rel", []) or a["id"] in b.get("rel", []):
            V.append("  - they are related: using both in one workflow is common.")
        if len(V) == 1:
            V.append("  - both are valid; choose by your target and the LEGAL notes.")
        return V
    def _compare(self, nl):
        import difflib as dl
        if re.search(r"\b(all|everything)\b|\u0647\u0645\u0647", nl):
            L = ["COMPARE ALL - every tool in the toolbox:", ""]
            pages = []
            for e in GB_KB:
                L.append("%s %-28s [%s|%s] %s" % (e.get("icon", ""), e["n"][:28], e.get("cat", "-"), e.get("risk", "safe"), e["d"][:58]))
                pages.append((e["p"], e["n"]))
            return {"kind": "plan", "head": "Compare All (%d tools)" % len(GB_KB), "text": "\n".join(L), "pages": pages[:6]}
        pick = []
        for s, e in self._name_hits(nl, dl)[:2]:
            if s >= 2.0:
                pick.append(e)
        if len(pick) < 2:
            parts = re.split(r"\bvs\b|versus|\u0628\u0627|\u0648 |and |with |\u06cc\u0627 |or | ", nl)
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                h = self._name_hits(p, dl)
                if h and h[0][0] >= 2.0 and h[0][1] not in pick:
                    pick.append(h[0][1])
                if len(pick) == 2:
                    break
        if len(pick) < 2:
            names = ", ".join(e["n"] for e in GB_KB)
            return {"kind": "text", "text": "Name TWO tools to compare, e.g.:\n  compare hashid vs bruteforce\n  compare all\nAll tool names:\n  " + names}
        a, b = pick
        L = ["COMPARE: %s  vs  %s" % (a["n"], b["n"]), "", "[A]"]
        L += self._cmp_side(a) + ["", "[B]"] + self._cmp_side(b) + [""]
        L += self._verdict(a, b)
        return {"kind": "plan", "head": "Comparator", "text": "\n".join(L),
                "pages": [(a["p"], a["n"]), (b["p"], b["n"])]}
    def answer(self, q):
        import difflib as dl
        raw = (q or "").strip()
        low = raw.lower()
        nl = self.norm(raw)
        # ── AIBrain v4 + Web/Image commands (patch5) ──
        _bq = raw
        if low in ("/clearmem", "/resetmem"):  # v5.3 wipe learned memory
            try:
                self.brain.knowledge = {}
                self.brain.history.clear()
                self.brain._persist()
            except Exception:
                pass
            try:
                with self.web._db() as con:
                    con.execute("DELETE FROM mem")
            except Exception:
                pass
            return {"kind": "text", "text": "Memory cleared: learned knowledge and web answer cache wiped. Next questions will be searched fresh."}
        if low.startswith("/webfirst"):  # v5.1
            _p = low.split()
            if len(_p) > 1 and _p[1] in ("on", "off"):
                self.webfirst = (_p[1] == "on")
                self.cortex.st["webfirst"] = self.webfirst
                self.cortex._save()
                return {"kind": "text", "text": "WEB-FIRST mode: " + _p[1].upper() + (" - every question hits the web before internal knowledge." if _p[1] == "on" else " - internal knowledge first, web as fallback.")}
            return {"kind": "text", "text": "WEB-FIRST mode is currently: " + ("ON" if getattr(self, "webfirst", False) else "OFF") + ". Usage: /webfirst on | off"}
        if low.startswith('/brief ') or low.startswith('/steps '):  # auto-added v5
            _wq = raw.split(None, 1)[1]
            for _pat, _tid in GB_DANGER:
                if _tid is None and re.search(_pat, self.norm(_wq)):
                    return {"kind": "dno", "text": GB_NO}
            if low.startswith('/brief '):
                return {"kind": "text", "text": self.cortex.answer(_wq, brief=True)}
            return {"kind": "text", "text": self.cortex.answer(_wq, force="howto")}
        if low in ('/stats',):
            return {"kind": "text", "text": self.cortex.stats_report()}
        if low in ('/topic',):
            return {"kind": "text", "text": self.cortex.topic_report()}
        if low in ('/related',):
            return {"kind": "text", "text": self.cortex.related_report()}
        if low.startswith('/web ') or low.startswith('/search '):
            _wq = raw.split(None, 1)[1]
            for _pat, _tid in GB_DANGER:
                if _tid is None and re.search(_pat, self.norm(_wq)):
                    return {"kind": "dno", "text": GB_NO}
            _fa = None
            try:
                _fa = self.web.full_explanation(_wq)
            except Exception:
                _fa = None
            if _fa:
                try:
                    self.brain.learn(_wq, _fa)
                except Exception:
                    pass
                return {"kind": "text", "text": _fa}
            return {"kind": "text", "text": self.cortex.answer(_wq)}
        if low.startswith('/offline '):  # auto-added v4: offline archive
            _wq = raw.split(None, 1)[1]
            _arc = self.web.archive_search(_wq)
            return {"kind": "text", "text": _arc or "📦 Nothing matching found in the offline archive."}
        if low in ('/archive', '/archivestats'):
            return {"kind": "text", "text": self.web.archive_stats()}
        if low.startswith('/img ') or low.startswith('/image '):
            _wq = raw.split(None, 1)[1]
            return {"kind": "text", "text": self.web.image_search_and_answer(_wq)}
        try:
            if low.startswith('/summarize ') or low.startswith('/summary '):
                return {"kind": "text", "text": self.brain.summarize_url(raw.split(None, 1)[1].strip())}
            if low in ('/memory', '/learned'):
                return {"kind": "text", "text": self.brain.memory_report()}
            if low in ('/forgetall',):
                return {"kind": "text", "text": self.brain.forget_all()}
            self.brain.remember(raw)
            _bq = self.brain.preprocess(raw)
            _rec = self.brain.recall(_bq)
            if _rec:
                return {"kind": "text", "text": _rec}
        except Exception:
            _bq = raw
        # -- WEB-FIRST mode (v5.1): web before internal KB --
        if getattr(self, "webfirst", False) and not raw.startswith("/"):
            _dng = False
            for _pat, _tid in GB_DANGER:
                if _tid is None and re.search(_pat, self.norm(raw)):
                    _dng = True
                    break
            if not _dng:
                try:
                    _wa2 = self.cortex.answer(_bq)
                except Exception:
                    _wa2 = None
                if _wa2 and not _wa2.startswith("No web result"):
                    return {"kind": "text", "text": _wa2}
        if low.startswith('/img ') or low.startswith('/image '):  # auto-added: image search
            _wq = raw.split(None, 1)[1]
            return {"kind": "text", "text": self.web.image_search_and_answer(_wq)}
        if low == "/clear":
            return {"kind": "clear"}
        if low == "/help":
            return {"kind": "text", "text": "Toolbox AI v5.3 - commands:\n WEB: /web <q> full explanation | /web wiki|news|deep <q> | /brief <q> | /steps <q>\n /webfirst on|off | /offline <q> | /archive | /summarize <url>\n IMG: /img <q> -> ~/.toolbox_pro_images/\n MEM: /memory | /forgetall | /clearmem | /stats | /topic | /related\n KB: /tools /cats /risk /find /plan compare /why /next /teach /good /bad /hist /clear\nAll output is English-only."}
        if low == "/tools":
            L = ["All %d tools:" % len(GB_KB), ""]
            for e in GB_KB:
                L.append("  %s %-26s [%s] %s" % (e.get("icon", ""), e["n"], e.get("cat", "-"), e["d"][:55]))
            return {"kind": "text", "text": "\n".join(L)}
        if low == "/cats":
            cats = {}
            for e in GB_KB:
                cats.setdefault(e.get("cat", "-"), []).append(e["n"])
            L = ["Categories:"]
            for c in sorted(cats):
                L.append("  [%s] %s" % (c, ", ".join(cats[c])))
            return {"kind": "text", "text": "\n".join(L)}
        if low == "/risk":
            L = ["Tools by risk level:"]
            for lvl in ("dangerous", "sensitive", "safe"):
                ns = [e["n"] for e in GB_KB if e.get("risk", "safe") == lvl]
                L.append("  %s (%d): %s" % (lvl.upper(), len(ns), ", ".join(ns)))
            L.append("Dangerous/sensitive = YOUR OWN systems or written permission only.")
            return {"kind": "text", "text": "\n".join(L)}
        if low == "/hist":
            if not self.hist:
                return {"kind": "text", "text": "No history yet."}
            return {"kind": "text", "text": "\n".join("%d. %s -> %s" % (n, a, b) for n, (a, b) in enumerate(self.hist, 1))}
        if low.startswith("/teach "):
            body = raw[7:]
            if "|" not in body:
                return {"kind": "text", "text": "Usage: /teach question | answer"}
            a, b = body.split("|", 1)
            self.custom.append({"q": a.strip(), "a": b.strip()})
            self._save()
            return {"kind": "text", "text": "Learned and saved forever."}
        if low in ("/good", "/bad"):
            if not self.last_e:
                return {"kind": "text", "text": "Nothing to rate yet."}
            d = 0.6 if low == "/good" else -0.6
            self.weights[self.last_e] = round(self.weights.get(self.last_e, 0.0) + d, 2)
            self._save()
            return {"kind": "text", "text": "Ranking for %s updated to %+.1f" % (self.byid(self.last_e)["n"], self.weights[self.last_e])}
        if low == "/why":
            if not self.last_e:
                return {"kind": "text", "text": "Ask something first, then /why."}
            e = self.byid(self.last_e)
            m = self._matched(e, self.last_toks, self.last_nq)
            return {"kind": "text", "text": "Reasoning for last answer:\n tool: %s\n matched signals: %s\n learned bias: %+.1f\n intent: %s" % (e["n"], ", ".join(m) or "(fuzzy/phrase/name match)", self.weights.get(e["id"], 0.0), self.intent(self.last_nq))}
        if low == "/next":
            if not self.wiz:
                return {"kind": "text", "text": "No active wizard. Ask a how-to first."}
            eid, k = self.wiz
            en = self.byid(eid)
            if k >= len(en.get("s", [])):
                self.wiz = None
                return {"kind": "text", "text": "Wizard finished for %s." % en["n"]}
            st = en["s"][k]
            self.wiz = (eid, k + 1)
            fin = k + 1 == len(en["s"])
            return {"kind": "text", "text": "Step %d/%d of %s:\n  %s%s" % (k + 1, len(en["s"]), en["n"], st, "\n(wizard complete)" if fin else "")}
        if low.startswith("/plan "):
            pl = self._plan(self.norm(raw[6:]))
            return pl or {"kind": "text", "text": "No stored plan for that goal. Goals: wifi audit, network audit, web audit, person osint, password security, hash workflow."}
        if low.startswith("/find "):
            goal = self.norm(raw[6:])
            toks = [t for t in goal.split() if t not in self.EN_STOP and t not in self.FA_STOP and len(t) > 1]
            sc = sorted(((self.score(e, toks, goal, dl), e) for e in GB_KB), key=lambda x: -x[0])
            top = [x for x in sc[:3] if x[0] > 0.5]
            if not top:
                return {"kind": "text", "text": "Nothing matches that task. Try /tools to browse."}
            L = ["Best tools for: %s" % raw[6:].strip(), ""]
            pages = []
            for s, e in top:
                L.append("%s %s  (match %d%%)" % (e.get("icon", ""), e["n"], min(99, int(40 + s * 8))))
                L.append("   %s" % e["d"])
                pages.append((e["p"], e["n"]))
            return {"kind": "plan", "head": "Finder", "text": "\n".join(L), "pages": pages}
        if re.search(r"(compare|comparison|versus|\bvs\b|difference|\u0641\u0631\u0642|\u0645\u0642\u0627\u06cc\u0633\u0647|\u06a9\u062f\u0627\u0645 \u0628\u0647\u062a\u0631|better)", nl):
            return self._compare(nl)
        for c in self.custom:
            if dl.SequenceMatcher(None, nl, self.norm(c["q"])).ratio() > 0.8:
                return {"kind": "text", "text": "(taught) " + c["a"]}
        pl = self._plan(nl)
        if pl:
            return pl
        for pat, tid in GB_DANGER:
            if re.search(pat, nl):
                if tid is None:
                    return {"kind": "dno", "text": GB_NO}
                e = self.byid(tid)
                L = ["YES - Toolbox Pro HAS this capability.", ""] + self.block(e, "howto") + ["", "Built for authorized auditing; follow the steps and the LEGAL line."]
                self.last = e["id"]; self.last_e = e["id"]; self.last_nq = nl
                self.wiz = (e["id"], 0) if e.get("s") else None
                return {"kind": "ok", "page": e["p"], "head": "%s  |  intent: capability-check (dangerous)" % e["n"],
                        "text": "\n".join(L), "rel": e.get("rel", []), "wiz": bool(e.get("s"))}
        toks = [t for t in nl.split() if t not in self.EN_STOP and t not in self.FA_STOP and len(t) > 1]
        it = self.intent(low)
        sc = sorted(((self.score(e, toks, nl, dl), e) for e in GB_KB), key=lambda x: -x[0])
        top, e = sc[0]
        if self.last and (re.search(r"\b(it|that tool|this tool)\b", low) or "\u0647\u0645\u0648\u0646" in nl or "\u0627\u0648\u0646" in nl):
            e2 = self.byid(self.last)
            if e2:
                e, top = e2, top + 5
        if top < 4.5 or _looks_question(raw):  # v5.1 aggressive web trigger
            try:  # auto-added: web fallback (v4: context + learning)
                _wa = None
                try:
                    _wa = self.web.full_explanation(_bq)
                except Exception:
                    _wa = None
                if not _wa:
                    _wa = self.cortex.answer(_bq)
            except Exception:
                _wa = None
            if _wa:
                try:
                    self.brain.learn(raw, _wa)
                except Exception:
                    pass
                return {"kind": "text", "text": _wa}
            cands = [(x[1]["p"], x[1]["n"]) for x in sc[1:4] if x[0] > 0.5]
            return {"kind": "none",
                    "text": "Hmm, I could not map that to a tool.\nTry /find <task>, /tools, or keywords like wifi, port, hash, crack...\nClosest guesses are in the green buttons below.",
                    "cands": cands}
        self.last = e["id"]; self.last_e = e["id"]; self.last_nq = nl; self.last_toks = toks
        self.hist = (self.hist + [(raw, e["n"])])[-10:]
        self.wiz = (e["id"], 0) if e.get("s") else None
        conf = max(40, min(99, int(45 + top * 7)))
        L = self.block(e, it)
        if len(sc) > 1 and sc[1][1]["id"] != e["id"] and sc[1][0] >= 2.2 and sc[1][0] > top * 0.6:
            L.append("")
            L.append("Also close: %s - say 'compare %s vs %s' for details." % (sc[1][1]["n"], e["n"], sc[1][1]["n"]))
        head = "%s  |  confidence %d%%  |  intent: %s" % (e["n"], conf, it)
        rel = [x["n"] for x in (self.byid(r) for r in e.get("rel", [])) if x]
        fol = []
        if e.get("r"):
            fol.append("what does it need?")
        fol.append("is it legal/safe?")
        if rel:
            fol.append("how does %s help?" % rel[0])
        return {"kind": "ok", "page": e["p"], "head": head, "text": "\n".join(L),
                "rel": rel, "wiz": bool(e.get("s")), "follow": fol[:3]}


class ToolboxApp:
    def __init__(self):
        self.lang = "en"
        self.settings_file = SETTINGS_FILE
        self._load_prefs()
        self.root = tk.Tk()

        self.root.title("")
        self.root.geometry("950x650")
        self.root.configure(bg=TH["bg"])
        self.root.minsize(800, 500)
        self._ct_out_map = {}
        self._apply_startup_prefs()

        self._build_ui()
    def _load_prefs(self):
        try:
            with open(self.settings_file, encoding='utf-8') as f:
                self.prefs = json.load(f)
        except Exception:
            self.prefs = {}
        self.lang = "en"

    def _save_prefs(self, **kw):
        self.prefs.update(kw)
        try:
            with open(self.settings_file, "w", encoding='utf-8') as f:
                json.dump(self.prefs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def T(self, key):
        key = str(key)
        entry = I18N.get(key)
        txt = None
        if isinstance(entry, dict):
            txt = entry.get("en")
        if not txt:
            txt = EEEXTRA_TR.get(key)
        if not txt:
            txt = key
        return str(txt)

    def _wl_T(self, fa_t, en_t):
        """i18n hook: UI is English-only today; keeps call sites locale-ready."""
        return en_t


    def show_page(self, name):
        for p in self.pages.values():
            p.pack_forget()
        if name in self.pages:
            self.pages[name].pack(fill="both", expand=True)
    def _write(self, txt, text, clear=False):
        try:
            text = str(text)
            txt.config(state="normal")
            if clear:
                txt.delete("1.0", "end")
            txt.insert("end", text + "\n")
            txt.config(state="disabled")
            txt.see("end")
        except Exception:
            pass

    def _write_async(self, txt_widget, text, tag=None, clear=False):
        """ """
        def _do():
            try:
                txt_widget.configure(state="normal")
                if clear:
                    txt_widget.delete("1.0", "end")
                t2 = str(text)
                if tag:
                    txt_widget.insert("end", t2 + "\n", tag)
                else:
                    txt_widget.insert("end", t2 + "\n")
                txt_widget.configure(state="disabled")
                txt_widget.see("end")
            except Exception:
                pass
        try:
            self.root.after(0, _do)
        except Exception:
            pass

    def _dash_tools(self):
        # (icon, fa, en, [page ids], category)
        return [
        ("🌍", " IP", "IP Geolocation", ["ipgeox", "ipgeo"], "b_net"),
            ("📱", " ", "Phone Info", ["phoneinfo", "phone"], "b_info"),
            ("🔑", " ", "Pass Check", ["passcheck"], "b_sec"),
            ("🛡", "", "Pass Forge", ["passforge"], "b_sec"),
            ("📝", " ", "Wordlist", ["wordlist"], "b_sec"),
            ("🖥", " ", "Host Scan", ["hostscan"], "b_net"),
            ("🛰", " ", "Nmap", ["nmapx", "nmap"], "b_net"),
            ("📊", " ", "Sys Monitor", ["sysmon"], "b_sys"),
            ("🌐", " ", "Web Tools", ["webtools"], "b_net"),
            ("📡", "", "WiFi", ["wifiattack", "wifi"], "b_net"),
            ("🕸", " ", "Web Pentest", ["webpentest"], "b_sec"),
            ("🔓", " ", "Brute Force", ["bruteforce"], "b_sec"),
            ("🔍", "OSINT", "OSINT", ["osint"], "b_info"),
            ("💣", "", "Exploits", ["exploitfinder"], "b_sec"),
            ("📦", " ", "Packages", ["packx"], "b_sys"),
            ("⚙", "", "Settings", ["settings"], "b_sys"),
            ("🔧", "", "Forge", ["custom", "forge", "custom_edit"], "b_sys"),
            ("🧬", " ", "Hash ID", ["hashid"], "b_sec"),
            ("📷", "", "Exif/Metadata", ["exif"], "b_info"),
            ("🌐", "", "SubFinder", ["subfind"], "b_net"),
            ("🔌", "", "Netcat", ["ncat"], "b_net"),
            ("📡", "Airgeddon", "Airgeddon", ["airgeddon"], "b_net"),
        ("🤖", "Toolbox AI", "Toolbox AI", ["guidebot"], "b_info")]


    def _build_ui(self):
        try:
            self.root.title("🌙 Pro Toolbox")
            self.root.geometry("1280x800")
            self.root.minsize(900, 600)
            self.root.configure(bg=TH["bg"])
        except Exception:
            pass
        self.pages = {}
        self.content = tk.Frame(self.root, bg=TH["bg"])
        self.content.pack(fill="both", expand=True)
        self._build_all_pages()
        try:
            self.show_page("dashboard")
        except Exception:
            pass
    def _inject_help(self, pg, key):
        pg = getattr(pg, "_scroll_inner", pg) or pg
        try:
            hf = tk.Frame(pg)
            if pg.grid_slaves():
                rows = []
                for s in pg.grid_slaves():
                    try:
                        rows.append(int(s.grid_info().get("row", 0)))
                    except Exception:
                        pass
                hf.grid(row=(max(rows) + 1 if rows else 0), column=0, sticky="ew", pady=4)
            else:
                exp = []
                for s in pg.pack_slaves():
                    try:
                        info = s.pack_info()
                        if str(info.get("expand", 0)) in ("1", "true", "True", "yes"):
                            exp.append((s, info))
                    except Exception:
                        pass
                for s, info in exp:
                    try:
                        s.pack_forget()
                    except Exception:
                        pass
                hf.pack(side="bottom", fill="x", pady=4)
                for s, info in exp:
                    try:
                        opts = {k: info[k] for k in ("side", "fill", "expand", "padx", "pady", "ipadx", "ipady", "anchor") if k in info}
                        s.pack(**opts)
                    except Exception:
                        try:
                            s.pack(fill="both", expand=True)
                        except Exception:
                            pass
            b = tk.Button(hf, text=self._wl_T("❓   ", "❓ Tool Guide"),
                          command=lambda k=key: self._show_help(k))
            b.pack(side="left", padx=8, pady=2)
        except Exception:
            pass


    def _show_help(self, key):
        try:
            e = TOOL_HELP.get(key)
            if not e:
                return
            txt = e.get("en") or e.get("fa") or ""
            try:
                txt = str(txt)
            except Exception:
                pass
            w = tk.Toplevel(self.root)
            w.title("Tool Guide")
            w.geometry("760x560")
            try:
                w.configure(bg=TH["bg"])
            except Exception:
                pass
            sb = tk.Scrollbar(w, orient="vertical")
            t = tk.Text(w, wrap="word", padx=14, pady=12,
                        yscrollcommand=sb.set)
            sb.configure(command=t.yview)
            sb.pack(side="right", fill="y")
            t.pack(side="left", fill="both", expand=True)
            t.insert("1.0", txt)
            t.configure(state="disabled")
            def _hw(ev, t=t):
                d = -1 if getattr(ev, "delta", 0) > 0 else 1
                if getattr(ev, "num", None) == 4:
                    d = -1
                elif getattr(ev, "num", None) == 5:
                    d = 1
                t.yview_scroll(d * 3, "units")
                return "break"
            for _sq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                t.bind(_sq, _hw)
                w.bind(_sq, _hw)
                sb.bind(_sq, _hw)
        except Exception:
            import traceback
            traceback.print_exc()


    def _build_dashboard(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["dashboard"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=8)
        self.dash_search = tk.Entry(top, bg=TH["card"], fg=TH["text"],
                                    insertbackground=TH["text"], font=TH["font"])
        self.dash_search.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.dash_search.bind("<KeyRelease>", lambda e: self._dash_apply_filter())
        self.dash_search.bind("<Return>", lambda e: self._hist_record_search())
        tk.Button(top, text=self._wl_T("", "Search"),
                  command=lambda: (self._hist_record_search(), self._dash_apply_filter()),
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=3)
        tk.Button(top, text=self._wl_T("", "History"),
                  command=self._show_history,
                  bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        cat = tk.Frame(page, bg=TH["bg"])
        cat.pack(fill="x", pady=4)
        self.dash_cat = "all"
        for cid, ctxt in [("all", self._wl_T("", "All")),
                          ("b_net", self.T("b_net")),
                          ("b_sec", self.T("b_sec")),
                          ("b_info", self.T("b_info")),
                          ("b_sys", self.T("b_sys"))]:
            tk.Button(cat, text=ctxt,
                      command=lambda c=cid: self._dash_set_cat(c),
                      bg=TH["card"], fg=TH["text"], font=TH["font_s"]).pack(side="left", padx=3)
        wrap = tk.Frame(page, bg=TH["bg"])
        wrap.pack(fill="both", expand=True, pady=6)
        self.dash_scroll = tk.Scrollbar(wrap, orient="vertical",
                                        bg=TH["card"], troughcolor=TH["bg"])
        self.dash_canvas = tk.Canvas(wrap, bg=TH["bg"], highlightthickness=0,
                                     yscrollcommand=self.dash_scroll.set)
        self.dash_scroll.configure(command=self.dash_canvas.yview)
        self.dash_scroll.pack(side="right", fill="y", padx=(8, 0))
        self.dash_canvas.pack(side="left", fill="both", expand=True)
        self.dash_grid = tk.Frame(self.dash_canvas, bg=TH["bg"])
        self._dash_win = self.dash_canvas.create_window((0, 0), window=self.dash_grid, anchor="nw")
        self.dash_grid.bind("<Configure>",
            lambda e: self.dash_canvas.configure(scrollregion=self.dash_canvas.bbox("all")))
        self.dash_canvas.bind("<Configure>",
            lambda e: self.dash_canvas.itemconfig(self._dash_win, width=e.width))
        self.dash_canvas.bind("<Button-4>", lambda e: self.dash_canvas.yview_scroll(-3, "units"))
        self.dash_canvas.bind("<Button-5>", lambda e: self.dash_canvas.yview_scroll(3, "units"))
        self._dash_apply_filter()

    def _dash_set_cat(self, cid):
        self.dash_cat = cid
        self._dash_apply_filter()

    def _dash_apply_filter(self):
        q = (self.dash_search.get() or "").strip().lower()
        cat = getattr(self, "dash_cat", "all")
        try:
            self.dash_canvas.yview_moveto(0)
        except Exception:
            pass
        for w in self.dash_grid.winfo_children():
            w.destroy()
        cols = 3
        shown = 0
        for icon, fa_t, en_t, ids, bcat in self._dash_tools():
            if cat != "all" and bcat != cat:
                continue
            label = self._wl_T(fa_t, en_t)
            if q and q not in label.lower() and q not in en_t.lower():
                continue
            r, c = divmod(shown, cols)
            card = tk.Frame(self.dash_grid, bg=TH["card"], highlightthickness=1,
                            highlightbackground=TH["accent"])
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            tk.Label(card, text=icon, font=("Segoe UI", 24),
                     bg=TH["card"], fg=TH["text"]).pack(pady=(12, 2))
            tk.Label(card, text=label, font=TH["font_b"],
                     bg=TH["card"], fg=TH["text"]).pack(pady=(0, 3))
            tk.Label(card, text=self._wl_T("  ←", "open ←"),
                     font=TH["font_s"], bg=TH["card"], fg=TH["dim"]).pack(pady=(0, 10))
            def _go(ids2=ids):
                for pid in ids2:
                    if pid in self.pages:
                        self.show_page(pid)
                        return
                import re as _re_go
                def _norm(s):
                    return _re_go.sub(r"[^a-z]", "", s.lower())
                want = [_norm(x) for x in ids2]
                for key in list(self.pages.keys()):
                    nk = _norm(key)
                    if any(w and (w in nk or nk in w) for w in want):
                        self.show_page(key)
                        return
                print("  :", ids2, "| available:", sorted(self.pages.keys()))
            card.bind("<Button-1>", lambda e, g=_go: g())
            for ch in card.winfo_children():
                ch.bind("<Button-1>", lambda e, g=_go: g())
            self._dash_bind_wheel(card)
            shown += 1
        # ---- Exit card ----
        try:
            r, c = divmod(shown, cols)
            ex_card = tk.Frame(self.dash_grid, bg=TH["card"], highlightthickness=1,
                               highlightbackground=TH["red"])
            ex_card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            tk.Label(ex_card, text="\U0001f6aa", font=("Segoe UI", 24),
                     bg=TH["card"], fg=TH["text"]).pack(pady=(12, 2))
            tk.Label(ex_card, text="Exit", font=TH["font_b"],
                     bg=TH["card"], fg=TH["red"]).pack(pady=(0, 3))
            tk.Label(ex_card, text="Good Bye!", font=TH["font_s"],
                     bg=TH["card"], fg=TH["dim"]).pack(pady=(0, 10))
            ex_card.bind("<Button-1>", lambda e: self._app_exit())
            for ch in ex_card.winfo_children():
                ch.bind("<Button-1>", lambda e: self._app_exit())
            self._dash_bind_wheel(ex_card)
        except Exception as e:
            print("Exit card error:", repr(e))

        for c in range(cols):
            self.dash_grid.columnconfigure(c, weight=1, uniform="d")



    def _build_settings(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["settings"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                 command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self.T("desc_settings"),
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        wrap = tk.Frame(page, bg=TH["bg"])
        wrap.pack(fill="both", expand=True, padx=60)

        def sec(title):
            f = tk.Frame(wrap, bg=TH["bg2"], padx=12, pady=8,
                        highlightbackground=TH["border"], highlightthickness=1)
            f.pack(fill="x", pady=6)
            tk.Label(f, text=title, bg=TH["bg2"], fg=TH["moon"],
                    font=TH["font_b"]).pack(anchor="w")
            return f

        f_ap = sec(self.T("appearance"))
        lf = tk.Frame(f_ap, bg=TH["bg2"])
        lf.pack(fill="x", pady=3)
        tk.Label(lf, text="Language: English", bg=TH["bg2"], fg=TH["text"]).pack(side="left")
        tr2 = tk.Frame(f_ap, bg=TH["bg2"])
        tr2.pack(fill="x", pady=3)
        tk.Label(tr2, text="Theme:", bg=TH["bg2"], fg=TH["text"]).pack(side="left")
        self._theme_names = {k: str(THEME_EN[k]) for k in THEMES}
        cur = self.prefs.get("theme", "dark")
        self.set_theme = tk.StringVar(value=self._theme_names.get(cur, self._theme_names["dark"]))
        om = tk.OptionMenu(tr2, self.set_theme, *list(self._theme_names.values()))
        om.config(bg=TH["card"], fg=TH["text"], highlightthickness=0)
        om["menu"].config(bg=TH["card"], fg=TH["text"])
        om.pack(side="left", padx=5)
        tk.Label(tr2, text="Font size:", bg=TH["bg2"], fg=TH["text"]).pack(side="left", padx=(10, 0))
        self.set_fs = tk.Entry(tr2, bg=TH["card"], fg=TH["text"], width=3,
                              insertbackground=TH["text"])
        self.set_fs.pack(side="left")
        self.set_fs.insert(0, str(self.prefs.get("fontsize", 10)))
        tr3 = tk.Frame(f_ap, bg=TH["bg2"])
        tr3.pack(fill="x", pady=3)
        tk.Label(tr3, text="Window opacity:", bg=TH["bg2"], fg=TH["text"]).pack(side="left")
        self.set_opacity = tk.Scale(tr3, from_=0.5, to=1.0, resolution=0.05,
                                    orient="horizontal", bg=TH["bg2"], fg=TH["text"],
                                    length=180, highlightthickness=0)
        self.set_opacity.set(float(self.prefs.get("opacity", 1.0)))
        self.set_opacity.pack(side="left", padx=5)
        tk.Label(tr3, text="🏷 Window title:", bg=TH["bg2"], fg=TH["text"]).pack(side="left", padx=(10, 0))
        self.set_title = tk.Entry(tr3, bg=TH["card"], fg=TH["text"], width=14,
                                 insertbackground=TH["text"])
        self.set_title.pack(side="left")
        self.set_title.insert(0, self.prefs.get("title", ""))
        tr4 = tk.Frame(f_ap, bg=TH["bg2"])
        tr4.pack(fill="x", pady=3)
        self.set_top = tk.BooleanVar(value=self.prefs.get("topmost", False))
        self.set_full = tk.BooleanVar(value=self.prefs.get("fullscreen", False))
        self.set_priv = tk.BooleanVar(value=self.prefs.get("private", False))
        for var, txt in [
                         (self.set_top, "📌 Always on top"),
                         (self.set_full, "🖥 Fullscreen on launch"),
                         (self.set_priv, " Private mode (no history)")]:
            tk.Checkbutton(tr4, text=txt, variable=var, bg=TH["bg2"], fg=TH["text"],
                          selectcolor=TH["card"], font=TH["font_s"]).pack(side="left", padx=4)
        f_so = sec(self.T("sound"))
        self.set_sound = tk.BooleanVar(value=self.prefs.get("sound", True))
        tk.Checkbutton(f_so, text=self._wl_T("", "Enabled"),
                      variable=self.set_sound, bg=TH["bg2"], fg=TH["text"],
                      selectcolor=TH["card"]).pack(anchor="w")
        sf = tk.Frame(f_so, bg=TH["bg2"])
        sf.pack(fill="x", pady=3)
        tk.Button(sf, text="🗑 Delete sound files", command=self._del_sounds,
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        f_pf = sec(self.T("performance"))
        pf = tk.Frame(f_pf, bg=TH["bg2"])
        pf.pack(fill="x", pady=3)
        tk.Label(pf, text=self._wl_T(" HTTP:", "HTTP Proxy:"), bg=TH["bg2"], fg=TH["text"]).pack(side="left")
        self.set_proxy = tk.Entry(pf, bg=TH["card"], fg=TH["text"],
                                  insertbackground=TH["text"], width=30)
        self.set_proxy.pack(side="left", padx=5)
        self.set_proxy.insert(0, self.prefs.get("proxy", ""))
        nf = tk.Frame(f_pf, bg=TH["bg2"])
        nf.pack(fill="x", pady=3)
        tk.Label(nf, text="🧰 Extra nmap args:", bg=TH["bg2"],
                fg=TH["text"]).pack(side="left")
        self.set_nmapargs = tk.Entry(nf, bg=TH["card"], fg=TH["text"], width=20,
                                    insertbackground=TH["text"])
        self.set_nmapargs.pack(side="left", padx=5)
        self.set_nmapargs.insert(0, self.prefs.get("nmapargs", ""))

        f_da = sec(self.T("data"))
        bf2 = tk.Frame(f_da, bg=TH["bg2"])
        bf2.pack(fill="x", pady=3)
        tk.Button(bf2, text=self._wl_T("", "Export"), command=self._st_export,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        tk.Button(bf2, text=self._wl_T("", "Import"), command=self._st_import,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        tk.Button(bf2, text=self._wl_T(" ", "Clear History"),
                 command=self._st_clearhist, bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        tk.Button(bf2, text=self._wl_T("", "Reset"), command=self._st_reset,
                 bg=TH["red"], fg="#fff").pack(side="left", padx=3)
        f_ab = sec(self.T("about"))
        tk.Label(f_ab, text="Version: Toolbox Pro 3.0   |   Python " + sys.version.split()[0],
                bg=TH["bg2"], fg=TH["dim"], font=TH["font_s"]).pack(anchor="w")
        tk.Label(f_ab, text="Created by: Fatal Error",
                bg=TH["bg2"], fg=TH["accent2"], font=TH["font_s"]).pack(anchor="w")

        # ═══════════════════════════════════════════════════════════
        # Save Changes Button - Applies all changes instantly
        # ═══════════════════════════════════════════════════════════
        save_bar = tk.Frame(page, bg=TH["bg"])
        save_bar.pack(fill="x", padx=60, pady=(20, 10))

        save_btn = tk.Button(
            save_bar,
            text="💾 Save Changes",
            command=self._st_apply,
            bg=TH["green"],
            fg="#000",
            font=("Segoe UI", 14, "bold"),
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#7ee2a8",
            activeforeground="#000",
            highlightthickness=2,
            highlightbackground=TH["green"]
        )
        save_btn.pack(fill="x")

        self.set_msg = tk.Label(page, text="", bg=TH["bg"], fg=TH["green"],
                                font=TH["font_b"])
        self.set_msg.pack(pady=(5, 15))



    def _apply_theme_to_widget(self, w=None):
        """Recursively apply current TH colors/fonts to ALL existing widgets - LIVE"""
        if w is None:
            w = self.root
        try:
            cls = w.__class__.__name__
            if cls in ("Frame", "Toplevel", "Tk"):
                try: w.configure(bg=TH.get("bg", "#0a0e1a"))
                except: pass
            elif cls == "Label":
                try: w.configure(bg=TH.get("bg"), fg=TH.get("text"), font=TH.get("font"))
                except: pass
            elif cls == "Button":
                try: w.configure(bg=TH.get("card"), fg=TH.get("text"), font=TH.get("font"),
                                activebackground=TH.get("card"), activeforeground=TH.get("text"))
                except: pass
            elif cls == "Entry":
                try: w.configure(bg=TH.get("card"), fg=TH.get("text"),
                                insertbackground=TH.get("text"), font=TH.get("font"))
                except: pass
            elif cls == "Text":
                try: w.configure(bg=TH.get("bg2"), fg=TH.get("text"))
                except: pass
            elif cls == "Checkbutton":
                try: w.configure(bg=TH.get("bg2"), fg=TH.get("text"),
                                selectcolor=TH.get("card"), font=TH.get("font_s"))
                except: pass
            elif cls == "Radiobutton":
                try: w.configure(bg=TH.get("bg"), fg=TH.get("text"),
                                selectcolor=TH.get("card"), font=TH.get("font_s"))
                except: pass
            elif cls == "Scale":
                try: w.configure(bg=TH.get("bg2"), fg=TH.get("text"))
                except: pass
            elif cls == "OptionMenu":
                try:
                    w.configure(bg=TH.get("card"), fg=TH.get("text"))
                    w["menu"].configure(bg=TH.get("card"), fg=TH.get("text"))
                except: pass
            elif cls == "Scrollbar":
                try: w.configure(bg=TH.get("card"), troughcolor=TH.get("bg"))
                except: pass
            elif cls == "Canvas":
                try: w.configure(bg=TH.get("bg"))
                except: pass
        except Exception:
            pass
        try:
            for child in w.winfo_children():
                self._apply_theme_to_widget(child)
        except Exception:
            pass

    def _st_apply(self):
        """Apply ALL settings LIVE - no restart needed"""
        try:
            # ── Read all values ──
            pr_var = getattr(self, 'set_proxy', None)
            pr = pr_var.get().strip() if pr_var else self.prefs.get("proxy", "")

            theme_var = getattr(self, 'set_theme', None)
            if theme_var and hasattr(self, '_theme_names'):
                rev = {v: k for k, v in self._theme_names.items()}
                th = rev.get(theme_var.get(), "dark")
            else:
                th = self.prefs.get("theme", "dark")

            fs_var = getattr(self, 'set_fs', None)
            try:
                fs = int(_digits_en(fs_var.get()).strip() or 10) if fs_var else int(self.prefs.get("fontsize", 10))
            except Exception:
                fs = 10

            op_var = getattr(self, 'set_opacity', None)
            op = float(op_var.get()) if op_var else float(self.prefs.get("opacity", 1.0))
            title_var = getattr(self, 'set_title', None)
            title = title_var.get().strip() if title_var else self.prefs.get("title", "")
            top_var = getattr(self, 'set_top', None)
            topmost = top_var.get() if top_var else self.prefs.get("topmost", False)
            full_var = getattr(self, 'set_full', None)
            fullscreen = full_var.get() if full_var else self.prefs.get("fullscreen", False)
            priv_var = getattr(self, 'set_priv', None)
            private = priv_var.get() if priv_var else self.prefs.get("private", False)
            sound_var = getattr(self, 'set_sound', None)
            sound = sound_var.get() if sound_var else self.prefs.get("sound", True)
            nmap_var = getattr(self, 'set_nmapargs', None)
            nmapargs = nmap_var.get().strip() if nmap_var else self.prefs.get("nmapargs", "")
            lang_var_obj = getattr(self, 'lang_var', None)
            lang = lang_var_obj.get() if lang_var_obj else getattr(self, "lang", "en")

            # ── Update TH dict (THIS IS KEY FOR LIVE!) ──
            TH.update(THEMES.get(th, THEMES["dark"]))
            TH["font"] = ("Segoe UI", fs)
            TH["font_s"] = ("Segoe UI", max(8, fs - 1))
            TH["font_b"] = ("Segoe UI", fs, "bold")
            TH["font_h"] = ("Segoe UI", fs + 6, "bold")

            # ── Apply to root window ──
            try:
                self.root.configure(bg=TH["bg"])
                self.root.attributes("-alpha", op)
                self.root.attributes("-topmost", bool(topmost))
                try: self.root.attributes("-zoomed", bool(fullscreen))
                except: pass
                self.root.title(title if title else "Pro Toolbox")
            except Exception:
                pass

            # ── Apply proxy ──
            for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                if pr: os.environ[k] = pr
                else: os.environ.pop(k, None)

            # ── Save prefs ──
            self.lang = lang
            self._save_prefs(
                lang=lang, sound=sound, proxy=pr, theme=th, fontsize=fs,
                opacity=op, title=title, topmost=topmost,
                fullscreen=fullscreen, private=private, nmapargs=nmapargs
            )

            # ── LIVE apply theme to ALL existing widgets (NO RESTART!) ──
            try:
                self._apply_theme_to_widget(self.root)
            except Exception as e:
                print("Theme apply error:", e)

            # ── Also do a full rebuild for complete refresh ──
            try:
                self._rebuild_ui()
                self.show_page("settings")
            except Exception:
                pass

            # ── Success message ──
            try:
                msg = getattr(self, 'set_msg', None)
                if msg and msg.winfo_exists():
                    msg.configure(text="All changes applied instantly!", fg=TH["green"])
            except Exception:
                pass

        except Exception as e:
            print("_st_apply error:", e)


    def _st_restart2(self):
        try:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve())],
                            cwd=str(Path.home()))
        except Exception:
            pass
        self.root.destroy()

    def _st_export(self):
        from tkinter import filedialog
        f = filedialog.asksaveasfilename(defaultextension=".json",
                                         filetypes=[("JSON", "*.json")],
                                         initialfile="toolbox_settings.json")
        if not f:
            return
        try:
            with open(self.settings_file, encoding='utf-8') as s:
                data = s.read()
            with open(f, "w", encoding='utf-8') as d:
                d.write(data)
            self.set_msg.configure(text=self._wl_T("  ", "Exported"))
        except Exception as e:
            self.set_msg.configure(text="Error: %s" % e)

    def _st_import(self):
        from tkinter import filedialog
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not f:
            return
        try:
            with open(f, encoding='utf-8') as s:
                json.load(s)
            with open(f, encoding='utf-8') as s:
                data = s.read()
            with open(self.settings_file, "w", encoding='utf-8') as d:
                d.write(data)
            self.set_msg.configure(text=self._wl_T("   ...", "Restored, restarting..."))
            self.root.after(900, self._st_restart2)
        except Exception as e:
            self.set_msg.configure(text="Error: %s" % e)

    def _st_clearhist(self):
        try:
            p = self._hist_file()
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
        self._save_prefs(ig_history=[])
        self.set_msg.configure(text=self._wl_T("   ", "Search history cleared"))

    def _st_reset(self):
        try:
            with open(self.settings_file, "w", encoding='utf-8') as f:
                f.write("{}")
            self.set_msg.configure(text=self._wl_T("   ...", "Reset done, restarting..."))
            self.root.after(900, self._st_restart2)
        except Exception as e:
            self.set_msg.configure(text="Error: %s" % e)


    def _ig_local_phone(self, ip):
        L = []
        try:
            r = subprocess.run(["ping", "-c", "2", "-W", "1", ip],
                               capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                m = re.search(r"time=(\d+\.?\d*)", r.stdout)
                L.append("  📶 " + self._ig_lb(':  ✅    : ', 'Status: online ✅    Ping: ') +
                         ((m.group(1) + " ms") if m else "-"))
            else:
                L.append("  📶 " + self._ig_lb(':  ❌', 'Status: offline ❌'))
        except Exception:
            L.append("  📶 " + self._ig_lb(': ', 'Status: unknown'))
        mac = ""
        try:
            with open("/proc/net/arp", encoding="utf-8") as f:
                for ln in f.readlines()[1:]:
                    p2 = ln.split()
                    if p2 and p2[0] == ip and len(p2) >= 4 and p2[3] != "00:00:00:00:00:00":
                        mac = p2[3]
        except Exception:
            pass
        if mac:
            L.append("  📌 MAC: " + mac)
            name = self._hs_name(ip)
            if not name:
                name = self._wf_vendor(mac)
            if name:
                L.append("  🏷 " + self._ig_lb(' : ', 'Device name: ') + name)
        return "\n".join(L)



    def _pf_charset(self):
        ch = ""
        if getattr(self, 'pf_lower', None) and self.pf_lower.get():
            ch += "abcdefghijklmnopqrstuvwxyz"
        if getattr(self, 'pf_upper', None) and self.pf_upper.get():
            ch += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if getattr(self, 'pf_digits', None) and self.pf_digits.get():
            ch += "0123456789"
        if getattr(self, 'pf_symbols', None) and self.pf_symbols.get():
            ch += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        if not ch:
            ch = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ch

    def _passforge_worker(self):
        import secrets
        try:
            length = min(max(int(self.pf_len.get()), 4), 128)
        except Exception:
            length = 16
        try:
            count = min(max(int(self.pf_cnt.get()), 1), 50)
        except Exception:
            count = 5
        self.pf_last = []
        lines = [""]
        if self.pf_phrase.get():
            words = ["moon","star","night","sky","dream","calm","shadow","light",
                     "river","mountain","forest","wind","rain","snow","fire","sea",
                     "wolf","eagle","tiger","lion","bear","fox","deer","hawk",
                     "silver","golden","purple","blue","green","white","black","red"]
            wcount = max(3, length // 5)
            for i in range(count):
                parts = [secrets.choice(words).capitalize() for _ in range(wcount)]
                pwd = "-".join(parts) + str(secrets.randbelow(90) + 10)
                ent = wcount * math.log2(len(words)) + math.log2(90)
                self.pf_last.append(pwd)
                lines.append("  %3d. %s" % (i + 1, pwd))
                lines.append("       %s%s%d%s" % (self._pf_strength(ent),
                             self._wl_T(' | : ', ' | Entropy: '), round(ent), self._wl_T(' ', ' bits')))
                lines.append("")
        else:
            chars = self._pf_charset()
            if not chars:
                chars = string.ascii_letters + string.digits
            for i in range(count):
                pwd = "".join(secrets.choice(chars) for _ in range(length))
                ent = length * math.log2(len(chars))
                self.pf_last.append(pwd)
                lines.append("  %3d. %s" % (i + 1, pwd))
                lines.append("       %s%s%d%s" % (self._pf_strength(ent),
                             self._wl_T(' | : ', ' | Entropy: '), round(ent), self._wl_T(' ', ' bits')))
                lines.append("")
        self.root.after(0, lambda: self._write(self.pf_out, "\n".join(lines), True))



    def _pf_strength(self, ent):
        if ent >= 90:
            return self._wl_T("🟢  ", "🟢 Very strong")
        if ent >= 60:
            return self._wl_T("🟢 ", "🟢 Strong")
        if ent >= 40:
            return self._wl_T("🟡 ", "🟡 Medium")
        return self._wl_T("🔴 ", "🔴 Weak")

    def _pk_pm(self):
        if shutil.which("apt"):
            return "apt", ["sudo", "apt", "install", "-y"], ["apt", "search"]
        elif shutil.which("pacman"):
            return "pacman", ["sudo", "pacman", "-S", "--noconfirm"], ["pacman", "-Ss"]
        elif shutil.which("dnf"):
            return "dnf", ["sudo", "dnf", "install", "-y"], ["dnf", "search"]
        elif shutil.which("apk"):
            return "apk", ["sudo", "apk", "add"], ["apk", "search"]
        return None, None, None


    def _pk_pkg_installed(self, t, pm):
        try:
            if pm == "apt":
                r = subprocess.run(["dpkg", "-s", t], capture_output=True, text=True, timeout=10)
                if r.returncode == 0 and "install ok installed" in (r.stdout or ""):
                    return True
            elif pm == "pacman":
                r = subprocess.run(["pacman", "-Q", t], capture_output=True, timeout=10)
                if r.returncode == 0:
                    return True
            elif pm == "dnf":
                r = subprocess.run(["rpm", "-q", t], capture_output=True, timeout=10)
                if r.returncode == 0:
                    return True
            elif pm == "apk":
                r = subprocess.run(["apk", "info", "-e", t], capture_output=True, timeout=10)
                if t in (r.stdout or ""):
                    return True
        except Exception:
            pass
        return bool(shutil.which(t))

    def _packx_worker(self, names):
        runner = AsyncCommandRunner.get("packx")
        if runner.running:
            runner.stop()
            for _ in range(20):
                if not runner.running:
                    break
                time.sleep(0.1)
        toks = names.split()
        pm, inst, srch = self._pk_pm()
        T = self._wl_T
        if not pm:
            self._write_async(self.pk_out, "\n  No package manager found (apt/pacman/dnf/apk)\n", clear=True)
            return
        self._write_async(self.pk_out, "\n  " + T(" : ", "Package manager: ") + pm, clear=True)
        installed, missing = [], []
        for t in toks:
            if self._pk_pkg_installed(t, pm):
                installed.append(t)
            else:
                missing.append(t)
        if installed:
            self._write_async(self.pk_out, "  " + T("   : ", "Already installed: ") + ", ".join(installed))
        if not missing:
            self._write_async(self.pk_out, " ✅ " + T(" .", "All requested packages are already installed."))
            return
        sudo_ok = False
        try:
            sudo_ok = (subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=5).returncode == 0)
        except Exception:
            pass
        if not sudo_ok:
            import tempfile
            _fd3, sh = tempfile.mkstemp(prefix="tb_pk_", suffix=".sh")
            try:
                with os.fdopen(_fd3, "w") as f:
                    f.write("#!/bin/bash\n" + " ".join(inst + missing) + "\necho\nread -p 'Press Enter to close...'\n")
                os.chmod(sh, 0o700)
            except Exception:
                pass
            term = None
            for c0 in ("x-terminal-emulator", "xfce4-terminal", "gnome-terminal", "konsole", "xterm"):
                if shutil.which(c0):
                    term = c0
                    break
            if term:
                try:
                    args = [term, "--", sh] if term == "gnome-terminal" else [term, "-e", sh]
                    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._write_async(self.pk_out, "  🔐 " + T("    sudo    .", "Terminal opened; enter sudo password there."))
                except Exception:
                    self._write_async(self.pk_out, "  ⚠ " + T(" sudo      sudo  .", "sudo password required; run app with sudo."))
            else:
                self._write_async(self.pk_out, "  ⚠ " + T(" sudo      sudo  .", "sudo password required; run app with sudo."))
            return
        self._write_async(self.pk_out, "  ⏳ " + T("  : ", "Installing: ") + ", ".join(missing))
        def _on_line(l):
            self._write_async(self.pk_out, l)
        def _finish(missing2):
            t0 = time.time()
            while runner.running and time.time() - t0 < 310:
                time.sleep(0.3)
            still = [t for t in missing2 if not self._pk_pkg_installed(t, pm)]
            if still:
                self._write_async(self.pk_out, "  ⚠ " + T("      : ", "Not installed; maybe wrong name: ") + ", ".join(still))
            else:
                self._write_async(self.pk_out, "  ✅ " + T("    .", "Installed successfully."))
        if not runner.run(inst + missing, _on_line, timeout=300):
            self._write_async(self.pk_out, "  ⚠ " + T("   ...", "Another install is still running; try again in a moment."))
            return
        threading.Thread(target=_finish, args=(missing,), daemon=True).start()

    def _sysmon_refresh(self):
        lines = []
        try:
            with open("/proc/loadavg") as f:
                ld = f.read().split()
            lines.append("  CPU Load: %s %s %s" % (ld[0], ld[1], ld[2]))
        except Exception:
            pass
        try:
            _, o = run_cmd(["free", "-h"], 5)
            for l in o.splitlines():
                if l.startswith("Mem:"):
                    p = l.split()
                    lines.append("  RAM: %s / %s (free: %s)" % (p[2], p[1], p[3]))
        except Exception:
            pass
        try:
            _, o = run_cmd(["df", "-h", "/"], 5)
            for l in o.splitlines():
                if "/" in l and "%" in l:
                    p2 = l.split()
                    lines.append("  Total disk: %s" % p2[1])
                    lines.append("  Used: %s" % p2[2])
                    lines.append("  Free: %s" % p2[3])
        except Exception:
            pass
        try:
            _, o = run_cmd(["uptime", "-p"], 5)
            if o.strip():
                lines.append("  Uptime: %s" % o.strip())
        except Exception:
            pass
        subnet, my_ip, gw = get_subnet_info()
        lines.append("  IP: %s" % (my_ip or "?"))
        lines.append("  Gateway: %s" % (gw or "?"))
        if hasattr(self, 'sm_out'):
            _lines_extra = []
            try:
                _rc_up, _out_up = run_cmd(["uptime", "-p"], 5)
                if _out_up.strip():
                    _lines_extra.append(self._wl_T(' ⏱ : ', ' ⏱ Uptime: ') + _out_up.strip())
            except Exception:
                pass
            try:
                _sub_x, _ip_x, _gw_x = get_subnet_info()
                _lines_extra += ["  🌐 IP:        %s" % (_ip_x or "?"),
                                 "  🌐 Gateway:   %s" % (_gw_x or "?"), ""]
            except Exception:
                pass
            for _e in _lines_extra:
                lines.append(_e)
            self._write_async(self.sm_out, "\n".join(lines), clear=True)

    def _ct_file(self):
        return os.path.expanduser("~/.toolbox_custom_tools.json")




    def _ct_load(self):
        try:
            with open(self._ct_file(), encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _ct_save(self, tools):
        with open(self._ct_file(), "w", encoding='utf-8') as f:
            json.dump(tools, f, ensure_ascii=False, indent=2)

    def _ct_find(self, tid):
        for t in self._ct_load():
            if t.get("id") == tid:
                return t
        return None














    def _build_passforge(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["passforge"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text="Password Forge",
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        f1 = tk.Frame(page, bg=TH["bg"])
        f1.pack(pady=5)
        tk.Label(f1, text=self._wl_T(":", "Length:"), bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.pf_len = tk.Entry(f1, bg=TH["card"], fg=TH["text"], width=5,
                              insertbackground=TH["text"])
        self.pf_len.pack(side="left", padx=3)
        self.pf_len.insert(0, "16")
        tk.Label(f1, text="Count:", bg=TH["bg"], fg=TH["text"]).pack(side="left", padx=(15, 0))
        self.pf_cnt = tk.Entry(f1, bg=TH["card"], fg=TH["text"], width=5,
                              insertbackground=TH["text"])
        self.pf_cnt.pack(side="left", padx=3)
        self.pf_cnt.insert(0, "5")
        f2 = tk.Frame(page, bg=TH["bg"])
        f2.pack(pady=5)
        self.pf_lower = tk.BooleanVar(value=True)
        self.pf_upper = tk.BooleanVar(value=True)
        self.pf_digits = tk.BooleanVar(value=True)
        self.pf_symbols = tk.BooleanVar(value=True)
        self.pf_phrase = tk.BooleanVar(value=False)
        for var, txt in [(self.pf_lower, "a-z"), (self.pf_upper, "A-Z"),
                         (self.pf_digits, "0-9"), (self.pf_symbols, "#$@"),
                         (self.pf_phrase, "Phrase mode")]:
            tk.Checkbutton(f2, text=txt, variable=var, bg=TH["bg"], fg=TH["text"],
                          selectcolor=TH["card"]).pack(side="left", padx=5)
        f3 = tk.Frame(page, bg=TH["bg"])
        f3.pack(pady=8)
        tk.Button(f3, text="Generate", command=self._pf_start,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        tk.Button(f3, text="Copy Last", command=self._pf_copy,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=5)
        self.pf_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                             font=("Courier", 11), state="disabled",
                             wrap="word", padx=10, pady=10)
        self.pf_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _pf_start(self):
        threading.Thread(target=self._passforge_worker, daemon=True).start()

    def _pf_copy(self):
        last = getattr(self, "pf_last", None)
        if last:
            self.root.clipboard_clear()
            self.root.clipboard_append(last[-1])
            self._write(self.pf_out, "  Copied: %s" % last[-1])

    def _build_wordlist(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["wordlist"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text="Wordlist Builder",
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        f1 = tk.Frame(page, bg=TH["bg"])
        f1.pack(fill="x", padx=40, pady=2)
        tk.Label(f1, text="Base words (comma):", bg=TH["bg"], fg=TH["text"],
                font=TH["font_s"]).pack(anchor="w")
        self.wl_base = tk.Entry(f1, bg=TH["card"], fg=TH["text"],
                               insertbackground=TH["text"])
        self.wl_base.pack(fill="x")
        self.wl_base.insert(0, "ali,reza,mamad")
        f2 = tk.Frame(page, bg=TH["bg"])
        f2.pack(fill="x", padx=40, pady=2)
        tk.Label(f2, text="Prefixes (comma):", bg=TH["bg"], fg=TH["text"],
                font=TH["font_s"]).pack(anchor="w")
        self.wl_pre = tk.Entry(f2, bg=TH["card"], fg=TH["text"],
                              insertbackground=TH["text"])
        self.wl_pre.pack(fill="x")
        f3 = tk.Frame(page, bg=TH["bg"])
        f3.pack(fill="x", padx=40, pady=2)
        tk.Label(f3, text="Suffixes (comma):", bg=TH["bg"], fg=TH["text"],
                font=TH["font_s"]).pack(anchor="w")
        self.wl_suf = tk.Entry(f3, bg=TH["card"], fg=TH["text"],
                              insertbackground=TH["text"])
        self.wl_suf.pack(fill="x")
        f4 = tk.Frame(page, bg=TH["bg"])
        f4.pack(pady=4)
        tk.Label(f4, text="Digits:", bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.wl_d1 = tk.Entry(f4, bg=TH["card"], fg=TH["text"], width=6,
                             insertbackground=TH["text"])
        self.wl_d1.pack(side="left", padx=3)
        self.wl_d1.insert(0, "0")
        tk.Label(f4, text="to", bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.wl_d2 = tk.Entry(f4, bg=TH["card"], fg=TH["text"], width=6,
                             insertbackground=TH["text"])
        self.wl_d2.pack(side="left", padx=3)
        self.wl_d2.insert(0, "99")
        self.wl_digits = tk.BooleanVar(value=True)
        self.wl_upper = tk.BooleanVar(value=False)
        tk.Checkbutton(f4, text="+digits", variable=self.wl_digits, bg=TH["bg"],
                      fg=TH["text"], selectcolor=TH["card"]).pack(side="left", padx=5)
        tk.Checkbutton(f4, text="upper/cap", variable=self.wl_upper, bg=TH["bg"],
                      fg=TH["text"], selectcolor=TH["card"]).pack(side="left", padx=5)
        f5 = tk.Frame(page, bg=TH["bg"])
        f5.pack(pady=6)
        tk.Button(f5, text="Generate", command=self._wl_start,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        tk.Button(f5, text="Save to file", command=self._wl_save,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=5)
        self.wl_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                             font=("Courier", 10), state="disabled",
                             wrap="none", padx=10, pady=10)
        self.wl_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _wl_start(self):
        threading.Thread(target=self._wl_worker, daemon=True).start()

    def _wl_worker(self):
        LIMIT = 100000
        out = []
        bases = [w.strip() for w in self.wl_base.get().split(",") if w.strip()]
        pres = [w.strip() for w in self.wl_pre.get().split(",") if w.strip()] or [""]
        sufs = [w.strip() for w in self.wl_suf.get().split(",") if w.strip()] or [""]
        try:
            d1 = int(_digits_en(self.wl_d1.get()).strip() or 0)
            d2 = int(_digits_en(self.wl_d2.get()).strip() or 99)
        except Exception:
            d1, d2 = 0, 99
        if d2 < d1:
            d1, d2 = d2, d1
        if d2 - d1 > 9999:
            d2 = d1 + 9999
        with_digits = self.wl_digits.get()
        upper = self.wl_upper.get()
        done = False
        for b in bases:
            vs = [b]
            if upper:
                vs += [b.upper(), b.capitalize()]
            for v in vs:
                for pre in pres:
                    for suf in sufs:
                        out.append(pre + v + suf)
                        if with_digits:
                            for d in range(d1, d2 + 1):
                                out.append(pre + v + str(d) + suf)
                                if len(out) >= LIMIT:
                                    done = True
                                    break
                        if len(out) >= LIMIT:
                            done = True
                            break
                    if done:
                        break
                if done:
                    break
            if done:
                break
        self.wl_list = out
        preview = "\n".join("  " + w for w in out[:100])
        msg = "\n  Generated: %d words%s\n\n%s\n" % (
            len(out), " (limit reached)" if done else "", preview)
        self._write_async(self.wl_out, msg, clear=True)

    def _wl_save(self):
        lst = getattr(self, "wl_list", None)
        if not lst:
            return
        from tkinter import filedialog
        f = filedialog.asksaveasfilename(defaultextension=".txt",
                                         filetypes=[("Text", "*.txt")],
                                         initialfile="wordlist.txt")
        if not f:
            return
        try:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lst) + "\n")
            self._write(self.wl_out, "  Saved: %s (%d lines)" % (f, len(lst)))
        except Exception as e:
            self._write(self.wl_out, "  Error: %s" % e)

    def _build_hostscan(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["hostscan"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text="Host Scanner (network devices)",
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        subnet, my_ip, gw = get_subnet_info()
        info = "  %s (%s)   %s (%s)   %s" % (
            "◄ You", my_ip or "?", "◄ Router", gw or "?", subnet or "?")
        tk.Label(page, text=info, bg=TH["bg"], fg=TH["dim"],
                font=TH["font_s"]).pack()
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=8)
        tk.Button(bf, text=self._wl_T("🖧   ", "🖧 Unified Host Scan"), command=self._hs_unified,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=4)
        tk.Button(bf, text="Stop", command=self._hs_stop,
                 bg=TH["red"], fg="#fff").pack(side="left", padx=4)
        self.hs_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                             font=("Courier", 11), state="disabled",
                             wrap="word", padx=10, pady=10)
        self.hs_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _hs_stop(self):
        if not getattr(self, "_hs_busy", False):
            self._write(self.hs_out, "\n⏹ " + self.T("    ", "No scan running"), True)
            return
        self._hs_stop_flag = True
        p = getattr(self, "_hs_proc", None)
        if p:
            try:
                p.terminate()
            except Exception:
                pass
        self._write(self.hs_out, "\n⏹ " + self.T("   ...", "Stopping scan..."), True)



    def _hs_unified(self):
        if getattr(self, "_hs_busy", False):
            return
        self._hs_busy = True
        self._hs_stop_flag = False
        threading.Thread(target=self._hs_unified_done, daemon=True).start()

    def _hs_unified_done(self):
        try:
            self._hs_unified_worker()
        finally:
            self._hs_busy = False

    def _hs_unified_worker(self):
        out = self.hs_out
        try:
            _, my_ip, gw = get_subnet_info()
        except Exception:
            my_ip, gw = "", ""
        base = ".".join((my_ip or "192.168.1.0").split(".")[:3]) + "."
        hosts = {}

        def add(ip, mac=None, name=None):
            h = hosts.setdefault(ip, {"mac": None, "name": None})
            if mac and not h["mac"]: h["mac"] = mac
            if name and not h["name"]: h["name"] = name

        def read_arp():
            try:
                with open("/proc/net/arp", encoding="utf-8") as f:
                    for r in f.readlines()[1:]:
                        p = r.split()
                        if len(p) >= 4 and p[3] != "00:00:00:00:00:00":
                            add(p[0], p[3])
            except Exception:
                pass

        self._write_async(out, "\n🖧 " + self._wl_T("  ", "Unified host scan"), clear=True)

        # ── 1) ARP table ──
        self._write_async(out, "⏳ [1/3] " + self._wl_T("   ARP table...", "Reading ARP table..."))
        read_arp()

        self._write_async(out, "⏳ [2/3] " + self._wl_T("   Ping sweep...", "Running ping sweep..."))
        def _ping(ip):
            if getattr(self, "_hs_stop_flag", False):
                return None
            try:
                r = subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True, timeout=2)
                return ip if r.returncode == 0 else None
            except Exception:
                return None
        try:
            import concurrent.futures as _cf
            with _cf.ThreadPoolExecutor(max_workers=64) as ex:
                for ip in list(ex.map(_ping, [base + str(i) for i in range(1, 255)], timeout=45)):
                    if ip: add(ip)
        except Exception:
            pass
        read_arp()

        if getattr(self, "_hs_stop_flag", False):
            self._hs_finish(hosts, True)
            return

        # ── 3) Nmap ──
        if shutil.which("nmap"):
            self._write_async(out, "⏳ [3/3] " + self._wl_T("   Nmap...", "Running Nmap..."))
            try:
                p = subprocess.Popen(["nmap", "-sn", base + "0/24"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                self._hs_proc = p
                try:
                    out_txt, _ = p.communicate(timeout=90)
                except subprocess.TimeoutExpired:
                    p.kill(); out_txt, _ = p.communicate()
                finally:
                    self._hs_proc = None
                cur = None
                for ln in (out_txt or "").splitlines():
                    if "Nmap scan report for" in ln:
                        if "(" in ln and ")" in ln:
                            cur = ln.split("(")[1].split(")")[0]
                            add(cur, name=ln.split(" for ")[1].split(" (")[0].strip())
                        else:
                            cur = ln.split()[-1]; add(cur)
                    elif ln.strip().startswith("MAC Address:") and cur:
                        ps = ln.split()
                        if len(ps) >= 3: add(cur, mac=ps[2])
            except Exception:
                pass
        else:
            self._write_async(out, "⏳ [3/3] " + self._wl_T("Nmap   -  .", "Nmap not installed - skipped."))

        if getattr(self, "_hs_stop_flag", False):
            self._hs_finish(hosts, True)
            return

        try:
            hmap = {}
            with open("/etc/hosts", encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if ln and not ln.startswith("#"):
                        ps = ln.split()
                        if len(ps) > 1: hmap[ps[0]] = ps[1]
        except Exception:
            hmap = {}
        unnamed = []
        for ip, h in hosts.items():
            if ip == my_ip:
                try: h["name"] = socket.gethostname()
                except Exception: pass
            elif ip == gw:
                h["name"] = self._wl_T("", "Router")
            elif ip in hmap:
                h["name"] = hmap[ip]
            else:
                unnamed.append(ip)
        if unnamed and shutil.which("avahi-resolve"):
            try:
                r = subprocess.run(["avahi-resolve", "-a"] + unnamed[:16], capture_output=True, text=True, timeout=5)
                for ln in (r.stdout or "").splitlines():
                    if "\t" in ln:
                        ip2, nm = ln.split("\t", 1)
                        if ip2 in hosts and nm.strip(): hosts[ip2]["name"] = nm.strip()
            except Exception:
                pass

        self._hs_finish(hosts, False)

    def _hs_finish(self, hosts, stopped):
        out = self.hs_out
        if stopped:
            hdr = "⏹ " + self._wl_T("  ", "Scan stopped")
        else:
            hdr = "✅ " + self._wl_T("  ", "Scan complete")
        L = ["", hdr + " - " + str(len(hosts)) + " " + self._wl_T(" ", "live hosts found"),
             "  " + "─" * 36]
        for i, ip in enumerate(sorted(hosts, key=lambda x: int(x.split(".")[-1]) if x.count(".") == 3 else 0), 1):
            h = hosts[ip]
            name = h["name"] or ""
            if not name and h["mac"]:
                name = self._wf_vendor(h["mac"]) or ""
            line = " [%d] %s" % (i, ip)
            if name: line += "  |  " + "Name" + ": " + name
            if h["mac"]: line += "  |  MAC: " + h["mac"]
            L.append(line)
        L.append("  " + "─" * 36)
        self._write_async(out, "\n".join(L))




    def _hs_name(self, ip):
        """     : hosts / mDNS / NetBIOS / PTR"""
        try:
            _, my_ip, gw = get_subnet_info()
        except Exception:
            my_ip, gw = None, None
        if ip == my_ip:
            try:
                return socket.gethostname()
            except Exception:
                pass
        if ip == gw:
            return self._wl_T("", "Router")
        try:
            with open("/etc/hosts", encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith("#"):
                        continue
                    ps = ln.split()
                    if ps and ps[0] == ip and len(ps) > 1:
                        return ps[1]
        except Exception:
            pass
        res = []
        def _gh():
            try:
                res.append(socket.gethostbyaddr(ip)[0])
            except Exception:
                pass
        t = threading.Thread(target=_gh, daemon=True)
        t.start(); t.join(2)
        if res and res[0] and res[0] != ip:
            return res[0]
        if shutil.which("avahi-resolve"):
            try:
                r = subprocess.run(["avahi-resolve", "-a", ip], capture_output=True, text=True, timeout=3)
                out = (r.stdout or "").strip()
                if out and "\t" in out:
                    nm = out.split("\t")[-1].strip()
                    if nm:
                        return nm
            except Exception:
                pass
        if shutil.which("nmblookup"):
            try:
                r = subprocess.run(["nmblookup", "-A", ip], capture_output=True, text=True, timeout=4)
                m = re.search(r"^\s*([A-Za-z0-9_.-]+)\s*<00>", r.stdout or "", re.M)
                if m:
                    return m.group(1)
            except Exception:
                pass
        return ""



    def _build_nmapx(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["nmap"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text="Nmap Port Scanner",
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        row = tk.Frame(page, bg=TH["bg"])
        row.pack(fill="x", padx=40)
        self.nm_entry = tk.Entry(row, bg=TH["card"], fg=TH["text"],
                                 insertbackground=TH["text"], font=TH["font"])
        self.nm_entry.pack(side="left", fill="x", expand=True, padx=5)
        subnet, my_ip, gw = get_subnet_info()
        self.nm_entry.insert(0, my_ip or "scanme.nmap.org")
        mf = tk.Frame(page, bg=TH["bg"])
        mf.pack(pady=6)
        self.nm_mode = tk.StringVar(value="quick")
        for val, txt in [("quick", "🚀 Fast"), ("agg", "⚔ Full aggressive"),
                         ("vuln", "🩺 Vulnerability"), ("all", "🌊 All ports"),
                         ("syn", "👻 Stealth SYN")]:
            tk.Radiobutton(mf, text=txt, variable=self.nm_mode, value=val,
                          bg=TH["bg"], fg=TH["text"], selectcolor=TH["card"],
                          font=TH["font_s"]).pack(side="left", padx=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=4)
        tk.Button(bf, text="Run", command=self._nm_start,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        tk.Button(bf, text="Stop", command=self._nm_stop,
                 bg=TH["red"], fg="#fff").pack(side="left", padx=5)
        self.nm_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                             font=("Courier", 11), state="disabled",
                             wrap="word", padx=10, pady=10)
        self.nm_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _nm_stop(self):
        AsyncCommandRunner.get("nmap").stop()

    def _nm_start(self):
        t = self.nm_entry.get().strip()
        if not t:
            return
        if not shutil.which("nmap"):
            self._write(self.nm_out, "  nmap not installed.\n  Install: sudo apt install nmap", True)
            return
        mode = self.nm_mode.get()
        extra = self.prefs.get("nmapargs", "").split()
        args = {"quick": ["nmap", "-F", "-T4"] + extra + [t],
                "agg": ["nmap", "-A", "-T4"] + extra + [t],
                "vuln": ["nmap", "--script", "vuln", "-T4"] + extra + [t],
                "all": ["nmap", "-p-", "-T4"] + extra + [t],
                "syn": ["nmap", "-sS", "-T4"] + extra + [t]}.get(mode, ["nmap", "-T4", t])
        self._write(self.nm_out, "  Running: %s" % " ".join(args), True)
        runner = AsyncCommandRunner.get("nmap")
        runner.run(args, lambda l: self._write_async(self.nm_out, l), timeout=600)

    def _build_sysmon(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["sysmon"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text="System Monitor",
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T("", "Refresh"), command=self._sm_start,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        self.sm_auto = tk.BooleanVar(value=False)
        tk.Checkbutton(bf, text="Auto (5s)", variable=self.sm_auto,
                      command=self._sm_loop, bg=TH["bg"], fg=TH["text"],
                      selectcolor=TH["card"]).pack(side="left", padx=5)
        self.sm_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                             font=("Courier", 11), state="disabled",
                             wrap="word", padx=10, pady=10)
        self.sm_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _sm_start(self):
        threading.Thread(target=self._sysmon_refresh, daemon=True).start()

    def _sm_loop(self):
        if self.sm_auto.get():
            self._sm_tick()

    def _sm_tick(self):
        if not self.sm_auto.get():
            return
        self._sm_start()
        self.root.after(5000, self._sm_tick)

    def _build_custom(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["forge"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self.T("my_tools"),
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent2"]).pack(pady=10)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text="+ " + self.T("new_tool"), command=self._fe_open_new,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        tk.Button(bf, text=self._wl_T("", "Refresh"), command=self._forge_fill,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=5)
        self.fg_list = tk.Frame(page, bg=TH["bg"])
        self.fg_list.pack(fill="both", expand=True, padx=40, pady=10)
        self._forge_fill()

    def _forge_fill(self):
        for w in self.fg_list.winfo_children():
            w.destroy()
        tools = self._ct_load()
        if not tools:
            tk.Label(self.fg_list, text=self.T("no_tools"),
                    bg=TH["bg"], fg=TH["dim"], font=TH["font"]).pack(pady=30)
            return
        for t in tools:
            row = tk.Frame(self.fg_list, bg=TH["card"], padx=10, pady=8,
                          highlightbackground=TH["border"], highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=t.get("name", "?"), bg=TH["card"], fg=TH["text"],
                    font=TH["font_b"]).pack(side="left")
            tk.Label(row, text="%d steps" % len(t.get("steps", [])),
                    bg=TH["card"], fg=TH["dim"], font=TH["font_s"]).pack(side="left", padx=10)
            tk.Button(row, text=self.T("delete"),
                     command=lambda tid=t.get("id"): self._ct_delete(tid),
                     bg=TH["red"], fg="#fff").pack(side="right", padx=3)
            tk.Button(row, text=self.T("edit"),
                     command=lambda tid=t.get("id"): self._fe_open_edit(tid),
                     bg=TH["card"], fg=TH["accent"]).pack(side="right", padx=3)
            tk.Button(row, text=self.T("run"),
                     command=lambda tid=t.get("id"): self._ct_open_run(tid),
                     bg=TH["green"], fg="#000").pack(side="right", padx=3)

    def _ct_delete(self, tid):
        tools = [t for t in self._ct_load() if t.get("id") != tid]
        self._ct_save(tools)
        self._forge_fill()

    def _fe_open_new(self):
        self._fe_open(None)

    def _fe_open_edit(self, tid):
        self._fe_open(self._ct_find(tid))

    def _fe_open(self, tool):
        name = "forge_edit"
        if name in self.pages:
            del self.pages[name]
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages[name] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back",
                 command=lambda: (self._forge_fill(), self.show_page("forge")),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        title = self.T("edit") if tool else self.T("new_tool")
        tk.Label(page, text="Tool Forge - %s" % title,
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent2"]).pack(pady=5)
        f1 = tk.Frame(page, bg=TH["bg"])
        f1.pack(fill="x", padx=40, pady=2)
        tk.Label(f1, text="🏷 Tool name:", bg=TH["bg"], fg=TH["text"],
                font=TH["font_s"]).pack(anchor="w")
        self.fe_name = tk.Entry(f1, bg=TH["card"], fg=TH["text"],
                               insertbackground=TH["text"])
        self.fe_name.pack(fill="x")
        if tool:
            self.fe_name.insert(0, tool.get("name", ""))
        f2 = tk.Frame(page, bg=TH["bg"])
        f2.pack(fill="x", padx=40, pady=2)
        tk.Label(f2, text="🔤 Variable (name=value, comma-separated) -> use ${name} in commands",
                bg=TH["bg"], fg=TH["accent"], font=TH["font_s"]).pack(anchor="w")
        self.fe_vars = tk.Entry(f2, bg=TH["card"], fg=TH["text"],
                               insertbackground=TH["text"])
        self.fe_vars.pack(fill="x")
        if tool:
            vs = ", ".join("%s=%s" % (k, v) for k, v in tool.get("vars", {}).items())
            self.fe_vars.insert(0, vs)
        var_bar = tk.Frame(page, bg=TH["bg"])
        var_bar.pack(fill="x", padx=40, pady=(8, 0))
        tk.Label(var_bar, text="⚙ Steps (use ${varname} in commands):", bg=TH["bg"],
                fg=TH["text"], font=TH["font_s"]).pack(side="left")
        tk.Button(var_bar, text="📖 Guide", command=self._fe_var_guide,
                 bg=TH["accent"], fg="#000").pack(side="left", padx=6)
        tk.Button(var_bar, text="➕ Insert ${var}", command=self._fe_insert_var,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        tk.Button(var_bar, text="🔍 Check vars", command=self._fe_check_vars,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        self.fe_steps = tk.Frame(page, bg=TH["bg"])
        self.fe_steps.pack(fill="both", expand=True, padx=40, pady=5)
        self.fe_step_rows = []
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text="+ " + self.T("add_step"), command=self._fe_add_row,
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=5)
        tk.Button(bf, text=self.T("save"), command=self._fe_save,
                 bg=TH["green"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        self.fe_tool_id = tool.get("id") if tool else None
        if tool:
            for s in tool.get("steps", []):
                self._fe_add_row(s.get("cmd", ""), s.get("timeout", 120))
        else:
            self._fe_add_row()
        self.show_page(name)

    def _fe_add_row(self, cmd="", timeout=120):
        row = tk.Frame(self.fe_steps, bg=TH["bg2"], padx=5, pady=3)
        row.pack(fill="x", pady=2)
        e = tk.Entry(row, bg=TH["card"], fg=TH["text"],
                    insertbackground=TH["text"], font=("Courier", 10))
        e.pack(side="left", fill="x", expand=True, padx=3)
        e.insert(0, cmd)
        e.bind("<FocusIn>", lambda ev, en=e: setattr(self, "_fe_last_entry", en))
        self._fe_last_entry = e
        t = tk.Entry(row, bg=TH["card"], fg=TH["text"], width=6,
                    insertbackground=TH["text"])
        t.pack(side="left", padx=3)
        t.insert(0, str(timeout))
        def _del(r=row):
            r.destroy()
            self.fe_step_rows = [x for x in self.fe_step_rows if x[0] is not r]
        tk.Button(row, text="X", command=_del, bg=TH["red"], fg="#fff").pack(side="left")
        self.fe_step_rows.append((row, e, t))

    def _fe_var_guide(self):
        """Guide: how Forge variables work."""
        w = tk.Toplevel(self.root)
        w.title("Variable Guide")
        w.geometry("680x520")
        w.configure(bg=TH["bg"])
        sb = tk.Scrollbar(w)
        sb.pack(side="right", fill="y")
        txt = tk.Text(w, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                      wrap="word", padx=14, pady=12, yscrollcommand=sb.set)
        txt.pack(fill="both", expand=True)
        sb.configure(command=txt.yview)
        guide = """=== How Variables Work ===

[1] DEFINE
    In the "Variable" box write:  name=value
    Separate multiple vars with commas:
        target=8.8.8.8, port=443, out=result.txt

[2] USE IN COMMANDS
    Anywhere in a Step, write exactly:  ${name}
        nmap -p ${port} ${target}
        ping -c 3 ${target}
    On Run they are replaced automatically:
        nmap -p 443 8.8.8.8

[3] RULES
    * Name: letters/digits/underscore only
        OK:  target, my_ip2, PORT_1
        BAD: my ip, target-ip, 1st
    * No spaces inside ${ }:  ${target}  not  ${ target }
    * Values are inserted as-is; quote them in the command if they
      contain spaces:
        msg=hello world   ->   echo "${msg}"
    * An undefined ${var} stays literal (no error, but won't work)
    * The same var can be used many times, across multiple Steps

[4] BUTTONS
    Insert ${var}:
       Click inside a command box first (that sets the cursor),
       then press this button -> ${name} is inserted at the cursor.
       It then asks if you want to define its value right now.
    Check vars:
       Verifies every ${var} used in Steps is defined in the
       Variable box; missing ones are listed with a warning.

[5] FULL EXAMPLE
    Variable box:
        host=scanme.nmap.org, top=20
    Step 1:   ping -c 2 ${host}                 timeout: 30
    Step 2:   nmap --top-ports ${top} ${host}   timeout: 300
    Then: Save -> open the tool in Forge list -> press Run.

[6] SUDO
    Write sudo commands normally:  sudo nmap ${target}
    When running, enter your password in the key field on the Run page.
"""
        txt.insert("1.0", guide)
        txt.configure(state="disabled")

    def _fe_insert_var(self):
        """Insert ${name} at cursor of last-focused step command box."""
        from tkinter import simpledialog, messagebox
        e = getattr(self, "_fe_last_entry", None)
        try:
            if e is None or not e.winfo_exists():
                e = self.fe_step_rows[-1][1] if self.fe_step_rows else None
        except Exception:
            e = None
        if e is None:
            messagebox.showinfo("Insert", "Click inside a command box first.")
            return
        name = simpledialog.askstring("Variable",
            "Variable name (e.g. target, port, out_file):", parent=self.root)
        if not name:
            return
        name = re.sub(r"[^A-Za-z0-9_]", "", name.strip())
        if not name:
            messagebox.showwarning("Variable",
                "Invalid name! Only letters, digits and underscore.")
            return
        try:
            e.insert(tk.INSERT, "${%s}" % name)
            e.focus_set()
        except Exception:
            pass
        defined = [p.split("=", 1)[0].strip()
                   for p in self.fe_vars.get().split(",") if "=" in p]
        if name not in defined:
            if messagebox.askyesno("Add variable",
                    "Define its value now?\n\n%s=?" % name):
                val = simpledialog.askstring("Value",
                                             "Value for %s:" % name,
                                             parent=self.root)
                add = "%s=%s" % (name, val if val is not None else "")
                cur = self.fe_vars.get().strip().rstrip(",")
                self.fe_vars.delete(0, "end")
                self.fe_vars.insert(0, (cur + ", " + add) if cur else add)

    def _fe_check_vars(self):
        """Verify every ${var} used in steps is defined in the vars box."""
        from tkinter import messagebox
        defined = set()
        for part in self.fe_vars.get().split(","):
            if "=" in part:
                defined.add(part.split("=", 1)[0].strip())
        used = {}
        for row, e, t in list(getattr(self, "fe_step_rows", [])):
            try:
                for m in re.findall(r"\$\{([A-Za-z0-9_]+)\}", e.get()):
                    used[m] = used.get(m, 0) + 1
            except Exception:
                pass
        if not used:
            messagebox.showinfo("Check vars", "No ${var} used in any step.")
            return
        missing = sorted(k for k in used if k not in defined)
        L = ["Defined: " + (", ".join(sorted(defined)) or "-"),
             "Used:    " + ", ".join("%s (%dx)" % (k, v)
                                     for k, v in sorted(used.items()))]
        if missing:
            L += ["", "MISSING: " + ", ".join(missing),
                  "Add them like:  name=value"]
            messagebox.showwarning("Check vars", "\n".join(L))
        else:
            L += ["", "All variables are defined."]
            messagebox.showinfo("Check vars", "\n".join(L))

    def _fe_save(self):
        nm = self.fe_name.get().strip()
        if not nm:
            return
        vars_d = {}
        for part in self.fe_vars.get().split(","):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                vars_d[k.strip()] = v.strip()
        steps = []
        for row, e, t in self.fe_step_rows:
            c = e.get().strip()
            if not c:
                continue
            try:
                to = int(_digits_en(t.get()).strip() or 120)
            except Exception:
                to = 120
            steps.append({"cmd": c, "timeout": to})
        tools = self._ct_load()
        tid = self.fe_tool_id or ("t%d" % int(time.time()))
        existing = None
        for t2 in tools:
            if t2.get("id") == tid:
                existing = t2
        if existing:
            existing["name"] = nm
            existing["vars"] = vars_d
            existing["steps"] = steps
        else:
            tools.append({"id": tid, "name": nm, "vars": vars_d, "steps": steps})
        self._ct_save(tools)
        self._forge_fill()
        self.show_page("forge")

    def _ct_open_run(self, tid):
        t = self._ct_find(tid)
        if not t:
            return
        name = "ct_run"
        if name in self.pages:
            del self.pages[name]
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages[name] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back",
                 command=lambda: (self._forge_fill(), self.show_page("forge")),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=t.get("name", "?"),
                font=TH["font_h"], bg=TH["bg"], fg=TH["green"]).pack(pady=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self.T("run"), command=lambda tid=tid: self._ct_run(tid),
                 bg=TH["green"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        tk.Button(bf, text=self.T("stop"), command=self._ct_stop,
                 bg=TH["red"], fg="#fff").pack(side="left", padx=5)
        sf = tk.Frame(page, bg=TH["bg"])
        sf.pack(pady=3)
        tk.Label(sf, text=self._wl_T("🔐  sudo ():", " sudo password (optional):"),
                bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack(side="left")
        self.ct_sudo_var = tk.StringVar()
        tk.Entry(sf, textvariable=self.ct_sudo_var, show="*", width=16,
                bg=TH["card"], fg=TH["text"], insertbackground=TH["text"]).pack(side="left", padx=4)
        out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                     font=("Courier", 11), state="disabled",
                     wrap="word", padx=10, pady=10)
        out.pack(fill="both", expand=True, padx=40, pady=10)
        self._ct_out_map[tid] = out
        self.show_page(name)

    def _safe_unlink(self, p):
        try:
            os.unlink(p)
        except Exception:
            pass

    def _ct_run(self, tid=None):
        """Run a custom tool: executes saved steps sequentially with live output."""
        if tid is None:
            tid = getattr(self, "cr_id", None)
        if not tid:
            return
        t = self._ct_find(tid)
        if not t:
            return
        out = self._ct_out_map.get(tid)
        if out is None:
            return
        try:
            if not out.winfo_exists():
                return
        except Exception:
            return
        steps = t.get("steps", []) or []
        if not steps:
            self._write_async(out, "  \u26a0 " + self.T("No steps saved"), clear=True)
            return
        if getattr(self, "_ct_busy", False):
            return
        self._ct_busy = True
        self._ct_stop_flag = False
        try:
            sudo_pw = self.ct_sudo_var.get().strip()
        except Exception:
            sudo_pw = ""

        def _worker():
            import shlex
            import tempfile
            try:
                vars_d = t.get("vars", {}) or {}
                self._write_async(out, "  \u25b6 Running: %s (%d steps)"
                                  % (t.get("name", "?"), len(steps)), clear=True)
                for i, s in enumerate(steps, 1):
                    if getattr(self, "_ct_stop_flag", False):
                        self._write_async(out, "  \u23f9 " + self.T("Stopped"))
                        return
                    cmd = (s.get("cmd", "") or "").strip()
                    if not cmd:
                        continue
                    for k, v in vars_d.items():
                        cmd = cmd.replace("${%s}" % k, str(v))
                    try:
                        timeout = int(s.get("timeout", 120))
                    except Exception:
                        timeout = 120
                    _shp = None
                    if sudo_pw and cmd.lstrip().startswith("sudo "):
                        _rest = cmd.lstrip()[5:]
                        _fd2, _shp = tempfile.mkstemp(prefix="tb_ct_", suffix=".sh")
                        with os.fdopen(_fd2, "w") as _f2:
                            _f2.write("#!/bin/bash\necho %s | sudo -S %s\n" % (shlex.quote(sudo_pw), _rest))
                        os.chmod(_shp, 0o700)
                        threading.Timer(3.0, self._safe_unlink, args=(_shp,)).start()
                        cmd = "sudo -S " + _rest
                    self._write_async(out, "\n  \u2500\u2500 [%d/%d] %s \u2500\u2500"
                                      % (i, len(steps), cmd))
                    p = None
                    try:
                        p = subprocess.Popen((["bash", _shp] if _shp else ["bash", "-c", cmd]),
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT,
                                             text=True, bufsize=1,
                                             start_new_session=True)
                        self._ct_proc = p
                        for line in p.stdout:
                            if getattr(self, "_ct_stop_flag", False):
                                break
                            self._write_async(out, "  " + line.rstrip("\n"))
                        try:
                            p.wait(timeout=timeout)
                        except subprocess.TimeoutExpired:
                            try:
                                os.killpg(os.getpgid(p.pid), 15)
                            except Exception:
                                try: p.kill()
                                except Exception: pass
                            self._write_async(out, "  \u26a0 TIMEOUT after %ds" % timeout)
                        rc = p.returncode
                        if getattr(self, "_ct_stop_flag", False):
                            try: p.kill()
                            except Exception: pass
                            self._write_async(out, "  \u23f9 " + self.T("Stopped"))
                            return
                        if rc != 0:
                            self._write_async(out, "  \u26a0 Exit code: %s" % rc)
                    except Exception as e:
                        self._write_async(out, "  \u274c %s" % e)
                        return
                    finally:
                        self._ct_proc = None
                self._write_async(out, "\n  \u2705 " + self.T("All steps completed"))
            finally:
                self._ct_busy = False
                self._ct_proc = None
        threading.Thread(target=_worker, daemon=True).start()

    def _ct_stop(self):
        self._ct_stop_flag = True
        p = getattr(self, "_ct_proc", None)
        if p:
            try:
                p.kill()
            except Exception:
                pass

    def _build_ipgeox(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["ipgeox"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text="IP / Domain Geolocation",
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        row = tk.Frame(page, bg=TH["bg"])
        row.pack(fill="x", padx=40)
        self.ig_entry = tk.Entry(row, bg=TH["card"], fg=TH["text"],
                                 insertbackground=TH["text"], font=TH["font"])
        self.ig_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.ig_entry.bind("<Return>", lambda e: self._ig_start())
        tk.Button(row, text=self._wl_T("", "Search"), command=self._ig_start,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T(" ", "My Local IP"), command=lambda: self._ig_quick("local"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        tk.Button(bf, text=self._wl_T(" ", "My Public IP"), command=lambda: self._ig_quick("public"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        tk.Button(bf, text=self._wl_T("  ", "Open Map"), command=self._ig_open_map,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=3)
        self.ig_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                             font=("Courier", 11), state="disabled",
                             wrap="char", padx=10, pady=10)
        self.ig_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _ig_quick(self, mode):
        if mode == "local":
            subnet, my_ip, gw = get_subnet_info()
            if my_ip:
                self.ig_entry.delete(0, "end")
                self.ig_entry.insert(0, my_ip)
                self._ig_start()
        else:
            threading.Thread(target=self._ig_get_public, daemon=True).start()

    def _ig_get_public(self):
        try:
            import urllib.request
            ip = urllib.request.urlopen("https://api.ipify.org", timeout=10).read().decode().strip()
            def _fill():
                self.ig_entry.delete(0, "end")
                self.ig_entry.insert(0, ip)
                self._ig_start()
            self.root.after(0, _fill)
        except Exception:
            self.root.after(0, lambda: self._write(self.ig_out, self._ig_lb(" ", "Could not get public IP"), True))

    def _ig_lb(self, f, e):
        return e
    def _ig_open_map(self):
        import webbrowser
        link = getattr(self, "_ig_maplink", None)
        if link:
            try:
                webbrowser.open(link)
                self._write(self.ig_out, "  🔗 " + self._ig_lb("     ✅", "Map opened in browser ✅"))
            except Exception as e:
                self._write(self.ig_out, "  ⚠ " + self._ig_lb("    : ", "Browser open error: ") + str(e))
            return
        q = self.ig_entry.get().strip()
        if q:
            self._write(self.ig_out, "  🔎 " + self._ig_lb("     ...", "Searching & opening map..."), True)
            self._ig_auto_open = True
            threading.Thread(target=self._ig_worker, args=(q,), daemon=True).start()
        else:
            self._write(self.ig_out, " ⚠ " + self._ig_lb(" ", "Enter an IP or domain first"))

    def _ig_start(self):
        q = self.ig_entry.get().strip()
        if not q:
            return
        threading.Thread(target=self._ig_worker, args=(q,), daemon=True).start()

    def _ig_worker(self, q):
        self._ig_maplink = None
        if isinstance(q, str):
            q0 = q.strip()
            if q0 and not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", q0):
                dom = q0.split("/")[2] if q0.startswith("http") else q0
                try:
                    rr = subprocess.run(["ping", "-c", "1", "-W", "2", dom],
                                        capture_output=True, text=True, timeout=8)
                    mm = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", rr.stdout)
                    if mm:
                        q = mm.group(1)
                except Exception:
                    pass
        import ipaddress
        import urllib.request
        import urllib.error
        self.root.after(0, lambda: self._write(self.ig_out, "  🔎 " + self._ig_lb(": ", "Searching: ") + q, True))
        target = q
        if not re.match(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$', q):
            try:
                target = socket.gethostbyname(q)
                t2 = target
                self.root.after(0, lambda: self._write(self.ig_out, " 🌐 " + self._ig_lb(" : ", "Resolved IP: ") + t2))
            except Exception:
                self.root.after(0, lambda: self._write(self.ig_out, self._ig_lb(" ", "Could not resolve domain")))
                return
        try:
            ipobj = ipaddress.ip_address(target)
        except Exception:
            self.root.after(0, lambda: self._write(self.ig_out, self._ig_lb(" ", "Invalid IP")))
            return
        if ipobj.is_private:
            fn = getattr(self, "_ig_local_phone", None)
            result = None
            if fn:
                try:
                    result = fn(target)
                except Exception:
                    result = None
            if not result:
                result = self._ig_local_basic(target)
            head = "  🏠 " + self._ig_lb(" : ", "Private/local IP - no geo data exists; local analysis:")
            self._ig_auto_open = False
            self.root.after(0, lambda: self._write(self.ig_out, head + "\n" + result))
            return

        def _fetch(url, timeout=10):
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ToolboxPro/1.0"})
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())

        def _parse(pname, raw):
            if pname == "ipwho.is":
                if raw.get("success") is not False:
                    conn = raw.get("connection") or {}
                    return {"ip": raw.get("ip", target), "country": raw.get("country"), "cc": raw.get("country_code"),
                            "region": raw.get("region"), "city": raw.get("city"), "zip": raw.get("postal"),
                            "lat": raw.get("latitude"), "lon": raw.get("longitude"), "tz": raw.get("timezone"),
                            "isp": conn.get("isp"), "org": conn.get("org"), "as": conn.get("asn")}
            elif pname == "geojs.io":
                if raw.get("country"):
                    return {"ip": raw.get("ip", target), "country": raw.get("country"), "cc": raw.get("country_code"),
                            "region": raw.get("region"), "city": raw.get("city"), "zip": raw.get("postal"),
                            "lat": raw.get("latitude"), "lon": raw.get("longitude"), "tz": raw.get("timezone"),
                            "isp": raw.get("organization"), "org": raw.get("organization"), "as": raw.get("asn")}
            elif pname == "ipapi.co":
                if raw.get("country_name") or raw.get("city"):
                    return {"ip": raw.get("ip", target), "country": raw.get("country_name"), "cc": raw.get("country_code"),
                            "region": raw.get("region"), "city": raw.get("city"), "zip": raw.get("postal"),
                            "lat": raw.get("latitude"), "lon": raw.get("longitude"), "tz": raw.get("timezone"),
                            "isp": raw.get("org"), "org": raw.get("org"), "as": raw.get("asn")}
            elif pname == "ip-api.com":
                if raw.get("status") == "success":
                    return {"ip": raw.get("query"), "country": raw.get("country"), "cc": raw.get("countryCode"),
                            "region": raw.get("regionName"), "city": raw.get("city"), "zip": raw.get("zip"),
                            "lat": raw.get("lat"), "lon": raw.get("lon"), "tz": raw.get("timezone"),
                            "isp": raw.get("isp"), "org": raw.get("org"), "as": raw.get("as")}
            return None

        provs = [
            ("ipwho.is", "https://ipwho.is/%s" % target, 10),
            ("geojs.io", "https://get.geojs.io/v1/ip/geo/%s.json" % target, 10),
            ("ipapi.co", "https://ipapi.co/%s/json/" % target, 10),
            ("ip-api.com", "http://ip-api.com/json/%s?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query" % target, 6),
        ]
        data = None
        errs = []
        for pname, purl, ptm in provs:
            try:
                d = _parse(pname, _fetch(purl, ptm))
                if d:
                    data = d
                    data["src"] = pname
                    break
                errs.append("%s: incomplete answer" % pname)
            except urllib.error.HTTPError as e:
                extra = " (rate limit)" if e.code == 429 else ""
                errs.append("%s: HTTP %s%s" % (pname, e.code, extra))
            except Exception as e:
                errs.append("%s: %s" % (pname, str(e)[:50]))
        if data is None:
            msg = ("  ⚠ " + self._ig_lb(" : ", "All geo providers failed:") + "\n" +
                   "\n".join("     - " + x for x in errs) + "\n" +
                   "  💡 " + self._ig_lb(" / ", "Check internet/VPN, then retry"))
            self.root.after(0, lambda: self._write(self.ig_out, msg))
            return
        lat = data.get("lat", "?")
        lon = data.get("lon", "?")
        maplink = ("https://www.google.com/maps?q=%s,%s" % (lat, lon))
        self._ig_maplink = maplink
        if getattr(self, "_ig_auto_open", False):
            self._ig_auto_open = False
            try:
                import webbrowser
                self.root.after(0, lambda ml=maplink: webbrowser.open(ml))
            except Exception:
                pass
        L = ["", "  🌍 " + self._ig_lb(":", "Result:") + "  (source: %s)" % data.get("src", "?"), "",
             "  🌐 " + self._ig_lb(": ", "IP: ") + str(data.get("ip", "?")),
             "  🏳 " + self._ig_lb(": ", "Country: ") + ("%s (%s)" % (data.get("country", "?"), data.get("cc", "?"))),
             "  🏙 " + self._ig_lb(": ", "City: ") + str(data.get("city", "?")),
             "  🗺 " + self._ig_lb(": ", "Region: ") + str(data.get("region", "?")),
             "  📮 " + self._ig_lb(": ", "Zip: ") + str(data.get("zip", "?")),
             "  📍 " + self._ig_lb(": ", "Latitude: ") + str(lat),
             "  📍 " + self._ig_lb(": ", "Longitude: ") + str(lon),
             "  🕐 " + self._ig_lb(": ", "Timezone: ") + str(data.get("tz", "?")),
             "  🏢 " + self._ig_lb(": ", "Org: ") + str(data.get("org", "?")),
             "  📡 " + self._ig_lb(": ", "ISP: ") + str(data.get("isp", "?")),
             "  🧩 AS: " + str(data.get("as", "?")),
             "", "  🔗 " + self._ig_lb(" :", "Map link:"), "     " + maplink, ""]
        txt = "\n".join(L)
        self.root.after(0, lambda: self._write(self.ig_out, txt))

    def _ig_local_basic(self, ip):
        out = ["", "  🏠 Local network info for " + ip, ""]
        try:
            rr = subprocess.run(["ping", "-c", "2", "-W", "2", ip], capture_output=True, text=True, timeout=8)
            m = re.search(r"time=([\d.]+)", rr.stdout)
            out.append("  📶 Ping: " + (m.group(1) + " ms" if m else "no reply"))
        except Exception:
            out.append("  📶 Ping: error")
        try:
            nn = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True, timeout=6)
            m = re.search(r"lladdr ([0-9a-fA-F:]+)", nn.stdout)
            out.append("  🔧 MAC: " + (m.group(1) if m else "unknown"))
        except Exception:
            pass
        try:
            out.append("  🖥 Hostname: " + socket.gethostbyaddr(ip)[0])
        except Exception:
            out.append("  🖥 Hostname: unknown")
        out.append("")
        return "\n".join(out)
    def _build_packx(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["packx"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                 command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T(" ", "Package Installer"),
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        row = tk.Frame(page, bg=TH["bg"])
        row.pack(fill="x", padx=40)
        self.pk_entry = tk.Entry(row, bg=TH["card"], fg=TH["text"],
                                insertbackground=TH["text"], font=TH["font"])
        self.pk_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.pk_entry.insert(0, "nmap")
        tk.Button(row, text=self._wl_T("", "Install"), command=self._pk_start,
                 bg=TH["green"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        self.pk_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                             font=("Courier", 11), state="disabled",
                             wrap="word", padx=10, pady=10)
        self.pk_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _pk_start(self):
        n = self.pk_entry.get().strip()
        if not n:
            return
        self._write(self.pk_out, self._wl_T("  ...", "Checking..."), True)
        threading.Thread(target=self._packx_worker, args=(n,), daemon=True).start()

    def _apply_startup_prefs(self):
        tname = self.prefs.get("theme", "dark")
        TH.update(THEMES.get(tname, THEMES["dark"]))
        try:
            fs = int(self.prefs.get("fontsize", 10))
        except Exception:
            fs = 10
        TH["font"] = ("Segoe UI", fs)
        TH["font_s"] = ("Segoe UI", max(8, fs - 1))
        TH["font_b"] = ("Segoe UI", fs, "bold")
        TH["font_h"] = ("Segoe UI", fs + 6, "bold")
        try:
            self.root.attributes("-alpha", float(self.prefs.get("opacity", 1.0)))
        except Exception:
            pass
        if self.prefs.get("topmost", False):
            self.root.attributes("-topmost", True)
        if self.prefs.get("fullscreen", False):
            try:
                self.root.attributes("-zoomed", True)
            except Exception:
                pass
        ttl = self.prefs.get("title", "")
        if ttl:
            self.root.title(ttl)

    def _play_chime(self):
        if not self.prefs.get("sound", True):
            return
        def _w():
            try:
                import wave, struct
                import math as _m
                d = os.path.expanduser("~/.toolbox_sounds")
                os.makedirs(d, exist_ok=True)
                p = os.path.join(d, "start.wav")
                if not os.path.exists(p):
                    with wave.open(p, "wb") as w:
                        w.setnchannels(1)
                        w.setsampwidth(2)
                        w.setframerate(8000)
                        data = b""
                        for i in range(8000):
                            t = i / 8000.0
                            fq = 523 if i < 4000 else 784
                            data += struct.pack("<h", int(12000 * _m.sin(2 * _m.pi * fq * t) * (1 - t)))
                        w.writeframes(data)
                for pl in (["paplay", p], ["aplay", "-q", p], ["play", "-q", p]):
                    if shutil.which(pl[0]):
                        subprocess.Popen(pl, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                        return
            except Exception:
                pass
        threading.Thread(target=_w, daemon=True).start()

    def _del_sounds(self):
        d = os.path.expanduser("~/.toolbox_sounds")
        n = 0
        try:
            if os.path.isdir(d):
                for f2 in os.listdir(d):
                    try:
                        os.remove(os.path.join(d, f2))
                        n += 1
                    except Exception:
                        pass
        except Exception:
            pass
        self.set_msg.configure(text=str(n) + self._wl_T("    ", " sound files deleted"))

    def _build_wifiattack(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["wifiattack"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("📶 ", " WiFi Security Testing"),
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=6)
        tk.Label(page, text=self._wl_T("⚠ !",
                "⚠ Only on networks you own or have written permission for!"),
                bg=TH["bg"], fg=TH["red"], font=TH["font_b"]).pack()
        f1 = tk.Frame(page, bg=TH["bg"]); f1.pack(fill="x", padx=40, pady=4)
        tk.Label(f1, text=self._wl_T(":", "Interface:"), bg=TH["bg"],
                fg=TH["text"]).pack(side="left")
        self.wf_if = tk.Entry(f1, bg=TH["card"], fg=TH["text"], width=10,
                             insertbackground=TH["text"])
        self.wf_if.pack(side="left", padx=4)
        self.wf_if.insert(0, "wlan0")
        tk.Button(f1, text=self._wl_T(" ", "Monitor ON"),
                 command=lambda: self._wf_mon(True), bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        tk.Button(f1, text=self._wl_T(" ", "Monitor OFF"),
                 command=lambda: self._wf_mon(False), bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        f2 = tk.Frame(page, bg=TH["bg"]); f2.pack(fill="x", padx=40, pady=4)
        tk.Button(f2, text=self._wl_T(" AP (15s)", "Scan APs (15s)"),
                 command=self._wf_scan, bg=TH["accent"], fg="#000").pack(side="left", padx=3)
        tk.Label(f2, text="BSSID:", bg=TH["bg"], fg=TH["text"]).pack(side="left", padx=(10, 0))
        self.wf_bssid = tk.Entry(f2, bg=TH["card"], fg=TH["text"], width=14,
                                insertbackground=TH["text"])
        self.wf_bssid.pack(side="left", padx=3)
        tk.Label(f2, text="CH:", bg=TH["bg"], fg=TH["text"]).pack(side="left", padx=(6, 0))
        self.wf_ch = tk.Entry(f2, bg=TH["card"], fg=TH["text"], width=4,
                                  insertbackground=TH["text"])
        self.wf_ch.pack(side="left", padx=3)
        tk.Label(f2, text=self._wl_T(":", "Pkts:"), bg=TH["bg"], fg=TH["text"]).pack(side="left", padx=(6, 0))
        self.wf_pkts = tk.Entry(f2, bg=TH["card"], fg=TH["text"], width=6,
                                 insertbackground=TH["text"])
        self.wf_pkts.pack(side="left", padx=3)
        self.wf_pkts.insert(0, "10")
        tk.Button(f2, text=self._wl_T("", "Stop"), command=self._wf_stop,
                  bg=TH["card"], fg=TH["red"]).pack(side="left", padx=3)
        tk.Button(f2, text=self._wl_T(" Deauth ( !)", "Deauth test (own network!)"),
                 command=self._wf_deauth, bg=TH["red"], fg="#fff").pack(side="left", padx=3)
        f3 = tk.Frame(page, bg=TH["bg"]); f3.pack(fill="x", padx=40, pady=4)
        tk.Button(f3, text=self._wl_T(" (20s)", "Scan clients (20s)"),
                  command=self._wf_clients, bg=TH["accent"], fg="#000").pack(side="left", padx=3)
        tk.Label(f3, text="CLIENT:", bg=TH["bg"], fg=TH["text"]).pack(side="left", padx=(10, 0))
        self.wf_client = tk.Entry(f3, bg=TH["card"], fg=TH["text"], width=14,
                                  insertbackground=TH["text"])
        self.wf_client.pack(side="left", padx=3)
        self.wf_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 10),
                             state="disabled", wrap="word", padx=10, pady=10)
        self.wf_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _wf_mon(self, on):
        iface = self.wf_if.get().strip() or "wlan0"
        cmd = (["airmon-ng", "start", iface] if on else ["airmon-ng", "stop", iface + "mon"])
        if not shutil.which("airmon-ng"):
            self._write(self.wf_out, "  airmon-ng not found (sudo apt install aircrack-ng)", True)
            return
        def _w():
            rc, o = run_cmd(cmd, 30)
            self._write_async(self.wf_out, o, clear=True)
        threading.Thread(target=_w, daemon=True).start()

    def _wf_killscan(self):
        p = getattr(self, "_wf_scanproc", None)
        if p is not None and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
        self._wf_scanproc = None

    def _wf_ismon(self, iface):
        if not shutil.which("iw"):
            return True
        rc, o = run_cmd(["iw", "dev", iface, "info"], 5)
        return ("type monitor" in o)

    def _wf_scan(self):
        if not shutil.which("airodump-ng"):
            self._write(self.wf_out, "  airodump-ng not found", True)
            return
        iface = self.wf_if.get().strip() + "mon"
        if not self._wf_ismon(iface):
            self._write(self.wf_out, "  ⚠ " + self._ig_lb("    !  « ON»  ", "Not in monitor mode! Press Monitor ON first"), True)
            return
        self._wf_killscan()
        try:
            os.remove("/tmp/wscan-01.csv")
        except Exception:
            pass
        self._write(self.wf_out, "  🔍 " + self._ig_lb("  AP (15 )...", "Powerful AP scan (15s)..."), True)
        def _w():
            import subprocess
            p = subprocess.Popen(["airodump-ng", "--output-format", "csv",
                                  "--write", "/tmp/wscan", "--ignore-negative-one", iface],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._wf_scanproc = p
            try:
                p.wait(15)
            except Exception:
                p.terminate()
                try:
                    p.wait(3)
                except Exception:
                    pass
            L = ["", "  📶 " + self._ig_lb("AP   (   ):", "APs found (sorted by signal):"), "",
                 "  BSSID              CH  PWR  ENC    ESSID"]
            aps = []
            try:
                with open("/tmp/wscan-01.csv", errors="ignore") as f:
                    rows = f.read().split("\n")
                sec = ""
                for r in rows:
                    if r.startswith("BSSID,"):
                        sec = "AP"; continue
                    if r.strip() == "":
                        if sec == "AP":
                            sec = "ST"
                        continue
                    if sec != "AP":
                        continue
                    p2 = [x.strip() for x in r.split(",")]
                    if len(p2) >= 14 and p2[0].count(":") == 5:
                        try:
                            pwr = int(p2[8])
                        except Exception:
                            pwr = -100
                        ess = p2[13].strip() or "<hidden>"
                        aps.append((pwr, p2[0].upper(), p2[3], p2[5], ess))
            except Exception as e:
                L.append("  parse error: %s" % e)
            aps.sort(key=lambda x: x[0], reverse=True)
            seen = set()
            apmap = {}
            for pwr, bssid, chn, enc, ess in aps:
                if bssid in seen:
                    continue
                seen.add(bssid)
                apmap[bssid] = chn
                L.append("  %-18s %3s %4s  %-6s %s" % (bssid, chn, pwr, enc, ess))
            self._wf_apmap = apmap
            L.append("")
            L.append("  🧮 " + self._ig_lb(" AP: ", "AP count: ") + str(len(seen)))
            bb = self.wf_bssid.get().strip().upper()
            chv = apmap.get(bb, "")
            def _fc(chv=chv):
                if chv:
                    self.wf_ch.delete(0, "end")
                    self.wf_ch.insert(0, chv)
            self.root.after(0, _fc)
            self._write_async(self.wf_out, "\n".join(L), clear=True)
        threading.Thread(target=_w, daemon=True).start()

    def _wf_deauth(self):
        b = self.wf_bssid.get().strip()
        if not b or b.count(":") != 5:
            self._write(self.wf_out, "  " + self._ig_lb("BSSID  (AA:BB:CC:DD:EE:FF)", "BSSID invalid (AA:BB:CC:DD:EE:FF)"), True)
            return
        cl = self.wf_client.get().strip()
        if cl and cl.count(":") != 5:
            self._write(self.wf_out, "  " + self._ig_lb("MAC   ", "Invalid client MAC"), True)
            return
        if not shutil.which("aireplay-ng"):
            self._write(self.wf_out, "  aireplay-ng not found", True)
            return
        try:
            if os.geteuid() != 0:
                self._write(self.wf_out, "  ⚠ needs root - run with sudo", True)
                return
        except Exception:
            pass
        iface = self.wf_if.get().strip() + "mon"
        try:
            n = int(self.wf_pkts.get().strip() or "10")
        except Exception:
            n = 10
        if n < 0:
            n = 10
        def _w():
            self._wf_killscan()
            extra = []
            ch = self.wf_ch.get().strip()
            if not ch:
                ch = getattr(self, "_wf_apmap", {}).get(b.upper(), "")
            if ch:
                def _fc(c=ch):
                    self.wf_ch.delete(0, "end")
                    self.wf_ch.insert(0, c)
                self.root.after(0, _fc)
                rc2, _o2 = run_cmd(["iwconfig", iface, "channel", ch], 10)
                if rc2 != 0:
                    run_cmd(["iw", "dev", iface, "set", "channel", ch], 10)
                extra.append("  📡 " + self._ig_lb("  : ", "Channel set: ") + ch)
            tgt = ["-a", b]
            if cl:
                tgt += ["-c", cl]
                extra.append("  🎯 " + self._ig_lb(":   ", "Target: only client ") + cl)
            if n == 0:
                self._wf_kill()
                import subprocess
                p = subprocess.Popen(["aireplay-ng", "--deauth", "0"] + tgt + [iface],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, bufsize=1)
                self._wf_proc = p
                extra.append("  ♾ " + self._ig_lb("    -    «»  ", "Infinite mode ON - press Stop to end"))
                self._write_async(self.wf_out, "\n".join(extra), clear=True)
                def _reader(p=p):
                    for line in p.stdout:
                        self._write_async(self.wf_out, line.rstrip("\n"), clear=False)
                threading.Thread(target=_reader, daemon=True).start()
                return
            tmo = max(30, min(600, 10 + n))
            rc, o = run_cmd(["aireplay-ng", "--deauth", str(n)] + tgt + [iface], tmo)
            self._write_async(self.wf_out, "\n".join(extra + [o]), clear=True)
        threading.Thread(target=_w, daemon=True).start()

    def _wf_vendor(self, mac):
        try:
            import urllib.request
            req = urllib.request.Request("https://api.macvendors.com/" + mac,
                                         headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as r:
                return r.read().decode("utf-8", "ignore").strip()[:24]
        except Exception:
            return ""

    def _wf_clients(self):
        b = self.wf_bssid.get().strip().upper()
        if not b or b.count(":") != 5:
            self._write(self.wf_out, "  " + self._ig_lb(" BSSID   ", "Enter BSSID first"), True)
            return
        if not shutil.which("airodump-ng"):
            self._write(self.wf_out, "  airodump-ng not found", True)
            return
        iface = self.wf_if.get().strip() + "mon"
        if not self._wf_ismon(iface):
            self._write(self.wf_out, "  ⚠ " + self._ig_lb("    !  « ON»  ", "Not in monitor mode! Press Monitor ON first"), True)
            return
        ch = self.wf_ch.get().strip() or getattr(self, "_wf_apmap", {}).get(b, "")
        self._wf_killscan()
        try:
            os.remove("/tmp/cscan-01.csv")
        except Exception:
            pass
        self._write(self.wf_out, " 🔍 " + self._ig_lb(" (20 )...", "Deep client scan (20s)..."), True)
        def _w():
            import subprocess
            cmd = ["airodump-ng", "--output-format", "csv", "--write", "/tmp/cscan",
                   "--ignore-negative-one", "--bssid", b]
            if ch:
                cmd += ["-c", str(ch)]
            cmd.append(iface)
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._wf_scanproc = p
            try:
                p.wait(20)
            except Exception:
                p.terminate()
                try:
                    p.wait(3)
                except Exception:
                    pass
            L = ["", " 📱 " + self._ig_lb(" ", "Clients connected to ") + b, "",
                 "  STATION MAC           PWR   PKTS  NAME"]
            best = {}
            try:
                with open("/tmp/cscan-01.csv", errors="ignore") as f:
                    rows = f.read().split("\n")
                sec = ""
                for r in rows:
                    if r.startswith("Station MAC"):
                        sec = "ST"; continue
                    if r.startswith("BSSID,"):
                        sec = "AP"; continue
                    if sec != "ST" or r.strip() == "":
                        continue
                    p2 = [x.strip() for x in r.split(",")]
                    if len(p2) >= 6 and p2[0].count(":") == 5 and p2[5].strip().upper() == b:
                        try:
                            pwr = int(p2[3])
                        except Exception:
                            pwr = -100
                        try:
                            pk = int(p2[4])
                        except Exception:
                            pk = 0
                        m = p2[0].upper()
                        if m not in best or pk > best[m][0]:
                            best[m] = (pk, pwr)
            except Exception as e:
                L.append("  parse error: %s" % e)
            cl = sorted(best.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)
            for idx2, (mac, (pk, pwr)) in enumerate(cl):
                name = self._wf_vendor(mac) if idx2 < 10 else ""
                L.append("  %-21s %5s %6s  %s" % (mac, pwr, pk, name or "-"))
            if not cl:
                L.append("  " + self._ig_lb("   -    ", "No clients found - nobody connected?"))
            else:
                L.append("")
                L.append("  💡 " + self._ig_lb("   MAC    CLIENT ", "For targeted attack, put client MAC in CLIENT"))
            self._write_async(self.wf_out, "\n".join(L), clear=True)
        threading.Thread(target=_w, daemon=True).start()

    def _wf_kill(self):
        p = getattr(self, "_wf_proc", None)
        if p is not None and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass

    def _wf_stop(self):
        p = getattr(self, "_wf_proc", None)
        if p is not None and p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
            self._write(self.wf_out, "  🛑 " + self._ig_lb("  ", "Attack stopped"), True)
        else:
            self._write(self.wf_out, "  🛑 " + self._ig_lb("    ", "No infinite attack running"), True)

    def _build_webpentest(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["webpentest"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🕸   ()", "🕸 Web Pentest (non-destructive)"),
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        row = tk.Frame(page, bg=TH["bg"])
        row.pack(fill="x", padx=40)
        self.wp_entry = tk.Entry(row, bg=TH["card"], fg=TH["text"],
                                insertbackground=TH["text"], font=TH["font"])
        self.wp_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.wp_entry.insert(0, "https://example.com")
        tk.Button(row, text=self.T("run"), command=self._wp_start,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        self.wp_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                             state="disabled", wrap="word", padx=10, pady=10)
        self.wp_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _wp_start(self):
        u = self.wp_entry.get().strip()
        if not u:
            return
        if not u.startswith("http"):
            u = "https://" + u
        threading.Thread(target=self._wp_worker, args=(u,), daemon=True).start()

    def _wp_worker(self, url):
        import urllib.request
        import ssl as _ssl
        from urllib.parse import urlparse
        host = urlparse(url).hostname or url
        L = ["", "  == " + host + " ==", ""]
        try:
            ip = socket.gethostbyname(host)
            L.append("  [OK] DNS: %s" % ip)
        except Exception:
            L.append("  [ERR] DNS fail")
            self._write_async(self.wp_out, "\n".join(L), clear=True)
            return
        for port in [80, 443, 8080, 8443, 21, 22, 25, 3306]:
            s = socket.socket()
            s.settimeout(1)
            try:
                s.connect((host, port))
                L.append("  [OPEN] %d" % port)
            except Exception:
                pass
            finally:
                s.close()
        try:
            ctx = _ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as ss:
                ss.settimeout(5)
                ss.connect((host, 443))
                cert = ss.getpeercert()
                L.append("  [OK] TLS: %s" % cert.get("subject", [(("", ""), )])[0][0][1])
                L.append("  [OK] " + self._wl_T(":", "Expires:") + " %s" % cert.get("notAfter", "?"))
        except Exception as e:
            L.append("  [NO] TLS/443: %s" % e)
        for path in ["/robots.txt", "/sitemap.xml", "/admin", "/wp-admin/", "/phpmyadmin/"]:
            try:
                req = urllib.request.Request(url.rstrip("/") + path,
                                            headers={"User-Agent": "Mozilla/5.0"})
                r = urllib.request.urlopen(req, timeout=8)
                L.append("  [%d] %s" % (r.status, path))
            except Exception as e:
                st = getattr(e, "code", None)
                if st:
                    L.append("  [%d] %s" % (st, path))
        self._write_async(self.wp_out, "\n".join(L), clear=True)

    def _build_bruteforce(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["bruteforce"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                 bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🔓   ()", "🔓 Hash Cracking (offline)"),
                font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=10)
        f1 = tk.Frame(page, bg=TH["bg"]); f1.pack(fill="x", padx=40, pady=3)
        tk.Label(f1, text="Hash:", bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.bf_hash = tk.Entry(f1, bg=TH["card"], fg=TH["text"],
                               insertbackground=TH["text"])
        self.bf_hash.pack(side="left", fill="x", expand=True, padx=4)
        f2 = tk.Frame(page, bg=TH["bg"]); f2.pack(fill="x", padx=40, pady=3)
        tk.Label(f2, text="Type:", bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.bf_type = tk.StringVar(value="md5")
        for t2 in ["md5", "sha1", "sha256", "sha512"]:
            tk.Radiobutton(f2, text=t2, variable=self.bf_type, value=t2,
                          bg=TH["bg"], fg=TH["text"], selectcolor=TH["card"],
                          font=TH["font_s"]).pack(side="left", padx=3)
        f3 = tk.Frame(page, bg=TH["bg"]); f3.pack(fill="x", padx=40, pady=3)
        tk.Label(f3, text=self._wl_T(" :", "Wordlist file:"), bg=TH["bg"],
                fg=TH["text"]).pack(side="left")
        self.bf_file = tk.Entry(f3, bg=TH["card"], fg=TH["text"],
                               insertbackground=TH["text"])
        self.bf_file.pack(side="left", fill="x", expand=True, padx=4)
        tk.Label(page, text=self._wl_T("( =  -)", "(empty = digits 0000-9999)"),
                bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        f4 = tk.Frame(page, bg=TH["bg"]); f4.pack(pady=6)
        self._bf_stop = False
        tk.Button(f4, text=self.T("run"), command=self._bf_start,
                 bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=4)
        tk.Button(f4, text=self.T("stop"), command=self._bf_stopfn,
                 bg=TH["red"], fg="#fff").pack(side="left", padx=4)
        self.bf_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                             state="disabled", wrap="word", padx=10, pady=10)
        self.bf_out.pack(fill="both", expand=True, padx=40, pady=10)

    def _bf_stopfn(self):
        self._bf_stop = True

    def _bf_start(self):
        h = self.bf_hash.get().strip().lower()
        if not h:
            return
        self._bf_stop = False
        threading.Thread(target=self._bf_worker, args=(h,), daemon=True).start()

    def _bf_worker(self, h):
        import hashlib
        import time as _t
        typ = self.bf_type.get()
        src = self.bf_file.get().strip()
        t0 = _t.time()
        n = 0
        gen = None
        if src and os.path.exists(src):
            gen = (l.strip() for l in open(src, errors="ignore") if l.strip())
        else:
            gen = (str(i).zfill(4) for i in range(10000))
        self._write_async(self.bf_out, "  " + self._wl_T("...", "start..."), clear=True)
        for w in gen:
            if self._bf_stop:
                self._write_async(self.bf_out, "  ⏹ " + self._wl_T("", "stopped"))
                return
            if hashlib.new(typ, w.encode()).hexdigest() == h:
                dt = max(_t.time() - t0, 0.001)
                self._write_async(self.bf_out, "  ✅ " + self._wl_T(" :", "FOUND:") +
                                  " %s   (%d hash, %.0f h/s)" % (w, n, n / dt))
                return
            n += 1
            if n % 50000 == 0:
                self._write_async(self.bf_out, "  ... %d" % n)
        self._write_async(self.bf_out, "  ❌ " + self._wl_T(" ", "not found") + " (%d)" % n)

    # ══ OSINT -    ══
    def _build_osint(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["osint"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🕵 OSINT ", "🕵 Advanced OSINT"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T("  /  / IP /  -   ",
                 "Username / Domain / IP / Email - public sources only"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40, pady=4)
        self.os_q = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                             insertbackground=TH["text"], font=("Courier", 11))
        self.os_q.pack(side="left", fill="x", expand=True, padx=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        for tfa, ten, kind in [("👤  ", "👤 User", "user"),
                               ("🌐 ", "🌐 Domain", "domain"),
                               ("🌍 IP", "🌍 IP", "ip"),
                               ("✉ ", "✉ Email", "mail")]:
            tk.Button(bf, text=self._wl_T(tfa, ten),
                      command=lambda k=kind: self._os_run(k),
                      bg=TH["accent"], fg="#000").pack(side="left", padx=3)
        tk.Button(bf, text=self._wl_T("⏹ ", "⏹ Stop"), command=self._os_stop_set,
                  bg=TH["red"], fg="#fff").pack(side="left", padx=3)
        self.os_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word", padx=10, pady=10)
        self.os_out.pack(fill="both", expand=True, padx=40, pady=8)
        self.os_stop = threading.Event()
        self._os_busy = False

    def _os_run(self, kind):
        q = self.os_q.get().strip()
        if not q or self._os_busy:
            return
        self._os_busy = True
        self.os_stop.clear()
        threading.Thread(target=self._os_worker, args=(kind, q), daemon=True).start()

    def _os_stop_set(self):
        self.os_stop.set()

    def _os_worker(self, kind, q):
        """Dispatcher: routes kind to the right real-source worker"""
        try:
            if kind == "user":
                self._os_user_worker(q)
            elif kind == "domain":
                self._os_domain_worker(q)
            elif kind == "ip":
                self._os_ip_worker(q)
            else:
                self._os_mail_worker(q)
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self._write_async(self.os_out, "\n  ❌ " + self._wl_T(": ", "Error: ") + repr(e))
            except Exception:
                pass
        finally:
            self._os_busy = False

    def _os_http(self, url, timeout=8, follow=True):
        import urllib.request, urllib.error
        class _NoRedir(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        try:
            opener = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedir)
            req = urllib.request.Request(url, headers={"User-Agent":
                "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
                "Accept-Language": "en-US,en;q=0.9"})
            r = opener.open(req, timeout=timeout)
            return r.status, r.read(), False
        except urllib.error.HTTPError as e:
            return e.code, b"", (e.code in (301, 302, 303, 307, 308))
        except Exception:
            return None, b"", False

    def _os_github_email(self, u):
        import json
        code, data = self._os_http("https://api.github.com/users/%s/events/public" % u, timeout=10)
        if code != 200:
            return None
        try:
            for ev in json.loads(data.decode("utf-8", "replace")):
                try:
                    em = ev["payload"]["commits"][0]["author"]["email"]
                    if em and "noreply" not in em:
                        return em
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _os_gravatar_json(self, email):
        import hashlib, json
        h = hashlib.md5(email.strip().lower().encode()).hexdigest()
        code, data = self._os_http("https://gravatar.com/%s.json" % h, timeout=8)
        if code == 200:
            try:
                ents = json.loads(data.decode("utf-8", "replace")).get("entry", [])
                return ents[0] if ents else None
            except Exception:
                return None
        return None

    def _os_keybase(self, u):
        import json
        code, data = self._os_http("https://keybase.io/_/api/1.0/user/lookup.json?usernames=%s" % u, timeout=8)
        if code == 200:
            try:
                th = json.loads(data.decode("utf-8", "replace")).get("them") or []
                return th[0] if th else None
            except Exception:
                return None
        return None

    def _os_run_sherlock(self, u, W):
        import subprocess, shutil as _sh
        exe = _sh.which("sherlock")
        if not exe:
            for p in (os.path.expanduser("~/.local/bin/sherlock"), "/usr/local/bin/sherlock"):
                if os.path.exists(p):
                    exe = p
                    break
        if not exe:
            W("     ⚠ " + self._wl_T("     +   :", "Sherlock not installed; for 400+ sites install:") + " pip install sherlock-project")
            return
        W("     ⏳ " + self._wl_T(" Sherlock (  )...", "Running Sherlock (real local tool)..."))
        try:
            proc = subprocess.Popen([exe, u], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            t0 = time.time()
            for line in proc.stdout:
                if self.os_stop.is_set() or time.time() - t0 > 120:
                    proc.kill()
                    break
                if line.strip():
                    W("     " + line.rstrip())
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        except Exception as e:
            W("     ❌ " + repr(e))

    def _os_user_worker(self, u):
        import json
        from concurrent.futures import ThreadPoolExecutor
        import threading as _th
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.os_out, s, clear=clear)
        W("\n  ── 👤 " + T("  :", "Hunting username:") + " %s ──" % u, clear=True)
        W("  🎯 " + T("    API/ ✅", "Only real API-verified ✅"))
        VER = [
            ("GitHub",     "https://api.github.com/users/%s", "api"),
            ("GitLab",     "https://gitlab.com/api/v4/users?username=%s", "jsonlist"),
            ("Reddit",     "https://www.reddit.com/user/%s/about.json", "api"),
            ("Wikipedia",  "https://en.wikipedia.org/w/api.php?action=query&list=users&format=json&ususers=%s", "wiki"),
            ("Duolingo",   "https://www.duolingo.com/2017-06-30/users?username=%s", "jsonusers"),
            ("Telegram",   "https://t.me/%s", ("tgme_page_message", "Sorry, this page")),
            ("Instagram",  "https://www.instagram.com/%s/", ('"profilePage":"profile"', "Sorry, this page isn")),
            ("Steam",      "https://steamcommunity.com/id/%s", ("persona_name", "could not be found")),
            ("HackerNews", "https://news.ycombinator.com/user?id=%s", ("", "No such user")),
            ("Mastodon",   "https://mastodon.social/@%s", "status"),
            ("Keybase",    "https://keybase.io/%s", "status"),
            ("Tumblr",     "https://%s.tumblr.com", "status"),
            ("Last.fm",    "https://www.last.fm/user/%s", "status"),
            ("Vimeo",      "https://vimeo.com/%s", "status"),
            ("Medium",     "https://medium.com/@%s", "status"),
            ("Bitbucket",  "https://bitbucket.org/%s", "status"),
            ("DeviantArt", "https://www.deviantart.com/%s", "status"),
            ("Flickr",     "https://www.flickr.com/people/%s/", "status"),
            ("Pinterest",  "https://www.pinterest.com/%s/", "status"),
            ("Snapchat",   "https://www.snapchat.com/add/%s", "status"),
            ("YouTube",    "https://www.youtube.com/@%s", "status")]
        lock = _th.Lock()
        st = {"ok": 0, "blk": 0}
        found = {}
        def check(item):
            name, url, kind = item
            if self.os_stop.is_set():
                return
            code, data, redir = self._os_http(url % u, timeout=8, follow=(kind != "status"))
            txt = data.decode("utf-8", "replace") if data else ""
            ok = None
            if kind == "api":
                ok = True if code == 200 else (False if code == 404 else None)
            elif kind == "jsonlist":
                if code == 200:
                    try:
                        ok = len(json.loads(txt)) > 0
                    except Exception:
                        ok = None
            elif kind == "jsonusers":
                if code == 200:
                    try:
                        ok = len(json.loads(txt).get("users", [])) > 0
                    except Exception:
                        ok = None
            elif kind == "wiki":
                try:
                    ok = len(json.loads(txt).get("query", {}).get("users", [])) > 0
                except Exception:
                    ok = None
            elif kind == "status":
                if redir or code in (301, 302, 303, 307, 308):
                    ok = None
                elif code == 200:
                    ok = True
                elif code in (404, 410):
                    ok = False
            else:
                yes, no = kind
                if code != 200:
                    ok = None
                elif no and no in txt:
                    ok = False
                elif yes and yes in txt:
                    ok = True
            if ok is True:
                with lock:
                    st["ok"] += 1
                    found[name] = url % u
                W("  ✅ %-11s %s" % (name, url % u))
            elif ok is None and code in (403, 429, 999):
                with lock:
                    st["blk"] += 1
        with ThreadPoolExecutor(max_workers=10) as ex:
            list(ex.map(check, VER))
        W("\n  🏁 " + T(" :", "Verified:") + " %d / %d" % (st["ok"], len(VER)) +
          ("" if not st["blk"] else "   ⛔ " + T(":", "Blocked:") + " %d" % st["blk"]))
        names, mails, cross = [], [], []
        def add_name(v):
            v = (v or "").strip()
            if v and v not in names and len(v) < 60:
                names.append(v)
        def add_cross(sv, url2):
            if url2 and url2 not in cross:
                cross.append(url2)
                W("     🔗 %s: %s" % (sv, url2))
        W("\n  🕵 " + T("    :", "Deep extraction from public sources:"))
        if "GitHub" in found and not self.os_stop.is_set():
            code, data = self._os_http("https://api.github.com/users/" + u)
            if code == 200:
                try:
                    d = json.loads(data.decode("utf-8", "replace"))
                    add_name(d.get("name"))
                    for k, lab in [("bio", T("", "Bio")), ("company", T("", "Company")),
                                   ("blog", "Blog"), ("location", T("", "Location")),
                                   ("twitter_username", "Twitter")]:
                        if d.get(k):
                            W("     • GitHub %s: %s" % (lab, d[k]))
                            W(" • " + T("/:", "Repos/Followers:") + " %s / %s" % (d.get("public_repos"), d.get("followers")))
                except Exception:
                    pass
            em = self._os_github_email(u)
            if em:
                mails.append(em)
                W(" • " + T(" :", "Public email from commits:") + " %s" % em)
        if "Reddit" in found and not self.os_stop.is_set():
            code, data = self._os_http("https://www.reddit.com/user/%s/about.json" % u)
            if code == 200:
                try:
                    d = json.loads(data.decode("utf-8", "replace")).get("data", {})
                    W("     • Reddit Karma: %s / %s" % (d.get("link_karma", "?"), d.get("comment_karma", "?")))
                except Exception:
                    pass
        kb = None if self.os_stop.is_set() else self._os_keybase(u)
        if kb:
            add_name((kb.get("profile") or {}).get("full_name"))
            for p in (kb.get("proofs_summary") or {}).get("proofs", []):
                add_cross("Keybase→%s" % p.get("proof_type", "?"), p.get("service_url"))
        for em in list(mails):
            g = None if self.os_stop.is_set() else self._os_gravatar_json(em)
            if g:
                add_name(g.get("displayName"))
                try:
                    add_name((g.get("name") or {}).get("formatted"))
                except Exception:
                    pass
                for acc in (g.get("accounts") or []):
                    add_cross("Gravatar→%s" % acc.get("shortname", "?"), acc.get("url"))
        W("\n  📛 " + T("  ():", "Real name (public):") + " " + (", ".join(names) or T(" ", "not found")))
        W("  ✉ " + T(" :", "Public email:") + " " + (", ".join(mails) or T(" ", "not found")))
        W(" 🔗 " + T(" :", "Other-service accounts:") + " %d" % len(cross))
        MAN = [("X/Twitter", "https://x.com/%s"), ("Facebook", "https://www.facebook.com/%s"),
               ("LinkedIn", "https://www.linkedin.com/in/%s/"), ("TikTok", "https://www.tiktok.com/@%s"),
               ("Spotify", "https://open.spotify.com/user/%s"), ("SoundCloud", "https://soundcloud.com/%s"),
               ("Twitch", "https://www.twitch.tv/%s"), ("Threads", "https://www.threads.net/@%s")]
        W("  🔗 " + T(" :", "Manual check:"))
        for name, url in MAN:
            W("     • %s: %s" % (name, url % u))
        W("\n  🧰 " + T("   :", "Real tool on system:"))
        self._os_run_sherlock(u, W)
        W("  🧰 " + T(" OSINT  ():", "Real OSINT tools (online):"))
        W("     • Sherlock: https://github.com/sherlock-project/sherlock")
        W("     • WhatsMyName: https://whatsmyname.app/?q=%s" % u)
        W("     • Namechk: https://namechk.com/")
        W("     • OSINT Framework: https://osintframework.com/")

    def _os_dig(self, dom, rtype):
        try:
            if shutil.which("dig"):
                out = subprocess.run(["dig", "+short", rtype, dom], capture_output=True, text=True, timeout=10)
                return [l.strip() for l in out.stdout.splitlines() if l.strip()]
            if shutil.which("host"):
                out = subprocess.run(["host", "-t", rtype, dom], capture_output=True, text=True, timeout=10)
                return [l.strip() for l in out.stdout.splitlines() if l.strip()]
        except Exception:
            pass
        return []

    def _os_domain_worker(self, dom):
        import ssl, socket, json
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.os_out, s, clear=clear)
        W("\n  ──  " + T("OSINT :", "Domain OSINT:") + " %s ──" % dom, clear=True)
        W("  📮 DNS:")
        try:
            W("     A: " + socket.gethostbyname(dom))
        except Exception:
            W("     A: ❌")
        for rt in ("MX", "NS", "TXT"):
            vals = self._os_dig(dom, rt)
            if vals:
                W("     %s: %s" % (rt, " | ".join(vals[:4])))
        if shutil.which("whois"):
            W("  📜 WHOIS:")
            try:
                out = subprocess.run(["whois", dom], capture_output=True, text=True, timeout=20)
                keys = ("Registrar:", "Creation Date:", "Registry Expiry Date:", "Updated Date:",
                        "Registrant Organization:", "Registrant Country:", "Name Server:")
                seen = set()
                for l in out.stdout.splitlines():
                    l = l.strip()
                    if l.startswith(keys):
                        k = l.split(":")[0]
                        if k not in seen:
                            seen.add(k)
                            W("     " + l)
            except Exception:
                W("     ❌")
        else:
            W("  📜 WHOIS (RDAP):")
            code, data = self._os_http("https://rdap.org/domain/%s" % dom, timeout=12)
            if code == 200:
                try:
                    d = json.loads(data.decode("utf-8", "replace"))
                    for ev in d.get("events", []):
                        if ev.get("eventAction") in ("registration", "expiration", "last changed"):
                            W("     %s: %s" % (ev.get("eventAction"), str(ev.get("eventDate"))[:10]))
                    for ent in d.get("entities", []):
                        if "registrar" in (ent.get("roles") or []):
                            try:
                                for v in ent["vcardArray"][1]:
                                    if v[0] == "fn":
                                        W("     Registrar: %s" % v[3]); break
                            except Exception:
                                pass
                    ns = d.get("nameservers") or []
                    if ns:
                        W("     NS: %s" % " | ".join(x.get("ldhName", "?") for x in ns[:4]))
                except Exception:
                    W("     ❌")
            else:
                W("     ❌ " + T("  ", "unavailable"))
        W("  🔒 SSL:")
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((dom, 443), timeout=8) as sock:
                with ctx.wrap_socket(sock, server_hostname=dom) as s:
                    cert = s.getpeercert()
            def flat(t):
                return ", ".join("%s=%s" % (a, b) for pair in t for a, b in pair)
            W("     " + T(":", "Issuer:") + " " + flat(cert.get("issuer", ())))
            W("     " + T(":", "Valid:") + " %s → %s" % (cert.get("notBefore"), cert.get("notAfter")))
            san = cert.get("subjectAltName", ())
            if san:
                W("     SAN: %d " % len(san) + T("", "entries"))
        except Exception:
            W("     ❌ " + T("  ", "unavailable"))
        W("  🛰 " + T(" :", "Server tech:"))
        try:
            import urllib.request
            req = urllib.request.Request("https://" + dom + "/", headers={"User-Agent": "Mozilla/5.0"})
            r = urllib.request.urlopen(req, timeout=6)
            got = False
            for h in ("Server", "X-Powered-By"):
                v = r.headers.get(h)
                if v:
                    W("     %s: %s" % (h, v))
                    got = True
            if not got:
                W("     —")
        except Exception:
            W("     —")
        W(" 🕸 " + T(" ( ):", "Subdomains (real CT logs):"))
        subs = []
        code, data = self._os_http("https://crt.sh/?q=%25." + dom + "&output=json", timeout=25)
        if code == 200:
            try:
                seen = set()
                for e in json.loads(data.decode("utf-8", "replace")):
                    for nm in str(e.get("name_value", "")).splitlines():
                        nm = nm.strip().lower()
                        if nm and nm.endswith("." + dom) and "*" not in nm and nm not in seen:
                            seen.add(nm)
                subs = sorted(seen)
            except Exception:
                subs = []
        if subs:
            W("     " + T("%d    :" % len(subs), "%d real subdomains:" % len(subs)))
            for s2 in subs[:20]:
                try:
                    W("     ✅ %s -> %s" % (s2, socket.gethostbyname(s2)))
                except Exception:
                    W("     ✅ %s" % s2)
        else:
            W("     — " + T("  crt.sh  ", "none in crt.sh"))
        try:
            code, data = self._os_http("https://api.hackertarget.com/reverseiplookup/?q=" + socket.gethostbyname(dom))
            if code == 200:
                lines = [l for l in data.decode().splitlines() if l.strip() and "No" not in l and "error" not in l.lower()]
                if lines:
                    W(" 🔁 " + T(":", "Shared hosting:") + " " + ", ".join(lines[:10]))
        except Exception:
            pass
        W("  🧰 " + T(" OSINT :", "Real OSINT tools:"))
        W("     • SecurityTrails: https://securitytrails.com/domain/%s/dns" % dom)
        W("     • Shodan: https://www.shodan.io/search?query=hostname:%s" % dom)
        W("     • Censys: https://search.censys.io/domain/%s" % dom)
        W("     • URLScan: https://urlscan.io/search/#%s" % dom)
        W("     • Wayback: https://web.archive.org/web/*/%s" % dom)
        W("     • VirusTotal: https://www.virustotal.com/gui/domain/%s" % dom)
        W("  🏁 " + T("  ", "Domain analysis done"))

    def _os_ip_worker(self, ip):
        import json, socket
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.os_out, s, clear=clear)
        W("\n ── 🌍 " + T("OSINT :", "IP OSINT:") + " %s ──" % ip, clear=True)
        try:
            W("  🔁 DNS : " + socket.gethostbyaddr(ip)[0])
        except Exception:
            W("  🔁 DNS : ❌")
        _geo_done = False
        code, data = self._os_http("https://ipwho.is/%s" % ip)
        if code == 200:
            try:
                d0 = json.loads(data.decode("utf-8", "replace"))
                if d0.get("success") is not False and d0.get("country"):
                    _c0 = d0.get("connection") or {}
                    W("  🗺 " + T(":", "Location:") + " %s %s %s" % (d0.get("country"), d0.get("region"), d0.get("city")))
                    W("  🏢 ISP: %s | %s" % (_c0.get("isp"), _c0.get("org")))
                    W("  🛜 AS: %s" % _c0.get("asn"))
                    W("  🕐 %s | 📍 %s,%s" % (d0.get("timezone"), d0.get("latitude"), d0.get("longitude")))
                    _geo_done = True
            except Exception:
                pass
        if not _geo_done:
            code, data = self._os_http("http://ip-api.com/json/%s?lang=en" % ip)
            if code == 200:
                try:
                    d = json.loads(data.decode("utf-8", "replace"))
                    if d.get("status") == "success":
                        W("  🗺 " + T(":", "Location:") + " %s %s %s" % (d.get("country"), d.get("regionName"), d.get("city")))
                        W("  🏢 ISP: %s | %s" % (d.get("isp"), d.get("org")))
                        W("  🛜 AS: %s" % d.get("as"))
                        W("  🕐 %s | 📍 %s,%s" % (d.get("timezone"), d.get("lat"), d.get("lon")))
                except Exception:
                    pass
            else:
                code2, data2 = self._os_http("https://ipapi.co/%s/json/" % ip, timeout=10)
                if code2 == 200:
                    try:
                        d = json.loads(data2.decode("utf-8", "replace"))
                        W("  🗺 " + T(":", "Location:") + " %s %s" % (d.get("country_name"), d.get("city")))
                        W("  🏢 Org: %s | %s" % (d.get("org", "?"), d.get("asn", "?")))
                    except Exception:
                        pass
                else:
                    W("  ⚠ " + T("    ", "Geo service unavailable"))
        W("  🏛 " + T("  (RDAP):", "Network ownership (RDAP):"))
        code, data = self._os_http("https://rdap.org/ip/%s" % ip, timeout=12)
        if code == 200:
            try:
                d = json.loads(data.decode("utf-8", "replace"))
                if d.get("name"):
                    W("     Net: %s" % d.get("name"))
                if d.get("country"):
                    W("     " + T(":", "Country:") + " %s" % d.get("country"))
                for ent in (d.get("entities") or [])[:3]:
                    try:
                        for v in ent["vcardArray"][1]:
                            if v[0] == "fn":
                                W("     Org: %s" % v[3]); break
                    except Exception:
                        pass
                cidr = d.get("cidr0_cidrs") or []
                if cidr:
                    W("     CIDR: %s/%s" % (cidr[0].get("v4prefix", "?"), cidr[0].get("length", "?")))
            except Exception:
                W("     ❌")
        else:
            W("     —")
        ports = [21, 22, 25, 53, 80, 110, 143, 443, 3306, 3389, 8080, 8443]
        openp = []
        for p in ports:
            if self.os_stop.is_set():
                break
            try:
                s = socket.create_connection((ip, p), timeout=1.2)
                s.close()
                openp.append(p)
            except Exception:
                pass
        W(" 🔌 " + T(" :", "Open ports:") + " " + (", ".join(map(str, openp)) or "—"))
        try:
            code, data = self._os_http("https://api.hackertarget.com/reverseiplookup/?q=" + ip)
            if code == 200:
                lines = [l for l in data.decode().splitlines() if l.strip() and "No" not in l and "error" not in l.lower()]
                if lines:
                    W(" 🔁 " + T(":", "Shared:") + " " + ", ".join(lines[:10]))
        except Exception:
            pass
        W("  🧰 " + T(" OSINT :", "Real OSINT tools:"))
        W("     • Shodan: https://www.shodan.io/host/%s" % ip)
        W("     • Censys: https://search.censys.io/ipv4/%s" % ip)
        W("     • GreyNoise: https://viz.greynoise.io/ip/%s" % ip)
        W("     • AbuseIPDB: https://www.abuseipdb.com/check/%s" % ip)
        W("     • VirusTotal: https://www.virustotal.com/gui/ip-address/%s" % ip)
        W("  🏁 " + T("  IP", "IP analysis done"))

    def _os_mail_worker(self, em):
        import hashlib, json
        from urllib.parse import quote
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.os_out, s, clear=clear)
        W("\n  ── ✉ " + T("OSINT :", "Email OSINT:") + " %s ──" % em, clear=True)
        local, _, dom = em.partition("@")
        if not dom:
            W("  ❌ " + T("  ", "Invalid email format"))
            return
        em_n = em.strip().lower()
        h = hashlib.md5(em_n.encode()).hexdigest()
        code, _ = self._os_http("https://www.gravatar.com/avatar/%s?d=404" % h)
        if code == 200:
            W("  🖼 Gravatar: ✅ " + T("/ :", "Has profile:") + " https://gravatar.com/%s" % h)
        else:
            W("  🖼 Gravatar: ❌")
        mx = self._os_dig(dom, "MX")
        W("  📮 MX: " + (" | ".join(mx[:3]) if mx else "❌ " + T("  MX!", "no MX!")))
        disp = ["mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
                "yopmail.com", "sharklasers.com", "trashmail.com", "getnada.com", "temp-mail.org"]
        W("  🗑 " + T(":", "Disposable:") + " " + ("⚠ " if dom.lower() in disp else "✅ "))
        W("  🐙 " + T("   GitHub:", "GitHub email search:"))
        code, data = self._os_http("https://api.github.com/search/users?q=" + quote(em_n), timeout=12)
        if code == 200:
            try:
                items = json.loads(data.decode("utf-8", "replace")).get("items", [])
                if items:
                    for it in items[:3]:
                        W("     ✅ " + T("   :", "Public-email account:") + " %s" % it.get("html_url"))
                else:
                    W("     — " + T("   GitHub ", "no public email on GitHub"))
            except Exception:
                W("     ❌")
        elif code == 403:
            W("     ⛔ " + T("  GitHub", "GitHub rate limit"))
        W("  💡 " + T("   «%s»       " % local,
                     "Search '%s' in username mode for more" % local))
        W("  🧰 " + T(" OSINT :", "Real OSINT tools:"))
        W("     • HaveIBeenPwned: https://haveibeenpwned.com/account/%s" % em_n)
        W("     • Hunter.io: https://hunter.io/email-verifier/%s" % em_n)
        W("     • IntelX: https://intelx.io/?s=%s" % quote(em_n))
        W("  🏁 " + T("  ", "Email analysis done"))

    def _build_hashid(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["hashid"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🧬    ", "🧬 Hash Identifier & Cracker"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T("   +   hashcat / john /  ",
                 "Detect type + crack via hashcat / john / built-in engine"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40, pady=4)
        tk.Label(r, text=self._wl_T(":", "Hash:"), bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.hi_hash = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                                insertbackground=TH["text"], font=("Courier", 11))
        self.hi_hash.pack(side="left", fill="x", expand=True, padx=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T("▶   ", "▶ Analyze & Crack"),
                  command=self._hi_run, bg=TH["accent"], fg="#000",
                  font=TH["font_b"]).pack(side="left", padx=4)
        tk.Button(bf, text=self._wl_T("⏹ ", "⏹ Stop"), command=self._hi_stop_set,
                  bg=TH["red"], fg="#fff").pack(side="left", padx=4)
        self.hi_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word", padx=10, pady=10)
        self.hi_out.pack(fill="both", expand=True, padx=40, pady=8)
        self.hi_stop = threading.Event()
        self._hi_busy = False

    def _hi_detect(self, h):
        res = []
        if re.fullmatch(r"[a-fA-F0-9]{32}", h):
            res.append(("MD5", 0, "raw-md5"))
            res.append(("NTLM", 1000, "nt"))
        if re.fullmatch(r"[a-fA-F0-9]{16}", h):
            res.append(("MySQL323", 300, None))
        if re.fullmatch(r"[a-fA-F0-9]{40}", h):
            res.append(("SHA1", 100, "raw-sha1"))
        if re.fullmatch(r"[a-fA-F0-9]{56}", h):
            res.append(("SHA224", 1300, "raw-sha224"))
        if re.fullmatch(r"[a-fA-F0-9]{64}", h):
            res.append(("SHA256", 1400, "raw-sha256"))
        if re.fullmatch(r"[a-fA-F0-9]{96}", h):
            res.append(("SHA384", 10800, "raw-sha384"))
        if re.fullmatch(r"[a-fA-F0-9]{128}", h):
            res.append(("SHA512", 1700, "raw-sha512"))
        if re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", h):
            res.append(("bcrypt", 3200, "bcrypt"))
        if re.fullmatch(r"\$1\$[./A-Za-z0-9]{1,8}\$[./A-Za-z0-9]{22}", h):
            res.append(("MD5crypt", 500, "md5crypt"))
        if re.fullmatch(r"\$5\$(rounds=\d+\$)?[./A-Za-z0-9]{1,16}\$[./A-Za-z0-9]{43}", h):
            res.append(("SHA256crypt", 7400, "sha256crypt"))
        if re.fullmatch(r"\$6\$(rounds=\d+\$)?[./A-Za-z0-9]{1,16}\$[./A-Za-z0-9]{86}", h):
            res.append(("SHA512crypt", 1800, "sha512crypt"))
        return res

    def _hi_wordlist(self):
        cands = ["/usr/share/wordlists/rockyou.txt",
                 "/usr/share/wordlists/rockyou.txt.gz",
                 "/opt/wordlists/rockyou.txt"]
        for c in cands:
            if os.path.exists(c):
                return c
        return self._hi_small_words()

    def _hi_words_iter(self, path):
        import gzip
        if path.endswith(".gz"):
            return gzip.open(path, "rt", errors="replace")
        return open(path, "r", errors="replace")

    def _hi_run(self):
        h = self.hi_hash.get().strip()
        if not h or self._hi_busy:
            return
        self._hi_busy = True
        self.hi_stop.clear()
        threading.Thread(target=self._hi_worker, args=(h,), daemon=True).start()

    def _hi_stop_set(self):
        self.hi_stop.set()

    def _hi_worker(self, h):
        import time
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.hi_out, s, clear=clear)
        t0 = time.time()
        W("\n  ──  " + T("  ", "Analyzing input hash") + " ──")
        W("  " + T("", "Length") + ": %d" % len(h))
        dets = self._hi_detect(h)
        if not dets:
            W(" ❌  " + T(" - ", "No known pattern"))
            self._hi_busy = False
            return
        for name, mode, jf in dets:
            extra = (", john: " + jf) if jf else ""
            W("  • %s   (hashcat -m %d%s)" % (name, mode, extra))
        cracked = None
        used = None

        def _py(m):
            return m in (0, 100, 1400, 1700, 1000)

        for name, mode, jf in dets:
            if cracked is not None or self.hi_stop.is_set():
                break
            if _py(mode):
                W("\n ⚡  " + T(" : ()...", "Stage 1: common passwords (instant)...") + "  [" + name + "]")
                cracked = self._hi_python(h, mode, self._hi_small_words(), 100000)
                if cracked is not None:
                    used = (name, mode)
        if cracked is None and not self.hi_stop.is_set():
            wl = self._hi_wordlist()
            if wl.endswith(".gz"):
                cdir = os.path.expanduser("~/.cache/toolbox_pro")
                try:
                    os.makedirs(cdir, 0o700, exist_ok=True)
                except Exception:
                    cdir = os.path.expanduser("~")
                dec = os.path.join(cdir, "rockyou.txt")
                if not os.path.exists(dec):
                    W(" 📦 " + T(" rockyou ( ~ )...", "Decompressing rockyou (once ~20s)..."))
                    import gzip
                    with gzip.open(wl, "rt", errors="replace") as fi, open(dec, "w") as fo:
                        for line in fi:
                            fo.write(line)
                wl = dec
            W("  📖 " + T(" :", "Wordlist:") + " " + wl)
            for name, mode, jf in dets:
                if cracked is not None or self.hi_stop.is_set():
                    break
                W("\n  ── " + T(" :", "Trying:") + " %s (hashcat -m %d) ──" % (name, mode))
                if shutil.which("hashcat"):
                    cracked = self._hi_hashcat(h, mode, wl)
                elif shutil.which("john") and jf:
                    cracked = self._hi_john(h, jf, wl)
                if cracked is not None:
                    used = (name, mode)
                    break
                if _py(mode) and not self.hi_stop.is_set():
                    W("  ⚙ " + T("  (  )...", "Built-in engine (up to 300k)..."))
                    cracked = self._hi_python(h, mode, wl, 300000)
                    if cracked is not None:
                        used = (name, mode)
        if self.hi_stop.is_set():
            W("\n  ⏹ " + T(" ", "Stopped"))
        elif cracked is not None:
            W("\n  🎉 " + T(" !  :", "Cracked! Plaintext:") + " " + cracked)
            if used:
                W("  🔑 Method: %s (hashcat -m %d)" % used)
        else:
            W("\n ⚠ " + T(" ", "Not cracked; try a bigger wordlist"))
        W("  ⏱ " + T(" :", "Total time:") + " %.1fs" % (time.time() - t0))
        self._hi_busy = False
    def _hi_small_words(self):
        cdir = os.path.expanduser("~/.cache/toolbox_pro")
        try:
            os.makedirs(cdir, 0o700, exist_ok=True)
        except Exception:
            cdir = os.path.expanduser("~")
        p = os.path.join(cdir, "small_words.txt")
        with open(p, "w") as f:
            f.write("123456\npassword\n12345678\nqwerty\n123456789\n12345\n1234\n111111\n1234567\ndragon\n123123\nbaseball\nabc123\nfootball\nmonkey\nletmein\nshadow\nmaster\n696969\nmichael\nlogin\nadmin\nwelcome\npassword1\nadmin123\nroot\ntoor\nsecret\n1234567890\n")
        try:
            os.chmod(p, 0o600)
        except Exception:
            pass
        return p
    def _hi_hb(self, proc, t0):
        import time
        while proc.poll() is None:
            if self.hi_stop.is_set():
                proc.kill()
                return False
            time.sleep(0.5)
            el = int(time.time() - t0)
            if el % 5 == 0 and el != getattr(self, "_hb_last", -1):
                self._hb_last = el
                self._write_async(self.hi_out, "  ⏳ %ds " % el + self._wl_T("    ...", "elapsed; still cracking..."))
        return True

    def _hi_hashcat(self, h, mode, wl):
        import time
        W = lambda s, clear=False: self._write_async(self.hi_out, s, clear=clear)
        import tempfile
        _fd4, hf = tempfile.mkstemp(prefix="tb_hash_", suffix=".txt")
        with os.fdopen(_fd4, "w") as f:
            f.write(h + "\n")
        os.chmod(hf, 0o600)
        _fd5, pot = tempfile.mkstemp(prefix="tb_pot_", suffix=".txt")
        os.close(_fd5)
        os.unlink(pot)
        cmd = ["hashcat", "-m", str(mode), "-a", "0", hf, wl,
               "--potfile-path=" + pot, "--force", "--quiet"]
        W("  💻 hashcat -m %d ..." % mode)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            W("  ❌ hashcat: %s" % e)
            return None
        self._hb_last = -1
        self._hi_hb(proc, time.time())
        if os.path.exists(pot):
            for line in open(pot, errors="replace"):
                if line.startswith(h + ":"):
                    return line[len(h) + 1:].strip()
        return None

    def _hi_john(self, h, jf, wl):
        import time
        W = lambda s, clear=False: self._write_async(self.hi_out, s, clear=clear)
        import tempfile as _tf
        _fd7, hf = _tf.mkstemp(prefix="tb_hash_j_", suffix=".txt")
        with os.fdopen(_fd7, "w") as f:
            f.write(h + "\n")
        os.chmod(hf, 0o600)
        cmd = ["john", "--format=" + jf, "--wordlist=" + wl, hf]
        W("  💻 john --format=%s ..." % jf)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            W("  ❌ john: %s" % e)
            return None
        self._hb_last = -1
        self._hi_hb(proc, time.time())
        pot = os.path.expanduser("~/.john/john.pot")
        if os.path.exists(pot):
            for line in open(pot, errors="replace"):
                if line.startswith(h + ":"):
                    return line[len(h) + 1:].strip()
        return None

    def _hi_python(self, h, mode, wl, cap):
        import hashlib, time
        W = lambda s, clear=False: self._write_async(self.hi_out, s, clear=clear)
        hlow = h.lower()
        def dig(w):
            b = w.encode("utf-8", "replace")
            try:
                if mode == 0:
                    return hashlib.md5(b).hexdigest()
                if mode == 100:
                    return hashlib.sha1(b).hexdigest()
                if mode == 1400:
                    return hashlib.sha256(b).hexdigest()
                if mode == 1700:
                    return hashlib.sha512(b).hexdigest()
                if mode == 1000:
                    return hashlib.new("md4", w.encode("utf-16-le"), **_md4kw).hexdigest()
            except Exception:
                return None
            return None
        _md4kw = {}
        if mode == 1000:
            _md4kw = None
            for _kw in ({}, {"usedforsecurity": False}):
                try:
                    hashlib.new("md4", b"", **_kw)
                    _md4kw = dict(_kw)
                    break
                except (ValueError, TypeError):
                    continue
            if _md4kw is None:
                W("  \u26a0 MD4 (NTLM) is not supported by this system's OpenSSL.")
                W("  \u26a0 Python cracker cannot test mode 1000 here.")
                W("  \u26a0 Use hashcat (-m 1000) for NTLM on this machine instead.")
                return None
        f = self._hi_words_iter(wl)
        n = 0
        t0 = time.time()
        found = None
        try:
            for line in f:
                if self.hi_stop.is_set() or n >= cap:
                    break
                w = line.rstrip("\n")
                n += 1
                d = dig(w)
                if d and d == hlow:
                    found = w
                    break
        finally:
            f.close()
        W("  ⏱ %d " % n + self._wl_T("  ", "words tested") + " (%.1fs)" % (time.time() - t0))
        return found

    # ══ EXIF -  ══
    def _build_exif(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["exif"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("📷  ", "📷 Metadata Inspector"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T(" ( GPS ...)",
                 "Show & scrub file metadata (camera, GPS...)"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40, pady=4)
        self.ex_path = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                                insertbackground=TH["text"], font=("Courier", 11))
        self.ex_path.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(r, text=self._wl_T("📂 ", "📂 Browse"), command=self._ex_browse,
                  bg=TH["card"], fg=TH["text"]).pack(side="left", padx=4)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T("▶ ", "▶ Show"), command=self._ex_show,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=4)
        tk.Button(bf, text=self._wl_T("🧹 ", "🧹 Scrub"), command=self._ex_scrub,
                  bg=TH["red"], fg="#fff").pack(side="left", padx=4)
        self.ex_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word", padx=10, pady=10)
        self.ex_out.pack(fill="both", expand=True, padx=40, pady=8)

    def _ex_browse(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename()
        if p:
            self.ex_path.delete(0, "end")
            self.ex_path.insert(0, p)

    def _ex_show(self):
        p = self.ex_path.get().strip()
        if not p or not os.path.exists(p):
            self._write_async(self.ex_out, "  ❌ " + self._wl_T("  ", "File not found"), clear=True)
            return
        threading.Thread(target=self._ex_worker, args=(p, False), daemon=True).start()

    def _ex_scrub(self):
        p = self.ex_path.get().strip()
        if not p or not os.path.exists(p):
            self._write_async(self.ex_out, "  ❌ " + self._wl_T("  ", "File not found"), clear=True)
            return
        threading.Thread(target=self._ex_worker, args=(p, True), daemon=True).start()

    def _ex_worker(self, p, scrub):
        import json as _json
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.ex_out, s, clear=clear)
        W("\n  ── 📷 " + T("", "Metadata of") + " " + os.path.basename(p) + " ──", clear=True)
        if not shutil.which("exiftool"):
            W("  ⚠ exiftool " + T(" !", "not installed!"))
            W("  📦 " + T("   « » :", "Install via Packages card or:"))
            W("     sudo apt install -y libimage-exiftool-perl")
            st = os.stat(p)
            import time as _t
            W("  📏 " + T(":", "Size:") + " %d B" % st.st_size)
            W("  🕒 " + T(" :", "Modified:") + " " + _t.ctime(st.st_mtime))
            return
        if scrub:
            try:
                subprocess.run(["exiftool", "-all=", p], capture_output=True, timeout=60)
                W("  🧹 " + T("   (: *_original)", "Metadata removed (backup: *_original)"))
            except Exception as e:
                W("  ❌ %s" % e)
        W("  ── ⭐ " + T("   :", "Device & location summary:") + " ──")
        d = {}
        try:
            r = subprocess.run(["exiftool", "-json", "-n", "-q", "-m", p],
                               capture_output=True, text=True, timeout=30)
            d = (_json.loads(r.stdout or "[]") or [{}])[0]
        except Exception:
            d = {}
        dev = []
        for k in ("Make", "Model", "DeviceName", "LensModel", "Software", "OperatingSystem"):
            if d.get(k):
                dev.append("%s: %s" % (k, d[k]))
        if dev:
            W("     📱 " + " | ".join(dev))
        when = d.get("DateTimeOriginal") or d.get("CreateDate") or d.get("ModifyDate")
        if when:
            W("     🕒 " + T(" :", "Taken:") + " %s" % when)
        lat = d.get("GPSLatitude")
        lon = d.get("GPSLongitude")
        if lat is not None and lon is not None:
            W("     📍 " + T(" GPS:", "GPS location:") + " %s, %s" % (lat, lon))
            if d.get("GPSAltitude") is not None:
                W("     ⛰ " + T(":", "Altitude:") + " %s m" % d.get("GPSAltitude"))
            W("     🗺 https://www.google.com/maps?q=%s,%s" % (lat, lon))
            W("     🌐 https://www.openstreetmap.org/?mlat=%s&mlon=%s#map=17/%s/%s" % (lat, lon, lat, lon))
        else:
            W("     📍 " + T("GPS    ✅ (  )", "No GPS in file ✅ (privacy-safe)"))
        W("\n  ── 🧾 " + T("  exiftool ( ):", "Full exiftool output:") + " ──")
        try:
            out = subprocess.run(["exiftool", "-a", "-u", "-G1", p],
                                 capture_output=True, text=True, timeout=60)
            lines = [l for l in out.stdout.splitlines() if l.strip()]
            if lines:
                for l in lines[:1500]:
                    W("  " + l)
                if len(lines) > 1500:
                    W("  … +%d " % (len(lines) - 1500) + T(" ", "more lines"))
                W("\n  🏁 %d " % len(lines) + T("   ", "metadata tags found"))
            else:
                W("  ℹ " + T("  ", "No metadata found"))
        except Exception as e:
            W("  ❌ %s" % e)

    def _build_subfind(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["subfind"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🌐 ", "🌐 Subdomain Finder"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T("      -  ",
                 "Discover subdomains via common wordlist - fully local"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40, pady=4)
        tk.Label(r, text=self._wl_T(":", "Domain:"), bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.sf_domain = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                                  insertbackground=TH["text"], font=("Courier", 11))
        self.sf_domain.pack(side="left", fill="x", expand=True, padx=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T("▶ ", "▶ Start"), command=self._sf_start,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=4)
        tk.Button(bf, text=self._wl_T("⏹ ", "⏹ Stop"), command=self._sf_stop_set,
                  bg=TH["red"], fg="#fff").pack(side="left", padx=4)
        tk.Label(page, text=self._wl_T("  ( ):", "Wordlist (editable):"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack(anchor="e", padx=44)
        self.sf_words = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 10),
                                height=5, wrap="word", padx=8, pady=6)
        self.sf_words.pack(fill="x", padx=40, pady=4)
        self.sf_words.insert("1.0", "www mail ftp admin dev api blog vpn test ns1 ns2 mx webmail cpanel portal intranet git cdn static app m mobile old new backup db mysql dns gateway proxy secure login wiki docs support status monitor grafana jenkins img images media download files share cloud owa exchange smtp imap pop remote ssh")
        self.sf_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word", padx=10, pady=10)
        self.sf_out.pack(fill="both", expand=True, padx=40, pady=8)
        self.sf_stop = threading.Event()
        self._sf_busy = False

    def _sf_start(self):
        dom = self.sf_domain.get().strip().lower()
        if not dom or self._sf_busy:
            return
        words = self.sf_words.get("1.0", "end").split()
        if not words:
            return
        self._sf_busy = True
        self.sf_stop.clear()
        threading.Thread(target=self._sf_worker, args=(dom, words), daemon=True).start()

    def _sf_stop_set(self):
        self.sf_stop.set()

    def _sf_worker(self, dom, words):
        import socket, random, string
        from concurrent.futures import ThreadPoolExecutor
        T = self._wl_T
        self._write_async(self.sf_out, "\n ── " + T(" ", "Discovering") + " %s ──" % dom, clear=True)
        rand = "".join(random.choices(string.ascii_lowercase, k=12))
        try:
            socket.gethostbyname("%s.%s" % (rand, dom))
            self._write_async(self.sf_out, " ⚠ " + T(" wildcard !", "Wildcard DNS detected; results may be misleading!"))
        except Exception:
            pass
        st = {"ok": 0, "all": 0}
        _lk = threading.Lock()
        def check(w):
            if self.sf_stop.is_set():
                return
            host = "%s.%s" % (w, dom)
            try:
                ip = socket.gethostbyname(host)
                with _lk:
                    st["ok"] += 1
                self._write_async(self.sf_out, "  ✅ %-28s -> %s" % (host, ip))
            except Exception:
                pass
            with _lk:
                st["all"] += 1
        with ThreadPoolExecutor(max_workers=8) as ex:
            for w in words:
                if self.sf_stop.is_set():
                    break
                ex.submit(check, w)
        self._write_async(self.sf_out, "\n  🏁 " + T(":", "Done:") + " %d/%d " % (st["ok"], st["all"]) + T("  ", "subdomains found"))
        self._sf_busy = False

    # ══ AIRGEDDON ══
    def _build_airgeddon(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["airgeddon"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("📡 Airgeddon - ", "📡 Airgeddon - WiFi Pentest"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T("       !",
                                       "Only on networks you own or have written permission for!"),
                 bg=TH["bg"], fg=TH["red"], font=TH["font_b"]).pack()
        info = tk.Frame(page, bg=TH["bg"])
        info.pack(fill="x", padx=40, pady=6)
        tk.Button(info, text=self._wl_T("", "Install"), command=self._ag_install,
                  bg=TH["green"], fg="#000").pack(side="left", padx=3)
        tk.Button(info, text=self._wl_T("", "Refresh"), command=self._ag_refresh_status,
                  bg=TH["card"], fg=TH["text"]).pack(side="left", padx=3)
        self.ag_status = tk.Label(info, text="", bg=TH["bg"], fg=TH["dim"], font=TH["font_s"])
        self.ag_status.pack(side="right")
        console = tk.Frame(page, bg=TH["bg2"], padx=8, pady=8,
                           highlightbackground=TH["border"], highlightthickness=1)
        console.pack(fill="both", expand=True, padx=40, pady=6)
        self.ag_out = tk.Text(console, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word")
        self.ag_out.pack(fill="both", expand=True)
        btns = tk.Frame(page, bg=TH["bg"])
        btns.pack(pady=8)
        tk.Button(btns, text=self._wl_T("▶  Airgeddon ( )", "▶ Start Airgeddon (external terminal)"),
                  command=self._ag_start, bg=TH["green"], fg="#000", font=TH["font_b"]).pack()

    def _ag_refresh_status(self):
        T = self._wl_T
        path = shutil.which("airgeddon")
        if path:
            ver = ""
            try:
                with open(path, errors="ignore") as f:
                    head = f.read(20000)
                m = re.search(r'airgeddon_version="([^"]+)"', head)
                if m:
                    ver = m.group(1)
            except Exception:
                pass
            ifs = []
            try:
                base = "/sys/class/net"
                for d in sorted(os.listdir(base)):
                    if d != "lo" and os.path.isdir(os.path.join(base, d, "wireless")):
                        ifs.append(d)
            except Exception:
                pass
            txt = T(" ", "Installed")
            if ver:
                txt += " | " + ver
            txt += " | " + (", ".join(ifs) if ifs else T("   ", "no wireless iface"))
            self.ag_status.configure(text=txt, fg=TH["green"])
        else:
            self.ag_status.configure(text=T(" - ",
                                            "Not installed - Start installs and runs"), fg=TH["red"])

    def _ag_term(self, body):
        import tempfile
        _fd6, sh = tempfile.mkstemp(prefix="tb_ag_", suffix=".sh")
        try:
            with os.fdopen(_fd6, "w") as f:
                f.write("#!/bin/bash\n" + body + "\necho\nread -p 'Press Enter to close...'\n")
            os.chmod(sh, 0o700)
        except Exception:
            return None
        term = None
        for c0 in ("x-terminal-emulator", "xfce4-terminal", "gnome-terminal", "konsole", "xterm"):
            if shutil.which(c0):
                term = c0
                break
        if not term:
            return None
        return [term, "--", sh] if term == "gnome-terminal" else [term, "-e", sh]

    def _ag_install(self):
        T = self._wl_T
        args = self._ag_term("sudo apt update && sudo apt install -y airgeddon")
        if args is None:
            self._write_async(self.ag_out, T("   : sudo apt install -y airgeddon",
                                             "No terminal; manually: sudo apt install -y airgeddon"), clear=True)
            return
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._write_async(self.ag_out, T("     sudo   .",
                                         "Install terminal opened; enter sudo password there."), clear=True)

    def _ag_start(self):
        T = self._wl_T
        body = ("if ! command -v airgeddon >/dev/null 2>&1; then\n"
                "  echo 'airgeddon not found - installing...'\n"
                "  sudo apt update && sudo apt install -y airgeddon\n"
                "fi\n"
                "if [ \"$(id -u)\" = \"0\" ]; then airgeddon; else sudo airgeddon; fi\n")
        args = self._ag_term(body)
        if args is None:
            self._write_async(self.ag_out, T("   : sudo airgeddon",
                                             "No terminal found; run: sudo airgeddon"), clear=True)
            return
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._write_async(self.ag_out, T(" airgeddon .",
                                         "External terminal opened; airgeddon runs there."), clear=True)

    def _build_ncat(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["ncat"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🔌  Netcat", "🔌 Netcat Interface"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T("       ", "Connect or listen; live send/receive"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40, pady=4)
        self.nc_mode = tk.StringVar(value="connect")
        tk.Radiobutton(r, text=self._wl_T(" ()", "Connect"), variable=self.nc_mode,
                       value="connect", bg=TH["bg"], fg=TH["text"], selectcolor=TH["card"]).pack(side="left", padx=4)
        tk.Radiobutton(r, text=self._wl_T(" ()", "Listen"), variable=self.nc_mode,
                       value="listen", bg=TH["bg"], fg=TH["text"], selectcolor=TH["card"]).pack(side="left", padx=4)
        tk.Label(r, text=self._wl_T(":", "Host:"), bg=TH["bg"], fg=TH["text"]).pack(side="left", padx=(10, 0))
        self.nc_host = tk.Entry(r, bg=TH["card"], fg=TH["text"], width=14,
                                insertbackground=TH["text"], font=("Courier", 11))
        self.nc_host.pack(side="left", padx=3)
        self.nc_host.insert(0, "127.0.0.1")
        tk.Label(r, text=self._wl_T(":", "Port:"), bg=TH["bg"], fg=TH["text"]).pack(side="left")
        self.nc_port = tk.Entry(r, bg=TH["card"], fg=TH["text"], width=7,
                                insertbackground=TH["text"], font=("Courier", 11))
        self.nc_port.pack(side="left", padx=3)
        self.nc_port.insert(0, "4444")
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T("▶ ", "▶ Start"), command=self._nc_start,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=4)
        tk.Button(bf, text=self._wl_T("⏹ ", "⏹ Stop"), command=self._nc_stop,
                  bg=TH["red"], fg="#fff").pack(side="left", padx=4)
        sr = tk.Frame(page, bg=TH["bg"])
        sr.pack(fill="x", padx=40, pady=4)
        self.nc_send = tk.Entry(sr, bg=TH["card"], fg=TH["text"],
                                insertbackground=TH["text"], font=("Courier", 11))
        self.nc_send.pack(side="left", fill="x", expand=True, padx=4)
        self.nc_send.bind("<Return>", lambda e: self._nc_sendline())
        tk.Button(sr, text=self._wl_T(" >", "Send >"), command=self._nc_sendline,
                  bg=TH["card"], fg=TH["text"]).pack(side="left", padx=4)
        self.nc_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word", padx=10, pady=10)
        self.nc_out.pack(fill="both", expand=True, padx=40, pady=8)
        self.nc_proc = None

    def _nc_cmd(self, mode, host, port):
        if shutil.which("ncat"):
            return (["ncat", "-l", "-p", port] if mode == "listen" else ["ncat", host, port])
        if shutil.which("nc"):
            return (["nc", "-l", "-p", port] if mode == "listen" else ["nc", host, port])
        return None

    def _nc_start(self):
        if self.nc_proc is not None:
            return
        mode = self.nc_mode.get()
        host = self.nc_host.get().strip()
        port = self.nc_port.get().strip()
        if not port.isdigit():
            return
        cmd = self._nc_cmd(mode, host, port)
        T = self._wl_T
        if cmd is None:
            self._write_async(self.nc_out, "  ❌ " + T("nc/ncat     « »   ncat  ", "nc/ncat not installed; use Packages card with: ncat"), clear=True)
            return
        try:
            self.nc_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception as e:
            self.nc_proc = None
            self._write_async(self.nc_out, "  ❌ %s" % e, clear=True)
            return
        msg = (T("  ...", "Waiting for connection...") if mode == "listen"
               else T("    «» ", "Connected; type and press Send"))
        self._write_async(self.nc_out, "\n  🔌 " + T(":", "Command:") + " " + " ".join(cmd) + "\n  " + msg, clear=True)
        threading.Thread(target=self._nc_reader, daemon=True).start()

    def _nc_reader(self):
        p = self.nc_proc
        try:
            for line in iter(p.stdout.readline, b""):
                self._write_async(self.nc_out, "  ◀ " + line.decode("utf-8", "replace").rstrip("\n"))
        except Exception:
            pass
        self._write_async(self.nc_out, "  ⏹ " + self._wl_T("  ", "Connection closed"))
        self.nc_proc = None

    def _nc_sendline(self):
        p = self.nc_proc
        if p is None or p.poll() is not None:
            return
        data = self.nc_send.get()
        if not data:
            return
        try:
            p.stdin.write((data + "\n").encode("utf-8", "replace"))
            p.stdin.flush()
            self._write_async(self.nc_out, "  ▶ " + data)
            self.nc_send.delete(0, "end")
        except Exception:
            pass

    def _nc_stop(self):
        p = self.nc_proc
        if p is not None:
            try:
                p.kill()
            except Exception:
                pass

    # ══ EXPLOIT FINDER -   ══
    def _build_exploitfinder(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["exploitfinder"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("💥  ", "💥 Exploit Finder"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T(" CVE       NVD",
                 "Search CVEs from the official NVD database"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40, pady=4)
        self.ef_q = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                             insertbackground=TH["text"], font=("Courier", 11))
        self.ef_q.pack(side="left", fill="x", expand=True, padx=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T("▶ ", "▶ Search"), command=self._ef_run,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=4)
        tk.Button(bf, text=self._wl_T("⏹ ", "⏹ Stop"), command=self._ef_stop_set,
                  bg=TH["red"], fg="#fff").pack(side="left", padx=4)
        self.ef_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word", padx=10, pady=10)
        self.ef_out.pack(fill="both", expand=True, padx=40, pady=8)
        self.ef_stop = threading.Event()
        self._ef_busy = False

    def _ef_run(self):
        q = self.ef_q.get().strip()
        if not q or self._ef_busy:
            return
        self._ef_busy = True
        self.ef_stop.clear()
        threading.Thread(target=self._ef_worker, args=(q,), daemon=True).start()

    def _ef_stop_set(self):
        self.ef_stop.set()

    def _ef_http(self, url, timeout=15):
        import urllib.request, urllib.error
        req = urllib.request.Request(url, headers={"User-Agent":
            "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"})
        try:
            r = urllib.request.urlopen(req, timeout=timeout)
            return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception:
            return None, b""

    def _ef_worker(self, q):
        import json
        from urllib.parse import quote
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.ef_out, s, clear=clear)
        try:
            W("\n  ── 💥 " + T("", "Searching") + " %s ──" % q, clear=True)
            url = ("https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch="
                   + quote(q) + "&resultsPerPage=15")
            W("  🌐 NVD ...")
            code, data = self._ef_http(url)
            if code == 200:
                d = json.loads(data.decode("utf-8", "replace"))
                vs = d.get("vulnerabilities", [])
                W("  📦 %d " % len(vs) + T("  ", "results"))
                for v in vs:
                    if self.ef_stop.is_set():
                        break
                    c = v.get("cve", {})
                    W("  • %s" % c.get("id", "?"))
                    for dd in c.get("descriptions", []):
                        if dd.get("lang") == "en":
                            W("      %s" % dd.get("value", "")[:110])
                            break
                W("  🔗 EDB: https://www.exploit-db.com/search?term=" + quote(q))
            elif code == 403:
                W("  ⚠ " + T("  NVD     ", "NVD rate limit; retry later"))
            else:
                W("  ❌ HTTP %s" % code)
            W("  🏁 " + T(" ", "Search done"))
        except Exception as e:
            import traceback
            traceback.print_exc()
            W("  ❌ %s" % e)
        finally:
            self._ef_busy = False

    # ══ WEB TOOLS -   ══
    def _build_webtools(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["webtools"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🌍  ", "🌍 Web Tools"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        tk.Label(page, text=self._wl_T("   CMS  robots.txt",
                 "Headers, server tech, CMS & robots.txt"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40, pady=4)
        self.wt_q = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                             insertbackground=TH["text"], font=("Courier", 11))
        self.wt_q.pack(side="left", fill="x", expand=True, padx=5)
        bf = tk.Frame(page, bg=TH["bg"])
        bf.pack(pady=5)
        tk.Button(bf, text=self._wl_T("▶ ", "▶ Run"), command=self._wt_run,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=4)
        tk.Button(bf, text=self._wl_T("🤖 robots", "🤖 robots"), command=self._wt_robots,
                  bg=TH["card"], fg=TH["text"]).pack(side="left", padx=4)
        self.wt_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                              state="disabled", wrap="word", padx=10, pady=10)
        self.wt_out.pack(fill="both", expand=True, padx=40, pady=8)

    def _wt_norm(self):
        u = self.wt_q.get().strip()
        if u and not u.startswith("http"):
            u = "https://" + u
        return u

    def _wt_run(self):
        u = self._wt_norm()
        if u:
            threading.Thread(target=self._wt_worker, args=(u, False), daemon=True).start()

    def _wt_robots(self):
        u = self._wt_norm()
        if u:
            threading.Thread(target=self._wt_worker, args=(u, True), daemon=True).start()

    def _wt_http(self, url, timeout=8):
        import urllib.request, urllib.error
        req = urllib.request.Request(url, headers={"User-Agent":
            "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"})
        try:
            r = urllib.request.urlopen(req, timeout=timeout)
            return r.status, r.headers, r.read(300000)
        except urllib.error.HTTPError as e:
            return e.code, e.headers, b""
        except Exception:
            return None, None, b""

    def _wt_worker(self, u, robots):
        T = self._wl_T
        W = lambda s, clear=False: self._write_async(self.wt_out, s, clear=clear)
        try:
            if robots:
                base = "/".join(u.split("/")[:3])
                W("\n  ── 🤖 robots.txt " + base + " ──", clear=True)
                code, _, body = self._wt_http(base + "/robots.txt")
                if code == 200 and body:
                    lines = [l.strip() for l in body.decode("utf-8", "replace").splitlines()
                             if l.strip() and not l.strip().startswith("#")]
                    for l in lines[:40]:
                        W("  " + l)
                    if not lines:
                        W("  ℹ " + T("/ ", "empty"))
                else:
                    W("  ❌ HTTP %s - " % code + T(" ", "not found"))
                return
            W("\n  ── 🌍 " + T("", "Analyzing") + " %s ──" % u, clear=True)
            code, hdrs, body = self._wt_http(u)
            if code is None:
                W("  ❌ " + T("   (DNS/)", "connection failed"))
                return
            W("  📊 HTTP %s" % code)
            if hdrs is not None:
                for h in ("Server", "X-Powered-By", "Content-Type",
                          "Strict-Transport-Security", "X-Frame-Options"):
                    v = hdrs.get(h)
                    if v:
                        W("  • %s: %s" % (h, v))
                sc = hdrs.get_all("Set-Cookie") or []
                if sc:
                    W("  • Set-Cookie: %d " % len(sc) + T("", "items"))
            cms = []
            if body:
                low = body.lower()
                if b"wp-content" in low:
                    cms.append("WordPress")
                if b"joomla" in low:
                    cms.append("Joomla")
                if b"drupal" in low:
                    cms.append("Drupal")
                import re as _re
                m = _re.search(rb'generator["\']? content=["\']([^"\']+)', low)
                if m:
                    cms.append(m.group(1).decode("utf-8", "replace"))
            W("  🧩 CMS: " + (", ".join(cms) if cms else "—"))
            W("  🏁 " + T("", "done"))
        except Exception as e:
            import traceback
            traceback.print_exc()
            W("  ❌ %s" % e)

    # ══ HELP BOOK -   ══







    def _hist_file(self):
        return os.path.join(os.path.expanduser("~"), ".toolbox_history.json")

    def _hist_record_search(self):
        """Save dashboard search query (skipped in Private mode)."""
        try:
            if self.prefs.get("private", False):
                return
            q = self.dash_search.get().strip()
            if len(q) < 2:
                return
            hist = []
            try:
                p = self._hist_file()
                if os.path.exists(p):
                    hist = json.load(open(p, encoding="utf-8"))
            except Exception:
                hist = []
            if not isinstance(hist, list):
                hist = []
            if hist and hist[0] == q:
                return
            hist = [x for x in hist if x != q]
            hist.insert(0, q)
            hist = hist[:50]
            json.dump(hist, open(self._hist_file(), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _show_history(self):
        hist = []
        try:
            p = self._hist_file()
            if os.path.exists(p):
                hist = json.load(open(p, encoding="utf-8"))
            if not isinstance(hist, list):
                hist = []
        except Exception:
            hist = []
        win = tk.Toplevel(self.root)
        win.title("Search History")
        win.geometry("460x380")
        win.configure(bg=TH["bg"])
        sb = tk.Scrollbar(win, orient="vertical")
        t = tk.Text(win, bg=TH["bg2"], fg=TH["text"], font=("Courier", 10),
                    yscrollcommand=sb.set)
        sb.configure(command=t.yview)
        sb.pack(side="right", fill="y")
        t.pack(fill="both", expand=True, padx=8, pady=8)
        if not hist:
            t.insert("1.0", "  History is empty.\n"
                            "  Type a search on the dashboard and press Enter.\n"
                            "  (Private mode in Settings disables recording.)")
        else:
            t.insert("1.0", "  Last %d searches - click one to search again:\n\n" % len(hist))
            for n, q in enumerate(hist, 1):
                tag = "h%d" % n
                t.tag_configure(tag, foreground=TH["accent"])
                def _go(qq=q, w=win):
                    try:
                        self.dash_search.delete(0, "end")
                        self.dash_search.insert(0, qq)
                        self._dash_apply_filter()
                        w.destroy()
                    except Exception:
                        pass
                t.tag_bind(tag, "<Button-1>", lambda e, g=_go: g())
                t.insert("end", "  %2d. %s\n" % (n, q), tag)
            def _wipe(w=win):
                try:
                    os.remove(self._hist_file())
                except Exception:
                    pass
                w.destroy()
                self._show_history()
            bar = tk.Frame(win, bg=TH["bg"])
            bar.pack(fill="x", padx=8, pady=(0, 8))
            tk.Button(bar, text="Clear all history", command=_wipe,
                      bg=TH["red"], fg="#fff", font=TH["font_s"]).pack(side="left")
        t.configure(state="disabled")
        def _hw(ev, t=t):
            d = -1 if getattr(ev, "delta", 0) > 0 else 1
            if getattr(ev, "num", None) == 4:
                d = -1
            elif getattr(ev, "num", None) == 5:
                d = 1
            t.yview_scroll(d * 3, "units")
            return "break"
        for _sq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            t.bind(_sq, _hw)
            win.bind(_sq, _hw)
            sb.bind(_sq, _hw)


    # ══ PHONE INFO ══
    def _ph_digits(self, s):
        return _digits_en(s)
    _PH_OPS = {
        "910": (" ", "MCI"), "911": (" ", "MCI"),
        "912": (" ", "MCI"), "913": (" ", "MCI"),
        "914": (" ", "MCI"), "915": (" ", "MCI"),
        "916": (" ", "MCI"), "917": (" ", "MCI"),
        "918": (" ", "MCI"), "919": (" ", "MCI"),
        "990": (" ", "MCI"), "991": (" ", "MCI"),
        "992": (" ", "MCI"), "993": (" ", "MCI"),
        "994": (" ", "MCI"),
        "901": ("", "Irancell"), "902": ("", "Irancell"),
        "903": ("", "Irancell"), "905": ("", "Irancell"),
        "930": ("", "Irancell"), "933": ("", "Irancell"),
        "935": ("", "Irancell"), "936": ("", "Irancell"),
        "937": ("", "Irancell"), "938": ("", "Irancell"),
        "939": ("", "Irancell"),
        "920": ("", "Rightel"), "921": ("", "Rightel"),
        "922": ("", "Rightel"), "923": ("", "Rightel"),
        "998": (" ", "Shatel")}
    _PH_GEN = {
        "912": ("1", "1382-1390"), "910": ("3-4", "1395-1402"),
        "911": ("1-2", "1383-1392"), "913": ("1-2", "1384-1393"),
        "914": ("1-2", "1384-1393"), "915": ("1-2", "1384-1393"),
        "916": ("1-2", "1384-1393"), "917": ("1-2", "1384-1393"),
        "918": ("1-2", "1384-1393"), "919": ("2", "1388-1395"),
        "990": ("4", "1397-1403"), "991": ("4", "1398-1403"),
        "992": ("4", "1399-1403"), "993": ("4", "1400-1403"),
        "994": ("4-5", "1401-1403"),
        "901": ("3-4", "1395-1402"), "902": ("4", "1397-1403"),
        "903": ("4", "1397-1403"), "905": ("4", "1398-1403"),
        "930": ("4", "1398-1403"), "933": ("4", "1398-1403"),
        "935": ("2", "1386-1395"), "936": ("2", "1386-1395"),
        "937": ("2", "1386-1395"), "938": ("2-3", "1390-1398"),
        "939": ("3", "1393-1400"),
        "920": ("3", "1393-1400"), "921": ("3-4", "1395-1402"),
        "922": ("4", "1398-1403"), "923": ("4", "1400-1403"),
        "998": ("4", "1398-1403")}

    _PH_PRE = {"912": "post", "910": "post",
               "919": "pre", "930": "pre", "933": "pre", "935": "pre",
               "936": "pre", "937": "pre", "938": "pre", "939": "pre",
               "901": "pre", "902": "pre", "903": "pre", "905": "pre",
               "920": "pre", "921": "pre", "922": "pre", "923": "pre",
               "990": "pre", "991": "pre", "992": "pre", "993": "pre",
               "994": "pre", "998": "pre"}

    def _ph_rand(self, tail):
        import re as _r
        score, notes = 0, []
        if len(set(tail)) == 1:
            score += 3; notes.append("all same digits")
        if tail == tail[::-1] and len(set(tail)) > 1:
            score += 2; notes.append("mirror")
        if all(abs(ord(a) - ord(b)) == 1 for a, b in zip(tail, tail[1:])):
            score += 2; notes.append("sequential")
        if _r.search(r"(\d)\1{2}$", tail):
            score += 2; notes.append("repeated ending")
        if _r.fullmatch(r"(\d+)(\1)+", tail):
            score += 2; notes.append("repeating pattern")
        return score, notes

    def _build_phoneinfo(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["phoneinfo"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("📱  ", "📱 Phone Info"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40)
        self.ph_entry = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                                 insertbackground=TH["text"], font=TH["font"])
        self.ph_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.ph_entry.insert(0, "09123456789")
        tk.Button(r, text=self._wl_T("", "Analyze"), command=self._ph_run,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        self.ph_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                              font=("Courier", 11), state="disabled",
                              wrap="word", padx=10, pady=10)
        self.ph_out.pack(fill="both", expand=True, padx=40, pady=8)

    def _ph_run(self):
        d = self._ph_digits(self.ph_entry.get())
        if d.startswith("0098"): d = "0" + d[4:]
        elif d.startswith("+98"): d = "0" + d[3:]
        elif d.startswith("98") and len(d) == 12: d = "0" + d[2:]
        elif d.startswith("9") and len(d) == 10: d = "0" + d
        if len(d) != 11 or not d.startswith("09"):
            self._write(self.ph_out, "  ❌ Invalid number - e.g. 09123456789", True)
            return
        pre = d[1:4]
        op = self._PH_OPS.get(pre)
        op_name = op[1] if op else "Unknown"
        L = ["", "  ── 📋 Basic info ──",
             "  📱 Mobile line: " + d,
             "  Prefix: 0" + pre,
             "  Operator: " + op_name,
             "", "  ── 📡 SIM generation & issue ──",
             "  SIM generation: " + str(self._PH_GEN.get(pre, ("?", "?"))[0]),
             "  Estimated issue year: " + str(self._PH_GEN.get(pre, ("?", "?"))[1]),
             "  👤 Owner name: only via operator inquiry",
             "  (For privacy, this info is not public)",
             "", "  ── Country info ──",
             "  Country: 🇮🇷 Iran", "  Country code: +98",
             "  Timezone: Asia/Tehran (UTC+3:30)", "  Language: Persian", "  Currency: Rial (IRR)",
             "", "  ── 🔗 Different formats ──",
             "  With spaces: " + d[:4] + " " + d[4:7] + " " + d[7:],
             "  Without zero: " + d[1:],
             "  International: +98 " + d[1:4] + " " + d[4:7] + " " + d[7:],
             "  💬 WhatsApp: https://wa.me/98" + d[1:]]
        score, notes = self._ph_rand(d[4:])
        L += ["", "  ── ⭐ Advanced randomness analysis ──", "  Randomness score: " + str(score)]
        if score >= 4: L.append("  Level: ⭐ Special rand")
        elif score >= 1: L.append("  Level: semi-rand")
        for n2 in notes: L.append("    · " + n2)
        if score == 0: L.append("  Level: Normal")
        pt = self._PH_PRE.get(pre)
        L += ["", "  ── 💳 Prepaid / Postpaid detection ──"]
        if pt == "pre": L.append("  💳 Line type: Prepaid")
        elif pt == "post": L.append("  📋 Line type: Postpaid")
        else: L.append("  🔄 Line type: both possible")
        if score >= 4: L.append("  → Due to randomness, postpaid is more likely")
        L += ["", "  ── 🔒 Security analysis ──", "  ✔ No suspicious pattern",
              "  ⚠ MNP possible: the real operator may differ"]
        self._write(self.ph_out, "\n".join(L), True)

    def _build_passcheck(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["passcheck"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🔑  ", "🔑 Pass Check"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40)
        self.pc_entry = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                                 insertbackground=TH["text"], font=TH["font"], show="*")
        self.pc_entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(r, text=self._wl_T("", "Check"), command=self._pc_run,
                  bg=TH["accent"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        self.pc_out = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                              font=("Courier", 11), state="disabled",
                              wrap="word", padx=10, pady=10)
        self.pc_out.pack(fill="both", expand=True, padx=40, pady=8)

    def _pc_time(self, ent):
        secs = (2 ** ent) / 1e10
        if secs < 1: return self._wl_T("   ", "< 1 second")
        if secs < 60: return self._wl_T(" ", "seconds")
        if secs < 3600: return self._wl_T(" ", "minutes")
        if secs < 86400: return self._wl_T(" ", "hours")
        if secs < 31536000: return self._wl_T(" ", "months")
        if secs < 31536000 * 1000: return self._wl_T(" ", "years")
        return self._wl_T(" ", "centuries")

    def _pc_run(self):
        import math
        p = self.pc_entry.get()
        T = lambda f, e: e
        if not p:
            self._write(self.pc_out, T("  ❌   ", "  ❌ No password"), True)
            return
        pool = 0
        if any(c.islower() for c in p): pool += 26
        if any(c.isupper() for c in p): pool += 26
        if any(c.isdigit() for c in p): pool += 10
        if any(not c.isalnum() for c in p): pool += 32
        ent = int(len(p) * math.log2(pool)) if pool else 0
        if ent >= 90: st = T("🟢  ", "🟢 Very strong")
        elif ent >= 60: st = T("🟢 ", "🟢 Strong")
        elif ent >= 40: st = T("🟡 ", "🟡 Medium")
        else: st = T("🔴 ", "🔴 Weak")
        L = ["",
             "  " + T(": ", "Input: ") + "*" * len(p),
             "  " + T(": ", "Length: ") + str(len(p)),
             "  " + T(" : ", "Pure digits: ") + str(sum(c.isdigit() for c in p)),
             "  " + T(": ", "Entropy: ") + str(ent) + T(" ", " bits"),
             "  " + T(": ", "Status: ") + st,
             "  ⏱ " + T("  (GPU): ", "Crack time (GPU): ") + self._pc_time(ent)]
        self._write(self.pc_out, "\n".join(L), True)

    # ══ CUSTOM EDITOR ══
    def _build_custom_edit(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["custom_edit"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=10)
        tk.Button(top, text=self._wl_T(" >", "< Back"),
                  command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text=self._wl_T("🔧  ", "🔧 Forge Editor"),
                 font=TH["font_h"], bg=TH["bg"], fg=TH["accent"]).pack(pady=5)
        r = tk.Frame(page, bg=TH["bg"])
        r.pack(fill="x", padx=40)
        tk.Label(r, text=self._wl_T(":", "Name:"), bg=TH["bg"],
                 fg=TH["text"]).pack(side="left")
        self.ce_name = tk.Entry(r, bg=TH["card"], fg=TH["text"],
                                insertbackground=TH["text"])
        self.ce_name.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(r, text=self._wl_T("💾 ", "💾 Save"), command=self._ce_save,
                  bg=TH["green"], fg="#000", font=TH["font_b"]).pack(side="left", padx=5)
        tk.Label(page, text=self._wl_T(" (   ):", "Commands (one per line):"),
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack(anchor="w", padx=44)
        self.ce_steps = tk.Text(page, bg=TH["bg2"], fg=TH["text"],
                                font=("Courier", 11), height=8)
        self.ce_steps.pack(fill="both", expand=True, padx=40, pady=6)
        self.ce_list = tk.Label(page, text="", bg=TH["bg"], fg=TH["dim"],
                                font=TH["font_s"], justify="right")
        self.ce_list.pack(pady=(0, 10))
        self._ce_refresh()

    def _ce_refresh(self):
        tools = self._ct_load()
        if tools:
            self.ce_list.configure(text=self._wl_T(" : ", "Current tools: ") +
                                        " ".join(t.get("name", "?") for t in tools))
        else:
            self.ce_list.configure(text=self._wl_T("  ", "No tools yet"))

    def _ce_save(self):
        name = self.ce_name.get().strip()
        lines = [l.strip() for l in self.ce_steps.get("1.0", "end").splitlines() if l.strip()]
        if not name or not lines:
            return
        tools = self._ct_load()
        tools.append({"id": "ct%d" % (len(tools) + 1), "name": name, "vars": {},
                      "steps": [{"cmd": l} for l in lines]})
        self._ct_save(tools)
        self.ce_name.delete(0, "end")
        self.ce_steps.delete("1.0", "end")
        self._ce_refresh()


    def _dash_bind_wheel(self, w):
        def _up(e):
            self.dash_canvas.yview_scroll(-3, "units")
        def _dn(e):
            self.dash_canvas.yview_scroll(3, "units")
        w.bind("<Button-4>", _up)
        w.bind("<Button-5>", _dn)
        for ch in w.winfo_children():
            self._dash_bind_wheel(ch)

    def _attach_scrollbars(self):
        for name, page in list(self.pages.items()):
            try:
                self._sb_walk(page)
            except Exception:
                pass

    def _sb_walk(self, w):
        for ch in list(w.winfo_children()):
            if isinstance(ch, tk.Text):
                self._sb_attach(ch)
            self._sb_walk(ch)

    def _sb_attach(self, ch):
        if getattr(ch, "_sb_done", False):
            return
        ch._sb_done = True
        try:
            info = ch.pack_info()
            pack_opts = {}
            for k in ("side", "fill", "expand", "padx", "pady"):
                if k in info and info[k]:
                    pack_opts[k] = info[k]
        except Exception:
            pack_opts = {"fill": "both", "expand": 1}
        parent = ch.master
        sb = tk.Scrollbar(parent, orient="vertical", command=ch.yview,
                          bg=TH["card"], troughcolor=TH["bg"])
        ch.pack_forget()
        sb.pack(side="right", fill="y", padx=(6, 0))
        ch.pack(**pack_opts)
        ch.configure(yscrollcommand=sb.set)
        def _w_up(e, c=ch):
            c.yview_scroll(-3, "units")
        def _w_dn(e, c=ch):
            c.yview_scroll(3, "units")
        ch.bind("<Button-4>", _w_up)
        ch.bind("<Button-5>", _w_dn)

    def _build_settings_scrolled(self):
        holder = {}
        orig_Frame = tk.Frame
        app = self
        def patched_Frame(master=None, *a, **k):
            if master is app.content and "inner" not in holder:
                outer = orig_Frame(app.content, bg=TH["bg"])
                vsb = tk.Scrollbar(outer, orient="vertical")
                vsb.pack(side="right", fill="y")
                cv = tk.Canvas(outer, bg=TH["bg"], highlightthickness=0, yscrollcommand=vsb.set)
                cv.pack(side="left", fill="both", expand=True)
                vsb.config(command=cv.yview)
                inner = orig_Frame(cv, bg=TH["bg"])
                win = cv.create_window((0, 0), window=inner, anchor="nw")
                def _on_conf(e, cv=cv, win=win):
                    cv.configure(scrollregion=cv.bbox("all"))
                    try:
                        cv.itemconfig(win, width=max(1, cv.winfo_width() - 2))
                    except Exception:
                        pass
                inner.bind("<Configure>", _on_conf)
                cv.bind("<Configure>", _on_conf)
                holder["inner"] = inner
                holder["outer"] = outer
                holder["cv"] = cv
                return inner
            return orig_Frame(master, *a, **k)
        tk.Frame = patched_Frame
        try:
            self._build_settings()
        finally:
            tk.Frame = orig_Frame
        if "outer" in holder:
            outer, inner, cv = holder["outer"], holder["inner"], holder["cv"]
            outer._scroll_inner = inner
            self.pages["settings"] = outer
            def _wheel(e, cv=cv):
                if getattr(e, "num", None) == 4:
                    cv.yview_scroll(-3, "units")
                elif getattr(e, "num", None) == 5:
                    cv.yview_scroll(3, "units")
                else:
                    cv.yview_scroll(-1 if getattr(e, "delta", 0) > 0 else 1, "units")
            def _bind_all(w):
                for seq in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
                    try:
                        w.bind(seq, _wheel)
                    except Exception:
                        pass
                for c in w.winfo_children():
                    _bind_all(c)
            _bind_all(cv)
        else:
            print("scroll wrap missed")

    def _build_all_pages(self):
        for _bn in ["dashboard", "ipgeox", "phoneinfo", "passcheck", "passforge",
                    "wordlist", "hostscan", "nmapx", "packx", "sysmon",
                    "settings", "custom", "wifiattack",
                    "webpentest", "bruteforce", "osint", "exploitfinder",
                    "custom_edit", "webtools",
                    "hashid", "exif",
                    "subfind", "ncat", "airgeddon", "guidebot"]:
            try:
                _before = set(self.pages.keys())
            except Exception:
                _before = set()
            try:
                if _bn == "settings":
                    self._build_settings_scrolled()
                else:
                    getattr(self, "_build_" + _bn)()
            except Exception as _e:
                print("BUILD FAIL:", _bn, repr(_e))
            try:
                _new = set(self.pages.keys()) - _before
                if _new:
                    for _k in _new:
                        self._inject_help(self.pages[_k], _bn)
                else:
                    _pg = self.pages.get(_bn)
                    if _pg is not None:
                        self._inject_help(_pg, _bn)
            except Exception:
                pass
    def _rebuild_ui(self):
        try:
            for w in self.content.winfo_children():
                w.destroy()
        except Exception:
            pass
        self.pages = {}
        self._build_all_pages()
        try:
            self._attach_scrollbars()
        except Exception:
            pass
        try:
            self.show_page("dashboard")
        except Exception:
            pass



    def _farewell_night(self, user):
        """Compact decorated night-sky goodbye banner, printed in one shot."""
        import random
        R = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
        COLS = ["\033[97m", "\033[96m", "\033[94m", "\033[95m"]
        try:
            width = min(shutil.get_terminal_size((78, 24)).columns, 78)
        except Exception:
            width = 78
        stars = [".", "*", "+", "\u00b7", "\u02da", "\u2726"]

        def sky(seed):
            rnd = random.Random(seed)
            return "".join(rnd.choice(stars) if rnd.random() < 0.16 else " "
                           for _ in range(width))

        def paint(line, seed):
            rnd = random.Random(seed * 7)
            out = ""
            for ch in line:
                out += " " if ch == " " else rnd.choice(COLS) + ch + R
            return out

        Y = "\033[93m" + BOLD
        moon = [Y + "     \\   |   /" + R,
                Y + "      .-~~~-." + R,
                Y + "     (  \u263d  )" + R,
                Y + "      '-~~~-'" + R,
                Y + "     /   |   \\" + R]
        inner = width - 2
        visible = "\u2726 Good Bye, %s \u2726" % user
        pad = max(0, inner - len(visible))
        lft = pad // 2
        box = [DIM + "\u250c" + "\u2500" * inner + "\u2510" + R,
               DIM + "\u2502" + R + " " * lft +
               "\033[95m" + BOLD + "\u2726 " + R +
               "\033[96m" + BOLD + ("Good Bye, %s" % user) + R +
               "\033[95m" + BOLD + " \u2726" + R +
               " " * (pad - lft) + DIM + "\u2502" + R,
               DIM + "\u2514" + "\u2500" * inner + "\u2518" + R]
        out = ([""] + moon + ["", paint(sky(11), 1), paint(sky(22), 2)] + box +
               [paint(sky(33), 3), ""])
        print("\n".join(out), flush=True)

    def _app_exit(self):
        """Print 'Good Bye <username>' to terminal and exit the app."""
        import getpass
        try:
            user = os.environ.get("SUDO_USER") or getpass.getuser()
        except Exception:
            user = os.environ.get("USER") or "?"
        try:
            self._farewell_night(user)
        except Exception:
            print("Good Bye %s" % user, flush=True)
        try:
            log("Exit: Good Bye %s" % user, "INFO")
        except Exception:
            pass
        self.root.destroy()

    # ══ GUIDE BOT UI ══
    def _gb_engine(self):
        if not hasattr(self, "_gb_e"):
            self._gb_e = ToolboxAI()
        return self._gb_e

    def _gb_add(self, tag, text):
        t = self.gb_chat
        t.configure(state="normal")
        t.insert("end", text + "\n", tag)
        t.configure(state="disabled")
        t.see("end")

    def _gb_actions(self, items):
        f = self.gb_act
        for w in f.winfo_children():
            w.destroy()
        row = None
        for i, it in enumerate(items):
            if i % 3 == 0:
                row = tk.Frame(f, bg=TH["bg"])
                row.pack(fill="x", pady=1)
            fg = TH["text"] if it[2] == TH["card"] else "#000"
            tk.Button(row, text=it[0], command=it[1], bg=it[2], fg=fg,
                      font=TH["font_s"]).pack(side="left", padx=2)

    def _gb_ask(self, q=None):
        if getattr(self, "_gb_busy", False):
            return
        if q is None:
            q = self.gb_in.get().strip()
            self.gb_in.delete(0, "end")
        if not q:
            return
        self._gb_add("u", "You: " + q)
        self._gb_add("b", "")
        self._gb_actions([])
        self._gb_busy = True
        self._gb_think_start()

        def _think():
            try:
                rr = self._gb_engine().answer(q)
            except Exception as e:
                rr = {"kind": "text", "text": "⚠ Answer engine error: %s" % e}
            self._gb_schedule(rr)

        threading.Thread(target=_think, daemon=True).start()

    def _gb_think_start(self):
        self._gb_think_stop = False
        try:
            w = self.gb_chat
            w.configure(state="normal")
            w.insert("end", "\n\U0001f4ad Thinking \u280b", "tbthink")
            w.configure(state="disabled")
            w.see("end")
        except Exception:
            return
        self._gb_think_i = 0
        self._gb_think_tick()

    def _gb_think_tick(self):
        if getattr(self, "_gb_think_stop", True):
            return
        try:
            w = self.gb_chat
            if not w.winfo_exists():
                return
            frames = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"
            self._gb_think_i = getattr(self, "_gb_think_i", 0) + 1
            f = frames[self._gb_think_i % len(frames)]
            rng = w.tag_ranges("tbthink")
            if rng:
                a = w.index(str(rng[0]) + "+1c")
                b = str(rng[-1])
                w.configure(state="normal")
                w.delete(a, b)
                w.insert(a, " \U0001f4ad Thinking " + f, "tbthink")
                w.configure(state="disabled")
                w.see("end")
            else:
                return
        except Exception:
            import traceback
            traceback.print_exc()
        if not getattr(self, "_gb_think_stop", True):
            try:
                self.gb_chat.after(120, self._gb_think_tick)
            except Exception:
                pass
    def _gb_think_end(self):
        self._gb_think_stop = True
        try:
            w = self.gb_chat
            rng = w.tag_ranges("tbthink")
            if rng:
                w.configure(state="normal")
                w.delete(rng[0], rng[-1])
                w.configure(state="disabled")
        except Exception:
            pass

    def _gb_schedule(self, r):
        o = getattr(self, "root", None)
        if o is None or not hasattr(o, "after"):
            o = self if hasattr(self, "after") else None
        if o is None:
            self._gb_render(r)
            return
        o.after(0, lambda: self._gb_render(r))

    def _gb_render(self, r):
        self._gb_think_end()
        self._gb_busy = False
        k = r.get("kind")
        if k == "clear":
            self.gb_chat.configure(state="normal")
            self.gb_chat.delete("1.0", "end")
            self.gb_chat.configure(state="disabled")
            self._gb_add("h", "Chat cleared.")
            return
        if k == "text":
            self._gb_add("b", r["text"])
            return
        if k == "dno":
            self._gb_add("w", r["text"])
            return
        if k == "none":
            self._gb_add("b", r["text"])
            self._gb_actions([("Open " + nm, lambda p=p: self.show_page(p), TH["green"])
                              for p, nm in r.get("cands", []) if p])
            return
        if k == "plan":
            self._gb_add("h", r["head"])
            self._gb_add("b", r["text"])
            self._gb_actions([("Open " + nm, lambda p=p: self.show_page(p), TH["green"])
                              for p, nm in r.get("pages", [])])
            return
        self._gb_add("h", r["head"])
        self._gb_add("b", r["text"])
        if r.get("rel"):
            self._gb_add("d", "Related: " + ", ".join(r["rel"]))
        items = [("Open " + r["head"].split("  |")[0], lambda p=r["page"]: self.show_page(p), TH["green"])]
        if r.get("wiz"):
            items.append(("Next step", lambda: self._gb_ask("/next"), TH.get("accent2", TH["card"])))
        for fq in r.get("follow", []):
            items.append((fq, lambda t=fq: self._gb_ask(t), TH["card"]))
        self._gb_actions(items)

    def _gb_send(self):
        self._gb_ask()

    def _build_guidebot(self):
        page = tk.Frame(self.content, bg=TH["bg"])
        self.pages["guidebot"] = page
        top = tk.Frame(page, bg=TH["bg"])
        top.pack(fill="x", pady=8)
        tk.Button(top, text="< Back", command=lambda: self.show_page("dashboard"),
                  bg=TH["card"], fg=TH["text"]).pack(side="left")
        tk.Label(page, text="\U0001f916 Toolbox AI - Advanced Web-Enabled Assistant",
                 font=TH["font_h"], bg=TH["bg"], fg=TH.get("accent2", TH["text"])).pack(pady=(4, 0))
        tk.Label(page, text="Which tool? How to run it? Prerequisites? Capability checks? - English only - live web search, full explanations, learning memory.",
                 bg=TH["bg"], fg=TH["dim"], font=TH["font_s"]).pack()
        self.gb_chat = tk.Text(page, bg=TH["bg2"], fg=TH["text"], font=("Courier", 11),
                               wrap="word", state="disabled", padx=10, pady=8)
        self.gb_chat.pack(fill="both", expand=True, padx=30, pady=6)
        for tg, col, fnt in (("u", TH.get("accent", TH["text"]), ("Courier", 11, "bold")),
                             ("b", TH["text"], ("Courier", 11)),
                             ("h", TH.get("accent2", TH["text"]), ("Courier", 11, "bold")),
                             ("d", TH["dim"], ("Courier", 10)),
                             ("w", TH["red"], ("Courier", 11, "bold"))):
            self.gb_chat.tag_configure(tg, foreground=col, font=fnt)
        self.gb_act = tk.Frame(page, bg=TH["bg"])
        self.gb_act.pack(fill="x", padx=30)
        ch = tk.Frame(page, bg=TH["bg"])
        ch.pack(fill="x", padx=30, pady=2)
        for q in ["full wifi audit", "compare hashid vs bruteforce",
                  "Can it crack a WPA handshake?", "Is there a DDoS tool?", "/help"]:
            tk.Button(ch, text=q, font=TH["font_s"], bg=TH["card"], fg=TH["text"],
                      command=lambda t=q: self._gb_ask(t)).pack(side="left", padx=2)
        row = tk.Frame(page, bg=TH["bg"])
        row.pack(fill="x", padx=30, pady=(2, 10))
        self.gb_in = tk.Entry(row, bg=TH["card"], fg=TH["text"],
                              insertbackground=TH["text"], font=TH["font"])
        self.gb_in.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.gb_in.bind("<Return>", lambda e: self._gb_send())
        tk.Button(row, text="Send", command=self._gb_send,
                  bg=TH.get("accent", TH["card"]), fg="#000", font=TH["font_b"]).pack(side="left")
        self._gb_add("h", "Toolbox AI v5.3 ready - LIVE web search (Google-first), full explanations, image search, learning memory & offline archive. English only. /tools lists tools, /help commands, /clear wipes chat.")

    def run(self):
        try:
            self.root.update_idletasks()
            self._attach_scrollbars()
        except Exception:
            pass
        self._play_chime()
        log("GUI started", "INFO")
        self.root.mainloop()

if __name__ == "__main__":
    app = ToolboxApp()
    app.run()
