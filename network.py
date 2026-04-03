import socket
import json
import threading
import time
from collections import defaultdict

HOST = 'localhost'
PORT = 5000
BUFFER_SIZE = 4096
DISCOVERY_PORT = 5001
DISCOVERY_BROADCAST = '<broadcast>'

class GameServer:
    def __init__(self, max_players=4):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(max_players)
        
        self.players = {}  # {client_socket: player_id}
        self.player_data = {}  # {player_id: {x, y, bullets, hp}}
        self.lock = threading.Lock()
        self.max_players = max_players
        self.running = True
        self.player_counter = 1
        self.room_code = str(__import__('random').randint(1000, 9999))
        
    def accept_connections(self):
        while self.running and len(self.players) < self.max_players:
            try:
                self.server_socket.settimeout(1)
                client_socket, addr = self.server_socket.accept()
                with self.lock:
                    player_id = self.player_counter
                    self.player_counter += 1
                    self.players[client_socket] = player_id
                    self.player_data[player_id] = {'x': 550, 'y': 0, 'bullets': [], 'hp': 100}
                
                # Send welcome message with player_id
                welcome_msg = json.dumps({
                    'type': 'welcome',
                    'player_id': player_id
                })
                client_socket.send(welcome_msg.encode())
                
                threading.Thread(target=self.handle_client, args=(client_socket, player_id), daemon=True).start()
                print(f"Player {player_id} joined from {addr}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error accepting connection: {e}")
    
    def handle_client(self, client_socket, player_id):
        try:
            while self.running:
                data = client_socket.recv(BUFFER_SIZE).decode()
                if not data:
                    break
                
                msg = json.loads(data)
                with self.lock:
                    if msg['type'] == 'update':
                        self.player_data[player_id] = msg['data']
                    elif msg['type'] == 'disconnect':
                        break
                
                # Broadcast current game state to all players
                self.broadcast_state()
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
    
    def start(self):
        threading.Thread(target=self.accept_connections, daemon=True).start()
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
    
    def stop(self):
        self.running = False
        self.server_socket.close()
    
    def broadcast_presence(self):
        """Announce server presence via UDP broadcast"""
        try:
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            while self.running:
                try:
                    # Get local IP (try connecting to public server to find our IP)
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                except:
                    local_ip = '127.0.0.1'
                
                message = json.dumps({
                    'type': 'server_announce',
                    'ip': local_ip,
                    'port': PORT,
                    'room_code': self.room_code,
                    'players': len(self.players),
                    'max_players': self.max_players
                })
                
                try:
                    broadcast_socket.sendto(message.encode(), (DISCOVERY_BROADCAST, DISCOVERY_PORT))
                    broadcast_socket.sendto(message.encode(), ('255.255.255.255', DISCOVERY_PORT))
                except:
                    pass
                
                time.sleep(0.5)  # Announce every 0.5 second for faster discovery
        except Exception as e:
            print(f"Broadcast error: {e}")
        finally:
            try:
                broadcast_socket.close()
            except:
                pass


class GameClient:
    def __init__(self, player_id):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_id = player_id
        self.other_players = {}  # {player_id: {x, y, bullets, hp}}
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
    
    def connect(self, host=HOST, port=PORT):
        try:
            self.socket.connect((host, port))
            self.connected = True
            threading.Thread(target=self.receive_updates, daemon=True).start()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def send_update(self, player_data):
        try:
            msg = json.dumps({
                'type': 'update',
                'data': player_data
            })
            self.socket.send(msg.encode())
        except Exception as e:
            print(f"Error sending update: {e}")
    
    def receive_updates(self):
        try:
            while self.running and self.connected:
                data = self.socket.recv(BUFFER_SIZE).decode()
                if not data:
                    break
                
                msg = json.loads(data)
                
                if msg.get('type') == 'welcome':
                    self.player_id = msg['player_id']
                else:
                    # It's a state update
                    state = msg
                    with self.lock:
                        # Only store other players (not self)
                        self.other_players = {
                            str(pid): pdata for pid, pdata in state['players'].items()
                            if str(pid) != str(self.player_id)
                        }
        except Exception as e:
            print(f"Error receiving updates: {e}")
        finally:
            self.connected = False
    
    def get_other_players(self):
        with self.lock:
            return dict(self.other_players)
    
    def disconnect(self):
        self.running = False
        try:
            self.socket.send(json.dumps({'type': 'disconnect'}).encode())
        except:
            pass
        self.socket.close()


def discover_servers(timeout=3):
    """Discover available servers on local network via UDP broadcast"""
    servers = []
    
    try:
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        discovery_socket.bind(('', DISCOVERY_PORT))
        discovery_socket.settimeout(0.5) # Shorter timeout per receive attempt
        
        start_time = time.time()
        seen_servers = set()
        
        while time.time() - start_time < timeout:
            try:
                data, addr = discovery_socket.recvfrom(BUFFER_SIZE)
                message = json.loads(data.decode())
                
                if message.get('type') == 'server_announce':
                    server_key = f"{message['ip']}:{message['port']}:{message.get('room_code', '')}"
                    
                    # Avoid duplicates
                    if server_key not in seen_servers:
                        seen_servers.add(server_key)
                        servers.append({
                            'ip': message['ip'],
                            'port': message['port'],
                            'room_code': message.get('room_code', '0000'),
                            'players': message.get('players', 0),
                            'max_players': message.get('max_players', 4),
                            'address': f"{message['ip']}:{message['port']}"
                        })
            except (socket.timeout, json.JSONDecodeError):
                continue
            except Exception as e:
                print(f"Discovery error: {e}")
                break
        
        discovery_socket.close()
    except Exception as e:
        print(f"Discovery socket error: {e}")
    
    return servers
