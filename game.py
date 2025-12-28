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
if level == 1:
    TILEMAP_PATH = 'assets/level 1.tmx'
elif level == 2:
    TILEMAP_PATH = 'assets/level 2.tmx'


#constant variables

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600 
FPS = 60
PLAYER_SIZE = (50, 60)
PLAYER_SPEED = 2.25
JUMP_VELOCITY = -11  # initial jump impulse (negative = upward)
GRAVITY = 0.5
TILE_SIZE = 32
MAP_SHIFT_DOWN_TILES = 0  
PASS_THROUGH_TILES = ["1", "4", "5", "6", "7", "8", "9", "10", "11"]  # Tiles that can be passed through 

#initialises pygame and display
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile Game")
clock = pygame.time.Clock()
running = True

# Example layer configuration: midground (trees) between background and spikes
LAYER_IDS = {
    'midground': {'4'},   # trees on their own layer
    'foreground': {'13'}  # spikes on top
}
LAYER_ORDER = ['background', 'midground', 'foreground']

def load_map(filename):
    # pass custom layers to TileMap; defaults keep behaviour the same if omitted
    return TileMap(filename, tile_size=TILE_SIZE, layer_ids=LAYER_IDS, layer_order=LAYER_ORDER)

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

# create player instance after map is loaded
class player:
    def __init__(self):
        self.player = pygame.image.load('assets/PLAYER1.png').convert_alpha()
        self.player = pygame.transform.scale(self.player, PLAYER_SIZE)
        if level == 1:
            self.player_x = 100
            self.player_y = 400
        elif level == 2:
            self.player_x = 10
            self.player_y = 550
        
        self.player_vel_y = 0
        self.is_jumping = False
        self.facing_right = True
        # keys will be refreshed each frame in update()
        self.keys = pygame.key.get_pressed()

    def update(self):
        # refresh input snapshot each frame
        self.keys = pygame.key.get_pressed()

        # HORIZONTAL MOVEMENT
        dx = 0
        if self.keys[pygame.K_a]:
            dx = -PLAYER_SPEED
            self.facing_right = False
        if self.keys[pygame.K_d]:
            dx = PLAYER_SPEED
            self.facing_right = True

        self.player_x += dx
        player_rect = pygame.Rect(self.player_x, self.player_y, PLAYER_SIZE[0], PLAYER_SIZE[1])

        # optional collision with blue_slime if present
        if hasattr(self, 'blue_slime') and player_rect.colliderect(self.blue_slime.rect):
            if hasattr(self, 'reset_game'):
                self.reset_game()

        # Horizontal collision
        for tile in self.tilemap.tiles:
            if tile.tile_id in PASS_THROUGH_TILES:
                continue
            tile_top = tile.rect.y + self.map_offset_y
            tile_bottom = tile_top + TILE_SIZE
            tile_left = tile.rect.x
            tile_right = tile_left + TILE_SIZE

            player_right = self.player_x + PLAYER_SIZE[0]
            player_left = self.player_x
            player_top = self.player_y
            player_bottom = self.player_y + PLAYER_SIZE[1]

            if player_bottom > tile_top and player_top < tile_bottom:
                if dx > 0 and player_right > tile_left and player_left < tile_left:
                    self.player_x = tile_left - PLAYER_SIZE[0]
                elif dx < 0 and player_left < tile_right and player_right > tile_right:
                    self.player_x = tile_right
            
        # Clamp player horizontally
        map_left = 0
        map_right = max(tile.rect.x for tile in self.tilemap.tiles) + TILE_SIZE

        self.player_x = max(map_left, min(self.player_x, map_right - PLAYER_SIZE[0]))

        # JUMPING (single-press)
        if (self.keys[pygame.K_SPACE] or self.keys[pygame.K_w] or self.keys[pygame.K_UP]) and not self.is_jumping:
            self.player_vel_y = JUMP_VELOCITY
            self.is_jumping = True

        # VERTICAL MOVEMENT
        self.player_vel_y += GRAVITY
        self.player_y += self.player_vel_y

        # Vertical collision
        for tile in self.tilemap.tiles:
            if tile.tile_id in  PASS_THROUGH_TILES:
                continue
            
            tile_top = tile.rect.y + self.map_offset_y
            tile_bottom = tile_top + TILE_SIZE
            tile_left = tile.rect.x
            tile_right = tile_left + TILE_SIZE

            player_right = self.player_x + PLAYER_SIZE[0]
            player_left = self.player_x
            player_top = self.player_y
            player_bottom = self.player_y + PLAYER_SIZE[1]
            
               
            
            if player_right > tile_left and player_left < tile_right:
                if self.player_vel_y > 0 and player_bottom > tile_top and player_top < tile_top:
                # Falling
                    self.player_y = tile_top - PLAYER_SIZE[1]
                    self.player_vel_y = 0
                    self.is_jumping = False
                elif self.player_vel_y < 0 and player_top < tile_bottom and player_bottom > tile_bottom:
                # Jumping
                    self.player_y = tile_bottom
                    self.player_vel_y = 0

    def draw(self, surface):
        """Draw the player on the given surface, flipping when facing left."""
        image = self.player if self.facing_right else pygame.transform.flip(self.player, True, False)
        surface.blit(image, (self.player_x, self.player_y))

# instantiate and attach map info (done after the player class is fully defined)
player_obj = player()
player_obj.tilemap = tilemap
player_obj.map_offset_y = map_offset_y

def draw():
    screen.fill((0,0,0))
    tilemap.draw_map(screen, y_offset=map_offset_y)
    menu_button.menu(events, pos=pygame.mouse.get_pos())
    # draw player on top of tiles
    player_obj.draw(screen)

    pygame.display.flip()
    
def update():
    # game update logic
    player_obj.update()

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
        update()
        draw()
        
        
        
    

#checks if file is main file and runs game
if __name__ == "__main__":
    run()