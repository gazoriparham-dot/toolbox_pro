#!/bin/bash
set -e
echo "=== Toolbox Pro Installer ==="
sudo apt update
sudo apt install -y python3-pip python3-tk nmap aircrack-ng hashcat exiftool
pip3 install -r requirements.txt 2>/dev/null || pip3 install --break-system-packages -r requirements.txt
echo ""
echo "=== Done! Run with:  sudo python3 toolbox_pro.py  ==="
