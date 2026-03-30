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
        self.vel = v
        self.gvel = 0
    

    def draw(self, keys):
        self.update(keys)
        pygame.draw.rect(screen, (200,100,40), (self.x, SCREEN_HEIGHT - self.y, self.width, self.height))


    def update(self, keys):
        if keys[pygame.K_SPACE] or keys[pygame.K_s]:
            self.y += self.vel
            self.gvel = 0
        else:
            self.gvel += 0.2
            self.y -= self.gvel
            if self.gvel > 5*self.vel:
                self.gvel = 5*self.vel
        if keys[pygame.K_m] or keys[pygame.K_z]:
            self.y -= self.vel
        if keys[pygame.K_a]:
            self.x -= self.vel
        if keys[pygame.K_x]:
            self.x += self.vel

        if self.x > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.width
        if self.x < 0:
            self.x = self.width
        if self.y > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT
        if self.y < map(self.x):
            self.y = map(self.x)


def map(x):
    return 100 + 150*math.sin(x/500) + 50*math.sin(x/100) + 20*math.sin(x/70) + 10*math.sin(x/30)

def drawMap():
    for i in range(0,SCREEN_WIDTH):
        pygame.draw.rect(screen, (80,120,60), (i ,SCREEN_HEIGHT - map(i) + 10 ,1 ,map(i)))

def drawHouse(x, height):
    pygame.draw.rect(screen, (50,50,60), (x, SCREEN_HEIGHT - map(x) - height, 100, SCREEN_HEIGHT))


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
fps = 60
player = Player(10,20,500,50,2)

running = True

while running:
    pygame.time.delay(int((1/fps)*1000))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((170,190,255))
    keys = pygame.key.get_pressed()

    drawHouse(100, 100)
    drawHouse(600, 200)
    drawMap()
    player.draw(keys)

    pygame.display.flip()