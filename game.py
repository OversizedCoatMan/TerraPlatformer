import pygame
import sys
from tiles import TileMap
import sqlite3
import subprocess
import os


conn = sqlite3.connect('assets/game_data.db')
cur = conn.cursor()
cur.execute('create table if not exists game_data (level integer, deaths integer)')

cur.execute('select level, deaths from game_data order by rowid desc limit 1')
row = cur.fetchall()

if row:
    level = row[0][0]
    
    deaths = row[0][1] if row[0][1] is not None else 0
    
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
TILEMAP_PATH = f'assets/level {level}.tmx'
if not os.path.exists(TILEMAP_PATH):
    print(f"Warning: map '{TILEMAP_PATH}' not found; falling back to 'assets/level 1.tmx'")
    
    level = 1
    TILEMAP_PATH = 'assets/level 1.tmx'
    try:
        cur.execute('delete from game_data')
        cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, 0))
        conn.commit()
    except Exception:
        pass


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600 
FPS = 60
LIVES = 3

respawn_cooldown = 0
reward_cooldown = 0
is_resetting = False
PLAYER_SIZE = (50, 60)
PLAYER_SPEED = 2.25
JUMP_VELOCITY = -11
GRAVITY = 0.5
SLIME_SPEED = 1.1

TILE_SIZE = 32
MAP_SHIFT_DOWN_TILES = 0  
PASS_THROUGH_TILES = ["1", "4", "5", "6", "7", "8", "9", "10", "11"]   
KILL_BLOCK_TILES = {"13", "14"}


def get_spawn_for_level(lvl):
    """Return (x,y) spawn coordinates (map/screen pixels) for given level."""
    if lvl == 1:
        return 100, 400
    if lvl == 2:
        return 10, 550
    if lvl == 3:
        return 10, 350
    if lvl == 4:
        return 10, 550
    return 10, 350


def resolve_player_spawn(p):
    """If the player is overlapping solid tiles after a spawn, nudge them up until clear.

    This prevents the player from being placed inside geometry and phasing through
    on the next update. Limits to 200 pixels of upward adjustment.
    """
    for _ in range(200):
        player_rect = pygame.Rect(p.player_x, p.player_y, PLAYER_SIZE[0], PLAYER_SIZE[1])
        overlapping = False
        for tile in p.tilemap.tiles:
            if tile.tile_id in PASS_THROUGH_TILES:
                continue
            tile_rect = pygame.Rect(tile.rect.x, tile.rect.y + p.map_offset_y, TILE_SIZE, TILE_SIZE)
            if player_rect.colliderect(tile_rect):
                overlapping = True
                break
        if not overlapping:
            return
        p.player_y -= 1




pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile Game")
clock = pygame.time.Clock()
running = True
life_image = pygame.image.load('assets/heart.png').convert_alpha()
life_image = pygame.transform.scale(life_image, (32, 32))
arial = pygame.font.SysFont('Arial', 24, False, False)
footstep_grass = pygame.mixer.Sound("assets/footstep grass 28.wav")
LAYER_IDS = {
    'midground': {'4'},
    'foreground': {'13'}
}
LAYER_ORDER = ['background', 'midground', 'foreground']

def load_map(filename):
    return TileMap(filename, tile_size=TILE_SIZE, layer_ids=LAYER_IDS, layer_order=LAYER_ORDER)

tilemap = load_map(TILEMAP_PATH)
map_offset_y = SCREEN_HEIGHT - len(tilemap.map_data) * TILE_SIZE
map_offset_y += MAP_SHIFT_DOWN_TILES * TILE_SIZE

main_menu = pygame.image.load('assets/main menu.png').convert_alpha()
def death_counter():
    global deaths
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
                if self.rect.collidepoint(event.pos):
                    script_path = os.path.join(os.path.dirname(__file__), 'main.py')
                    subprocess.Popen([sys.executable, script_path], cwd=os.path.dirname(__file__))
                    running = False
