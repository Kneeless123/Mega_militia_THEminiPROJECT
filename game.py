import pygame
import math

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600

clock = pygame.time.Clock()

class Player:
    def __init__(self, w, h):
        self.width = w
        self.height = h
        self.x = SCREEN_WIDTH / 2
        self.y = 0
        self.MaxVel = 1
        self.xvel = 0
        self.yvel = 0
        self.hp = 100
        self.right = True
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

    def drawHealth(self):
        x, y = 20, 20
        pygame.draw.rect(screen, (0, 0, 0),       (x-2, y-1, 104, 12))
        pygame.draw.rect(screen, (200, 200, 200),  (x-1, y,   102, 10))
        pygame.draw.rect(screen, (70, 150, 50),    (x,   y+1, self.hp, 8))

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
        if keys[pygame.K_s]:
            self.yvel += 0.15
            if self.yvel > self.MaxVel:
                self.yvel = self.MaxVel
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
            self.facc += abs(self.xvel) * 0.4
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

        if self.hp < 100:
            self.hp += self.MaxVel / 60
        else:
            self.hp = 100

        if self.xvel != 0:
            self.right = self.xvel > 0


def map(x):
    return 100 + 150*math.sin(x/500) + 50*math.sin(x/100) + 20*math.sin(x/70) + 10*math.sin(x/30)

def drawMap():
    for i in range(0, SCREEN_WIDTH):
        pygame.draw.rect(screen, (80, 120, 60), (i, SCREEN_HEIGHT - map(i) + 10, 1, map(i)))

def drawHouse(x, height):
    pygame.draw.rect(screen, (50, 50, 60), (x, SCREEN_HEIGHT - map(x) - height, 100, SCREEN_HEIGHT))


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
player = Player(10, 20)

running = True

while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((170, 150, 255))
    keys = pygame.key.get_pressed()

    drawHouse(100, 100)
    drawHouse(600, 200)
    drawMap()
    player.drawHealth()
    player.draw(keys)

    pygame.display.flip()