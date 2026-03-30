class Tiles:
    h = 50
    w = 50
    def __init__(self, clr):
        self.color = clr

    def draw(self, posX, posY, screen):
        pygame.draw.rect(screen, self.color, (posX * Tiles.w, posY * Tiles.h, Tiles.w, Tiles.h))


sky = (100, 150, 200)
grass = (80, 150, 60)
dirt = (130, 60, 50)