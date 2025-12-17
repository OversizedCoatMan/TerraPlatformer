import pygame
import sys
from tiles import TileMap
import sqlite3
import subprocess
import os
#---------------#
#--MAP LOADING--#
#---------------#
#connects to database, if no table create one
conn = sqlite3.connect('game_data.db')
cur = conn.cursor()
cur.execute('create table if not exists game_data (level integer)')

#fetches data from database
cur.execute('select level from game_data order by rowid desc limit 1')
row = cur.fetchone()

#checks if there is level data in database, if not it sets it to level 1
if row:
    level = row[0]
else:
    
    cur.execute('insert into game_data (level) values (?)', (1,))
    conn.commit()
    level = 1

#loads maps based on level data in database
if level == 1:
    TILEMAP_PATH = 'assets/tree test.csv'
elif level == 2:
    TILEMAP_PATH = 'assets/test1.csv'

#constant variables
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600 
FPS = 60
PLAYER_SIZE = (50, 60)
GRAVITY = 0.5
TILE_SIZE = 32
MAP_SHIFT_DOWN_TILES = 0   

#initialises pygame and display
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile Game")
clock = pygame.time.Clock()
running = True
def load_map(filename):
    return TileMap(filename, tile_size=TILE_SIZE)
#loads tilemap and calculates y offset to lower map
tilemap = load_map(TILEMAP_PATH)
map_offset_y = SCREEN_HEIGHT - len(tilemap.map_data) * TILE_SIZE
map_offset_y += MAP_SHIFT_DOWN_TILES * TILE_SIZE

main_menu = pygame.image.load('assets/main menu.png').convert_alpha()
class BUTTON:
    def __init__(self, x, y, image, scale, held):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def menu(self, events, pos):
        """Render the button and handle click events.

        Accepts an events list (from pygame.event.get()) instead of calling
        pygame.event.get() again so events aren't consumed twice.
        """
        global running
        screen.blit(self.image, (self.rect.x, self.rect.y))
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Use event.pos for the exact click position
                if self.rect.collidepoint(event.pos):
                    # Launch main.py with the same Python interpreter so it
                    # has access to the same virtualenv/site-packages (e.g. pygame).
                    script_path = os.path.join(os.path.dirname(__file__), 'main.py')
                    subprocess.Popen([sys.executable, script_path], cwd=os.path.dirname(__file__))
                    running = False
menu_button = BUTTON(48, 11, main_menu, 0.2, False)


def draw():
    screen.fill((0,0,0))
    tilemap.draw_map(screen, y_offset=map_offset_y)
    menu_button.menu(events, pos=pygame.mouse.get_pos())
    pygame.display.flip()
    
#handles events in game, 
def event():
    global level, running, events
    keys = pygame.key.get_pressed()
    pos = pygame.mouse.get_pos()
    for event in events:
        if event.type == pygame.QUIT:
            level = 2
            
            cur.execute('delete from game_data')
            cur.execute('insert into game_data (level) values (?)', (level,))
            conn.commit()
            running = False
            pygame.quit()
            sys.exit()


#calls functions while game is running
def run():
    global events
    while running:
        events = pygame.event.get()
        clock.tick(FPS)
        event()
        draw()
        
        
    

#checks if file is main file and runs game
if __name__ == "__main__":
    run()