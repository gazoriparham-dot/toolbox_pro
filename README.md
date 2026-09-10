<div align="center">

# 🛡️ Toolbox Pro

**All-in-one Network Security & OSINT Toolkit with Graphical Interface**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey)
![Language](https://img.shields.io/badge/Language-English-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)

</div>

---

## ⚠️ Legal Disclaimer

> **For authorized use only!**
> This tool is intended for **educational purposes** and security testing on networks/systems **you own or have explicit written permission to test**.
>
> Unauthorized use against third-party systems is illegal in most jurisdictions. The developers assume **no liability** for misuse.

---

## 📖 About the Project

**Toolbox Pro** is an integrated, graphical toolkit that combines over 20 specialized capabilities for security testing, network reconnaissance, OSINT, system monitoring, and AI-assisted guidance into a single user-friendly interface. Instead of managing multiple terminal windows and remembering complex commands, everything is accessible through one unified dashboard.

### Why Toolbox Pro?

- ✅ Full graphical interface with Tkinter — no command memorization required
- ✅ 20+ specialized tools in one application
- 🌍 **Language: English** (more languages coming in future updates)
- ✅ AI assistant for guidance and answering questions
- ✅ Custom tool builder (Forge) for creating personalized workflows
- ✅ Asynchronous command execution without freezing the UI
- ✅ Comprehensive logging system for activity tracking

---

## ✨ Features

### 🔐 Security

| Tool | Description |
|------|-------------|
| Password Checker | Analyzes password strength against security criteria |
| Hash Identifier | Automatically detects hash types |
| Web Pentest | Performs basic web security checks |
| Port Scanner | Scans open ports and identifies services |

### 🌐 Network

| Tool | Description |
|------|-------------|
| LAN Scanner | Discovers devices on your local network |
| IP Analyzer | Provides geolocation and ISP information |
| WiFi Security | Tests wireless network security |
| Netcat Interface | GUI for netcat connections and listening |

### 🕵️ OSINT

| Tool | Description |
|------|-------------|
| Username OSINT | Searches usernames across 28+ platforms |
| Domain Intel | Gathers DNS, WHOIS, SSL, and subdomain data |
| Email Lookup | Analyzes email addresses and Gravatar profiles |
| IP Intelligence | Retrieves geolocation, ISP, and port information |

### 💻 System

| Tool | Description |
|------|-------------|
| System Monitor | Real-time CPU/RAM/network monitoring |
| Package Manager | Installs required system packages automatically |
| Metadata Inspector | Views and scrubs file metadata (EXIF) |

### 🤖 Artificial Intelligence

| Tool | Description |
|------|-------------|
| WebBrain | Intelligent web search and information extraction |
| AIBrain | Context-aware question answering |
| Cortex | Coordination engine for AI components |
| Toolbox AI | Web-enabled assistant with live search capabilities |

### 🔧 Forge
Build custom tools by defining shell commands with variables and execution steps.

---

## 📋 Requirements

### Operating System
> ⚠️ **Linux only** — this tool depends on Linux-specific features (`/proc`, `airmon-ng`, etc.) and will not work on Windows/macOS.

- **Recommended:** Kali Linux, Parrot OS, or Ubuntu 22.04+

### Software

| Requirement | Version | Required |
|-------------|---------|----------|
| Python | 3.10 or higher | ✅ |
| Tkinter | Included with Python | ✅ |
| nmap | Any version | For network scanning |
| aircrack-ng | Any version | For WiFi security tools |
| hashcat | Any version | For hash cracking |
| exiftool | Any version | For metadata inspection |

### Permissions
- **Root/sudo access** is required for network and WiFi tools.

---

## 🚀 Installation & Setup

### ⚡ Quick Install (single command)

    git clone https://github.com/gazoriparham-dot/toolbox_pro.git && cd toolbox_pro && bash install.sh


### 1. Clone the Repository

    git clone https://github.com/gazoriparham-dot/toolbox_pro.git
    cd toolbox_pro

### 2. Install Python Dependencies

    pip install -r requirements.txt

### 3. Install System Packages

    sudo apt update
    sudo apt install -y nmap aircrack-ng hashcat exiftool python3-tk

### 4. Run the Application

    sudo python3 toolbox_pro.py

> 💡 Note: Some tools (like WiFi security) require root privileges. Running with `sudo` ensures full functionality.

---

## 📁 Project Structure

    toolbox_pro/
    ├── toolbox_pro.py      # Main application and GUI
    ├── webbrain.py         # Web search and information extraction module
    ├── aibrain.py          # AI question answering module
    ├── cortex.py           # AI coordination engine
    ├── requirements.txt    # Python dependencies
    ├── README.md           # This file
    └── LICENSE             # MIT license

> 🔴 **Important:** All four Python files (`toolbox_pro.py`, `webbrain.py`, `aibrain.py`, and `cortex.py`) are required for the application to function properly.

---

## 🖥️ Usage Guide

1. Launch the application — the main dashboard appears with categorized tool cards
2. Select a category from the sidebar (Security / Network / OSINT / System / AI)
3. Click on a tool card to open it
4. Enter your target/input and click "Run"
5. View results in the output panel
6. Use the **Toolbox AI** assistant for guidance and help
7. All activities are logged to `~/.toolbox_pro.log`

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'webbrain'` | Ensure all four Python files are in the same directory |
| `tkinter not found` | Install with `sudo apt install python3-tk` |
| `nmap: command not found` | Install with `sudo apt install nmap` |
| UI freezes during operation | Run with `sudo` for proper permissions |
| WiFi tools not working | Ensure your wireless adapter supports monitor mode |

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing`
5. Open a pull request

⚠️ **Note:** Pull requests that facilitate attacks against unauthorized systems will not be accepted.

---

## 🗺️ Roadmap

- [ ] Add unit tests
- [ ] Docker support
- [ ] PDF reporting module
- [ ] **Multi-language support (additional languages)**
- [ ] Enhanced theming and customization
- [ ] Additional Forge capabilities

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**⭐ If you find this project useful, please consider starring it!**

Built with ❤️ for the cybersecurity community

</div>
