import pygame
import sys
from tiles import TileMap
import sqlite3

#connects to database, if no table create one
conn = sqlite3.connect('game_data.db')
cur = conn.cursor()
cur.execute('create table if not exists game_data (level integer)')

#fetched data from database
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

#loads tilemap and calculates y offset to lower map
tilemap = TileMap(TILEMAP_PATH, tile_size=TILE_SIZE)
map_offset_y = SCREEN_HEIGHT - len(tilemap.map_data) * TILE_SIZE
map_offset_y += MAP_SHIFT_DOWN_TILES * TILE_SIZE

def draw():
    screen.fill((0,0,0))
    tilemap.draw_map(screen, y_offset=map_offset_y)
    pygame.display.flip()
    
#handles events in game, 
def events():
    global level, running
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
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
    while running:
        clock.tick(FPS)
        events()
        draw()
        
    

#checks if file is main file and runs game
if __name__ == "__main__":
    run()