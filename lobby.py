import tkinter as tk
from tkinter import simpledialog, messagebox
import socket
from network import discover_servers
import threading

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
        # Get player name first
        name = simpledialog.askstring("Join Game", "Enter your player name:")
        if not name:
            return
        
        self.player_name = name
        
        # Search for servers
        self.info_label.config(text="Searching for servers...", fg="blue")
        self.root.update()
        
        # Discover servers in background thread
        def search_servers():
            servers = discover_servers(timeout=3)
            self.root.after(0, lambda: self.show_server_list(servers))
        
        threading.Thread(target=search_servers, daemon=True).start()
    
    def show_server_list(self, servers):
        """Show list of discovered servers for user to select from"""
        if not servers:
            messagebox.showwarning("No Servers", "No servers found on the network. Try entering a manual address.")
            self.info_label.config(text="No servers found. Try 'Manual Address'", fg="red")
            
            # Option to manually enter address
            host = simpledialog.askstring("Manual Address", "Enter host address (IP:PORT):", initialvalue="localhost:5000")
            if host:
                self.host_address = host
                self.game_mode = 'join'
                if self.test_connection(host):
                    self.info_label.config(text=f"Connecting to {host}...", fg="green")
                    self.root.update()
                    self.root.after(500, self.start_game)
                else:
                    messagebox.showerror("Connection Failed", f"Could not connect to {host}")
                    self.info_label.config(text="Connection failed. Try again.", fg="red")
            return
        
        # Create server selection window
        select_window = tk.Toplevel(self.root)
        select_window.title("Available Servers")
        select_window.geometry("400x300")
        select_window.transient(self.root)
        
        tk.Label(select_window, text="Select a Server:", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Listbox for servers
        listbox_frame = tk.Frame(select_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(listbox_frame, height=10)
        listbox.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        # Populate listbox
        for i, server in enumerate(servers):
            status = f"{server['players']}/{server['max_players']} players"
            label = f"{server['address']} ({status})"
            listbox.insert(tk.END, label)
        
        def select_server():
            if listbox.curselection():
                index = listbox.curselection()[0]
                selected = servers[index]
                self.host_address = selected['address']
                self.game_mode = 'join'
                select_window.destroy()
                
                self.info_label.config(text=f"Connecting to {self.host_address}...", fg="green")
                self.root.update()
                
                if self.test_connection(self.host_address):
                    self.root.after(500, self.start_game)
                else:
                    messagebox.showerror("Connection Failed", f"Could not connect to {self.host_address}")
                    self.info_label.config(text="Connection failed. Try again.", fg="red")
        
        def manual_entry():
            select_window.destroy()
            host = simpledialog.askstring("Manual Address", "Enter host address (IP:PORT):", initialvalue="localhost:5000")
            if host:
                self.host_address = host
                self.game_mode = 'join'
                if self.test_connection(host):
                    self.info_label.config(text=f"Connecting to {host}...", fg="green")
                    self.root.update()
                    self.root.after(500, self.start_game)
                else:
                    messagebox.showerror("Connection Failed", f"Could not connect to {host}")
                    self.info_label.config(text="Connection failed. Try again.", fg="red")
        
        button_frame = tk.Frame(select_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Connect", command=select_server, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Manual Entry", command=manual_entry, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=select_window.destroy, width=12).pack(side=tk.LEFT, padx=5)
    
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
