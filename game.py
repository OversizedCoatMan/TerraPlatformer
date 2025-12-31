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
cur.execute('create table if not exists game_data (level integer, deaths integer)')

#fetches data from database
cur.execute('select level, deaths from game_data order by rowid desc limit 1')
row = cur.fetchall()

#checks if there is level data in database, if not it sets it to level 1
if row:
    level = row[0][0]
    # Ensure deaths is an integer (fallback to 0 if DB stored NULL)
    deaths = row[0][1] if row[0][1] is not None else 0
    # If the database stored NULL for deaths, normalize it back to 0 so future updates are numeric
    if row[0][1] is None:
        try:
            cur.execute('update game_data set deaths = ? where rowid = (select rowid from game_data order by rowid desc limit 1)', (deaths,))
            conn.commit()
        except Exception:
            pass
else:
    cur.execute('insert into game_data (level, deaths) values (?, ?)', (1, 0))
    conn.commit()
    level = 1
    deaths = 0
# determine tilemap path from saved level, with fallback if file missing
TILEMAP_PATH = f'assets/level {level}.tmx'
if not os.path.exists(TILEMAP_PATH):
    print(f"Warning: map '{TILEMAP_PATH}' not found; falling back to 'assets/level 1.tmx'")
    # reset saved level to 1 and persist that change
    level = 1
    TILEMAP_PATH = 'assets/level 1.tmx'
    try:
        cur.execute('delete from game_data')
        cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, 0))
        conn.commit()
    except Exception:
        pass


#constant variables

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600 
FPS = 60
LIVES = 3
PLAYER_SIZE = (50, 60)
PLAYER_SPEED = 2.25
JUMP_VELOCITY = -11  # initial jump impulse (negative = upward)
GRAVITY = 0.5
SLIME_SPEED = 1.1

TILE_SIZE = 32
MAP_SHIFT_DOWN_TILES = 0  
PASS_THROUGH_TILES = ["1", "4", "5", "6", "7", "8", "9", "10", "11"]  # Tiles that can be passed through 
KILL_BLOCK_TILES = {"13"}



#initialises pygame and display
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile Game")
clock = pygame.time.Clock()
running = True
life_image = pygame.image.load('assets/heart.png').convert_alpha()
life_image = pygame.transform.scale(life_image, (32, 32))
arial = pygame.font.SysFont('Arial', 24, False, False)
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

def death_counter():
    global deaths
    # Render death counter in white so it contrasts with the black background
    death_text = arial.render(f'Deaths: {deaths}', True, (255, 255, 255))
    screen.blit(death_text, (680, 10))
class BUTTON:
    def __init__(self, x, y, image, scale, held):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def menu(self, events, pos):
        
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
        # default spawn position
        self.player_x = 100
        self.player_y = 400
        if level == 2:
            # alternate spawn for level 2
            self.player_x = 10
            self.player_y = 550
        elif level == 3:
            # alternate spawn for level 3
            self.player_x = 10
            self.player_y = 350

        self.player_vel_y = 0
        self.is_jumping = False
        self.facing_right = True
        # keys will be refreshed each frame in update()
        self.keys = pygame.key.get_pressed()

    def update(self):
        global level, TILEMAP_PATH, tilemap, map_offset_y, blue_enemy, tile_bottom, tile_top, tile_left, tile_right
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
        # Advance level when reaching the right edge
        if self.player_x >= 800 - PLAYER_SIZE[0]:
            new_level = level + 1
            new_path = f'assets/level {new_level}.tmx'
            if not os.path.exists(new_path):
                print(f"Warning: map '{new_path}' not found; staying on level {level}")
            else:
                level = new_level
                TILEMAP_PATH = new_path
                # reload and assign globally so draw/update use the new map
                tilemap = load_map(TILEMAP_PATH)
                self.tilemap = tilemap
                map_offset_y = SCREEN_HEIGHT - len(tilemap.map_data) * TILE_SIZE
                self.map_offset_y = map_offset_y
                # persist level and current death count
                cur.execute('delete from game_data')
                cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, deaths))
                conn.commit()
                # respawn enemy for the new level and attach to player (may be None)
                blue_enemy = spawn_enemy(level)
                self.blue_slime = blue_enemy
                # place player at left edge of new level
                self.player_x = 0

        self.player_x += dx
        player_rect = pygame.Rect(self.player_x, self.player_y, PLAYER_SIZE[0], PLAYER_SIZE[1])

        

        # Horizontal
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
                    if tile.tile_id in KILL_BLOCK_TILES:
                        reset_game()
                    else:
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
            
               
            
            if player_right > tile_left + 5 and player_left < tile_right - 5:
                if self.player_vel_y > 0 and player_bottom > tile_top and player_top < tile_top:
                    if tile.tile_id in KILL_BLOCK_TILES:
                        reset_game()
                    else:
                # Falling
                        self.player_y = tile_top - PLAYER_SIZE[1]
                        self.player_vel_y = 0
                        self.is_jumping = False
                elif self.player_vel_y < 0 and player_top < tile_bottom and player_bottom > tile_bottom:
                    if tile.tile_id in KILL_BLOCK_TILES:
                        reset_game()
                    else:
                # Jumping
                        self.player_y = tile_bottom
                        self.player_vel_y = 0
        if self.player_y >= SCREEN_HEIGHT - 32:
            reset_game()
    def draw(self, surface):
        """Draw the player on the given surface, flipping when facing left."""
        image = self.player if self.facing_right else pygame.transform.flip(self.player, True, False)
        surface.blit(image, (self.player_x, self.player_y))
