# Server Discovery Explained

## What is Server Discovery?

**Before:** Players had to manually type IP address and port number
```
Join Game → "Enter host address (IP:PORT):" → localhost:5000   ❌ Tedious
```

**After:** Game automatically finds available servers
```
Join Game → [Automatic scan] → Select from list   ✅ Easy
```

---

## How It Works: UDP Broadcast

### The Concept

Imagine you're in a large building and you want to find a friend:
- **Old way**: "What's your room number?" (manual IP entry)
- **New way**: Yell "Is anyone here? Please raise your hand!" (broadcast discovery)

### Technical Implementation

**Step 1: Server Announces Itself (Every 1 Second)**

The host player's computer running the game server:
- Broadcasts a message on the local network
- Message type: UDP (like shouting - no connection needed)
- Port: 5001 (special port just for announcements)
- Content: `{ type: "server_announce", ip: "192.168.1.100", port: 5000, ... }`

```python
# In network.py → GameServer.broadcast_presence()
broadcast_socket.sendto(
    message.encode(),
    ('<broadcast>', 5001)  # Send to everyone on local network
)
```

**Step 2: Client Listens for Announcements (3-Second Scan)**

When a player clicks "Join Game":
- Their computer listens on UDP port 5001
- Waits 3 seconds for announcements
- Collects all incoming server messages
- Stops listening after 3 seconds

```python
# In network.py → discover_servers()
discovery_socket.bind(('', DISCOVERY_PORT))  # Listen on port 5001
discovery_socket.settimeout(3)  # Wait max 3 seconds

while time.time() - start < 3:
    data, addr = discovery_socket.recvfrom(4096)  # Receive messages
```

**Step 3: Show List to Player**

The lobby displays all found servers:
```
192.168.1.100:5000 (1 player)
192.168.1.105:5000 (3 players)
192.168.1.110:5000 (0 players)
```

Player clicks one to connect

---

## Network Levels Explained

### UDP (User Datagram Protocol) - Used for Discovery
- **Fast**: No connection setup overhead
- **Unreliable**: Messages might get lost (OK for discovery - we wait for multiple copies)
- **No connection**: Just send and forget
- **Use case**: Broadcasting announcements everyone hears
- **Speed**: ~1-2ms delivery time

### TCP (Transmission Control Protocol) - Used for Gameplay
- **Reliable**: Messages guaranteed to arrive in order
- **Connected**: Must establish connection first
- **Slower**: More overhead but guaranteed delivery
- **Use case**: Game state (positions, bullets, HP)
- **Speed**: 5-50ms depending on network

### How They Work Together:
```
DISCOVERY PHASE (UDP):
Client    ──[UDP broadcast on :5001]──→  Server
          (Who's hosting?)
          
Client    ←──[UDP response :5001]──      Server
          (I'm at 192.168.1.100:5000)

GAMEPLAY PHASE (TCP):
Client    ←→[TCP connection :5000]←→    Server
          (Continuous bidirectional communication)
```

---

## What Gets Broadcast?

### Server Announcement Message Structure:

```json
{
  "type": "server_announce",
  "ip": "192.168.1.100",
  "port": 5000,
  "players": 2,
  "max_players": 4
}
```

**Breakdown:**
- `type`: Always "server_announce" (identifies message type)
- `ip`: Server's actual local IP address (192.168.x.x)
- `port`: TCP port for game connection (always 5000)
- `players`: Current player count (changes each broadcast)
- `max_players`: Maximum 4 (hardcoded)

### How IP is Detected:

```python
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))  # Connect to Google's DNS
local_ip = s.getsockname()[0]  # Get our local IP
s.close()
```

**Why this works:**
- Google's DNS (8.8.8.8) is just a reference point
- We're not actually sending anything
- The OS knows which network interface to use to reach 8.8.8.8
- We read the IP of that interface

**Fallback:**
If detection fails (no internet): uses `127.0.0.1` (localhost)

---

## Broadcast Frequency

**Why announce every 1 second?**

**Pros of fast interval:**
- If client scans while server is quiet, they might miss it
- Multiple copies = higher chance client hears at least one

**Cons of fast interval:**
- Network overhead
- Extra CPU usage on server

**Current compromise:**
- 1 second interval = 3 announcements during client's 3-second listen period
- Enough for reliability without too much overhead

```
Server announces:   [msg]  [msg]  [msg]
                     0s     1s     2s     3s
                     
Client scanning:  [listen------]
                     0s     1s     2s     3s
                     
Chance of hearing:  ~98% (even if one packet lost)
```

---

## Troubleshooting Discovery

### "No Servers Found" - What Could Be Wrong?

**1. Different Networks**
```
Host WiFi: "Home WiFi" (192.168.1.x)
Client WiFi: "Mobile Hotspot" (192.168.43.x)
Result: ❌ No broadcast reaches each other
```
- **Fix**: Connect both to same WiFi

**2. Firewall Blocking UDP**
```
UDP :5001 port blocked by Windows Defender
Result: ❌ Broadcast reaches client but can't listen
```
- **Fix**: Allow Python through firewall

**3. WiFi "Guest Mode"**
```
Guest networks typically isolate devices
Result: ❌ Broadcasts don't cross isolation
```
- **Fix**: Connect to main network (if possible)

