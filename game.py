import pygame
import math
import tkinter as tk
from tkinter import messagebox
from lobby import LobbyGUI
from network import GameServer, GameClient
import threading
import json
import time

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600

clock = pygame.time.Clock()

class Player:
    def __init__(self, w, h, player_id=0):
        self.player_id = player_id
        self.width = w
        self.height = h
        self.x = SCREEN_WIDTH / 2
        self.y = 0
        self.MaxVel = 1
        self.xvel = 0
        self.yvel = 0
        self.spawn_pos = (SCREEN_WIDTH / 2, 0)
        self.hp = 100
        self.boost = 100
        self.right = True
        self.background = pygame.image.load("Sprites/background.png").convert()
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.count = 0
        self.f = 0
        self.facc = 0.0  # float accumulator for animation
        self.animation = {
            "idle": [
                pygame.image.load("Sprites/frame00.png").convert_alpha(),
                pygame.image.load("Sprites/frame10.png").convert_alpha(),
                pygame.image.load("Sprites/frame61.png").convert_alpha(),
                pygame.image.load("Sprites/frame62.png").convert_alpha(),
            ],
            "right": [
                pygame.image.load(f"Sprites/frame2{i}.png").convert_alpha()
                for i in range(10)
            ],
            "left": [
                pygame.image.load(f"Sprites/frame4{i}.png").convert_alpha()
                for i in range(10)
            ]
        }

    def drawHealth(self, x_pos=20, y_pos=20):
        x, y = x_pos, y_pos
        pygame.draw.rect(screen, (0, 0, 0),       (x-2, y-1, 104, 12))
        pygame.draw.rect(screen, (200, 200, 200),  (x-1, y,   102, 10))
        pygame.draw.rect(screen, (70, 150, 50),    (x,   y+1, self.hp, 8))
        x, y = x_pos, y_pos*2
        pygame.draw.rect(screen, (0, 0, 0),       (x-2, y-1, 104, 12))
        pygame.draw.rect(screen, (200, 200, 200),  (x-1, y,   102, 10))
        pygame.draw.rect(screen, (70, 100, 150),    (x,   y+1, self.boost, 8))

    def draw(self, keys):
        self.update(keys)
        pos = (self.x - 64, SCREEN_HEIGHT - self.y - 64)
        if  self.y - map(self.x) > 5:
            if self.right:
                screen.blit(self.animation["idle"][2], pos)
            else:
                screen.blit(self.animation["idle"][3], pos)
        else:
            if self.xvel != 0 and self.right:
                screen.blit(self.animation["right"][self.f], pos)
            elif self.xvel != 0 and not self.right:
                screen.blit(self.animation["left"][self.f], pos)
            elif self.right:
                screen.blit(self.animation["idle"][0], pos)
            else:
                screen.blit(self.animation["idle"][1], pos)

    def update(self, keys):
        if keys[pygame.K_s] and self.boost > 0:
            self.yvel += 0.15
            if self.yvel > self.MaxVel:
                self.yvel = self.MaxVel
            self.boost -= 0.5
            self.boost = max(0, self.boost)
            self.count = 0
        else:
            self.yvel -= 0.15
            if self.yvel < -5:
                self.yvel = -10

        if keys[pygame.K_z]:
            self.yvel -= 0.15

        if keys[pygame.K_a]:
            self.xvel -= 0.15
            if self.xvel < -self.MaxVel:
                self.xvel = -self.MaxVel
        if keys[pygame.K_x]:
            self.xvel += 0.15
            if self.xvel > self.MaxVel:
                self.xvel = self.MaxVel
        if not (keys[pygame.K_a] or keys[pygame.K_x]):
            self.xvel /= 1.2
        if abs(self.xvel) < 0.1:
            self.xvel = 0

        self.x += self.xvel
        self.y += self.yvel

        if self.xvel != 0:
            self.facc += abs(self.xvel) * 0.3
            self.f = int(self.facc) % 10
        else:
            self.facc = 0
            self.f = 0

        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            self.xvel = 0
        if self.x < 0:
            self.x = 0
            self.xvel = 0
        if self.y > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT
            self.yvel = 0
        if self.y < map(self.x):
            self.y = map(self.x)
            if not keys[pygame.K_s]:
                self.yvel = 0
                if self.count == 60:
                    self.boost += 0.25
                    self.boost = min(100, self.boost)

        if self.hp < 100:
            self.hp += self.MaxVel / 60
        else:
            self.hp = 100

        if self.xvel != 0:
            self.right = self.xvel > 0
        self.count += 1
        self.count = min(60, self.count)

    def respawn(self):
        self.x, self.y = self.spawn_pos
        self.hp = 100
        self.boost = 100
        self.xvel = 0
        self.yvel = 0

    def draw_remote_player(self, px, py, is_right=True, hp=100):
        """Draw another player at position (px, py) with additional state"""
        pos = (px - 64, SCREEN_HEIGHT - py - 64)
        
        # Determine frame based on orientation
        if is_right:
            screen.blit(self.animation["idle"][0], pos)
        else:
            screen.blit(self.animation["idle"][1], pos)
            
        # Draw HP bar for other player
        hp_width = max(0, min(100, hp))
        pygame.draw.rect(screen, (0, 0, 0),       (px-52, SCREEN_HEIGHT - py - 75, 104, 12))
        pygame.draw.rect(screen, (200, 200, 200),  (px-51, SCREEN_HEIGHT - py - 74, 102, 10))
        # Color based on HP
        color = (70, 150, 50) if hp > 30 else (200, 50, 50)
        pygame.draw.rect(screen, color,    (px-50, SCREEN_HEIGHT - py - 73, hp_width, 8))

