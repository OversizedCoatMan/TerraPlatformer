import pygame, csv, os
import xml.etree.ElementTree as ET


class Tile(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y, tile_id, flip_h=False, flip_v=False, flip_d=False):
        """Tile with optional flip flags (from Tiled TMX GID flags).

        flip_h: horizontal flip
        flip_v: vertical flip (useful for upside-down roof spikes)
        flip_d: diagonal flip (approximate by rotating 90deg then applying flips)
        """
        super().__init__()
        img = pygame.image.load(image_path).convert_alpha()

        # Approximate diagonal handling: rotate first, then apply flips.
        if flip_d:
            img = pygame.transform.rotate(img, -90)

        if flip_h or flip_v:
            img = pygame.transform.flip(img, flip_h, flip_v)

        self.image = img
        self.rect = self.image.get_rect(topleft=(x, y))
        self.tile_id = tile_id
        self.flip_h = flip_h
        self.flip_v = flip_v
        self.flip_d = flip_d

    def draw(self, surface, y_offset=0):
        surface.blit(self.image, (self.rect.x, self.rect.y + y_offset))


class TileMap:
    def __init__(self, filename, tile_size=32, layer_ids=None, layer_order=None):
        """Load a tilemap with support for ordered, named layers.

        - layer_ids: dict mapping layer_name -> iterable of tile id strings
          e.g. {'midground': {'4'}, 'foreground': {'13'}}
        - layer_order: list of layer names describing draw order (bottom -> top)
          default is ['background', 'foreground'] where any tile not matched by
          layer_ids will go into 'background'.
        """
        self.tile_size = tile_size

        # default: spikes are foreground
        self.layer_ids = {name: set(ids) for name, ids in (layer_ids or {'foreground': {'13'}}).items()}
        self.layer_order = list(layer_order) if layer_order is not None else ['background', 'foreground']

        # main tile list (compatibility) and named layers
        self.tiles = []
        self.layers = {name: [] for name in self.layer_order}

        # build gid->image map for TMX tilesets (if applicable)
        self.gid_to_image = self.parse_tilesets(filename)

        # load tiles and fill layers
        self.tiles = self.load_tiles(filename)

        # convenience properties for existing code
        self.background_tiles = self.layers.get('background', [])
        self.foreground_tiles = self.layers.get('foreground', [])

        # Store map dimensions
        self.map_width = max(tile.rect.x for tile in self.tiles) + self.tile_size if self.tiles else 0
        self.map_height = max(tile.rect.y for tile in self.tiles) + self.tile_size if self.tiles else 0

        # Read raw CSV for calculations (use first parsed layer if available)
        parsed = self.read_layers(filename)
        self.map_data = parsed[0][1] if parsed else []

    def read_layers(self, filename):
        """Return a list of (layer_name, rows) for a map file.

        - For a plain CSV file we return [('background', rows)].
        - For a TMX file we extract each <layer name="..."> <data>...</data> block
          and return [(layer_name, rows), ...] in file order.
        """
        layers = []
        with open(filename, 'r', newline='') as f:
            content = f.read()

        # TMX multi-layer parsing
        if '<layer' in content and '<data' in content:
            search_pos = 0
            while True:
                layer_start = content.find('<layer', search_pos)
                if layer_start == -1:
                    break
                # try to find name attribute
                name_start = content.find('name="', layer_start)
                if name_start != -1:
                    name_start += len('name="')
                    name_end = content.find('"', name_start)
                    layer_name = content[name_start:name_end]
                else:
                    layer_name = 'layer'

                # find <data ...> inside this layer
                data_start = content.find('<data', layer_start)
                if data_start == -1:
                    search_pos = layer_start + 6
                    continue
                # find end of opening data tag and closing tag
                data_content_start = content.find('>', data_start) + 1
                data_end = content.find('</data>', data_content_start)
                csv_block = content[data_content_start:data_end].strip()

                rows = []
                for line in csv_block.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    parts = [cell.strip() for cell in line.split(',') if cell.strip() != '']
                    if parts:
                        rows.append(parts)

                layers.append((layer_name, rows))
                search_pos = data_end

            return layers

        # Plain CSV fallback (single background layer)
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = []
            for row in reader:
                rows.append([cell.strip() for cell in row])

        return [('background', rows)]

    def parse_tilesets(self, filename):
        """Parse TMX tileset references and return a dict mapping global gid (str) -> image path.

        - Supports external TSX files and inline tileset definitions.
        - Attempts to resolve image paths relative to the TMX or TSX file; falls back to searching the TMX directory by basename.
        """
        gid_map = {}
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
        except Exception:
            return gid_map

        tmx_dir = os.path.dirname(os.path.abspath(filename))

        for tileset in root.findall('tileset'):
            firstgid = int(tileset.get('firstgid', '1'))
            source = tileset.get('source')

            # load external TSX if provided
            tsx_root = None
            tsx_dir = tmx_dir
            if source:
                tsx_path = os.path.join(tmx_dir, source)
                try:
                    tsx_tree = ET.parse(tsx_path)
                    tsx_root = tsx_tree.getroot()
                    tsx_dir = os.path.dirname(os.path.abspath(tsx_path))
                except Exception:
                    tsx_root = None
            else:
                # inline tileset
                tsx_root = tileset

            if tsx_root is None:
                continue

            # find <tile> entries with images
            for tile in tsx_root.findall('tile'):
                local_id = int(tile.get('id', '0'))
                image = tile.find('image')
                if image is None:
                    continue
                src = image.get('source')
                if not src:
                    continue

                # try resolving path relative to tsx dir
                candidate = os.path.join(tsx_dir, src)
                if os.path.exists(candidate):
                    image_path = candidate
                else:
                    # fallback: try to find by basename in tmx dir or project assets directory
                    basename = os.path.basename(src)
                    # prefer local project assets folder if it contains the image
                    project_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
                    candidate_assets = os.path.join(project_assets, basename)
                    if os.path.exists(candidate_assets):
                        image_path = candidate_assets
                    else:
                        candidate2 = os.path.join(tmx_dir, basename)
                        if os.path.exists(candidate2):
                            image_path = candidate2
                        else:
                            # search for file with basename inside tmx_dir (non-recursive)
                            found = None
                            for fname in os.listdir(tmx_dir):
                                if fname.lower() == basename.lower():
                                    found = os.path.join(tmx_dir, fname)
                                    break
                            if found:
                                image_path = found
                            else:
                                # give relative path as last resort
                                image_path = src

                gid = firstgid + local_id
                gid_map[str(gid)] = image_path

        return gid_map


    def _choose_layer_for_id(self, tile_id):
        # return the first layer (by layer_order) that claims this id
        for layer in self.layer_order:
            ids = self.layer_ids.get(layer)
            if ids and tile_id in ids:
                return layer
        # default to background
        return 'background' if 'background' in self.layer_order else self.layer_order[0]

    def _normalize_gid(self, raw):
        """Convert a TMX cell value (may include flip flags) into a plain gid string.

        Tiled stores flipping flags in the high bits; the gid is raw & 0x1FFFFFFF.
        """
        try:
            v = int(raw)
        except Exception:
            return raw
        gid = v & 0x1FFFFFFF
        return str(gid)

    def _parse_gid(self, raw):
        """Return (gid_str, flip_h, flip_v, flip_d).

        Uses Tiled's bitmask flags: horizontal (1<<31), vertical (1<<30), diagonal (1<<29).
        """
        try:
            v = int(raw)
        except Exception:
            return raw, False, False, False

        FLIP_H = bool(v & 0x80000000)
        FLIP_V = bool(v & 0x40000000)
        FLIP_D = bool(v & 0x20000000)
        gid = v & 0x1FFFFFFF
        return str(gid), FLIP_H, FLIP_V, FLIP_D

    def load_tiles(self, filename):
        tiles = []

        # read layers from file (TMX returns list of (name, rows), plain CSV returns [('background', rows)])
        parsed_layers = self.read_layers(filename)

        # If the file is a TMX, use its layer order unless a custom layer_order was provided;
        # merge custom order with parsed names so custom layers are respected but all parsed layers are included.
        parsed_names = [name for name, _ in parsed_layers]
        if parsed_names:
            if any(name in self.layer_order for name in parsed_names):
                # keep declared order but ensure parsed names are present
                merged = [n for n in self.layer_order if n in parsed_names]
                merged += [n for n in parsed_names if n not in merged]
                self.layer_order = merged
            else:
                # prefer file order
                self.layer_order = parsed_names

        # ensure layers dict contains all layer names (include any pre-existing user layers like 'foreground')
        for name in self.layer_order:
            if name not in self.layers:
                self.layers[name] = []
        # append any remaining known layers (from initial config) to the end so they draw on top
        for name in list(self.layers.keys()):
            if name not in self.layer_order:
                self.layer_order.append(name)

        for layer_name, rows in parsed_layers:
            for y, row in enumerate(rows):
                for x, raw in enumerate(row):
                    gid, flip_h, flip_v, flip_d = self._parse_gid(raw)
                    if gid == '0' or gid == '':
                        continue

                    t = None
                    if gid == '1':
                        t = Tile('assets/dirt bg.png', x*self.tile_size, y*self.tile_size, tile_id="1", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '2':
                        t = Tile('assets/dirt block placed.png', x*self.tile_size, y*self.tile_size, tile_id="2", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '3':
                        t = Tile('assets/grass.png', x*self.tile_size, y*self.tile_size, tile_id="3", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '4':
                        t = Tile('assets/mini tree.png', x*self.tile_size, y*self.tile_size, tile_id="4", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '5':
                        t = Tile('assets/Tree Root L.png', x*self.tile_size, y*self.tile_size, tile_id="5", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '6':
                        t = Tile('assets/tree root r.png', x*self.tile_size, y*self.tile_size, tile_id="6", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '7':
                        t = Tile('assets/trunk 1.png', x*self.tile_size, y*self.tile_size, tile_id="7", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '8':
                        t = Tile('assets/trunk 2.png', x*self.tile_size, y*self.tile_size, tile_id="8", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '9':
                        t = Tile('assets/trunk 3.png', x*self.tile_size, y*self.tile_size, tile_id="9", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '10':
                        t = Tile('assets/trunk 4.png', x*self.tile_size, y*self.tile_size, tile_id="10", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '11':
                        t = Tile('assets/trunk base.png', x*self.tile_size, y*self.tile_size, tile_id="11", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid in self.gid_to_image:
                        # prefer TMX/TSX-provided image if available
                        img = self.gid_to_image[gid]
                        t = Tile(img, x*self.tile_size, y*self.tile_size, tile_id=gid, flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '12':
                        t = Tile('assets/stone block.png', x*self.tile_size, y*self.tile_size, tile_id="12", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '13':
                        t = Tile('assets/spike.png', x*self.tile_size, y*self.tile_size, tile_id="13", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)
                    elif gid == '14':
                        t = Tile('assets/water.png', x*self.tile_size, y*self.tile_size, tile_id="14", flip_h=flip_h, flip_v=flip_v, flip_d=flip_d)

                    # If the gid wasn't handled above, skip this cell (avoid appending None)
                    if t is None:
                        # warn so the user can add a mapping if needed
                        print(f"Warning: unknown gid {gid} at ({x},{y}) in layer '{layer_name}'")
                        continue

                    tiles.append(t)

                    # decide which named layer to place this tile in.
                    # Prefer the TMX layer name when present (so 'spikes' layer stays 'spikes'),
                    # unless the user explicitly mapped this tile id to a different layer via layer_ids.
                    target_layer = self._choose_layer_for_id(t.tile_id)

                    # ensure TMX layer exists in layers dict
                    if layer_name and layer_name not in self.layers:
                        self.layer_order.append(layer_name)
                        self.layers.setdefault(layer_name, [])

                    # If user explicitly mapped this tile id to a (known) layer, respect it.
                    mapped_layer = None
                    for lname, ids in self.layer_ids.items():
                        if t.tile_id in ids:
                            mapped_layer = lname
                            break

                    if mapped_layer and mapped_layer in self.layers:
                        layer = mapped_layer
                    else:
                        # prefer TMX layer name when available
                        if layer_name and layer_name in self.layers and layer_name.lower() != 'tile layer 1':
                            layer = layer_name
                        else:
                            layer = target_layer

                    if layer not in self.layers:
                        self.layers[layer] = []
                    self.layers[layer].append(t)

        return tiles

    def draw_map(self, surface, y_offset=0):
        # Draw layers in order from bottom to top
        for layer in self.layer_order:
            for tile in self.layers.get(layer, []):
                tile.draw(surface, y_offset)
