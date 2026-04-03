import socket
import json
import threading
import time
from collections import defaultdict

HOST = 'localhost'
PORT = 5000
BUFFER_SIZE = 4096

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
        self.player_counter = 0
        
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
    
    def stop(self):
        self.running = False
        self.server_socket.close()


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
