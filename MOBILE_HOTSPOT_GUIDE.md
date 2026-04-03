# Mobile Hotspot Connection Guide

## Problem

When both PCs are connected to an Android (or iPhone) mobile hotspot instead of a regular WiFi router, the automatic server discovery fails because:

- Mobile hotspots **block UDP broadcast packets** (port 5001)
- Both PCs independently start their own servers
- They cannot find or connect to each other

## Solution

The game now has **3 fallback mechanisms** for mobile hotspot scenarios:

### Method 1: Using `server_ip.txt` File (Easiest)

**On the HOST PC (first player to launch):**
1. Run `launch.bat`
2. Game will start and create `server_ip.txt` with the IP address
3. Share this file with the other player (USB, email, cloud drive, etc.)

**On the CLIENT PC (second player):**
1. Copy `server_ip.txt` from the host PC into your game folder
2. Run `launch.bat`
3. Game will automatically find the IP in `server_ip.txt` and connect

### Method 2: Using Environment Variable (Cmd/PowerShell)

**On the HOST PC:**
1. Run `launch.bat`
2. Game displays: `[INFO] This PC's IP: 192.168.1.100:5000` (example)
3. Note this IP address

**On the CLIENT PC:**
1. Open Command Prompt or PowerShell

   **Command Prompt:**
   ```
   set MEGA_SERVER_IP=192.168.1.100
   python game.py
   ```

   **PowerShell:**
   ```
   $env:MEGA_SERVER_IP = "192.168.1.100"
   python game.py
   ```

2. Replace `192.168.1.100` with the actual IP from the host PC

### Method 3: Using `join_server.bat` Script

**On the HOST PC:**
1. Run `launch.bat`
2. Game displays: `[INFO] This PC's IP: 192.168.1.100:5000` (example)

**On the CLIENT PC:**
1. Open Command Prompt
2. Run:
   ```
   join_server.bat 192.168.1.100
   ```
   Replace `192.168.1.100` with the host PC's IP

## Step-by-Step Walkthrough

### Scenario: Two PCs on Android Mobile Hotspot

**Setup:**
- PC1 (host): IP 192.168.1.5
- PC2 (client): IP 192.168.1.100
- Both connected to Android hotspot named "AndroidAP"

**Steps:**

1. **On PC1:**
   - Click `launch.bat`
   - Game starts, prints:
     ```
     [INFO] This computer's IP: 192.168.1.5:5000
     [!] No servers found via broadcast
     [*] Starting new game server...
     [+] Server started on port 5000
     [INFO] This PC's IP: 192.168.1.5:5000
     ```
   - Note the IP: `192.168.1.5`

2. **Share the IP with PC2 (using your preferred method):**
   - Email the IP
   - Text message
   - Or copy `server_ip.txt` via USB/cloud

3. **On PC2:**
   - Option A: Copy `server_ip.txt` from PC1, paste into your game folder, run `launch.bat`
   - Option B: Run `join_server.bat 192.168.1.5`
   - Option C: Run `set MEGA_SERVER_IP=192.168.1.5 && python game.py`

4. **Success:** PC2 connects to PC1's server

## Finding Your Local IP Address

If you need to find your PC's IP address:

**Command Prompt:**
```
ipconfig
```
Look for "IPv4 Address" under your network adapter (e.g., `192.168.1.5`)

**Windows Settings:**
1. Open Settings
2. Network & Internet
3. WiFi
4. Advanced Options
5. Look for "IPv4 address"

## Troubleshooting

### "Could not connect to server"
- Verify the IP address is correct (run `ipconfig` to check current IP)
- Ensure both PCs are connected to the same network
- Check Windows Firewall isn't blocking port 5000

### Both PCs start their own servers
- The environment variable or `server_ip.txt` might not be found
- Try Method 1 (copy `server_ip.txt` file) first
- Verify the IP address is correct

### Connection works on WiFi but not mobile hotspot
- This is expected - UDP broadcast is blocked
- Use one of the three manual methods above
- Regular WiFi will auto-detect without manual steps

## Back to Regular WiFi

On standard WiFi networks (not mobile hotspots), you can simply launch both games:
1. First PC runs `launch.bat` → Starts server
2. Second PC runs `launch.bat` → Automatically discovers and joins

No manual steps needed!

## Technical Details

The game attempts connections in this order:

```
1. Check localhost:5000 (same PC)
   ↓ (fails)
2. UDP broadcast discovery on port 5001
   ↓ (succeeds on WiFi, fails on mobile hotspot)
3a. Use discovered server
   or
3b. Check MEGA_SERVER_IP environment variable
   ↓ (if set)
4a. Connect to that IP
   or
4b. Check server_ip.txt file
   ↓ (if exists)
5a. Connect using IP from file
   or
5b. Start own server (host mode)
```