class Bullet:
    def __init__(self, w, h, spX, spY, x, y, owner_id=0):
        self.owner_id = owner_id
        self.width = w
        self.height = h
        self.xVelo = spX
        self.yVelo = spY
        self.x = x
        self.y = y

    def draw(self):
        self.update()
        pygame.draw.rect(screen, (50,10,10), (int(self.x), int(SCREEN_HEIGHT - self.y), int(self.width), int(self.height)))

    def update(self):
        self.x += self.xVelo
        self.y += self.yVelo

    def outOfBounds(self):
        return self.x > SCREEN_WIDTH or self.x < 0 or self.y > SCREEN_HEIGHT or self.y < 0

    def get_rect(self):
        """Returns (x1, y1, x2, y2) for collision detection"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)




def map(x):
    return 100 + 150*math.sin(x/500) + 50*math.sin(x/100) + 20*math.sin(x/70) + 10*math.sin(x/30)

def drawMap():
    for i in range(0, SCREEN_WIDTH):
        pygame.draw.rect(screen, (80, 120, 60), (i, SCREEN_HEIGHT - map(i) + 10, 1, map(i)))

def drawHouse(x, height):
    pygame.draw.rect(screen, (50, 50, 60), (x, SCREEN_HEIGHT - map(x) - height, 100, SCREEN_HEIGHT))

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

def show_lobby():
    """Show the tkinter lobby and return (game_mode, player_name, host_address)"""
    root = tk.Tk()
    lobby = LobbyGUI(root)
    root.mainloop()
    
    return lobby.game_mode, lobby.player_name, lobby.host_address


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("MEGA MILITIA - Multiplayer")

# Show lobby
game_mode, player_name, host_address = show_lobby()

if not game_mode:
    pygame.quit()
    exit()

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
    
    client = GameClient(player_id=-1)
    if client.connect(host, port):
        print(f"Connected to server at {host}:{port}")
        # Wait a moment for the welcome message to be processed
        time.sleep(1)
        player_id = client.player_id
    else:
        pygame.quit()
        exit()

player = Player(10, 20, player_id=player_id if player_id is not None else -1)
running = True
bullets = []
counter = 0
game_phase = 'playing'

while running:
    clock.tick(60)
    counter += 1
    if counter == 60:
        counter = 0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(player.background, (0, 0))
    keys = pygame.key.get_pressed()

    drawHouse(100, 100)
    drawHouse(600, 200)
    drawMap()
    
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

    player.draw(keys)
    player.drawHealth()

    # Send player state to network
    if server:
        server_player_data = {
            'x': player.x,
            'y': player.y,
            'bullets': [{'x': b.x, 'y': b.y} for b in bullets],
            'hp': player.hp,
            'right': player.right
        }
        with server.lock:
            server.player_data[player_id] = server_player_data
            # Host needs to get other player data from the server
            other_players_data = {
                pid: pdata for pid, pdata in server.player_data.items()
                if pid != player_id
            }
    
    if client:
        client_player_data = {
            'x': player.x,
            'y': player.y,
            'bullets': [{'x': b.x, 'y': b.y} for b in bullets],
            'hp': player.hp,
            'right': player.right
        }
        client.send_update(client_player_data)
        other_players_data = client.get_other_players()
        if player_id == -1 and client.player_id is not None:
             player_id = client.player_id
             player.player_id = player_id

    # Draw other players and their bullets
    for other_id, other_data in other_players_data.items():
        px = other_data.get('x', SCREEN_WIDTH / 2)
        py = other_data.get('y', 0)
        other_hp = other_data.get('hp', 100)
        other_right = other_data.get('right', True)
        
        # Draw remote player
        player.draw_remote_player(px, py, other_right, other_hp)
        
        # Draw remote player's bullets
        for bullet_data in other_data.get('bullets', []):
            bx = bullet_data.get('x', 0)
            by = bullet_data.get('y', 0)
            pygame.draw.rect(screen, (255, 50, 50), (int(bx), int(SCREEN_HEIGHT - by), 6, 6))
            
            # Check if remote bullet hits local player
            if player.hp > 0:
                dist = math.hypot(player.x - bx, player.y - by)
                if dist < 40: # Hit radius
                    player.hp -= 2 # Taking damage
                    if player.hp <= 0:
                        game_phase = 'dead'

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

    # Draw game info
    font = pygame.font.Font(None, 24)
    name_text = font.render(f"Player: {player_name}", True, (255, 255, 255))
    screen.blit(name_text, (20, 50))
    
    player_count_text = font.render(f"Players: {len(other_players_data) + 1}", True, (255, 255, 255))
    screen.blit(player_count_text, (SCREEN_WIDTH - 200, 20))
    
    if game_phase == 'dead':
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        dead_text = pygame.font.Font(None, 74).render("YOU ARE DEAD", True, (255, 50, 50))
        screen.blit(dead_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))
        
        respawn_text = pygame.font.Font(None, 36).render("Press 'R' to Respawn", True, (255, 255, 255))
        screen.blit(respawn_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2))
        
        if keys[pygame.K_r]:
            player.respawn()
            game_phase = 'playing'

    pygame.display.flip()

# Cleanup
if server:
    server.stop()
if client:
    client.disconnect()
pygame.quit()