menu_button = BUTTON(48, 11, main_menu, 0.2, False)

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
        elif level == 3:
            self.player_x = 10
            self.player_y = 350
        elif level == 4:
            self.player_x = 10
            self.player_y = 550
            
        self.player_vel_y = 0
        self.is_jumping = False

        self.player_vel_y = 0
        self.is_jumping = False
        self.facing_right = True
        
        self.keys = pygame.key.get_pressed()
        self.footstep_grass = footstep_grass
        self._last_sfx_time = 0

    def update(self):
        global level, TILEMAP_PATH, tilemap, map_offset_y, blue_enemy, tile_bottom, tile_top, tile_left, tile_right
        debounce_ms = 500
        self.keys = pygame.key.get_pressed()

        dx = 0
        if self.keys[pygame.K_a]:
            dx = -PLAYER_SPEED
            if not self.is_jumping:
                now = pygame.time.get_ticks()
                if now - self._last_sfx_time >= debounce_ms:
                    player_bottom = self.player_y + PLAYER_SIZE[1]
                    player_center_x = self.player_x + PLAYER_SIZE[0] // 2
                    on_grass = False
                    for tile in self.tilemap.tiles:
                        tile_screen = pygame.Rect(tile.rect.x, tile.rect.y + self.map_offset_y, TILE_SIZE, TILE_SIZE)
                        if tile_screen.collidepoint(player_center_x, player_bottom):
                            if tile.tile_id == '3':
                                on_grass = True
                            break
                    if on_grass:
                        self.footstep_grass.play()
                        self._last_sfx_time = now
            self.facing_right = False
        if self.keys[pygame.K_d]:
            dx = PLAYER_SPEED
            if not self.is_jumping:
                now = pygame.time.get_ticks()
                if now - self._last_sfx_time >= debounce_ms:
                    player_bottom = self.player_y + PLAYER_SIZE[1]
                    player_center_x = self.player_x + PLAYER_SIZE[0] // 2
                    on_grass = False
                    for tile in self.tilemap.tiles:
                        tile_screen = pygame.Rect(tile.rect.x, tile.rect.y + self.map_offset_y, TILE_SIZE, TILE_SIZE)
                        if tile_screen.collidepoint(player_center_x, player_bottom):
                            if tile.tile_id == '3':
                                on_grass = True
                            break
                    if on_grass:
                        self.footstep_grass.play()
                        self._last_sfx_time = now
            self.facing_right = True
        if self.player_x >= 800 - PLAYER_SIZE[0]:
            new_level = level + 1
            new_path = f'assets/level {new_level}.tmx'
            if reward_cooldown == 0:
                reward_player()
            if not os.path.exists(new_path):
                print(f"Warning: map '{new_path}' not found; staying on level {level}")
            else:
                level = new_level
                TILEMAP_PATH = new_path
                tilemap = load_map(TILEMAP_PATH)
                self.tilemap = tilemap
                map_offset_y = SCREEN_HEIGHT - len(tilemap.map_data) * TILE_SIZE
                self.map_offset_y = map_offset_y
                
                cur.execute('delete from game_data')
                cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, deaths))
                conn.commit()
                blue_enemy = spawn_enemy(level)
                self.blue_slime = blue_enemy
                sx, sy = get_spawn_for_level(level)
                self.player_x = sx
                self.player_y = sy
                self.player_vel_y = 0
                self.is_jumping = False
                resolve_player_spawn(self)

        self.player_x += dx
        player_rect = pygame.Rect(self.player_x, self.player_y, PLAYER_SIZE[0], PLAYER_SIZE[1])

        

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
            
        map_left = 0
        map_right = max(tile.rect.x for tile in self.tilemap.tiles) + TILE_SIZE

        self.player_x = max(map_left, min(self.player_x, map_right - PLAYER_SIZE[0]))

        if (self.keys[pygame.K_SPACE] or self.keys[pygame.K_w] or self.keys[pygame.K_UP]) and not self.is_jumping:
            self.player_vel_y = JUMP_VELOCITY
            self.is_jumping = True

        self.player_vel_y += GRAVITY
        self.player_y += self.player_vel_y

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
                        self.player_y = tile_top - PLAYER_SIZE[1]
                        self.player_vel_y = 0
                        self.is_jumping = False
                elif self.player_vel_y < 0 and player_top < tile_bottom and player_bottom > tile_bottom:
                    if tile.tile_id in KILL_BLOCK_TILES:
                        reset_game()
                    else:
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
                if self.direction == 1 and slime_right > tile_left and slime_left < tile_left:
                    self.rect.x = tile_left - TILE_SIZE
                    self.direction = -1
                elif self.direction == -1 and slime_left < tile_right and slime_right > tile_right:
                    self.rect.x = tile_right
                    self.direction = 1
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
blue_enemy = spawn_enemy(level)

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
    
    death_counter()
    pygame.display.flip()
    
def reward_player():
    global level, LIVES, reward_cooldown
    if level == 3 and LIVES < 3:
        LIVES += 1
        reward_cooldown = FPS * 2
    
def reset_game(ignore_cooldown=False):
    global level, LIVES, deaths, TILEMAP_PATH, tilemap, map_offset_y, blue_enemy, respawn_cooldown, reward_cooldown, is_resetting
    if is_resetting and not ignore_cooldown:
        return
    if not ignore_cooldown and respawn_cooldown > 0:
        return

    is_resetting = True
    try:
        if deaths is None:
            deaths = 0
        LIVES -= 1
        deaths += 1

        print(deaths)
        cur.execute('delete from game_data')
        cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, deaths))
        respawn_cooldown = FPS//2
        if LIVES == 0:
            LIVES = 3
            level = 1
            player_obj.player_x = 100
            player_obj.player_y = 374
            player_obj.player_vel_y = 0
            player_obj.is_jumping = False
            TILEMAP_PATH = 'assets/level 1.tmx'
            tilemap = load_map(TILEMAP_PATH)
            map_offset_y = SCREEN_HEIGHT - len(tilemap.map_data) * TILE_SIZE
            player_obj.tilemap = tilemap
            player_obj.map_offset_y = map_offset_y
            
            blue_enemy = spawn_enemy(level)
            player_obj.blue_slime = blue_enemy
            try:
                cur.execute('delete from game_data')
                cur.execute('insert into game_data (level, deaths) values (?, ?)', (level, deaths))
                conn.commit()
            except Exception:
                pass
            respawn_cooldown = FPS/2

        else:
            player_obj.player_vel_y = 0
            player_obj.is_jumping = False
            sx, sy = get_spawn_for_level(level)
            player_obj.player_x = sx
            player_obj.player_y = sy
            resolve_player_spawn(player_obj)
    finally:
        is_resetting = False

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


def run():
    global events, respawn_cooldown, reward_cooldown
    while running:
        events = pygame.event.get()
        clock.tick(FPS)
        if respawn_cooldown > 0:
            respawn_cooldown -= 1
        if reward_cooldown > 0:
            reward_cooldown -= 1
        if level == 1:
            TILEMAP_PATH = 'assets/level 1.tmx'
        elif level == 2:
            TILEMAP_PATH = 'assets/level 2.tmx'
        event()
        player_obj.update()
        
        if blue_enemy is not None:
            blue_enemy.movement()
        draw()

if __name__ == "__main__":
    run()