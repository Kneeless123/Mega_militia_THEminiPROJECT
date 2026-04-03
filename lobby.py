import tkinter as tk
from tkinter import simpledialog, messagebox
import socket

class LobbyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MEGA MILITIA - Lobby")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        self.game_mode = None  # 'host' or 'join'
        self.player_name = None
        self.host_address = None
        
        self.setup_ui()
    
    def setup_ui(self):
        tk.Label(self.root, text="MEGA MILITIA", font=("Arial", 20, "bold")).pack(pady=20)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Host Game", command=self.host_game, width=15, height=2).pack(pady=10)
        tk.Button(button_frame, text="Join Game", command=self.join_game, width=15, height=2).pack(pady=10)
        tk.Button(button_frame, text="Exit", command=self.root.quit, width=15, height=2).pack(pady=10)
        
        info_frame = tk.Frame(self.root)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.info_label = tk.Label(info_frame, text="Select an option to continue", 
                                     font=("Arial", 10), fg="gray")
        self.info_label.pack()
    
    def host_game(self):
        name = simpledialog.askstring("Host Game", "Enter your player name:")
        if name:
            self.player_name = name
            self.game_mode = 'host'
            self.info_label.config(text=f"Hosting game as '{name}'...", fg="green")
            self.root.update()
            self.root.after(1000, self.start_game)
    
    def join_game(self):
        host = simpledialog.askstring("Join Game", "Enter host address (IP:PORT):", initialvalue="localhost:5000")
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
    
    def start_game(self):
        self.root.destroy()
