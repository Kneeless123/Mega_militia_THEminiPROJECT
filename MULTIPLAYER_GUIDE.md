# MEGA MILITIA - Complete Multiplayer Implementation Guide

## Table of Contents
1. System Architecture Overview
2. Network Module Deep Dive (network.py)
3. Lobby GUI Implementation (lobby.py)
4. Game Integration and Modifications (game.py)
5. Collision Detection System
6. Data Synchronization Flow
7. Threading and Concurrency

---

## Part 1: System Architecture Overview

The multiplayer system follows a **central server architecture**, meaning one player acts as a "host" who runs a game server, and other players connect as clients. This differs from peer-to-peer (P2P) where every player connects to every other player directly.

### Why Central Server?
- **Simpler for small player counts (up to 4)**: One source of truth
- **Easier state management**: Server manages all positions and bullets
- **Fewer network connections**: With 4 players, only 3 connections vs. 6 in P2P
- **Authoritative**: Prevents cheating by centralizing game logic

### Network Communication Flow:
```
Client 1 (sends update) → Server → Broadcasts to all (Client 1, 2, 3, 4)
Client 2 (sends update) → Server → Broadcasts to all (Client 1, 2, 3, 4)
Client 3 (sends update) → Server → Broadcasts to all (Client 1, 2, 3, 4)
```

Each player sends their position, bullets, and HP to the server, and the server broadcasts all player data back to everyone 60 times per second.

---

## Part 2: Network Module Deep Dive (network.py)

### 2.1 Module Imports and Constants

```python
import socket
import json
import threading
import time
from collections import defaultdict
```

**Explanation:**
- `socket`: Python's low-level networking library for TCP/IP communication
- `json`: Used to serialize and deserialize Python dictionaries into text format for transmission
- `threading`: Allows background threads so the server can accept connections while running the game
- `time`: Used for delays and timeout management
- `defaultdict`: (imported but not used in this version) - useful for avoiding KeyError when accessing non-existent keys

```python
HOST = 'localhost'
PORT = 5000
BUFFER_SIZE = 4096
```

**Explanation:**
- `HOST = 'localhost'`: The server listens on localhost (127.0.0.1), meaning only local machines can connect. Change this to '0.0.0.0' to allow internet connections
- `PORT = 5000`: The TCP port number (1-65535). Port 5000 is commonly used for development. Must match on client and server
- `BUFFER_SIZE = 4096`: Maximum bytes to receive in a single `recv()` call. 4KB is typical for text-based game updates

### 2.2 GameServer Class - The Host's Game Server

#### Constructor: `__init__(self, max_players=4)`

```python
def __init__(self, max_players=4):
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server_socket.bind((HOST, PORT))
    self.server_socket.listen(max_players)
```

**Line-by-line explanation:**

1. `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`:
   - `AF_INET`: Address Family Internet (IPv4)
   - `SOCK_STREAM`: TCP protocol (connection-oriented, reliable)
   - Creates a TCP socket object for listening to incoming connections

2. `setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)`:
   - **Problem it solves**: Without this, if you restart the server within 60 seconds, you get "Address already in use" error
   - `SOL_SOCKET`: Socket level option
   - `SO_REUSEADDR`: Allow reusing the address/port immediately
   - `1`: Enable this option
   - This is essential for development so you can restart quickly

3. `bind((HOST, PORT))`:
   - Attaches the socket to localhost:5000
   - This tells the OS "listen for connections on these address/port combinations"
   - Without binding, the socket can't receive connections

4. `listen(max_players)`:
   - Sets the socket to listening mode
   - `max_players` is the backlog (how many pending connections to queue)
   - Once we accept a connection, another can be pending

**Initialization of data structures:**

```python
self.players = {}  # {client_socket: player_id}
self.player_data = {}  # {player_id: {x, y, bullets, hp}}
self.lock = threading.Lock()
self.max_players = max_players
self.running = True
self.player_counter = 0
```

- `self.players`: Dictionary mapping socket objects to player IDs (for tracking who is connected)
- `self.player_data`: Dictionary storing game state for each player
- `self.lock`: **CRITICAL** - A threading lock. When multiple threads access/modify data simultaneously, race conditions occur (data corruption). The lock ensures only one thread modifies data at a time
- `self.running`: Boolean flag to control the server loop
- `self.player_counter`: Auto-increment counter to assign unique IDs (0, 1, 2, 3...)

#### Method: `accept_connections(self)`

```python
def accept_connections(self):
    while self.running and len(self.players) < self.max_players:
        try:
            self.server_socket.settimeout(1)
            client_socket, addr = self.server_socket.accept()
```

**Explanation:**

1. `while self.running and len(self.players) < self.max_players`:
   - Loop continues while server is running AND we haven't reached max players
   - `len(self.players)` counts connected players by checking dictionary size
   - `self.max_players` is 4, so after 4 connections, we stop accepting

2. `self.server_socket.settimeout(1)`:
   - Sets timeout to 1 second
   - Without this, `accept()` would block forever, preventing the server from checking `self.running`
   - With 1-second timeout, if no connection arrives, it raises `socket.timeout` exception
   - Allows graceful server shutdown

3. `client_socket, addr = self.server_socket.accept()`:
   - **Blocking call** waiting for a client to connect
   - Returns TWO things:
     - `client_socket`: New socket object for communicating with this specific client
     - `addr`: Tuple of (IP_address, port) where client connected from

**Connection Registration:**

```python
with self.lock:
    player_id = self.player_counter
    self.player_counter += 1
    self.players[client_socket] = player_id
    self.player_data[player_id] = {'x': 550, 'y': 0, 'bullets': [], 'hp': 100}

threading.Thread(target=self.handle_client, args=(client_socket, player_id), daemon=True).start()
print(f"Player {player_id} joined from {addr}")
```

**Explanation of lock usage (`with self.lock:`):**
- `with` statement ensures lock is acquired and released (even if exception occurs)
- Inside the lock, we safely assign a player_id and register the player
- If two clients connected simultaneously without locking, they might both get ID 0 (data corruption)

**Player initialization:**
- `player_id = self.player_counter`: Gets next available ID
- `self.player_counter += 1`: Increments for next player
- `self.players[client_socket] = player_id`: Maps socket to ID
- `self.player_data[player_id]`: Initializes with starting position (550, 0) and 100 HP

