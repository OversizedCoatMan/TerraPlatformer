import pygame 
from subprocess import Popen

LENGTH = 800
HEIGHT = 600
pygame.init()
main_menu = pygame.display.set_mode((LENGTH, HEIGHT))
pygame.display.set_caption("Main Menu") 
title = pygame.image.load("assets/Terraplatformer_menu_img.png").convert_alpha()
title_small = pygame.transform.scale(title, (LENGTH, 200))

menubg = pygame.image.load("assets/terraria background.png").convert_alpha()
menubg_large = pygame.transform.scale(menubg, (LENGTH, HEIGHT))
start = pygame.image.load("assets/startbtn.png").convert_alpha()
close = pygame.image.load("assets/closeimg.png").convert_alpha()
main_menu.blit(menubg_large, (0, 0))

class BUTTON:
    def __init__(self, x, y, image, scale, held):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
    
    def start(self, events):
        global pos, running
        main_menu.blit(self.image, (self.rect.x, self.rect.y))
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(pos):
                    print("Start Button Pressed")
                    Popen(["python", "game.py"])
                    running = False
    def close(self, events):
        global pos, running
        main_menu.blit(self.image, (self.rect.x, self.rect.y))
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(pos):
                    running = False
        



def draw(main_menu, button, events):
    main_menu.fill((0, 0, 0))
    main_menu.blit(menubg_large, (0, 0))
    title_x = (LENGTH - title_small.get_width()) // 2
    main_menu.blit(title_small, (title_x, 50))
    button.start(events)
    closebtn.close(events)


startbtn = BUTTON(LENGTH // 2, 300, start, 0.5, False)
closebtn = BUTTON(LENGTH // 2, 400, close, 0.5, False)
clock = pygame.time.Clock()

running = True
while running:
    events = pygame.event.get()
    pos = pygame.mouse.get_pos()
    clock.tick(60)
    
    draw(main_menu, startbtn, events)
        
    for event in events:
        if event.type == pygame.QUIT:
            running = False
    pygame.display.update()
pygame.quit()