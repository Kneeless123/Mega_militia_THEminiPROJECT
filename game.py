import pygame
import math

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600



class Player:
    def __init__(self,w ,h ,x, y, v):
        self.width = w
        self.height = h
        self.x = x
        self.y = y
        self.MaxVel = v
        self.xvel = 0
        self.yvel = 0
        self.hp = 100
    
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
        if keys[pygame.K_m] or keys[pygame.K_s]:
            self.yvel += 0.2*self.MaxVel
            self.yvel = min(self.MaxVel, self.yvel)
        else:
            self.yvel -= 0.1*self.MaxVel
            self.yvel = max(-5*self.MaxVel, self.yvel)

        if keys[pygame.K_SPACE] or keys[pygame.K_z]:
            self.yvel -= 0.1*self.MaxVel
            self.y += self.yvel

        if keys[pygame.K_a]:
            self.xvel -= 0.1*self.MaxVel
            self.xvel = max(-self.MaxVel, self.xvel)
        elif keys[pygame.K_x]:
            self.xvel += 0.1*self.MaxVel
            self.xvel = min(self.MaxVel, self.xvel)
        else:
            if self.xvel > 0:
                self.xvel -= 0.1*self.MaxVel
            else:
                self.xvel += 0.1*self.MaxVel
            if abs(self.xvel) <= 0.1*self.MaxVel:
                self.xvel = 0

        self.x += self.xvel
        self.y += self.yvel

        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
        if self.x < 0:
            self.x = 0
        if self.y > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT
        if self.y < map(self.x):
            self.y = map(self.x)
            self.yvel = 0


def map(x):
    return 100 + 150*math.sin(x/500) + 50*math.sin(x/100) + 20*math.sin(x/70) + 10*math.sin(x/30)

def drawMap():
    step = 1
    for i in range(0,SCREEN_WIDTH, step):
        pygame.draw.rect(screen, (80,120,60), (i ,SCREEN_HEIGHT - map(i) + 10 ,step ,map(i)))

def drawHouse(x, height):
    pygame.draw.rect(screen, (50,50,60), (x, SCREEN_HEIGHT - map(x) - height, 100, SCREEN_HEIGHT))


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
fps = 60
player = Player(10,20,500,50,60/fps)

running = True

while running:
    pygame.time.delay(int((1/fps)*1000))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((170,150,255))
    keys = pygame.key.get_pressed()

    drawHouse(100, 100)
    drawHouse(600, 200)
    drawMap()
    player.drawHealth()
    player.draw(keys)

    pygame.display.flip()