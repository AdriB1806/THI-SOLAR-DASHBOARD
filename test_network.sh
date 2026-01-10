#!/bin/bash

# Network connection test script for THI PV Dashboard
echo "=========================================="
echo "THI PV Dashboard Network Test"
echo "=========================================="
echo ""

echo "Testing network connection to THI server..."
echo ""

# Test DNS resolution
echo "1. Testing DNS resolution for 'jupyterhub-wi':"
if host jupyterhub-wi >/dev/null 2>&1; then
    IP=$(host jupyterhub-wi | awk '/has address/ {print $4}')
    echo "   ✓ SUCCESS - Resolved to: $IP"
    echo "   ✓ You are connected to THI network!"
    CONNECTED=true
else
    echo "   ✗ FAILED - Cannot resolve hostname"
    echo "   ✗ You are NOT connected to THI network"
    CONNECTED=false
fi

echo ""

# Test FTP connection
if [ "$CONNECTED" = true ]; then
    echo "2. Testing FTP connection:"
    python3 -c "
import ftplib
try:
    ftp = ftplib.FTP('jupyterhub-wi', timeout=10)
    try:
        ftp.login('ftpuser', 'ftpuser123')
        ftp.cwd('pvdaten')
        with open('pv.csv', 'wb') as f:
            ftp.retrbinary('RETR pv.csv', f.write)
    finally:
        try:
            ftp.quit()
        except Exception:
            pass
    print('   ✓ FTP connection successful!')
    print('   ✓ Data file downloaded')
    with open('pv.csv', 'r', encoding='utf-8', errors='replace') as f:
        lines = []
        for _ in range(3):
            line = f.readline()
            if not line:
                break
            lines.append(line)
        print(f'   ✓ File preview (showing up to 3 lines):')
        for line in lines:
            print(f'      {line.strip()}')
except Exception as e:
    print(f'   ✗ FTP connection failed: {e}')
"
else
    echo "2. Skipping FTP test (not on THI network)"
    echo ""
    echo "=========================================="
    echo "HOW TO CONNECT TO THI NETWORK:"
    echo "=========================================="
    echo ""
    echo "Option 1: On Campus"
    echo "  - Connect to THI campus WiFi"
    echo ""
    echo "Option 2: Remote Access"
    echo "  - Install THI VPN client"
    echo "  - Connect to THI VPN"
    echo "  - Contact THI IT: it-service@thi.de"
    echo ""
fi

echo ""
echo "=========================================="
echo "Current Network Info:"
echo "=========================================="
echo "IP Address: $(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)"
echo "Network: $(networksetup -getairportnetwork en0 2>/dev/null || echo "N/A")"
echo ""
