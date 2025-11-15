import pygame 

LENGTH = 800
HEIGHT = 600
player_x = 10
player_y = 520
player_speed = 2.5
player_vel_y = 0
is_jumping = False
player_facing_right = True
pygame.init()
game = pygame.display.set_mode((LENGTH, HEIGHT))

player = pygame.image.load("assets/player1.png").convert_alpha()
player = pygame.transform.scale(player, (60, 70))   

def gravity():
    global player_y, player_vel_y, is_jumping
    player_vel_y += 0.5
    player_y += player_vel_y
    
    if player_y >= HEIGHT - player.get_height():
        player_y = HEIGHT - player.get_height()
        player_vel_y = 0
        is_jumping = False

def move_player():
    global player_x, player_y, player_vel_y, is_jumping, events, player_facing_right
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        if player_x > 0:
            player_x -= player_speed
        player_facing_right = False
    if keys[pygame.K_d]:
        if player_x < LENGTH - player.get_width():
            player_x += player_speed
        player_facing_right = True
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not is_jumping:
                player_vel_y = -10
                is_jumping = True


def draw(game):
    global player_x, player_y, player_facing_right
    game.fill((0, 0, 0))
    if player_facing_right:
        game.blit(player, (player_x, player_y))
    else:
        game.blit(pygame.transform.flip(player, True, False), (player_x, player_y))

clock = pygame.time.Clock()
running = True
while running:
    events = pygame.event.get()
    pos = pygame.mouse.get_pos()
    clock.tick(60)
    draw(game)
    move_player()
    gravity()
    
        
    for event in events:
        if event.type == pygame.QUIT:
            running = False
    pygame.display.update()
pygame.quit()
