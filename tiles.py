import pygame, csv, os

class Tile(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y, tile_id):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.tile_id = tile_id

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
        # Support two formats: a plain CSV (rows of comma-separated values)
        # or a Tiled TMX file with a <data encoding="csv">...</data> block.
        map_data = []
        with open(filename, 'r', newline='') as f:
            content = f.read()

        # If file looks like a TMX (XML) file, extract the CSV block
        if '<data' in content and '</data>' in content:
            start = content.find('<data')
            # find the closing '>' of the opening <data ...> tag
            start = content.find('>', start) + 1
            end = content.find('</data>', start)
            csv_block = content[start:end].strip()
            # csv_block may contain newlines and trailing commas
            for line in csv_block.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Remove any trailing commas, split on commas
                parts = [cell.strip() for cell in line.split(',') if cell.strip() != '']
                if parts:
                    map_data.append(parts)
        else:
            # Plain CSV file
            with open(filename, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    map_data.append([cell.strip() for cell in row])

        return map_data

    def load_tiles(self, filename):
        tiles = []
        map_data = self.read_csv(filename)
        for y, row in enumerate(map_data):
            for x, tile in enumerate(row):
                if tile == '1':
                    tiles.append(Tile('assets/dirt block placed.png', x*self.tile_size, y*self.tile_size, tile_id="1"))
                elif tile == '2':
                    tiles.append(Tile('assets/grass.png', x*self.tile_size, y*self.tile_size, tile_id="2"))
                elif tile == '10':
                    tiles.append(Tile('assets/Tree Root L.png', x*self.tile_size, y*self.tile_size, tile_id="10"))
                elif tile == '11':
                    tiles.append(Tile('assets/tree root r.png', x*self.tile_size, y*self.tile_size, tile_id="11"))
                elif tile == '12':
                    tiles.append(Tile('assets/trunk 1.png', x*self.tile_size, y*self.tile_size, tile_id="12"))
                elif tile == '13':
                    tiles.append(Tile('assets/trunk 2.png', x*self.tile_size, y*self.tile_size, tile_id="13"))
                elif tile == '14':
                    tiles.append(Tile('assets/trunk 3.png', x*self.tile_size, y*self.tile_size, tile_id="14"))
                elif tile == '15':
                    tiles.append(Tile('assets/trunk 4.png', x*self.tile_size, y*self.tile_size, tile_id="15"))
                elif tile == '16':
                    tiles.append(Tile('assets/trunk base.png', x*self.tile_size, y*self.tile_size, tile_id="16"))
                elif tile == '19':
                    tiles.append(Tile('assets/mini tree.png', x*self.tile_size, y*self.tile_size, tile_id="19"))
                elif tile == '20':
                    tiles.append(Tile('assets/dirt bg.png', x*self.tile_size, y*self.tile_size, tile_id="20"))
        return tiles

    def draw_map(self, surface, y_offset=0):
        for tile in self.tiles:
            tile.draw(surface, y_offset)
