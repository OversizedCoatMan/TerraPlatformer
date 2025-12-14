import pygame
import sys
from tiles import TileMap

# --------------------------
# CONFIG
# --------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SIZE = (50, 60)
GRAVITY = 0.5
JUMP_VELOCITY = -11
PLAYER_SPEED = 2.25
SLIME_SPEED = 2
TILEMAP_PATH = 'assets/tree test.csv'
TILE_SIZE = 32  # Size of each tile
MAP_SHIFT_DOWN_TILES = 3  # Lower map by 3 tiles
PASS_THROUGH_TILES = ["10", "11", "12", "13", "14", "15", "16", "19", "20"]  # Tiles that can be passed through

# --------------------------
# GAME CLASS
# --------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tile Game")
        self.clock = pygame.time.Clock()
        self.running = True

        self.tilemap = TileMap(TILEMAP_PATH, tile_size=TILE_SIZE)
        self.map_offset_y = SCREEN_HEIGHT - len(self.tilemap.map_data) * TILE_SIZE
        self.map_offset_y += MAP_SHIFT_DOWN_TILES * TILE_SIZE

        self.player = pygame.image.load('assets/PLAYER1.png').convert_alpha()
        self.player = pygame.transform.scale(self.player, PLAYER_SIZE)

        # Create enemy here AFTER pygame is initialized
        self.blue_slime = self.Enemy(300, 504, 'assets/blue slime.png')

        self.reset_game()


    class Enemy:
        def __init__(self, x, y, image_path):
            self.x = x
            self.y = y
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
            # Correct rect creation
            self.rect = self.image.get_rect(topleft=(self.x, self.y))
            self.slime_vel_y = 0
            self.direction = 1  # 1 for right, -1 for left
        def slime_ai(self):
            
            # Apply gravity
            self.slime_vel_y += GRAVITY
            self.y += self.slime_vel_y

            # --- VERTICAL COLLISION ---
            for tile in game.tilemap.tiles:
                if tile.tile_id in PASS_THROUGH_TILES:
                    continue

                tile_top = tile.rect.y + game.map_offset_y
                tile_bottom = tile_top + TILE_SIZE
                tile_left = tile.rect.x
                tile_right = tile_left + TILE_SIZE

                slime_left = self.x
                slime_right = self.x + TILE_SIZE
                slime_top = self.y
                slime_bottom = self.y + TILE_SIZE

                if slime_right > tile_left and slime_left < tile_right:
                    # Falling onto tile
                    if self.slime_vel_y > 0 and slime_bottom > tile_top and slime_top < tile_top:
                        self.y = tile_top - TILE_SIZE
                        self.slime_vel_y = 0

            # --- HORIZONTAL MOVEMENT ---
            self.x += SLIME_SPEED * self.direction

            # --- HORIZONTAL COLLISION ---
            for tile in game.tilemap.tiles:
                if tile.tile_id in PASS_THROUGH_TILES:
                    continue

                tile_top = tile.rect.y + game.map_offset_y
                tile_bottom = tile_top + TILE_SIZE
                tile_left = tile.rect.x
                tile_right = tile_left + TILE_SIZE

                slime_left = self.x
                slime_right = self.x + TILE_SIZE
                slime_top = self.y
                slime_bottom = self.y + TILE_SIZE

                if slime_bottom > tile_top and slime_top < tile_bottom:
                    # Walking into wall RIGHT
                    if self.direction == 1 and slime_right > tile_left and slime_left < tile_left:
                        self.x = tile_left - TILE_SIZE
                        self.direction = -1

                    # Walking into wall LEFT
                    elif self.direction == -1 and slime_left < tile_right and slime_right > tile_right:
                        self.x = tile_right
                        self.direction = 1
            self.rect.topleft = (self.x, self.y)

        

            
    # --------------------------
    # RESET GAME
    # --------------------------
    def reset_game(self):
        # Get the bottom-most tile
        bottom_tile = max(self.tilemap.tiles, key=lambda t: t.rect.y)
        self.player_x = 10
        self.player_y = 350  - PLAYER_SIZE[1]
        self.player_vel_y = 0
        self.is_jumping = False
        self.facing_right = True
        self.x = 300
        self.y = 504
        self.direction = 1

    # --------------------------
    # MAIN LOOP
    # --------------------------
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()
            self.blue_slime.slime_ai()
        pygame.quit()
        sys.exit()

    # --------------------------
    # EVENT HANDLING
    # --------------------------
    def events(self):
        self.keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not self.is_jumping:
                if self.player_y + PLAYER_SIZE[1] >= SCREEN_HEIGHT or self.tile_below():
                    self.player_vel_y = JUMP_VELOCITY
                    self.is_jumping = True

    # --------------------------
    # HELPERS
    # --------------------------
    def tile_below(self):
        for tile in self.tilemap.tiles:
            tile_top = tile.rect.y + self.map_offset_y
            if (self.player_x + PLAYER_SIZE[0] > tile.rect.x and
                self.player_x < tile.rect.x + TILE_SIZE and
                self.player_y + PLAYER_SIZE[1] >= tile_top - 1):
                return True
        return False

    # --------------------------
    # GAME LOGIC
    # --------------------------
    def update(self):
        
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

        if player_rect.colliderect(self.blue_slime.rect):
            self.reset_game()
        # Horizontal collision
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
            
            if player_bottom > tile_top and player_top < tile_bottom:

                if dx > 0 and player_right > tile_left and player_left < tile_left:
                    self.player_x = tile_left - PLAYER_SIZE[0]
                elif dx < 0 and player_left < tile_right and player_right > tile_right:
                    self.player_x = tile_right
            
        # Clamp player horizontally
        map_left = 0
        map_right = max(tile.rect.x for tile in self.tilemap.tiles) + TILE_SIZE
        self.player_x = max(map_left, min(self.player_x, map_right - PLAYER_SIZE[0]))

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

        # Reset if player falls below screen
        if self.player_y + PLAYER_SIZE[1] >= SCREEN_HEIGHT:
            self.reset_game()
    
    # --------------------------
    # DRAW
    # --------------------------
    def draw(self):
        self.screen.fill((0, 0, 0))
        self.tilemap.draw_map(self.screen, y_offset=self.map_offset_y)
        player_image = self.player if self.facing_right else pygame.transform.flip(self.player, True, False)
        self.screen.blit(player_image, (self.player_x, self.player_y))
        self.screen.blit(self.blue_slime.image, (self.blue_slime.x, self.blue_slime.y))
        pygame.display.update()

# --------------------------
# RUN GAME
# --------------------------
if __name__ == "__main__":
    game = Game()
    game.run()