class blue_slime:
    def __init__(self, x, y):
        self.image = pygame.image.load('assets/blue slime.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (32, 32))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.direction = 1
        
    def movement(self):
        global SLIME_DIRECTION, tile_left, tile_right
        
        slime_left = self.rect.x
        slime_right = self.rect.x + self.rect.width
        slime_bottom = self.rect.y + self.rect.height
        slime_top = self.rect.y

        self.rect.x += SLIME_SPEED * self.direction

            # --- HORIZONTAL COLLISION ---
        for tile in tilemap.tiles:
            if tile.tile_id in PASS_THROUGH_TILES:
                continue

            tile_top = tile.rect.y + map_offset_y
            tile_bottom = tile_top + TILE_SIZE
            tile_left = tile.rect.x
            tile_right = tile_left + TILE_SIZE

            slime_left = self.rect.x
            slime_right = self.rect.x + TILE_SIZE
            slime_top = self.rect.y
            slime_bottom = self.rect.y + TILE_SIZE

            if slime_bottom > tile_top and slime_top < tile_bottom:
                # Walking into wall RIGHT
                if self.direction == 1 and slime_right > tile_left and slime_left < tile_left:
                    self.rect.x = tile_left - TILE_SIZE
                    self.direction = -1
                    # Walking into wall LEFT
                elif self.direction == -1 and slime_left < tile_right and slime_right > tile_right:
                    self.rect.x = tile_right
                    self.direction = 1
        self.rect.topleft = (self.rect.x, self.rect.y)

    def collision(self, player_rect):
        if self.rect.colliderect(player_rect):
            reset_game()

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))


def spawn_enemy(level):
    global blue_enemy
    if level == 1:
        return blue_slime(300, 504)
    elif level == 2:
        return blue_slime(200, 536)
    elif level == 3:
        return blue_slime(900, 500)
    else:
        return None




player_obj = player()
player_obj.tilemap = tilemap
player_obj.map_offset_y = map_offset_y
# spawn the enemy for the current level
blue_enemy = spawn_enemy(level)
# attach the global enemy to the player so collisions work (player checks hasattr)
player_obj.blue_slime = blue_enemy

def draw():
    screen.fill((102,102,255))
    tilemap.draw_map(screen, y_offset=map_offset_y)
    menu_button.menu(events, pos=pygame.mouse.get_pos())
   
    player_obj.draw(screen)
    if LIVES == 3:
        screen.blit(life_image, (0, 20))
        screen.blit(life_image, (35, 20))
        screen.blit(life_image, (70, 20))
    elif LIVES == 2:
        screen.blit(life_image, (0, 20))
        screen.blit(life_image, (35, 20))
    elif LIVES == 1:
        screen.blit(life_image, (0, 20))
    if blue_enemy is not None:
        blue_enemy.draw(screen)
        blue_enemy.collision(pygame.Rect(player_obj.player_x, player_obj.player_y, PLAYER_SIZE[0], PLAYER_SIZE[1]))
    # Draw HUD elements before flipping the display
    death_counter()
    pygame.display.flip()
    

    
def reset_game():
    global level, LIVES, deaths, TILEMAP_PATH, tilemap, map_offset_y, blue_enemy
    # Defensive: ensure deaths is an int (in case DB had NULL or other code left it unset)
    if deaths is None:
        deaths = 0
    LIVES -= 1
    deaths += 1

    print(deaths)
    cur.execute('delete from game_data')
    cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, deaths))
    if LIVES == 0:
        # fully reset to level 1 and update globals used by draw()/collision
        level = 1
        TILEMAP_PATH = 'assets/level 1.tmx'
        tilemap = load_map(TILEMAP_PATH)
        map_offset_y = SCREEN_HEIGHT - len(tilemap.map_data) * TILE_SIZE
        # attach updated map and offset to player so collisions match rendering
        player_obj.tilemap = tilemap
        player_obj.map_offset_y = map_offset_y
        player_obj.player_x = 100
        player_obj.player_y = 374
        # respawn and attach enemy for the new level
        blue_enemy = spawn_enemy(level)
        player_obj.blue_slime = blue_enemy
        # persist level to database
        try:
            cur.execute('delete from game_data')
            cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, deaths))
            conn.commit()
        except Exception:
            pass
        # restore lives
        LIVES = 3

    else:
        # reset player state and position for current level
        player_obj.player_vel_y = 0
        player_obj.is_jumping = False
        if level == 1:
            player_obj.player_x = 100
            player_obj.player_y = 374
        elif level == 2:
            player_obj.player_x = 10
            player_obj.player_y = 462
        elif level == 3:
            player_obj.player_x = 10
            player_obj.player_y = 352
#handles events in game, 
def event():
    global level, running, events
    keys = pygame.key.get_pressed()
    pos = pygame.mouse.get_pos()
    
    for event in events:
        if event.type == pygame.QUIT:
            
            
            cur.execute('delete from game_data')
            cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, deaths))
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
        if level == 1:
            TILEMAP_PATH = 'assets/level 1.tmx'
        elif level == 2:
            TILEMAP_PATH = 'assets/level 2.tmx'
        event()
        player_obj.update()
        
        blue_slime.movement(blue_enemy)
        draw()

        
        
        
    

#checks if file is main file and runs game
if __name__ == "__main__":
    run()