# MEGA MILITIA - Multiplayer Shooter

A local network multiplayer shooter game built with Pygame and socket programming.

## Quick Start

### For Beginners (Windows)

1. **Download/Clone the repository**
   ```bash
   git clone https://github.com/yourusername/MEGA_MILITIA.git
   cd MEGA_MILITIA
   ```

2. **Run setup.bat (one-time setup)**
   - Double-click `setup.bat`
   - This will:
     - Install Python 3.11 (if not already installed)
     - Create a virtual environment
     - Install required packages (pygame, Pillow)
   - Wait for completion (~2 minutes)

3. **Launch the game**
   - Double-click `launch.bat`
   - A tkinter window will appear with game options

### Game Modes

#### Host Game
- Click "Host Game"
- Enter your player name
- The game starts and waits for other players to join
- Share your server address with other players (shown in game window)

#### Join Game
- Click "Join Game"
- Enter your player name
- The game automatically searches for servers on your local network
- Select a server from the list and click "Connect"
- Or manually enter a server address (IP:PORT) if auto-discovery doesn't work

## Features

### Implemented
✅ **Multiplayer Gameplay** - Up to 4 players on local network
✅ **Server Discovery** - Automatically find nearby servers without typing IPs
✅ **Real-time Synchronization** - Position, bullets, and HP synced 60 times per second
✅ **Collision Detection** - Bullets deal 10 HP damage on hit
✅ **Mouse-aimed Bullets** - Click to fire bullets toward mouse cursor
✅ **Health System** - 100 HP per player, death when HP ≤ 0
✅ **Auto-cleanup** - Off-screen bullets and disconnected players removed

### Optional Features (To Contribute)
- [ ] Player sprites and animations
- [ ] Spawn/respawn system
- [ ] Different weapon types
- [ ] Sound effects and music
- [ ] Projectile trails/effects
- [ ] Team system
- [ ] Leaderboard/Kill counter

## How It Works

### Server Discovery (UDP Broadcast)
1. **Host** starts game and broadcasts presence on local network every 1 second
   - Message: `{ type: "server_announce", ip: "192.168.1.100", port: 5000, ... }`
2. **Clients** listen for broadcasts on UDP port 5001 for 3 seconds
3. **Lobby** displays all discovered servers with player counts
4. **Client** connects to selected server via TCP port 5000

### Game Communication (TCP)
1. **Client**: Sends position, bullets, HP every frame → Server
2. **Server**: Broadcasts all player data to all clients every frame
3. **All clients**: Render other players and detect collisions locally

## Troubleshooting

### "No servers found on the network"
- Make sure both computers are on the **same WiFi network**
- Try manual entry: `localhost:5000` (host on same machine)
- Try manual entry: `HOST_IP:5000` (host's actual IP)

### "Could not connect to server"
- Verify firewall isn't blocking ports 5000-5001
- Make sure host game is still running
- Try restarting both games

### "Connection drops during game"
- Network instability or packet loss
- Try moving closer to router
- Restart game and reconnect

## Technical Details

- **Language**: Python 3.11+
- **Networking**: TCP sockets (game state), UDP broadcast (discovery)
- **Threading**: Multi-threaded server handles concurrent clients
- **GUI**: Tkinter lobby, Pygame game window
- **Update Rate**: 60 frames per second

For detailed technical documentation, see `MULTIPLAYER_GUIDE.md`

## Contributing

Thank you for your interest in contributing! This is a learning project, so:
- Focus on small, meaningful features
- Keep code clean and documented
- Test on local network before submitting
- No major rewrites or scope creep

## File Structure

```
MEGA_MILITIA/
├── game.py                 # Main game loop
├── network.py              # Server/client networking code
├── lobby.py                # Tkinter GUI for joining/hosting
├── setup.bat               # One-click setup (Windows)
├── launch.bat              # One-click launcher (Windows)
├── requirements.txt        # Python dependencies
├── MULTIPLAYER_GUIDE.md    # Technical documentation
├── Sprites/                # Game sprite images
└── README.md               # This file
```

## License

MIT License - Feel free to use and modify

---

**Original To-Do (Completed Items Marked)**
- ✅ Sprites - Loaded from Sprites/ directory
- ✅ Bullets - Fire toward mouse, collision detection implemented
- ✅ Multiplayer - 4-player support with socket programming
- ✅ Lobby UI - Player name input, server selection
- 🔄 Other mechanics - (optional, see above)
- 🔄 HUD - Health bar implemented, can extend

Note: The `objects.py` file contains past map-drawing attempts and can be ignored.

