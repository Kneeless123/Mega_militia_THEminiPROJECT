import pygame
import math

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600

clock = pygame.time.Clock()

class Player:
    def __init__(self ,w ,h):
        self.width = w
        self.height = h
        self.x = SCREEN_WIDTH/2
        self.y = 0
        self.MaxVel = 1
        self.xvel = 0
        self.yvel = 0
        self.hp = 100
        self.left = False
        self.right = False
        self.stand = True
    
    def drawHealth(self):
        x = 20
        y = 20
        pygame.draw.rect(screen, (0,0,0), (x-2 ,y-1 , 104, 12))
        pygame.draw.rect(screen, (200,200,200), (x-1 ,y , 102, 10))
        pygame.draw.rect(screen, (70,150,50), (x ,y+1 , self.hp, 8))

    def draw(self, keys):
        self.update(keys)
        pygame.draw.rect(screen, (200,100,40), (self.x, SCREEN_HEIGHT - self.y, self.width, self.height))


    def update(self, keys):
        if keys[pygame.K_s]:
            self.yvel += 0.15
            if self.MaxVel < self.yvel:
                self.yvel = self.MaxVel
        else:
            self.yvel -= 0.15
            if -5 > self.yvel:
                self.yvel = -10

        if keys[pygame.K_z]:
            self.yvel -= 0.15

        if keys[pygame.K_a]:
            self.xvel -= 0.15
            if -self.MaxVel > self.xvel:
                self.xvel = -self.MaxVel
        if keys[pygame.K_x]:
            self.xvel += 0.15
            if self.MaxVel < self.xvel:
                self.xvel = self.MaxVel
        if not (keys[pygame.K_a] or keys[pygame.K_x]):
            self.xvel /= 1.2
        if abs(self.xvel) < 0.1:
            self.xvel = 0

        self.x += self.xvel
        self.y += self.yvel

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
            self.hp += self.MaxVel/60
        else:
            self.hp = 100
        if self.xvel > 0:
            self.right = True
            self.left = False
            self.stand = False
        elif self.xvel < 0:
            self.right = False
            self.left = True
            self.stand = False
        else:
            self.right = False
            self.left = False
            self.stand = True


def map(x):
    return 100 + 150*math.sin(x/500) + 50*math.sin(x/100) + 20*math.sin(x/70) + 10*math.sin(x/30)

def drawMap(surface = "screen"):
    step = 1
    for i in range(0,SCREEN_WIDTH, step):
        pygame.draw.rect(screen, (80,120,60), (i ,SCREEN_HEIGHT - map(i) + 10 ,step ,map(i)))

def drawHouse(x, height, surface = "screen"):
    pygame.draw.rect(screen, (50,50,60), (x, SCREEN_HEIGHT - map(x) - height, 100, SCREEN_HEIGHT))


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
player = Player(10, 20)

running = True
frame = 0
FPS = 60

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    frame += 1
    frame %= FPS


    screen.fill((170,150,255))
    keys = pygame.key.get_pressed()


    drawHouse(100, 100)
    drawHouse(600, 200)

    drawMap()
    
    player.drawHealth()
    player.draw(keys)


    pygame.display.flip()