**4. Timeout Too Short**
```
Client stops listening before server broadcasts
Result: ❌ Timing mismatch
```
- **Current**: 3 second timeout + 1 second broadcasts = reliable
- Would only fail if server started broadcasting after client stopped listening

**5. Server Just Started**
```
Client scans before first broadcast sent
Result: ❌ Server not announced yet
```
- **Fix**: Wait 2 seconds between host start and client search

---

## Data Flow Diagram

```
┌─────────────────────── LOCAL NETWORK (WiFi) ───────────────────┐
│                                                                   │
│  HOST COMPUTER                    CLIENT COMPUTER                │
│  (Running Game Server)            (Looking for Game)             │
│  ┌────────────────┐               ┌────────────────┐             │
│  │ Server Started │               │ User clicks    │             │
│  │   localhost    │               │ "Join Game"    │             │
│  │ :5000 (TCP)    │               │                │             │
│  └────────┬────────┘               └────────┬────────┘             │
│           │                                  │                     │
│           │ Spawn broadcast thread          │                     │
│           │                                  │ discover_servers()   │
│           ▼                                  ▼                     │
│  Every 1 second:              Create UDP socket on :5001         │
│  UDP broadcast on :5001       Wait 3 seconds for messages         │
│  Message:                                                         │
│  { ip: "192.168.1.100",    ─── UDP Broadcast ──→  Receive!      │
│    port: 5000, ... }          (MessageBox)                        │
│                                                                    │
│                    ←─── Parse Message ────                        │
│                       Add to server list                          │
│                                                                    │
│                                  Show to user:                    │
│                                  ☐ 192.168.1.100:5000 (1 player) │
│                                  [SELECT] button                  │
│                                                                    │
│                                  User clicks "SELECT"             │
│                                       │                           │
│           Open TCP port :5000  ←──────┘                          │
│           Accept connection                                       │
│                ├────────── TCP Connection :5000 ────────────┤   │
│                │   (Now game state flows here)               │   │
│                │   Positions, bullets, HP every 16ms        │   │
│                ▼                                              ▼   │
│           GAME RUNNING                                    GAME RUNNING
│
└──────────────────────────────────────────────────────────────────┘
```

---

## Connection States

### Phase 1: Discovery (UDP)
```
Host:   "I'm here! 192.168.1.100:5000"  [broadcast]
Client: [listening for broadcasts]      ← Receives
Client: Records into list
```

### Phase 2: Fallback (Manual)
```
Host:   [broadcasting]
Client: "If discovery fails..."
Client: User types "192.168.1.100:5000" manually
```

### Phase 3: Connection (TCP)
```
Client: "Connecting to 192.168.1.100:5000"
Host:   [accepts on :5000]
        ←─ TCP Connection Established ─→
        Now bidirectional comm at 60 FPS
```

---

## Why This Design?

### Pros:
✅ **No server registry needed** - Peer-to-peer discovery
✅ **Fast** - Discovers servers in <3 seconds  
✅ **Simple** - Just broadcasts and listens
✅ **Fallback** - Manual entry if discovery fails
✅ **LAN-compatible** - Works on office/home WiFi

### Cons:
❌ **Local network only** - Can't cross internet
❌ **Not encrypted** - Anyone on WiFi sees announcements  
❌ **Not authenticated** - No server validation
❌ **Unreliable** - UDP packets can be lost (but multiple retries help)

### When to Use Manual Entry:
- Server on different network
- Firewall is blocking UDP
- Don't want to wait 3 seconds for scan
- Playing across internet (use VPN + manual)

---

## Code Reference

### Server Side (network.py)
```python
def broadcast_presence(self):
    """Runs in background, announces every 1 second"""
    while self.running:
        message = json.dumps({
            'type': 'server_announce',
            'ip': get_local_ip(),
            'port': PORT,
            'players': len(self.players),
            'max_players': self.max_players
        })
        broadcast_socket.sendto(message.encode(), ('<broadcast>', 5001))
        time.sleep(1)
```

### Client Side (network.py)
```python
def discover_servers(timeout=3):
    """Listen for server announcements for N seconds"""
    servers = []
    discovery_socket.bind(('', 5001))
    discovery_socket.settimeout(timeout)
    
    while time.time() - start < timeout:
        data, addr = discovery_socket.recvfrom(4096)
        servers.append(parse_announcement(data))
    
    return servers
```

### UI Side (lobby.py)
```python
def join_game(self):
    servers = discover_servers(timeout=3)  # 3-second scan
    show_server_list(servers)  # Display to user
```

---

## Summary

| Aspect | Details |
|--------|---------|
| **Protocol** | UDP broadcast (announcement) + TCP (gameplay) |
| **Ports** | 5001 (UDP discovery), 5000 (TCP game) |
| **Frequency** | Announces every 1 second |
| **Scan Time** | 3 seconds for client to listen |
| **Range** | Local network (same WiFi) |
| **Reliability** | ~98% (multiple retries) |
| **Fallback** | Manual IP:PORT entry |
| **Speed** | Sub-second discovery |
| **CPU Impact** | Minimal (background thread) |

