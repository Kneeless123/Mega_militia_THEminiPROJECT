# MEGA MILITIA - Setup Guide for Beginners

This guide will walk you through getting MEGA MILITIA running on your computer, step by step.

## What You Need

- **Windows 10 or Windows 11** (setup.bat is Windows-specific)
- **An internet connection** (for Python installation)
- **About 5-10 minutes** for first-time setup

For **Mac/Linux**, see the [Alternative Setup](#alternative-setup-macos-linux) section at the bottom.

---

## Step 1: Get the Game Files

### Option A: Download from GitHub (Easiest)
1. Go to the GitHub repository
2. Click the green **Code** button
3. Click **Download ZIP**
4. Extract the ZIP file to a folder on your computer
   - Example: `C:\Users\YourUsername\Desktop\MEGA_MILITIA`

### Option B: Clone with Git (For Advanced Users)
```bash
git clone https://github.com/yourusername/MEGA_MILITIA.git
cd MEGA_MILITIA
```

---

## Step 2: Run setup.bat (Automatic Setup)

1. **Open File Explorer** and navigate to your `MEGA_MILITIA` folder
2. **Double-click** on `setup.bat`
3. A command window will open and show:
   ```
   ========================================
     MEGA MILITIA - Setup Script
   ========================================
   ```
4. The script will:
   - Check if Python is installed
   - Install Python 3.11 if needed
   - Create a virtual environment
   - Install required packages

5. **Wait for completion** - this takes 2-3 minutes the first time
6. When done, you'll see:
   ```
   ========================================
   [+] Setup complete!
   ========================================
   ```

7. **Press any key** to close the window

**What if something goes wrong?**
- If Python installation fails, install Python 3.11 manually from https://www.python.org
- If pip fails, try unplugging/replugging Ethernet cable or reconnecting WiFi
- Run setup.bat again - it's safe to run multiple times

---

## Step 3: Launch the Game

1. **Double-click** `launch.bat` in your `MEGA_MILITIA` folder
2. A **tkinter window** will appear with options:
   - **Host Game** - Start a game server that others can join
   - **Join Game** - Connect to someone else's game
   - **Exit** - Close the lobby

---

## Playing the Game

### Hosting a Game (Let Others Connect to You)

1. Click **Host Game**
2. Enter your player name (e.g., "Player1")
3. **Game starts!** You're now hosting

   The game window shows:
   - A terrain map at the bottom
   - Your character (green rectangle)
   - Your health bar (top-left)

4. **Share with friends:**
   - Tell them your computer's IP address
   - Tell them to select "Join Game" and enter your IP with port 5000
   - Example: `192.168.1.100:5000`

5. **Controls while playing:**
   - **A** - Move left
   - **X** - Move right
   - **S** - Jump/boost
   - **Z** - Another movement option
   - **Left Mouse Click** - Fire bullet toward mouse cursor

6. **Damage System:**
   - Each bullet hit = 10 HP damage
   - Health regenerates slowly when not hit
   - When HP reaches 0: "YOU ARE DEAD" message appears
   - Currently you stay dead (respawn not yet implemented)

### Joining a Game (Playing on Someone Else's Server)

1. Click **Join Game**
2. Enter your player name
3. The game **automatically searches** for servers on your local network (2-3 seconds)
4. A **Server List** window appears showing all available servers:
   ```
   192.168.1.100:5000 (1/4 players)
   192.168.1.105:5000 (2/4 players)
   ```
   (Each entry shows the server address and current player count)

5. **Select a server** from the list and click **Connect**
6. If no servers found, click **Manual Entry** and type the host's address
7. **Game joins!** You'll see other players on screen

**Play:**
- Use same controls as hosting
- You see other players' positions in real-time
- Shoot their bullets to damage them
- Avoid their bullets

---

## Troubleshooting

### "No servers found on the network"

**Cause 1: Different WiFi Network**
- Verify both computers are connected to the **same WiFi network**
- Servers on different networks can't find each other

**Cause 2: First Server Hasn't Started Broadcasting**
- Wait 5 seconds for the server to start broadcasting
- Try scanning again

**Solution:**
- Click **Manual Entry** and type the host's IP address
- Example: If host's IP is 192.168.1.100, type `192.168.1.100:5000`

**How to find host's IP:**
- On host computer, open Command Prompt and type: `ipconfig`
- Look for "IPv4 Address" under your WiFi adapter
- Looks like: `192.168.1.100`

### "Could not connect to server"

**Cause 1: Firewall Blocking**
- Windows Firewall might be blocking ports 5000-5001
- Try: Settings → Privacy & Security → Windows Defender Firewall → Allow an app through firewall
- Add Python.exe or MEGA_MILITIA

**Cause 2: Wrong IP Address**
- Double-check the IP address and port number
- Make sure host game is still running
- Try using `localhost:5000` if on the same computer

**Cause 3: Host Game Crashed**
- Host player needs to re-run `launch.bat`
- Restart and try joining again

### Game Seems Slow or Laggy

**Cause 1: WiFi Connection Quality**
- Try moving closer to the WiFi router
- Reduce interference (move away from microwave, etc.)

**Cause 2: Lots of Bullets on Screen**
- The more bullets, the more data to sync
- Stop shooting so much 😄

**Cause 3: Network Congestion**
- Other devices on WiFi using bandwidth
- Ask others to stop downloading/streaming

### Game Crashes or Won't Start

**Step 1:** Try running setup.bat again
```
This reinstalls dependencies in case something broke
```

**Step 2:** Delete the `venv` folder and run setup.bat
```
This forces a complete reinstall of the environment
```

**Step 3:** Check Python version
```
Open Command Prompt and type: python --version
Should show 3.11.x or higher
```

---

## Advanced Setup (Mac/Linux)

### Mac Users:

1. **Install Homebrew** (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3.11**:
   ```bash
   brew install python@3.11
   ```

3. **Run setup manually**:
   ```bash
   cd ~/Desktop/MEGA_MILITIA
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Launch game**:
   ```bash
   python game.py
   ```

### Linux Users:

```bash
# Install Python and venv
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-tkinter

# Clone and setup
git clone <repo-url>
cd MEGA_MILITIA
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Launch
python game.py
```

---

## Next Steps

Once you're comfortable running the game:

1. **Try it with friends** - Set up on multiple computers
2. **Explore the code** - Look at game.py, network.py, and lobby.py
3. **Read MULTIPLAYER_GUIDE.md** - Detailed technical documentation
4. **Contribute** - Add new features or improve existing ones!

---

## Getting Help

If something doesn't work:

1. **Check the Troubleshooting section** above
2. **Read MULTIPLAYER_GUIDE.md** for technical details
3. **Search online** for the error message
4. **Ask on GitHub** - Create an issue with your error message

---

## Uninstalling

To completely remove MEGA MILITIA:

1. Delete the `MEGA_MILITIA` folder
2. That's it! No registry keys or system changes

---

**Enjoy playing MEGA MILITIA!** 🎮
