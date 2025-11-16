import pygame 

pygame.init()

LENGTH = 800
HEIGHT = 600
player_x = 10
player_y = 520
player_speed = 2.5
player_vel_y = 0
is_jumping = False
player_facing_right = True

game = pygame.display.set_mode((LENGTH, HEIGHT))
dirt_block = pygame.image.load("assets/dirt block placed.png").convert_alpha()

player = pygame.image.load("assets/player1.png").convert_alpha()
player = pygame.transform.scale(player, (50, 60))  

class BLOCK:
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw_block(self, game):
        game.blit(self.image, (self.rect.x, self.rect.y))
    
    def check_collision(self, player_x, player_y, player_width, player_height):
        if player_x + player_width > self.rect.x and player_x < self.rect.x + self.rect.width:
            if player_y + player_height > self.rect.y and player_y < self.rect.y + self.rect.height:
                return True
        return False


def gravity():
    global player_y, player_vel_y, is_jumping
    player_vel_y += 0.5
    player_y += player_vel_y
    
    # Check collision with dirt block
    if dirt.check_collision(player_x, player_y, player.get_width(), player.get_height()):
        if player_vel_y > 0:
            # Falling onto block - place on top
            player_y = dirt.rect.y - player.get_height()
            player_vel_y = 0
            is_jumping = False
        else:
            # Jumping into block from below - stop upward movement
            player_y = dirt.rect.y + dirt.rect.height
            player_vel_y = 0
    
    # Check if reached ground
    elif player_y >= HEIGHT - player.get_height():
        player_y = HEIGHT - player.get_height()
        player_vel_y = 0
        is_jumping = False

def move_player():
    global player_x, player_y, player_vel_y, is_jumping, events, player_facing_right
    keys = pygame.key.get_pressed()

    if keys[pygame.K_a]:
        if player_x > 0 and not dirt.check_collision(player_x - player_speed, player_y, player.get_width(), player.get_height()):
            player_x -= player_speed
        player_facing_right = False

    if keys[pygame.K_d]:
        if player_x < LENGTH - player.get_width() and not dirt.check_collision(player_x + player_speed, player_y, player.get_width(), player.get_height()):
            player_x += player_speed
        player_facing_right = True

    for event in events:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not is_jumping:
            # Check if standing on block or ground
            on_block = dirt.check_collision(player_x, player_y + 2, player.get_width(), player.get_height())
            on_ground = player_y + player.get_height() >= HEIGHT - 2
            if on_block or on_ground:
                player_vel_y = -10
                is_jumping = True


def draw(game):
    global player_x, player_y, player_facing_right
    game.fill((0, 0, 0))
    if player_facing_right:
        game.blit(player, (player_x, player_y))
    else:
        game.blit(pygame.transform.flip(player, True, False), (player_x, player_y))
dirt = BLOCK(200, 515, dirt_block, 0.5)
clock = pygame.time.Clock()
running = True
while running:
    events = pygame.event.get()
    pos = pygame.mouse.get_pos()
    clock.tick(60)
    
    gravity()
    move_player()
    draw(game)
    dirt.draw_block(game)
        
    for event in events:
        if event.type == pygame.QUIT:
            running = False
    pygame.display.update()
pygame.quit()