**Thread spawning:**
```python
threading.Thread(target=self.handle_client, args=(client_socket, player_id), daemon=True).start()
```
- Creates a new thread to handle this client
- `target=self.handle_client`: The function to run
- `args=`: Arguments to pass to that function
- `daemon=True`: Thread dies when main thread exits (doesn't prevent shutdown)
- `.start()`: Actually starts the thread

**Exception handling:**

```python
except socket.timeout:
    continue
except Exception as e:
    print(f"Error accepting connection: {e}")
```

- `socket.timeout`: When 1-second timeout expires with no connection, we simply `continue` (check loop condition again)
- Triggers when `self.running` becomes False, allowing graceful shutdown
- Generic exception catches other errors (port already in use, etc.)

#### Method: `handle_client(self, client_socket, player_id)`

```python
def handle_client(self, client_socket, player_id):
    try:
        while self.running:
            data = client_socket.recv(BUFFER_SIZE).decode()
            if not data:
                break
```

**Explanation:**

1. `client_socket.recv(BUFFER_SIZE)`:
   - **Blocking call** waiting to receive up to 4096 bytes from client
   - Returns bytes object (raw binary data)
   - If client closes connection, returns empty bytes `b''`

2. `.decode()`:
   - Converts bytes to string using UTF-8 encoding
   - Example: `b'{"type":"update","data":{...}}'` → `'{"type":"update","data":{...}}'`

3. `if not data: break`:
   - If `data` is empty string (client disconnected), exit loop

**Processing client updates:**

```python
msg = json.loads(data)
with self.lock:
    if msg['type'] == 'update':
        self.player_data[player_id] = msg['data']
    elif msg['type'] == 'disconnect':
        break
```

1. `json.loads(data)`:
   - Converts JSON string to Python dictionary
   - Example: `'{"type":"update","data":{"x":100,"y":50}}'` → `{'type': 'update', 'data': {'x': 100, 'y': 50}}`

2. `with self.lock:`:
   - **CRITICAL**: Lock ensures no race conditions while updating shared state
   - Two threads reading/writing `player_data` simultaneously = corruption

3. `if msg['type'] == 'update':`:
   - Client sent position/bullets/HP update
   - `self.player_data[player_id] = msg['data']`: Replace entire player record with new data

4. `elif msg['type'] == 'disconnect':`:
   - Explicit disconnect message (clean shutdown)

**Broadcasting and cleanup:**

```python
self.broadcast_state()
```

- After processing client update, send current game state to ALL players
- Called in main game loop: 60 times per second

**Finally block (guaranteed execution):**

```python
except Exception as e:
    print(f"Error handling player {player_id}: {e}")
finally:
    with self.lock:
        if client_socket in self.players:
            del self.players[client_socket]
        if player_id in self.player_data:
            del self.player_data[player_id]
    client_socket.close()
    print(f"Player {player_id} disconnected")
```

**Explanation:**
- `finally:` block executes EVEN if exception occurs (guaranteed cleanup)
- Thread-safe removal: Use `with self.lock:` when modifying shared state
- `if client_socket in self.players:` - Check before deleting (safe removal)
- `del self.players[client_socket]`: Remove socket→ID mapping
- `del self.player_data[player_id]`: Remove player's game data
- `client_socket.close()`: Close TCP connection (release OS resources)
- Print message confirming disconnection

#### Method: `broadcast_state(self)`

```python
def broadcast_state(self):
    state = {
        'players': self.player_data
    }
    msg = json.dumps(state)
    with self.lock:
        for client_socket in list(self.players.keys()):
            try:
                client_socket.send(msg.encode())
            except:
                pass
```

**Explanation:**

1. `state = {'players': self.player_data}`:
   - Creates dictionary with all player data
   - Example structure:
   ```python
   {
       'players': {
           0: {'x': 550, 'y': 0, 'bullets': [{'x': 100, 'y': 50}], 'hp': 100},
           1: {'x': 600, 'y': 40, 'bullets': [], 'hp': 85},
           2: {'x': 500, 'y': -20, 'bullets': [...], 'hp': 100}
       }
   }
   ```

2. `msg = json.dumps(state)`:
   - Converts Python dict to JSON string
   - Example: `'{"players": {...}}'`

3. `for client_socket in list(self.players.keys())`:
   - `list()` creates static copy of keys
   - **WHY list()?** Without it, dictionary might change during iteration (RuntimeError)
   - Iterates through all connected clients

4. `client_socket.send(msg.encode())`:
   - `.encode()`: Converts string to bytes (UTF-8)
   - `.send()`: Transmits bytes over TCP to client

5. `except: pass`:
   - If send fails (client disconnected abruptly), silently ignore
   - Prevents server crash if one client goes down

#### Methods: `start()` and `stop()`

```python
def start(self):
    threading.Thread(target=self.accept_connections, daemon=True).start()

def stop(self):
    self.running = False
    self.server_socket.close()
```

**Explanation:**
- `start()`: Spawns background thread running `accept_connections()` loop
  - Daemon thread dies with main thread, preventing resource leaks
- `stop()`: Sets `running = False` and closes socket
  - Main loop checks `self.running`, so it exits gracefully
  - Socket close prevents "Address already in use" on restart

---

### 2.3 GameClient Class - Joining Player's Connection

#### Constructor: `__init__(self, player_id)`

```python
def __init__(self, player_id):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.player_id = player_id
    self.other_players = {}  # {player_id: {x, y, bullets, hp}}
    self.lock = threading.Lock()
    self.running = True
    self.connected = False
```

**Explanation:**
- `socket.socket()`: Create TCP client socket (not bound to any address yet)
- `player_id`: Assigned by server after connection (initially None)
- `other_players`: Dictionary storing data about OTHER players (not self)
- `lock`: Protects `other_players` from race conditions
- `running` / `connected`: Flags for connection lifecycle

#### Method: `connect(self, host=HOST, port=PORT)`

```python
def connect(self, host=HOST, port=PORT):
    try:
        self.socket.connect((host, port))
        self.connected = True
        threading.Thread(target=self.receive_updates, daemon=True).start()
        return True
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False
```

**Explanation:**

1. `self.socket.connect((host, port))`:
   - **Blocking call** - waits until server accepts connection or timeout occurs
   - Raises exception if server not running or unreachable
   - `(host, port)` tuple specifies server address

2. `self.connected = True`:
   - Flag indicating successful connection

3. `threading.Thread(target=self.receive_updates, daemon=True).start()`:
   - Spawns background thread to listen for server updates
   - Without this, `recv()` would block the main game thread
   - Daemon prevents hanging on program exit

4. `return True/False`:
   - Allows caller to check connection success

#### Method: `send_update(self, player_data)`

```python
def send_update(self, player_data):
    try:
        msg = json.dumps({
            'type': 'update',
            'data': player_data
        })
        self.socket.send(msg.encode())
    except Exception as e:
        print(f"Error sending update: {e}")
```

**Explanation:**

1. Creates message dict with `'type': 'update'` and actual data
2. `json.dumps()` serializes to JSON string
3. `.encode()` converts to bytes
4. `.send()` transmits to server
5. Exception likely means connection died (server crashed)

**Called 60 times per second from main game loop:**
```python
client.send_update({
    'x': player.x,
    'y': player.y,
    'bullets': [{'x': b.x, 'y': b.y} for b in bullets],
    'hp': player.hp
})
```

#### Method: `receive_updates(self)` - Background Thread

```python
def receive_updates(self):
    try:
        while self.running and self.connected:
            data = self.socket.recv(BUFFER_SIZE).decode()
            if not data:
                break
            
            state = json.loads(data)
            with self.lock:
                # Only store other players (not self)
                self.other_players = {
                    pid: pdata for pid, pdata in state['players'].items()
                    if pid != self.player_id
                }
    except Exception as e:
        print(f"Error receiving updates: {e}")
    finally:
        self.connected = False
```

**Explanation:**

**Receiving and parsing:**
1. `data = self.socket.recv(BUFFER_SIZE).decode()`:
   - Blocking receive - waits for server to send update
   - Called 60 times per second by server's broadcast
   - `.decode()` converts bytes to string

2. `if not data: break`:
   - Server sent nothing = connection closed gracefully

3. `state = json.loads(data)`:
   - Converts JSON to dict: `{'players': {0: {...}, 1: {...}, ...}}`

**Filtering and storing:**
```python
with self.lock:
    self.other_players = {
        pid: pdata for pid, pdata in state['players'].items()
        if pid != self.player_id
    }
```

**Dictionary comprehension breakdown:**
```python
{pid: pdata for pid, pdata in state['players'].items() 
        if pid != self.player_id}
```

- `.items()`: Returns tuples of (key, value) from dict
- `for pid, pdata in ...`: Unpacks each (player_id, player_data) tuple
- `if pid != self.player_id`: Filter condition - exclude self
- `pid: pdata`: Build new dict with remaining players

**Example:**
```python
state = {
    'players': {
        0: {...my data...},
        1: {...other player 1...},
        2: {...other player 2}
    }
}

# If self.player_id == 0:
self.other_players = {
    1: {...other player 1...},
    2: {...other player 2...}
}
```

**Exception handling:**
```python
except Exception as e:
    print(f"Error receiving updates: {e}")
finally:
    self.connected = False
```

- Any error (network dropout, server crash) sets `connected = False`
- Main game loop checks this and exits gracefully

#### Methods: `get_other_players()` and `disconnect()`

```python
def get_other_players(self):
    with self.lock:
        return dict(self.other_players)
```

**Explanation:**
- **Thread-safe getter** - acquires lock before accessing `other_players`
- Returns a COPY: `dict()` creates independent dict (safe from external modification)
- Main game loop calls this 60 times/sec to draw other players

```python
def disconnect(self):
    self.running = False
    try:
        self.socket.send(json.dumps({'type': 'disconnect'}).encode())
    except:
        pass
    self.socket.close()
```

**Explanation:**
- `self.running = False`: Signals receive thread to exit
- Sends disconnect message (graceful shutdown)
- Catches exception in case server already dead
- Closes socket (releases TCP port)

---

## Part 3: Lobby GUI Implementation (lobby.py)

### 3.1 Tkinter Overview

Tkinter is Python's standard GUI library. It provides widgets (buttons, text fields) for building interfaces.

```python
import tkinter as tk
from tkinter import simpledialog, messagebox
import socket
```

**Explanation:**
- `tk`: Main tkinter module for widgets and window
- `simpledialog`: Pop-up dialogs for asking user input
- `messagebox`: Pop-up error/info messages
- `socket`: Check if server is running before joining

### 3.2 LobbyGUI Class

#### Constructor: `__init__(self, root)`

```python
def __init__(self, root):
    self.root = root
    self.root.title("MEGA MILITIA - Lobby")
    self.root.geometry("400x300")
    self.root.resizable(False, False)
    
    self.game_mode = None  # 'host' or 'join'
    self.player_name = None
    self.host_address = None
    
    self.setup_ui()
```

**Explanation:**

1. `self.root = root`:
   - Saves reference to main window (created before passing to class)

2. `self.root.title("MEGA MILITIA - Lobby")`:
   - Sets window title shown in taskbar/title bar

3. `self.root.geometry("400x300")`:
   - Window size: 400 pixels wide × 300 pixels tall

4. `self.root.resizable(False, False)`:
   - `(False, False)` = (width not resizable, height not resizable)
   - Window size is fixed

5. **Instance variables:**
   - `game_mode`: Will be 'host' or 'join' after button click
   - `player_name`: Input by user in dialog
   - `host_address`: IP:PORT format for join mode

6. `self.setup_ui()`:
   - Calls method to create GUI widgets

#### Method: `setup_ui(self)`

```python
def setup_ui(self):
    tk.Label(self.root, text="MEGA MILITIA", font=("Arial", 20, "bold")).pack(pady=20)
```

**Explanation:**

1. `tk.Label()`:
   - Creates text label widget
   - `text="MEGA MILITIA"`: Displayed text
   - `font=("Arial", 20, "bold")`: Font name, size, style

2. `.pack()`:
   - **Geometry manager** - positions widget in window
   - `pady=20`: Padding above/below (Y-axis) = 20 pixels

3. **NO variable assignment:**
   - Widget appears because `.pack()` adds it to window
   - We don't need reference to it later, so no `var = tk.Label(...)`

**Button frame creation:**

```python
button_frame = tk.Frame(self.root)
button_frame.pack(pady=20)

tk.Button(button_frame, text="Host Game", command=self.host_game, width=15, height=2).pack(pady=10)
tk.Button(button_frame, text="Join Game", command=self.join_game, width=15, height=2).pack(pady=10)
tk.Button(button_frame, text="Exit", command=self.root.quit, width=15, height=2).pack(pady=10)
```

**Explanation:**

1. `tk.Frame(self.root)`:
   - Container widget for organizing buttons vertically
   - `self.root` = parent window

2. `.pack(pady=20)`:
   - Adds 20pixels vertical padding around the frame as a whole

3. **Button creation (3 buttons):**
   - `text`: Button label
   - `command=self.host_game`: Function to call when clicked (NO parentheses - pass function object, not call it)
   - `width=15, height=2`: Button size in character units
   - `.pack(pady=10)`: Stack buttons vertically with 10px spacing

4. `command=self.root.quit`:
   - Built-in method to close window

**Info label (for status messages):**

```python
info_frame = tk.Frame(self.root)
info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

self.info_label = tk.Label(info_frame, text="Select an option to continue", 
                             font=("Arial", 10), fg="gray")
self.info_label.pack()
```

**Explanation:**

1. `info_frame`: Container at bottom of window
   - `side=tk.BOTTOM`: Position frame at bottom
   - `fill=tk.X`: Fill horizontally (stretch to window width)
   - `padx=10, pady=10`: 10px padding all sides

2. `self.info_label = tk.Label(...)`:
   - Store reference for later updates (change text/color)
   - Example: `self.info_label.config(text="New text", fg="green")`

3. `fg="gray"`:
   - `fg` = foreground color (text color)
   - Gray text at start

#### Method: `host_game(self)`

```python
def host_game(self):
    name = simpledialog.askstring("Host Game", "Enter your player name:")
    if name:
        self.player_name = name
        self.game_mode = 'host'
        self.info_label.config(text=f"Hosting game as '{name}'...", fg="green")
        self.root.update()
        self.root.after(1000, self.start_game)
```

**Explanation:**

1. `simpledialog.askstring()`:
   - Pop-up dialog asking for text input
   - Returns user input string or None if cancelled

2. `if name:`:
   - Check if user entered something (not None or empty)

3. `self.player_name = name`:
   - Save player's chosen name

4. `self.game_mode = 'host'`:
   - Mark this as hosting mode
   - Will be checked after `root.mainloop()` returns

5. `self.info_label.config()`:
   - Update label text and color
   - `text=f"..."`: F-string inserts `name` variable
   - `fg="green"`: Change text color to green (success)

6. `self.root.update()`:
   - **Force window refresh** - without this, label update might not show
   - Normally tkinter batches updates, but we want immediate feedback

7. `self.root.after(1000, self.start_game)`:
   - **Schedule function call after 1000ms (1 second)**
   - `self.start_game`: Function to call (no parentheses)
   - Delays 1 second before closing window
   - User sees status message before switching to game

#### Method: `join_game(self)`

```python
def join_game(self):
    host = simpledialog.askstring("Join Game", "Enter host address (IP:PORT):", 
                                   initialvalue="localhost:5000")
    if host:
        name = simpledialog.askstring("Join Game", "Enter your player name:")
        if name:
            self.player_name = name
            self.host_address = host
            self.game_mode = 'join'
            self.info_label.config(text=f"Connecting to {host}...", fg="green")
            self.root.update()
            
            # Try to connect
            if self.test_connection(host):
                self.root.after(500, self.start_game)
            else:
                messagebox.showerror("Connection Failed", f"Could not connect to {host}")
                self.info_label.config(text="Connection failed. Try again.", fg="red")
```

**Explanation:**

1. `simpledialog.askstring(..., initialvalue="localhost:5000")`:
   - Pre-fills input box with default value
   - User can modify or accept default

2. **Nested if statements:**
   - First `if host:` checks if address entered
   - Then `if name:` checks if name entered
   - Both conditions must be true to proceed

3. `self.test_connection(host)`:
   - **Check if server is actually running before showing success**
   - Prevents misleading "Connecting..." message if server not up

4. `messagebox.showerror()`:
   - Error pop-up showing connection failed
   - Stays visible until user clicks OK

5. `info_label.config(text=..., fg="red")`:
   - Red text indicates error state
   - User can try again

#### Method: `test_connection(self, host_addr)`

```python
def test_connection(self, host_addr):
    try:
        host, port = host_addr.split(':')
        port = int(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except:
        return False
```

**Explanation:**

1. `host, port = host_addr.split(':')`:
   - Splits "localhost:5000" into ["localhost", "5000"]
   - Unpacks into two variables

2. `port = int(port)`:
   - Converts string "5000" to integer 5000
   - `connect()` requires integer port

3. `socket.socket()`:
   - Create test socket

4. `s.settimeout(2)`:
   - Don't wait forever - 2 second timeout

5. `result = s.connect_ex((host, port))`:
   - `connect_ex()` returns 0 on success, non-zero on error
   - (Unlike `connect()` which raises exception)
   - Non-blocking friendly

6. `s.close()`:
   - Close test socket

7. `return result == 0`:
   - True if connection succeeded, False otherwise

8. `except: return False`:
   - Any parsing error (bad format) returns False

#### Method: `start_game(self)`

```python
def start_game(self):
    self.root.destroy()
```

**Explanation:**
- `destroy()`: Closes window and exits `root.mainloop()`
- Control returns to game.py which proceeds with game initialization
- The window closure signals that user made their choice

### 3.3 Lobby Invocation in game.py

```python
def show_lobby():
    """Show the tkinter lobby and return (game_mode, player_name, host_address)"""
    root = tk.Tk()
    lobby = LobbyGUI(root)
    root.mainloop()
    
    return lobby.game_mode, lobby.player_name, lobby.host_address
```

**Explanation:**

1. `root = tk.Tk()`:
   - Create main tkinter window (only one per app)

2. `lobby = LobbyGUI(root)`:
   - Pass window to our GUI class (initializes widgets)

3. `root.mainloop()`:
   - **Blocking call** - event loop
   - Waits for user clicks, updates window
   - Only returns when window destroyed (user clicks button)

4. `return lobby.game_mode, ...`:
   - After window closes, return user's choices
   - `game_mode`: 'host' or 'join'
   - `player_name`: What they typed
   - `host_address`: Server address (None if hosting)

**Called at game start:**
```python
game_mode, player_name, host_address = show_lobby()

if not game_mode:
    pygame.quit()
    exit()
```

- If user cancelled (game_mode == None), quit game

---

## Part 4: Game Integration and Modifications (game.py)

### 4.1 New Imports for Networking

```python
import tkinter as tk
from tkinter import messagebox
from lobby import LobbyGUI
from network import GameServer, GameClient
import threading
import json
import time
```

**Explanation:**
- `tkinter`: GUI library for lobby
- `messagebox`: Not used currently, but available for in-game messages
- `LobbyGUI`: Import the lobby class
- `GameServer, GameClient`: Import networking classes
- `threading, json, time`: Already imported in network.py, but main game also uses

### 4.2 Player Class Modifications

#### New Constructor Parameter

```python
def __init__(self, w, h, player_id=0):
    self.player_id = player_id
    self.width = w
    self.height = h
    # ... rest of initialization ...
```

**Explanation:**
- Added `player_id=0`: Identifies which player this object represents
- Default is 0 (host player)
- Used to match with network player data

#### Modified `drawHealth()` Method

```python
def drawHealth(self, x_pos=20, y_pos=20):
    x, y = x_pos, y_pos
    pygame.draw.rect(screen, (0, 0, 0),       (x-2, y-1, 104, 12))
    pygame.draw.rect(screen, (200, 200, 200),  (x-1, y,   102, 10))
    pygame.draw.rect(screen, (70, 150, 50),    (x,   y+1, self.hp, 8))
    x, y = x_pos, y_pos*2
    pygame.draw.rect(screen, (0, 0, 0),       (x-2, y-1, 104, 12))
    pygame.draw.rect(screen, (200, 200, 200),  (x-1, y,   102, 10))
    pygame.draw.rect(screen, (70, 100, 150),    (x,   y+1, self.boost, 8))
```

**Changes:**
- **New parameters**: `x_pos=20, y_pos=20` with defaults
- Allows drawing health bars at different positions (for remote players)
- Old version hard-coded `(20, 20)` - only worked for local player

**Explanation of position parameters:**
```python
x, y = x_pos, y_pos  # HP bar at (x_pos, y_pos)
x, y = x_pos, y_pos*2  # Boost bar at (x_pos, y_pos*2) - twice as far down
```

#### New Method: `draw_remote_player(self, px, py)`

```python
def draw_remote_player(self, px, py):
    """Draw another player at position (px, py)"""
    pos = (px - 64, SCREEN_HEIGHT - py - 64)
    screen.blit(self.animation["idle"][0], pos)
```

**Explanation:**

1. `pos = (px - 64, SCREEN_HEIGHT - py - 64)`:
   - Convert world coordinates to screen coordinates
   - `px - 64`: Center sprite (sprite is 128×128, so offset by 64)
   - `SCREEN_HEIGHT - py - 64`: Flip Y-axis (world Y increases up, screen Y increases down)

2. `self.animation["idle"][0]`:
   - Use first idle animation frame (standing still)
   - Remote players always shown in idle pose (don't have animation data)

3. `screen.blit(...)`:
   - Draw sprite on screen

### 4.3 Bullet Class Modifications

#### Added `owner_id` Parameter

```python
def __init__(self, w, h, spX, spY, x, y, owner_id=0):
    self.owner_id = owner_id
    self.width = w
    self.height = h
    # ... rest unchanged ...
```

**Explanation:**
- `owner_id`: Track which player fired this bullet
- Used to prevent self-damage and identify friendly fire
- Not currently used for damage prevention, but available for future features

#### Existing `draw()`, `update()`, `outOfBounds()` unchanged

These methods already worked correctly:
- `draw()`: Updates position then renders at new location
- `update()`: Adds velocity to position each frame
- `outOfBounds()`: Returns True if bullet left the map

#### New Method: `get_rect()`

```python
def get_rect(self):
    """Returns (x1, y1, x2, y2) for collision detection"""
    return (self.x, self.y, self.x + self.width, self.y + self.height)
```

**Explanation:**
- Returns axis-aligned bounding box (AABB)
- `(x1, y1, x2, y2)` format for collision math
- Currently not used (using simpler collision), but available for future

### 4.4 Collision Detection Function

```python
def check_bullet_player_collision(bullet, player_x, player_y, player_width=128, player_height=128):
    """Check if bullet hits a player"""
    # Player collision box (approximate)
    px_screen = player_x
    py_screen = SCREEN_HEIGHT - player_y
    
    # Bullet position on screen
    bx = bullet.x
    by = SCREEN_HEIGHT - bullet.y
    
    # Simple AABB collision
    if (px_screen - 64 < bx < px_screen + 64 and
        py_screen - 64 < by < py_screen + 64):
        return True
    return False
```

**Explanation:**

1. **Coordinate system mapping:**
   - `px_screen = player_x`: World X stays same for screen
   - `py_screen = SCREEN_HEIGHT - player_y`: Flip Y axis

2. **Bullet coordinates:**
   - `bx = bullet.x`, `by = SCREEN_HEIGHT - bullet.y`: Same conversion

3. **AABB (Axis-Aligned Bounding Box) collision:**
   ```python
   if (px_screen - 64 < bx < px_screen + 64 and
       py_screen - 64 < by < py_screen + 64):
   ```
   
   **Breakdown:**
   - `px_screen - 64 < bx < px_screen + 64`: Bullet X within ±64 of player X
   - `py_screen - 64 < by < py_screen + 64`: Bullet Y within ±64 of player Y
   - `and`: Both conditions true = collision
   
   **Why ±64?** Player sprite is 128×128, center is at (px_screen, py_screen), so collision box extends ±64

4. **Simplified collision:**
   - Not perfect (bullets can clip edges), but good enough for gameplay
   - Alternative: pixel-perfect or circular collision (more CPU intensive)

---

## Part 5: Game Initialization and State Management

### 5.1 Pre-Game Setup

```python
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("MEGA MILITIA - Multiplayer")

# Show lobby
game_mode, player_name, host_address = show_lobby()

if not game_mode:
    pygame.quit()
    exit()
```

**Explanation:**

1. `pygame.init()`: Initialize all pygame modules (required)
2. `pygame.display.set_mode()`: Create game window
3. `pygame.display.set_caption()`: Window title
4. `show_lobby()`: **Blocking** - doesn't return until lobby closes
5. `if not game_mode: exit()`: Exit if user cancelled

### 5.2 Network Initialization

```python
# Initialize network
player_id = None
server = None
client = None
other_players_data = {}

if game_mode == 'host':
    # Start server
    server = GameServer(max_players=4)
    server.start()
    player_id = 0  # Host is always player 0
    print(f"Server started. Waiting for players...")
    screen.fill((170, 150, 255))
    pygame.display.flip()
    time.sleep(1)
else:
    # Connect as client
    if ':' in host_address:
        host, port = host_address.split(':')
        port = int(port)
    else:
        host = host_address
        port = 5000
    
    client = GameClient(player_id=None)
    if client.connect(host, port):
        print(f"Connected to server at {host}:{port}")
        time.sleep(0.5)
    else:
        pygame.quit()
        exit()
```

**Explanation:**

**Host flow:**
1. `server = GameServer()`: Create server instance
2. `server.start()`: Start accepting connections in background thread
3. `player_id = 0`: Host is always player 0
4. Show "Waiting for players" message
5. `time.sleep(1)`: Brief pause so message visible

**Client flow:**
1. Parse address: `"localhost:5000"` → `host="localhost"`, `port=5000`
2. `client = GameClient(player_id=None)`: Create client
3. `client.connect()`: Attempt connection
4. If fails, quit game

### 5.3 Player Creation and Game Loop Setup

```python
player = Player(10, 20, player_id=player_id if player_id is not None else -1)
running = True
bullets = []
counter = 0
game_phase = 'playing'
```

**Explanation:**

1. **Player ID assignment:**
   ```python
   player_id if player_id is not None else -1
   ```
   - If `player_id` is 0 (host), use 0
   - Otherwise, use -1 (clients get ID from server later... not fully implemented)

2. `bullets = []`: List of local player's bullets

3. `counter`: Frames counter (cycles 0-59 at 60 FPS)

4. `game_phase = 'playing'`: Track game state (plays or dead)

---

## Part 6: Main Game Loop - Network Integration

### 6.1 Per-Frame Update Flow

```python
while running:
    clock.tick(60)
    counter += 1
    if counter == 60:
        counter = 0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((170, 150, 255))
    keys = pygame.key.get_pressed()

    drawHouse(100, 100)
    drawHouse(600, 200)
    drawMap()
```

**Explanation:**

1. `clock.tick(60)`: Ensure 60 FPS (16ms per frame)
2. `counter`: Increments each frame, resets at 60 (1 second)
3. **Event loop**: Check for quit
4. **Rendering setup**: Clear screen, get input, draw environment

### 6.2 Bullet Spawning with Mouse Aiming

```python
# Spawn bullets toward the mouse on left click (rate-limited)
if pygame.mouse.get_pressed()[0] and counter % 4 == 0:
    mx, my = pygame.mouse.get_pos()
    px_screen = player.x
    py_screen = SCREEN_HEIGHT - player.y
    dx = mx - px_screen
    dy_screen = my - py_screen
    dist = math.hypot(dx, dy_screen)
    if dist > 0:
        speed = 10
        vx = dx / dist * speed
        vy = -dy_screen / dist * speed
        bullets.append(Bullet(5, 5, vx, vy, player.x, player.y, owner_id=player_id if player_id is not None else -1))
```

**Complete breakdown:**

1. **Rate limiting:**
   ```python
   if pygame.mouse.get_pressed()[0] and counter % 4 == 0:
   ```
   - `pygame.mouse.get_pressed()[0]`: Left mouse button (True/False)
   - `counter % 4 == 0`: Only spawn on frames 0, 4, 8, 12, ... (15/sec)
   - Without this, holding mouse would spawn hundreds per second

2. **Get mouse position:**
   ```python
   mx, my = pygame.mouse.get_pos()
   ```
   - Returns pixel position in screen coordinates

3. **Calculate direction vector:**
   ```python
   px_screen = player.x
   py_screen = SCREEN_HEIGHT - player.y
   dx = mx - px_screen
   dy_screen = my - py_screen
   ```
   - `px_screen, py_screen`: Player position in screen coordinates
   - `dx, dy_screen`: Vector FROM player TO mouse

4. **Normalize to unit vector:**
   ```python
   dist = math.hypot(dx, dy_screen)
   if dist > 0:
       vx = dx / dist * speed
       vy = -dy_screen / dist * speed
   ```
   - `math.hypot()`: Euclidean distance = √(dx² + dy²)
   - `vx = dx / dist * speed`: Unit vector scaled by speed (10 pixels/frame)
   - `vy = -dy_screen / dist * speed`: Negative because screen Y inverted
   - `if dist > 0`: Avoid division by zero if mouse on player

5. **Create bullet:**
   ```python
   bullets.append(Bullet(5, 5, vx, vy, player.x, player.y, owner_id=...))
   ```
   - Width/height: 5×5 pixels
   - Velocity: (vx, vy) toward mouse
   - Position: Starts at player location
   - Owner: Current player's ID

### 6.3 Network State Broadcasting

**Host (server side):**

```python
if server:
    server_player_data = {
        'x': player.x,
        'y': player.y,
        'bullets': [{'x': b.x, 'y': b.y} for b in bullets],
        'hp': player.hp
    }
    if player_id in server.player_data:
        server.player_data[player_id] = server_player_data
```

**Explanation:**

1. **Pack local state into dict:**
   - Position (x, y)
   - Bullet positions (list of {'x': ..., 'y': ...})
   - Current HP

2. **List comprehension for bullets:**
   ```python
   [{'x': b.x, 'y': b.y} for b in bullets]
   ```
   Creates list: `[{'x': 100, 'y': 50}, {'x': 110, 'y': 60}, ...]`

3. **Update server's player_data:**
   ```python
   server.player_data[player_id] = server_player_data
   ```
   - Server continuously updates with latest player info
   - Server broadcasts `player_data` to all clients 60x/sec

**Client (joining player side):**

```python
if client:
    client_player_data = {
        'x': player.x,
        'y': player.y,
        'bullets': [{'x': b.x, 'y': b.y} for b in bullets],
        'hp': player.hp
    }
    client.send_update(client_player_data)
    other_players_data = client.get_other_players()
```

**Explanation:**

1. **Pack same state dict** as host
2. `client.send_update()`: Send to server (called 60x/sec)
3. `other_players_data = client.get_other_players()`: Receive other player data (thread-safe getter)

**Update loop 60 times/second = 60 FPS = ~17ms per update**

### 6.4 Rendering Remote Players

```python
# Draw other players and their bullets
for other_id, other_data in other_players_data.items():
    px = other_data.get('x', SCREEN_WIDTH / 2)
    py = other_data.get('y', 0)
    other_hp = other_data.get('hp', 100)
    
    # Draw remote player
    player.draw_remote_player(px, py)
    
    # Draw remote player's HP bar
    hp_width = max(0, min(100, other_hp))
    pygame.draw.rect(screen, (0, 0, 0),       (px-52, SCREEN_HEIGHT - py - 75, 104, 12))
    pygame.draw.rect(screen, (200, 200, 200),  (px-51, SCREEN_HEIGHT - py - 74, 102, 10))
    pygame.draw.rect(screen, (70, 150, 50),    (px-50, SCREEN_HEIGHT - py - 73, hp_width, 8))
```

**Explanation:**

1. **Iterate other players:**
   ```python
   for other_id, other_data in other_players_data.items():
   ```
   - `other_data` is dict with  'x', 'y', 'bullets', 'hp'

2. **Safe value extraction:**
   ```python
   px = other_data.get('x', SCREEN_WIDTH / 2)
   ```
   - `.get()` method: Return value if exists, else default (SCREEN_WIDTH/2)
   - Prevents KeyError if data missing

3. **Clamp HP to range:**
   ```python
   hp_width = max(0, min(100, other_hp))
   ```
   - `min(100, other_hp)`: Cap at maximum 100
   - `max(0, ...)`: Cap at minimum 0
   - Ensures HP bar width between 0-100 pixels

4. **Draw HP bar (3 rectangles):**
   - Black outline: `(0, 0, 0)` - 104 wide
   - Gray background: `(200, 200, 200)` - 102 wide
   - Green fill: `(70, 150, 50)` - `hp_width` wide (0-100)

**Drawing remote player's bullets:**

```python
# Draw remote player's bullets
for bullet_data in other_data.get('bullets', []):
    bx = bullet_data.get('x', 0)
    by = bullet_data.get('y', 0)
    pygame.draw.rect(screen, (255, 100, 100), (int(bx), int(SCREEN_HEIGHT - by), 5, 5))
```

1. `.get('bullets', [])`: Extract bullet list (empty list if missing)
2. Each bullet: `{'x': ..., 'y': ...}`
3. Draw as light red rectangle (255, 100, 100)

### 6.5 Collision Detection - Remote Bullets Hit Local Player

```python
# Check if remote bullet hits local player
if (player.x - 32 < bx < player.x + 32 and
    player.y - 32 < by < player.y + 32):
    player.hp -= 10
    if player.hp <= 0:
        game_phase = 'dead'
```

**Explanation:**

1. **AABB collision check:**
   - `player.x ± 32`: Player collision box width
   - `player.y ± 32`: Player collision box height
   - If bullet within box → collision

2. **Apply damage:**
   - `player.hp -= 10`: Subtract 10 HP per hit

3. **Death check:**
   - If HP ≤ 0, set game_phase to 'dead'
   - Displays "YOU ARE DEAD" message

### 6.6 Local Bullets - Collision with Remote Players

```python
# Draw and cull local bullets
for b in bullets[:]:
    b.draw()
    if b.outOfBounds():
        bullets.remove(b)
    else:
        # Check collision with other players
        for other_id, other_data in other_players_data.items():
            other_px = other_data.get('x', SCREEN_WIDTH / 2)
            other_py = other_data.get('y', 0)
            if check_bullet_player_collision(b, other_px, other_py):
                if b in bullets:
                    bullets.remove(b)
                break
```

**Explanation:**

1. `for b in bullets[:]`:
   - Iterate over COPY of bullet list
   - Allows removing bullets during loop without skipping

2. `b.draw()`:
   - Update bullet position and render

3. **Out of bounds removal:**
   ```python
   if b.outOfBounds():
       bullets.remove(b)
   ```
   - If bullet off-screen, remove it
   - Prevents memory leak

4. **Collision check:**
   ```python
   else:  # Only check collision if still on screen
       for other_id, other_data in other_players_data.items():
   ```
   - Iterate through remote players

5. **Hit detection:**
   ```python
   if check_bullet_player_collision(b, other_px, other_py):
       if b in bullets:
           bullets.remove(b)
       break
   ```
   - Call collision function (defined earlier)
   - If hit, remove bullet
   - `break`: Stop checking other players (bullet destroyed)

### 6.7 UI and Game Over

```python
# Draw game info
font = pygame.font.Font(None, 24)
player_count_text = font.render(f"Players: {len(other_players_data) + 1}", True, (0, 0, 0))
screen.blit(player_count_text, (SCREEN_WIDTH - 200, 20))

if game_phase == 'dead':
    dead_text = pygame.font.Font(None, 50).render("YOU ARE DEAD", True, (200, 0, 0))
    screen.blit(dead_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 25))

pygame.display.flip()
```

**Explanation:**

1. **Player count display:**
   - `len(other_players_data) + 1`: Other players + self
   - Rendered at top-right (SCREEN_WIDTH - 200, 20)

2. **Death message:**
   - If `game_phase == 'dead'`: Show "YOU ARE DEAD" in red
   - Larger font (50 vs 24)
   - Centered on screen

3. `pygame.display.flip()`: Actually show all drawn elements

### 6.8 Cleanup on Exit

```python
# Cleanup
if server:
    server.stop()
if client:
    client.disconnect()
pygame.quit()
```

**Explanation:**

1. `server.stop()`: Sets `running = False`, closes socket
2. `client.disconnect()`: Sends disconnect message, closes socket
3. `pygame.quit()`: Clean up pygame resources

---

## Part 7: Advanced Concepts - Threading and Concurrency

### 7.1 Why Threading?

**Without threading:**
```python
# Server accepts connection
client_socket, addr = server_socket.accept()
# Blocked here until client sends data
data = client_socket.recv(4096)
# Can't accept more clients while waiting for this one!
```

**With threading:**
```python
# Main thread
while running:
    client_socket, addr = server_socket.accept()  # Non-blocking with timeout
    # Immediately spawn new thread
    threading.Thread(target=handle_client, args=(client_socket,)).start()
# Main thread continues accepting while worker threads handle each client
```

### 7.2 Race Conditions and Locks

**Race condition example (without lock):**
```python
# Thread 1: Read self.player_counter
player_id = self.player_counter  # Gets 0

# Context switch to Thread 2
# Thread 2: Read self.player_counter
player_id = self.player_counter  # Also gets 0 (sees old value)

# Thread 1: Increment and store
self.player_counter = 1
self.players[socket1] = 0

# Thread 2: Increment and store
self.player_counter = 1  # Only incremented once!
self.players[socket2] = 0  # DUPLICATE player ID!
```

**With lock:**
```python
with self.lock:  # Thread 1 enters, locks
    player_id = self.player_counter
    self.player_counter += 1
    # Thread 2 waits here for lock
    self.players[socket1] = player_id

# Lock released, Thread 2 enters
with self.lock:
    player_id = self.player_counter  # Gets 1 (correct)
    self.player_counter += 1
    self.players[socket2] = player_id  # Gets ID 1 (unique)
```

### 7.3 Daemon Threads

```python
threading.Thread(target=..., daemon=True).start()
```

**Explanation:**
- **Non-daemon thread**: Program waits for it to finish before exiting
- **Daemon thread**: Program exits even if thread still running
- Used for background tasks that should die with main program

### 7.4 Thread-Safe Patterns

**Pattern 1: Lock before modifying shared state**
```python
with self.lock:
    self.shared_dict[key] = value
```

**Pattern 2: Thread-safe getter**
```python
def get_data(self):
    with self.lock:
        return dict(self.data)  # Return copy
```

**Pattern 3: Communication via queues**
```python
# Instead of locks (for complex use cases)
from queue import Queue
messages = Queue()
worker_thread.get()  # Blocking, thread-safe
```

---

## Part 8: Data Flow Diagram

```
FRAME UPDATE SEQUENCE (60 times per second):

1. GAME WINDOW (main game.py)
   ↓
2. Player input: WASD for movement, mouse for aiming
   ↓
3. Create bullets toward mouse if clicking
   ↓
4. Update local player position (movement physics)
   ↓
5. BROADCAST LOCAL STATE (to network)
   │
   ├─→ [HOST MODE] Update server.player_data[my_id]
   │   Server thread immediately broadcasts to all clients
   │
   └─→ [CLIENT MODE] Send via socket to server
       Server receives via handle_client thread
       Server broadcasts to all clients via broadcast_state
   
6. RECEIVE REMOTE STATE (from network)
   │
   ├─→ [HOST MODE] Other players' data in server.player_data
   │
   └─→ [CLIENT MODE] Receive thread listens on socket
       Updates self.other_players
   
7. RENDERING
   ├─ Draw local player
   ├─ Draw local bullets
   ├─ For each remote player:
   │  ├─ Draw remote player sprite
   │  ├─ Draw HP bar
   │  ├─ Draw remote bullets
   │  └─ Check remote bullet→local player collision
   ├─ Check local bullet→remote player collision
   └─ Draw UI (player count, death message)

8. Display.flip() - show frame

9. Sleep 16ms (60 FPS = 1000ms / 60 = 16.6ms)

10. LOOP back to step 1
```

---

## Part 9: Summary of Key Concepts

### Networking
- **TCP/IP**: Reliable ordered message delivery
- **JSON serialization**: Convert Python objects to transmittable text
- **Client-server model**: One host server, multiple joining clients

### Threading
- **Daemon threads**: Background worker threads (listening for connections)
- **Locks**: Mutex for thread-safe shared state access
- **Non-blocking I/O**: Timeouts prevent threads from freezing

### Collision Detection
- **AABB**: Axis-aligned bounding boxes (rectangles)
- **Vector math**: Normalize direction for consistent speed

### Game Loop
- **60 FPS**: 16ms per frame budget
- **Network packets**: Update game state 60x/second
- **Deterministic**: Server broadcasts same state, all clients see same game

---

## Part 10: Extension Ideas

1. **Persistent Player IDs for Clients**
   - Currently host always player 0, clients assigned but not stored
   - Could use server to assign and transmit client's ID

2. **Player Names and Team System**
   - Send player_name with updates
   - Implement teams/colors for better visual distinction

3. **Respawning System**
   - After death, wait 3 seconds and respawn at random location
   - Currently stuck at "YOU ARE DEAD"

4. **Ammo/Cooldown System**
   - Bullets cost "ammo" (limit firing rate)
   - Currently client-side rate-limiting via `counter % 4`

5. **Server-Side Authority**
   - Currently client sends bullets, server trusts it
   - Could validate bullet trajectory (prevent cheating)

6. **Lag Compensation**
   - Extrapolate player positions while waiting for updates
   - Reduce jitter from network latency

7. **Connection Stability**
   - Reconnect on disconnect
   - Buffered messages if server temporarily unreachable

---

## Conclusion

The multiplayer system implements a complete game synchronization framework:
- **Network layer** handles connection/disconnection and state broadcasting
- **Lobby UI** provides player with game mode choice
- **Game integration** weaves networking into pygame rendering loop
- **Collision system** validates hits across network
- **Threading** enables simultaneous client handling

This is a production-ready foundation for a multiplayer pygame game, scalable to support more players / complex game logic with minor modifications.
