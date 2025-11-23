import pygame, csv, os

class Tile(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, y_offset=0):
        surface.blit(self.image, (self.rect.x, self.rect.y + y_offset))


class TileMap:
    def __init__(self, filename, tile_size=32):
        self.tile_size = tile_size
        self.tiles = self.load_tiles(filename)

        # Store map dimensions
        self.map_width = max(tile.rect.x for tile in self.tiles) + self.tile_size if self.tiles else 0
        self.map_height = max(tile.rect.y for tile in self.tiles) + self.tile_size if self.tiles else 0

        # Read raw CSV for calculations
        self.map_data = self.read_csv(filename)

    def read_csv(self, filename):
        map_data = []
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                map_data.append(row)
        return map_data

    def load_tiles(self, filename):
        tiles = []
        map_data = self.read_csv(filename)
        for y, row in enumerate(map_data):
            for x, tile in enumerate(row):
                if tile == '1':
                    tiles.append(Tile('assets/dirt block placed.png', x*self.tile_size, y*self.tile_size))
                elif tile == '2':
                    tiles.append(Tile('assets/grass.png', x*self.tile_size, y*self.tile_size))
        return tiles

    def draw_map(self, surface, y_offset=0):
        for tile in self.tiles:
            tile.draw(surface, y_offset)
